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

__version__ = '12.0'
__title__ = "Services and Status System Tray dBus Child/Parent Process"
__mod__ = 'hpssd'
__doc__ = "Provides persistent data and event services to HPLIP client applications. Required to be running for PC send fax, optional in all other cases."


# StdLib
import sys
import struct
import os
import time
import getopt
import select
import signal
import tempfile
#import threading
#import Queue
from pickle import loads, HIGHEST_PROTOCOL

# Local
from base.g import *
from base.codes import *
from base import utils, device, status, models, module, services, os_utils
from base.sixext import PY3
from base.sixext import to_bytes_utf8
# dBus
try:
    from dbus import lowlevel, SystemBus, SessionBus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    if PY3:
        try:
            from gi._gobject import MainLoop, timeout_add, threads_init, io_add_watch, IO_IN #python3-gi version: 3.4.0
        except:
            from gi.repository.GLib import MainLoop, timeout_add, threads_init, io_add_watch, IO_IN #python3-gi version: 3.8.0
    else:
        from gobject import MainLoop, timeout_add, threads_init, io_add_watch, IO_IN
    dbus_loaded = True
except ImportError:
    log.error("dbus failed to load (python-dbus ver. 0.80+ required). Exiting...")
    dbus_loaded = False
    sys.exit(1)

import warnings
# Ignore: .../dbus/connection.py:242: DeprecationWarning: object.__init__() takes no parameters
# (occurring on Python 2.6/dBus 0.83/Ubuntu 9.04)
warnings.simplefilter("ignore", DeprecationWarning)


# Globals
PIPE_BUF = 4096
dbus_loop, main_loop = None, None
system_bus = None
session_bus = None
w1, w2, r3 = None, None, None
devices = {} # { 'device_uri' : DeviceCache, ... }


# ***********************************************************************************
#
# DEVICE CACHE
#
# ***********************************************************************************

class DeviceCache(object):
    def __init__(self, model=''):
        self.history = utils.RingBuffer(prop.history_size) # circular buffer of device.Event
        self.model = models.normalizeModelName(model)
        self.cache = {} # variable name : value
        self.faxes = {} # (username, jobid): FaxEvent
        self.dq = {} # last device query results
        #self.backoff = False
        self.backoff_counter = 0  # polling backoff: 0 = none, x = backed off by x intervals
        self.backoff_countdown = 0
        self.polling = False # indicates whether its in the device polling list


