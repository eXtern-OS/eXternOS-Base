# LivePatchSocket.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2017 Canonical
#
#  Author: Andrea Azzarone <andrea.azzarone@canonical.com>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

from gi.repository import GLib
import http.client
import socket
import threading
import yaml

HOST_NAME = '/var/snap/canonical-livepatch/current/livepatchd.sock'


class UHTTPConnection(http.client.HTTPConnection):

    def __init__(self, path):
        http.client.HTTPConnection.__init__(self, 'localhost')
        self.path = path

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.path)
        self.sock = sock


class LivePatchSocket(object):

    def __init__(self, http_conn=None):
        if http_conn is None:
            self.conn = UHTTPConnection(HOST_NAME)
        else:
            self.conn = http_conn

    def get_status(self, on_done):

        def do_call():
            try:
                self.conn.request('GET', '/status?verbose=True')
                r = self.conn.getresponse()
                active = r.status == 200
                data = yaml.safe_load(r.read())
            except Exception as e:
                active = False
                data = dict()
            check_state = LivePatchSocket.get_check_state(data)
            patch_state = LivePatchSocket.get_patch_state(data)
            fixes = LivePatchSocket.get_fixes(data)
            GLib.idle_add(lambda: on_done(
                active, check_state, patch_state, fixes))

        thread = threading.Thread(target=do_call)
        thread.start()

    @staticmethod
    def get_check_state(data):
        try:
            status = data['status']
            kernel = next((k for k in status if k['running']), None)
            return kernel['livepatch']['checkState']
        except Exception as e:
            return 'check-failed'

    @staticmethod
    def get_patch_state(data):
        try:
            status = data['status']
            kernel = next((k for k in status if k['running']), None)
            return kernel['livepatch']['patchState']
        except Exception as e:
            return 'unknown'

    @staticmethod
    def get_fixes(data):
        try:
            status = data['status']
            kernel = next((k for k in status if k['running']), None)
            fixes = kernel['livepatch']['fixes']
            return [LivePatchFix(f)
                    for f in fixes.replace('* ', '').split('\n') if len(f) > 0]
        except Exception as e:
            return list()


class LivePatchFix(object):

    def __init__(self, text):
        patched_pattern = ' (unpatched)'
        self.patched = text.find(patched_pattern) == -1
        self.name = text.replace(patched_pattern, '')

    def __eq__(self, other):
        if isinstance(other, LivePatchFix):
            return self.name == other.name and self.patched == other.patched
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result
