# -*- coding: utf-8 -*-
#
# (c) Copyright 2015 HP Development Company, L.P.
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
# Author: Suma Byrappa
#

# Std Lib
import sys
import os
import os.path
import struct
import time
import threading
from io import BytesIO  #TBD check whether this requires base.six ...
from stat import *

# Local
from base.g import *
from base.codes import *
from base import device, utils, pml, codes
from prnt import cups
from .fax import *
import hpmudext

try:
    from ctypes import cdll
    from ctypes import *
    import ctypes.util as cu
except ImportError:
    log.error("Marvell fax support requires python-ctypes module. Exiting!")
    sys.exit(1)

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    memoryview = buffer
            
# **************************************************************************** #
# Marvell Message Types
START_FAX_JOB = 0
END_FAX_JOB = 1
SEND_FAX_JOB = 2
GET_FAX_LOG_ENTRY = 5
GET_FAX_SETTINGS = 9
SET_FAX_SETTINGS = 10
CLEAR_FAX_STATUS = 11
REQUEST_FAX_STATUS = 12
FAX_DATA_BLOCK = 13

SUCCESS = 0
FAILURE = 1

FAX_DATA_BLOCK_SIZE = 4096

# Fax data variant header TTI header control
TTI_NONE = 0
TTI_PREPENDED_TO_IMAGE = 1
TTI_OVERLAYED_ON_IMAGE = 2

# **************************************************************************** #
class MarvellFaxDevice(FaxDevice):

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

        try:
            sendfax_path = utils.which('hp-sendfax')
            sendfax_a_path = os.readlink(sendfax_path+"/hp-sendfax")
            if not os.path.isabs(sendfax_a_path):
                   sendfax_f_path = os.path.join(sendfax_path, sendfax_a_path)
            else:
                   sendfax_f_path = sendfax_a_path

            sendfax_abs_path = os.path.realpath(sendfax_f_path)
            (head, tail) = os.path.split(sendfax_abs_path)  

            lib_name = head+"/fax/plugins/fax_marvell.so"
            log.debug("Load the library %s\n" % lib_name)
            from installer import pluginhandler
            pluginObj = pluginhandler.PluginHandle()

            if pluginObj.getStatus() != pluginhandler.PLUGIN_INSTALLED:
                log.error("Loading %s failed. Try after installing plugin libraries\n" %lib_name);
                log.info("Run \"hp-plugin\" to installa plugin libraries if you are not automatically prompted\n")
                job_id =0;
                self.service.SendEvent(device_uri, printer_name, EVENT_FAX_FAILED_MISSING_PLUGIN, os.getenv('USER'), job_id, "Plugin is not installed")
                sys.exit(1)
            else:
                self.libfax_marvell = cdll.LoadLibrary(lib_name)
        except Error as e:
            log.error("Loading fax_marvell failed (%s)\n" % e.msg);
            sys.exit(1)


    # Creates a message packet for message type given in argument, and sends it to device
    #
    # 1. Gets the message packet using fax_marvell.so
    # 2. Writes the packets to device
    # 3. Returns the result of send operation
    def send_packet_for_message(self, msg_type, param1=0, param2=0, status=0, data_len=0):
        int_array_8 = c_int * 8
        i_buf = int_array_8(0, 0, 0, 0, 0, 0, 0, 0)

        result = self.libfax_marvell.create_packet(msg_type, param1, param2, status, data_len, byref(i_buf))
        buf = memoryview(i_buf)
        try:
            log.log_data(buf.tobytes(), 32)
        except:
            log.log_data(buf, 32)    # For Python 2.6
        self.writeMarvellFax(buf)