#  dbus interface on session bus
class StatusService(dbus.service.Object):
    def __init__(self, name, object_path):
        dbus.service.Object.__init__(self, name, object_path)


    @dbus.service.method('com.hplip.StatusService', in_signature='s', out_signature='sa(ssisisd)')
    def GetHistory(self, device_uri):
        log.debug("GetHistory('%s')" % device_uri)
        send_systray_blip()
        try:
            devices[device_uri]
        except KeyError:
            #log.warn("Unknown device URI: %s" % device_uri)
            return (device_uri, [])
        else:
            h = devices[device_uri].history.get()
            log.debug("%d events in history:" % len(h))
            [x.debug() for x in h]
            return (device_uri, [x.as_tuple() for x in h])


    @dbus.service.method('com.hplip.StatusService', in_signature='s', out_signature='sa{ss}')
    def GetStatus(self, device_uri):
        log.debug("GetStatus('%s')" % device_uri)
        send_systray_blip()
        try:
            devices[device_uri]
        except KeyError:
            #log.warn("Unknown device URI: %s" % device_uri)
            return (device_uri, {})
        else:
            t = {}
            dq = devices[device_uri].dq
            [t.setdefault(x, str(dq[x])) for x in list(dq.keys())]
            log.debug(t)
            return (device_uri, t)


    @dbus.service.method('com.hplip.StatusService', in_signature='ssi', out_signature='i')
    def SetCachedIntValue(self, device_uri, key, value):
        log.debug("SetCachedIntValue('%s', '%s', %d)" % (device_uri, key, value))
        if check_device(device_uri) == ERROR_SUCCESS:
            devices[device_uri].cache[key] = value
            return value

        return -1


    @dbus.service.method('com.hplip.StatusService', in_signature='ss', out_signature='i')
    def GetCachedIntValue(self, device_uri, key):
        try:
            ret = devices[device_uri].cache[key]
        except KeyError:
            ret = -1

        log.debug("GetCachedIntValue('%s', '%s') --> %d" % (device_uri, key, ret))
        return ret


    @dbus.service.method('com.hplip.StatusService', in_signature='sss', out_signature='s')
    def SetCachedStrValue(self, device_uri, key, value):
        log.debug("SetCachedStrValue('%s', '%s', '%s')" % (device_uri, key, value))
        if check_device(device_uri) == ERROR_SUCCESS:
            devices[device_uri].cache[key] = value
            return value

        return ''


    @dbus.service.method('com.hplip.StatusService', in_signature='ss', out_signature='s')
    def GetCachedStrValue(self, device_uri, key):
        try:
            ret = devices[device_uri].cache[key]
        except KeyError:
            ret = ''

        log.debug("GetCachedStrValue('%s', '%s') --> %s" % (device_uri, key, ret))
        return ret


    # Pass a non-zero job_id to retrieve a specific fax
    # Pass zero for job_id to retrieve any avail. fax
    @dbus.service.method('com.hplip.StatusService', in_signature='ssi', out_signature='ssisisds')
    def CheckForWaitingFax(self, device_uri, username, job_id=0):
        log.debug("CheckForWaitingFax('%s', '%s', %d)" % (device_uri, username, job_id))
        send_systray_blip()
        r = (device_uri, '', 0, username, job_id, '', 0.0, '')
        check_device(device_uri)
        show_waiting_faxes(device_uri)

        if job_id: # check for specific job_id
            try:
                devices[device_uri].faxes[(username, job_id)]
            except KeyError:
                return r
            else:
                return self.check_for_waiting_fax_return(device_uri, username, job_id)

        else: # return any matching one from cache. call mult. times to get all.
            for u, j in list(devices[device_uri].faxes.keys()):
                if u == username:
                    return self.check_for_waiting_fax_return(device_uri, u, j)

            return r


    # if CheckForWaitingFax returns a fax job, that job is removed from the cache
    def check_for_waiting_fax_return(self, d, u, j):
        log.debug("Fax (username=%s, jobid=%d) removed from faxes and returned to caller." % (u, j))
        r = devices[d].faxes[(u, j)].as_tuple()
        del devices[d].faxes[(u, j)]
        show_waiting_faxes(d)
        return r


    # Alternate way to "send" an event rather than using a signal message
    @dbus.service.method('com.hplip.StatusService', in_signature='ssisis', out_signature='')
    def SendEvent(self, device_uri, printer_name, event_code, username, job_id, title):
        event = device.Event(device_uri, printer_name, event_code, username, job_id, title)
        handle_event(event)



def check_device(device_uri):
    if not PY3:
        device_uri = str(device_uri)

    try:
        devices[device_uri]
    except KeyError:
        log.debug("New device: %s" % device_uri)
        try:
            back_end, is_hp, bus, model, serial, dev_file, host, zc, port = \
                device.parseDeviceURI(device_uri)
        except Error:
            log.debug("Invalid device URI: %s" % device_uri)
            return ERROR_INVALID_DEVICE_URI

        devices[device_uri] = DeviceCache(model)

    return ERROR_SUCCESS


def create_history(event):
    history = devices[event.device_uri].history.get()

    if history and history[-1].event_code == event.event_code:
        log.debug("Duplicate event. Replacing previous event.")
        devices[event.device_uri].history.replace(event)
        return True
    else:
        devices[event.device_uri].history.append(event)
        return False



