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
# Based on:
# "sane.py", part of the Python Imaging Library (PIL)
# http://www.pythonware.com/products/pil/
# Python wrapper on top of the _sane module, which is in turn a very
# thin wrapper on top of the SANE library.  For a complete understanding
# of SANE, consult the documentation at the SANE home page:
# http://www.mostang.com/sane/ .#
#
# Modified to work without PIL by Don Welch
#
# (C) Copyright 2003 A.M. Kuchling.  All Rights Reserved
# (C) Copyright 2004 A.M. Kuchling, Ralph Heinkel  All Rights Reserved
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of A.M. Kuchling and
# Ralph Heinkel not be used in advertising or publicity pertaining to
# distribution of the software without specific, written prior permission.
#
# A.M. KUCHLING, R.H. HEINKEL DISCLAIM ALL WARRANTIES WITH REGARD TO THIS
# SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS,
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY SPECIAL, INDIRECT OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
# USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
# Python wrapper on top of the scanext module, which is in turn a very
# thin wrapper on top of the SANE library.  For a complete understanding
# of SANE, consult the documentation at the SANE home page:
# http://www.mostang.com/sane/ .
#
# Original authors: Andrew Kuchling, Ralph Heinkel
# Modified by: Don Welch, Sarbeswar Meher
#

# Std Lib
import scanext
import threading
import time
import os

# Local
from base.g import *
from base import utils
from base.sixext import to_bytes_utf8
from base.sixext.moves import queue

EVENT_SCAN_CANCELED = 1

TYPE_STR = { scanext.TYPE_BOOL:   "TYPE_BOOL",   scanext.TYPE_INT:    "TYPE_INT",
             scanext.TYPE_FIXED:  "TYPE_FIXED",  scanext.TYPE_STRING: "TYPE_STRING",
             scanext.TYPE_BUTTON: "TYPE_BUTTON", scanext.TYPE_GROUP:  "TYPE_GROUP" }

UNIT_STR = { scanext.UNIT_NONE:        "UNIT_NONE",
             scanext.UNIT_PIXEL:       "UNIT_PIXEL",
             scanext.UNIT_BIT:         "UNIT_BIT",
             scanext.UNIT_MM:          "UNIT_MM",
             scanext.UNIT_DPI:         "UNIT_DPI",
             scanext.UNIT_PERCENT:     "UNIT_PERCENT",
             scanext.UNIT_MICROSECOND: "UNIT_MICROSECOND" }


MAX_READSIZE = 65536

class Option:
    """Class representing a SANE option.
    Attributes:
    index -- number from 0 to n, giving the option number
    name -- a string uniquely identifying the option
    title -- single-line string containing a title for the option
    desc -- a long string describing the option; useful as a help message
    type -- type of this option.  Possible values: TYPE_BOOL,
            TYPE_INT, TYPE_STRING, and so forth.
    unit -- units of this option.  Possible values: UNIT_NONE,
            UNIT_PIXEL, etc.
    size -- size of the value in bytes
    cap -- capabilities available; CAP_EMULATED, CAP_SOFT_SELECT, etc.
    constraint -- constraint on values.  Possible values:
        None : No constraint
        (min,max,step)  Integer values, from min to max, stepping by
        list of integers or strings: only the listed values are allowed
    """

    def __init__(self, args, cur_device):
        import string
        self.cur_device = cur_device

        self.index, self.name, self.title, self.desc, self.type, \
            self.unit, self.size, self.cap, self.constraint = args

        if type(self.name) != type(''):
            self.name = str(self.name)

    def isActive(self):
        return scanext.isOptionActive(self.cap)

    def isSettable(self):
        return scanext.isOptionSettable(self.cap)

    def __repr__(self):
        if self.isSettable():
            settable = 'yes'
        else:
            settable = 'no'

        if self.isActive():
            active = 'yes'
            curValue = self.cur_device.getOption(self.name)
        else:
            active = 'no'
            curValue = '<not available, inactive option>'


        return """\nName:      %s
Cur value: %s
Index:     %d
Title:     %s
Desc:      %s
Type:      %s
Unit:      %s
Constr:    %s
isActive:    %s
isSettable:  %s\n""" % (self.name, curValue,
                      self.index, self.title, self.desc,
                      TYPE_STR[self.type], UNIT_STR[self.unit],
                      self.constraint, active, settable)
        return s

    def limitAndSet(self, value):
        if value is not None and self.constraint is not None:
            if type(self.constraint) == type(()):
                if value < self.constraint[0]:
                    value = self.constraint[0]
                    log.warn("Invalid value for %s (%s < min value of %d). Using %d." %
                        (self.name, self.name, value, value))

                elif value > self.constraint[1]:
                    value = self.constraint[1]
                    log.warn("Invalid value for %s (%s > max value of %d). Using %d." %
                        (self.name, self.name, value, value))

                self.cur_device.setOption(self.name, value)

            elif type(self.constraint) == type([]):
                if value not in self.constraint:
                    v = self.constraint[0]
                    min_dist = sys.maxsize
                    for x in self.constraint:
                        if abs(value-x) < min_dist:
                            min_dist = abs(value-x)
                            v = x

                    log.warn("Invalid value for %s (%s not in constraint list: %s). Using %d." %
                        (self.name, self.name, value, ', '.join(self.constraint), v))

                    self.cur_device.setOption(self.name, v)

        else:
            value = self.cur_device.getOption(self.name)

        return value


##class _SaneIterator:
##    """ intended for ADF scans.
##    """
##
##    def __init__(self, cur_device):
##        self.cur_device = cur_device
##
##    def __iter__(self):
##        return self
##
##    def __del__(self):
##        self.cur_device.cancelScan()
##
##    def next(self):
##        try:
##            self.cur_device.startScan()
##        except error, v:
##            if v == 'Document feeder out of documents':
##                raise StopIteration
##            else:
##                raise
##        return self.cur_device.performScan(1)




class ScanDevice:
    """Class representing a SANE device.
    Methods:
    startScan()    -- initiate a scan, using the current settings
    cancelScan()   -- cancel an in-progress scanning operation

    Also available, but rather low-level:
    getParameters() -- get the current parameter settings of the device
    getOptions()    -- return a list of tuples describing all the options.

    Attributes:
    optlist -- list of option names

    You can also access an option name to retrieve its value, and to
    set it.  For example, if one option has a .name attribute of
    imagemode, and scanner is a ScanDevice object, you can do:
         print scanner.imagemode
         scanner.imagemode = 'Full frame'
         scanner.['imagemode'] returns the corresponding Option object.
    """

    def __init__(self, dev):
        self.scan_thread = None
        self.dev = scanext.openDevice(dev)
        self.options = {}
        self.__load_options_dict()


    def __load_options_dict(self):
        opts = self.options
        opt_list = self.dev.getOptions()

        for t in opt_list:
            o = Option(t, self)

            if o.type != scanext.TYPE_GROUP:
                opts[o.name] = o


    def setOption(self, key, value):
        opts = self.options

        if key not in opts:
            opts[key] = value
            return

        opt = opts[key]

        if opt.type == scanext.TYPE_GROUP:
            log.error("Groups can't be set: %s" % key)

        if not scanext.isOptionActive(opt.cap):
            log.error("Inactive option: %s" % key)

        if not scanext.isOptionSettable(opt.cap):
            log.error("Option can't be set by software: %s" % key)

        if type(value) == int and opt.type == scanext.TYPE_FIXED:
            # avoid annoying errors of backend if int is given instead float:
            value = float(value)

        try:
            self.last_opt = self.dev.setOption(opt.index, value)
        except scanext.error:
            log.error("Unable to set option %s to value %s" % (key, value))
            return

        # do binary AND to find if we have to reload options:
        if self.last_opt & scanext.INFO_RELOAD_OPTIONS:
            self.__load_options_dict()


    def getOption(self, key):
        opts = self.options

        if key == 'optlist':
            return list(opts.keys())

        if key == 'area':
            return (opts["tl-x"], opts["tl-y"]), (opts["br-x"], opts["br-y"])

        if key not in opts:
            raise AttributeError('No such attribute: %s' % key)

        opt = opts[key]

        if opt.type == scanext.TYPE_BUTTON:
            raise AttributeError("Buttons don't have values: %s" % key)

        if opt.type == scanext.TYPE_GROUP:
            raise AttributeError("Groups don't have values: %s " % key)

        if not scanext.isOptionActive(opt.cap):
            raise AttributeError('Inactive option: %s' % key)

        return self.dev.getOption(opt.index)


    def getOptionObj(self, key):
        opts = self.options
        if key in opts:
            return opts[key]


    def getParameters(self):
        """Return a 6-tuple holding all the current device settings:
           (format, format_name, last_frame, (pixels_per_line, lines), depth, bytes_per_line)

            - format is the SANE frame type
            - format is one of 'grey', 'color' (RGB), 'red', 'green', 'blue'.
            - last_frame [bool] indicates if this is the last frame of a multi frame image
            - (pixels_per_line, lines) specifies the size of the scanned image (x,y)
            - lines denotes the number of scanlines per frame
            - depth gives number of pixels per sample
        """
        return self.dev.getParameters()


    def getOptions(self):
        "Return a list of tuples describing all the available options"
        return self.dev.getOptions()


    def startScan(self, byte_format='BGRA', update_queue=None, event_queue=None):
        """
            Perform a scan with the current device.
            Calls sane_start().
        """
        if not self.isScanActive():
            status = self.dev.startScan()
            self.format, self.format_name, self.last_frame, self.pixels_per_line, \
            self.lines, self.depth, self.bytes_per_line = self.dev.getParameters()

            self.scan_thread = ScanThread(self.dev, byte_format, update_queue, event_queue)
            self.scan_thread.scan_active = True
            self.scan_thread.start()
            return True, self.lines * self.bytes_per_line, status
        else:
            # Already active
            return False, 0, scanext.SANE_STATUS_DEVICE_BUSY


    def cancelScan(self):
        "Cancel an in-progress scanning operation."
        return self.dev.cancelScan()


    def getScan(self):
        "Get the output buffer and info about a completed scan."
        if not self.isScanActive():
            s = self.scan_thread

            return s.buffer, s.format, s.format_name, s.pixels_per_line, \
                s.lines, s.depth, s.bytes_per_line, s.pad_bytes, s.total_read, s.total_write


    def freeScan(self):
        "Cleanup the scan file after a completed scan."
        if not self.isScanActive():
            s = self.scan_thread

            try:
                s.buffer.close()
                os.remove(s.buffer_path)
            except (IOError, AttributeError):
                pass


    def isScanActive(self):
        if self.scan_thread is not None:
            return self.scan_thread.isAlive() and self.scan_thread.scan_active
        else:
            return False


    def waitForScanDone(self):
        if self.scan_thread is not None and \
            self.scan_thread.isAlive() and \
            self.scan_thread.scan_active:

            try:
                self.scan_thread.join()
            except KeyboardInterrupt:
                pass


    def waitForScanActive(self):
        #time.sleep(0.5)
        if self.scan_thread is not None:
            while True:
                #print self.scan_thread.isAlive()
                #print self.scan_thread.scan_active
                if self.scan_thread.isAlive() and \
                    self.scan_thread.scan_active:
                    return

                time.sleep(0.1)
                #print "Waiting..."


##    def scanMulti(self):
##        return _SaneIterator(self)


    def closeScan(self):
        "Close the SANE device after a scan."
        self.dev.closeScan()
        


class ScanThread(threading.Thread):
    def __init__(self, device, byte_format='BGRA', update_queue=None, event_queue=None):
        threading.Thread.__init__(self)
        self.scan_active = True
        self.dev = device
        self.update_queue = update_queue
        self.event_queue = event_queue
        self.buffer_fd, self.buffer_path = utils.make_temp_file(prefix='hpscan')
        self.buffer = os.fdopen(self.buffer_fd, "w+b")
        self.format = -1
        self.format_name = ''
        self.last_frame = -1
        self.pixels_per_line = -1
        self.lines = -1
        self.depth = -1
        self.bytes_per_line = -1
        self.pad_bytes = -1
        self.total_read = 0
        self.byte_format = byte_format
        self.total_write = 0


    def updateQueue(self, status, bytes_read):
        if self.update_queue is not None:
            try:
                status = int(status)
            except (ValueError, TypeError):
                status = -1 #scanext.SANE_STATUS_GOOD

            self.update_queue.put((status, bytes_read))



    def run(self):
        from base.sixext import to_bytes_utf8
        #self.scan_active = True
        self.format, self.format_name, self.last_frame, self.pixels_per_line, \
            self.lines, self.depth, self.bytes_per_line = self.dev.getParameters()

        log.debug("format=%d" % self.format)
        log.debug("format_name=%s" % self.format_name)
        log.debug("last_frame=%d" % self.last_frame)
        log.debug("ppl=%d" % self.pixels_per_line)
        log.debug("lines=%d" % self.lines)
        log.debug("depth=%d" % self.depth)
        log.debug("bpl=%d" % self.bytes_per_line)
        log.debug("byte_format=%s" % self.byte_format)

        w = self.buffer.write
        readbuffer = self.bytes_per_line

        if self.format == scanext.FRAME_RGB: # "Color"
            if self.depth == 8: # 8 bpp (32bit)
                self.pad_bytes = self.bytes_per_line - 3 * self.pixels_per_line

                log.debug("pad_bytes=%d" % self.pad_bytes)

                dir = -1
                if self.byte_format == 'RGBA':
                    dir = 1

                try:
                    st, t = self.dev.readScan(readbuffer)
                except scanext.error as stObj:
                    st = stObj.args[0]
                    self.updateQueue(st, 0)

                while st == scanext.SANE_STATUS_GOOD:
                    if t:
                        len_t = len(t)
                        w(b"".join([t[index:index+3:dir] + b'\xff' for index in range(0,len_t - self.pad_bytes,3)]))
                        self.total_read += len_t
                        self.total_write +=  len_t+(len_t - self.pad_bytes)/3
                        self.updateQueue(st, self.total_read)
                        log.debug("Color Read %d bytes" % self.total_read)

                    else:
                        time.sleep(0.1)

                    try:
                        st, t = self.dev.readScan(readbuffer)
                    except scanext.error as stObj:
                        st = stObj.args[0]
                        self.updateQueue(st, self.total_read)
                        break

                    if self.checkCancel():
                        break

        elif self.format == scanext.FRAME_GRAY:

            if self.depth == 1: # 1 bpp lineart
                self.pad_bytes = self.bytes_per_line - (self.pixels_per_line + 7) // 8;

                log.debug("pad_bytes=%d" % self.pad_bytes)

                try:
                    st, t = self.dev.readScan(readbuffer)
                except scanext.error as stObj:
                    st = stObj.args[0]
                    self.updateQueue(st, 0)

                while st == scanext.SANE_STATUS_GOOD:
                    if t:
                        len_t = len(t)
                        w(b''.join([b''.join([b"\x00\x00\x00\xff" if k & ord(t[index:index+1]) else b"\xff\xff\xff\xff" for k in [0x80, 0x40, 0x20, 0x10, 0x8, 0x4, 0x2, 0x1]]) for index in range(0, len_t - self.pad_bytes)]))
                        self.total_read += len_t
                        self.total_write += ((len_t - self.pad_bytes) * 32)
                        self.updateQueue(st, self.total_read)
                        log.debug("Lineart Read %d bytes" % self.total_read)
                    else:
                        time.sleep(0.1)

                    try:
                        st, t = self.dev.readScan(readbuffer)
                    except scanext.error as stObj:
                        st = stObj.args[0]
                        self.updateQueue(st, self.total_read)
                        break

                    if self.checkCancel():
                        break
            elif self.depth == 8: # 8 bpp grayscale
                self.pad_bytes = self.bytes_per_line - self.pixels_per_line

                log.debug("pad_bytes=%d" % self.pad_bytes)
                try:
                    st, t = self.dev.readScan(readbuffer)
                except scanext.error as stObj:
                    st = stObj.args[0]
                    self.updateQueue(st, 0)
                while st == scanext.SANE_STATUS_GOOD:
                    if t:
                        len_t = len(t)
                        w(b"".join([3*t[index:index+1] + b'\xff' for index in range(0, len_t - self.pad_bytes)]))
                        self.total_read += len_t 
                        self.total_write += ((len_t  - self.pad_bytes) * 4)
                        self.updateQueue(st, self.total_read)
                        log.debug("Gray Read %d bytes" % self.total_read)
                    else:
                        time.sleep(0.1)

                    try:
                        st, t = self.dev.readScan(readbuffer)
                    except scanext.error as stObj:
                        st = stObj.args[0]
                        self.updateQueue(st, self.total_read)
                        break

                    if self.checkCancel():
                        break

        #self.dev.cancelScan()
        self.buffer.seek(0)
        self.scan_active = False
        log.debug("Scan thread exiting...")



    def checkCancel(self):
        canceled = False
        while self.event_queue.qsize():
            try:
                event = self.event_queue.get(0)
                if event == EVENT_SCAN_CANCELED:
                    canceled = True
                    log.debug("Cancel pressed!")
                    self.dev.canclScan()


            except queue.Empty:
                break

        return canceled



def init():
    return scanext.init()


def deInit():
    return scanext.deInit()


def openDevice(dev):
    "Open a device for scanning"
    return ScanDevice(dev)


def getDevices(local_only=0):
    return scanext.getDevices(local_only)


def reportError(code):
    log.error("SANE: %s (code=%d)" % (scanext.getErrorMessage(code), code))