#        self.closeMarvellFax()

        return result


    # Reads response message packet from the device for message type given in argument.
    #       Reads the response from device, and sends the data read to the caller of this method
    #       No Marvell specific code or info
    def read_response_for_message(self, msg_type):
        ret_buf = BytesIO()
        while self.readMarvellFax(32, ret_buf, timeout=10):
                            pass

        ret_buf = ret_buf.getvalue()
        #self.closeMarvellFax()

        log.debug("response_for_message (%d): response packet is\n" % msg_type)
        log.log_data(ret_buf, 32)

        return ret_buf


    def setPhoneNum(self, num):
        log.debug("************************* setPhoneNum (%s) START **************************" % num)

        set_buf = BytesIO()

        int_array = c_int * 8
        i_buf = int_array(0, 0, 0, 0, 0, 0, 0, 0)

        char_array = c_char * 308
        c_buf = char_array()

        date_array = c_char * 15
        date_buf = date_array()
        t = time.localtime()
        date_buf = "%4d%02d%02d%02d%02d%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
        log.debug("Date and Time string is ==>")
        log.debug(date_buf)

        result = self.libfax_marvell.create_packet(SET_FAX_SETTINGS, 0, 0, 0, 0, byref(i_buf))
        result = self.libfax_marvell.create_fax_settings_packet(self.station_name, str(num), date_buf, byref(c_buf))

        msg_buf = memoryview(i_buf)
        msg_c_buf = memoryview(c_buf)

        for i in range(0, 32):
            try:
                set_buf.write(str(msg_buf.tobytes()[i]).encode('utf-8'))
            except:
                set_buf.write(str(msg_buf[i]))   #For python 2.6
        for i in range(0, 308):
            try:
                set_buf.write(str(msg_c_buf.tobytes()[i]).encode('utf-8'))
            except:
                 set_buf.write(msg_c_buf[i])      #For python 2.6

        set_buf = set_buf.getvalue()
        log.debug("setPhoneNum: send SET_FAX_SETTINGS message and data ===> ")
        log.log_data(set_buf, 340)

        self.writeMarvellFax(set_buf)
        ret_buf = BytesIO()
        while self.readMarvellFax(32, ret_buf, timeout=10):
                            pass
        ret_buf = ret_buf.getvalue()
        self.closeMarvellFax()

        response = self.libfax_marvell.extract_response(ret_buf) 
        log.debug("setPhoneNum: response is %d" % response)
 
        log.debug("************************* setPhoneNum END **************************")
        return response


    def getPhoneNum(self):
        int_array_8 = c_int * 8
        i_buf = int_array_8(0, 0, 0, 0, 0, 0, 0, 0)
        ph_buf = int_array_8(0, 0, 0, 0, 0, 0, 0, 0)

        log.debug("******************** getPhoneNum START **********************")
        result = self.libfax_marvell.create_packet(GET_FAX_SETTINGS, 0, 0, 0, 0, byref(i_buf))
        buf = memoryview(i_buf)
        self.writeMarvellFax(buf)
        ret_buf = BytesIO()
        while self.readMarvellFax(512, ret_buf, timeout=10):
                            pass
        ret_buf = ret_buf.getvalue()
        self.closeMarvellFax()

        response = self.libfax_marvell.extract_response(ret_buf) 
        log.debug("create_packet: response is %d" % response)
 
        response = self.libfax_marvell.extract_phone_number(ret_buf, ph_buf) 
        ph_num_buf = BytesIO()
        for i in range(0, 7):
            if ph_buf[i]:
               try:
                   ph_num_buf.write(str(ph_buf[i]))
               except:
                   pass

        ph_num_buf = ph_num_buf.getvalue()
        log.debug("getPhoneNum: ph_num_buf=%s " % (ph_num_buf))

        log.debug("******************** getPhoneNum END **********************")
        return str(ph_num_buf)


    # Note down the fax (phone) number
    phone_num = property(getPhoneNum, setPhoneNum)


    # Set the station name in the device's settings
    #
    def setStationName(self, name):
        log.debug("************************* setStationName(%s) START **************************" % name)

        int_array = c_int * 8
        i_buf = int_array(0, 0, 0, 0, 0, 0, 0, 0)
        set_buf = BytesIO()

        char_array = c_char * 308
        c_buf = char_array()

        date_array = c_char * 15
        date_buf = date_array()
        t = time.localtime()
        date_buf = "%4d%02d%02d%02d%02d%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
        log.debug("Date and Time string is ==>")
        log.debug(date_buf)

        result = self.libfax_marvell.create_packet(SET_FAX_SETTINGS, 0, 0, 0, 0, byref(i_buf))
        
        try:
            result = self.libfax_marvell.create_fax_settings_packet(name, self.phone_num, date_buf, byref(c_buf))
        except(UnicodeEncodeError, UnicodeDecodeError):
            log.error("Unicode Error")

        msg_buf = memoryview(i_buf)
        msg_c_buf = memoryview(c_buf)

        for i in range(0, 32):
            try:
                set_buf.write(str(msg_buf.tobytes()[i]).encode('utf-8'))
            except:
                set_buf.write(msg_buf[i])  #For python 2.6
        for i in range(0, 308):
            try:
                set_buf.write(str(msg_c_buf.tobytes()[i]).encode('utf-8'))
            except:
                set_buf.write(msg_c_buf[i])   #For python 2.6
        set_buf = set_buf.getvalue()
        log.debug("setStationName: SET_FAX_SETTINGS message and data ===> ")
        log.log_data(set_buf, 340)

        self.writeMarvellFax(set_buf)
        ret_buf = BytesIO()
            
        while self.readMarvellFax(32, ret_buf, timeout=10):
                            pass
        ret_buf = ret_buf.getvalue()
        self.closeMarvellFax()

        response = self.libfax_marvell.extract_response(ret_buf) 
        log.debug("setStationName: response is %d" % response)
 
        log.debug("************************* setStationName END **************************")
        return response


    def getStationName(self):
        int_array = c_int * 8
        i_buf = int_array(0, 0, 0, 0, 0, 0, 0, 0)
        st_buf = create_string_buffer(128)

        log.debug("************************* getStationName START **************************")

        result = self.libfax_marvell.create_packet(GET_FAX_SETTINGS, 0, 0, 0, 0, byref(i_buf))

        buf = memoryview(i_buf)
        self.writeMarvellFax(buf)
        #self.closeMarvellFax()

        ret_buf = BytesIO()
        while self.readMarvellFax(512, ret_buf, timeout=10):
                            pass

        ret_buf = ret_buf.getvalue()
        self.closeMarvellFax()

        response = self.libfax_marvell.extract_response(ret_buf)
        log.debug("getStationName: response is %d" % response)

        result = self.libfax_marvell.extract_station_name(ret_buf, st_buf) 
        log.debug("getStationName: station_name=%s ; result is %d" % (st_buf.value, result))
 
        log.debug("************************* getStationName END **************************")
        return st_buf.value.decode('utf-8')


   # Note down the station-name
    station_name = property(getStationName, setStationName)


    # Set date and time in the device's settings
    #
    # 1. Gets the message packet and fax_settings packet using fax_marvell.so 
    # 2. Writes the packets to the device; Reads response from the device
    # 3. Extracts the status from the device's response
    def setDateAndTime(self):
        int_array = c_int * 8
        i_buf = int_array(0, 0, 0, 0, 0, 0, 0, 0)

        log.debug("************************* setDateAndTime START **************************")

        c_buf = create_string_buffer(308)
        set_buf = BytesIO()
        ret_buf = BytesIO()
        date_array = c_char * 15
        date_buf = date_array()

        t = time.localtime()

        date_buf = "%4d%02d%02d%02d%02d%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
        log.debug("Date and Time string is ==>")
        log.debug(date_buf)

        result = self.libfax_marvell.create_packet(SET_FAX_SETTINGS, 0, 0, 0, 0, byref(i_buf))