def handle_fax_event(event, pipe_name):
    if event.event_code == EVENT_FAX_RENDER_COMPLETE and \
        event.username == prop.username:

        fax_file_fd, fax_file_name = tempfile.mkstemp(prefix="hpfax-")
        pipe = os.open(pipe_name, os.O_RDONLY)
        bytes_read = 0
        while True:
            data = os.read(pipe, PIPE_BUF)
            if not data:
                break

            os.write(fax_file_fd, data)
            bytes_read += len(data)

        log.debug("Saved %d bytes to file %s" % (bytes_read, fax_file_name))

        os.close(pipe)
        os.close(fax_file_fd)

        devices[event.device_uri].faxes[(event.username, event.job_id)] = \
            device.FaxEvent(fax_file_name, event)

        show_waiting_faxes(event.device_uri)

        try:
            os.waitpid(-1, os.WNOHANG)
        except OSError:
            pass

        # See if hp-sendfax is already running for this queue
        ok, lock_file = utils.lock_app('hp-sendfax-%s' % event.printer_name, True)

        if ok:
            # able to lock, not running...
            utils.unlock(lock_file)

            path = utils.which('hp-sendfax')
            if path:
                path = os.path.join(path, 'hp-sendfax')
            else:
                log.error("Unable to find hp-sendfax on PATH.")
                return

            log.debug("Running hp-sendfax: %s --printer=%s" % (path, event.printer_name))
            os.spawnlp(os.P_NOWAIT, path, 'hp-sendfax',
                '--printer=%s' % event.printer_name)

        else:
            # cannot lock file - hp-sendfax is running
            # no need to do anything... hp-sendfax is polling
            log.debug("hp-sendfax is running. Waiting for CheckForWaitingFax() call.")

    else:
        log.warn("Not handled!")
        pass


def show_waiting_faxes(d):
    f = devices[d].faxes

    if not len(f):
        log.debug("No faxes waiting for %s" % d)
    else:
        if len(f) == 1:
            log.debug("1 fax waiting for %s:" % d)
        else:
            log.debug("%d faxes waiting for %s:" % (len(f), d))

        [f[x].debug() for x in f]


# Qt4 only
def handle_hpdio_event(event, bytes_written):
    log.debug("Reading %d bytes from hpdio pipe..." % bytes_written)
    total_read, data = 0, to_bytes_utf8('')

    while True:
        r, w, e = select.select([r3], [], [r3], 0.0)
        if not r: break

        x = os.read(r3, PIPE_BUF)
        if not x: break

        data = to_bytes_utf8('').join([data, x])
        total_read += len(x)

        if total_read == bytes_written: break

    log.debug("Read %d bytes" % total_read)

    if total_read == bytes_written:
        dq = loads(data)

        if check_device(event.device_uri) == ERROR_SUCCESS:
            devices[event.device_uri].dq = dq.copy()

            handle_event(device.Event(event.device_uri, '',
                dq.get('status-code', STATUS_PRINTER_IDLE), prop.username, 0, ''))

            send_toolbox_event(event, EVENT_DEVICE_UPDATE_REPLY)

def handle_plugin_install():

    child_process=os.fork()
    if child_process== 0:    # child process
        lockObj = utils.Sync_Lock("/tmp/pluginInstall.tmp")
        lockObj.acquire()
        child_pid=os.getpid()
        from installer import pluginhandler
        pluginObj = pluginhandler.PluginHandle()

        if pluginObj.getStatus() != PLUGIN_INSTALLED:
            os_utils.execute('hp-diagnose_plugin')
        else:
            log.debug("Device Plug-in was already installed. Not Invoking Plug-in installation wizard")

        lockObj.release()
        os.kill(child_pid,signal.SIGKILL)
    else: #parent process
        log.debug("Started Plug-in installation wizard")
    

def handle_printer_diagnose():
    path = utils.which('hp-diagnose_queues')
    if path:
        path = os.path.join(path, 'hp-diagnose_queues')
    else:
        log.error("Unable to find hp-diagnose_queues on PATH.")
        return

    log.debug("Running hp-diagnose_queues: %s" % (path))
    os.spawnlp(os.P_NOWAIT, path, 'hp-diagnose_queues','-s')


def handle_event(event, more_args=None):
    #global polling_blocked
    #global request_queue

   # checking if any zombie child process exists. then cleaning same.
    try:
        os.waitpid(0, os.WNOHANG)
    except OSError:
        pass

    log.debug("Handling event...")

    if more_args is None:
        more_args = []

    event.debug()

    if event.event_code == EVENT_AUTO_CONFIGURE:
        handle_plugin_install()
        return

    if event.event_code == EVENT_DIAGNOSE_PRINTQUEUE:
        handle_printer_diagnose()
        return
        
    if event.device_uri and check_device(event.device_uri) != ERROR_SUCCESS:
        return

    # If event-code > 10001, its a PJL error code, so convert it
    if event.event_code > EVENT_MAX_EVENT:
        event.event_code = status.MapPJLErrorCode(event.event_code)

    # regular user/device status event
    if event.event_code < EVENT_MIN_USER_EVENT:
        pass

    elif EVENT_MIN_USER_EVENT <= event.event_code <= EVENT_MAX_USER_EVENT:

        if event.device_uri:
            #event.device_uri = event.device_uri.replace('hpfax:', 'hp:')
            dup_event = create_history(event)

            if event.event_code in (EVENT_DEVICE_STOP_POLLING,
                                    EVENT_START_MAINT_JOB,
                                    EVENT_START_COPY_JOB,
                                    EVENT_START_FAX_JOB,
                                    EVENT_START_PRINT_JOB):
                pass # stop polling (increment counter)

            elif event.event_code in (EVENT_DEVICE_START_POLLING, # should this event force counter to 0?
                                      EVENT_END_MAINT_JOB,
                                      EVENT_END_COPY_JOB,
                                      EVENT_END_FAX_JOB,
                                      EVENT_END_PRINT_JOB,
                                      EVENT_PRINT_FAILED_MISSING_PLUGIN,
                                      EVENT_SCANNER_FAIL,
                                      EVENT_END_SCAN_JOB,
                                      EVENT_SCAN_FAILED_MISSING_PLUGIN,
                                      EVENT_FAX_JOB_FAIL,
                                      EVENT_FAX_JOB_CANCELED,
                                      EVENT_FAX_FAILED_MISSING_PLUGIN,
                                      EVENT_COPY_JOB_FAIL,
                                      EVENT_COPY_JOB_CANCELED):
                pass # start polling if counter <= 0
                # TODO: Do tools send END event if canceled or failed? Should they?
                # TODO: What to do if counter doesn't hit 0 after a period? Timeout?
                # TODO: Also, need to deal with the backoff setting (or it completely sep?)

        # Send to system tray icon if available
        if not dup_event: # and event.event_code != STATUS_PRINTER_IDLE:
            send_event_to_systray_ui(event)

        # send EVENT_HISTORY_UPDATE signal to hp-toolbox
        send_toolbox_event(event, EVENT_HISTORY_UPDATE)

        if event.event_code in (EVENT_PRINT_FAILED_MISSING_PLUGIN, EVENT_SCAN_FAILED_MISSING_PLUGIN,EVENT_FAX_FAILED_MISSING_PLUGIN):
            handle_plugin_install()

    # Handle fax signals
    elif EVENT_FAX_MIN <= event.event_code <= EVENT_FAX_MAX and more_args:
        log.debug("Fax event")
        pipe_name = str(more_args[0])
        handle_fax_event(event, pipe_name)

    elif event.event_code == EVENT_USER_CONFIGURATION_CHANGED:
        # Sent if polling, hiding, etc. configuration has changed
    #    send_event_to_hpdio(event)
        send_event_to_systray_ui(event)

    elif event.event_code == EVENT_SYS_CONFIGURATION_CHANGED: # Not implemented
        #send_event_to_hpdio(event)
        send_event_to_systray_ui(event)

    # Qt4 only
    elif event.event_code in (EVENT_DEVICE_UPDATE_REQUESTED,):
                              #EVENT_DEVICE_START_POLLING,  # ?  Who handles polling? hpssd? probably...
                              #EVENT_DEVICE_STOP_POLLING):  # ?
        send_event_to_hpdio(event)

    # Qt4 only
    elif event.event_code in (EVENT_DEVICE_UPDATE_ACTIVE,
                              EVENT_DEVICE_UPDATE_INACTIVE):
        send_event_to_systray_ui(event)

    # Qt4 only
    elif event.event_code == EVENT_DEVICE_UPDATE_REPLY:
        bytes_written = int(more_args[1])
        handle_hpdio_event(event, bytes_written)

    # Qt4 only
    elif event.event_code == EVENT_CUPS_QUEUES_ADDED or event.event_code == EVENT_CUPS_QUEUES_REMOVED:
        send_event_to_systray_ui(event)
        send_toolbox_event(event, EVENT_HISTORY_UPDATE)

    # Qt4 only
    elif event.event_code == EVENT_SYSTEMTRAY_EXIT:
        send_event_to_hpdio(event)
        send_toolbox_event(event)
        send_event_to_systray_ui(event)
        log.debug("Exiting")
        main_loop.quit()

    elif event.event_code in (EVENT_DEVICE_START_POLLING,
                              EVENT_DEVICE_STOP_POLLING):
        pass

    else:
        log.error("Unhandled event: %d" % event.event_code)



