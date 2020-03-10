#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Handles the apt system lock"""
# Copyright (C) 2010 Sebastian Heinlein <devel@glatzor.de>
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

__all__ = ("LockFailedError", "system")

import fcntl
import os
import struct

import apt_pkg
from gi.repository import GLib

from aptdaemon import enums
from aptdaemon.errors import TransactionCancelled


class LockFailedError(Exception):

    """The locking of file failed."""

    def __init__(self, flock, process=None):
        """Return a new LockFailedError instance.

        Keyword arguments:
        flock -- the path of the file lock
        process -- the process which holds the lock or None
        """
        msg = "Could not acquire lock on %s." % flock
        if process:
            msg += " The lock is hold by %s." % process
        Exception.__init__(self, msg)
        self.flock = flock
        self.process = process


class FileLock(object):

    """Represents a file lock."""

    def __init__(self, path):
        self.path = path
        self.fd = None

    @property
    def locked(self):
        return self.fd is not None

    def acquire(self):
        """Return the file descriptor of the lock file or raise
        LockFailedError if the lock cannot be obtained.
        """
        if self.fd:
            return self.fd
        fd_lock = apt_pkg.get_lock(self.path)
        if fd_lock < 0:
            process = get_locking_process_name(self.path)
            raise LockFailedError(self.path, process)
        else:
            self.fd = fd_lock
            return fd_lock

    def release(self):
        """Relase the lock."""
        if self.fd:
            os.close(self.fd)
            self.fd = None


def get_locking_process_name(lock_path):
    """Return the name of a process which holds a lock. It will be None if
    the name cannot be retrivied.
    """
    try:
        fd_lock_read = open(lock_path, "r")
    except IOError:
        return None
    else:
        # Get the pid of the locking application
        flk = struct.pack('hhQQi', fcntl.F_WRLCK, os.SEEK_SET, 0, 0, 0)
        flk_ret = fcntl.fcntl(fd_lock_read, fcntl.F_GETLK, flk)
        pid = struct.unpack("hhQQi", flk_ret)[4]
        # Get the command of the pid
        try:
            with open("/proc/%s/status" % pid, "r") as fd_status:
                try:
                    for key, value in (line.split(":") for line in
                                       fd_status.readlines()):
                        if key == "Name":
                            return value.strip()
                except Exception:
                    return None
        except IOError:
            return None
        finally:
            fd_lock_read.close()
    return None

apt_pkg.init()

#: The lock for dpkg status file
_status_dir = os.path.dirname(apt_pkg.config.find_file("Dir::State::status"))
status_lock = FileLock(os.path.join(_status_dir, "lock"))
frontend_lock = FileLock(os.path.join(_status_dir, "lock-frontend"))

#: The lock for the package archive
_archives_dir = apt_pkg.config.find_dir("Dir::Cache::Archives")
archive_lock = FileLock(os.path.join(_archives_dir, "lock"))

#: The lock for the repository indexes
lists_lock = FileLock(os.path.join(
    apt_pkg.config.find_dir("Dir::State::lists"), "lock"))


def acquire():
    """Acquire an exclusive lock for the package management system."""
    try:
        for lock in frontend_lock, status_lock, archive_lock, lists_lock:
            if not lock.locked:
                lock.acquire()
    except:
        release()
        raise

    os.environ['DPKG_FRONTEND_LOCKED'] = '1'

def release():
    """Release an exclusive lock for the package management system."""
    for lock in lists_lock, archive_lock, status_lock, frontend_lock:
        lock.release()

    try:
        del os.environ['DPKG_FRONTEND_LOCKED']
    except KeyError:
        pass


def wait_for_lock(trans, alt_lock=None):
    """Acquire the system lock or the optionally given one. If the lock
    cannot be obtained pause the transaction in the meantime.

    :param trans: the transaction
    :param lock: optional alternative lock
    """
    def watch_lock():
        """Helper to unpause the transaction if the lock can be obtained.

        Keyword arguments:
        trans -- the corresponding transaction
        alt_lock -- alternative lock to the system lock
        """
        try:
            if alt_lock:
                alt_lock.acquire()
            else:
                acquire()
        except LockFailedError:
            return True
        trans.paused = False
        return True

    try:
        if alt_lock:
            alt_lock.acquire()
        else:
            acquire()
    except LockFailedError as error:
        trans.paused = True
        trans.status = enums.STATUS_WAITING_LOCK
        if error.process:
            # TRANSLATORS: %s is the name of a package manager
            msg = trans.gettext("Waiting for %s to exit")
            trans.status_details = msg % error.process
        lock_watch = GLib.timeout_add_seconds(3, watch_lock)
        while trans.paused and not trans.cancelled:
            GLib.main_context_default().iteration()
        GLib.source_remove(lock_watch)
        if trans.cancelled:
            raise TransactionCancelled()

# vim:ts=4:sw=4:et