# TBD: Need to check.. create_marvell_faxsettings_pkt showing as not defined...
#        result = create_marvell_faxsettings_pkt(self.phone_num, self.station_name, date_buf, c_buf)

        msg_buf = memoryview(i_buf)
        for i in range(0, 31):
            try:
                set_buf.write(msg_buf.tobytes()[i:i+1])
            except:
                set_buf.write(msg_buf[i])  # For python 2.6

        set_buf.write(c_buf.raw)
        set_buf = set_buf.getvalue()
        self.writeMarvellFax(set_buf)
        while self.readMarvellFax(32, ret_buf, timeout=5):
                            pass
        ret_buf = ret_buf.getvalue()
        self.closeMarvellFax()

        response = self.libfax_marvell.extract_response(ret_buf)
        log.debug("setDateAndTime: response is %d" % response)

        return response


    # Get the state of the device 
    #
    # 1. Gets the message packet using fax_marvell.so 
    # 2. Writes the packet to the device; Reads response from the device
    # 3. Extracts the response status and device status from the device's response
    def getFaxDeviceState(self):
        log.debug("************************* getFaxDeviceState: START **************************")

        int_array = c_int * 8
        i_buf = int_array(0, 0, 0, 0, 0, 0, 0, 0)
        param1 = c_int(0)

        result = self.libfax_marvell.create_packet(REQUEST_FAX_STATUS, 0, 0, 0, 0, byref(i_buf))
        buf = memoryview(i_buf)
        self.writeMarvellFax(buf)

        ret_buf = BytesIO()
        while self.readMarvellFax(32, ret_buf, timeout=5):
                            pass
        ret_buf = ret_buf.getvalue()
        self.closeMarvellFax()

        response = self.libfax_marvell.extract_response(ret_buf)
        log.debug("getFaxDeviceState: response is %d" % response)

        return response


    # Creates a thread which does actual Fax submission the state of the device 
    #
    def sendFaxes(self, phone_num_list, fax_file_list, cover_message='', cover_re='',
                  cover_func=None, preserve_formatting=False, printer_name='',
                  update_queue=None, event_queue=None):

        if not self.isSendFaxActive():

            self.send_fax_thread = MarvellFaxSendThread(self, self.service, phone_num_list, fax_file_list,
                                                    cover_message, cover_re, cover_func,
                                                    preserve_formatting,
                                                    printer_name, update_queue,
                                                    event_queue)

            self.send_fax_thread.start()
            return True
        else:
            return False



