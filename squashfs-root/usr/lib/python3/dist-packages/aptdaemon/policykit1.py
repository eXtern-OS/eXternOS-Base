#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Provides access to PolicyKit privilege mangement using gdefer Deferreds."""
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

__all__ = ("check_authorization_by_name", "check_authorization_by_pid",
           "get_pid_from_dbus_name", "get_uid_from_dbus_name",
           "CHECK_AUTH_ALLOW_USER_INTERACTION", "CHECK_AUTH_NONE",
           "PK_ACTION_ADD_REMOVE_VENDOR_KEY", "PK_ACTION_CANCEL_FOREIGN",
           "PK_ACTION_CHANGE_REPOSITORY",
           "PK_ACTION_CHANGE_CONIFG",
           "PK_ACTION_GET_TRUSTED_VENDOR_KEYS",
           "PK_ACTION_INSTALL_FILE",
           "PK_ACTION_INSTALL_OR_REMOVE_PACKAGES",
           "PK_ACTION_INSTALL_PACKAGES_FROM_NEW_REPO",
           "PK_ACTION_INSTALL_PACKAGES_FROM_HIGH_TRUST_REPO",
           "PK_ACTION_INSTALL_PURCHASED_PACKAGES",
           "PK_ACTION_UPDATE_CACHE", "PK_ACTION_UPGRADE_PACKAGES",
           "PK_ACTION_SET_PROXY", "PK_ACTION_CLEAN")

import dbus

from defer import Deferred, inline_callbacks, return_value
from .errors import NotAuthorizedError, AuthorizationFailed

PK_ACTION_INSTALL_OR_REMOVE_PACKAGES = (
    "org.debian.apt.install-or-remove-packages")
PK_ACTION_INSTALL_PURCHASED_PACKAGES = (
    "org.debian.apt.install-purchased-packages")
PK_ACTION_INSTALL_PACKAGES_FROM_NEW_REPO = (
    "org.debian.apt.install-packages-from-new-repo")
PK_ACTION_INSTALL_PACKAGES_FROM_HIGH_TRUST_REPO = (
    "org.debian.apt.install-packages.high-trust-repo")
PK_ACTION_INSTALL_FILE = "org.debian.apt.install-file"
PK_ACTION_UPGRADE_PACKAGES = "org.debian.apt.upgrade-packages"
PK_ACTION_UPDATE_CACHE = "org.debian.apt.update-cache"
PK_ACTION_CANCEL_FOREIGN = "org.debian.apt.cancel-foreign"
PK_ACTION_GET_TRUSTED_VENDOR_KEYS = "org.debian.apt.get-trusted-vendor-keys"
PK_ACTION_CHANGE_REPOSITORY = "org.debian.apt.change-repository"
PK_ACTION_CHANGE_CONFIG = "org.debian.apt.change-config"
PK_ACTION_SET_PROXY = "org.debian.apt.set-proxy"
PK_ACTION_CLEAN = "org.debian.apt.clean"

CHECK_AUTH_NONE = 0
CHECK_AUTH_ALLOW_USER_INTERACTION = 1


def check_authorization_by_name(dbus_name, action_id, timeout=86400, bus=None,
                                flags=None):
    """Check if the given sender is authorized for the specified action.

    If the sender is not authorized raise NotAuthorizedError.

    Keyword arguments:
    dbus_name -- D-Bus name of the subject
    action_id -- the PolicyKit policy name of the action
    timeout -- time in seconds for the user to authenticate
    bus -- the D-Bus connection (defaults to the system bus)
    flags -- optional flags to control the authentication process
    """
    subject = ("system-bus-name", {"name": dbus_name})
    return _check_authorization(subject, action_id, timeout, bus, flags)


def check_authorization_by_pid(pid, action_id, timeout=86400, bus=None,
                               flags=None):
    """Check if the given process is authorized for the specified action.

    If the sender is not authorized raise NotAuthorizedError.

    Keyword arguments:
    pid -- id of the process
    action_id -- the PolicyKit policy name of the action
    timeout -- time in seconds for the user to authenticate
    bus -- the D-Bus connection (defaults to the system bus)
    flags -- optional flags to control the authentication process
    """
    subject = ("unix-process", {"pid": pid})
    return _check_authorization(subject, action_id, timeout, bus, flags)


def _check_authorization(subject, action_id, timeout, bus, flags=None):
    def policykit_done(xxx_todo_changeme):
        (authorized, challenged, auth_details) = xxx_todo_changeme
        if authorized:
            deferred.callback(auth_details)
        elif challenged:
            deferred.errback(AuthorizationFailed(subject, action_id))
        else:
            deferred.errback(NotAuthorizedError(subject, action_id))
    if not bus:
        bus = dbus.SystemBus()
    # Set the default flags
    if flags is None:
        flags = CHECK_AUTH_ALLOW_USER_INTERACTION
    deferred = Deferred()
    pk = bus.get_object("org.freedesktop.PolicyKit1",
                        "/org/freedesktop/PolicyKit1/Authority")
    details = {}
    pk.CheckAuthorization(
        subject, action_id, details, flags, "",
        dbus_interface="org.freedesktop.PolicyKit1.Authority",
        timeout=timeout,
        reply_handler=policykit_done,
        error_handler=deferred.errback)
    return deferred


def get_pid_from_dbus_name(dbus_name, bus=None):
    """Return a deferred that gets the id of process owning the given
    system D-Bus name.
    """
    if not bus:
        bus = dbus.SystemBus()
    deferred = Deferred()
    bus_obj = bus.get_object("org.freedesktop.DBus",
                             "/org/freedesktop/DBus/Bus")
    bus_obj.GetConnectionUnixProcessID(dbus_name,
                                       dbus_interface="org.freedesktop.DBus",
                                       reply_handler=deferred.callback,
                                       error_handler=deferred.errback)
    return deferred


@inline_callbacks
def get_uid_from_dbus_name(dbus_name, bus=None):
    """Return a deferred that gets the uid of the user owning the given
    system D-Bus name.
    """
    if not bus:
        bus = dbus.SystemBus()
    pid = yield get_pid_from_dbus_name(dbus_name, bus)
    with open("/proc/%s/status" % pid) as proc:
        values = [v for v in proc.readlines() if v.startswith("Uid:")]
    uid = int(values[0].split()[1])
    return_value(uid)


@inline_callbacks
def get_proc_info_from_dbus_name(dbus_name, bus=None):
    """Return a deferred that gets the pid, the uid of the user owning the
    given system D-Bus name and its command line.
    """
    if not bus:
        bus = dbus.SystemBus()
    pid = yield get_pid_from_dbus_name(dbus_name, bus)
    with open("/proc/%s/status" % pid) as proc:
        lines = proc.readlines()
        uid_values = [v for v in lines if v.startswith("Uid:")]
        gid_values = [v for v in lines if v.startswith("Gid:")]
    # instead of ", encoding='utf8'" we use the "rb"/decode() here for
    # py2 compatibility
    with open("/proc/%s/cmdline" % pid, "rb") as cmdline_file:
        cmdline = cmdline_file.read().decode("utf-8")
    uid = int(uid_values[0].split()[1])
    gid = int(gid_values[0].split()[1])
    return_value((pid, uid, gid, cmdline))

# vim:ts=4:sw=4:et