def send_systray_blip():
    send_event_to_systray_ui(device.Event('', '', EVENT_DEVICE_UPDATE_BLIP))


def send_event_to_systray_ui(event, event_code=None):
    e = event.copy()

    if event_code is not None:
        e.event_code = event_code

    e.send_via_pipe(w1, 'systemtray')


def send_event_to_hpdio(event):
    event.send_via_pipe(w2, 'hpdio')


def send_toolbox_event(event, event_code=None):
    global session_bus

    e = event.copy()

    if event_code is not None:
        e.event_code = event_code

    e.send_via_dbus(session_bus, 'com.hplip.Toolbox')



def handle_signal(typ, *args, **kwds):
    if kwds['interface'] == 'com.hplip.StatusService' and \
        kwds['member'] == 'Event':

        event = device.Event(*args[:6])
        return handle_event(event, args[6:])


def handle_system_signal(*args, **kwds):
    return handle_signal('system', *args, **kwds)


def handle_session_signal(*args, **kwds):
    return handle_signal('session', *args, **kwds)



def run(write_pipe1=None,  # write pipe to systemtray
        write_pipe2=None,  # write pipe to hpdio
        read_pipe3=None):  # read pipe from hpdio

    global dbus_loop, main_loop
    global system_bus, session_bus
    global w1, w2, r3

    log.set_module("hp-systray(hpssd)")
    log.debug("PID=%d" % os.getpid())
    w1, w2, r3 = write_pipe1, write_pipe2, read_pipe3

    dbus_loop = DBusGMainLoop(set_as_default=True)
    main_loop = MainLoop()

    try:
        system_bus = SystemBus(mainloop=dbus_loop)
    except dbus.exceptions.DBusException as e:
        log.error("Unable to connect to dbus system bus. Exiting.")
        sys.exit(1)

    try:
        session_bus = dbus.SessionBus()
    except dbus.exceptions.DBusException as e:
        if os.getuid() != 0:
            log.error("Unable to connect to dbus session bus. Exiting.")
            sys.exit(1)
        else:
            log.error("Unable to connect to dbus session bus (running as root?)")
            sys.exit(1)

    # Receive events from the system bus
    system_bus.add_signal_receiver(handle_system_signal, sender_keyword='sender',
        destination_keyword='dest', interface_keyword='interface',
        member_keyword='member', path_keyword='path')

    # Receive events from the session bus
    session_bus.add_signal_receiver(handle_session_signal, sender_keyword='sender',
        destination_keyword='dest', interface_keyword='interface',
        member_keyword='member', path_keyword='path')

    # Export an object on the session bus
    session_name = dbus.service.BusName("com.hplip.StatusService", session_bus)
    status_service = StatusService(session_name, "/com/hplip/StatusService")

    log.debug("Entering main dbus loop...")
    try:
        main_loop.run()
    except KeyboardInterrupt:
        log.debug("Ctrl-C: Exiting...")

