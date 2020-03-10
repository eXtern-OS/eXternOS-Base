#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exception classes"""
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

__all__ = ("AptDaemonError", "ForeignTransaction", "InvalidMetaDataError",
           "InvalidProxyError", "RepositoryInvalidError",
           "TransactionAlreadyRunning", "TransactionCancelled",
           "TransactionAlreadySimulating",
           "TransactionFailed", "TransactionRoleAlreadySet",
           "NotAuthorizedError", "convert_dbus_exception",
           "get_native_exception")

import inspect
from functools import wraps
import sys

import dbus

import aptdaemon.enums

PY3K = sys.version_info.major > 2


class AptDaemonError(dbus.DBusException):

    """Internal error of the aptdaemon"""

    _dbus_error_name = "org.debian.apt"

    def __init__(self, message=""):
        message = _convert_unicode(message)
        dbus.DBusException.__init__(self, message)
        self._message = message

    def get_dbus_message(self):
        """Overwrite the DBusException method, since it calls
        Exception.__str__() internally which doesn't support unicode or
        or non-ascii encodings."""
        if PY3K:
            return dbus.DBusException.get_dbus_message(self)
        else:
            return self._message.encode("UTF-8")


class TransactionRoleAlreadySet(AptDaemonError):

    """Error if a transaction has already been configured."""

    _dbus_error_name = "org.debian.apt.TransactionRoleAlreadySet"


class TransactionAlreadyRunning(AptDaemonError):

    """Error if a transaction has already been configured."""

    _dbus_error_name = "org.debian.apt.TransactionAlreadyRunning"


class TransactionAlreadySimulating(AptDaemonError):

    """Error if a transaction should be simulated but a simulation is
    already processed.
    """

    _dbus_error_name = "org.debian.apt.TransactionAlreadySimulating"


class ForeignTransaction(AptDaemonError):

    """Error if a transaction was initialized by a different user."""

    _dbus_error_name = "org.debian.apt.TransactionAlreadyRunning"


class TransactionFailed(AptDaemonError):

    """Internal error if a transaction could not be processed successfully."""

    _dbus_error_name = "org.debian.apt.TransactionFailed"

    def __init__(self, code, details="", *args):
        if not args:
            # Avoid string replacements if not used
            details = details.replace("%", "%%")
        args = tuple([_convert_unicode(arg) for arg in args])
        details = _convert_unicode(details)
        self.code = code
        self.details = details
        self.details_args = args
        AptDaemonError.__init__(self, "%s: %s" % (code, details % args))

    def __unicode__(self):
        return "Transaction failed: %s\n%s" % \
               (aptdaemon.enums.get_error_string_from_enum(self.code),
                self.details)

    def __str__(self):
        if PY3K:
            return self.__unicode__()
        else:
            return self.__unicode__().encode("utf-8")


class InvalidMetaDataError(AptDaemonError):

    """Invalid meta data given"""

    _dbus_error_name = "org.debian.apt.InvalidMetaData"


class InvalidProxyError(AptDaemonError):

    """Invalid proxy given"""

    _dbus_error_name = "org.debian.apt.InvalidProxy"

    def __init__(self, proxy):
        AptDaemonError.__init__(self, "InvalidProxyError: %s" % proxy)


class TransactionCancelled(AptDaemonError):

    """Internal error if a transaction was cancelled."""

    _dbus_error_name = "org.debian.apt.TransactionCancelled"


class RepositoryInvalidError(AptDaemonError):

    """The added repository is invalid"""

    _dbus_error_name = "org.debian.apt.RepositoryInvalid"


class PolicyKitError(dbus.DBusException):
    pass


class NotAuthorizedError(PolicyKitError):

    _dbus_error_name = "org.freedesktop.PolicyKit.Error.NotAuthorized"

    def __init__(self, subject, action_id):
        dbus.DBusException.__init__(self, "%s: %s" % (subject, action_id))
        self.action_id = action_id
        self.subject = subject


class AuthorizationFailed(NotAuthorizedError):

    _dbus_error_name = "org.freedesktop.PolicyKit.Error.Failed"


def convert_dbus_exception(func):
    """A decorator which maps a raised DBbus exception to a native one.

    This decorator requires introspection to the decorated function. So it
    cannot be used on any already decorated method.
    """
    argnames, varargs, kwargs, defaults = inspect.getargspec(func)

    @wraps(func)
    def _convert_dbus_exception(*args, **kwargs):
        try:
            error_handler = kwargs["error_handler"]
        except KeyError:
            _args = list(args)
            try:
                index = argnames.index("error_handler")
                error_handler = _args[index]
            except (IndexError, ValueError):
                pass
            else:
                _args[index] = lambda err: error_handler(
                    get_native_exception(err))
                args = tuple(_args)
        else:
            kwargs["error_handler"] = lambda err: error_handler(
                get_native_exception(err))
        try:
            return func(*args, **kwargs)
        except dbus.exceptions.DBusException as error:
            raise get_native_exception(error)
    return _convert_dbus_exception


def get_native_exception(error):
    """Map a DBus exception to a native one. This allows to make use of
    try/except on the client side without having to check for the error name.
    """
    if not isinstance(error, dbus.DBusException):
        return error
    dbus_name = error.get_dbus_name()
    dbus_msg = error.get_dbus_message()
    if dbus_name == TransactionFailed._dbus_error_name:
        return TransactionFailed(*dbus_msg.split(":", 1))
    elif dbus_name == AuthorizationFailed._dbus_error_name:
        return AuthorizationFailed(*dbus_msg.split(":", 1))
    elif dbus_name == NotAuthorizedError._dbus_error_name:
        return NotAuthorizedError(*dbus_msg.split(":", 1))
    for error_cls in [AptDaemonError, TransactionRoleAlreadySet,
                      TransactionAlreadyRunning, ForeignTransaction,
                      InvalidMetaDataError, InvalidProxyError,
                      TransactionCancelled, RepositoryInvalidError]:
        if dbus_name == error_cls._dbus_error_name:
            return error_cls(dbus_msg)
    return error


def _convert_unicode(text, encoding="UTF-8"):
    """Always return an unicode."""
    if PY3K and not isinstance(text, str):
        text = str(text, encoding, errors="ignore")
    elif not PY3K and not isinstance(text, unicode):
        text = unicode(text, encoding, errors="ignore")
    return text

# vim:ts=4:sw=4:et
