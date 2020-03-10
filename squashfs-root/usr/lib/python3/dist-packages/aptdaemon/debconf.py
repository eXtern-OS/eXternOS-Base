#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integration of debconf on the client side

Provides the DebconfProxy class which allows to run the debconf frontend
as normal user by connecting to the root running debconf through the
socket of the passthrough frontend.
"""
# Copyright (C) 2009 Sebastian Heinlein <devel@glatzor.de>
# Copyright (C) 2009 Michael Vogt <michael.vogt@ubuntu.com>
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

__all__ = ("DebconfProxy",)

import copy
import logging
import os
import os.path
import socket
import subprocess
import tempfile
import sys

from gi.repository import GLib

log = logging.getLogger("AptClient.DebconfProxy")


class DebconfProxy(object):

    """The DebconfProxy class allows to run the debconf frontend
    as normal user by connecting to the root debconf through the socket of the
    passthrough frontend.
    """

    def __init__(self, frontend="gnome", socket_path=None):
        """Initialize a new DebconfProxy instance.

        Keyword arguments:
        frontend -- the to be used debconf frontend (defaults to gnome)
        socket_path -- the path to the socket of the passthrough frontend.
            Will be created if not specified
        """
        self.socket_path = socket_path
        self.temp_dir = None
        if socket_path is None:
            self.temp_dir = tempfile.mkdtemp(prefix="aptdaemon-")
            self.socket_path = os.path.join(self.temp_dir, "debconf.socket")
        log.debug("debconf socket: %s" % self.socket_path)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(self.socket_path)
        self.frontend = frontend
        self._listener_id = None
        self._active_conn = None
        self._watch_ids = []

    def _get_debconf_env(self):
        """Returns a dictonary of the environment variables required by
        the debconf frontend.
        """
        env = copy.copy(os.environ)
        env["DEBCONF_DB_REPLACE"] = "configdb"
        env["DEBCONF_DB_OVERRIDE"] = "Pipe{infd:none outfd:none}"
        env["DEBIAN_FRONTEND"] = self.frontend
        if log.level == logging.DEBUG:
            env["DEBCONF_DEBUG"] = "."
        return env

    def start(self):
        """Start listening on the socket."""
        logging.debug("debconf.start()")
        self.socket.listen(1)
        self._listener_id = GLib.io_add_watch(
            self.socket, GLib.PRIORITY_DEFAULT_IDLE,
            GLib.IO_IN, self._accept_connection)

    def stop(self):
        """Stop listening on the socket."""
        logging.debug("debconf.stop()")
        self.socket.close()
        if self._listener_id is not None:
            GLib.source_remove(self._listener_id)
            self._listener_id = None
        if self.temp_dir:
            try:
                os.remove(self.socket_path)
                os.rmdir(self.temp_dir)
            except OSError:
                pass

    def _accept_connection(self, socket, condition):
        if self._active_conn:
            log.debug("Delaying connection")
            return True
        conn, addr = socket.accept()
        self._active_conn = conn
        mask = GLib.IO_IN | GLib.IO_ERR | GLib.IO_HUP | GLib.IO_NVAL
        self.helper = subprocess.Popen(["debconf-communicate"],
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       env=self._get_debconf_env())
        GLib.io_add_watch(conn, GLib.PRIORITY_HIGH_IDLE,
                          mask, self._copy_conn, self.helper.stdin)
        GLib.io_add_watch(self.helper.stdout, GLib.PRIORITY_HIGH_IDLE,
                          mask, self._copy_stdout, conn)
        return True

    def _copy_stdout(self, source, condition, conn):
        """Callback to copy data from the stdout of debconf-communicate to
        the passthrough frontend."""
        logging.debug("_copy_stdout")
        try:
            debconf_data = source.readline()
            if debconf_data:
                log.debug("From debconf: %s", debconf_data)
                conn.send(debconf_data)
                return True
        except (socket.error, IOError) as error:
            log.debug(error)
        # error, stop listening
        log.debug("Stop reading from stdout")
        self.helper.stdout.close()
        self._active_conn.close()
        self._active_conn = None
        return False

    def _copy_conn(self, source, condition, stdin):
        """Callback to copy data from the passthrough frontend to stdin of
        debconf-communicate."""
        logging.debug("_copy_conn")
        try:
            socket_data = source.recv(1024)
            if socket_data:
                log.debug("From socket: %s", socket_data)
                stdin.write(socket_data)
                stdin.flush()
                return True
        except (socket.error, IOError) as error:
            log.debug(error)
        # error, stop listening
        log.debug("Stop reading from conn")
        self.helper.stdin.close()
        return False


def _test():
    """Run the DebconfProxy from the command line for testing purposes.

    You have to execute the following commands before in a separate terminal:
    $ echo "fset debconf/frontend seen false" | debconf-communicate
    $ export DEBCONF_PIPE=/tmp/debconf.socket
    $ dpkg-reconfigure debconf -f passthrough
    """
    logging.basicConfig(level=logging.DEBUG)
    socket_path = "/tmp/debconf.socket"
    if os.path.exists(socket_path):
        os.remove(socket_path)
    proxy = DebconfProxy("gnome", socket_path)
    proxy.start()
    loop = GLib.MainLoop()
    loop.run()

if __name__ == "__main__":
    _test()

# vim:ts=4:sw=4:et