# **************************************************************************** #
# Does the actual Fax transmission
# **************************************************************************** #
class MarvellFaxSendThread(FaxSendThread):
    def __init__(self, dev, service, phone_num_list, fax_file_list,
                 cover_message='', cover_re='', cover_func=None, preserve_formatting=False,
                 printer_name='', update_queue=None, event_queue=None):

        FaxSendThread.__init__(self, dev, service, phone_num_list, fax_file_list,
             cover_message, cover_re, cover_func, preserve_formatting,
             printer_name, update_queue, event_queue)


    def run(self):

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

        rec_name = None
        rec_num = None

        state = STATE_READ_SENDER_INFO
        self.rendered_file_list = []

        while state != STATE_DONE: # --------------------------------- Fax state machine
            if self.check_for_cancel():
                log.debug("***** Job is Cancelled.")
                state = STATE_ABORTED

            log.debug("*************** STATE=(%d, 0, 0)" % state)

            if state == STATE_ABORTED: # --------------------------------- Aborted 
                log.error("Aborted by user.")
                self.write_queue((STATUS_IDLE, 0, ''))
                state = STATE_CLEANUP


            elif state == STATE_SUCCESS: # --------------------------------- Success 
                log.debug("Success.")
                self.write_queue((STATUS_COMPLETED, 0, ''))
                state = STATE_CLEANUP


            elif state == STATE_ERROR: # --------------------------------- Error 
                log.error("Error, aborting.")
                self.write_queue((STATUS_ERROR, 0, ''))
                state = STATE_CLEANUP


            elif state == STATE_BUSY: # --------------------------------- Busy 
                log.error("Device busy, aborting.")
                self.write_queue((STATUS_BUSY, 0, ''))
                state = STATE_CLEANUP


            elif state == STATE_READ_SENDER_INFO: # --------------------------------- Get sender info 
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
                            self.sender_fax = self.dev.phone_num
                        except Error:
                            log.error("Getting station-name and phone_num failed!")
                            state = STATE_ERROR

                finally:
                    self.dev.close()


            elif state == STATE_PRERENDER: # --------------------------------- Pre-render non-G3 files 
                log.debug("%s State: Pre-render non-G3 files" % ("*"*20))
                state = self.pre_render(STATE_COUNT_PAGES)


            elif state == STATE_COUNT_PAGES: # --------------------------------- Get total page count 
                log.debug("%s State: Get total page count" % ("*"*20))
                state = self.count_pages(STATE_NEXT_RECIPIENT)


            elif state == STATE_NEXT_RECIPIENT: # --------------------------------- Loop for multiple recipients
                log.debug("%s State: Next recipient" % ("*"*20))
                state = STATE_COVER_PAGE

                try:
                    recipient = next(next_recipient)

                    self.write_queue((STATUS_SENDING_TO_RECIPIENT, 0, recipient['name']))
                    
                    rec_name = recipient['name']
                    rec_num = recipient['fax'].encode('ascii')
                    log.debug("recipient is %s num is %s" % (rec_name, rec_num))

                except StopIteration:
                    state = STATE_SUCCESS
                    log.debug("Last recipient.")
                    continue

                self.recipient_file_list = self.rendered_file_list[:]


            elif state == STATE_COVER_PAGE: # --------------------------------- Create cover page 
                log.debug("%s State: Render cover page" % ("*"*20))
                state = self.cover_page(recipient)


            elif state == STATE_SINGLE_FILE: # --------------------------------- Special case for single file (no merge)
                log.debug("%s State: Handle single file" % ("*"*20))
                state = self.single_file(STATE_SEND_FAX)

            elif state == STATE_MERGE_FILES: # --------------------------------- Merge multiple G3 files 
                log.debug("%s State: Merge multiple files" % ("*"*20))
                log.debug("Not merging the files for Marvell support")
                state = STATE_SEND_FAX

            elif state == STATE_SEND_FAX: # --------------------------------- Send fax state machine 
                log.debug("%s State: Send fax" % ("*"*20))
                state = STATE_NEXT_RECIPIENT

                next_file = self.next_file_gen()

                FAX_SEND_STATE_DONE = 0
                FAX_SEND_STATE_SUCCESS = 10
                FAX_SEND_STATE_ABORT = 21
                FAX_SEND_STATE_ERROR = 22
                FAX_SEND_STATE_BUSY = 25
                FAX_SEND_STATE_DEVICE_OPEN = 30
                FAX_SEND_STATE_NEXT_FILE = 35
                FAX_SEND_STATE_CHECK_IDLE = 40
                FAX_SEND_STATE_START_JOB_REQUEST = 50
                FAX_SEND_STATE_SEND_JOB_REQUEST = 60
                FAX_SEND_STATE_SET_PARAMS = 70
                FAX_SEND_STATE_SEND_FAX_HEADER = 80
                FAX_SEND_STATE_SEND_FILE_DATA = 90
                FAX_SEND_STATE_END_FILE_DATA = 100
                FAX_SEND_STATE_END_JOB_REQUEST = 110
                FAX_SEND_STATE_GET_LOG_INFORMATION = 120

                monitor_state = False
                current_state = SUCCESS
                fax_send_state = FAX_SEND_STATE_DEVICE_OPEN

                while fax_send_state != FAX_SEND_STATE_DONE:

                    if self.check_for_cancel():
                        log.error("Fax send aborted.")
                        fax_send_state = FAX_SEND_STATE_ABORT

                    if monitor_state:
                        fax_state = self.getFaxDeviceState()
                        if fax_state != SUCCESS:
                            log.error("Device is in error state=%d" % fax_state)
                            fax_send_state = FAX_SEND_STATE_ERROR
                            state = STATE_ERROR


                    log.debug("*********  FAX_SEND_STATE=(%d, %d, %d)" % (STATE_SEND_FAX, fax_send_state, current_state))

                    if fax_send_state == FAX_SEND_STATE_ABORT: # -------------- Abort 
                        monitor_state = False
                        fax_send_state = FAX_SEND_STATE_END_JOB_REQUEST
                        state = STATE_ABORTED

                    elif fax_send_state == FAX_SEND_STATE_ERROR: # -------------- Error 
                        log.error("Fax send error.")
                        monitor_state = False

                        fax_send_state = FAX_SEND_STATE_END_JOB_REQUEST
                        state = STATE_ERROR

                    elif fax_send_state == FAX_SEND_STATE_BUSY: # -------------- Busy 
                        log.error("Fax device busy.")
                        monitor_state = False
                        fax_send_state = FAX_SEND_STATE_END_JOB_REQUEST
                        state = STATE_BUSY

                    elif fax_send_state == FAX_SEND_STATE_SUCCESS: # -------------- Success 
                        log.debug("Fax send success.")
                        monitor_state = False
                        fax_send_state = FAX_SEND_STATE_END_JOB_REQUEST
                        state = STATE_NEXT_RECIPIENT

                    elif fax_send_state == FAX_SEND_STATE_DEVICE_OPEN: # -------------- Device open 
                        log.debug("%s State: Open device" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_NEXT_FILE
                        try:
                            self.dev.open()
                        except Error as e:
                            log.error("Unable to open device (%s)." % e.msg)
                            fax_send_state = FAX_SEND_STATE_ERROR
                        else:
                            if self.dev.device_state == DEVICE_STATE_NOT_FOUND:
                                fax_send_state = FAX_SEND_STATE_ERROR


                    elif fax_send_state == FAX_SEND_STATE_NEXT_FILE: # -------------- Device open 
                        log.debug("%s State: Open device" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_CHECK_IDLE
                        try:
                             fax_file = next(next_file)
                             self.f = fax_file[0]
                             log.debug("***** file name is : %s..." % self.f)
                        except StopIteration:
                             log.debug("file(s) are sent to the device" )
                             fax_send_state = FAX_SEND_STATE_DONE


                    elif fax_send_state == FAX_SEND_STATE_CHECK_IDLE: # -------------- Check for initial idle
                        log.debug("%s State: Check idle" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_START_JOB_REQUEST

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
                            log.debug("Magic=%s Version=%d Total Pages=%d hDPI=%d vDPI=%d Size=%d Resolution=%d Encoding=%d"
                            % (magic, version, total_pages, hort_dpi, vert_dpi, page_size, resolution, encoding))

                        dev_state = self.dev.getFaxDeviceState()

                        if (dev_state == 0):
                           log.debug("State: device status is zero ")
                        else:
                           log.debug("State: device status is non-zero ")
                           fax_send_state = FAX_SEND_STATE_BUSY


                    elif fax_send_state == FAX_SEND_STATE_START_JOB_REQUEST: # -------------- Request fax start
                        log.debug("%s State: Request start" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_SEND_JOB_REQUEST

                        file_len = os.stat(self.f)[ST_SIZE]
                        tx_data_len = file_len - FILE_HEADER_SIZE - (PAGE_HEADER_SIZE*total_pages)
                        log.debug("#### file_len = %d" % file_len)
                        log.debug("#### tx_data_len = %d" % tx_data_len)
                        ret_value = self.dev.send_packet_for_message(START_FAX_JOB, tx_data_len, 0, 0, 0)
                        if ret_value:
                           log.debug("Sending start fax request failed with %d" % ret_value)
                           fax_send_state = FAX_SEND_STATE_ERROR
                        else:
                           log.debug("Successfully sent start fax request")
                           ret_buf = self.dev.read_response_for_message(START_FAX_JOB)
                           dev_response = self.dev.libfax_marvell.extract_response(ret_buf)
                           if dev_response:
                              log.debug("start-fax request failed with %d" % dev_response)
                              fax_send_state = FAX_SEND_STATE_ERROR
                           else:
                              log.debug("start-fax request is successful")

                    elif fax_send_state == FAX_SEND_STATE_SEND_JOB_REQUEST: # -------------- Set data request 
                        log.debug("%s State: Send data request" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_SET_PARAMS 

                        ret_value = self.dev.send_packet_for_message(SEND_FAX_JOB)
                        if ret_value:
                           log.debug("Sending send-data request failed with %d" % ret_value)
                           fax_send_state = FAX_SEND_STATE_ERROR
                        else:
                           log.debug("Successfully sent send-fax request")


                    elif fax_send_state == FAX_SEND_STATE_SET_PARAMS: # -------------- Set fax send params 
                        log.debug("%s State: Set params" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_SEND_FAX_HEADER

                        c_buf = create_string_buffer(68)
                        set_buf = BytesIO()

                        no_data = None
                        ret_val = self.dev.libfax_marvell.create_job_settings_packet(no_data, rec_num, c_buf)
                        set_buf.write(c_buf.raw)
                        set_buf = set_buf.getvalue()

                        self.dev.writeMarvellFax(set_buf)
                        #self.dev.closeMarvellFax()


                    elif fax_send_state == FAX_SEND_STATE_SEND_FAX_HEADER: # -------------- Fax header 
                        #   Taken care by the device
                        fax_send_state = FAX_SEND_STATE_SEND_FILE_DATA

                    elif fax_send_state == FAX_SEND_STATE_SEND_FILE_DATA:  # --------------------------------- Send fax pages state machine 
                        log.debug("%s State: Send pages" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_END_FILE_DATA
                        current_state = SUCCESS
                        page = BytesIO()

                        file_len = os.stat(self.f)[ST_SIZE]
                        bytes_to_read = file_len - FILE_HEADER_SIZE - (PAGE_HEADER_SIZE*total_pages)

                        for p in range(total_pages):

                            if self.check_for_cancel():
                                current_state = FAILURE

                            if current_state == FAILURE:
                                break

                            try:
                                header = ff.read(PAGE_HEADER_SIZE)
                            except IOError:
                                log.error("Unable to read fax file.")
                                current_state = FAILURE
                                continue

                            page_num, ppr, rpp, b_to_read, thumbnail_bytes, reserved2 = \
                                self.decode_page_header(header)

                            log.debug("Page=%d PPR=%d RPP=%d BPP=%d Thumb=%d" %
                                      (page_num, ppr, rpp, b_to_read, thumbnail_bytes))

                            page.write(ff.read(b_to_read))
                            thumbnail = ff.read(thumbnail_bytes) # thrown away for now (should be 0 read)
                            page.seek(0)
                            bytes_to_write = b_to_read
                            total_read = 0
                            while (bytes_to_write > 0):
                               try:
                                   data = page.read(FAX_DATA_BLOCK_SIZE)
                               except IOError:
                                   log.error("Unable to read fax file.")
                                   current_state = FAILURE
                                   continue

                               if data == '':
                                   log.error("No data!")
                                   current_state = FAILURE
                                   break

                               if self.check_for_cancel():
                                   current_state = FAILURE
                                   log.error("Job is cancelled. Aborting...")
                                   break

                               total_read += FAX_DATA_BLOCK_SIZE

                               try:
                                   ret_value = self.dev.send_packet_for_message(FAX_DATA_BLOCK, 0, 0, 0, len(data))
                                   if ret_value:
                                      log.debug("Sending fax-data-block request failed with %d" % ret_value)
                                      current_state = FAILURE
                                   else:
                                      log.debug("Successfully sent fax-data-block request")

                                   self.dev.writeMarvellFax(data)
                                   #self.dev.closeMarvellFax()
                               except Error:
                                   log.error("Channel write error.")
                                   current_state = FAILURE
                                   break

                               bytes_to_write = bytes_to_write - FAX_DATA_BLOCK_SIZE

                            page.truncate(0)
                            page.seek(0)


                    elif fax_send_state == FAX_SEND_STATE_END_FILE_DATA: # -------------- end-of-data
                        log.debug("%s State: Send end-of-file-data request" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_END_JOB_REQUEST

                        ret_value = self.dev.send_packet_for_message(FAX_DATA_BLOCK, 0, 0, current_state, 0)
                        if ret_value:
                           log.debug("Sending fax-data-block packet failed with %d" % ret_value)
                           current_state = FAILURE
                        else:
                           log.debug("Successfully sent fax-data-block request")
                           ret_buf = self.dev.read_response_for_message(SEND_FAX_JOB)
                           dev_response = self.dev.libfax_marvell.extract_response(ret_buf)
                           if dev_response:
                              log.debug("send-fax request failed with %d" % dev_response)
                              current_state = FAILURE
                           else:
                              log.debug("send-fax request is successful")

                           if current_state:
                              log.debug("Exiting...")
                              sys.exit(1)


                    elif fax_send_state == FAX_SEND_STATE_END_JOB_REQUEST: # -------------- Wait for complete 
                        log.debug("%s State: End the job" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_NEXT_FILE

                        ret_value = self.dev.send_packet_for_message(END_FAX_JOB, 0, 0, current_state, 0)
                        if ret_value:
                           log.debug("Sending end-fax-job packet failed with %d" % ret_value)
                           current_state = FAILURE
                        else:
                           log.debug("Successfully sent end-fax-job request")
                           ret_buf = self.dev.read_response_for_message(END_FAX_JOB)
                           dev_response = self.dev.libfax_marvell.extract_response(ret_buf)
                           if dev_response:
                              log.debug("end-fax-job request failed with %d" % dev_response)
                              current_state = FAILURE
                           else:
                              log.debug("end-fax-job request is successful")

                        if current_state != SUCCESS:
                           # There was an error during transmission...
                           log.error("An error occurred! setting fax_send_state to DONE")
                           fax_send_state = FAX_SEND_STATE_DONE

                        try:
                            ff.close()
                        except NameError:
                            pass

                        time.sleep(1)

                        self.dev.close()


            elif state == STATE_CLEANUP: # --------------------------------- Cleanup 
                log.debug("%s State: Cleanup" % ("*"*20))

                if self.remove_temp_file:
                    log.debug("Removing merged file: %s" % self.f)
                    try:
                        os.remove(self.f)
                        log.debug("Removed")
                    except OSError:
                        log.debug("Not found")

                state = STATE_DONE


