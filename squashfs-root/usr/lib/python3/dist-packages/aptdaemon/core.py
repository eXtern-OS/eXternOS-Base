#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Core components of aptdaemon.

This module provides the following core classes of the aptdaemon:
AptDaemon - complete daemon for managing software via DBus interface
Transaction - represents a software management operation
TransactionQueue - queue for aptdaemon transactions

The main function allows to run the daemon as a command.
"""
# Copyright (C) 2008-2009 Sebastian Heinlein <devel@glatzor.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

__all__ = ("Transaction", "TransactionQueue", "AptDaemon",
           "APTDAEMON_TRANSACTION_DBUS_INTERFACE", "APTDAEMON_DBUS_INTERFACE"
           "APTDAEMON_DBUS_PATH", "APTDAEMON_DBUS_SERVICE",
           "APTDAEMON_IDLE_CHECK_INTERVAL", "APTDAEMON_IDLE_TIMEOUT",
           "TRANSACTION_IDLE_TIMEOUT", "TRANSACTION_DEL_TIMEOUT")

import collections
from xml.etree import ElementTree
import gettext
from hashlib import md5
import locale
import logging
import logging.handlers
from optparse import OptionParser
import os
import re
import signal
import sys
import time
import uuid

from gi.repository import GObject, GLib
import dbus.exceptions
import dbus.service
import dbus.mainloop.glib

from .config import ConfigWriter
from . import errors
from . import enums
from defer import inline_callbacks, return_value, Deferred
from defer.utils import dbus_deferred_method
from . import policykit1
from .utils import split_package_id
from .worker import DummyWorker
from .worker.aptworker import (AptWorker,
                               trans_only_installs_pkgs_from_high_trust_repos)
from .loop import mainloop
from .logger import ColoredFormatter

# Setup i18n
_ = lambda msg: gettext.dgettext("aptdaemon", msg)
if sys.version >= '3':
    _gettext_method = "gettext"
    _ngettext_method = "ngettext"
else:
    _gettext_method = "ugettext"
    _ngettext_method = "ungettext"

APTDAEMON_DBUS_INTERFACE = 'org.debian.apt'
APTDAEMON_DBUS_PATH = '/org/debian/apt'
APTDAEMON_DBUS_SERVICE = 'org.debian.apt'

APTDAEMON_TRANSACTION_DBUS_INTERFACE = 'org.debian.apt.transaction'

APTDAEMON_IDLE_CHECK_INTERVAL = 60
APTDAEMON_IDLE_TIMEOUT = 10 * 60

# Maximum allowed time between the creation of a transaction and its queuing
TRANSACTION_IDLE_TIMEOUT = 300
# Keep the transaction for the given time alive on the bus after it has
# finished
TRANSACTION_DEL_TIMEOUT = 30

# regexp for the pkgname and optional arch, for details see
#   http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Source
REGEX_VALID_PACKAGENAME = "^[a-z0-9][a-z0-9\-+.]+(:[a-z0-9]+)?$"
# regexp for the version number, for details see:
#   http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
REGEX_VALID_VERSION = "^[0-9][0-9.+\-A-Za-z:~]*$"
# regexp for the archive (Suite) as found in the Release file
REGEX_VALID_RELEASE = "^[a-zA-Z0-9_\-\.]+$"

# Setup the DBus main loop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

# Required for daemon mode
os.putenv("PATH",
          "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")

# Setup logging to syslog and the console
log = logging.getLogger("AptDaemon")
try:
    _syslog_handler = logging.handlers.SysLogHandler(
        address="/dev/log",
        facility=logging.handlers.SysLogHandler.LOG_DAEMON)
    _syslog_handler.setLevel(logging.INFO)
    _syslog_formatter = logging.Formatter("%(name)s: %(levelname)s: "
                                          "%(message)s")
    _syslog_handler.setFormatter(_syslog_formatter)
except:
    pass
else:
    log.addHandler(_syslog_handler)
_console_handler = logging.StreamHandler()
_console_formatter = ColoredFormatter("%(asctime)s %(name)s [%(levelname)s]: "
                                      "%(message)s",
                                      "%T")
_console_handler.setFormatter(_console_formatter)
log.addHandler(_console_handler)
# FIXME: Use LoggerAdapter (requires Python 2.6)
log_trans = logging.getLogger("AptDaemon.Trans")

# Required for translations from APT
try:
    locale.setlocale(locale.LC_ALL, "")
except locale.Error:
    log.warning("Failed to unset LC_ALL. Translations are not available.")


def _excepthook(exc_type, exc_obj, exc_tb, apport_excepthook):
    """Handle exceptions of aptdaemon and avoid tiggering apport crash
    reports for valid DBusExceptions that are sent to the client.
    """
    # apport registers it's own excepthook as sys.excepthook. So we have to
    # send exceptions that we don't want to be tracked to Python's
    # internal excepthook directly
    if issubclass(exc_type, errors.AptDaemonError):
        sys.__excepthook__(exc_type, exc_obj, exc_tb)
    else:
        apport_excepthook(exc_type, exc_obj, exc_tb)

if sys.excepthook.__name__ == "apport_excepthook":
    apport_excepthook = sys.excepthook
    sys.excepthook = lambda etype, eobj, etb: _excepthook(etype, eobj, etb,
                                                          apport_excepthook)


class DBusObject(dbus.service.Object):

    """Enhanced D-Bus object class which supports properties."""

    WRITABLE_PROPERTIES = ()

    # pylint: disable-msg=C0103,C0322
    @dbus.service.signal(dbus_interface=dbus.PROPERTIES_IFACE,
                         signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed_properties,
                          invalidated_properties):
        """The signal gets emitted if a property of the object's
        interfaces changed.

        :param property: The name of the interface.
        :param changed_properties: A dictrionary of changed
            property/value pairs
        :param invalidated_properties: An array of property names which
            changed but the value isn't conveyed.

        :type interface: s
        :type changed_properties: a{sv}
        :type invalidated_properties: as
        """
        log.debug("Emitting PropertiesChanged: %s, %s, %s" %
                  (interface, changed_properties, invalidated_properties))

    # pylint: disable-msg=C0103,C0322
    @dbus.service.method(dbus.INTROSPECTABLE_IFACE,
                         in_signature='', out_signature='s',
                         path_keyword='object_path',
                         connection_keyword='connection')
    def Introspect(self, object_path, connection):
        # Inject the properties into the introspection xml data
        data = dbus.service.Object.Introspect(self, object_path, connection)
        xml = ElementTree.fromstring(data)
        for iface in xml.findall("interface"):
            props = self._get_properties(iface.attrib["name"])
            for key, value in props.items():
                attrib = {"name": key}
                if key in self.WRITABLE_PROPERTIES:
                    attrib["access"] = "readwrite"
                else:
                    attrib["access"] = "read"
                if isinstance(value, dbus.String):
                    attrib["type"] = "s"
                elif isinstance(value, dbus.UInt32):
                    attrib["type"] = "u"
                elif isinstance(value, dbus.Int32):
                    attrib["type"] = "i"
                elif isinstance(value, dbus.UInt64):
                    attrib["type"] = "t"
                elif isinstance(value, dbus.Int64):
                    attrib["type"] = "x"
                elif isinstance(value, dbus.Boolean):
                    attrib["type"] = "b"
                elif isinstance(value, dbus.Struct):
                    attrib["type"] = "(%s)" % value.signature
                elif isinstance(value, dbus.Dictionary):
                    attrib["type"] = "a{%s}" % value.signature
                elif isinstance(value, dbus.Array):
                    attrib["type"] = "a%s" % value.signature
                else:
                    raise Exception("Type %s of property %s isn't "
                                    "convertable" % (type(value), key))
                iface.append(ElementTree.Element("property", attrib))
        new_data = ElementTree.tostring(xml, encoding="UTF-8")
        return new_data

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(dbus.PROPERTIES_IFACE,
                          in_signature="ssv", out_signature="",
                          sender_keyword="sender")
    def Set(self, iface, name, value, sender):
        """Set a property.

        Only the user who intiaited the transaction is
        allowed to modify it.

        :param iface: The interface which provides the property.
        :param name: The name of the property which should be modified.
        :param value: The new value of the property.

        :type iface: s
        :type name: s
        :type value: v
        """
        log.debug("Set() was called: %s, %s" % (name, value))
        return self._set_property(iface, name, value, sender)

    # pylint: disable-msg=C0103,C0322
    @dbus.service.method(dbus.PROPERTIES_IFACE,
                         in_signature="s", out_signature="a{sv}")
    def GetAll(self, iface):
        """Get all available properties of the given interface."""
        log.debug("GetAll() was called: %s" % iface)
        return self._get_properties(iface)

    # pylint: disable-msg=C0103,C0322
    @dbus.service.method(dbus.PROPERTIES_IFACE,
                         in_signature="ss", out_signature="v")
    def Get(self, iface, property):
        """Return the value of the given property provided by the given
        interface.
        """
        log.debug("Get() was called: %s, %s" % (iface, property))
        return self._get_properties(iface)[property]

    def _set_property(self, iface, name, value, sender):
        """Helper to set a property on the properties D-Bus interface."""
        raise dbus.exceptions.DBusException("Unknown or read only "
                                            "property: %s" % name)

    def _get_properties(self, iface):
        """Helper to get the properties of a D-Bus interface."""
        return {}


class Transaction(DBusObject):

    """Represents a transaction on the D-Bus.

    A transaction represents a single package management task, e.g.
    installation or removal of packages. This class allows to expose
    information and to controll the transaction via DBus using PolicyKit
    for managing privileges.
    """

    ROLE_ACTION_MAP = {
        enums.ROLE_PK_QUERY: None,
        enums.ROLE_INSTALL_PACKAGES: (
            policykit1.PK_ACTION_INSTALL_OR_REMOVE_PACKAGES),
        enums.ROLE_REMOVE_PACKAGES: (
            policykit1.PK_ACTION_INSTALL_OR_REMOVE_PACKAGES),
        enums.ROLE_INSTALL_FILE: (
            policykit1.PK_ACTION_INSTALL_FILE),
        enums.ROLE_UPGRADE_PACKAGES: (
            policykit1.PK_ACTION_UPGRADE_PACKAGES),
        enums.ROLE_UPGRADE_SYSTEM: (
            policykit1.PK_ACTION_UPGRADE_PACKAGES),
        enums.ROLE_UPDATE_CACHE: (
            policykit1.PK_ACTION_UPDATE_CACHE),
        enums.ROLE_COMMIT_PACKAGES: (
            policykit1.PK_ACTION_INSTALL_OR_REMOVE_PACKAGES),
        enums.ROLE_ADD_VENDOR_KEY_FILE: (
            policykit1.PK_ACTION_CHANGE_REPOSITORY),
        enums.ROLE_ADD_VENDOR_KEY_FROM_KEYSERVER: (
            policykit1.PK_ACTION_CHANGE_REPOSITORY),
        enums.ROLE_REMOVE_VENDOR_KEY: (
            policykit1.PK_ACTION_CHANGE_REPOSITORY),
        enums.ROLE_FIX_INCOMPLETE_INSTALL: (
            policykit1.PK_ACTION_INSTALL_OR_REMOVE_PACKAGES),
        enums.ROLE_FIX_BROKEN_DEPENDS: (
            policykit1.PK_ACTION_INSTALL_OR_REMOVE_PACKAGES),
        enums.ROLE_ADD_REPOSITORY: (
            policykit1.PK_ACTION_CHANGE_REPOSITORY),
        enums.ROLE_RECONFIGURE: (
            policykit1.PK_ACTION_INSTALL_OR_REMOVE_PACKAGES),
        enums.ROLE_CLEAN: (
            policykit1.PK_ACTION_CLEAN),
        enums.ROLE_ENABLE_DISTRO_COMP: (
            policykit1.PK_ACTION_CHANGE_REPOSITORY),
        enums.ROLE_ADD_LICENSE_KEY: (
            policykit1.PK_ACTION_INSTALL_OR_REMOVE_PACKAGES)}

    WRITABLE_PROPERTIES = ("HttpProxy", "Terminal", "AllowUnauthenticated",
                           "DebconfSocket", "MetaData", "Locale",
                           "RemoveObsoleteDepends")

    def __init__(self, tid, role, queue, pid, uid, gid, cmdline, sender,
                 connect=True, bus=None, packages=None, kwargs=None):
        """Initialize a new Transaction instance.

        Keyword arguments:
        tid -- The unique identifier
        role -- The role enum of the transaction
        queue -- TransactionQueue instance of the daemon
        pid -- the id of the process which created the transaction
        uid -- the uid of the user who created the transaction
        cmdline -- the cmdline of the calling process
        sender -- the DBus name of the sender who created the transaction
        connect -- if the Transaction should connect to DBus (default is True)
        bus -- the DBus connection which should be used
            (defaults to system bus)
        """
        if tid is None:
            tid = uuid.uuid4().hex
        self.tid = "/org/debian/apt/transaction/%s" % tid
        if connect is True:
            self.bus = bus
            if bus is None:
                self.bus = dbus.SystemBus()
            bus_name = dbus.service.BusName(APTDAEMON_DBUS_SERVICE, self.bus)
            dbus_path = self.tid
        else:
            bus = None
            bus_name = None
            dbus_path = None
        DBusObject.__init__(self, bus_name, dbus_path)
        if not packages:
            packages = ([], [], [], [], [], [])
        if not kwargs:
            kwargs = {}
        self.queue = queue
        self.uid = uid
        self.gid = gid
        self.locale = dbus.String("")
        self.allow_unauthenticated = dbus.Boolean(False)
        self.remove_obsoleted_depends = dbus.Boolean(False)
        self.cmdline = cmdline
        self.pid = pid
        self.http_proxy = dbus.String("")
        self.terminal = dbus.String("")
        self.debconf = dbus.String("")
        self.kwargs = kwargs
        self._translation = None
        # The transaction which should be executed after this one
        self.after = None
        self._role = dbus.String(role)
        self._progress = dbus.Int32(0)
        # items_done, total_items, bytes_done, total_bytes, speed, time
        self._progress_details = dbus.Struct((0, 0, 0, 0, 0.0, 0),
                                             signature="iixxdx")
        self._progress_download = dbus.Struct(("", "", "", 0, 0, ""),
                                              signature="sssxxs")
        self._progress_package = dbus.Struct(("", ""), signature="ss")
        self._exit = dbus.String(enums.EXIT_UNFINISHED)
        self._status = dbus.String(enums.STATUS_SETTING_UP)
        self._status_details = dbus.String("")
        self._error = None
        self._error_property = dbus.Struct(("", ""), signature="ss")
        self._cancellable = dbus.Boolean(True)
        self._term_attached = dbus.Boolean(False)
        self._required_medium = dbus.Struct(("", ""), signature="ss")
        self._config_file_conflict = dbus.Struct(("", ""), signature="ss")
        self._config_file_conflict_resolution = ""
        self.cancelled = dbus.Boolean(False)
        self.paused = dbus.Boolean(False)
        self._meta_data = dbus.Dictionary(signature="sv")
        self._download = dbus.Int64(0)
        self._space = dbus.Int64(0)
        self._depends = dbus.Struct([dbus.Array([], signature='s')
                                     for i in range(7)],
                                    signature="asasasasasasas")
        self._packages = dbus.Struct([dbus.Array(pkgs, signature="s")
                                      for pkgs in packages],
                                     signature="asasasasasas")
        self._unauthenticated = dbus.Array([], signature=dbus.Signature('s'))
        self._high_trust_packages = dbus.Array([],
                                               signature=dbus.Signature('s'))
        # Add a timeout which removes the transaction from the bus if it
        # hasn't been setup and run for the TRANSACTION_IDLE_TIMEOUT period
        self._idle_watch = GLib.timeout_add_seconds(
            TRANSACTION_IDLE_TIMEOUT, self._remove_from_connection_no_raise)
        # Handle a disconnect of the client application
        self.sender_alive = True
        if bus:
            self._sender_watch = bus.watch_name_owner(
                sender, self._sender_owner_changed)
        else:
            self._sender_watch = None
        self.sender = sender
        self.output = ""
        self.simulated = None
        self._simulated_cb = None

    def _sender_owner_changed(self, connection):
        """Callback if the owner of the original sender changed, e.g.
        disconnected."""
        if not connection:
            self.sender_alive = False

    def _remove_from_connection_no_raise(self):
        """Version of remove_from_connection that does not raise if the
        object isn't exported.
        """
        log_trans.debug("Removing transaction")
        try:
            self.remove_from_connection()
        except LookupError as error:
            log_trans.debug("remove_from_connection() raised LookupError: "
                            "'%s'" % error)
        # Forget a not yet queued transaction
        try:
            self.queue.limbo.pop(self.tid)
        except KeyError:
            pass
        return False

    def _convert_struct(self, lst, signature):
        """Convert a list to a DBus struct with the given signature. Currently
        integer, long, unsigned long, double, string and boolean are
        supported (ixtdsb).
        """
        struct = []
        for num, item in enumerate(lst):
            try:
                if signature[num] == "i":
                    struct.append(dbus.Int32(item))
                elif signature[num] == "x":
                    struct.append(dbus.Int64(item))
                elif signature[num] == "t":
                    struct.append(dbus.UInt64(item))
                elif signature[num] == "d":
                    struct.append(dbus.Double(item))
                elif signature[num] == "b":
                    struct.append(dbus.Boolean(item))
                elif signature[num] == "s":
                    struct.append(get_dbus_string(item))
                else:
                    raise Exception("Value %s with unknown signature %s" %
                                    (item, signature[num]))
            except Exception as error:
                raise error.__class__("Failed to convert item %s of %s with "
                                      "signature %s: %s" % (num, lst,
                                                            signature,
                                                            str(error)))
        return dbus.Struct(struct, signature=dbus.Signature(signature))

    def _set_meta_data(self, data):
        # Perform some checks
        if self.status != enums.STATUS_SETTING_UP:
            raise errors.TransactionAlreadyRunning()
        if not isinstance(data, dbus.Dictionary):
            raise errors.InvalidMetaDataError("The data value has to be a "
                                              "dictionary: %s" % data)
        if not data.signature.startswith("s"):
            raise errors.InvalidMetaDataError("Only strings are accepted "
                                              "as keys.")
        for key, value in data.items():
            if key in self._meta_data:
                raise errors.InvalidMetaDataError("The key %s already "
                                                  "exists. It is not allowed "
                                                  "to overwrite existing "
                                                  "data." % key)
            if not len(key.split("_")) > 1:
                raise errors.InvalidMetaDataError("The key %s has to be of "
                                                  "the format "
                                                  "IDENTIFIER-KEYNAME")
            if not isinstance(value, dbus.String):
                raise errors.InvalidMetaDataError("The value has to be a "
                                                  "string: %s" % value)
        # Merge new data into existing one:
        self._meta_data.update(data)
        self.PropertyChanged("MetaData", self._meta_data)

    def _get_meta_data(self):
        return self._meta_data

    meta_data = property(_get_meta_data, _set_meta_data,
                         doc="Allows client applications to store meta data "
                             "for the transaction in a dictionary.")

    def _set_role(self, enum):
        if self._role != enums.ROLE_UNSET:
            raise errors.TransactionRoleAlreadySet()
        self._role = dbus.String(enum)
        self.PropertyChanged("Role", self._role)

    def _get_role(self):
        return self._role

    role = property(_get_role, _set_role, doc="Operation type of transaction.")

    def _set_progress_details(self, details):
        # items_done, total_items, bytes_done, total_bytes, speed, time
        self._progress_details = self._convert_struct(details, "iixxdx")
        self.PropertyChanged("ProgressDetails", self._progress_details)

    def _get_progress_details(self):
        return self._progress_details

    progress_details = property(_get_progress_details, _set_progress_details,
                                doc="Tuple containing detailed progress "
                                    "information: items done, total items, "
                                    "bytes done, total bytes, speed and "
                                    "remaining time")

    def _set_error(self, excep):
        self._error = excep
        msg = self.gettext(excep.details) % excep.details_args
        self._error_property = self._convert_struct((excep.code, msg), "ss")
        self.PropertyChanged("Error", self._error_property)

    def _get_error(self):
        return self._error

    error = property(_get_error, _set_error, doc="Raised exception.")

    def _set_exit(self, enum):
        self.status = enums.STATUS_FINISHED
        self._exit = dbus.String(enum)
        self.PropertyChanged("ExitState", self._exit)
        self.Finished(self._exit)
        if self._sender_watch:
            self._sender_watch.cancel()
        # Remove the transaction from the Bus after it is complete. A short
        # timeout helps lazy clients
        GLib.timeout_add_seconds(TRANSACTION_DEL_TIMEOUT,
                                 self._remove_from_connection_no_raise)

    def _get_exit(self):
        return self._exit

    exit = property(_get_exit, _set_exit,
                    doc="The exit state of the transaction.")

    def _get_download(self):
        return self._download

    def _set_download(self, size):
        self._download = dbus.Int64(size)
        self.PropertyChanged("Download", self._download)

    download = property(_get_download, _set_download,
                        doc="The download size of the transaction.")

    def _get_space(self):
        return self._space

    def _set_space(self, size):
        self._space = dbus.Int64(size)
        self.PropertyChanged("Space", self._space)

    space = property(_get_space, _set_space,
                     doc="The required disk space of the transaction.")

    def _set_packages(self, packages):
        self._packages = dbus.Struct([dbus.Array(pkgs, signature="s")
                                      for pkgs in packages],
                                     signature="as")
        self.PropertyChanged("Packages", self._packages)

    def _get_packages(self):
        return self._packages

    packages = property(_get_packages, _set_packages,
                        doc="Packages which will be explictly installed, "
                            "reinstalled, removed, purged, upgraded or "
                            "downgraded.")

    def _get_unauthenticated(self):
        return self._unauthenticated

    def _set_unauthenticated(self, unauthenticated):
        self._unauthenticated = dbus.Array(unauthenticated, signature="s")
        self.PropertyChanged("Unauthenticated", self._unauthenticated)

    unauthenticated = property(_get_unauthenticated, _set_unauthenticated,
                               doc="Unauthenticated packages in this "
                                   "transaction")

    # package that can have a different auth schema, useful for e.g.
    # lightweight packages like unity-webapps or packages comming from
    # a high trust repository (e.g. a internal company repo)
    def _get_high_trust_packages(self):
        return self._high_trust_packages

    def _set_high_trust_packages(self, whitelisted_packages):
        self._high_trust_packages = dbus.Array(whitelisted_packages,
                                               signature="s")
        self.PropertyChanged("HighTrustWhitelistedPackages",
                             self._high_trust_packages)

    high_trust_packages = property(_get_high_trust_packages,
                                   _set_high_trust_packages,
                                   doc="High trust packages in this "
                                       "transaction")

    def _get_depends(self):
        return self._depends

    def _set_depends(self, depends):
        self._depends = dbus.Struct([dbus.Array(deps, signature="s")
                                     for deps in depends],
                                    signature="as")
        self.PropertyChanged("Dependencies", self._depends)

    depends = property(_get_depends, _set_depends,
                       doc="The additional dependencies: installs, removals, "
                           "upgrades and downgrades.")

    def _get_status(self):
        return self._status

    def _set_status(self, enum):
        self._status = dbus.String(enum)
        self.PropertyChanged("Status", self._status)

    status = property(_get_status, _set_status,
                      doc="The status of the transaction.")

    def _get_status_details(self):
        return self._status_details

    def _set_status_details(self, text):
        self._status_details = get_dbus_string(text)
        self.PropertyChanged("StatusDetails", self._status_details)

    status_details = property(_get_status_details, _set_status_details,
                              doc="The status message from apt.")

    def _get_progress(self):
        return self._progress

    def _set_progress(self, percent):
        self._progress = dbus.Int32(percent)
        self.PropertyChanged("Progress", self._progress)

    progress = property(_get_progress, _set_progress,
                        "The progress of the transaction in percent.")

    def _get_progress_package(self):
        return self._progress_package

    def _set_progress_package(self, progress_package):
        self._progress_package = self._convert_struct(progress_package, "ss")

    progress_package = property(_get_progress_package,
                                _set_progress_package,
                                doc="The last progress update of a currently"
                                    "processed package. A tuple of package "
                                    "name and status enum.")

    def _get_progress_download(self):
        return self._progress_download

    def _set_progress_download(self, progress_download):
        self._progress_download = self._convert_struct(progress_download,
                                                       "sssxxs")
        self.PropertyChanged("ProgressDownload", self._progress_download)

    progress_download = property(_get_progress_download,
                                 _set_progress_download,
                                 doc="The last progress update of a currently"
                                     "running download. A tuple of URI, "
                                     "status, short description, full size, "
                                     "partially downloaded size and a status "
                                     "message.")

    def _get_cancellable(self):
        return self._cancellable

    def _set_cancellable(self, cancellable):
        self._cancellable = dbus.Boolean(cancellable)
        self.PropertyChanged("Cancellable", self._cancellable)

    cancellable = property(_get_cancellable, _set_cancellable,
                           doc="If it's currently allowed to cancel the "
                               "transaction.")

    def _get_term_attached(self):
        return self._term_attached

    def _set_term_attached(self, attached):
        self._term_attached = dbus.Boolean(attached)
        self.PropertyChanged("TerminalAttached", self._term_attached)

    term_attached = property(_get_term_attached, _set_term_attached,
                             doc="If the controlling terminal is currently "
                                 "attached to the dpkg call of the "
                                 "transaction.")

    def _get_required_medium(self):
        return self._required_medium

    def _set_required_medium(self, medium):
        self._required_medium = self._convert_struct(medium, "ss")
        self.PropertyChanged("RequiredMedium", self._required_medium)
        self.MediumRequired(*self._required_medium)

    required_medium = property(_get_required_medium, _set_required_medium,
                               doc="Tuple containing the label and the drive "
                                   "of a required CD/DVD to install packages "
                                   "from.")

    def _get_config_file_conflict(self):
        return self._config_file_conflict

    def _set_config_file_conflict(self, prompt):
        if prompt is None:
            self._config_file_conflict = dbus.Struct(("", ""), signature="ss")
            return
        self._config_file_conflict = self._convert_struct(prompt, "ss")
        self.PropertyChanged("ConfigFileConflict", self._config_file_conflict)
        self.ConfigFileConflict(*self._config_file_conflict)

    config_file_conflict = property(_get_config_file_conflict,
                                    _set_config_file_conflict,
                                    doc="Tuple containing the old and the new "
                                        "path of the configuration file")

    # Signals

    # pylint: disable-msg=C0103,C0322
    @dbus.service.signal(dbus_interface=APTDAEMON_TRANSACTION_DBUS_INTERFACE,
                         signature="sv")
    def PropertyChanged(self, property, value):
        """The signal gets emitted if a property of the transaction changed.

        :param property: The name of the property.
        :param value: The new value of the property.

        :type property: s
        :type value: v
        """
        log_trans.debug("Emitting PropertyChanged: %s, %s" % (property, value))

    # pylint: disable-msg=C0103,C0322
    @dbus.service.signal(dbus_interface=APTDAEMON_TRANSACTION_DBUS_INTERFACE,
                         signature="s")
    def Finished(self, exit_state):
        """The signal gets emitted if the transaction has been finished.

        :param exit_state: The exit state of the transaction, e.g.
            ``exit-failed``.
        :type exit_state: s
        """
        log_trans.debug("Emitting Finished: %s" %
                        enums.get_exit_string_from_enum(exit_state))

    # pylint: disable-msg=C0103,C0322
    @dbus.service.signal(dbus_interface=APTDAEMON_TRANSACTION_DBUS_INTERFACE,
                         signature="ss")
    def MediumRequired(self, medium, drive):
        """Set and emit the required medium change.

        This method/signal should be used to inform the user to
        insert the installation CD/DVD:

        Keyword arguments:
        medium -- the CD/DVD label
        drive -- mount point of the drive
        """
        log_trans.debug("Emitting MediumRequired: %s, %s" % (medium, drive))

    # pylint: disable-msg=C0103,C0322
    @dbus.service.signal(dbus_interface=APTDAEMON_TRANSACTION_DBUS_INTERFACE,
                         signature="ss")
    def ConfigFileConflict(self, old, new):
        """Set and emit the ConfigFileConflict signal.

        This method/signal should be used to inform the user to
        answer a config file prompt.

        Keyword arguments:
        old -- current version of the configuration prompt
        new -- new version of the configuration prompt
        """
        log_trans.debug("Emitting ConfigFileConflict: %s, %s" % (old, new))

    # Methods

    def _set_locale(self, locale_str):
        """Set the language and encoding.

        Keyword arguments:
        locale -- specifies language, territory and encoding according
                  to RFC 1766,  e.g. "de_DE.UTF-8"
        """
        if self.status != enums.STATUS_SETTING_UP:
            raise errors.TransactionAlreadyRunning()
        try:
            # ensure locale string is str() and not dbus.String()
            (lang, encoding) = locale._parse_localename(str(locale_str))
        except ValueError:
            raise
        else:
            if lang is None:
                lang = "C"
                self.locale = dbus.String(lang)
            else:
                self.locale = dbus.String("%s.%s" % (lang, encoding))
            self._translation = gettext.translation("aptdaemon",
                                                    fallback=True,
                                                    languages=[lang])
            self.PropertyChanged("locale", self.locale)

    @inline_callbacks
    def _set_http_proxy(self, url, sender):
        """Set an http network proxy.

        Keyword arguments:
        url -- the URL of the proxy server, e.g. http://proxy:8080
        """
        if url != "" and (not url.startswith("http://") or ":" not in url):
            raise errors.InvalidProxyError(url)
        action = policykit1.PK_ACTION_SET_PROXY
        yield policykit1.check_authorization_by_name(sender, action,
                                                     bus=self.bus)
        self.http_proxy = dbus.String(url)
        self.PropertyChanged("HttpProxy", self.http_proxy)

    def _set_remove_obsoleted_depends(self, remove_obsoleted_depends):
        """Set the handling of the removal of automatically installed
        dependencies which are now obsoleted.

        Keyword arguments:
        remove_obsoleted_depends -- If True also remove automatically installed
            dependencies of to removed packages
        """
        self.remove_obsoleted_depends = dbus.Boolean(remove_obsoleted_depends)
        self.PropertyChanged("RemoveObsoletedDepends",
                             self.remove_obsoleted_depends)

    def _set_allow_unauthenticated(self, allow_unauthenticated):
        """Set the handling of unauthenticated packages

        Keyword arguments:
        allow_unauthenticated -- True to allow packages that come from a
            repository without a valid authentication signature
        """
        self.allow_unauthenticated = dbus.Boolean(allow_unauthenticated)
        self.PropertyChanged("AllowUnauthenticated",
                             self.allow_unauthenticated)

    # pylint: disable-msg=C0103,C0322
    @dbus.service.method(APTDAEMON_TRANSACTION_DBUS_INTERFACE,
                         in_signature="s", out_signature="",
                         sender_keyword="sender")
    def RunAfter(self, tid, sender):
        """Queue the transaction for processing after the given transaction.

        The transaction will also fail if the previous one failed. Several
        transactions can be chained up.

        :param tid: The id of the transaction which should be executed
            before.

        :type tid: s
        """
        log_trans.info("Queuing transaction %s", self.tid)
        try:
            trans_before = self.queue.limbo[tid]
        except KeyError:
            raise Exception("The given transaction doesn't exist or is "
                            "already queued!")
        if trans_before.after:
            raise Exception("There is already an after transaction!")
        trans_before.after = self

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_TRANSACTION_DBUS_INTERFACE,
                          in_signature="", out_signature="",
                          sender_keyword="sender")
    def Run(self, sender):
        """Check the authentication, simulate and queue the transaction for
        processing."""
        log_trans.info("Queuing transaction %s", self.tid)
        return self._run(sender)

    @inline_callbacks
    def _run(self, sender):
        yield self._check_foreign_user(sender)
        yield self._check_simulated()
        yield self._check_auth()
        self.queue.put(self.tid)
        self.status = enums.STATUS_WAITING
        next_trans = self.after
        while next_trans:
            yield self._check_simulated()
            yield next_trans._check_auth()
            self.queue.put(next_trans.tid)
            next_trans.status = enums.STATUS_WAITING
            next_trans = next_trans.after

    @inline_callbacks
    def _check_simulated(self):
        # Simulate the new transaction if this has not been done before:
        # FIXME: Compare the simulated timestamp with the time stamp of
        #       the status and re-simulate the transaction
        if self.simulated is None:
            # If there isn't any transaction on the queue we send an early
            # progress information. Otherwise it juse seems that aptdaemon
            # hangs since it doesn't send any progress information after the
            # the transaction has been started
            if not self.queue.worker.trans:
                self.progress = 9
            yield self._simulate_real()
        else:
            raise StopIteration

    @inline_callbacks
    def _check_auth(self):
        """Check silently if one of the high level privileges has been granted
        before to reduce clicks to install packages from third party
        epositories: AddRepository -> UpdateCache -> InstallPackages
        """
        self.status = enums.STATUS_AUTHENTICATING
        action = self.ROLE_ACTION_MAP[self.role]
        if action is None:
            raise StopIteration
        # Special case if InstallPackages only touches stuff from the
        # high trust whitelist
        if (self.role in (enums.ROLE_INSTALL_PACKAGES,
                          enums.ROLE_COMMIT_PACKAGES) and
                trans_only_installs_pkgs_from_high_trust_repos(self)):
            action = policykit1.PK_ACTION_INSTALL_PACKAGES_FROM_HIGH_TRUST_REPO
        # Special case if CommitPackages only upgrades
        if (self.role == enums.ROLE_COMMIT_PACKAGES and
                not self.packages[enums.PKGS_INSTALL] and
                not self.packages[enums.PKGS_REINSTALL] and
                not self.packages[enums.PKGS_REMOVE] and
                not self.packages[enums.PKGS_PURGE] and
                not self.packages[enums.PKGS_DOWNGRADE]):
            action = policykit1.PK_ACTION_UPGRADE_PACKAGES
        try:
            authorized = yield self._check_alternative_auth()
            if not authorized:
                yield policykit1.check_authorization_by_name(self.sender,
                                                             action,
                                                             bus=self.bus)
        except errors.NotAuthorizedError as error:
            self.error = errors.TransactionFailed(enums.ERROR_NOT_AUTHORIZED,
                                                  str(error))
            self.exit = enums.EXIT_FAILED
            raise(error)
        except errors.AuthorizationFailed as error:
            self.error = errors.TransactionFailed(enums.ERROR_AUTH_FAILED,
                                                  str(error))
            self.exit = enums.EXIT_FAILED
            raise(error)

    @inline_callbacks
    def _check_alternative_auth(self):
        """Check non-interactively if one of the high level privileges
        has been granted.
        """
        if self.role not in [enums.ROLE_ADD_REPOSITORY,
                             enums.ROLE_ADD_VENDOR_KEY_FROM_KEYSERVER,
                             enums.ROLE_UPDATE_CACHE,
                             enums.ROLE_INSTALL_PACKAGES,
                             enums.ROLE_ADD_LICENSE_KEY]:
            return_value(False)
        flags = policykit1.CHECK_AUTH_NONE
        for action in [policykit1.PK_ACTION_INSTALL_PACKAGES_FROM_NEW_REPO,
                       policykit1.PK_ACTION_INSTALL_PURCHASED_PACKAGES]:
            try:
                yield policykit1.check_authorization_by_name(self.sender,
                                                             action,
                                                             bus=self.bus,
                                                             flags=flags)
            except errors.NotAuthorizedError:
                continue
            else:
                return_value(True)
        return_value(False)

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_TRANSACTION_DBUS_INTERFACE,
                          in_signature="", out_signature="",
                          sender_keyword="sender")
    def Cancel(self, sender):
        """Cancel the transaction."""
        log_trans.info("Cancelling transaction %s", self.tid)
        return self._cancel(sender)

    @inline_callbacks
    def _cancel(self, sender):
        try:
            yield self._check_foreign_user(sender)
        except errors.ForeignTransaction:
            action = policykit1.PK_ACTION_CANCEL_FOREIGN
            yield policykit1.check_authorization_by_name(sender, action,
                                                         bus=self.bus)
        try:
            self.queue.remove(self)
            log_trans.debug("Removed transaction from queue")
        except ValueError:
            pass
        else:
            self.status = enums.STATUS_CANCELLING
            self.exit = enums.EXIT_CANCELLED
            raise StopIteration
        if self.tid in self.queue.limbo:
            self.exit = enums.EXIT_CANCELLED
            raise StopIteration
        elif self.cancellable:
            log_trans.debug("Setting cancel event")
            self.cancelled = True
            self.status = enums.STATUS_CANCELLING
            self.paused = False
            raise StopIteration
        raise errors.AptDaemonError("Could not cancel transaction")

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_TRANSACTION_DBUS_INTERFACE,
                          in_signature="", out_signature="",
                          sender_keyword="sender")
    def Simulate(self, sender):
        """Simulate a transaction to update its dependencies, download size
        and required disk space.

        Call this method if you want to show changes before queuing the
        transaction.
        """
        log_trans.info("Simulate was called")
        return self._simulate(sender)

    @inline_callbacks
    def _simulate(self, sender):
        if self._simulated_cb:
            raise errors.TransactionAlreadySimulating()
        if self.status != enums.STATUS_SETTING_UP:
            raise errors.TransactionAlreadyRunning()
        yield self._check_foreign_user(sender)
        yield self._simulate_real()

    @inline_callbacks
    def _simulate_real(self):
        if self._simulated_cb:
            raise errors.TransactionAlreadySimulating()
        self.queue.worker.simulate(self)
        deferred = Deferred()
        if self._idle_watch is not None:
            GLib.source_remove(self._idle_watch)
        self._idle_watch = None
        self._simulated_cb = self.queue.worker.connect(
            "transaction-simulated",
            self._on_transaction_simulated,
            deferred)
        yield deferred

    def _on_transaction_simulated(self, worker, trans, deferred):
        if trans is not self:
            return
        self.queue.worker.disconnect(self._simulated_cb)
        self._simualted_cb = None
        if trans.error:
            deferred.errback(trans.error)
        else:
            deferred.callback()

    def _set_terminal(self, ttyname):
        """Set the controlling terminal.

        The worker will be attached to the specified slave end of a pty
        master/slave pair. This allows to interact with the

        Can only be changed before the transaction is started.

        Keyword arguments:
        ttyname -- file path to the slave file descriptor
        """
        if self.status != enums.STATUS_SETTING_UP:
            raise errors.TransactionAlreadyRunning()
        if not os.access(ttyname, os.W_OK):
            raise errors.AptDaemonError("Pty device does not exist: "
                                        "%s" % ttyname)
        if not os.stat(ttyname)[4] == self.uid:
            raise errors.AptDaemonError("Pty device '%s' has to be owned by"
                                        "the owner of the transaction "
                                        "(uid %s) " % (ttyname, self.uid))
        if os.path.dirname(ttyname) != "/dev/pts":
            raise errors.AptDaemonError("%s isn't a tty" % ttyname)
        try:
            slave_fd = os.open(ttyname, os.O_RDWR | os.O_NOCTTY)
            if os.isatty(slave_fd):
                self.terminal = dbus.String(ttyname)
                self.PropertyChanged("Terminal", self.terminal)
            else:
                raise errors.AptDaemonError("%s isn't a tty" % ttyname)
        finally:
            os.close(slave_fd)

    def _set_debconf(self, debconf_socket):
        """Set the socket of the debconf proxy.

        The worker process forwards all debconf commands through this
        socket by using the passthrough frontend. On the client side
        debconf-communicate should be connected to the socket.

        Can only be changed before the transaction is started.

        Keyword arguments:
        debconf_socket: absolute path to the socket
        """
        if self.status != enums.STATUS_SETTING_UP:
            raise errors.TransactionAlreadyRunning()
        if not os.access(debconf_socket, os.W_OK):
            raise errors.AptDaemonError("socket does not exist: "
                                        "%s" % debconf_socket)
        if not os.stat(debconf_socket)[4] == self.uid:
            raise errors.AptDaemonError("socket '%s' has to be owned by the "
                                        "owner of the "
                                        "transaction" % debconf_socket)
        self.debconf = dbus.String(debconf_socket)
        self.PropertyChanged("DebconfSocket", self.debconf)

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_TRANSACTION_DBUS_INTERFACE,
                          in_signature="s", out_signature="",
                          sender_keyword="sender")
    def ProvideMedium(self, medium, sender):
        """Continue paused transaction with the inserted medium.

        If a media change is required to install packages from CD/DVD
        the transaction will be paused and could be resumed with this
        method.

        :param medium: The label of the CD/DVD.
        :type medium: s
        """
        log_trans.info("Medium %s was provided", medium)
        return self._provide_medium(medium, sender)

    @inline_callbacks
    def _provide_medium(self, medium, sender):
        yield self._check_foreign_user(sender)
        if not self.required_medium:
            raise errors.AptDaemonError("There isn't any required medium.")
        if not self.required_medium[0] == medium:
            raise errors.AptDaemonError("The medium '%s' isn't "
                                        "requested." % medium)
        self.paused = False

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_TRANSACTION_DBUS_INTERFACE,
                          in_signature="ss", out_signature="",
                          sender_keyword="sender")
    def ResolveConfigFileConflict(self, config, answer, sender):
        """Resolve a configuration file conflict and continue the transaction.

        If a config file prompt is detected the transaction will be
        paused and could be resumed with this method.

        :param config: The path to the original config file.
        :param answer: The answer to the configuration file question, can be
            "keep" or "replace"

        :type config: s
        :type answer: s
        """
        log_trans.info("Resolved conflict of %s with %s", config, answer)
        return self._resolve_config_file_conflict(config, answer, sender)

    @inline_callbacks
    def _resolve_config_file_conflict(self, config, answer, sender):
        yield self._check_foreign_user(sender)
        if not self.config_file_conflict:
            raise errors.AptDaemonError("There isn't any config file prompt "
                                        "required")
        if answer not in ["keep", "replace"]:
            # FIXME: should we re-send the config file prompt
            #        message or assume the client is buggy and
            #        just use a safe default (like keep)?
            raise errors.AptDaemonError("Invalid value: %s" % answer)
        if not self.config_file_conflict[0] == config:
            raise errors.AptDaemonError("Invalid config file: %s" % config)
        self.config_file_conflict_resolution = answer
        self.paused = False

    @inline_callbacks
    def _set_property(self, iface, name, value, sender):
        """Helper to set a name on the properties D-Bus interface."""
        yield self._check_foreign_user(sender)
        if iface == APTDAEMON_TRANSACTION_DBUS_INTERFACE:
            if name == "MetaData":
                self._set_meta_data(value)
            elif name == "Terminal":
                self._set_terminal(value)
            elif name == "DebconfSocket":
                self._set_debconf(value)
            elif name == "Locale":
                self._set_locale(value)
            elif name == "RemoveObsoletedDepends":
                self._set_remove_obsoleted_depends(value)
            elif name == "AllowUnauthenticated":
                self._set_allow_unauthenticated(value)
            elif name == "HttpProxy":
                self._set_http_proxy(value, sender)
            else:
                raise dbus.exceptions.DBusException("Unknown or read only "
                                                    "property: %s" % name)
        else:
            raise dbus.exceptions.DBusException("Unknown interface: %s" %
                                                iface)

    def _get_properties(self, iface):
        """Helper to get the properties of a D-Bus interface."""
        if iface == APTDAEMON_TRANSACTION_DBUS_INTERFACE:
            return {"Role": self.role,
                    "Progress": self.progress,
                    "ProgressDetails": self.progress_details,
                    "ProgressDownload": self.progress_download,
                    "Status": self.status,
                    "StatusDetails": self.status_details,
                    "Cancellable": self.cancellable,
                    "TerminalAttached": self.term_attached,
                    "RequiredMedium": self.required_medium,
                    "ConfigFileConflict": self.config_file_conflict,
                    "ExitState": self.exit,
                    "Error": self._error_property,
                    "Locale": self.locale,
                    "Terminal": self.terminal,
                    "DebconfSocket": self.debconf,
                    "Paused": dbus.Boolean(self.paused),
                    "AllowUnauthenticated": self.allow_unauthenticated,
                    "RemoveObsoletedDepends": self.remove_obsoleted_depends,
                    "HttpProxy": self.http_proxy,
                    "Packages": self.packages,
                    "MetaData": self.meta_data,
                    "Dependencies": self.depends,
                    "Download": self.download,
                    "Space": self.space,
                    "Unauthenticated": self.unauthenticated,
                    }
        else:
            return {}

    @inline_callbacks
    def _check_foreign_user(self, dbus_name):
        """Check if the transaction is owned by the given caller."""
        uid = yield policykit1.get_uid_from_dbus_name(dbus_name, self.bus)
        if self.uid != uid:
            raise errors.ForeignTransaction()

    def _set_kwargs(self, kwargs):
        """Set the kwargs which will be send to the AptWorker."""
        self.kwargs = kwargs

    def _get_translations(self):
        """Get a usable translations object, no matter what."""
        if self._translation:
            return self._translation
        else:
            domain = "aptdaemon"
            return gettext.translation(domain, gettext.bindtextdomain(domain),
                                       gettext.bind_textdomain_codeset(domain),
                                       fallback=True)

    def gettext(self, msg):
        """Translate the given message to the language of the transaction.
        Fallback to the system default.
        """
        # Avoid showing the header of the mo file for an empty string
        if not msg:
            return ""
        translation = self._get_translations()
        return getattr(translation, _gettext_method)(msg)

    def ngettext(self, singular, plural, count):
        """Translate the given plural message to the language of the
        transaction. Fallback to the system default.
        """
        translation = self._get_translations()
        return getattr(translation, _ngettext_method)(singular, plural, count)


class TransactionQueue(GObject.GObject):

    """Queue for transactions."""

    __gsignals__ = {"queue-changed": (GObject.SignalFlags.RUN_FIRST,
                                      None,
                                      ())}

    def __init__(self, worker):
        """Intialize a new TransactionQueue instance."""
        GObject.GObject.__init__(self)
        self._queue = collections.deque()
        self._proc_count = 0
        self.worker = worker
        # Used to keep track of not yet queued transactions
        self.limbo = {}
        self.worker.connect("transaction-done", self._on_transaction_done)

    def __len__(self):
        return len(self._queue)

    def _emit_queue_changed(self):
        """Emit the queued-changed signal."""
        log.debug("emitting queue changed")
        self.emit("queue-changed")

    def put(self, tid):
        """Add an item to the queue."""
        trans = self.limbo.pop(tid)
        if trans._idle_watch is not None:
            GLib.source_remove(trans._idle_watch)
        if self.worker.trans:
            trans.status = enums.STATUS_WAITING
            self._queue.append(trans)
        else:
            self.worker.run(trans)
        self._emit_queue_changed()

    def _on_transaction_done(self, worker, trans):
        """Mark the last item as done and request a new item."""
        # FIXME: Check if the transaction failed because of a broken system or
        #       if dpkg journal is dirty. If so allready queued transactions
        #       except the repair transactions should be removed from the queue
        if trans.exit in [enums.EXIT_FAILED, enums.EXIT_CANCELLED]:
            if trans.exit == enums.EXIT_FAILED:
                exit = enums.EXIT_PREVIOUS_FAILED
            else:
                exit = enums.EXIT_CANCELLED
            _trans = trans.after
            while _trans:
                self.remove(_trans)
                _trans.exit = exit
                msg = enums.get_role_error_from_enum(trans.role)
                _trans.status_details = msg
                _trans = _trans.after
        try:
            next_trans = self._queue.popleft()
        except IndexError:
            log.debug("There isn't any queued transaction")
        else:
            self.worker.run(next_trans)
        self._emit_queue_changed()

    def remove(self, transaction):
        """Remove the specified item from the queue."""
        self._queue.remove(transaction)
        self._emit_queue_changed()

    def clear(self):
        """Remove all items from the queue."""
        for transaction in self._queue:
            transaction._remove_from_connection_no_raise()
        self._queue.clear()

    @property
    def items(self):
        """Return a list containing all queued items."""
        return list(self._queue)


class AptDaemon(DBusObject):

    """Provides a system daemon to process package management tasks.

    The daemon is transaction based. Each package management tasks runs
    in a separate transaction. The transactions can be created,
    monitored and managed via the D-Bus interface.
    """

    def __init__(self, options, connect=True, bus=None):
        """Initialize a new AptDaemon instance.

        Keyword arguments:
        options -- command line options of the type optparse.Values
        connect -- if the daemon should connect to the D-Bus (default is True)
        bus -- the D-Bus to connect to (defaults to the system bus)
        """
        log.info("Initializing daemon")
        # glib does not support SIGQUIT
        # GLib.unix_signal_add_full(
        #     GLib.PRIORITY_HIGH, signal.SIGQUIT, self._sigquit, None)
        GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGTERM,
                             self._sigquit, None)
        # Decrease the priority of the daemon to avoid blocking UI
        os.nice(5)
        self.options = options
        self.packagekit = None
        if connect is True:
            if bus is None:
                bus = dbus.SystemBus()
            self.bus = bus
            bus_path = APTDAEMON_DBUS_PATH
            # Check if another object has already registered the name on
            # the bus. Quit the other daemon if replace would be set
            try:
                bus_name = dbus.service.BusName(APTDAEMON_DBUS_SERVICE,
                                                bus,
                                                do_not_queue=True)
            except dbus.exceptions.NameExistsException:
                if self.options.replace is False:
                    log.critical("Another daemon is already running")
                    sys.exit(1)
                log.warning("Replacing already running daemon")
                the_other_guy = bus.get_object(APTDAEMON_DBUS_SERVICE,
                                               APTDAEMON_DBUS_PATH)
                the_other_guy.Quit(dbus_interface=APTDAEMON_DBUS_INTERFACE,
                                   timeout=300)
                time.sleep(1)
                bus_name = dbus.service.BusName(APTDAEMON_DBUS_SERVICE,
                                                bus,
                                                do_not_queue=True)
        else:
            bus_name = None
            bus_path = None
        DBusObject.__init__(self, bus_name, bus_path)
        if options.dummy:
            self.worker = DummyWorker()
        else:
            load_plugins = not options.disable_plugins
            try:
                from .worker.pkworker import AptPackageKitWorker
                self.worker = AptPackageKitWorker(options.chroot,
                                                  load_plugins)
            except:
                self.worker = AptWorker(options.chroot, load_plugins)
        self.queue = TransactionQueue(self.worker)
        self.queue.connect("queue-changed", self._on_queue_changed)
        # keep state of the last information about reboot required
        self._reboot_required = self.worker.is_reboot_required()
        log.debug("Daemon was initialized")

    def _on_queue_changed(self, queue):
        """Callback for a changed transaction queue."""
        # check for reboot required
        if self.worker.is_reboot_required() != self._reboot_required:
            self._reboot_required = self.worker.is_reboot_required()
            self.PropertyChanged("RebootRequired", self._reboot_required)
        # check for the queue
        if self.queue.worker.trans:
            current = self.queue.worker.trans.tid
        else:
            current = ""
        queued = [trans.tid for trans in self.queue.items]
        self.ActiveTransactionsChanged(current, queued)

    # pylint: disable-msg=C0103,C0322
    @dbus.service.signal(dbus_interface=APTDAEMON_DBUS_INTERFACE,
                         signature="sv")
    def PropertyChanged(self, property, value):
        """The signal gets emitted if a property of the transaction changed.

        :param property: The name of the property.
        :param value: The new value of the property.

        :type property: s
        :type value: v
        """
        log.debug("Emitting PropertyChanged: %s, %s" % (property, value))

    # pylint: disable-msg=C0103,C0322
    @dbus.service.signal(dbus_interface=APTDAEMON_DBUS_INTERFACE,
                         signature="sas")
    def ActiveTransactionsChanged(self, current, queued):
        """The currently processed or the queued transactions changed.

        :param current: The path of the currently running transaction or
            an empty string.
        :param queued: List of the ids of the queued transactions.

        :type current: s
        :type queued: as
        """
        log.debug("Emitting ActiveTransactionsChanged signal: %s, %s",
                  current, queued)

    def run(self):
        """Start the daemon and listen for calls."""
        if self.options.disable_timeout is False:
            log.debug("Using inactivity check")
            GLib.timeout_add_seconds(APTDAEMON_IDLE_CHECK_INTERVAL,
                                     self._check_for_inactivity)
        log.debug("Waiting for calls")
        try:
            mainloop.run()
        except KeyboardInterrupt:
            self.Quit(None)

    @inline_callbacks
    def _create_trans(self, role, sender, packages=None, kwargs=None):
        """Helper method which returns the tid of a new transaction."""
        pid, uid, gid, cmdline = (
            yield policykit1.get_proc_info_from_dbus_name(sender, self.bus))
        tid = uuid.uuid4().hex
        trans = Transaction(
            tid, role, self.queue, pid, uid, gid, cmdline, sender,
            packages=packages, kwargs=kwargs, bus=self.bus)
        self.queue.limbo[trans.tid] = trans
        return_value(trans.tid)

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="", out_signature="s",
                          sender_keyword="sender")
    def FixIncompleteInstall(self, sender):
        """Try to complete cancelled installations. This is equivalent to a
        call of ``dpkg --configure -a``.

        Requires the ``org.debian.apt.install-or-remove-packages``
        :ref:`PolicyKit privilege <policykit>`.

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("FixIncompleteInstall() called")
        return self._create_trans(enums.ROLE_FIX_INCOMPLETE_INSTALL, sender)

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="", out_signature="s",
                          sender_keyword="sender")
    def FixBrokenDepends(self, sender):
        """Try to resolve unsatisfied dependencies of installed packages.

        Requires the ``org.debian.apt.install-or-remove-packages``
        :ref:`PolicyKit privilege <policykit>`.

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("FixBrokenDepends() called")
        return self._create_trans(enums.ROLE_FIX_BROKEN_DEPENDS, sender)

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="", out_signature="s",
                          sender_keyword="sender")
    def UpdateCache(self, sender):
        """Download the latest information about available packages from the
        repositories and rebuild the package cache.

        Requires the ``org.debian.apt.update-cache``
        :ref:`PolicyKit privilege <policykit>`.

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("UpdateCache() was called")
        kwargs = {"sources_list": None}
        return self._create_trans(enums.ROLE_UPDATE_CACHE, sender,
                                  kwargs=kwargs)

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="s", out_signature="s",
                          sender_keyword="sender")
    def UpdateCachePartially(self, sources_list, sender):
        """Update the cache from the repositories defined in the given
        sources.list only.

        Requires the ``org.debian.apt.update-cache``
        :ref:`PolicyKit privilege <policykit>`.

        :param sources_list: The absolute path to a sources.list, e.g.
            :file:`/etc/apt/sources.list.d/ppa-aptdaemon.list` or the name
            of the snippet in :file:`/etc/apt/sources.list.d/`, e.g.
            :file:`ppa-aptdaemon.list`.
        :type sources_list: s

        :returns: The D-Bus path of the new transaction object which
            performs this action.
         """
        log.info("UpdateCachePartially() was called")
        kwargs = {"sources_list": sources_list}
        return self._create_trans(enums.ROLE_UPDATE_CACHE, sender,
                                  kwargs=kwargs)

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="as", out_signature="s",
                          sender_keyword="sender")
    def RemovePackages(self, package_names, sender):
        """Remove the given packages from the system. The configuration files
        will be kept by default. Use :func:`CommitPackages()` to also purge the
        configuration files.

        Requires the ``org.debian.apt.install-or-packages``
        :ref:`PolicyKit privilege <policykit>`.

        :param package_names: packages to be removed
        :type package_names: as

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("RemovePackages() was called: '%s'", package_names)
        self._check_package_names(package_names)
        return self._create_trans(enums.ROLE_REMOVE_PACKAGES, sender,
                                  packages=([], [], package_names, [], [], []))

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="b", out_signature="s",
                          sender_keyword="sender")
    def UpgradeSystem(self, safe_mode, sender):
        """Apply all available upgrades and try to resolve conflicts.

        Requires the ``org.debian.apt.upgrade-packages``
        :ref:`PolicyKit privilege <policykit>`.

        :param safe_mode: If True only already installed packages will be
            updated. Updates which require to remove installed packages or to
            install additional packages will be skipped.

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("UpgradeSystem() was called with safe mode: "
                 "%s" % safe_mode)
        return self._create_trans(enums.ROLE_UPGRADE_SYSTEM, sender,
                                  kwargs={"safe_mode": safe_mode})

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="asasasasasas", out_signature="s",
                          sender_keyword="sender")
    def CommitPackages(self, install, reinstall, remove, purge, upgrade,
                       downgrade, sender):
        """Perform several package changes at the same time.

        The version number and target release of the packages can be specified
        using the traditional apt-get syntax, e.g. "xterm=281.1" to force
        installing the version 281.1 of xterm or "xterm/experimental" to
        force installing xterm from the experimental release.

        Requires the ``org.debian.apt.install-or-remove-packages``
        :ref:`PolicyKit privilege <policykit>`.

        :param install: Packages to be installed.
        :param reinstall: Packages to be re-installed
        :param remove: Packages to be removed
        :param purge: Package to be removed including theirs configuration
            files.
        :param upgrade: Packages to be upgraded.
        :param downgrade: Packages to be downgraded. You
            have to append the target version to the package name separated
            by "="

        :type install: as
        :type reinstall: as
        :type remove: as
        :type purge: as
        :type upgrade: as
        :type downgrade: as

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        # FIXME: take sha1 or md5 cash into accout to allow selecting a version
        #       or an origin different from the candidate
        log.info("CommitPackages() was called: %s, %s, %s, %s, %s, %s",
                 install, reinstall, remove, purge, upgrade, downgrade)

        def check_empty_list(lst):
            if lst == [""]:
                return []
            else:
                return lst
        packages_lst = [check_empty_list(lst) for lst in [install, reinstall,
                                                          remove, purge,
                                                          upgrade,
                                                          downgrade]]
        for packages in packages_lst:
            self._check_package_names(packages)
        return self._create_trans(enums.ROLE_COMMIT_PACKAGES, sender,
                                  packages=packages_lst)

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="as", out_signature="s",
                          sender_keyword="sender")
    def InstallPackages(self, package_names, sender):
        """Fetch and install the given packages from the repositories.

        The version number and target release of the packages can be specified
        using the traditional apt-get syntax, e.g. "xterm=281.1" to force
        installing the version 281.1 of xterm or "xterm/experimental" to
        force installing xterm from the experimental release.

        Requires the ``org.debian.apt.install-or-remove-packages``
        :ref:`PolicyKit privilege <policykit>`.

        :param package_names: Packages to be upgraded
        :type package_names: as

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("InstallPackages() was called: %s" % package_names)
        self._check_package_names(package_names)
        return self._create_trans(enums.ROLE_INSTALL_PACKAGES, sender,
                                  packages=(package_names, [], [], [], [], []))

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="as", out_signature="s",
                          sender_keyword="sender")
    def UpgradePackages(self, package_names, sender):
        """Upgrade the given packages to their latest version.

        The version number and target release of the packages can be specified
        using the traditional apt-get syntax, e.g. "xterm=281.1" to force
        installing the version 281.1 of xterm or "xterm/experimental" to
        force installing xterm from the experimental release.

        Requires the ``org.debian.apt.upgrade-packages``
        :ref:`PolicyKit privilege <policykit>`.

        :param package_names: Packages to be upgraded
        :type package_names: as

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("UpgradePackages() was called: %s" % package_names)
        self._check_package_names(package_names)
        return self._create_trans(enums.ROLE_UPGRADE_PACKAGES, sender,
                                  packages=([], [], [], [], package_names, []))

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="ss", out_signature="s",
                          sender_keyword="sender")
    def AddVendorKeyFromKeyserver(self, keyid, keyserver, sender):
        """Download and install the key of a software vendor. The key is
        used to authenticate packages of the vendor.

        Requires the ``org.debian.apt.change-repositories``
        :ref:`PolicyKit privilege <policykit>`.

        :param keyid: The id of the GnuPG key (e.g. 0x0EB12F05)
        :param keyserver: The server to get the key from (e.g.
            keyserver.ubuntu.com)

        :type keyid: s
        :type keyserver: s

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("InstallVendorKeyFromKeyserver() was called: %s %s",
                 keyid, keyserver)
        return self._create_trans(enums.ROLE_ADD_VENDOR_KEY_FROM_KEYSERVER,
                                  sender, kwargs={"keyid": keyid,
                                                  "keyserver": keyserver})

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="s", out_signature="s",
                          sender_keyword="sender")
    def AddVendorKeyFromFile(self, path, sender):
        """Install the key file of a software vendor. The key is
        used to authenticate packages of the vendor.

        Requires the ``org.debian.apt.change-repositories``
        :ref:`PolicyKit privilege <policykit>`.

        :param path: The absolute path to the key file.
        :type path: s

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("InstallVendorKeyFile() was called: %s" % path)
        return self._create_trans(enums.ROLE_ADD_VENDOR_KEY_FILE,
                                  sender, kwargs={"path": path})

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="s", out_signature="s",
                          sender_keyword="sender")
    def RemoveVendorKey(self, fingerprint, sender):
        """Remove the given key of a software vendor. The key is used to
        authenticate packages of the vendor.

        Requires the ``org.debian.apt.change-repositories``
        :ref:`PolicyKit privilege <policykit>`.

        :param fingerprint: The fingerprint of the key.
        :type fingerprint: s

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("RemoveVendorKey() was called: %s" % fingerprint)
        return self._create_trans(enums.ROLE_REMOVE_VENDOR_KEY,
                                  sender, kwargs={"fingerprint": fingerprint})

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="sb", out_signature="s",
                          sender_keyword="sender")
    def InstallFile(self, path, force, sender):
        """Install the given local package file.

        Requires the ``org.debian.apt.install-file``
        :ref:`PolicyKit privilege <policykit>`.

        :param path: The absolute path to the package file.
        :param force: If the installation of a package which violates the
            Debian/Ubuntu policy should be forced.

        :type path: s
        :type force: b

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("InstallFile() was called: %s" % path)
        # FIXME: Perform some checks
        # FIXME: Should we already extract the package name here?
        return self._create_trans(enums.ROLE_INSTALL_FILE,
                                  sender, kwargs={"path": path,
                                                  "force": force})

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="", out_signature="s",
                          sender_keyword="sender")
    def Clean(self, sender):
        """Remove downloaded package files.

        Requires the ``org.debian.apt.clean``
        :ref:`PolicyKit privilege <policykit>`.

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("Clean() was called")
        return self._create_trans(enums.ROLE_CLEAN, sender)

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="ass", out_signature="s",
                          sender_keyword="sender")
    def Reconfigure(self, packages, priority, sender):
        """Reconfigure already installed packages.

        Requires the ``org.debian.apt.install-or-remove-packages``
        :ref:`PolicyKit privilege <policykit>`.

        :param packages: List of package names which should be reconfigure.
        :param priority: The minimum debconf priority of question to be
            displayed. Can be of value "low", "medium", "high", "critical",
            "default".

        :type packages: as
        :type priority: s

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("Reconfigure() was called: %s" % " ".join(packages))
        return self._create_trans(enums.ROLE_RECONFIGURE, sender,
                                  packages=[[], packages, [], [], [], []],
                                  kwargs={"priority": priority})

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="sssasss", out_signature="s",
                          sender_keyword="sender")
    def AddRepository(self, src_type, uri, dist, comps, comment, sourcesfile,
                      sender):
        """Add given repository to the sources list.

        Requires the ``org.debian.apt.change-repositories``
        :ref:`PolicyKit privilege <policykit>`.

        :param src_type: The type of the repository (deb, deb-src).
        :param uri: The main repository URI
            (e.g. http://archive.ubuntu.com/ubuntu)
        :param dist: The distribution to use (e.g. stable or lenny-backports).
        :param comps: List of components (e.g. main, restricted).
        :param comment: A comment which should be added to the sources.list.
        :param sourcesfile: (Optoinal) filename in sources.list.d.

        :type src_type: s
        :type uri: s
        :type dist: s
        :type comps: as
        :type comment: s
        :type sourcesfile: s

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("AddRepository() was called: type='%s' uri='%s' "
                 "dist='%s' comps='%s' comment='%s' sourcesfile='%s'",
                 src_type, uri, dist, comps, comment, sourcesfile)
        return self._create_trans(enums.ROLE_ADD_REPOSITORY, sender,
                                  kwargs={"src_type": src_type, "uri": uri,
                                          "dist": dist, "comps": comps,
                                          "comment": comment,
                                          "sourcesfile": sourcesfile})

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="s", out_signature="s",
                          sender_keyword="sender")
    def EnableDistroComponent(self, component, sender):
        """Enable the component in the distribution repositories. This will
        not affect third-party repositories.

        The repositories of a distribution are often separated into
        different components because of policy reasons. E.g. Debian uses main
        for DFSG-free software and non-free for re-distributable but not free
        in the sense of the Debian Free Software Guidelines.

        Requires the ``org.debian.apt.change-repositories``
        :ref:`PolicyKit privilege <policykit>`.

        :param component: The component, e,g, main or non-free.
        :type component: s
        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("EnableComponent() was called: component='%s' ", component)
        return self._create_trans(enums.ROLE_ENABLE_DISTRO_COMP, sender,
                                  kwargs={"component": component})

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="", out_signature="as",
                          sender_keyword="sender")
    def GetTrustedVendorKeys(self, sender):
        """Get the list of the installed vendor keys which are used to
        authenticate packages.

        Requires the ``org.debian.apt.get-trusted-vendor-keys``
        :ref:`PolicyKit privilege <policykit>`.

        :returns: Fingerprints of all installed keys.
        """
        log.info("GetTrustedVendorKeys() was called")
        return self._get_trusted_vendor_keys(sender)

    @inline_callbacks
    def _get_trusted_vendor_keys(self, sender):
        action = policykit1.PK_ACTION_GET_TRUSTED_VENDOR_KEYS
        yield policykit1.check_authorization_by_name(sender, action,
                                                     bus=self.bus)
        fingerprints = self.worker.get_trusted_vendor_keys()
        return_value(fingerprints)

    # pylint: disable-msg=C0103,C0322
    @dbus.service.method(APTDAEMON_DBUS_INTERFACE,
                         in_signature="", out_signature="sas")
    def GetActiveTransactions(self):
        """Return the currently running transaction and the list of queued
        transactions.
        """
        log.debug("GetActiveTransactions() was called")
        queued = [trans.tid for trans in self.queue.items]
        if self.queue.worker.trans:
            current = self.queue.worker.trans.tid
        else:
            current = ""
        return current, queued

    # pylint: disable-msg=C0103,C0322
    @dbus.service.method(APTDAEMON_DBUS_INTERFACE,
                         in_signature="", out_signature="",
                         sender_keyword="caller_name")
    def Quit(self, caller_name):
        """Request a shutdown of the daemon."""
        log.info("Quitting was requested")
        log.debug("Quitting main loop...")
        mainloop.quit()
        log.debug("Exit")

    # pylint: disable-msg=C0103,C0322
    @dbus_deferred_method(APTDAEMON_DBUS_INTERFACE,
                          in_signature="sss", out_signature="s",
                          sender_keyword="sender")
    def AddLicenseKey(self, pkg_name, json_token, server_name, sender):
        """Install a license key to use a piece of proprietary software.

        Requires the ``org.debian.apt.install-or-remove-packages``
        :ref:`PolicyKit privilege <policykit>`.

        :param pkg_name: The name of the package which requires the license
        :type pkg_name: s
        :param json_token: The oauth token to use with the server in
            json format
        :type pkg_name: s
        :param server_name: The name of the server to use (ubuntu-production,
            ubuntu-staging)
        :type pkg_name: s

        :returns: The D-Bus path of the new transaction object which
            performs this action.
        """
        log.info("AddLicenseKey() was called")
        return self._create_trans(enums.ROLE_ADD_LICENSE_KEY, sender,
                                  kwargs={'pkg_name': pkg_name,
                                          'json_token': json_token,
                                          'server_name': server_name})

    @inline_callbacks
    def _set_property(self, iface, name, value, sender):
        """Helper to set a property on the properties D-Bus interface."""
        action = policykit1.PK_ACTION_CHANGE_CONFIG
        yield policykit1.check_authorization_by_name(sender, action,
                                                     bus=self.bus)
        if iface == APTDAEMON_DBUS_INTERFACE:
            if name == "PopConParticipation":
                self.worker.set_config(name, dbus.Boolean(value))
            elif name == "AutoUpdateInterval":
                self.worker.set_config(name, dbus.Int32(value), "10periodic")
            elif name == "AutoDownload":
                self.worker.set_config(name, dbus.Boolean(value), "10periodic")
            elif name == "AutoCleanInterval":
                self.worker.set_config(name, dbus.Int32(value), "10periodic")
            elif name == "UnattendedUpgrade":
                self.worker.set_config(name, dbus.Boolean(value), "10periodic")
            else:
                raise dbus.exceptions.DBusException("Unknown or read only "
                                                    "property: %s" % name)
        else:
            raise dbus.exceptions.DBusException("Unknown interface: %s" %
                                                iface)

    def _check_package_names(self, pkg_names):
        """Check if the package names are valid. Otherwise raise an
        exception.
        """
        for fullname in pkg_names:
            name, version, release = split_package_id(fullname)
            name, sep, auto_flag = name.partition("#")
            if not auto_flag in ("", "auto"):
                raise errors.AptDaemonError("%s isn't a valid flag" %
                                            auto_flag)
            if not re.match(REGEX_VALID_PACKAGENAME, name):
                raise errors.AptDaemonError("%s isn't a valid package name" %
                                            name)
            if (version is not None and
                    not re.match(REGEX_VALID_VERSION, version)):
                raise errors.AptDaemonError("%s isn't a valid version" %
                                            version)
            if (release is not None and
                    not re.match(REGEX_VALID_RELEASE, release)):
                raise errors.AptDaemonError("%s isn't a valid release" %
                                            release)

    def _get_properties(self, iface):
        """Helper get the properties of a D-Bus interface."""
        if iface == APTDAEMON_DBUS_INTERFACE:
            return {
                "AutoUpdateInterval": dbus.Int32(
                    self.worker.get_config("AutoUpdateInterval")),
                "AutoDownload": dbus.Boolean(
                    self.worker.get_config("AutoDownload")),
                "AutoCleanInterval": dbus.Int32(
                    self.worker.get_config("AutoCleanInterval")),
                "UnattendedUpgrade": dbus.Int32(
                    self.worker.get_config("UnattendedUpgrade")),
                "PopConParticipation": dbus.Boolean(
                    self.worker.get_config("PopConParticipation")),
                "RebootRequired": dbus.Boolean(
                    self.worker.is_reboot_required())}
        else:
            return {}

    def _sigquit(self, data):
        """Internal callback for the quit signal."""
        self.Quit(None)

    def _check_for_inactivity(self):
        """Shutdown the daemon if it has been inactive for time specified
        in APTDAEMON_IDLE_TIMEOUT.
        """
        log.debug("Checking for inactivity")
        timestamp = self.queue.worker.last_action_timestamp
        if (not self.queue.worker.trans and
                not GLib.main_context_default().pending() and
                time.time() - timestamp > APTDAEMON_IDLE_TIMEOUT and
                not self.queue):
            log.info("Quitting due to inactivity")
            self.Quit(None)
            return False
        return True


def get_dbus_string(text, encoding="UTF-8"):
    """Convert the given string or unicode object to a dbus.String."""
    try:
        return dbus.String(text)
    except UnicodeDecodeError:
        return dbus.String(text.decode(encoding, "ignore"))


def main():
    """Allow to run the daemon from the command line."""
    parser = OptionParser()
    parser.add_option("-t", "--disable-timeout",
                      default=False,
                      action="store_true", dest="disable_timeout",
                      help=_("Do not shutdown the daemon because of "
                             "inactivity"))
    parser.add_option("", "--disable-plugins",
                      default=False,
                      action="store_true", dest="disable_plugins",
                      help=_("Do not load any plugins"))
    parser.add_option("-d", "--debug",
                      default=False,
                      action="store_true", dest="debug",
                      help=_("Show internal processing "
                             "information"))
    parser.add_option("-r", "--replace",
                      default=False,
                      action="store_true", dest="replace",
                      help=_("Quit and replace an already running "
                             "daemon"))
    parser.add_option("", "--session-bus",
                      default=False,
                      action="store_true", dest="session_bus",
                      help=_("Listen on the DBus session bus (Only required "
                             "for testing"))
    parser.add_option("", "--chroot", default=None,
                      action="store", type="string", dest="chroot",
                      help=_("Perform operations in the given "
                             "chroot"))
    parser.add_option("-p", "--profile",
                      default=False,
                      action="store", type="string", dest="profile",
                      help=_("Store profile stats in the specified "
                             "file"))
    parser.add_option("--dummy",
                      default=False,
                      action="store_true", dest="dummy",
                      help=_("Do not make any changes to the system (Only "
                             "of use to developers)"))
    options, args = parser.parse_args()
    if options.debug is True:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
        _console_handler.setLevel(logging.INFO)
    if options.session_bus:
        bus = dbus.SessionBus()
    else:
        bus = None
    daemon = AptDaemon(options, bus=bus)
    if options.profile:
        import profile
        profiler = profile.Profile()
        profiler.runcall(daemon.run)
        profiler.dump_stats(options.profile)
        profiler.print_stats()
    else:
        daemon.run()

# vim:ts=4:sw=4:et
