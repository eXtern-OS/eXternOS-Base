# -*- coding: utf-8 -*-
#    Gedit External Tools plugin
#    Copyright (C) 2005-2006  Steve Frécinaux <steve@istique.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

__all__ = ('Capture', )

import os
import sys
import signal
import locale
import subprocess
import fcntl
from gi.repository import GLib, GObject

try:
    import gettext
    gettext.bindtextdomain('gedit')
    gettext.textdomain('gedit')
    _ = gettext.gettext
except:
    _ = lambda s: s

class Capture(GObject.Object):
    CAPTURE_STDOUT = 0x01
    CAPTURE_STDERR = 0x02
    CAPTURE_BOTH = 0x03
    CAPTURE_NEEDS_SHELL = 0x04

    WRITE_BUFFER_SIZE = 0x4000

    __gsignals__ = {
        'stdout-line': (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_STRING,)),
        'stderr-line': (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_STRING,)),
        'begin-execute': (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, tuple()),
        'end-execute': (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_INT,))
    }

    def __init__(self, command, cwd=None, env={}):
        GObject.GObject.__init__(self)
        self.pipe = None
        self.env = env
        self.cwd = cwd
        self.flags = self.CAPTURE_BOTH | self.CAPTURE_NEEDS_SHELL
        self.command = command
        self.input_text = None

    def set_env(self, **values):
        self.env.update(**values)

    def set_command(self, command):
        self.command = command

    def set_flags(self, flags):
        self.flags = flags

    def set_input(self, text):
        self.input_text = text.encode("UTF-8") if text else None

    def set_cwd(self, cwd):
        self.cwd = cwd

    def execute(self):
        if self.command is None:
            return

        # Initialize pipe
        popen_args = {
            'cwd': self.cwd,
            'shell': self.flags & self.CAPTURE_NEEDS_SHELL,
            'env': self.env
        }

        if self.input_text is not None:
            popen_args['stdin'] = subprocess.PIPE
        if self.flags & self.CAPTURE_STDOUT:
            popen_args['stdout'] = subprocess.PIPE
        if self.flags & self.CAPTURE_STDERR:
            popen_args['stderr'] = subprocess.PIPE

        self.tried_killing = False
        self.in_channel = None
        self.out_channel = None
        self.err_channel = None
        self.in_channel_id = 0
        self.out_channel_id = 0
        self.err_channel_id = 0

        try:
            self.pipe = subprocess.Popen(self.command, **popen_args)
        except OSError as e:
            self.pipe = None
            self.emit('stderr-line', _('Could not execute command: %s') % (e, ))
            return

        self.emit('begin-execute')

        if self.input_text is not None:
            self.in_channel, self.in_channel_id = self.add_in_watch(self.pipe.stdin.fileno(),
                                                                    self.on_in_writable)

        if self.flags & self.CAPTURE_STDOUT:
            self.out_channel, self.out_channel_id = self.add_out_watch(self.pipe.stdout.fileno(),
                                                                       self.on_output)

        if self.flags & self.CAPTURE_STDERR:
            self.err_channel, self.err_channel_id = self.add_out_watch(self.pipe.stderr.fileno(),
                                                                       self.on_err_output)

        # Wait for the process to complete
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT,
                             self.pipe.pid,
                             self.on_child_end)

    def add_in_watch(self, fd, io_func):
        channel = GLib.IOChannel.unix_new(fd)
        channel.set_flags(channel.get_flags() | GLib.IOFlags.NONBLOCK)
        channel.set_encoding(None)
        channel_id = GLib.io_add_watch(channel,
                                       GLib.PRIORITY_DEFAULT,
                                       GLib.IOCondition.OUT | GLib.IOCondition.HUP | GLib.IOCondition.ERR,
                                       io_func)
        return (channel, channel_id)

    def add_out_watch(self, fd, io_func):
        channel = GLib.IOChannel.unix_new(fd)
        channel.set_flags(channel.get_flags() | GLib.IOFlags.NONBLOCK)
        channel_id = GLib.io_add_watch(channel,
                                       GLib.PRIORITY_DEFAULT,
                                       GLib.IOCondition.IN | GLib.IOCondition.HUP | GLib.IOCondition.ERR,
                                       io_func)
        return (channel, channel_id)

    def write_chunk(self, dest, condition):
        if condition & (GObject.IO_OUT):
            status = GLib.IOStatus.NORMAL
            l = len(self.input_text)
            while status == GLib.IOStatus.NORMAL:
                if l == 0:
                    return False
                m = min(l, self.WRITE_BUFFER_SIZE)
                try:
                    (status, length) = dest.write_chars(self.input_text, m)
                    self.input_text = self.input_text[length:]
                    l -= length
                except Exception as e:
                    return False
            if status != GLib.IOStatus.AGAIN:
                return False

        if condition & ~(GObject.IO_OUT):
            return False

        return True

    def on_in_writable(self, dest, condition):
        ret = self.write_chunk(dest, condition)
        if ret is False:
            self.input_text = None
            try:
                self.in_channel.shutdown(True)
            except:
                pass
            self.in_channel = None
            self.in_channel_id = 0
            self.cleanup_pipe()

        return ret

    def handle_source(self, source, condition, signalname):
        if condition & (GObject.IO_IN | GObject.IO_PRI):
            status = GLib.IOStatus.NORMAL
            while status == GLib.IOStatus.NORMAL:
                try:
                    (status, buf, length, terminator_pos) = source.read_line()
                except Exception as e:
                    return False
                if buf:
                    self.emit(signalname, buf)
            if status != GLib.IOStatus.AGAIN:
                return False

        if condition & ~(GObject.IO_IN | GObject.IO_PRI):
            return False

        return True

    def on_output(self, source, condition):
        ret = self.handle_source(source, condition, 'stdout-line')
        if ret is False and self.out_channel:
            try:
                self.out_channel.shutdown(True)
            except:
                pass
            self.out_channel = None
            self.out_channel_id = 0
            self.cleanup_pipe()

        return ret

    def on_err_output(self, source, condition):
        ret = self.handle_source(source, condition, 'stderr-line')
        if ret is False and self.err_channel:
            try:
                self.err_channel.shutdown(True)
            except:
                pass
            self.err_channel = None
            self.err_channel_id = 0
            self.cleanup_pipe()

        return ret

    def cleanup_pipe(self):
        if self.in_channel is None and self.out_channel is None and self.err_channel is None:
            self.pipe = None

    def stop(self, error_code=-1):
        if self.in_channel_id:
            GLib.source_remove(self.in_channel_id)
            self.in_channel.shutdown(True)
            self.in_channel = None
            self.in_channel_id = 0

        if self.out_channel_id:
            GLib.source_remove(self.out_channel_id)
            self.out_channel.shutdown(True)
            self.out_channel = None
            self.out_channel_id = 0

        if self.err_channel_id:
            GLib.source_remove(self.err_channel_id)
            self.err_channel.shutdown(True)
            self.err_channel = None
            self.err_channel = 0

        if self.pipe is not None:
            if not self.tried_killing:
                os.kill(self.pipe.pid, signal.SIGTERM)
                self.tried_killing = True
            else:
                os.kill(self.pipe.pid, signal.SIGKILL)

            self.pipe = None

    def emit_end_execute(self, error_code):
        self.emit('end-execute', error_code)
        return False

    def on_child_end(self, pid, error_code):
        # In an idle, so it is emitted after all the std*-line signals
        # have been intercepted
        GLib.idle_add(self.emit_end_execute, error_code)

# ex:ts=4:et:
