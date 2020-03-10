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

# Std Lib
import sys
import os
import os.path
import struct
import time
import threading
from base.sixext.moves import StringIO
from io import BytesIO
# Local
from base.g import *
from base.codes import *
from base import device, utils, pml, codes
from prnt import cups
from .fax import *


# **************************************************************************** #

# Page flags
PAGE_FLAG_NONE = 0x00
PAGE_FLAG_NEW_PAGE = 0x01
PAGE_FLAG_END_PAGE = 0x02
PAGE_FLAG_NEW_DOC = 0x04
PAGE_FLAG_END_DOC = 0x08
PAGE_FLAG_END_STREAM = 0x10

MAJOR_VER = 2
MINOR_VER = 0

MFPDTF_RASTER_BITMAP  = 0 # Not used
MFPDTF_RASTER_GRAYMAP = 1 # Not used
MFPDTF_RASTER_MH      = 2 # OfficeJets B&W Fax
MFPDTF_RASTER_MR      = 3 # Not used
MFPDTF_RASTER_MMR     = 4 # LaserJets B&W Fax
MFPDTF_RASTER_RGB     = 5 # Not used
MFPDTF_RASTER_YCC411  = 6 # Not used
MFPDTF_RASTER_JPEG    = 7 # Color Fax
MFPDTF_RASTER_PCL     = 8 # Not used
MFPDTF_RASTER_NOT     = 9 # Not used

# Data types for FH
DT_UNKNOWN       = 0
DT_FAX_IMAGES    = 1
DT_SCANNED_IMAGES= 2
DT_DIAL_STRINGS  = 3
DT_DEMO_PAGES    = 4
DT_SPEED_DIALS   = 5
DT_FAX_LOGS      = 6
DT_CFG_PARMS     = 7
DT_LANG_STRS     = 8
DT_JUNK_FAX_CSIDS= 9
DT_REPORT_STRS   = 10
DT_FONTS         = 11
DT_TTI_BITMAP    = 12
DT_COUNTERS      = 13
DT_DEF_PARMS     = 14
DT_SCAN_OPTIONS  = 15
DT_FW_JOB_TABLE  = 17

# Raster data record types
RT_START_PAGE = 0
RT_RASTER = 1
RT_END_PAGE = 2

# FH
FIXED_HEADER_SIZE = 8

# Variants
IMAGE_VARIANT_HEADER_SIZE = 10
DIAL_STRINGS_VARIANT_HEADER_SIZE = 6
FAX_IMAGE_VARIANT_HEADER_SIZE = 74

# Data records
SOP_RECORD_SIZE = 36
RASTER_RECORD_SIZE = 4
EOP_RECORD_SIZE = 12
DIAL_STRING_RECORD_SIZE = 51

# Page flags
PAGE_FLAG_NEW_PAGE = 0x01
PAGE_FLAG_END_PAGE = 0x02
PAGE_FLAG_NEW_DOC = 0x04
PAGE_FLAG_END_DOC = 0x08
PAGE_FLAG_END_STREAM = 0x10

# Fax data variant header data source
SRC_UNKNOWN = 0
SRC_HOST = 2
SRC_SCANNER = 5
SRC_HOST_THEN_SCANNER = 6
SRC_SCANNER_THEN_HOST = 7

# Fax data variant header TTI header control
TTI_NONE = 0
TTI_PREPENDED_TO_IMAGE = 1
TTI_OVERLAYED_ON_IMAGE = 2

RASTER_DATA_SIZE = 504



# **************************************************************************** #
class PMLFaxDevice(FaxDevice):

    def __init__(self, device_uri=None, printer_name=None,
                 callback=None,
                 fax_type=FAX_TYPE_NONE,
                 disable_dbus=False):

        FaxDevice.__init__(self, device_uri,
                           printer_name,
                           callback, fax_type,
                           disable_dbus)

        self.send_fax_thread = None
        self.upload_log_thread = None


    def setPhoneNum(self, num):
        return self.setPML(pml.OID_FAX_LOCAL_PHONE_NUM, str(num))

    def getPhoneNum(self):
        if PY3:
            data = utils.printable(self.getPML(pml.OID_FAX_LOCAL_PHONE_NUM)[1].encode('utf-8'))
            return data.decode('utf-8')
        else:
            return utils.printable(self.getPML(pml.OID_FAX_LOCAL_PHONE_NUM)[1])
    phone_num = property(getPhoneNum, setPhoneNum, doc="OID_FAX_LOCAL_PHONE_NUM")


    def setStationName(self, name):
        return self.setPML(pml.OID_FAX_STATION_NAME, name)

    def getStationName(self):
        if PY3:
            data = utils.printable(self.getPML(pml.OID_FAX_STATION_NAME)[1].encode('utf-8'))
            return data.decode('utf-8')
        else:
            return utils.printable(self.getPML(pml.OID_FAX_STATION_NAME)[1])

    station_name = property(getStationName, setStationName, doc="OID_FAX_STATION_NAME")

    def setDateAndTime(self):    #Need Revisit
        pass
        #t = time.localtime()
        #p = struct.pack("BBBBBBB", t[0]-2000, t[1], t[2], t[6]+1, t[3], t[4], t[5])
        #log.debug(repr(p))
        #return self.setPML(pml.OID_DATE_AND_TIME, p.decode('latin-1'))

    def uploadLog(self):
        if not self.isUloadLogActive():
            self.upload_log_thread = UploadLogThread(self)
            self.upload_log_thread.start()
            return True
        else:
            return False

    def isUploadLogActive(self):
        if self.upload_log_thread is not None:
            return self.upload_log_thread.isAlive()
        else:
            return False

    def waitForUploadLogThread(self):
        if self.upload_log_thread is not None and \
            self.upload_log_thread.isAlive():

            self.upload_log_thread.join()

    def sendFaxes(self, phone_num_list, fax_file_list, cover_message='', cover_re='',
                  cover_func=None, preserve_formatting=False, printer_name='',
                  update_queue=None, event_queue=None):

        if not self.isSendFaxActive():

            self.send_fax_thread = PMLFaxSendThread(self, self.service, phone_num_list, fax_file_list,
                                                    cover_message, cover_re, cover_func,
                                                    preserve_formatting,
                                                    printer_name, update_queue,
                                                    event_queue)

            self.send_fax_thread.start()
            return True
        else:
            return False



# **************************************************************************** #
class PMLUploadLogThread(threading.Thread):
    def __init__(self, dev):
        threading.Thread.__init__(self)
        self.dev = dev


    def run(self):
        STATE_DONE = 0
        STATE_ABORT = 10
        STATE_SUCCESS = 20
        STATE_BUSY = 25
        STATE_DEVICE_OPEN = 28
        STATE_CHECK_IDLE = 30
        STATE_REQUEST_START = 40
        STATE_WAIT_FOR_ACTIVE = 50
        STATE_UPLOAD_DATA = 60
        STATE_DEVICE_CLOSE = 70

        state = STATE_CHECK_IDLE

        while state != STATE_DONE: # --------------------------------- Log upload state machine
            if state == STATE_ABORT:
                pass
            elif state == STATE_SUCCESS:
                pass
            elif state == STATE_BUSY:
                pass

            elif state == STATE_DEVICE_OPEN: # --------------------------------- Open device (28)
                state = STATE_REQUEST_START
                try:
                    self.dev.open()
                except Error as e:
                    log.error("Unable to open device (%s)." % e.msg)
                    state = STATE_ERROR
                else:
                    try:
                        dev.setPML(pml.OID_UPLOAD_TIMEOUT, pml.DEFAULT_UPLOAD_TIMEOUT)
                    except Error:
                        state = STATE_ERROR

            elif state == STATE_CHECK_IDLE: # --------------------------------- Check idle (30)
                state = STATE_REQUEST_START
                ul_state = self.getCfgUploadState()

                if ul_state != pml.UPDN_STATE_IDLE:
                    state = STATE_BUSY


            elif state == STATE_REQUEST_START: # --------------------------------- Request start (40)
                state = STATE_WAIT_FOR_ACTIVE
                self.dev.setPML(pml.OID_FAX_CFG_UPLOAD_DATA_TYPE, pml.FAX_CFG_UPLOAD_DATA_TYPE_FAXLOGS)
                self.dev.setPML(pml.OID_DEVICE_CFG_UPLOAD, pml.UPDN_STATE_REQSTART)

            elif state == STATE_WAIT_FOR_ACTIVE: # --------------------------------- Wait for active state (50)
                state = STATE_UPLOAD_DATA

                tries = 0
                while True:
                    tries += 1
                    ul_state = self.getCfgUploadState()

                    if ul_state == pml.UPDN_STATE_XFERACTIVE:
                        break

                    if ul_state in (pml.UPDN_STATE_ERRORABORT, pml.UPDN_STATE_XFERDONE):
                        log.error("Cfg upload aborted!")
                        state = STATE_ERROR
                        break

                    if tries > 10:
                        state = STATE_ERROR
                        log.error("Unable to get into active state!")
                        break

                    time.sleep(0.5)

            elif state == STATE_UPLOAD_DATA: # --------------------------------- Upload log data (60)
                pass

            elif state == STATE_DEVICE_CLOSE: # --------------------------------- Close device (70)
                self.dev.close()



