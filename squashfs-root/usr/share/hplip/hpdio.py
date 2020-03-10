#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2015 HP Development Company, L.P.
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch
#

__version__ = '0.1'
__title__ = "Services and Status System Tray Device I/O Child Process"
__mod__ = 'hpdio'
__doc__ = "Provides device I/O process isolation for system tray application."


# StdLib
import sys
import struct
import os
import time
from base.sixext.moves import queue
import select
from pickle import dumps, HIGHEST_PROTOCOL

# Local
from base.g import *
from base.codes import *
from base import utils, device, status, models
from base.sixext import PY3

# dBus
try:
    from dbus import lowlevel, SessionBus
except ImportError:
    log.error("dbus failed to load (python-dbus ver. 0.80+ required). Exiting...")
    sys.exit(1)

# Globals
PIPE_BUF = 4096
session_bus = None
r2, w3 = None, None
devices = {} # { 'device_uri' : device.Device(), ... }


def send_message(device_uri, event_code, bytes_written=0):
    args = [device_uri, '', event_code, prop.username, 0, '', '', bytes_written]
    msg = lowlevel.SignalMessage('/', 'com.hplip.StatusService', 'Event')
    msg.append(signature='ssisissi', *args)
    SessionBus().send_message(msg)


def run(read_pipe2=None,  # pipe from hpssd
        write_pipe3=None): # pipe to hpssd

    global r2, w3
#    tmp_dir = '/tmp'
    os.umask(0o111)

    try:
        log.set_module("hp-systray(hpdio)")
        log.debug("PID=%d" % os.getpid())

        r2, w3 = read_pipe2, write_pipe3

        fmt = "80s80sI32sI80sf" # TODO: Move to Event class
        fmt_size = struct.calcsize(fmt)

        response = {}
        dev = None
        m = ''
        while True:
            try:
                r, w, e = select.select([r2], [], [r2], 1.0)
            except KeyboardInterrupt:
                break
            except select.error as e:
                if e[0] == errno.EINTR:
                    continue
                else:
                    break

            if not r: continue
            if e: break
            m = os.read(r2, fmt_size)
            if not m:
                break

            while len(m) >= fmt_size:
                response.clear()
                event = device.Event(*[x.rstrip(b'\x00').decode('utf-8') if isinstance(x, bytes) else x for x in struct.unpack(fmt, m[:fmt_size])])
                m = m[fmt_size:]

                action = event.event_code
                if PY3:
                     device_uri = event.device_uri
                else:
                     device_uri = str(event.device_uri)

                log.debug("Handling event...")
                event.debug()

                send_message(device_uri, EVENT_DEVICE_UPDATE_ACTIVE)

                if action in (EVENT_DEVICE_UPDATE_REQUESTED, EVENT_POLLING_REQUEST):
                    #try:
                    if 1:
                        #log.debug("%s starting for %s" % (ACTION_NAMES[action], device_uri))

                        try:
                            dev = devices[device_uri]
                        except KeyError:
                            dev = devices[device_uri] = device.Device(device_uri, disable_dbus=True)

                        try:
                            #print "Device.open()"
                            dev.open()
                        except Error as e:
                            log.error(e.msg)
                            response = {'error-state': ERROR_STATE_ERROR,
                                        'device-state': DEVICE_STATE_NOT_FOUND,
                                        'status-code' : EVENT_ERROR_DEVICE_IO_ERROR}

                        if dev.device_state == DEVICE_STATE_NOT_FOUND:
                            dev.error_state = ERROR_STATE_ERROR
                        else:
                            if action == EVENT_DEVICE_UPDATE_REQUESTED:
                                try:
                                    #print "Device.queryDevice()"
                                    dev.queryDevice()

                                except Error as e:
                                    log.error("Query device error (%s)." % e.msg)
                                    dev.error_state = ERROR_STATE_ERROR
                                    dev.status_code = EVENT_ERROR_DEVICE_IO_ERROR

                                response = dev.dq
                                #print response

                                log.debug("Device state = %d" % dev.device_state)
                                log.debug("Status code = %d" % dev.status_code)
                                log.debug("Error state = %d" % dev.error_state)

                            else: # EVENT_POLLING_REQUEST
                                try:
                                    dev.pollDevice()

                                except Error as e:
                                    log.error("Poll device error (%s)." % e.msg)
                                    dev.error_state = ERROR_STATE_ERROR

                                else:
                                    response = {'test' : 1}

                    #finally:
                    if 1:
                        if dev is not None:
                            dev.close()

                    #thread_activity_lock.release()

                elif action == EVENT_USER_CONFIGURATION_CHANGED:
                    pass

                elif action == EVENT_SYSTEMTRAY_EXIT:
                    log.debug("Exiting")
                    sys.exit(1)

                send_message(device_uri, EVENT_DEVICE_UPDATE_INACTIVE)

                if action == EVENT_DEVICE_UPDATE_REQUESTED:
                    #print response
                    data = dumps(response, HIGHEST_PROTOCOL)

                    log.debug("Sending data through pipe to hpssd...")
                    total_written = 0
                    while True:
                        total_written += os.write(w3, data[:PIPE_BUF])
                        data = data[PIPE_BUF:]
                        if not data:
                            break

                    log.debug("Wrote %d bytes" % total_written)

                    send_message(device_uri, EVENT_DEVICE_UPDATE_REPLY, total_written)

                elif action == EVENT_POLLING_REQUEST:
                    # TODO: Translate into event: scan requested, copy requested, etc.. send as event
                    #try:
                    #    os.write
                    pass


    except KeyboardInterrupt:
        log.debug("Ctrl-C: Exiting...")
