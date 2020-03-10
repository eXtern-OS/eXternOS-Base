#!/usr/bin/python
"""
The module provides a client to the PackageKit DBus interface. It allows to
perform basic package manipulation tasks in a cross distribution way, e.g.
to search for packages, install packages or codecs.
"""
# Copyright (C) 2008 Canonical Ltd.
# Copyright (C) 2008 Aidan Skinner <aidan@skinner.me.uk>
# Copyright (C) 2008 Martin Pitt <martin.pitt@ubuntu.com>
# Copyright (C) 2008 Tim Lauridsen <timlau@fedoraproject.org>
# Copyright (C) 2008-2009 Sebastian Heinlein <devel@glatzor.de>
#
# Licensed under the GNU General Public License Version 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import locale
import os.path
import shutil
import weakref
import sys

import dbus
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

from gi.repository import GObject, GLib

from . import enums
from . import debconf
import defer
from defer.utils import deferable
from .errors import convert_dbus_exception, TransactionFailed

__all__ = ("AptTransaction", "AptClient", "get_transaction", "get_aptdaemon")


# the default timeout for dbus method calls
_APTDAEMON_DBUS_TIMEOUT = 86400


class AptTransaction(GObject.Object):

    """Represents an aptdaemon transaction.

    .. note:: This class cannot be inherited since it makes use of
              a metaclass.

    .. signal:: allow-unauthenticated -> allow

        The signal is emitted when :attr:`allow_unauthenticated` changed.

        :param allow: If unauthenticated packages are allowed to be installed.

    .. signal:: cancellable-changed -> cancellable

        The signal is emitted when :attr:`cancellable` changed.

        :param cancellable: If the transaction can be cancelled now.

    .. signal:: config-file-conflict -> cur, new

        The signal is emitted when :attr:`config_file_conflict` changed.

        :param cur: The path to the current configuration file.
        :param new: The path to the new configuration file.

    .. signal:: debconf-socket-changed -> path

        The signal is emitted when :attr:`debconf_socket` changed.

        :param path: The path to the socket which will be used to forward
            debconf communication to the user session.

    .. signal:: dependencies-changed -> installs, re-installs, removals, \
                                        purges, upgrades, downgrades, kepts

        The signal is emitted when :attr:`dependencies` changed.

        Most likely after :meth:`simulate()` was called.

        :param installs: List of package which will be installed.
        :param reinstalls: List of package which will be re-installed.
        :param removals: List of package which will be removed,
        :param purges: List of package which will be removed including
            configuration files.
        :param upgrades: List of package which will be upgraded.
        :param downgrades: List of package which will be downgraded to an older
            version.
        :param kepts: List of package which will be skipped from upgrading.

    .. signal:: download-changed -> download

        The signal is emitted when :attr:`download` changed.

        :param download: Download size integer in Bytes.

    .. signal:: error -> error_code, error_details

        The signal is emitted when an error occured.

        :param error_code: The error code enumeration, e.g.
             :data:`aptdaemon.enums.ERROR_NO_CACHE`.
        :param error_details: The error description string.

    .. signal:: finished -> exit_state

        The signal is emitted when the transaction is completed or has
        failed.

        :param exit_state: The exit status enumeration string.

    .. signal:: http-proxy-changed -> uri

        The signal is emitted when :attr:`http_proxy` changed.

        :param uri: The URI of the proxy server, e.g. "http://proxy:8080".

    .. signal:: locale-changed -> locale

        The signal is emitted when :attr:`locale` changed.

        :param locale: The language which should be used for messages,
            eg. "de_DE".

    .. signal:: meta-data-changed -> meta_data

        The signal is emitted when :attr:`meta_data` changed.

        :param meta_data: The latest meta data dictionary.

    .. signal:: medium-required -> name, device

        The signal is emitted when :attr:`required_medium` changed.

        :param name: The name of the volume.
        :param device: The path of the device in which the volume should
            be inserted.

    .. signal:: remove-obsoleted-depends-changed -> remove

        The signal is emitted when :attr:`remove_obsoleted_depends` changed.

        :param remove: If obsolete dependencies should also be removed.

    .. signal:: role-changed -> role

        The signal is emitted when :attr:`role` changed.

        :param role: The new role enum, e.g.
            :data:`~aptdaemon.enums.ROLE_UPDATE_CACHE`.

    .. signal:: space-changed -> space

        The signal is emitted when :attr:`space` changed.
        Most likely after :meth:`simulate()` was called.

        :param space: Required disk space integer in Bytes. Can be negative
            if disk space will be freed.

    .. signal:: packages-changed -> installs, re-installs, removals, \
                                    purges, upgrades, downgrades

        The signal is emitted when :attr:`packages` changed.

        :param installs: List of package which will be installed.
        :param reinstalls: List of package which will be re-installed.
        :param removals: List of package which will be removed,
        :param purges: List of package which will be removed including
            configuration files.
        :param upgrades: List of package which will be upgraded.
        :param downgrades: List of package which will be downgraded to an older
            version.

    .. signal:: paused

        The signal is emitted when the transaction was paused.
        See :attr:`paused` and :sig:`resumed`.

    .. signal:: progress-changed -> progress

        The signal is emitted when :attr:`progress` changed.

        :param progress: The progress integer.

    .. signal:: progress-details-changed -> current_items, total_items, \
                                            currenty_bytes, total_bytes, \
                                            current_cps, eta

        The signal is emitted when detailed information of the progress
        is available.

        :param current_items: The number of already processed items.
        :param total_items: The number of all items.
        :param current_bytes: The number of already downloaded byte.
        :param total_bytes: The number of bytes which have to be downloaded
            totally.
        :param current_cps: The current download speed in bytes per second.
        :param eta: The elapsed time in seconds to accomplish the task.

    .. signal:: progress-download-changed -> uri, short_desc, total_size, \
                                             current_size, msg

        The signal is emitted when progress information about a single
        download is available.

        :param uri: The URI of the file which is downloaded.
        :param status: The status of the downloade, e.g.
            :data:`~aptdaemon.enums.DOWNLOAD_AUTH_FAILED`.
        :param short_desc: A short description of the file.
        :param total_size: The size of the file in Bytes.
        :param current_size: How much of the file in Bytes has already be
            downloaded.
        :param msg: The status or error description.

    .. signal:: resumed

        The signal is emitted when a paused transaction was resumed.
        See :attr:`paused` and :sig:`paused`.

    .. signal:: terminal-changed -> path

        The signal is emitted when :attr:`terminal` changed.

        :param path: The path to the slave end of the controlling terminal
            for the underlying dpkg call.

    .. signal:: terminal-attached-changed -> attached

        The signal is emitted when :attr:`term_attached` changed.

        :param attached: If the controlling terminal can be used.

    .. signal:: unauthenticated-changed -> unauthenticated

        The signal is emitted when :attr:`unauthenticated` changed.

        :param unauthenticated: List of unauthenticated packages.

    .. attribute:: cancellable

        If the transaction can be currently cancelled.

    .. attribute:: config_file_conflict

        If there is a conflict in the configuration file handling during
        an installation this attribute contains a tuple of the path to the
        current and the new temporary configuration file.

        The :meth:`resolve_config_file_conflict()` can be used to
        resolve the conflict and continue the processing of the
        transaction.

    .. attribute:: dependencies

        List of dependencies lists in the following order: packages to
        install, to re-install, to remove, to purge, to upgrade,
        to downgrade and to keep.

        You have to call :meth:`simulate()` to calculate the
        dependencies before the transaction will be executed.

    .. attribute:: download

        The number of Bytes which have to be downloaed.

        You have to call :meth:`simulate()` to calculate the
        download size before the transaction will be executed.

    .. attribute:: error

        In the case of a failed transaction this attribute holds the
        corresponding :exc:`errors.TransactionFailed` instance.

    .. attribute:: error_code

        In the case of a failed transaction this attribute is set to the
        underlying error code, e.g.
        :data:`enums.ERROR_PACKAGE_DOWNLOAD_FAILED`.

    .. attribute:: error_details

        In the case of a failed transaction this attribute contains a
        detailed error message in the language of the transaction.

    .. attribute:: exit

        Contains the exit status enum if the transaction has been completed,
        e.g. :data:`enums.EXIT_SUCCESS` or :data:`enums.EXIT_FAILED`.

    .. attribute:: http_proxy

        The URI to the http proxy server which should be used only for this
        transaction, e.g. "http://proxy:8080". It is recommended to set
        the system wide proxy server instead of setting this attribute
        for every transaction.

        See :meth:`set_http_proxy()`.

    .. attribute:: meta_data

        Dictionary of optional meta data which can be set by client
        applications. See :meth:`set_meta_data()`.

    .. attribute:: packages

       List of package lists which will be explicitly changed in the
       following order: packages to install, to re-install, to remove,
       to purge, to upgrade, to downgrade.

    .. attribute:: paused

        If the transaction is currently paused, e.g. it is required to
        insert a medium to install from.

    .. attribute:: progress

        An integer ranging from 0 to 101 to describe the progress of the
        transaction.

        .. note:: A value of 101 indicates that there cannot be made any
                  assumptions on the progress of the transaction.

    .. attribute:: remove_obsoleted_depends

        If dependencies which have been required by a removed package only
        should be removed, too.

    .. attribute:: required_medium

        If a medium should be inserted to continue the fetch phase of a
        transaction, this attribute contains a tuple of the device path of
        of the drive which should be used and secondly of the name of the
        medium.

        The :func:`provide_medium()` method should be used to notify aptdaemon
        about an inserted medium and to continue processing the transaction.

    .. attribute:: role

        The kind of action which is performed by the transaction, e.g.
        :data:`enums.ROLE_UPGRADE_SYSTEM`.

    .. attribute:: space

        The required disk space in Bytes. Will be negative if space is
        freed.

        You have to call :meth:`simulate()` to calculate the
        download size before the transaction will be executed.

    .. attribute:: status

        The enum of the current status, e.g.
        :data:`enums.STATUS_DOWNLOADING`.

    .. attribute:: status_details

        A string describing the current status of the transaction.

    .. attribute:: tid

        The unique identifier of the transaction. It is also the D-Bus path
        of the corresponding transaction object.

    .. attribute:: term_attached

        If the the package manager can be controlled using the controlling
        terminal specified by :func:`set_terminal()`.

    .. attribute:: unauthenticated

        List of packages which are going to be installed but are not
        downloaded from an authenticated repository.

        You have to call :meth:`simulate()` to calculate the
        dependencies before the transaction will be executed.
    """

    __gsignals__ = {"finished": (GObject.SIGNAL_RUN_FIRST,
                                 GObject.TYPE_NONE,
                                 (GObject.TYPE_STRING,)),
                    "dependencies-changed": (GObject.SIGNAL_RUN_FIRST,
                                             GObject.TYPE_NONE,
                                             (GObject.TYPE_PYOBJECT,
                                              GObject.TYPE_PYOBJECT,
                                              GObject.TYPE_PYOBJECT,
                                              GObject.TYPE_PYOBJECT,
                                              GObject.TYPE_PYOBJECT,
                                              GObject.TYPE_PYOBJECT,
                                              GObject.TYPE_PYOBJECT)),
                    "download-changed": (GObject.SIGNAL_RUN_FIRST,
                                         GObject.TYPE_NONE,
                                         (GObject.TYPE_INT64,)),
                    "space-changed": (GObject.SIGNAL_RUN_FIRST,
                                      GObject.TYPE_NONE,
                                      (GObject.TYPE_INT64,)),
                    "error": (GObject.SIGNAL_RUN_FIRST,
                              GObject.TYPE_NONE,
                              (GObject.TYPE_STRING, GObject.TYPE_STRING)),
                    "role-changed": (GObject.SIGNAL_RUN_FIRST,
                                     GObject.TYPE_NONE,
                                     (GObject.TYPE_STRING,)),
                    "terminal-attached-changed": (GObject.SIGNAL_RUN_FIRST,
                                                  GObject.TYPE_NONE,
                                                  (GObject.TYPE_BOOLEAN,)),
                    "cancellable-changed": (GObject.SIGNAL_RUN_FIRST,
                                            GObject.TYPE_NONE,
                                            (GObject.TYPE_BOOLEAN,)),
                    "meta-data-changed": (GObject.SIGNAL_RUN_FIRST,
                                          GObject.TYPE_NONE,
                                          (GObject.TYPE_PYOBJECT,)),
                    "status-changed": (GObject.SIGNAL_RUN_FIRST,
                                       GObject.TYPE_NONE,
                                       (GObject.TYPE_STRING,)),
                    "status-details-changed": (GObject.SIGNAL_RUN_FIRST,
                                               GObject.TYPE_NONE,
                                               (GObject.TYPE_STRING,)),
                    "progress-changed": (GObject.SIGNAL_RUN_FIRST,
                                         GObject.TYPE_NONE,
                                         (GObject.TYPE_INT,)),
                    "progress-details-changed": (GObject.SIGNAL_RUN_FIRST,
                                                 GObject.TYPE_NONE,
                                                 (GObject.TYPE_INT,
                                                  GObject.TYPE_INT,
                                                  GObject.TYPE_INT64,
                                                  GObject.TYPE_INT64,
                                                  GObject.TYPE_INT,
                                                  GObject.TYPE_INT64)),
                    "progress-download-changed": (GObject.SIGNAL_RUN_FIRST,
                                                  GObject.TYPE_NONE,
                                                  (GObject.TYPE_STRING,
                                                   GObject.TYPE_STRING,
                                                   GObject.TYPE_STRING,
                                                   GObject.TYPE_INT64,
                                                   GObject.TYPE_INT64,
                                                   GObject.TYPE_STRING)),
                    "packages-changed": (GObject.SIGNAL_RUN_FIRST,
                                         GObject.TYPE_NONE,
                                         (GObject.TYPE_PYOBJECT,
                                          GObject.TYPE_PYOBJECT,
                                          GObject.TYPE_PYOBJECT,
                                          GObject.TYPE_PYOBJECT,
                                          GObject.TYPE_PYOBJECT,
                                          GObject.TYPE_PYOBJECT)),
                    "unauthenticated-changed": (GObject.SIGNAL_RUN_FIRST,
                                                GObject.TYPE_NONE,
                                                (GObject.TYPE_PYOBJECT,)),
                    "paused": (GObject.SIGNAL_RUN_FIRST,
                               GObject.TYPE_NONE,
                               ()),
                    "resumed": (GObject.SIGNAL_RUN_FIRST,
                                GObject.TYPE_NONE,
                                ()),
                    "allow-unauthenticated-changed": (GObject.SIGNAL_RUN_FIRST,
                                                      GObject.TYPE_NONE,
                                                      (GObject.TYPE_BOOLEAN,)),
                    "remove-obsoleted-depends-changed": (
                        GObject.SIGNAL_RUN_FIRST,
                        GObject.TYPE_NONE,
                        (GObject.TYPE_BOOLEAN,)),
                    "locale-changed": (GObject.SIGNAL_RUN_FIRST,
                                       GObject.TYPE_NONE,
                                       (GObject.TYPE_STRING,)),
                    "terminal-changed": (GObject.SIGNAL_RUN_FIRST,
                                         GObject.TYPE_NONE,
                                         (GObject.TYPE_STRING,)),
                    "debconf-socket-changed": (GObject.SIGNAL_RUN_FIRST,
                                               GObject.TYPE_NONE,
                                               (GObject.TYPE_STRING,)),
                    "http-proxy-changed": (GObject.SIGNAL_RUN_FIRST,
                                           GObject.TYPE_NONE,
                                           (GObject.TYPE_STRING,)),
                    "medium-required": (GObject.SIGNAL_RUN_FIRST,
                                        GObject.TYPE_NONE,
                                        (GObject.TYPE_STRING,
                                         GObject.TYPE_STRING)),
                    "config-file-conflict": (GObject.SIGNAL_RUN_FIRST,
                                             GObject.TYPE_NONE,
                                             (GObject.TYPE_STRING,
                                              GObject.TYPE_STRING)),
                    }

    _tid_cache = weakref.WeakValueDictionary()

    def __new__(cls, tid, *args, **kwargs):
        """Cache transactions with identical tid."""
        try:
            return AptTransaction._tid_cache[tid]
        except KeyError:
            value = GObject.Object.__new__(cls, tid, *args, **kwargs)
            AptTransaction._tid_cache[tid] = value
            return value

    def __init__(self, tid, bus=None):
        GObject.GObject.__init__(self)
        self.tid = tid
        self.role = enums.ROLE_UNSET
        self.error = None
        self.error_code = None
        self.error_details = None
        self.exit = enums.EXIT_UNFINISHED
        self.cancellable = False
        self.term_attached = False
        self.required_medium = None
        self.config_file_conflict = None
        self.status = None
        self.status_details = ""
        self.progress = 0
        self.paused = False
        self.http_proxy = None
        self.dependencies = [[], [], [], [], [], [], []]
        self.packages = [[], [], [], [], []]
        self.unauthenticated = []
        self.meta_data = {}
        self.remove_obsoleted_depends = False
        self.download = 0
        self.downloads = {}
        self.space = 0
        self.locale = ""
        self._method = None
        self._args = []
        self._debconf_helper = None
        # Connect the signal handlers to the DBus iface
        if not bus:
            bus = dbus.SystemBus()
        self._proxy = bus.get_object("org.debian.apt", tid)
        self._iface = dbus.Interface(self._proxy, "org.debian.apt.transaction")
        # Watch for a crashed daemon which orphaned the dbus object
        self._owner_watcher = bus.watch_name_owner("org.debian.apt",
                                                   self._on_name_owner_changed)
        # main signals
        self._signal_matcher = \
            self._iface.connect_to_signal("PropertyChanged",
                                          self._on_property_changed)

    def _on_name_owner_changed(self, connection):
        """Fail the transaction if the daemon died."""
        if connection == "" and self.exit == enums.EXIT_UNFINISHED:
            self._on_property_changed("Error", (enums.ERROR_DAEMON_DIED,
                                                "It seems that the daemon "
                                                "died."))
            self._on_property_changed("Cancellable", False)
            self._on_property_changed("TerminalAttached", False)
            self._on_property_changed("ExitState", enums.EXIT_FAILED)

    def _on_property_changed(self, property_name, value):
        """Callback for the PropertyChanged signal."""
        if property_name == "TerminalAttached":
            self.term_attached = value
            self.emit("terminal-attached-changed", value)
        elif property_name == "Cancellable":
            self.cancellable = value
            self.emit("cancellable-changed", value)
        elif property_name == "DebconfSocket":
            self.emit("debconf-socket-changed", value)
        elif property_name == "RemoveObsoletedDepends":
            self.emit("remove-obsoleted-depends-changed", value)
            self.remove_obsoleted_depends = value
        elif property_name == "AllowUnauthenticated":
            self.emit("allow-unauthenticated-changed", value)
        elif property_name == "Terminal":
            self.emit("terminal-changed", value)
        elif property_name == "Dependencies":
            self.dependencies = value
            self.emit("dependencies-changed", *value)
        elif property_name == "Packages":
            self.packages = value
            self.emit("packages-changed", *value)
        elif property_name == "Unauthenticated":
            self.unauthenticated = value
            self.emit("unauthenticated-changed", value)
        elif property_name == "Locale":
            self.locale = value
            self.emit("locale-changed", value)
        elif property_name == "Role":
            self.role = value
            self.emit("role-changed", value)
        elif property_name == "Status":
            self.status = value
            self.emit("status-changed", value)
        elif property_name == "StatusDetails":
            self.status_details = value
            self.emit("status-details-changed", value)
        elif property_name == "ProgressDownload":
            uri, status, desc, size, download, msg = value
            if uri:
                self.downloads[uri] = (status, desc, size, download, msg)
                self.emit("progress-download-changed", *value)
        elif property_name == "Progress":
            self.progress = value
            self.emit("progress-changed", value)
        elif property_name == "ConfigFileConflict":
            self.config_file_conflict = value
            if value != ("", ""):
                self.emit("config-file-conflict", *value)
        elif property_name == "MetaData":
            self.meta_data = value
            self.emit("meta-data-changed", value)
        elif property_name == "Paused":
            self.paused = value
            if value:
                self.emit("paused")
            else:
                self.emit("resumed")
        elif property_name == "RequiredMedium":
            self.required_medium = value
            if value != ("", ""):
                self.emit("medium-required", *value)
        elif property_name == "ProgressDetails":
            self.emit("progress-details-changed", *value)
        elif property_name == "Download":
            self.download = value
            self.emit("download-changed", value)
        elif property_name == "Space":
            self.space = value
            self.emit("space-changed", value)
        elif property_name == "HttpProxy":
            self.http_proxy = value
            self.emit("http-proxy-changed", value)
        elif property_name == "Error":
            self.error_code, self.error_details = value
            if self.error_code != "":
                self.error = TransactionFailed(self.error_code,
                                               self.error_details)
                self.emit("error", *value)
        elif property_name == "ExitState":
            if value != enums.EXIT_UNFINISHED and value != self.exit:
                self.exit = value
                if self._debconf_helper:
                    self._debconf_helper.stop()
                self._disconnect_from_dbus()
                # Finally sync all properties a last time. We cannot ensure
                # that the ExitState signal is the last one, so some
                # other PropertyChanged signals could be lost, see LP#747172
                self.sync(reply_handler=self._on_final_sync_done,
                          error_handler=self._on_final_sync_done)

    def _on_final_sync_done(self, data):
        self._owner_watcher.cancel()
        self.emit("finished", self.exit)

    @deferable
    @convert_dbus_exception
    def sync(self, reply_handler=None, error_handler=None):
        """Sync the properties of the transaction with the daemon.

        This method is called automatically on the creation of the
        AptTransaction instance.

        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException
        """
        def sync_properties(prop_dict):
            for property_name, value in prop_dict.items():
                self._on_property_changed(property_name, value)
            if reply_handler:
                reply_handler(self)
        if reply_handler and error_handler:
            self._proxy.GetAll("org.debian.apt.transaction",
                               dbus_interface=dbus.PROPERTIES_IFACE,
                               reply_handler=sync_properties,
                               error_handler=error_handler)
        else:
            properties = self._proxy.GetAll(
                "org.debian.apt.transaction",
                dbus_interface=dbus.PROPERTIES_IFACE)
            sync_properties(properties)

    @deferable
    @convert_dbus_exception
    def run_after(self, transaction, reply_handler=None, error_handler=None):
        """Chain this transaction after the given one. The transaction will
        fail if the previous one fails.

        To start processing of the chain you have to call :meth:`run()`
        of the first transaction. The others will be queued after it
        automatically.

        :param transaction: An AptTransaction on which this one depends.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException
         """
        try:
            return self._iface.RunAfter(transaction.tid,
                                        error_handler=error_handler,
                                        reply_handler=reply_handler,
                                        timeout=_APTDAEMON_DBUS_TIMEOUT)
        except Exception as error:
            if error_handler:
                error_handler(error)
            else:
                raise

    @deferable
    @convert_dbus_exception
    def run(self, reply_handler=None, error_handler=None):
        """Queue the transaction for processing.

        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.TransactionFailed, dbus.DBusException
        """
        try:
            return self._iface.Run(error_handler=error_handler,
                                   reply_handler=reply_handler,
                                   timeout=_APTDAEMON_DBUS_TIMEOUT)
        except Exception as error:
            if error_handler:
                error_handler(error)
            else:
                raise

    @deferable
    @convert_dbus_exception
    def simulate(self, reply_handler=None, error_handler=None):
        """Simulate the transaction to calculate the dependencies, the
        required download size and the required disk space.

        The corresponding properties of the AptTransaction will be updated.

        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.TransactionFailed, dbus.DBusException
        """
        self._iface.Simulate(reply_handler=reply_handler,
                             error_handler=error_handler)

    @deferable
    @convert_dbus_exception
    def cancel(self, reply_handler=None, error_handler=None):
        """Cancel the running transaction.

        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.NotAuthorizedError, dbus.DBusException
        """
        self._iface.Cancel(reply_handler=reply_handler,
                           error_handler=error_handler)

    @deferable
    @convert_dbus_exception
    def set_http_proxy(self, proxy, reply_handler=None, error_handler=None):
        """Use the given http proxy for downloading packages in this
        transaction.

        :param proxy: The URL of the proxy server, e.g. "http://proxy:8080"
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.NotAuthorizedError, dbus.DBusException
            aptdaemon.errors.ForeignTransaction,
        """
        if reply_handler:
            _reply_handler = lambda: reply_handler(self)
        else:
            _reply_handler = None
        self._proxy.Set("org.debian.apt.transaction", "HttpProxy", proxy,
                        dbus_interface=dbus.PROPERTIES_IFACE,
                        reply_handler=_reply_handler,
                        error_handler=error_handler)

    @deferable
    @convert_dbus_exception
    def set_remove_obsoleted_depends(self, remove_obsoleted_depends,
                                     reply_handler=None, error_handler=None):
        """Include no longer required dependencies which have been installed
        automatically when removing packages.

        :param remove_obsoleted_depends: If obsolete dependencies should be
            also removed.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.ForeignTransaction, dbus.DBusException
        """
        if reply_handler:
            _reply_handler = lambda: reply_handler(self)
        else:
            _reply_handler = None
        self._proxy.Set("org.debian.apt.transaction",
                        "RemoveObsoletedDepends", remove_obsoleted_depends,
                        dbus_interface=dbus.PROPERTIES_IFACE,
                        reply_handler=_reply_handler,
                        error_handler=error_handler)

    @deferable
    @convert_dbus_exception
    def set_allow_unauthenticated(self, allow_unauthenticated,
                                  reply_handler=None, error_handler=None):
        """Allow to install unauthenticated packages.

        Unauthenticated packages are from the repository of a vendor whose
        key hasn't been installed. By default this is not allowed.

        :param allow_unauthenticated: If unauthenticated packages can be
            installed.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.ForeignTransaction, dbus.DBusException
        """
        if reply_handler:
            _reply_handler = lambda: reply_handler(self)
        else:
            _reply_handler = None
        self._proxy.Set("org.debian.apt.transaction",
                        "AllowUnauthenticated", allow_unauthenticated,
                        dbus_interface=dbus.PROPERTIES_IFACE,
                        reply_handler=_reply_handler,
                        error_handler=error_handler)

    @deferable
    @convert_dbus_exception
    def set_debconf_frontend(self, frontend, reply_handler=None,
                             error_handler=None):
        """Setup a debconf frontend to answer questions of the maintainer
        scripts.

        Debian allows packages to interact with the user during installation,
        configuration and removal phase via debconf. Aptdaemon forwards the
        communication to a debconf instance running as the user of the
        client application.

        :param frontend: The name of the debconf frontend which should be
            launched, e.g. gnome or kde. Defaults to gnome.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.ForeignTransaction, dbus.DBusException
         """
        if reply_handler:
            _reply_handler = lambda: reply_handler(self)
        else:
            _reply_handler = None
        self._debconf_helper = debconf.DebconfProxy(frontend)
        self._proxy.Set("org.debian.apt.transaction", "DebconfSocket",
                        self._debconf_helper.socket_path,
                        dbus_interface=dbus.PROPERTIES_IFACE,
                        reply_handler=_reply_handler,
                        error_handler=error_handler)
        self._debconf_helper.start()

    @deferable
    @convert_dbus_exception
    def set_meta_data(self, **kwargs):
        """Store additional meta information of the transaction in the
        MetaData property of the transaction.

        The method accepts key=value pairs. The key has to be prefixed with
        an underscore separated identifier of the client application.

        In the following example Software-Center sets an application name
        and icon:

        >>> Transaction.set_meta_data(sc_icon="shiny", sc_app="xterm")

        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.ForeignTransaction, dbus.DBusException
        """
        reply_handler = kwargs.pop("reply_handler", None)
        error_handler = kwargs.pop("error_handler", None)
        if reply_handler:
            _reply_handler = lambda: reply_handler(self)
        else:
            _reply_handler = None
        meta_data = dbus.Dictionary(kwargs, signature="sv")
        self._proxy.Set("org.debian.apt.transaction", "MetaData", meta_data,
                        dbus_interface=dbus.PROPERTIES_IFACE,
                        reply_handler=_reply_handler,
                        error_handler=error_handler)

    @deferable
    @convert_dbus_exception
    def set_terminal(self, ttyname, reply_handler=None, error_handler=None):
        """Allow to set a controlling terminal for the underlying dpkg call.

        See the source code of gtk3widgets.AptTerminal or console.ConsoleClient
        as example.

        >>> master, slave = pty.openpty()
        >>> transaction.set_terminal(os.ttyname(slave))

        :param terminal: The slave end of a tty.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.ForeignTransaction, dbus.DBusException
        """
        if reply_handler:
            _reply_handler = lambda: reply_handler(self)
        else:
            _reply_handler = None
        self._proxy.Set("org.debian.apt.transaction", "Terminal", ttyname,
                        dbus_interface=dbus.PROPERTIES_IFACE,
                        reply_handler=_reply_handler,
                        error_handler=error_handler)

    def _disconnect_from_dbus(self):
        """Stop monitoring the progress of the transaction."""
        if hasattr(self, "_signal_matcher"):
            self._signal_matcher.remove()
            del self._signal_matcher

    @deferable
    @convert_dbus_exception
    def set_locale(self, locale_name, reply_handler=None, error_handler=None):
        """Set the language for status and error messages.

        :param locale: The locale name, e.g. de_DE@UTF-8.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.ForeignTransaction, dbus.DBusException
        """
        if reply_handler:
            _reply_handler = lambda: reply_handler(self)
        else:
            _reply_handler = None
        self._proxy.Set("org.debian.apt.transaction", "Locale", locale_name,
                        dbus_interface=dbus.PROPERTIES_IFACE,
                        reply_handler=_reply_handler,
                        error_handler=error_handler)

    @deferable
    @convert_dbus_exception
    def provide_medium(self, medium, reply_handler=None, error_handler=None):
        """Continue a paused transaction which waits for a medium to install
        from.

        :param medium: The name of the provided medium.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.ForeignTransaction, dbus.DBusException
         """
        self._iface.ProvideMedium(medium, reply_handler=reply_handler,
                                  error_handler=error_handler)

    @deferable
    @convert_dbus_exception
    def resolve_config_file_conflict(self, config, answer, reply_handler=None,
                                     error_handler=None):
        """Continue a paused transaction which waits for the resolution of a
        configuration file conflict.

        :param config: The path to the current version of the configuration
            file.
        :param answer: Can be either "keep" or "replace".
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: aptdaemon.errors.ForeignTransaction, dbus.DBusException
         """
        self._iface.ResolveConfigFileConflict(config, answer,
                                              reply_handler=reply_handler,
                                              error_handler=error_handler)


class AptClient(object):

    """Provides a complete client for aptdaemon."""

    def __init__(self, bus=None):
        """Return a new AptClient instance."""
        if bus:
            self.bus = bus
        else:
            self.bus = dbus.SystemBus()
        # Catch an invalid locale
        try:
            self._locale = "%s.%s" % locale.getdefaultlocale()
        except ValueError:
            self._locale = None
        self.terminal = None

    @convert_dbus_exception
    def get_trusted_vendor_keys(self, reply_handler=None, error_handler=None):
        """Get the list of the installed vendor keys which are used to
        authenticate packages.

        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: Fingerprints of all installed vendor keys.
        """
        daemon = get_aptdaemon(self.bus)
        keys = daemon.GetTrustedVendorKeys(reply_handler=reply_handler,
                                           error_handler=error_handler)
        return keys

    @deferable
    @convert_dbus_exception
    def upgrade_system(self, safe_mode=True, wait=False, reply_handler=None,
                       error_handler=None):
        """Create a new transaction to apply all avaibale upgrades.

        :param safe_mode: If True only already installed packages will be
            updated. Updates which require to remove installed packages or to
            install additional packages will be skipped.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a
            defer.Deferred. This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("UpgradeSystem", [safe_mode],
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def install_packages(self, package_names, wait=False, reply_handler=None,
                         error_handler=None):
        """Create a new transaction to install the given packages from the
        reporitories.

        The version number and target release of the packages can be specified
        using the traditional apt-get syntax, e.g. "xterm=281.1" to force
        installing the version 281.1 of xterm or "xterm/experimental" to
        force installing xterm from the experimental release.

        :param package_names: List of names of the packages which should be
            installed.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a
            defer.Deferred. This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("InstallPackages", [package_names],
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def add_repository(self, src_type, uri, dist, comps=None, comment="",
                       sourcesfile="", wait=False, reply_handler=None,
                       error_handler=None):
        """Create a new transaction to enable a repository.

        :param src_type: The type of the repository (deb, deb-src).
        :param uri: The main repository URI
           (e.g. http://archive.ubuntu.com/ubuntu)
        :param dist: The distribution to use (e.g. stable or lenny-backports).
        :param comps: List of components (e.g. main, restricted).
        :param comment: A comment which should be added to the sources.list.
        :param sourcesfile: (Optoinal) filename in sources.list.d.

        :param wait: if True run the transaction immediately and return
            its exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        # dbus can not deal with empty lists and will error
        if not comps:
            comps = [""]
        return self._run_transaction("AddRepository",
                                     [src_type, uri, dist, comps, comment,
                                      sourcesfile],
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def add_vendor_key_from_keyserver(self, keyid, keyserver, wait=False,
                                      reply_handler=None, error_handler=None):
        """Create a new transaction to download and install the key of a
        software vendor. The key is used to authenticate packages of the
        vendor.

        :param keyid: The id of the GnuPG key (e.g. 0x0EB12F05)
        :param keyserver: The server to get the key from (e.g.
            keyserver.ubuntu.com)

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("AddVendorKeyFromKeyserver",
                                     [keyid, keyserver],
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def add_vendor_key_from_file(self, path, wait=False, reply_handler=None,
                                 error_handler=None):
        """Create a new transaction to install the key file of a software
        vendor. The key is used to authenticate packages of the vendor.

        :param path: The absolute path to the key file.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("AddVendorKeyFromFile", [path],
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def remove_vendor_key(self, fingerprint, wait=False, reply_handler=None,
                          error_handler=None):
        """Create a new transaction to remove the key of a software vendor
        from the list of trusted ones.

        The key is used to authenticate the origin of packages.

        :param fingerprint: The fingerprint of the key.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("RemoveVendorKey", [fingerprint],
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def install_file(self, path, force=False, wait=False, reply_handler=None,
                     error_handler=None):
        """Create a new transaction to install a local package file.

        :param path: The absolute path to the .deb-file.
        :param force: Force the installation of a .deb-file even if it
            violates the quality standard defined in the packaging policy.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        # Root is not allowed to access FUSE file systems. So copy files
        # to the local system.
        # FIXME: the locally cached one should be removed afterwards
        home = os.getenv("HOME", None)
        if home and path.startswith(os.path.join(home, ".gvfs")):
            shutil.copy(path, "/tmp")
            path = os.path.join("/tmp", os.path.basename(path))
        return self._run_transaction("InstallFile", [path, force],
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def upgrade_packages(self, package_names, wait=False, reply_handler=None,
                         error_handler=None):
        """Create a new transaction to upgrade installed packages.

        The version number and target release of the packages can be specified
        using the traditional apt-get syntax, e.g. "xterm=281.1" to force
        installing the version 281.1 of xterm or "xterm/experimental" to
        force installing xterm from the experimental release.

        :param package_names: The list of package which should be upgraded.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("UpgradePackages", [package_names],
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def remove_packages(self, package_names, wait=False,
                        reply_handler=None, error_handler=None):
        """Create a new transaction to remove installed packages.

        :param package_names: The list of packages which should be removed.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("RemovePackages", [package_names],
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def commit_packages(self, install, reinstall, remove, purge, upgrade,
                        downgrade, wait=False, reply_handler=None,
                        error_handler=None):
        """Create a new transaction to perform a complex package management
        task which allows to install, remove, upgrade or downgrade several
        packages at the same time.

        The version number and target release of the packages can be specified
        using the traditional apt-get syntax, e.g. "xterm=281.1" to force
        installing the version 281.1 of xterm or "xterm/experimental" to
        force installing xterm from the experimental release.

        :param install: List of packages to install.
        :param reinstall: List of packages to re-install.
        :param remove: List of packages to remove.
        :param purge: List of packages to purge.
        :param upgrade: List of packages to upgrade.
        :param downgrade: List of packages to downgrade. The version of the
            package has to be appended to the name separated by a "=", e.g.
            "xterm=272-1".

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        def check_empty_list(lst):
            if not lst:
                return [""]
            else:
                return lst
        pkgs = [check_empty_list(lst) for lst in [install, reinstall, remove,
                                                  purge, upgrade, downgrade]]
        return self._run_transaction("CommitPackages", pkgs,
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def fix_broken_depends(self, wait=False, reply_handler=None,
                           error_handler=None):
        """Create a new transaction to fix unsatisfied dependencies of
        already installed packages.

        Corresponds to the ``apt-get -f install`` call.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("FixBrokenDepends", [],
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def reconfigure(self, packages, priority="default",
                    wait=False, reply_handler=None, error_handler=None):
        """Create a new transaction to reconfigure already installed packages.

        Corresponds to the ``dpkg-reconfigure`` call.

        :param packages: List of package names which should be reconfigured.
        :param priority: The minimum priority of question that will be
            displayed.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("Reconfigure", [packages, priority], wait,
                                     reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def fix_incomplete_install(self, wait=False, reply_handler=None,
                               error_handler=None):
        """Create a new transaction to complete a previous interrupted
        installation.

        Corresponds to the ``dpkg --confgiure -a`` call.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("FixIncompleteInstall", [], wait,
                                     reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def update_cache(self, sources_list=None, wait=False,
                     reply_handler=None, error_handler=None):
        """Create a new transaction to update the package cache.

        The repositories will be queried for installable packages.

        :param sources_list: Path to a sources.list which contains repositories
            that should be updated only. The other repositories will
            be ignored in this case. Can be either the file name of a snippet
            in /etc/apt/sources.list.d or an absolute path.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        if sources_list:
            return self._run_transaction("UpdateCachePartially",
                                         [sources_list], wait,
                                         reply_handler, error_handler)
        else:
            return self._run_transaction("UpdateCache", [], wait,
                                         reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def enable_distro_component(self, component, wait=False,
                                reply_handler=None, error_handler=None):
        """Create a new transaction to enable the component of the
        distribution repository.

        :param component: The name of the component, e.g. main or universe.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("EnableDistroComponent", [component],
                                     wait, reply_handler, error_handler)

    @deferable
    @convert_dbus_exception
    def clean(self, wait=False, reply_handler=None, error_handler=None):
        """Remove all downloaded files.

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("Clean", [], wait, reply_handler,
                                     error_handler)

    @deferable
    @convert_dbus_exception
    def add_license_key(self, pkg_name, json_token, server_name, wait=False,
                        reply_handler=None, error_handler=None):
        """Install a license key to use a piece of proprietary software.

        :param pkg_name: The package which requires the license
        :param json_token: The oauth token in json format
        :param server_name: The server name (ubuntu-procduction,
            ubuntu-staging)

        :param wait: if True run the transaction immediately and return its
            exit state instead of the transaction itself.
        :param reply_handler: Callback function. If specified in combination
            with error_handler the method will be called asynchrounsouly.
        :param error_handler: Errback function. In case of an error the given
            callback gets the corresponding exception instance.
        :param defer: Run the method asynchrounsly and return a defer.Deferred.
            This options is only available as a keyword.

        :raises: dbus.DBusException

        :returns: An AptTransaction instance.
        """
        return self._run_transaction("AddLicenseKey",
                                     [pkg_name, json_token, server_name],
                                     wait, reply_handler,
                                     error_handler)

    def _run_transaction(self, method_name, args, wait, reply_handler,
                         error_handler):
        async = reply_handler and error_handler
        try:
            deferred = self._run_transaction_helper(method_name, args, wait,
                                                    async)
        except Exception as error:
            if async:
                error_handler(error)
                return
            else:
                raise
        if async:
            def on_error(error):
                """Convert the DeferredException to a normal exception."""
                try:
                    error.raise_exception()
                except Exception as error:
                    error_handler(error)
            deferred.add_callbacks(reply_handler)
            deferred.add_errback(on_error)
            return deferred
        else:
            # Iterate on the main loop - we cannot use a sub loop here,
            # since the D-Bus python bindings only work on the main loop
            context = GLib.main_context_default()
            while not hasattr(deferred, "result"):
                context.iteration(True)
            # If there has been an error in the helper raise it
            if isinstance(deferred.result, defer.DeferredException):
                deferred.result.raise_exception()
            trans = deferred.result
            if trans.error:
                raise trans.error
            if wait:
                # Wait until the transaction is complete and the properties
                # of the transaction have been updated
                while trans.exit == enums.EXIT_UNFINISHED:
                    context.iteration(True)
                return trans.exit
            else:
                return trans

    @defer.inline_callbacks
    def _run_transaction_helper(self, method_name, args, wait, async):
        daemon = get_aptdaemon(self.bus)
        dbus_method = daemon.get_dbus_method(method_name)
        if async:
            deferred = defer.Deferred()
            dbus_method(reply_handler=deferred.callback,
                        error_handler=deferred.errback, *args,
                        timeout=_APTDAEMON_DBUS_TIMEOUT)
            tid = yield deferred
        else:
            tid = dbus_method(*args, timeout=_APTDAEMON_DBUS_TIMEOUT)
        trans = AptTransaction(tid, self.bus)
        if self._locale:
            yield trans.set_locale(self._locale)
        if self.terminal:
            yield trans.set_terminal(self.terminal)
        yield trans.sync()
        if wait and async:
            deferred_wait = defer.Deferred()
            sig = trans.connect("finished",
                                lambda trans, exit:
                                (exit != enums.EXIT_UNFINISHED and
                                 deferred_wait.callback(exit)))
            yield trans.run()
            yield deferred_wait
            GLib.source_remove(sig)
            defer.return_value(trans.exit)
        elif wait:
            yield trans.run()
        defer.return_value(trans)


@deferable
@convert_dbus_exception
def get_transaction(tid, bus=None, reply_handler=None, error_handler=None):
    """Get an existing transaction by its identifier.

    :param tid: The identifer and D-Bus path of the transaction
        e.g. /org/debian/apt/transaction/78904e5f9fa34098879e768032789109
    :param bus: Optionally the D-Bus on which aptdaemon listens. Defaults
        to the system bus.

    :param reply_handler: Callback function. If specified in combination
        with error_handler the method will be called asynchrounsouly.
    :param error_handler: Errback function. In case of an error the given
        callback gets the corresponding exception instance.
    :param defer: Run the method asynchrounsly and return a defer.Deferred.
        This options is only available as a keyword.

    :raises: dbus.DBusException

    :returns: An AptTransaction instance.
    """
    if not bus:
        bus = dbus.SystemBus()
    trans = AptTransaction(tid, bus)
    if error_handler and reply_handler:
        trans.sync(reply_handler=reply_handler, error_handler=error_handler)
    else:
        trans.sync()
        return trans


def get_size_string(bytes):
    """Returns a human friendly string for a given byte size.

    Note: The bytes are skipped from the returned unit: 1024 returns 1K
    """
    for unit in ["", "K", "M", "G"]:
        if bytes < 1024.0:
            return "%3.1f%s" % (bytes, unit)
        bytes /= 1024.0
    return "%3.1f%s" % (bytes, "T")


def get_aptdaemon(bus=None):
    """Get the daemon D-Bus interface.

    :param bus: Optionally the D-Bus on which aptdaemon listens. Defaults
        to the system bus.

    :raises: dbus.DBusException

    :returns: An dbus.Interface instance.
    """
    if not bus:
        bus = dbus.SystemBus()
    return dbus.Interface(bus.get_object("org.debian.apt",
                                         "/org/debian/apt",
                                         False),
                          "org.debian.apt")

# vim:ts=4:sw=4:et