# **************************************************************************** #
class PMLFaxSendThread(FaxSendThread):
    def __init__(self, dev, service, phone_num_list, fax_file_list,
                 cover_message='', cover_re='', cover_func=None, preserve_formatting=False,
                 printer_name='', update_queue=None, event_queue=None):

        FaxSendThread.__init__(self, dev, service, phone_num_list, fax_file_list,
             cover_message, cover_re, cover_func, preserve_formatting,
             printer_name, update_queue, event_queue)


    def run(self):
        #results = {} # {'file' : error_code,...}

        STATE_DONE = 0
        STATE_ABORTED = 10
        STATE_SUCCESS = 20
        STATE_BUSY = 25
        STATE_READ_SENDER_INFO = 30
        STATE_PRERENDER = 40
        STATE_COUNT_PAGES = 50
        STATE_NEXT_RECIPIENT = 60
        STATE_COVER_PAGE = 70
        STATE_SINGLE_FILE = 80
        STATE_MERGE_FILES = 90
        STATE_SINGLE_FILE = 100
        STATE_SEND_FAX = 110
        STATE_CLEANUP = 120
        STATE_ERROR = 130

        next_recipient = self.next_recipient_gen()

        state = STATE_READ_SENDER_INFO
        self.rendered_file_list = []

        while state != STATE_DONE: # --------------------------------- Fax state machine
            if self.check_for_cancel():
                state = STATE_ABORTED

            log.debug("STATE=(%d, 0, 0)" % state)

            if state == STATE_ABORTED: # --------------------------------- Aborted (10, 0, 0)
                log.error("Aborted by user.")
                self.write_queue((STATUS_IDLE, 0, ''))
                state = STATE_CLEANUP


            elif state == STATE_SUCCESS: # --------------------------------- Success (20, 0, 0)
                log.debug("Success.")
                self.write_queue((STATUS_COMPLETED, 0, ''))
                state = STATE_CLEANUP


            elif state == STATE_ERROR: # --------------------------------- Error (130, 0, 0)
                log.error("Error, aborting.")
                self.write_queue((STATUS_ERROR, 0, ''))
                state = STATE_CLEANUP


            elif state == STATE_BUSY: # --------------------------------- Busy (25, 0, 0)
                log.error("Device busy, aborting.")
                self.write_queue((STATUS_BUSY, 0, ''))
                state = STATE_CLEANUP


            elif state == STATE_READ_SENDER_INFO: # --------------------------------- Get sender info (30, 0, 0)
                log.debug("%s State: Get sender info" % ("*"*20))
                state = STATE_PRERENDER
                try:
                    try:
                        self.dev.open()
                    except Error as e:
                        log.error("Unable to open device (%s)." % e.msg)
                        state = STATE_ERROR
                    else:
                        try:
                            self.sender_name = self.dev.station_name
                            log.debug("Sender name=%s" % self.sender_name)
                            self.sender_fax = self.dev.phone_num
                            log.debug("Sender fax=%s" % self.sender_fax)
                        except Error:
                            log.error("PML get failed!")
                            state = STATE_ERROR

                finally:
                    self.dev.close()


            elif state == STATE_PRERENDER: # --------------------------------- Pre-render non-G3 files (40, 0, 0)
                log.debug("%s State: Pre-render non-G3 files" % ("*"*20))
                state = self.pre_render(STATE_COUNT_PAGES)


            elif state == STATE_COUNT_PAGES: # --------------------------------- Get total page count (50, 0, 0)
                log.debug("%s State: Get total page count" % ("*"*20))
                state = self.count_pages(STATE_NEXT_RECIPIENT)


            elif state == STATE_NEXT_RECIPIENT: # --------------------------------- Loop for multiple recipients (60, 0, 0)
                log.debug("%s State: Next recipient" % ("*"*20))
                state = STATE_COVER_PAGE

                try:
                    recipient = next(next_recipient)
                    #print recipient
                    log.debug("Processing for recipient %s" % recipient['name'])

                    self.write_queue((STATUS_SENDING_TO_RECIPIENT, 0, recipient['name']))

                except StopIteration:
                    state = STATE_SUCCESS
                    log.debug("Last recipient.")
                    continue

                self.recipient_file_list = self.rendered_file_list[:]


            elif state == STATE_COVER_PAGE: # --------------------------------- Create cover page (70, 0, 0)
                log.debug("%s State: Render cover page" % ("*"*20))
                state = self.cover_page(recipient)


            elif state == STATE_SINGLE_FILE: # --------------------------------- Special case for single file (no merge) (80, 0, 0)
                log.debug("%s State: Handle single file" % ("*"*20))
                state = self.single_file(STATE_SEND_FAX)

            elif state == STATE_MERGE_FILES: # --------------------------------- Merge multiple G3 files (90, 0, 0)
                log.debug("%s State: Merge multiple files" % ("*"*20))
                state = self.merge_files(STATE_SEND_FAX)

            elif state == STATE_SEND_FAX: # --------------------------------- Send fax state machine (110, 0, 0)
                log.debug("%s State: Send fax" % ("*"*20))
                state = STATE_NEXT_RECIPIENT

                FAX_SEND_STATE_DONE = 0
                FAX_SEND_STATE_ABORT = 10
                FAX_SEND_STATE_ERROR = 20
                FAX_SEND_STATE_BUSY = 25
                FAX_SEND_STATE_SUCCESS = 30
                FAX_SEND_STATE_DEVICE_OPEN = 40
                FAX_SEND_STATE_SET_TOKEN = 50
                FAX_SEND_STATE_EARLY_OPEN = 60
                FAX_SEND_STATE_SET_PARAMS = 70
                FAX_SEND_STATE_CHECK_IDLE = 80
                FAX_SEND_STATE_START_REQUEST = 90
                FAX_SEND_STATE_LATE_OPEN = 100
                FAX_SEND_STATE_SEND_DIAL_STRINGS = 110
                FAX_SEND_STATE_SEND_FAX_HEADER = 120
                FAX_SEND_STATE_SEND_PAGES = 130
                FAX_SEND_STATE_SEND_END_OF_STREAM = 140
                FAX_SEND_STATE_WAIT_FOR_COMPLETE = 150
                FAX_SEND_STATE_RESET_TOKEN = 160
                FAX_SEND_STATE_CLOSE_SESSION = 170

                monitor_state = False
                error_state = pml.DN_ERROR_NONE
                fax_send_state = FAX_SEND_STATE_DEVICE_OPEN

                while fax_send_state != FAX_SEND_STATE_DONE:

                    if self.check_for_cancel():
                        log.error("Fax send aborted.")
                        fax_send_state = FAX_SEND_STATE_ABORT

                    if monitor_state:
                        fax_state = self.getFaxDownloadState()
                        if not fax_state in (pml.UPDN_STATE_XFERACTIVE, pml.UPDN_STATE_XFERDONE):
                            log.error("D/L error state=%d" % fax_state)
                            fax_send_state = FAX_SEND_STATE_ERROR
                            state = STATE_ERROR

                    log.debug("STATE=(%d, %d, 0)" % (STATE_SEND_FAX, fax_send_state))

                    if fax_send_state == FAX_SEND_STATE_ABORT: # -------------- Abort (110, 10, 0)
                        # TODO: Set D/L state to ???
                        monitor_state = False
                        fax_send_state = FAX_SEND_STATE_RESET_TOKEN
                        state = STATE_ABORTED

                    elif fax_send_state == FAX_SEND_STATE_ERROR: # -------------- Error (110, 20, 0)
                        log.error("Fax send error.")
                        error_state = self.getFaxDownloadError()
                        log.debug("Error State=%d (%s)" % (error_state, pml.DN_ERROR_STR.get(error_state, "Unknown")))
                        monitor_state = False

                        fax_send_state = FAX_SEND_STATE_RESET_TOKEN
                        state = STATE_ERROR

                    elif fax_send_state == FAX_SEND_STATE_BUSY: # -------------- Busy (110, 25, 0)
                        log.error("Fax device busy.")
                        monitor_state = False
                        fax_send_state = FAX_SEND_STATE_RESET_TOKEN
                        state = STATE_BUSY

                    elif fax_send_state == FAX_SEND_STATE_SUCCESS: # -------------- Success (110, 30, 0)
                        log.debug("Fax send success.")
                        monitor_state = False
                        fax_send_state = FAX_SEND_STATE_RESET_TOKEN
                        state = STATE_NEXT_RECIPIENT

                    elif fax_send_state == FAX_SEND_STATE_DEVICE_OPEN: # -------------- Device open (110, 40, 0)
                        log.debug("%s State: Open device" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_SET_TOKEN
                        try:
                            self.dev.open()
                        except Error as e:
                            log.error("Unable to open device (%s)." % e.msg)
                            fax_send_state = FAX_SEND_STATE_ERROR
                        else:
                            if self.dev.device_state == DEVICE_STATE_NOT_FOUND:
                                fax_send_state = FAX_SEND_STATE_ERROR

                    elif fax_send_state == FAX_SEND_STATE_SET_TOKEN: # -------------- Acquire fax token (110, 50, 0)
                        log.debug("%s State: Acquire fax token" % ("*"*20))
                        try:
                            result_code, token = self.dev.getPML(pml.OID_FAX_TOKEN)
                        except Error:
                            log.debug("Unable to acquire fax token (1).")
                            fax_send_state = FAX_SEND_STATE_EARLY_OPEN
                        else:
                            if result_code > pml.ERROR_MAX_OK:
                                fax_send_state = FAX_SEND_STATE_EARLY_OPEN
                                log.debug("Skipping token acquisition.")
                            else:
                                token = time.strftime("%d%m%Y%H:%M:%S", time.gmtime())
                                log.debug("Setting token: %s" % token)
                                try:
                                    self.dev.setPML(pml.OID_FAX_TOKEN, token)
                                except Error:
                                    log.error("Unable to acquire fax token (2).")
                                    fax_send_state = FAX_SEND_STATE_ERROR
                                else:
                                    result_code, check_token = self.dev.getPML(pml.OID_FAX_TOKEN)

                                    if check_token == token:
                                        fax_send_state = FAX_SEND_STATE_EARLY_OPEN
                                    else:
                                        log.error("Unable to acquire fax token (3).")
                                        fax_send_state = FAX_SEND_STATE_ERROR


                    elif fax_send_state == FAX_SEND_STATE_EARLY_OPEN: # -------------- Early open (newer models) (110, 60, 0)
                        log.debug("%s State: Early open" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_CHECK_IDLE

                        if self.dev.fax_type == FAX_TYPE_BLACK_SEND_EARLY_OPEN: # newer
                            log.debug("Opening fax channel.")
                            try:
                                self.dev.openFax()
                            except Error as e:
                                log.error("Unable to open channel (%s)." % e.msg)
                                fax_send_state = FAX_SEND_STATE_ERROR
                        else:
                            log.debug("Skipped.")


                    elif fax_send_state == FAX_SEND_STATE_CHECK_IDLE: # -------------- Check for initial idle (110, 80, 0)
                        log.debug("%s State: Check idle" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_START_REQUEST

                        dl_state = self.getFaxDownloadState()
                        tx_status = self.getFaxJobTxStatus()
                        rx_status = self.getFaxJobRxStatus()

                        if ((dl_state == pml.UPDN_STATE_IDLE or \
                            dl_state == pml.UPDN_STATE_ERRORABORT or \
                            dl_state == pml.UPDN_STATE_XFERDONE) and \
                            (tx_status == pml.FAXJOB_TX_STATUS_IDLE or tx_status == pml.FAXJOB_TX_STATUS_DONE) and \
                            (rx_status == pml.FAXJOB_RX_STATUS_IDLE or rx_status == pml.FAXJOB_RX_STATUS_DONE)):

                            # xwas if state == pml.UPDN_STATE_IDLE:
                            if dl_state == pml.UPDN_STATE_IDLE:
                                log.debug("Starting in idle state")
                            else:
                                log.debug("Resetting to idle...")
                                self.dev.setPML(pml.OID_FAX_DOWNLOAD, pml.UPDN_STATE_IDLE)
                                time.sleep(0.5)
                        else:
                            fax_send_state = FAX_SEND_STATE_BUSY

                    elif fax_send_state == FAX_SEND_STATE_START_REQUEST: # -------------- Request fax start (110, 90, 0)
                        log.debug("%s State: Request start" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_SET_PARAMS

                        dl_state = self.getFaxDownloadState()

                        if dl_state == pml.UPDN_STATE_IDLE:
                            log.debug("Try: 0")
                            log.debug("Setting to up/down state request start...")
                            self.dev.setPML(pml.OID_FAX_DOWNLOAD, pml.UPDN_STATE_REQSTART)
                            time.sleep(1)

                            log.debug("Waiting for active state...")
                            i = 1

                            while i < 10:
                                log.debug("Try: %d" % i)
                                try:
                                    dl_state = self.getFaxDownloadState()
                                except Error:
                                    log.error("PML/SNMP error")
                                    fax_send_state = FAX_SEND_STATE_ERROR
                                    break

                                if dl_state == pml.UPDN_STATE_XFERACTIVE:
                                    break

                                time.sleep(1)
                                log.debug("Setting to up/down state request start...")
                                self.dev.setPML(pml.OID_FAX_DOWNLOAD, pml.UPDN_STATE_REQSTART)

                                i += 1

                            else:
                                log.error("Could not get into active state!")
                                fax_send_state = FAX_SEND_STATE_BUSY

                            monitor_state = True

                        else:
                            log.error("Could not get into idle state!")
                            fax_send_state = FAX_SEND_STATE_BUSY


                    elif fax_send_state == FAX_SEND_STATE_SET_PARAMS: # -------------- Set fax send params (110, 70, 0)
                        log.debug("%s State: Set params" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_LATE_OPEN

                        try:
                            self.dev.setPML(pml.OID_DEV_DOWNLOAD_TIMEOUT, pml.DEFAULT_DOWNLOAD_TIMEOUT)
                            self.dev.setPML(pml.OID_FAXJOB_TX_TYPE, pml.FAXJOB_TX_TYPE_HOST_ONLY)
                            log.debug("Setting date and time on device.")
                            self.dev.setDateAndTime()
                        except Error as e:
                            log.error("PML/SNMP error (%s)" % e.msg)
                            fax_send_state = FAX_SEND_STATE_ERROR


                    elif fax_send_state == FAX_SEND_STATE_LATE_OPEN: # -------------- Late open (older models) (110, 100, 0)
                        log.debug("%s State: Late open" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_SEND_DIAL_STRINGS

                        if self.dev.fax_type == FAX_TYPE_BLACK_SEND_LATE_OPEN: # older
                            log.debug("Opening fax channel.")
                            try:
                                self.dev.openFax()
                            except Error:
                                log.error("Unable to open channel.")
                                fax_send_state = FAX_SEND_STATE_ERROR
                        else:
                            log.debug("Skipped.")


                    elif fax_send_state == FAX_SEND_STATE_SEND_DIAL_STRINGS: # -------------- Dial strings (110, 110, 0)
                        log.debug("%s State: Send dial strings" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_SEND_FAX_HEADER

                        log.debug("Dialing: %s" % recipient['fax'])

                        log.debug("Sending dial strings...")
                        self.create_mfpdtf_fixed_header(DT_DIAL_STRINGS, True,
                            PAGE_FLAG_NEW_DOC | PAGE_FLAG_END_DOC | PAGE_FLAG_END_STREAM) # 0x1c on Windows, we were sending 0x0c
                        #print recipient
                        dial_strings = recipient['fax'].encode('ascii')
                        log.debug(repr(dial_strings))
                        self.create_mfpdtf_dial_strings(dial_strings)

                        try:
                            self.write_stream()
                        except Error:
                            log.error("Channel write error.")
                            fax_send_state = FAX_SEND_STATE_ERROR


                    elif fax_send_state == FAX_SEND_STATE_SEND_FAX_HEADER: # -------------- Fax header (110, 120, 0)
                        log.debug("%s State: Send fax header" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_SEND_PAGES

                        try:
                            ff = open(self.f, 'rb')
                        except IOError:
                            log.error("Unable to read fax file.")
                            fax_send_state = FAX_SEND_STATE_ERROR
                            continue

                        try:
                            header = ff.read(FILE_HEADER_SIZE)
                        except IOError:
                            log.error("Unable to read fax file.")
                            fax_send_state = FAX_SEND_STATE_ERROR
                            continue

                        magic, version, total_pages, hort_dpi, vert_dpi, page_size, \
                            resolution, encoding, reserved1, reserved2 = self.decode_fax_header(header)

                        if magic != b'hplip_g3':
                            log.error("Invalid file header. Bad magic.")
                            fax_send_state = FAX_SEND_STATE_ERROR
                        else:
                            log.debug("Magic=%s Ver=%d Pages=%d hDPI=%d vDPI=%d Size=%d Res=%d Enc=%d" %
                                      (magic, version, total_pages, hort_dpi, vert_dpi, page_size, resolution, encoding))

                            log.debug("Sending fax header...")
                            self.create_mfpdtf_fixed_header(DT_FAX_IMAGES, True, PAGE_FLAG_NEW_DOC)
                            self.create_mfpdtf_fax_header(total_pages)

                            try:
                                self.write_stream()
                            except Error:
                                log.error("Unable to write to channel.")
                                fax_send_state = FAX_SEND_STATE_ERROR


                    elif fax_send_state == FAX_SEND_STATE_SEND_PAGES:  # --------------------------------- Send fax pages state machine (110, 130, 0)
                        log.debug("%s State: Send pages" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_SEND_END_OF_STREAM
                        page = BytesIO()

                        for p in range(total_pages):

                            if self.check_for_cancel():
                                fax_send_state = FAX_SEND_STATE_ABORT

                            if fax_send_state == FAX_SEND_STATE_ABORT:
                                break

                            try:
                                header = ff.read(PAGE_HEADER_SIZE)
                            except IOError:
                                log.error("Unable to read fax file.")
                                fax_send_state = FAX_SEND_STATE_ERROR
                                continue

                            page_num, ppr, rpp, bytes_to_read, thumbnail_bytes, reserved2 = \
                                self.decode_page_header(header)

                            log.debug("Page=%d PPR=%d RPP=%d BPP=%d Thumb=%d" %
                                      (page_num, ppr, rpp, bytes_to_read, thumbnail_bytes))

                            page.write(ff.read(bytes_to_read))
                            thumbnail = ff.read(thumbnail_bytes) # thrown away for now (should be 0 read)
                            page.seek(0)

                            self.create_mfpdtf_fixed_header(DT_FAX_IMAGES, page_flags=PAGE_FLAG_NEW_PAGE)
                            self.create_sop_record(page_num, hort_dpi, vert_dpi, ppr, rpp, encoding)

                            try:
                                data = page.read(RASTER_DATA_SIZE)
                            except IOError:
                                log.error("Unable to read fax file.")
                                fax_send_state = FAX_SEND_STATE_ERROR
                                continue

                            if data == '':
                                log.error("No data!")
                                fax_send_state = FAX_SEND_STATE_ERROR
                                continue

                            self.create_raster_data_record(data)
                            total_read = RASTER_DATA_SIZE

                            while True:
                                data = page.read(RASTER_DATA_SIZE)
                                total_read += RASTER_DATA_SIZE

                                dl_state = self.getFaxDownloadState()
                                if dl_state == pml.UPDN_STATE_ERRORABORT:
                                    fax_send_state = FAX_SEND_STATE_ERROR
                                    break

                                if self.check_for_cancel():
                                    fax_send_state = FAX_SEND_STATE_ABORT
                                    break

                                if data == b'':
                                    self.create_eop_record(rpp)

                                    try:
                                        self.write_stream()
                                    except Error:
                                        log.error("Channel write error.")
                                        fax_send_state = FAX_SEND_STATE_ERROR
                                    break

                                else:
                                    try:
                                        self.write_stream()
                                    except Error:
                                        log.error("Channel write error.")
                                        fax_send_state = FAX_SEND_STATE_ERROR
                                        break

                                status = self.getFaxJobTxStatus()
                                while status == pml.FAXJOB_TX_STATUS_DIALING:
                                    self.write_queue((STATUS_DIALING, 0, recipient['fax']))
                                    time.sleep(1.0)

                                    if self.check_for_cancel():
                                        fax_send_state = FAX_SEND_STATE_ABORT
                                        break

                                    dl_state = self.getFaxDownloadState()
                                    if dl_state == pml.UPDN_STATE_ERRORABORT:
                                        fax_send_state = FAX_SEND_STATE_ERROR
                                        break

                                    status = self.getFaxJobTxStatus()

                                if fax_send_state not in (FAX_SEND_STATE_ABORT, FAX_SEND_STATE_ERROR):

                                    while status == pml.FAXJOB_TX_STATUS_CONNECTING:
                                        self.write_queue((STATUS_CONNECTING, 0, recipient['fax']))
                                        time.sleep(1.0)

                                        if self.check_for_cancel():
                                            fax_send_state = FAX_SEND_STATE_ABORT
                                            break

                                        dl_state = self.getFaxDownloadState()
                                        if dl_state == pml.UPDN_STATE_ERRORABORT:
                                            fax_send_state = FAX_SEND_STATE_ERROR
                                            break

                                        status = self.getFaxJobTxStatus()

                                if status == pml.FAXJOB_TX_STATUS_TRANSMITTING:
                                    self.write_queue((STATUS_SENDING, page_num, recipient['fax']))

                                self.create_mfpdtf_fixed_header(DT_FAX_IMAGES, page_flags=0)
                                self.create_raster_data_record(data)

                                if fax_send_state in (FAX_SEND_STATE_ABORT, FAX_SEND_STATE_ERROR):
                                    break

                            page.truncate(0)
                            page.seek(0)


                    elif fax_send_state == FAX_SEND_STATE_SEND_END_OF_STREAM: # -------------- EOS (110, 140, 0)
                        log.debug("%s State: Send EOS" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_WAIT_FOR_COMPLETE
                        log.debug("End of stream...")
                        self.create_mfpdtf_fixed_header(DT_FAX_IMAGES, False, PAGE_FLAG_END_STREAM)

                        try:
                            self.write_stream()
                        except Error:
                            log.error("Channel write error.")
                            fax_send_state = FAX_SEND_STATE_ERROR

                        monitor_state = False


                    elif fax_send_state == FAX_SEND_STATE_WAIT_FOR_COMPLETE: # -------------- Wait for complete (110, 150, 0)
                        log.debug("%s State: Wait for completion" % ("*"*20))

                        fax_send_state = FAX_SEND_STATE_WAIT_FOR_COMPLETE

                        time.sleep(1.0)
                        status = self.getFaxJobTxStatus()

                        if status == pml.FAXJOB_TX_STATUS_DIALING:
                                self.write_queue((STATUS_DIALING, 0, recipient['fax']))
                                log.debug("Dialing ...")

                        elif status == pml.FAXJOB_TX_STATUS_TRANSMITTING:
                            self.write_queue((STATUS_SENDING, page_num, recipient['fax']))
                            log.debug("Transmitting ...")

                        elif status in (pml.FAXJOB_TX_STATUS_DONE, pml.FAXJOB_RX_STATUS_IDLE):
                            fax_send_state = FAX_SEND_STATE_RESET_TOKEN
                            state = STATE_NEXT_RECIPIENT
                            log.debug("Transmitting done or idle ...")

                        else:
                            self.write_queue((STATUS_SENDING, page_num, recipient['fax']))
                            log.debug("Pending ...")


                    elif fax_send_state == FAX_SEND_STATE_RESET_TOKEN: # -------------- Release fax token (110, 160, 0)
                        log.debug("%s State: Release fax token" % ("*"*20))
                        self.write_queue((STATUS_CLEANUP, 0, ''))

                        try:
                            self.dev.setPML(pml.OID_FAX_TOKEN, '\x00'*16)
                        except Error:
                            log.error("Unable to release fax token.")

                        fax_send_state = FAX_SEND_STATE_CLOSE_SESSION


                    elif fax_send_state == FAX_SEND_STATE_CLOSE_SESSION: # -------------- Close session (110, 170, 0)
                        log.debug("%s State: Close session" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_DONE
                        log.debug("Closing session...")

                        try:
                            mm.close()
                        except NameError:
                            pass

                        try:
                            ff.close()
                        except NameError:
                            pass

                        if self.dev.fax_type == FAX_TYPE_BLACK_SEND_LATE_OPEN:
                            log.debug("Closing fax channel.")
                            self.dev.closeFax()

                        self.dev.setPML(pml.OID_FAX_DOWNLOAD, pml.UPDN_STATE_IDLE)

                        time.sleep(1)

                        if self.dev.fax_type == FAX_TYPE_BLACK_SEND_EARLY_OPEN:
                            log.debug("Closing fax channel.")
                            self.dev.closeFax()

                        self.dev.close()


            elif state == STATE_CLEANUP: # --------------------------------- Cleanup (120, 0, 0)
                log.debug("%s State: Cleanup" % ("*"*20))

                if self.remove_temp_file:
                    log.debug("Removing merged file: %s" % self.f)
                    try:
                        os.remove(self.f)
                        log.debug("Removed")
                    except OSError:
                        log.debug("Not found")

                state = STATE_DONE



# --------------------------------- Support functions


    def getFaxDownloadState(self):
        result_code, state = self.dev.getPML(pml.OID_FAX_DOWNLOAD)
        if state:
            log.debug("D/L State=%d (%s)" % (state, pml.UPDN_STATE_STR.get(state, 'Unknown')))
            return state
        else:
            return pml.UPDN_STATE_ERRORABORT

    def getFaxDownloadError(self):
        result_code, state = self.dev.getPML(pml.OID_FAX_DOWNLOAD_ERROR)
        if state:
            return state
        else:
            return pml.DN_ERROR_UNKNOWN

    def getFaxJobTxStatus(self):
        result_code, status = self.dev.getPML(pml.OID_FAXJOB_TX_STATUS)
        if status:
            log.debug("Tx Status=%d (%s)" % (status, pml.FAXJOB_TX_STATUS_STR.get(status, 'Unknown')))
            return status
        else:
            return pml.FAXJOB_TX_STATUS_IDLE

    def getFaxJobRxStatus(self):
        result_code, status = self.dev.getPML(pml.OID_FAXJOB_RX_STATUS)
        if status:
            log.debug("Rx Status=%d (%s)" % (status, pml.FAXJOB_RX_STATUS_STR.get(status, 'Unknown')))
            return status
        else:
            return pml.FAXJOB_RX_STATUS_IDLE

    def getCfgUploadState(self):
        result_code, state = self.dev.getPML(pml.OID_DEVICE_CFG_UPLOAD)
        if state:
            log.debug("Cfg Upload State = %d (%s)" % (state, pml.UPDN_STATE_STR.get(state, 'Unknown')))
            return state
        else:
            return pml.UPDN_STATE_ERRORABORT

    def create_mfpdtf_fixed_header(self, data_type, send_variant=False, page_flags=0):
        header_len = FIXED_HEADER_SIZE

        if send_variant:
            if data_type == DT_DIAL_STRINGS:
                    header_len += DIAL_STRINGS_VARIANT_HEADER_SIZE

            elif data_type == DT_FAX_IMAGES:
                header_len += FAX_IMAGE_VARIANT_HEADER_SIZE

        self.stream.write(struct.pack("<IHBB",
                          0, header_len, data_type, page_flags))


    def create_mfpdtf_dial_strings(self, number):
        p = struct.pack("<BBHH51s",
                          MAJOR_VER, MINOR_VER,
                          1, 51, number[:51])
        log.debug(repr(p))
        self.stream.write(p)


    def adjust_fixed_header_block_size(self):
        size = self.stream.tell()
        self.stream.seek(0)
        self.stream.write(struct.pack("<I", size))


    def create_sop_record(self, page_num, hort_dpi, vert_dpi, ppr, rpp, encoding, bpp=1):
        self.stream.write(struct.pack("<BBHHHIHHHHHHIHHHH",
                            RT_START_PAGE, encoding, page_num,
                            ppr, bpp,
                            rpp, 0x00, hort_dpi, 0x00, vert_dpi,
                            ppr, bpp,
                            rpp, 0x00, hort_dpi, 0x00, vert_dpi))


    def create_eop_record(self, rpp):
        self.stream.write(struct.pack("<BBBBII",
                            RT_END_PAGE, 0, 0, 0,
                            rpp, 0,))


    def create_raster_data_record(self, data):
        assert len(data) <= RASTER_DATA_SIZE
        self.stream.write(struct.pack("<BBH",
                        RT_RASTER, 0, len(data),))
        self.stream.write(data)


    def create_mfpdtf_fax_header(self, total_pages):
        self.stream.write(struct.pack("<BBBHBI20s20s20sI",
                            MAJOR_VER, MINOR_VER, SRC_HOST, total_pages,
                            TTI_PREPENDED_TO_IMAGE, 0, b'', b'', b'', 0))


    def write_stream(self):
        self.adjust_fixed_header_block_size()
        self.dev.writeFax(self.stream.getvalue())
        self.stream.truncate(0)
        self.stream.seek(0)
