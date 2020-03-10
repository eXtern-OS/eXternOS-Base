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
# Author: Don Welch, Naga Samrat Chowdary Narla
#

# Std Lib
import socket
import re
import gzip
import os.path
import time
from .sixext.moves import urllib_request, urllib_parse, urllib_error
import io
from io import BytesIO
from .sixext.moves import http_client
import struct
import string
import time
# Local
from .g import *
from .codes import *
from . import utils
from . import services
from . import os_utils
from . import status
from . import pml
from . import status
from prnt import pcl, ldl, cups
from . import models, mdns, slp, avahi
from .strings import *
from .sixext import PY3, to_bytes_utf8, to_unicode, to_string_latin, to_string_utf8, xStringIO

http_result_pat = re.compile("""HTTP/\d.\d\s(\d+)""", re.I)

HTTP_OK = 200
HTTP_ERROR = 500

try:
    import hpmudext
except ImportError:
    if not os.getenv("HPLIP_BUILD"):
        log.error("HPMUDEXT could not be loaded. Please check HPLIP installation.")
        sys.exit(1)
else:
    # Workaround for build machine
    try:
        MAX_BUFFER = hpmudext.HPMUD_BUFFER_SIZE
    except AttributeError:
        MAX_BUFFER = 8192

dbus_avail = False
dbus_disabled = False
try:
    import dbus
    from dbus import lowlevel, SessionBus
    dbus_avail = True
except ImportError:
    log.warn("python-dbus not installed.")

import warnings
# Ignore: .../dbus/connection.py:242: DeprecationWarning: object.__init__() takes no parameters
# (occurring on Python 2.6/dBus 0.83/Ubuntu 9.04)
warnings.simplefilter("ignore", DeprecationWarning)


DEFAULT_PROBE_BUS = ['usb', 'par', 'cups']
VALID_BUSES = ('par', 'net', 'cups', 'usb') #, 'bt', 'fw')
VALID_BUSES_WO_CUPS = ('par', 'net', 'usb')
DEFAULT_FILTER = None
VALID_FILTERS = ('print', 'scan', 'fax', 'pcard', 'copy')
DEFAULT_BE_FILTER = ('hp',)

pat_deviceuri = re.compile(r"""(.*):/(.*?)/(\S*?)\?(?:serial=(\S*)|device=(\S*)|ip=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[^&]*)|zc=(\S+)|hostname=(\S+))(?:&port=(\d))?""", re.IGNORECASE)
http_pat_url = re.compile(r"""/(.*?)/(\S*?)\?(?:serial=(\S*)|device=(\S*))&loc=(\S*)""", re.IGNORECASE)
direct_pat = re.compile(r'direct (.*?) "(.*?)" "(.*?)" "(.*?)"', re.IGNORECASE)

# Pattern to check for ; at end of CTR fields
# Note: If ; not present, CTR value is invalid
pat_dynamic_ctr = re.compile(r"""CTR:\d*\s.*;""", re.IGNORECASE)

# Cache for model data
model_dat = models.ModelData()

ip_pat = re.compile(r"""\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b""", re.IGNORECASE)
dev_pat = re.compile(r"""/dev/.+""", re.IGNORECASE)
usb_pat = re.compile(r"""(\d+):(\d+)""", re.IGNORECASE)


class Event(object):
    def __init__(self, device_uri, printer_name, event_code,
                 username=prop.username, job_id=0, title='',
                 timedate=0):

        self.device_uri = to_unicode(device_uri)
        self.printer_name = to_unicode(printer_name)
        self.event_code = int(event_code)
        self.username = to_unicode(username)
        self.job_id = int(job_id)
        self.title = to_unicode(title)

        if timedate:
            self.timedate = float(timedate)
        else:
            self.timedate = time.time()

        self.pipe_fmt = "80s80sI32sI80sf"
        self.dbus_fmt = "ssisisd"


    def debug(self):
        log.debug("    device_uri=%s" % self.device_uri)
        log.debug("    printer_name=%s" % self.printer_name)
        log.debug("    event_code=%d" % self.event_code)
        log.debug("    username=%s" % self.username)
        log.debug("    job_id=%d" % self.job_id)
        log.debug("    title=%s" % self.title)
        log.debug("    timedate=%s" % self.timedate)


    def pack_for_pipe(self):
        return struct.pack(self.pipe_fmt, self.device_uri.encode('utf-8'), self.printer_name.encode('utf-8'),
                self.event_code, self.username.encode('utf-8'), self.job_id, self.title.encode('utf-8'),
                self.timedate)


    def send_via_pipe(self, fd, recipient='hpssd'):
        if fd is not None:
            log.debug("Sending event %d to %s (via pipe %d)..." % (self.event_code, recipient, fd))
            try:
                os.write(fd, self.pack_for_pipe())
                return True
            except OSError:
                log.debug("Failed.")
                return False


    def send_via_dbus(self, session_bus, interface='com.hplip.StatusService'):
        if session_bus is not None and dbus_avail:
            log.debug("Sending event %d to %s (via dbus)..." % (self.event_code, interface))
            msg = lowlevel.SignalMessage('/', interface, 'Event')
            msg.append(signature=self.dbus_fmt, *self.as_tuple())
            session_bus.send_message(msg)


    def copy(self):
        return Event(*self.as_tuple())


    def __str__(self):
        return "<Event('%s', '%s', %d, '%s', %d, '%s', %f)>" % self.as_tuple()


    def as_tuple(self):
        return (self.device_uri, self.printer_name, self.event_code,
             self.username, self.job_id, self.title, self.timedate)


class FaxEvent(Event):
    def __init__(self, temp_file, event):
        Event.__init__(self, *event.as_tuple())
        self.temp_file = temp_file
        self.pipe_fmt = "80s80sI32sI80sfs"
        self.dbus_fmt = "ssisisfs"


    def debug(self):
        log.debug("FAX:")
        Event.debug(self)
        log.debug("    temp_file=%s" % self.temp_file)


    def __str__(self):
        return "<FaxEvent('%s', '%s', %d, '%s', %d, '%s', %f, '%s')>" % self.as_tuple()


    def as_tuple(self):
        return (self.device_uri, self.printer_name, self.event_code,
             self.username, self.job_id, self.title, self.timedate,
             self.temp_file)



class DeviceIOEvent(Event):
    def __init__(self, bytes_written, event):
        Event.__init__(self, *event.as_tuple())
        self.bytes_written = bytes_written
        self.pipe_fmt = "80s80sI32sI80sfI"
        self.dbus_fmt = "ssisisfi"


    def debug(self):
        log.debug("DEVIO:")
        Event.debug(self)
        log.debug("    bytes_written=%d" % self.bytes_written)


    def __str__(self):
        return "<DeviceIOEvent('%s', '%s', %d, '%s', %d, '%s', %f, '%d')>" % self.as_tuple()


    def as_tuple(self):
        return (self.device_uri, self.printer_name, self.event_code,
             self.username, self.job_id, self.title, self.timedate,
             self.bytes_written)


#
# DBus Support
#

def init_dbus(dbus_loop=None):
    global dbus_avail
    service = None
    session_bus = None

    if not prop.gui_build:
        dbus_avail = False
        return dbus_avail, None,  None

    if dbus_avail and not dbus_disabled:
        if os.getuid() == 0:
            log.debug("Not starting dbus: running as root.")
            dbus_avail = False
            return dbus_avail, None,  None

        try:
            if dbus_loop is None:
                session_bus = dbus.SessionBus()
            else:
                session_bus = dbus.SessionBus(dbus_loop)
        except dbus.exceptions.DBusException as e:
            if os.getuid() != 0:
                log.error("Unable to connect to dbus session bus. %s "%e)
            else:
                log.debug("Unable to connect to dbus session bus (running as root?). %s "%e)

            dbus_avail = False
            return dbus_avail, None,  None

        try:
            log.debug("Connecting to com.hplip.StatusService (try #1)...")
            service = session_bus.get_object('com.hplip.StatusService', "/com/hplip/StatusService")
            dbus_avail = True
        except dbus.exceptions.DBusException as e:
            try:
                os.waitpid(-1, os.WNOHANG)
            except OSError:
                pass

            path = utils.which('hp-systray')
            if path:
                path = os.path.join(path, 'hp-systray')
            else:
                path = os.path.join(prop.home_dir, 'systray.py')
                if not os.path.exists(path):
                    log.warn("Unable to start hp-systray")
                    return False, None,  None

            log.debug("Running hp-systray: %s --force-startup" % path)

            os.spawnlp(os.P_NOWAIT, path, 'hp-systray', '--force-startup')

            log.debug("Waiting for hp-systray to start...")
            time.sleep(1)

            t = 2
            while True:
                try:
                    log.debug("Connecting to com.hplip.StatusService (try #%d)..." % t)
                    service = session_bus.get_object('com.hplip.StatusService', "/com/hplip/StatusService")

                except dbus.exceptions.DBusException as e:
                    log.debug("Unable to connect to dbus. Is hp-systray running?")
                    t += 1

                    if t > 5:
                        log.warn("Unable to connect to dbus. Is hp-systray running?")
                        return False, None,  None

                    time.sleep(1)

                else:
                    log.debug("Connected.")
                    dbus_avail = True
                    break

    return dbus_avail, service,  session_bus


#
# Make URI from parameter (bus ID, IP address, etc)
#

def makeURI(param, port=1):
    cups_uri, sane_uri, fax_uri = '', '', ''
    found = False

    if dev_pat.search(param) is not None: # parallel
        log.debug("Trying parallel with %s" % param)

        result_code, uri = hpmudext.make_par_uri(param)

        if result_code == hpmudext.HPMUD_R_OK and uri:
            uri = to_string_utf8(uri)
            log.debug("Found: %s" % uri)
            found = True
            cups_uri = uri
        else:
            log.debug("Not found.")

    elif usb_pat.search(param) is not None: # USB
        match_obj = usb_pat.search(param)
        usb_bus_id = match_obj.group(1)
        usb_dev_id = match_obj.group(2)

        log.debug("Trying USB with bus=%s dev=%s..." % (usb_bus_id, usb_dev_id))
        result_code, uri = hpmudext.make_usb_uri(usb_bus_id, usb_dev_id)

        if result_code == ERROR_SUCCESS and uri:
            uri = to_string_utf8(uri)
            log.debug("Found: %s" % uri)
            found = True
            cups_uri = uri
        else:
            log.debug("Not found.")

    elif ip_pat.search(param) is not None: # IPv4 dotted quad
        log.debug("Trying IP address %s" % param)

        result_code, uri = hpmudext.make_net_uri(param, port)

        if result_code == hpmudext.HPMUD_R_OK and uri:
            uri = to_string_utf8(uri)
            log.debug("Found: %s" % uri)
            found = True
            cups_uri = uri
        else:
            log.debug("Not found.")

    else: # Try Zeroconf hostname
        log.debug("Trying ZC hostname %s" % param)

        result_code, uri = hpmudext.make_zc_uri(param, port)

        if result_code == hpmudext.HPMUD_R_OK and uri:
            uri = to_string_utf8(uri)
            log.debug("Found: %s" % uri)
            found = True
            cups_uri = uri

        else: # Try DNS hostname
            log.debug("Device not found using mDNS hostname. Trying with DNS hostname %s" % param)

            result_code, uri = hpmudext.make_net_uri(param, port)

            if result_code == hpmudext.HPMUD_R_OK and uri:
                uri = to_string_utf8(uri)
                uri = uri.replace("ip=","hostname=")
                log.debug("Found: %s" % uri)
                found = True
                cups_uri = uri
            else:
                log.debug("Not found.")

    if not found:
        log.debug("Trying serial number %s" % param)
        devices = probeDevices(bus=['usb', 'par'])

        for d in devices:
            log.debug(d)

            # usb has serial in URI...
            try:
                back_end, is_hp, bus, model, serial, dev_file, host, zc, port = \
                    parseDeviceURI(d)
            except Error:
                continue

            if bus == 'par': # ...parallel does not. Must get Device ID to obtain it...
                mq = queryModelByURI(d)

                result_code, device_id = \
                    hpmudext.open_device(d, mq.get('io-mode', hpmudext.HPMUD_UNI_MODE))

                if result_code == hpmudext.HPMUD_R_OK:
                    result_code, data = hpmudext.get_device_id(device_id)
                    serial = parseDeviceID(data).get('SN', '')
                    hpmudext.close_device(device_id)

            if serial.lower() == param.lower():
                log.debug("Found: %s" % d)
                found = True
                cups_uri = d
                break
            else:
                log.debug("Not found.")

    if found:
        try:
            mq = queryModelByURI(cups_uri)
        except Error as e:
            log.error("Error: %s" % e.msg)
            cups_uri, sane_uri, fax_uri = '', '', ''
        else:
            if mq.get('support-type', SUPPORT_TYPE_NONE) > SUPPORT_TYPE_NONE:
                if mq.get('scan-type', 0):
                    sane_uri = cups_uri.replace("hp:", "hpaio:")

                if mq.get('fax-type', 0):
                    fax_uri = cups_uri.replace("hp:", "hpfax:")

            else:
                cups_uri, sane_uri, fax_uri = '', '', ''

    else:
        scan_uri, fax_uri = '', ''

    if cups_uri:
        user_conf.set('last_used', 'device_uri', cups_uri)

    return cups_uri, sane_uri, fax_uri


#
# Model Queries
#

def queryModelByModel(model):
    model = models.normalizeModelName(model).lower()
    return model_dat[model]


def queryModelByURI(device_uri):
    try:
        back_end, is_hp, bus, model, \
            serial, dev_file, host, zc, port = \
            parseDeviceURI(device_uri)
    except Error:
        raise Error(ERROR_INVALID_DEVICE_URI)
    else:
        return queryModelByModel(model)


#
# Device Discovery
#

def probeDevices(bus=DEFAULT_PROBE_BUS, timeout=10,
                 ttl=4, filter=DEFAULT_FILTER,  search='', net_search='slp',
                 back_end_filter=('hp',)):

    num_devices, ret_devices = 0, {}

    if search:
        try:
            search_pat = re.compile(search, re.IGNORECASE)
        except:
            log.error("Invalid search pattern. Search uses standard regular expressions. For more info, see: http://www.amk.ca/python/howto/regex/")
            search = ''

    for b in bus:
        log.debug("Probing bus: %s" % b)
        if b not in VALID_BUSES:
            log.error("Invalid bus: %s" % b)
            continue

        if b == 'net':
            if net_search == 'slp':
                try:
                    detected_devices = slp.detectNetworkDevices(ttl, timeout)
                except Error as socket_error:
                    socket.error = socket_error
                    log.error("An error occured during network probe.[%s]"%socket_error)
                    raise ERROR_INTERNAL
            elif net_search == 'avahi':
                try:
                    detected_devices = avahi.detectNetworkDevices(ttl, timeout)
                except Error as socket_error:
                    socket.error = socket_error
                    log.error("An error occured during network probe.[%s]"%socket_error)
                    raise ERROR_INTERNAL
            else :#if net_search = 'mdns'
                try:
                    detected_devices = mdns.detectNetworkDevices(ttl, timeout)
                except Error as socket_error:
                    socket.error = socket_error
                    log.error("An error occured during network probe.[%s]"%socket_error)
                    raise ERROR_INTERNAL

            for ip in detected_devices:
                update_spinner()
                hn = detected_devices[ip].get('hn', '?UNKNOWN?')
                num_devices_on_jd = detected_devices[ip].get('num_devices', 0)
                num_ports_on_jd = detected_devices[ip].get('num_ports', 1)

                if num_devices_on_jd > 0:
                    for port in range(num_ports_on_jd):
                        dev = detected_devices[ip].get('device%d' % (port+1), '0')

                        if dev is not None and dev != '0':
                            device_id = parseDeviceID(dev)
                            model = models.normalizeModelName(device_id.get('MDL', '?UNKNOWN?'))

                            if num_ports_on_jd == 1:
                                if net_search == 'slp':
                                    device_uri = 'hp:/net/%s?ip=%s' % (model, ip)
                                else:
                                    device_uri = 'hp:/net/%s?zc=%s' % (model, hn)
                            else:
                                if net_search == 'slp':
                                    device_uri = 'hp:/net/%s?ip=%s&port=%d' % (model, ip, (port + 1))
                                else:
                                    device_uri = 'hp:/net/%s?zc=%s&port=%d' % (model, hn, (port + 1))

                            include = True
                            mq = queryModelByModel(model)

                            if not mq:
                                log.debug("Not found.")
                                include = False

                            elif int(mq.get('support-type', SUPPORT_TYPE_NONE)) == SUPPORT_TYPE_NONE:
                                log.debug("Not supported.")
                                include = False

                            elif filter not in (None, 'print', 'print-type'):
                                include = __checkFilter(filter, mq)

                            if include:
                                ret_devices[device_uri] = (model, model, hn)

        elif b in ('usb', 'par'):
            if b == 'par':
                bn = hpmudext.HPMUD_BUS_PARALLEL
            else:
                bn = hpmudext.HPMUD_BUS_USB

            result_code, data = hpmudext.probe_devices(bn)
            if result_code == hpmudext.HPMUD_R_OK:
                for x in data.splitlines():
                    m = direct_pat.match(x)

                    uri = m.group(1) or ''
                    mdl = m.group(2) or ''
                    desc = m.group(3) or ''
                    devid = m.group(4) or ''

                    log.debug(uri)
                    #if("scanjet" in  mdl.lower()):
                    #    continue # Do not include HP Scanjets

                    try:
                        back_end, is_hp, bb, model, serial, dev_file, host, zc, port = \
                            parseDeviceURI(uri)
                    except Error:
                        continue

                    include = True

                    if mdl and uri and is_hp:
                        mq = queryModelByModel(model)

                        if not mq:
                            log.debug("Not found.")
                            include = False

                        elif int(mq.get('support-type', SUPPORT_TYPE_NONE)) == SUPPORT_TYPE_NONE:
                            log.debug("Not supported.")
                            include = False

                        elif filter not in (None, 'print', 'print-type'):
                            include = __checkFilter(filter, mq)

                        if include:
                            ret_devices[uri] = (mdl, desc, devid) # model w/ _'s, mdl w/o

        elif b == 'cups':
            cups_printers = cups.getPrinters()
            x = len(cups_printers)

            for p in cups_printers:
                device_uri = p.device_uri
                log.debug("%s: %s" % (device_uri, p.name))

                if device_uri != '':
                    try:
                        back_end, is_hp, bs, model, serial, dev_file, host, zc, port = \
                            parseDeviceURI(device_uri)
                    except Error:
                        log.debug("Unrecognized URI: %s" % device_uri)
                        continue

                    if not is_hp:
                        continue

                    include = True
                    mq = queryModelByModel(model)

                    if not mq:
                        include = False
                        log.debug("Not found.")

                    elif int(mq.get('support-type', SUPPORT_TYPE_NONE)) == SUPPORT_TYPE_NONE:
                        log.debug("Not supported.")
                        include = False

                    elif filter not in (None, 'print', 'print-type'):
                        include = __checkFilter(filter, mq)

                    if include:
                        ret_devices[device_uri] = (model, model, '')

    probed_devices = {}
    for uri in ret_devices:
        num_devices += 1
        mdl, model, devid_or_hn = ret_devices[uri]

        include = True
        if search:
            match_obj = search_pat.search("%s %s %s %s" % (mdl, model, devid_or_hn, uri))

            if match_obj is None:
                log.debug("%s %s %s %s: Does not match search '%s'." % (mdl, model, devid_or_hn, uri, search))
                include = False

        if include:
            probed_devices[uri] = ret_devices[uri]

    cleanup_spinner()
    return probed_devices

#
# CUPS Devices
#

def getSupportedCUPSDevices(back_end_filter=['hp'], filter=DEFAULT_FILTER):
    devices = {}
    printers = cups.getPrinters()
    log.debug(printers)

    for p in printers:
        try:
            back_end, is_hp, bus, model, serial, dev_file, host, zc, port = \
                parseDeviceURI(p.device_uri)

        except Error:
            continue

        if (back_end_filter == '*' or back_end in back_end_filter or \
            ('hpaio' in back_end_filter and back_end == 'hp')) and \
            model and is_hp:

            include = True
            mq = queryModelByModel(model)

            if not mq:
                log.debug("Not found.")
                include = False

            elif int(mq.get('support-type', SUPPORT_TYPE_NONE)) == SUPPORT_TYPE_NONE:
                log.debug("Not supported.")
                include = False

            elif filter not in (None, 'print', 'print-type'):
                include = __checkFilter(filter, mq)

            if include:
                if 'hpaio' in back_end_filter:
                    d = p.device_uri.replace('hp:', 'hpaio:')
                else:
                    d = p.device_uri

                try:
                    devices[d]
                except KeyError:
                    devices[d] = [p.name]
                else:
                    devices[d].append(p.name)

    return devices # { 'device_uri' : [ CUPS printer list ], ... }


def getSupportedCUPSPrinters(back_end_filter=['hp'], filter=DEFAULT_FILTER):
    printer_list = []
    printers = cups.getPrinters()

    for p in printers:
        try:
            back_end, is_hp, bus, model, serial, dev_file, host, zc, port = \
                parseDeviceURI(p.device_uri)

        except Error:
            continue

        if (back_end_filter == '*' or back_end in back_end_filter) and model and is_hp:
            include = True
            mq = queryModelByModel(model)

            if not mq:
                log.debug("Not found.")
                include = False

            elif int(mq.get('support-type', SUPPORT_TYPE_NONE)) == SUPPORT_TYPE_NONE:
                log.debug("Not supported.")
                include = False

            elif filter not in (None, 'print', 'print-type'):
                include = __checkFilter(filter, mq)

            if include:
                printer_list.append(p)


    return printer_list # [ cupsext.Printer, ... ]


def getSupportedCUPSPrinterNames(back_end_filter=['hp'], filter=DEFAULT_FILTER):
    printers = getSupportedCUPSPrinters(back_end_filter, filter)
    return [p.name for p in printers]


def getDeviceURIByPrinterName(printer_name, scan_uri_flag=False):
    if printer_name is None:
        return None

    device_uri = None
    printers = cups.getPrinters()

    for p in printers:
        try:
            back_end, is_hp, bus, model, serial, dev_file, host, zc, port = \
                parseDeviceURI(p.device_uri)

        except Error:
            continue

        if is_hp and p.name == printer_name:
            if scan_uri_flag:
                device_uri = p.device_uri.replace('hp:', 'hpaio:')
            else:
                device_uri = p.device_uri
            break

    return device_uri

#
# IEEE-1284 Device ID parsing
#

def parseDeviceID(device_id):
    d= {}
    x = [y.strip() for y in device_id.strip().split(';') if y]

    for z in x:
        y = z.split(':')
        try:
            d.setdefault(y[0].strip(), y[1])
        except IndexError:
            d.setdefault(y[0].strip(), None)

    d.setdefault('MDL', '')
    d.setdefault('SN',  '')

    if 'MODEL' in d:
        d['MDL'] = d['MODEL']
        del d['MODEL']

    if 'SERIAL' in d:
        d['SN'] = d['SERIAL']
        del d['SERIAL']

    elif 'SERN' in d:
        d['SN'] = d['SERN']
        del d['SERN']

    if d['SN'].startswith('X'):
        d['SN'] = ''

    return d

#
# IEEE-1284 Device ID Dynamic Counter Parsing
#

def parseDynamicCounter(ctr_field, convert_to_int=True):
    counter, value = ctr_field.split(' ')
    try:
        counter = int(utils.xlstrip(str(counter), '0') or '0')

        if convert_to_int:
            value = int(utils.xlstrip(str(value), '0') or '0')
    except ValueError:
        if convert_to_int:
            counter, value = 0, 0
        else:
            counter, value = 0, ''

    return counter, value


#
# Parse Device URI Strings
#

def parseDeviceURI(device_uri):
    m = pat_deviceuri.match(device_uri)
    if m is None:
        log.debug("Device URI %s is invalid/unknown" % device_uri)
        raise Error(ERROR_INVALID_DEVICE_URI)

    back_end = m.group(1).lower() or ''
    is_hp = (back_end in ('hp', 'hpfax', 'hpaio'))
    bus = m.group(2).lower() or ''

    if bus not in ('usb', 'net', 'bt', 'fw', 'par'):
        log.debug("Device URI %s is invalid/unknown" % device_uri)
        raise Error(ERROR_INVALID_DEVICE_URI)

    model = m.group(3) or ''
    serial = m.group(4) or ''
    dev_file = m.group(5) or ''
    host = m.group(6) or ''
    zc = m.group(7) or ''
    hostname = m.group(8) or ''

    if hostname:
        host = hostname
    elif zc:
        host = zc

    port = m.group(8) or 1

    if bus == 'net':
        try:
            port = int(port)
        except (ValueError, TypeError):
            port = 1

        if port == 0:
            port = 1

    log.debug("%s: back_end:%s is_hp:%s bus:%s model:%s serial:%s dev_file:%s host:%s zc:%s port:%s" %
        (device_uri, back_end, is_hp, bus, model, serial, dev_file, host, zc, port))

    return back_end, is_hp, bus, model, serial, dev_file, host, zc, port


def isLocal(bus):
    return bus in ('par', 'usb', 'fw', 'bt')


def isNetwork(bus):
    return bus in ('net',)


#
# Misc
#

def __checkFilter(filter, mq):
    for f, p in list(filter.items()):
        if f is not None:
            op, val = p
            if not op(mq[f], val):
                return False

    return True


def validateBusList(bus, allow_cups=True):
    for b in bus:
        if allow_cups:
            vb = VALID_BUSES
        else:
            vb = VALID_BUSES_WO_CUPS

        if b not in vb:
            log.error("Invalid bus name: %s" %b)
            return False

    return True


def validateFilterList(filter):
    if filter is None:
        return True

    for f in filter:
        if f not in VALID_FILTERS:
            log.error("Invalid term '%s' in filter list" % f)
            return False

    return True


AGENT_types = { AGENT_TYPE_NONE        : 'invalid',
                AGENT_TYPE_BLACK       : 'black',
                AGENT_TYPE_BLACK_B8800 : 'black',
                AGENT_TYPE_CMY         : 'cmy',
                AGENT_TYPE_KCM         : 'kcm',
                AGENT_TYPE_CYAN        : 'cyan',
                AGENT_TYPE_MAGENTA     : 'magenta',
                AGENT_TYPE_YELLOW      : 'yellow',
                AGENT_TYPE_CYAN_LOW    : 'photo_cyan',
                AGENT_TYPE_MAGENTA_LOW : 'photo_magenta',
                AGENT_TYPE_YELLOW_LOW  : 'photo_yellow',
                AGENT_TYPE_GGK         : 'photo_gray',
                AGENT_TYPE_BLUE        : 'photo_blue',
                AGENT_TYPE_KCMY_CM     : 'kcmy_cm',
                AGENT_TYPE_LC_LM       : 'photo_cyan_and_photo_magenta',
                #AGENT_TYPE_Y_M         : 'yellow_and_magenta',
                #AGENT_TYPE_C_K         : 'cyan_and_black',
                AGENT_TYPE_LG_PK       : 'light_gray_and_photo_black',
                AGENT_TYPE_LG          : 'light_gray',
                AGENT_TYPE_G           : 'medium_gray',
                AGENT_TYPE_PG          : 'photo_gray',
                AGENT_TYPE_C_M         : 'cyan_and_magenta',
                AGENT_TYPE_K_Y         : 'black_and_yellow',
                AGENT_TYPE_PHOTO_BLACK : 'photo_black',
                AGENT_TYPE_MATTE_BLACK : 'matte_black',
                AGENT_TYPE_UNSPECIFIED : 'unspecified', # Kind=5,6
            }

AGENT_kinds = {AGENT_KIND_NONE            : 'invalid',
                AGENT_KIND_HEAD            : 'head',
                AGENT_KIND_SUPPLY          : 'supply',
                AGENT_KIND_HEAD_AND_SUPPLY : 'cartridge',
                AGENT_KIND_TONER_CARTRIDGE : 'toner',
                AGENT_KIND_MAINT_KIT       : 'maint_kit', # fuser
                AGENT_KIND_ADF_KIT         : 'adf_kit',
                AGENT_KIND_DRUM_KIT        : 'drum_kit',
                AGENT_KIND_TRANSFER_KIT    : 'transfer_kit',
                AGENT_KIND_INT_BATTERY     : 'battery',
                AGENT_KIND_UNKNOWN         : 'unknown',
              }

AGENT_healths = {AGENT_HEALTH_OK           : 'ok',
                  AGENT_HEALTH_MISINSTALLED : 'misinstalled', # supply/cart
                  #AGENT_HEALTH_FAIR_MODERATE : '',
                  AGENT_HEALTH_INCORRECT    : 'incorrect',
                  AGENT_HEALTH_FAILED       : 'failed',
                  AGENT_HEALTH_OVERTEMP     : 'overtemp', # battery
                  AGENT_HEALTH_CHARGING     : 'charging', # battery
                  AGENT_HEALTH_DISCHARGING  : 'discharging', # battery
                  AGENT_HEALTH_UNKNOWN      : 'unknown',
                }


AGENT_levels = {AGENT_LEVEL_TRIGGER_MAY_BE_LOW : 'low',
                 AGENT_LEVEL_TRIGGER_PROBABLY_OUT : 'low',
                 AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT : 'out',
               }




# **************************************************************************** #

string_cache = {}

class Device(object):
    def __init__(self, device_uri, printer_name=None,
                 service=None, callback=None, disable_dbus=False):

        log.debug("Device URI: %s" % device_uri)
        log.debug("Printer: %s" % printer_name)

        global dbus_disabled
        dbus_disabled = disable_dbus

        if not disable_dbus:
            if service is None:
                self.dbus_avail, self.service,  session_bus = init_dbus()
            else:
                self.dbus_avail = True
                self.service = service
        else:
            self.dbus_avail = False
            self.service = None

        self.last_event = None # Used in devmgr if dbus is disabled

        printers = cups.getPrinters()

        if device_uri is None and printer_name is not None:
            for p in printers:
                if p.name.lower() == printer_name.lower():
                    device_uri = p.device_uri
                    log.debug("Device URI: %s" % device_uri)
                    break
            else:
                raise Error(ERROR_DEVICE_NOT_FOUND)

        self.device_uri = device_uri
        self.callback = callback
        self.device_type = DEVICE_TYPE_UNKNOWN

        if self.device_uri is None:
            raise Error(ERROR_DEVICE_NOT_FOUND)

        if self.device_uri.startswith('hp:'):
            self.device_type = DEVICE_TYPE_PRINTER

        elif self.device_uri.startswith('hpaio:'):
            self.device_type = DEVICE_TYPE_SCANNER

        elif self.device_uri.startswith('hpfax:'):
            self.device_type = DEVICE_TYPE_FAX

        try:
            self.back_end, self.is_hp, self.bus, self.model, \
                self.serial, self.dev_file, self.host, self.zc, self.port = \
                parseDeviceURI(self.device_uri)
        except Error:
            self.io_state = IO_STATE_NON_HP
            raise Error(ERROR_INVALID_DEVICE_URI)

        log.debug("URI: backend=%s, is_hp=%s, bus=%s, model=%s, serial=%s, dev=%s, host=%s, port=%d" % \
            (self.back_end, self.is_hp, self.bus, self.model, self.serial, self.dev_file, self.host, self.port))

        self.model_ui = models.normalizeModelUIName(self.model)
        self.model = models.normalizeModelName(self.model)

        log.debug("Model/UI model: %s/%s" % (self.model, self.model_ui))

        if self.bus == 'net':
            self.http_host = self.host
        else:
            self.http_host = 'localhost'  

        # TODO:
        #service.setAlertsEx(self.hpssd_sock)

        self.mq = {} # Model query
        self.dq = {} # Device query
        self.icon = "default_printer"
        self.cups_printers = []
        self.channels = {} # { 'SERVICENAME' : channel_id, ... }
        self.device_id = -1
        self.r_values = None # ( r_value, r_value_str, rg, rr )
        self.deviceID = ''
        self.panel_check = True
        self.io_state = IO_STATE_HP_READY
        self.is_local = isLocal(self.bus)
        self.hist = []

        self.supported = False

        self.queryModel()
        if not self.supported:
            log.error("Unsupported model: %s" % self.model)
            self.error_code = STATUS_DEVICE_UNSUPPORTED
            self.sendEvent(self.error_code)
        else:
            self.supported = True


        self.mq.update({'model'    : self.model,
                        'model-ui' : self.model_ui})

        self.error_state = ERROR_STATE_ERROR
        self.device_state = DEVICE_STATE_NOT_FOUND
        self.status_code = EVENT_ERROR_DEVICE_NOT_FOUND

        self.updateCUPSPrinters()

        if self.mq.get('fax-type', FAX_TYPE_NONE) != FAX_TYPE_NONE:
            self.dq.update({ 'fax-uri' : self.device_uri.replace('hp:/', 'hpfax:/').replace('hpaio:/', 'hpfax:/')})

        if self.mq.get('scan-type', SCAN_TYPE_NONE) != SCAN_TYPE_NONE:
            self.dq.update({ 'scan-uri' : self.device_uri.replace('hp:/', 'hpaio:/').replace('hpfax:/', 'hpaio:/')})

        self.dq.update({
            'back-end'         : self.back_end,
            'is-hp'            : self.is_hp,
            'serial'           : self.serial,
            'dev-file'         : self.dev_file,
            'host'             : self.host,
            'port'             : self.port,
            'cups-printers'    : self.cups_printers,
            'status-code'      : self.status_code,
            'status-desc'      : '',
            'deviceid'         : '',
            'panel'            : 0,
            'panel-line1'      : '',
            'panel-line2'      : '',
            'device-state'     : self.device_state,
            'error-state'      : self.error_state,
            'device-uri'       : self.device_uri,
            'cups-uri'         : self.device_uri.replace('hpfax:/', 'hp:/').replace('hpaio:/', 'hp:/'),
            })

        self.device_vars = {
            'URI'        : self.device_uri,
            'DEVICE_URI' : self.device_uri,
            'SCAN_URI'   : self.device_uri.replace('hp:', 'hpaio:'),
            'SANE_URI'   : self.device_uri.replace('hp:', 'hpaio:'),
            'FAX_URI'    : self.device_uri.replace('hp:', 'hpfax:'),
            'PRINTER'    : self.first_cups_printer,
            'HOME'       : prop.home_dir,
                           }




    def sendEvent(self, event_code, printer_name='', job_id=0, title=''):
        if self.dbus_avail and self.service is not None:
            try:
                log.debug("Sending event %d to hpssd..." % event_code)
                self.service.SendEvent(self.device_uri, printer_name, event_code, prop.username, job_id, title)
            except dbus.exceptions.DBusException as e:
                log.debug("dbus call to SendEvent() failed.")


    def quit(self):
        pass


    def queryModel(self):
        if not self.mq:
            self.mq = queryModelByURI(self.device_uri)

        self.supported = bool(self.mq)

        if self.supported:
            for m in self.mq:
                self.__dict__[m.replace('-','_')] = self.mq[m]


    def queryString(self, string_id):
        return queryString(string_id)


    def open(self, open_for_printing=False):
        if self.supported and self.io_state in (IO_STATE_HP_READY, IO_STATE_HP_NOT_AVAIL):
            prev_device_state = self.device_state
            self.io_state = IO_STATE_HP_NOT_AVAIL
            self.device_state = DEVICE_STATE_NOT_FOUND
            self.error_state = ERROR_STATE_ERROR
            self.status_code = EVENT_ERROR_DEVICE_NOT_FOUND
            self.device_id = -1
            self.open_for_printing = open_for_printing

            if open_for_printing:
                log.debug("Opening device: %s (for printing)" % self.device_uri)
                self.io_mode = self.mq.get('io-mode', hpmudext.HPMUD_UNI_MODE)
            else:
                log.debug("Opening device: %s (not for printing)" % self.device_uri)
                self.io_mode = self.mq.get('io-mfp-mode', hpmudext.HPMUD_UNI_MODE)

            log.debug("I/O mode=%d" % self.io_mode)
            result_code, self.device_id = \
                hpmudext.open_device(self.device_uri, self.io_mode)

            if result_code != hpmudext.HPMUD_R_OK:
                self.error_state = ERROR_STATE_ERROR
                self.error_code = result_code+ERROR_CODE_BASE
                self.sendEvent(self.error_code)

                if result_code == hpmudext.HPMUD_R_DEVICE_BUSY:
                    log.error("Device busy: %s" % self.device_uri)
                else:
                    log.error("Unable to communicate with device (code=%d): %s" % (result_code, self.device_uri))

                self.last_event = Event(self.device_uri, '', EVENT_ERROR_DEVICE_NOT_FOUND,
                        prop.username, 0, '', time.time())

                raise Error(ERROR_DEVICE_NOT_FOUND)

            else:
                log.debug("device-id=%d" % self.device_id)
                self.io_state = IO_STATE_HP_OPEN
                self.error_state = ERROR_STATE_CLEAR
                log.debug("Opened device: %s (backend=%s, is_hp=%s, bus=%s, model=%s, dev=%s, serial=%s, host=%s, port=%d)" %
                    (self.back_end, self.device_uri, self.is_hp, self.bus, self.model,
                     self.dev_file, self.serial, self.host, self.port))

                if prev_device_state == DEVICE_STATE_NOT_FOUND:
                    self.device_state = DEVICE_STATE_JUST_FOUND
                else:
                    self.device_state = DEVICE_STATE_FOUND

                self.getDeviceID()
                self.getSerialNumber()
                return self.device_id


    def close(self):
        if self.io_state == IO_STATE_HP_OPEN:
            log.debug("Closing device...")

            if len(self.channels) > 0:

                for c in list(self.channels.keys()):
                    self.__closeChannel(c)

            result_code = hpmudext.close_device(self.device_id)
            log.debug("Result-code = %d" % result_code)

            self.channels.clear()
            self.io_state = IO_STATE_HP_READY


    def __openChannel(self, service_name):
        try:
            if self.io_state == IO_STATE_HP_OPEN:
                if service_name == hpmudext.HPMUD_S_PRINT_CHANNEL and not self.open_for_printing:
                    self.close()
                    self.open(True)
                elif service_name != hpmudext.HPMUD_S_PRINT_CHANNEL and self.open_for_printing:
                    self.close()
                    self.open(False)
            else:
                self.open(service_name == hpmudext.HPMUD_S_PRINT_CHANNEL)
        except:
            log.error("unable to open channel")
            return -1

        #if not self.mq['io-mode'] == IO_MODE_UNI:
        if 1:
            service_name = service_name.upper()

            if service_name not in self.channels:
                log.debug("Opening %s channel..." % service_name)

                result_code, channel_id = hpmudext.open_channel(self.device_id, service_name)

                self.channels[service_name] = channel_id
                log.debug("channel-id=%d" % channel_id)
                return channel_id
            else:
                return self.channels[service_name]
        else:
            return -1


    def openChannel(self, service_name):
        return self.__openChannel(service_name)

    def openPrint(self):
        return self.__openChannel(hpmudext.HPMUD_S_PRINT_CHANNEL)

    def openFax(self):
        return self.__openChannel(hpmudext.HPMUD_S_FAX_SEND_CHANNEL)

    def openPCard(self):
        return self.__openChannel(hpmudext.HPMUD_S_MEMORY_CARD_CHANNEL)

    def openEWS(self):
        return self.__openChannel(hpmudext.HPMUD_S_EWS_CHANNEL)

    def openEWS_LEDM(self):
        return self.__openChannel(hpmudext.HPMUD_S_EWS_LEDM_CHANNEL)

    def openLEDM(self):
        return self.__openChannel(hpmudext.HPMUD_S_LEDM_SCAN)

    def openMarvell_EWS(self):
        return self.__openChannel(hpmudext.HPMUD_S_MARVELL_EWS_CHANNEL)

    def closePrint(self):
        return self.__closeChannel(hpmudext.HPMUD_S_PRINT_CHANNEL)

    def closePCard(self):
        return self.__closeChannel(hpmudext.HPMUD_S_MEMORY_CARD_CHANNEL)

    def closeFax(self):
        return self.__closeChannel(hpmudext.HPMUD_S_FAX_SEND_CHANNEL)

    def openPML(self):
        return self.__openChannel(hpmudext.HPMUD_S_PML_CHANNEL)

    def openWifiConfig(self):
        return self.__openChannel(hpmudext.HPMUD_S_WIFI_CHANNEL)

    def closePML(self):
        return self.__closeChannel(hpmudext.HPMUD_S_PML_CHANNEL)

    def closeEWS(self):
        return self.__closeChannel(hpmudext.HPMUD_S_EWS_CHANNEL)

    def closeEWS_LEDM(self):
        return self.__closeChannel(hpmudext.HPMUD_S_EWS_LEDM_CHANNEL)

    def closeLEDM(self):
        return self.__closeChannel(hpmudext.HPMUD_S_LEDM_SCAN)

    def closeMarvell_EWS(self):
        return self.__closeChannel(hpmudext.HPMUD_S_MARVELL_EWS_CHANNEL)

    def openCfgUpload(self):
        return self.__openChannel(hpmudext.HPMUD_S_CONFIG_UPLOAD_CHANNEL)

    def closeCfgUpload(self):
        return self.__closeChannel(hpmudext.HPMUD_S_CONFIG_UPLOAD_CHANNEL)

    def openCfgDownload(self):
        return self.__openChannel(hpmudext.HPMUD_S_CONFIG_DOWNLOAD_CHANNEL)

    def closeCfgDownload(self):
        return self.__closeChannel(hpmudext.HPMUD_S_CONFIG_DOWNLOAD_CHANNEL)

    def openSoapFax(self):
        return self.__openChannel(hpmudext.HPMUD_S_SOAP_FAX)

    def openMarvellFax(self):
        return self.__openChannel(hpmudext.HPMUD_S_MARVELL_FAX_CHANNEL)

    def closeSoapFax(self):
        return self.__closeChannel(hpmudext.HPMUD_S_SOAP_FAX)

    def closeMarvellFax(self):
        return self.__closeChannel(hpmudext.HPMUD_S_MARVELL_FAX_CHANNEL)

    def closeWifiConfig(self):
        return self.__closeChannel(hpmudext.HPMUD_S_WIFI_CHANNEL)

    def __closeChannel(self, service_name):
        #if not self.mq['io-mode'] == IO_MODE_UNI and \
        if self.io_state == IO_STATE_HP_OPEN:

            service_name = service_name.upper()

            if service_name in self.channels:
                log.debug("Closing %s channel..." % service_name)

                result_code = hpmudext.close_channel(self.device_id,
                    self.channels[service_name])

                del self.channels[service_name]


    def closeChannel(self, service_name):
        return self.__closeChannel(service_name)


    def getDeviceID(self):
        needs_close = False
        self.raw_deviceID = ''
        self.deviceID = {}

        if self.io_state != IO_STATE_HP_OPEN:
           try:
               self.open()
           except:
               return -1
           needs_close = True

        result_code, data = hpmudext.get_device_id(self.device_id)

        if result_code == hpmudext.HPMUD_R_OK:
            self.raw_deviceID = data
            self.deviceID = parseDeviceID(data)

        if needs_close:
            self.close()

        return self.deviceID


    def getSerialNumber(self):
        if self.serial:
            return

        try:
            self.serial = self.deviceID['SN']
        except KeyError:
            pass
        else:
            if self.serial:
                return

        if self.mq.get('status-type', STATUS_TYPE_NONE) != STATUS_TYPE_NONE: # and \
            #not self.mq.get('io-mode', IO_MODE_UNI) == IO_MODE_UNI:

            try:
                try:
                    error_code, self.serial = self.getPML(pml.OID_SERIAL_NUMBER)
                except Error:
                    self.serial = ''
            finally:
                self.closePML()

        if self.serial is None:
            self.serial = ''


    def getThreeBitStatus(self):
        pass


    def getStatusFromDeviceID(self):
        self.getDeviceID()
        return status.parseStatus(parseDeviceID(self.raw_deviceID))


    def __parseRValues(self, r_value):
        r_value_str = str(r_value)
        r_value_str = ''.join(['0'*(9 - len(r_value_str)), r_value_str])
        rg, rr = r_value_str[:3], r_value_str[3:]
        r_value = int(rr)
        self.r_values = r_value, r_value_str, rg, rr
        return r_value, r_value_str, rg, rr


    def getRValues(self, r_type, status_type, dynamic_counters):
        r_value, r_value_str, rg, rr = 0, '000000000', '000', '000000'

        if r_type > 0 and \
            dynamic_counters != STATUS_DYNAMIC_COUNTERS_NONE:

            if self.r_values is None:
                if self.dbus_avail:
                    try:
                        r_value = int(self.service.GetCachedIntValue(self.device_uri, 'r_value'))
                    except dbus.exceptions.DBusException as e:
                        log.debug("dbus call to GetCachedIntValue() failed.")
                        r_value = -1

                if r_value != -1:
                    log.debug("r_value=%d" % r_value)
                    r_value, r_value_str, rg, rr = self.__parseRValues(r_value)

                    return r_value, r_value_str, rg, rr

            if self.r_values is None:

                if status_type ==  STATUS_TYPE_S and \
                    self.is_local and \
                    dynamic_counters != STATUS_DYNAMIC_COUNTERS_PML_SNMP:

                    try:
                        try:
                            r_value = self.getDynamicCounter(140)

                            if r_value is not None:
                                log.debug("r_value=%d" % r_value)
                                r_value, r_value_str, rg, rr = self.__parseRValues(r_value)

                                if self.dbus_avail:
                                    try:
                                        self.service.SetCachedIntValue(self.device_uri, 'r_value', r_value)
                                    except dbus.exceptions.DBusException as e:
                                        log.debug("dbus call to SetCachedIntValue() failed.")
                            else:
                                log.error("Error attempting to read r-value (2).")
                                r_value = 0
                        except Error:
                            log.error("Error attempting to read r-value (1).")
                            r_value = 0
                    finally:
                        self.closePrint()


                elif (status_type ==  STATUS_TYPE_S and
                      dynamic_counters == STATUS_DYNAMIC_COUNTERS_PCL and
                      not self.is_local) or \
                      dynamic_counters == STATUS_DYNAMIC_COUNTERS_PML_SNMP:

                    try:
                        result_code, r_value = self.getPML(pml.OID_R_SETTING)

                        if r_value is not None:
                            log.debug("r_value=%d" % r_value)
                            r_value, r_value_str, rg, rr = self.__parseRValues(r_value)

                            if self.dbus_avail:
                                try:
                                    self.service.SetCachedIntValue(self.device_uri, 'r_value', r_value)
                                except dbus.exceptions.DBusException as e:
                                    log.debug("dbus call to SetCachedIntValue() failed.")

                        else:
                            r_value = 0

                    finally:
                        self.closePML()

            else:
                r_value, r_value_str, rg, rr = self.r_values

        return r_value, r_value_str, rg, rr


    def __queryFax(self, quick=False, reread_cups_printers=False):
        io_mode = self.mq.get('io-mode', IO_MODE_UNI)
        self.status_code = STATUS_PRINTER_IDLE

        if io_mode != IO_MODE_UNI:

            if self.device_state != DEVICE_STATE_NOT_FOUND:
                if self.tech_type in (TECH_TYPE_MONO_INK, TECH_TYPE_COLOR_INK):
                    try:
                        self.getDeviceID()
                    except Error as e:
                        log.error("Error getting device ID.")
                        self.last_event = Event(self.device_uri, '', ERROR_DEVICE_IO_ERROR,
                            prop.username, 0, '', time.time())

                        raise Error(ERROR_DEVICE_IO_ERROR)

                status_desc = self.queryString(self.status_code)

                self.dq.update({
                    'serial'           : self.serial,
                    'cups-printers'    : self.cups_printers,
                    'status-code'      : self.status_code,
                    'status-desc'      : status_desc,
                    'deviceid'         : self.raw_deviceID,
                    'panel'            : 0,
                    'panel-line1'      : '',
                    'panel-line2'      : '',
                    'device-state'     : self.device_state,
                    'error-state'      : self.error_state,
                    })


            log.debug("Fax activity check...")

            tx_active, rx_active = status.getFaxStatus(self)

            if tx_active:
                self.status_code = STATUS_FAX_TX_ACTIVE
            elif rx_active:
                self.status_code = STATUS_FAX_RX_ACTIVE

            self.error_state = STATUS_TO_ERROR_STATE_MAP.get(self.status_code, ERROR_STATE_CLEAR)
            self.error_code = self.status_code
            self.sendEvent(self.error_code)

            try:
                self.dq.update({'status-desc' : self.queryString(self.status_code),
                                'error-state' : self.error_state,
                                })

            except (KeyError, Error):
                self.dq.update({'status-desc' : '',
                                'error-state' : ERROR_STATE_CLEAR,
                                })


            if self.panel_check:
                self.panel_check = bool(self.mq.get('panel-check-type', 0))

            status_type = self.mq.get('status-type', STATUS_TYPE_NONE)
            if self.panel_check and \
                status_type in (STATUS_TYPE_LJ, STATUS_TYPE_S, STATUS_TYPE_VSTATUS) and \
                io_mode != IO_MODE_UNI:

                log.debug("Panel check...")
                try:
                    self.panel_check, line1, line2 = status.PanelCheck(self)
                finally:
                    self.closePML()

                self.dq.update({'panel': int(self.panel_check),
                                  'panel-line1': line1,
                                  'panel-line2': line2,})

            if not quick and reread_cups_printers:
                self.updateCUPSPrinters()

        for d in self.dq:
            self.__dict__[d.replace('-','_')] = self.dq[d]

        self.last_event = Event(self.device_uri, '', self.status_code, prop.username, 0, '', time.time())

        log.debug(self.dq)



    def updateCUPSPrinters(self):
        self.cups_printers = []
        log.debug("Re-reading CUPS printer queue information.")
        printers = cups.getPrinters()
        for p in printers:
            if self.device_uri == p.device_uri:
                self.cups_printers.append(p.name)
                self.state = p.state # ?

                if self.io_state == IO_STATE_NON_HP:
                    self.model = p.makemodel.split(',')[0]

        self.dq.update({'cups-printers' : self.cups_printers})

        try:
            self.first_cups_printer = self.cups_printers[0]
        except IndexError:
            self.first_cups_printer = ''




    def queryDevice(self, quick=False, reread_cups_printers=False):
        if not self.supported:
            self.dq = {}

            self.last_event = Event(self.device_uri, '', STATUS_DEVICE_UNSUPPORTED,
                prop.username, 0, '', time.time())

            return

        if self.device_type == DEVICE_TYPE_FAX:
            return self.__queryFax(quick, reread_cups_printers)

        r_type = self.mq.get('r-type', 0)
        tech_type = self.mq.get('tech-type', TECH_TYPE_NONE)
        status_type = self.mq.get('status-type', STATUS_TYPE_NONE)
        battery_check = self.mq.get('status-battery-check', STATUS_BATTERY_CHECK_NONE)
        dynamic_counters = self.mq.get('status-dynamic-counters', STATUS_DYNAMIC_COUNTERS_NONE)
        io_mode = self.mq.get('io-mode', IO_MODE_UNI)
        io_mfp_mode = self.mq.get('io-mfp-mode', IO_MODE_UNI)
        status_code = STATUS_UNKNOWN

        # Turn off status if local connection and bi-di not avail.
        #if io_mode  == IO_MODE_UNI and self.back_end != 'net':
        #    status_type = STATUS_TYPE_NONE

        agents = []

        if self.device_state != DEVICE_STATE_NOT_FOUND:
            if self.tech_type in (TECH_TYPE_MONO_INK, TECH_TYPE_COLOR_INK):
                try:
                    self.getDeviceID()
                except Error as e:
                    log.error("Error getting device ID.")
                    self.last_event = Event(self.device_uri, '', ERROR_DEVICE_IO_ERROR,
                        prop.username, 0, '', time.time())

                    raise Error(ERROR_DEVICE_IO_ERROR)

            status_desc = self.queryString(self.status_code)

            self.dq.update({
                'serial'           : self.serial,
                'cups-printers'    : self.cups_printers,
                'status-code'      : self.status_code,
                'status-desc'      : status_desc,
                'deviceid'         : self.raw_deviceID,
                'panel'            : 0,
                'panel-line1'      : '',
                'panel-line2'      : '',
                'device-state'     : self.device_state,
                'error-state'      : self.error_state,
                })

            status_block = {}

            if status_type == STATUS_TYPE_NONE:
                log.warn("No status available for device.")
                status_block = {'status-code' : STATUS_UNKNOWN}

            elif status_type in (STATUS_TYPE_VSTATUS, STATUS_TYPE_S):
                log.debug("Type 1/2 (S: or VSTATUS:) status")
                status_block = status.parseStatus(self.deviceID)

            elif status_type in (STATUS_TYPE_LJ, STATUS_TYPE_PML_AND_PJL):
                log.debug("Type 3/9 LaserJet PML(+PJL) status")
                status_block = status.StatusType3(self, self.deviceID)

            elif status_type == STATUS_TYPE_LJ_XML:
                log.debug("Type 6: LJ XML")
                status_block = status.StatusType6(self)

            elif status_type == STATUS_TYPE_PJL:
                log.debug("Type 8: LJ PJL")
                status_block = status.StatusType8(self)

            elif status_type == STATUS_TYPE_LEDM:
                log.debug("Type 10: LEDM")
                status_block = status.StatusType10(self.getEWSUrl_LEDM)

            elif status_type == STATUS_TYPE_LEDM_FF_CC_0:
                log.debug("Type 11: LEDM_FF_CC_0")
                status_block = status.StatusType10(self.getUrl_LEDM)

            elif status_type == STATUS_TYPE_IPP:
                log.debug("Type 12: IPP")
                status_block = status.StatusTypeIPP(self.device_uri)

            else:
                log.error("Unimplemented status type: %d" % status_type)

            if battery_check and \
                io_mode != IO_MODE_UNI:

                log.debug("Battery check...")
                status.BatteryCheck(self, status_block, battery_check)

            if status_block:
                log.debug(status_block)
                self.dq.update(status_block)
                try:
                    status_block['agents']
                except KeyError:
                    pass
                else:
                    agents = status_block['agents']
                    del self.dq['agents']


            status_code = self.dq.get('status-code', STATUS_UNKNOWN)

            self.error_state = STATUS_TO_ERROR_STATE_MAP.get(status_code, ERROR_STATE_CLEAR)
            self.error_code = status_code
            self.sendEvent(self.error_code)

            try:
                self.dq.update({'status-desc' : self.queryString(status_code),
                                'error-state' : self.error_state,
                                })

            except (KeyError, Error):
                self.dq.update({'status-desc' : '',
                                'error-state' : ERROR_STATE_CLEAR,
                                })

            r_value = 0

            if not quick and status_type != STATUS_TYPE_NONE:
                if self.panel_check:
                    self.panel_check = bool(self.mq.get('panel-check-type', 0))

                if self.panel_check and \
                    status_type in (STATUS_TYPE_LJ, STATUS_TYPE_S, STATUS_TYPE_VSTATUS) and \
                    io_mode != IO_MODE_UNI:

                    log.debug("Panel check...")
                    try:
                        self.panel_check, line1, line2 = status.PanelCheck(self)
                    finally:
                        self.closePML()

                    self.dq.update({'panel': int(self.panel_check),
                                      'panel-line1': line1,
                                      'panel-line2': line2,})


                if dynamic_counters != STATUS_DYNAMIC_COUNTERS_NONE and \
                    io_mode != IO_MODE_UNI:

                    r_value, r_value_str, rg, rr = self.getRValues(r_type, status_type, dynamic_counters)
                else:
                    r_value, r_value_str, rg, rr = 0, '000000000', '000', '000000'

                self.dq.update({'r'  : r_value,
                                'rs' : r_value_str,
                                'rg' : rg,
                                'rr' : rr,
                              })

            if not quick and reread_cups_printers:
                self.updateCUPSPrinters()

            if not quick:
                # Make sure there is some valid agent data for this r_value
                # If not, fall back to r_value == 0
                if r_value > 0 and self.mq.get('r%d-agent1-kind' % r_value, 0) == 0:
                    r_value = 0
                    self.dq.update({'r'  : r_value,
                                    'rs' : r_value_str,
                                    'rg' : rg,
                                    'rr' : rr,
                                  })

                #Check if device itself is sending the supplies info. If so, then in that case we need not check model.dat static data and
                #compare with region, kind and type values.
                dynamic_sku_data = False
                for agent in agents:
                    try:
                        if agent['agent-sku'] != '':
                            dynamic_sku_data = True
                            break
                    except:
                        pass

                a, aa = 1, 1
                while True:
                    if dynamic_sku_data:
                        if a > len(agents):
                            break
                        agent = agents[a-1]
                        mq_agent_sku = agent['agent-sku']
                        agent_kind = agent['kind']
                        agent_type = agent['type']
                        found = True
                    else:
                        mq_agent_kind = self.mq.get('r%d-agent%d-kind' % (r_value, a), -1)
                        if mq_agent_kind == -1:
                            break
                        mq_agent_type = self.mq.get('r%d-agent%d-type' % (r_value, a), 0)
                        mq_agent_sku = self.mq.get('r%d-agent%d-sku' % (r_value, a), '')
                        found = False

                        log.debug("Looking for kind=%d, type=%d..." % (mq_agent_kind, mq_agent_type))
                        for agent in agents:
                            agent_kind = agent['kind']
                            agent_type = agent['type']

                            if agent_kind == mq_agent_kind and \
                               agent_type == mq_agent_type:
                                   found = True
                                   break

                    if found:
                        log.debug("found: r%d-kind%d-type%d" % (r_value, agent_kind, agent_type))

                        agent_health = agent.get('health', AGENT_HEALTH_OK)
                        agent_level = agent.get('level', 100)
                        agent_level_trigger = agent.get('level-trigger',
                            AGENT_LEVEL_TRIGGER_SUFFICIENT_0)

                        log.debug("health=%d, level=%d, level_trigger=%d, status_code=%d" %
                            (agent_health, agent_level, agent_level_trigger, status_code))

                        query = 'agent_%s_%s' % (AGENT_types.get(agent_type, 'unknown'),
                                                 AGENT_kinds.get(agent_kind, 'unknown'))

                        agent_desc = self.queryString(query)
                        query = 'agent_health_ok'

                        # If printer is not in an error state, and
                        # if agent health is OK, check for low supplies. If low, use
                        # the agent level trigger description for the agent description.
                        # Otherwise, report the agent health.
                        if (status_code == STATUS_PRINTER_POWER_SAVE or status_code == STATUS_PRINTER_IDLE or status_code == STATUS_PRINTER_OUT_OF_INK) and \
                            (agent_health == AGENT_HEALTH_OK or
                             (agent_health == AGENT_HEALTH_FAIR_MODERATE and agent_kind == AGENT_KIND_HEAD)) and \
                            agent_level_trigger >= AGENT_LEVEL_TRIGGER_MAY_BE_LOW:

                            query = 'agent_level_%s' % AGENT_levels.get(agent_level_trigger, 'unknown')

                            if tech_type in (TECH_TYPE_MONO_INK, TECH_TYPE_COLOR_INK):
                                code = agent_type + STATUS_PRINTER_LOW_INK_BASE
                            else:
                                code = agent_type + STATUS_PRINTER_LOW_TONER_BASE

                            self.dq['status-code'] = code
                            self.dq['status-desc'] = self.queryString(code)

                            self.dq['error-state'] = STATUS_TO_ERROR_STATE_MAP.get(code, ERROR_STATE_LOW_SUPPLIES)
                            self.error_code = code
                            self.sendEvent(self.error_code)

                            if agent_level_trigger in \
                                (AGENT_LEVEL_TRIGGER_PROBABLY_OUT, AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT):

                                query = 'agent_level_out'
                            else:
                                query = 'agent_level_low'

                            agent_health_desc = self.queryString(query)

                            self.dq.update(
                            {
                                'agent%d-kind' % aa :          agent_kind,
                                'agent%d-type' % aa :          agent_type,
                                'agent%d-known' % aa :         agent.get('known', False),
                                'agent%d-sku' % aa :           mq_agent_sku,
                                'agent%d-level' % aa :         agent_level,
                                'agent%d-level-trigger' % aa : agent_level_trigger,
                                'agent%d-ack' % aa :           agent.get('ack', False),
                                'agent%d-hp-ink' % aa :        agent.get('hp-ink', False),
                                'agent%d-health' % aa :        agent_health,
                                'agent%d-dvc' % aa :           agent.get('dvc', 0),
                                'agent%d-virgin' % aa :        agent.get('virgin', False),
                                'agent%d-desc' % aa :          agent_desc,
                                'agent%d-id' % aa :            agent.get('id', 0),
                                'agent%d-health-desc' % aa :   agent_health_desc,
                            })

                        else:
                            query = 'agent_health_%s' % AGENT_healths.get(agent_health, AGENT_HEALTH_OK)
                            agent_health_desc = self.queryString(query)

                            self.dq.update(
                            {
                                'agent%d-kind' % aa :          agent_kind,
                                'agent%d-type' % aa :          agent_type,
                                'agent%d-known' % aa :         False,
                                'agent%d-sku' % aa :           mq_agent_sku,
                                'agent%d-level' % aa :         agent_level,
                                'agent%d-level-trigger' % aa : agent_level_trigger,
                                'agent%d-ack' % aa :           False,
                                'agent%d-hp-ink' % aa :        False,
                                'agent%d-health' % aa :        agent_health,
                                'agent%d-dvc' % aa :           0,
                                'agent%d-virgin' % aa :        False,
                                'agent%d-desc' % aa :          agent_desc,
                                'agent%d-id' % aa :            0,
                                'agent%d-health-desc' % aa :   agent_health_desc,
                            })

                        aa += 1

                    else:
                        log.debug("Not found: %d" % a)

                    a += 1

        else: # Create agent keys for not-found devices

            r_value = 0
            if r_type > 0 and self.r_values is not None:
                r_value = self.r_values[0]

            # Make sure there is some valid agent data for this r_value
            # If not, fall back to r_value == 0
            if r_value > 0 and self.mq.get('r%d-agent1-kind', 0) == 0:
                r_value = 0

            a = 1
            while True:
                mq_agent_kind = self.mq.get('r%d-agent%d-kind' % (r_value, a), 0)

                if mq_agent_kind == 0:
                    break

                mq_agent_type = self.mq.get('r%d-agent%d-type' % (r_value, a), 0)
                mq_agent_sku = self.mq.get('r%d-agent%d-sku' % (r_value, a), '')
                query = 'agent_%s_%s' % (AGENT_types.get(mq_agent_type, 'unknown'),
                                         AGENT_kinds.get(mq_agent_kind, 'unknown'))

                agent_desc = self.queryString(query)

                self.dq.update(
                {
                    'agent%d-kind' % a :          mq_agent_kind,
                    'agent%d-type' % a :          mq_agent_type,
                    'agent%d-known' % a :         False,
                    'agent%d-sku' % a :           mq_agent_sku,
                    'agent%d-level' % a :         0,
                    'agent%d-level-trigger' % a : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
                    'agent%d-ack' % a :           False,
                    'agent%d-hp-ink' % a :        False,
                    'agent%d-health' % a :        AGENT_HEALTH_MISINSTALLED,
                    'agent%d-dvc' % a :           0,
                    'agent%d-virgin' % a :        False,
                    'agent%d-health-desc' % a :   self.queryString('agent_health_unknown'),
                    'agent%d-desc' % a :          agent_desc,
                    'agent%d-id' % a :            0,
                })

                a += 1

        for d in self.dq:
            self.__dict__[d.replace('-','_')] = self.dq[d]

        self.last_event = Event(self.device_uri, '', status_code, prop.username, 0, '', time.time())
        log.debug(self.dq)


    def isBusyOrInErrorState(self):
        try:
            self.queryDevice(quick=True)
        except Error:
            return True
        return self.error_state in (ERROR_STATE_ERROR, ERROR_STATE_BUSY)


    def isIdleAndNoError(self):
        try:
            self.queryDevice(quick=True)
        except Error:
            return False
        return self.error_state not in (ERROR_STATE_ERROR, ERROR_STATE_BUSY)


    def getPML(self, oid, desired_int_size=pml.INT_SIZE_INT): # oid => ( 'dotted oid value', pml type )
        channel_id = self.openPML()
        result_code, data, typ, pml_result_code = \
            hpmudext.get_pml(self.device_id, channel_id, pml.PMLToSNMP(oid[0]), oid[1])
        if pml_result_code > pml.ERROR_MAX_OK:
            log.debug("PML/SNMP GET %s failed (result code = 0x%x)" % (oid[0], pml_result_code))
            return pml_result_code, None

        converted_data = pml.ConvertFromPMLDataFormat(data, oid[1], desired_int_size)

        if log.is_debug():
            if oid[1] in (pml.TYPE_STRING, pml.TYPE_BINARY):

                log.debug("PML/SNMP GET %s (result code = 0x%x) returned:" %
                    (oid[0], pml_result_code))
                log.log_data(data)
            else:
                log.debug("PML/SNMP GET %s (result code = 0x%x) returned: %s" %
                    (oid[0], pml_result_code, repr(converted_data)))
        return pml_result_code, converted_data


    def setPML(self, oid, value): # oid => ( 'dotted oid value', pml type )
        channel_id = self.openPML()
        value = pml.ConvertToPMLDataFormat(value, oid[1])
        result_code, pml_result_code = \
            hpmudext.set_pml(self.device_id, channel_id, pml.PMLToSNMP(oid[0]), oid[1], value)

        if log.is_debug():
            if oid[1] in (pml.TYPE_STRING, pml.TYPE_BINARY):

                log.debug("PML/SNMP SET %s (result code = 0x%x) to:" %
                    (oid[0], pml_result_code))
            else:
                log.debug("PML/SNMP SET %s (result code = 0x%x) to: %s" %
                    (oid[0], pml_result_code, repr(value.decode('utf-8'))))

        return pml_result_code


    def getDynamicCounter(self, counter, convert_to_int=True):
        dynamic_counters = self.mq.get('status-dynamic-counters', STATUS_DYNAMIC_COUNTERS_NONE)
        log.debug("Dynamic counters: %d" % dynamic_counters)
        if dynamic_counters != STATUS_DYNAMIC_COUNTERS_NONE:

            if dynamic_counters == STATUS_DYNAMIC_COUNTERS_LIDIL_0_5_4:
                self.printData(ldl.buildResetPacket(), direct=True)
                self.printData(ldl.buildDynamicCountersPacket(counter), direct=True)
            else:
                self.printData(pcl.buildDynamicCounter(counter), direct=True)

            value, tries, times_seen, sleepy_time, max_tries = 0, 0, 0, 0.1, 5
            time.sleep(0.1)

            while True:

                if self.callback:
                    self.callback()

                sleepy_time += 0.1
                tries += 1

                time.sleep(sleepy_time)

                self.getDeviceID()

                if 'CTR' in self.deviceID and \
                    pat_dynamic_ctr.search(self.raw_deviceID) is not None:
                    dev_counter, value = parseDynamicCounter(self.deviceID['CTR'], convert_to_int)

                    if counter == dev_counter:
                        self.printData(pcl.buildDynamicCounter(0), direct=True)
                        # protect the value as a string during msg handling
                        if not convert_to_int:
                            value = '#' + value
                        return value

                if tries > max_tries:
                    if dynamic_counters == STATUS_DYNAMIC_COUNTERS_LIDIL_0_5_4:
                        self.printData(ldl.buildResetPacket())
                        self.printData(ldl.buildDynamicCountersPacket(counter), direct=True)
                    else:
                        self.printData(pcl.buildDynamicCounter(0), direct=True)

                    return None

                if dynamic_counters == STATUS_DYNAMIC_COUNTERS_LIDIL_0_5_4:
                    self.printData(ldl.buildResetPacket())
                    self.printData(ldl.buildDynamicCountersPacket(counter), direct=True)
                else:
                    self.printData(pcl.buildDynamicCounter(counter), direct=True)

        else:
            raise Error(ERROR_DEVICE_DOES_NOT_SUPPORT_OPERATION)


    def readPrint(self, bytes_to_read, stream=None, timeout=prop.read_timeout, allow_short_read=False):
        return self.__readChannel(self.openPrint, bytes_to_read, stream, timeout, allow_short_read)

    def readPCard(self, bytes_to_read, stream=None, timeout=prop.read_timeout, allow_short_read=False):
        return self.__readChannel(self.openPCard, bytes_to_read, stream, timeout, allow_short_read)

    def readFax(self, bytes_to_read, stream=None, timeout=prop.read_timeout, allow_short_read=False):
        return self.__readChannel(self.openFax, bytes_to_read, stream, timeout, allow_short_read)

    def readCfgUpload(self, bytes_to_read, stream=None, timeout=prop.read_timeout, allow_short_read=False):
        return self.__readChannel(self.openCfgUpload, bytes_to_read, stream, timeout, allow_short_read)

    def readEWS(self, bytes_to_read, stream=None, timeout=prop.read_timeout, allow_short_read=True):
        return self.__readChannel(self.openEWS, bytes_to_read, stream, timeout, allow_short_read)

    def readEWS_LEDM(self, bytes_to_read, stream=None, timeout=prop.read_timeout, allow_short_read=True):
        return self.__readChannel(self.openEWS_LEDM, bytes_to_read, stream, timeout, allow_short_read)

    def readLEDM(self, bytes_to_read, stream=None, timeout=prop.read_timeout, allow_short_read=True):
        return self.__readChannel(self.openLEDM, bytes_to_read, stream, timeout, allow_short_read)

    def readMarvell_EWS(self, bytes_to_read, stream=None, timeout=prop.read_timeout, allow_short_read=True):
        return self.__readChannel(self.openMarvell_EWS, bytes_to_read, stream, timeout, allow_short_read)

    def readSoapFax(self, bytes_to_read, stream=None, timeout=prop.read_timeout, allow_short_read=True):
        return self.__readChannel(self.openSoapFax, bytes_to_read, stream, timeout, allow_short_read)

    def readMarvellFax(self, bytes_to_read, stream=None, timeout=prop.read_timeout, allow_short_read=True):
        return self.__readChannel(self.openMarvellFax, bytes_to_read, stream, timeout, allow_short_read)

    def readWifiConfig(self, bytes_to_read, stream=None, timeout=prop.read_timeout, allow_short_read=True):
        return self.__readChannel(self.openWifiConfig, bytes_to_read, stream, timeout, allow_short_read)

#Common handling of reading chunked or unchunked data from LEDM devices
    def readLEDMData(dev, func, reply, timeout=6):

        END_OF_DATA=to_bytes_utf8("0\r\n\r\n")
        bytes_requested = 1024
        bytes_remaining = 0
        chunkedFlag = True

        bytes_read = func(bytes_requested, reply, timeout)

        for line in reply.getvalue().splitlines():
            if line.lower().find(to_bytes_utf8("content-length")) != -1:
                 bytes_remaining = int(line.split(to_bytes_utf8(":"))[1])
                 chunkedFlag = False
                 break

        xml_data_start = reply.getvalue().find(to_bytes_utf8("<?xml"))
        if (xml_data_start != -1):
            bytes_remaining = bytes_remaining - (len(reply.getvalue())  - xml_data_start)

        while bytes_read > 0:
            temp_buf = xStringIO()
            bytes_read = func(bytes_requested, temp_buf, timeout)

            reply.write(temp_buf.getvalue())

            if not chunkedFlag:     # Unchunked data
                bytes_remaining = bytes_remaining - bytes_read
                if bytes_remaining <= 0:
                    break
            elif END_OF_DATA == temp_buf.getvalue():   # Chunked data end
                    break



    def __readChannel(self, opener, bytes_to_read, stream=None,
                      timeout=prop.read_timeout, allow_short_read=False):

        channel_id = opener()

        log.debug("Reading channel %d (device-id=%d, bytes_to_read=%d, allow_short=%s, timeout=%d)..." %
            (channel_id, self.device_id, bytes_to_read, allow_short_read, timeout))

        num_bytes = 0

        if stream is None:
            buffer = to_bytes_utf8('')

        while True:
            result_code, data = \
                hpmudext.read_channel(self.device_id, channel_id, bytes_to_read, timeout)

            log.debug("Result code=%d" % result_code)

            l = len(data)

            if result_code == hpmudext.HPMUD_R_IO_TIMEOUT:
                log.debug("I/O timeout")
                break

            if result_code != hpmudext.HPMUD_R_OK:
                log.error("Channel read error")
                raise Error(ERROR_DEVICE_IO_ERROR)

            if not l:
                log.debug("End of data")
                break

            if stream is None:
                buffer = to_bytes_utf8('').join([buffer, data])
            else:
                stream.write(data)

            num_bytes += l

            if self.callback is not None:
                self.callback()

            if num_bytes == bytes_to_read:
                log.debug("Full read complete.")
                break

            if allow_short_read and num_bytes < bytes_to_read:
                log.debug("Allowed short read of %d of %d bytes complete." % (num_bytes, bytes_to_read))
                break

        if stream is None:
            log.debug("Returned %d total bytes in buffer." % num_bytes)
            return buffer
        else:
            log.debug("Saved %d total bytes to stream." % num_bytes)
            return num_bytes


    def writePrint(self, data):
        return self.__writeChannel(self.openPrint, data)

    def writePCard(self, data):
        return self.__writeChannel(self.openPCard, data)

    def writeFax(self, data):
        return self.__writeChannel(self.openFax, data)

    def writeEWS(self, data):
        return self.__writeChannel(self.openEWS, data)

    def writeEWS_LEDM(self, data):
        return self.__writeChannel(self.openEWS_LEDM, data)

    def writeLEDM(self, data):
        return self.__writeChannel(self.openLEDM, data)

    def writeMarvell_EWS(self, data):
        return self.__writeChannel(self.openMarvell_EWS, data)

    def writeCfgDownload(self, data):
        return self.__writeChannel(self.openCfgDownload, data)

    def writeSoapFax(self, data):
        return self.__writeChannel(self.openSoapFax, data)

    def writeMarvellFax(self, data):
        if not isinstance(data, bytes) and hasattr(data, 'tobytes'):   # hasattr function used for supporting 2.6
            data = data.tobytes()
        return self.__writeChannel(self.openMarvellFax, data)

    def writeWifiConfig(self, data):
        return self.__writeChannel(self.openWifiConfig, data)

    def __writeChannel(self, opener, data):
        channel_id = opener()
        buffer, bytes_out, total_bytes_to_write = data, 0, len(data)
        log.debug("Writing %d bytes to channel %d (device-id=%d)..." % (total_bytes_to_write, channel_id, self.device_id))

        while len(buffer) > 0:
            result_code, bytes_written = \
                hpmudext.write_channel(self.device_id, channel_id, 
                    buffer[:prop.max_message_len])
 
            log.debug("Result code=%d" % result_code)

            if result_code != hpmudext.HPMUD_R_OK:
                log.error("Channel write error")
                raise Error(ERROR_DEVICE_IO_ERROR)

            buffer = buffer[prop.max_message_len:]
            bytes_out += bytes_written

            if self.callback is not None:
                self.callback()

        if total_bytes_to_write != bytes_out:
            raise Error(ERROR_DEVICE_IO_ERROR)

        return bytes_out


    def writeEmbeddedPML(self, oid, value, style=1, direct=True):
        if style == 1:
            func = pcl.buildEmbeddedPML2
        else:
            func = pcl.buildEmbeddedPML

        data = func(pcl.buildPCLCmd('&', 'b', 'W',
                     pml.buildEmbeddedPMLSetPacket(oid[0],
                                                    value,
                                                    oid[1])))

        #log.log_data(data)

        self.printData(data, direct=direct, raw=True)

    def post(self, url, post):
        status_type = self.mq.get('status-type', STATUS_TYPE_NONE)
        data = """POST %s HTTP/1.1\r
Connection: Keep-alive\r
User-agent: hplip/2.0\r
Host: %s\r
Content-type: text/xml\r
Content-length: %d\r
\r
%s""" % (url, self.http_host, len(post), post)
        log.log_data(data)
        if status_type == STATUS_TYPE_LEDM:
            log.debug("status-type: %d" % status_type)
            self.writeEWS_LEDM(data)
            response = BytesIO()

            self.readLEDMData(self.readEWS_LEDM, response)

            response = response.getvalue()
            log.log_data(response)
            self.closeEWS_LEDM()

        elif status_type == STATUS_TYPE_LEDM_FF_CC_0:
            log.debug("status-type: %d" % status_type)
            self.writeLEDM(data)
            response = BytesIO()

            self.readLEDMData(self.readLEDM, response)

            response = response.getvalue()
            log.log_data(response)
            self.closeLEDM()

        else:
            log.error("Not an LEDM status-type: %d" % status_type)

        match = http_result_pat.match(to_string_utf8(response))
        if match is None: return HTTP_OK
        try:
            code = int(match.group(1))
        except (ValueError, TypeError):
            code = HTTP_ERROR

        return code == HTTP_OK

    def printGzipFile(self, file_name, printer_name=None, direct=False, raw=True, remove=False):
        return self.printFile(file_name, printer_name, direct, raw, remove)

    def printParsedGzipPostscript(self, print_file, printer_name=None):
        # always: direct=False, raw=False, remove=True
        try:
            os.stat(print_file)
        except OSError:
            log.error("File not found: %s" % print_file)
            return

        temp_file_fd, temp_file_name = utils.make_temp_file()
        f = gzip.open(print_file, 'r')

        x = f.readline()
        while not x.startswith(to_bytes_utf8('%PY_BEGIN')):
            os.write(temp_file_fd, x)
            x = f.readline()

        sub_lines = []
        x = f.readline()
        while not x.startswith(to_bytes_utf8('%PY_END')):
            sub_lines.append(x)
            x = f.readline()

        SUBS = {'VERSION' : prop.version,
                 'MODEL'   : self.model_ui,
                 'URI'     : self.device_uri,
                 'BUS'     : self.bus,
                 'SERIAL'  : self.serial,
                 'IP'      : self.host,
                 'PORT'    : self.port,
                 'DEVNODE' : self.dev_file,
                 }

        if self.bus == 'net' :
            SUBS['DEVNODE'] = 'n/a'
        else:
            SUBS['IP']= 'n/a'
            SUBS['PORT'] = 'n/a'
        
        if PY3:
            sub_lines = [s.decode('utf-8') for s in sub_lines]
        
            
        for s in sub_lines:
            os.write(temp_file_fd, to_bytes_utf8((s % SUBS)))
        

        os.write(temp_file_fd, f.read())
        f.close()
        os.close(temp_file_fd)

        self.printFile(temp_file_name, printer_name, direct=False, raw=False, remove=True)

    def printFile(self, file_name, printer_name=None, direct=False, raw=True, remove=False):
        is_gzip = os.path.splitext(file_name)[-1].lower() == '.gz'

        if printer_name is None:
            printer_name = self.first_cups_printer

            if not printer_name:
                raise Error(ERROR_NO_CUPS_QUEUE_FOUND_FOR_DEVICE)

        log.debug("Printing file '%s' to queue '%s' (gzip=%s, direct=%s, raw=%s, remove=%s)" %
                   (file_name, printer_name, is_gzip, direct, raw, remove))

        if direct: # implies raw==True
            if is_gzip:
                self.writePrint(gzip.open(file_name, 'r').read())
            else:
                self.writePrint(open(file_name, 'r').read())

        else:
            if not utils.which('lpr'):
                lp_opt = ''

                if raw:
                    lp_opt = '-oraw'

                if is_gzip:
                    c = 'gunzip -c %s | lp -c -d%s %s' % (file_name, printer_name, lp_opt)
                else:
                    c = 'lp -c -d%s %s %s' % (printer_name, lp_opt, file_name)

                exit_code = os_utils.execute(c)

                if exit_code != 0:
                    log.error("Print command failed with exit code %d!" % exit_code)

                if remove:
                    os.remove(file_name)

            else:
                raw_str, rem_str = '', ''
                if raw: raw_str = '-o raw'
                if remove: rem_str = '-r'

                if is_gzip:
                    c = 'gunzip -c %s | lpr %s %s -P%s' % (file_name, raw_str, rem_str, printer_name)
                else:
                    c = 'lpr -P%s %s %s %s' % (printer_name, raw_str, rem_str, file_name)

                exit_code = os_utils.execute(c)

                if exit_code != 0:
                    log.error("Print command failed with exit code %d!" % exit_code)


    def printTestPage(self, printer_name=None):
        return self.printParsedGzipPostscript(os.path.join( prop.home_dir, 'data',
                                              'ps', 'testpage.ps.gz' ), printer_name)


    def printData(self, data, printer_name=None, direct=True, raw=True):
        if direct:
            self.writePrint(data)
        else:
            temp_file_fd, temp_file_name = utils.make_temp_file()
            os.write(temp_file_fd, data)
            os.close(temp_file_fd)

            self.printFile(temp_file_name, printer_name, False, raw, remove=True)


    def cancelJob(self, jobid):
        cups.cancelJob(jobid)
        self.error_code = STATUS_PRINTER_CANCELING
        self.sendEvent(self.error_code)


    def queryHistory(self):
        result = []

        if self.dbus_avail:
            try:
                device_uri, history = self.service.GetHistory(self.device_uri)
            except dbus.exceptions.DBusException as e:
                log.error("dbus call to GetHistory() failed.")
                return []

            history.reverse()

            for h in history:
                result.append(Event(*tuple(h)))

            try:
                self.error_code = result[0].event_code
            except IndexError:
                self.error_code = STATUS_UNKNOWN

            self.error_state = STATUS_TO_ERROR_STATE_MAP.get(self.error_code, ERROR_STATE_CLEAR)

        else:
            self.error_code = STATUS_UNKNOWN
            self.error_state = ERROR_STATE_CLEAR

        self.hist = result
        return result

    def getEWSUrl(self, url, stream):
        try:
            if self.is_local:
                url2 = "%s&loc=%s" % (self.device_uri.replace('hpfax:', 'hp:'), url)
                data = self
            else:
                url2 = "http://%s%s" % (self.host, url)
                if self.zc:
                    status, ip = hpmudext.get_zc_ip_address(self.zc)
                    if status == hpmudext.HPMUD_R_OK:
                        url2 = "http://%s%s" % (ip, url)
                data = None

            log.debug("Opening: %s" % url2)
            opener = LocalOpener({})
            try:
                f = opener.open(url2, data)
                
            except Error:
                log.error("Status read failed: %s" % url2)
                stream.seek(0)
                stream.truncate()
            else:
                try:
                    stream.write(f.fp.read())
                    #stream.write(f)
                finally:
                    f.close()

        finally:
            self.closeEWS()

    def getEWSUrl_LEDM(self, url, stream, footer=""):
        try:
            url2 = "%s&loc=%s" % (self.device_uri.replace('hpfax:', 'hp:'), url)
            data = self
            opener = LocalOpenerEWS_LEDM({})
            try:
                if footer:
                    return opener.open_hp(url2, data, footer)
                else:
                    return opener.open_hp(url2, data)
            except Error:
                log.debug("Status read failed: %s" % url2)
        finally:
            self.closeEWS_LEDM()

    def getUrl_LEDM(self, url, stream, footer=""):
        try:
            url2 = "%s&loc=%s" % (self.device_uri.replace('hpfax:', 'hp:'), url)
            data = self
            opener = LocalOpener_LEDM({})
            try:
                if footer:
                    return opener.open_hp(url2, data, footer)
                else:
                    return opener.open_hp(url2, data)
            except Error:
                log.debug("Status read failed: %s" % url2)

        finally:
            self.closeLEDM()

    def FetchLEDMUrl(self, url, footer=""):
        data_fp = BytesIO()
        if footer:
            data = self.getUrl_LEDM(url, data_fp, footer)
        else:
            data = self.getUrl_LEDM(url, data_fp)
        if data:
            data = data.split(to_bytes_utf8('\r\n\r\n'), 1)[1]
            if data:
                data = status.ExtractXMLData(data)
        return data

#-------------------------For LEDM SOAP PROTOCOL(FAX) Devices----------------------------------------------------------------------#

    def FetchEWS_LEDMUrl(self, url, footer=""):
        data_fp = BytesIO()
        if footer:
            data = self.getEWSUrl_LEDM(url, data_fp, footer)
        else:
            data = self.getEWSUrl_LEDM(url, data_fp)
        if data:
            data = data.split(to_bytes_utf8('\r\n\r\n'), 1)[1]
            if data:
                data = status.ExtractXMLData(data)
        return data

    def readAttributeFromXml_EWS(self, uri, attribute):
        stream = BytesIO()
        data = self.FetchEWS_LEDMUrl(uri)
        if not data:
            log.error("Unable To read the XML data from device")
            return ""
        xmlDict = utils.XMLToDictParser().parseXML(data)

        try:
            return xmlDict[attribute]
        except:
            return str("")

#---------------------------------------------------------------------------------------------------#

    def readAttributeFromXml(self,uri,attribute):
        stream = BytesIO()
        data = self.FetchLEDMUrl(uri)
        if not data:
            log.error("Unable To read the XML data from device")
            return ""
        xmlDict = utils.XMLToDictParser().parseXML(data )
        try:
            return xmlDict[attribute]
        except:
            return str("")


    def downloadFirmware(self, usb_bus_id=None, usb_device_id=None): # Note: IDs not currently used
        ok = False
        filename = os.path.join(prop.data_dir, "firmware", self.model.lower() + '.fw.gz')
        log.debug(filename)

        if os.path.exists(filename):
            log.debug("Downloading firmware file '%s'..." % filename)

            # Write to port directly (no MUD) so that HAL can enumerate the printer
            if 0: # this currently doesn't work because usblp is loaded...
            #if usb_bus_id is not None and usb_device_id is not None:
                try:
                    p = "/dev/bus/usb/%s/%s" % (usb_bus_id, usb_device_id)
                    log.debug("Writing to %s..." % p)
                    f = os.open(p, os.O_RDWR)
                    x = gzip.open(filename).read()
                    os.write(f, x)
                    os.close(f)
                    ok = True
                    log.debug("OK")
                except (OSError, IOError) as e:
                    log.error("An error occured: %s" % e)
            else:
                try:
                    self.openPrint()
                    bytes_written = self.writePrint(gzip.open(filename).read())
                    log.debug("%s bytes downloaded." % utils.commafy(bytes_written))
                    self.closePrint()
                    ok = True
                    log.debug("OK")
                except Error as e:
                    log.error("An error occured: %s" % e.msg)
        else:
            log.error("Firmware file '%s' not found." % filename)

        return ok



    


# URLs: hp:/usb/HP_LaserJet_3050?serial=00XXXXXXXXXX&loc=/hp/device/info_device_status.xml
class LocalOpener(urllib_request.URLopener):
    def open_hp(self, url, dev):
        log.debug("open_hp(%s)" % url)

        match_obj = http_pat_url.search(url)
        bus = match_obj.group(1) or ''
        model = match_obj.group(2) or ''
        serial = match_obj.group(3) or ''
        device = match_obj.group(4) or ''
        loc = match_obj.group(5) or ''

        dev.openEWS()
        dev.writeEWS("""GET %s HTTP/1.0\nContent-Length:0\nHost:localhost\nUser-Agent:hplip\n\n""" % loc)

        reply = xStringIO()
        while dev.readEWS(8192, reply, timeout=1):
            pass

        reply.seek(0)
        log.log_data(reply.getvalue())
        
        response = http_client.HTTPResponse(reply)
        response.begin()

        if response.status != http_client.OK:
            raise Error(ERROR_DEVICE_STATUS_NOT_AVAILABLE)
        else:
            return response#.fp

# URLs: hp:/usb/HP_OfficeJet_7500?serial=00XXXXXXXXXX&loc=/hp/device/info_device_status.xml
class LocalOpenerEWS_LEDM(urllib_request.URLopener):
    def open_hp(self, url, dev, foot=""):
        log.debug("open_hp(%s)" % url)

        match_obj = http_pat_url.search(url)
        loc = url.split("=")[url.count("=")]

        dev.openEWS_LEDM()
        if foot:
            if "PUT" in foot:
                dev.writeEWS_LEDM("""%s""" % foot)
            else:
                dev.writeEWS_LEDM("""POST %s HTTP/1.1\r\nContent-Type:text/xml\r\nContent-Length:%s\r\nAccept-Encoding: UTF-8\r\nHost:localhost\r\nUser-Agent:hplip\r\n\r\n """ % (loc, len(foot)))
                dev.writeEWS_LEDM("""%s""" % foot)
        else:
            dev.writeEWS_LEDM("""GET %s HTTP/1.1\r\nAccept: text/plain\r\nHost:localhost\r\nUser-Agent:hplip\r\n\r\n""" % loc)

        reply = xStringIO()

        dev.readLEDMData(dev.readEWS_LEDM,reply)

        reply.seek(0)
        return reply.getvalue()


# URLs: hp:/usb/HP_OfficeJet_7500?serial=00XXXXXXXXXX&loc=/hp/device/info_device_status.xml
class LocalOpener_LEDM(urllib_request.URLopener):
    def open_hp(self, url, dev, foot=""):
        log.debug("open_hp(%s)" % url)

        match_obj = http_pat_url.search(url)
        loc = url.split("=")[url.count("=")]

        dev.openLEDM()
        if foot:
            if "PUT" in foot:
                dev.writeLEDM("""%s""" % foot)
            else:
                dev.writeLEDM("""POST %s HTTP/1.1\r\nContent-Type:text/xml\r\nContent-Length:%s\r\nAccept-Encoding: UTF-8\r\nHost:localhost\r\nUser-Agent:hplip\r\n\r\n """ % (loc, len(foot)))
                dev.writeLEDM("""%s""" % foot)
        else:
            dev.writeLEDM("""GET %s HTTP/1.1\r\nAccept: text/plain\r\nHost:localhost\r\nUser-Agent:hplip\r\n\r\n""" % loc)

        reply = xStringIO()

       
        dev.readLEDMData(dev.readLEDM,reply)

        reply.seek(0)
        return reply.getvalue()
