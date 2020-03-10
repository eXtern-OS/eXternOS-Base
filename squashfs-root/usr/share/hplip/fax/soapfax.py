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
import time
from io import BytesIO
from base.sixext.moves import urllib2_request, urllib2_parse, urllib2_error # TODO: Replace with urllib2 (urllib is deprecated in Python 3.0)
import re

# Local
from base.g import *
from base.codes import *
from base import device, utils, codes, dime
from .fax import *
from base.sixext import PY3
from base.sixext import to_bytes_utf8
#import xml.parsers.expat as expat


# **************************************************************************** #

http_result_pat = re.compile("""HTTP/\d.\d\s(\d+)""", re.I)


TIME_FORMAT_AM_PM = 1
TIME_FORMAT_24HR = 2

DATE_FORMAT_MM_DD_YYYY = 1
DATE_FORMAT_DD_MM_YYYY = 2
DATE_FORMAT_YYYY_MM_DD = 3

AM = 1
PM = 0

HTTP_OK = 200
HTTP_ERROR = 500

PIXELS_PER_LINE = 2528


# **************************************************************************** #
class SOAPFaxDevice(FaxDevice):

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

        if self.bus == 'net':
            self.http_host = self.host
        else:
            self.http_host = 'localhost'


    def post(self, url, post):
        s = []
        for k, v in list(post.items()):
            if PY3:
                s.append("%s=%s" % (k, urllib2_parse.quote(str(v))))
            else:
                s.append("%s=%s" % (k, urllib2_parse.quote(v.encode('utf-8'))))

        s = '&'.join(s)

        log.debug(s)

        data = """POST %s HTTP/1.1
Connection: Keep-alive
User-agent: hplip/2.0
Host: %s
Content-length: %d
Cache-control: No-cache

%s""" % (url, self.http_host, len(s), s)

        log.log_data(data)
        self.writeEWS(data.encode('utf-8'))
        ret = BytesIO()

        while self.readEWS(4096, ret, timeout=5):
            pass

        ret = ret.getvalue()
        log.log_data(ret)

        self.closeEWS()

        match = http_result_pat.match(ret.decode('utf-8'))
        try:
            code = int(match.group(1))
        except (ValueError, TypeError):
            code = HTTP_ERROR

        return code == HTTP_OK


    def setPhoneNum(self, num):
        return self.post("/hp/device/set_config.html", {"FaxNumber": str(num)})


    def getPhoneNum(self):
        stream = BytesIO()
        self.getEWSUrl("/hp/device/settings_fax_setup_wizard.xml", stream)
        fax_setup = utils.XMLToDictParser().parseXML(stream.getvalue())
        return fax_setup['faxsetupwizard-faxvoicenumber-faxnumber']

    phone_num = property(getPhoneNum, setPhoneNum)


    def setStationName(self, name):
        try:
            name = name
        except(UnicodeEncodeError, UnicodeDecodeError):
            log.error("Unicode Error")
        return self.post("/hp/device/set_config.html", {"FaxCompanyName": name})


    def getStationName(self):
        stream = BytesIO()
        self.getEWSUrl("/hp/device/settings_fax_setup_wizard.xml", stream)
        fax_setup = utils.XMLToDictParser().parseXML(stream.getvalue())
        return fax_setup['faxsetupwizard-userinformation-faxcompanyname']

    station_name = property(getStationName, setStationName)


    def setDateAndTime(self):
        stream = BytesIO()
        self.getEWSUrl("/hp/device/settings_fax_setup_wizard.xml", stream)
        fax_setup = utils.XMLToDictParser().parseXML(stream.getvalue())
        timeformat = fax_setup['faxsetupwizard-time-timeformat']

        try:
            timeformat = int(timeformat)
        except (ValueError, TypeError):
            timeformat = TIME_FORMAT_AM_PM

        log.debug("timeformat: %d" % timeformat)

        dateformat = fax_setup['faxsetupwizard-date-dateformat']

        try:
            dateformat = int(dateformat)
        except (ValueError, TypeError):
            dateformat = DATE_FORMAT_DD_MM_YYYY

        log.debug("dateformat: %d" % dateformat)

        t = time.localtime()
        hr = t[3]

        am_pm = PM
        if t[3] < 12:
            am_pm = AM

        if timeformat == TIME_FORMAT_AM_PM and hr > 12:
            hr -= 12

        post = {"DateFormat" : str(dateformat),
                "Year" : str(t[0]),
                "Month" : str(t[1]),
                "Day" : str(t[2]),
                "TimeFormat" : str(timeformat),
                "Hour" : str(hr),
                "Minute" : str(t[4])}

        if timeformat == TIME_FORMAT_AM_PM:
            post['AM'] = str(am_pm)

        return self.post("/hp/device/set_config.html", post)


    def sendFaxes(self, phone_num_list, fax_file_list, cover_message='', cover_re='',
                  cover_func=None, preserve_formatting=False, printer_name='',
                  update_queue=None, event_queue=None):

        if not self.isSendFaxActive():

            self.send_fax_thread = SOAPFaxSendThread(self, self.service, phone_num_list, fax_file_list,
                                                     cover_message, cover_re, cover_func,
                                                     preserve_formatting,
                                                     printer_name, update_queue,
                                                     event_queue)

            self.send_fax_thread.start()
            return True
        else:
            return False


# **************************************************************************** #
class SOAPFaxSendThread(FaxSendThread):
    def __init__(self, dev, service, phone_num_list, fax_file_list,
                 cover_message='', cover_re='', cover_func=None, preserve_formatting=False,
                 printer_name='', update_queue=None, event_queue=None):

        FaxSendThread.__init__(self, dev, service, phone_num_list, fax_file_list,
             cover_message, cover_re, cover_func, preserve_formatting,
             printer_name, update_queue, event_queue)

        self.job_id = utils.gen_random_uuid()
        log.debug("JobId: %s" % self.job_id)

        if dev.bus == 'net':
            self.http_host = "%s:8295" % self.dev.host
        else:
            self.http_host = 'localhost:8295'

        #self.http_host = 'localhost'


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
                            log.error("HTTP GET failed!")
                            state = STATE_ERROR

                finally:
                    self.dev.close()


            elif state == STATE_PRERENDER: # --------------------------------- Pre-render non-G4 files (40, 0, 0)
                log.debug("%s State: Pre-render non-G4 files" % ("*"*20))
                state = self.pre_render(STATE_COUNT_PAGES)

            elif state == STATE_COUNT_PAGES: # --------------------------------- Get total page count (50, 0, 0)
                log.debug("%s State: Get total page count" % ("*"*20))
                state = self.count_pages(STATE_NEXT_RECIPIENT)

            elif state == STATE_NEXT_RECIPIENT: # --------------------------------- Loop for multiple recipients (60, 0, 0)
                log.debug("%s State: Next recipient" % ("*"*20))
                state = STATE_COVER_PAGE

                try:
                    recipient = next(next_recipient)
                    log.debug("Processing for recipient %s" % recipient['name'])
                    self.write_queue((STATUS_SENDING_TO_RECIPIENT, 0, recipient['name']))
                except StopIteration:
                    state = STATE_SUCCESS
                    log.debug("Last recipient.")
                    continue

                recipient_file_list = self.rendered_file_list[:]


            elif state == STATE_COVER_PAGE: # --------------------------------- Create cover page (70, 0, 0)
                log.debug("%s State: Render cover page" % ("*"*20))
                state = self.cover_page(recipient)


            elif state == STATE_SINGLE_FILE: # --------------------------------- Special case for single file (no merge) (80, 0, 0)
                log.debug("%s State: Handle single file" % ("*"*20))
                state = self.single_file(STATE_SEND_FAX)

            elif state == STATE_MERGE_FILES: # --------------------------------- Merge multiple G4 files (90, 0, 0)
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
                FAX_SEND_STATE_BEGINJOB = 50
                FAX_SEND_STATE_DOWNLOADPAGES = 60
                FAX_SEND_STATE_ENDJOB = 70
                FAX_SEND_STATE_CANCELJOB = 80
                FAX_SEND_STATE_CLOSE_SESSION = 170

                monitor_state = False
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
                        monitor_state = False
                        fax_send_state = FAX_SEND_STATE_CANCELJOB
                        state = STATE_ABORTED

                    elif fax_send_state == FAX_SEND_STATE_ERROR: # -------------- Error (110, 20, 0)
                        log.error("Fax send error.")
                        monitor_state = False
                        fax_send_state = FAX_SEND_STATE_CLOSE_SESSION
                        state = STATE_ERROR

                    elif fax_send_state == FAX_SEND_STATE_BUSY: # -------------- Busy (110, 25, 0)
                        log.error("Fax device busy.")
                        monitor_state = False
                        fax_send_state = FAX_SEND_STATE_CLOSE_SESSION
                        state = STATE_BUSY

                    elif fax_send_state == FAX_SEND_STATE_SUCCESS: # -------------- Success (110, 30, 0)
                        log.debug("Fax send success.")
                        monitor_state = False
                        fax_send_state = FAX_SEND_STATE_CLOSE_SESSION
                        state = STATE_NEXT_RECIPIENT

                    elif fax_send_state == FAX_SEND_STATE_DEVICE_OPEN: # -------------- Device open (110, 40, 0)
                        log.debug("%s State: Open device" % ("*"*20))
                        fax_send_state = FAX_SEND_STATE_BEGINJOB
                        try:
                            self.dev.open()
                        except Error as e:
                            log.error("Unable to open device (%s)." % e.msg)
                            fax_send_state = FAX_SEND_STATE_ERROR
                        else:
                            if self.dev.device_state == DEVICE_STATE_NOT_FOUND:
                                fax_send_state = FAX_SEND_STATE_ERROR

                    elif fax_send_state == FAX_SEND_STATE_BEGINJOB: # -------------- BeginJob (110, 50, 0)
                        log.debug("%s State: BeginJob" % ("*"*20))

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
                                      (magic, version, total_pages, hort_dpi, vert_dpi, page_size,
                                       resolution, encoding))

                        job_id = self.job_id
                        delay = 0
                        faxnum = recipient['fax']
                        speeddial = 0

                        if resolution == RESOLUTION_STD:
                            res = "STANDARD"
                        elif resolution == RESOLUTION_FINE:
                            res = "FINE"
                        elif resolution == RESOLUTION_300DPI:
                            res = "SUPERFINE"

                        soap = utils.cat(
"""<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"><SOAP-ENV:Body><Fax:BeginJob xmlns:Fax="urn:Fax"><ticket xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Fax:Ticket"><jobId xmlns:xsd="http://www.w3.org/2001/XMLSchema" xsi:type="xsd:string">$job_id</jobId><resolution xsi:type="Fax:Resolution">$res</resolution><delay xmlns:xsd="http://www.w3.org/2001/XMLSchema" xsi:type="xsd:positiveInteger">$delay</delay><phoneNumber xmlns:xsd="http://www.w3.org/2001/XMLSchema" xsi:type="xsd:string">$faxnum</phoneNumber><speedDial xmlns:xsd="http://www.w3.org/2001/XMLSchema" xsi:type="xsd:positiveInteger">$speeddial</speedDial></ticket></Fax:BeginJob></SOAP-ENV:Body></SOAP-ENV:Envelope>""")

                        data = self.format_http(soap.encode('utf-8'))

                        log.log_data(data)

                        if log.is_debug():
                            open('beginjob.log', 'wb').write(data)
                        self.dev.openSoapFax()
                        self.dev.writeSoapFax(data)
                        ret = BytesIO()

                        while self.dev.readSoapFax(8192, ret, timeout=5):
                            pass

                        ret = ret.getvalue()

                        if log.is_debug():
                            open('beginjob_ret.log', 'wb').write(ret)
                        log.log_data(ret)
                        self.dev.closeSoapFax()

                        if self.get_error_code(ret.decode('utf-8')) == HTTP_OK:
                            fax_send_state = FAX_SEND_STATE_DOWNLOADPAGES
                        else:
                            fax_send_state = FAX_SEND_STATE_ERROR


                    elif fax_send_state == FAX_SEND_STATE_DOWNLOADPAGES: # -------------- DownloadPages (110, 60, 0)
                        log.debug("%s State: DownloadPages" % ("*"*20))
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

                            if ppr != PIXELS_PER_LINE:
                                log.error("Pixels per line (width) must be %d!" % PIXELS_PER_LINE)

                            page.write(ff.read(bytes_to_read))
                            thumbnail = ff.read(thumbnail_bytes) # thrown away for now (should be 0 read)
                            page.seek(0)

                            try:
                                data = page.read(bytes_to_read)
                            except IOError:
                                log.error("Unable to read fax file.")
                                fax_send_state = FAX_SEND_STATE_ERROR
                                break

                            if data == b'':
                                log.error("No data!")
                                fax_send_state = FAX_SEND_STATE_ERROR
                                break

                            height = rpp
                            job_id = self.job_id

                            soap = utils.cat(
"""<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"><SOAP-ENV:Header><jobId xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xsd:string" SOAP-ENV:mustUnderstand="1">$job_id</jobId></SOAP-ENV:Header><SOAP-ENV:Body><Fax:DownloadPage xmlns:Fax="urn:Fax"><height xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xsd:positiveInteger">$height</height></Fax:DownloadPage></SOAP-ENV:Body></SOAP-ENV:Envelope>""")

                            m = dime.Message()
                            m.add_record(dime.Record(b"cid:id0", b"http://schemas.xmlsoap.org/soap/envelope/",
                                dime.TYPE_T_URI, to_bytes_utf8(soap)))

                            m.add_record(dime.Record(b"", b"image/g4fax", dime.TYPE_T_MIME, data))

                            output = BytesIO()
                            m.generate(output)
                            data = self.format_http(output.getvalue(), content_type="application/dime")
                            log.log_data(data)
                            if log.is_debug():
                                           open('downloadpages%d.log' % p, 'wb').write(data)
                            try:
                                self.dev.writeSoapFax(data)
                            except Error:
                                fax_send_state = FAX_SEND_STATE_ERROR

                            ret = BytesIO()

                            try:
                                while self.dev.readSoapFax(8192, ret, timeout=5):
                                    pass
                            except Error:
                                fax_send_state = FAX_SEND_STATE_ERROR

                            ret = ret.getvalue()

                            if log.is_debug():
                                open('downloadpages%d_ret.log' % p, 'wb').write(ret)

                            log.log_data(ret)
                            self.dev.closeSoapFax()

                            if self.get_error_code(ret.decode('utf-8')) != HTTP_OK:
                                fax_send_state = FAX_SEND_STATE_ERROR
                                break

                            page.truncate(0)
                            page.seek(0)

                        else:
                            fax_send_state = FAX_SEND_STATE_ENDJOB


                    elif fax_send_state == FAX_SEND_STATE_ENDJOB: # -------------- EndJob (110, 70, 0)
                        log.debug("%s State: EndJob" % ("*"*20))

                        job_id = self.job_id

                        soap = utils.cat(
"""<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"><SOAP-ENV:Header><jobId xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xsd:string" SOAP-ENV:mustUnderstand="1">$job_id</jobId></SOAP-ENV:Header><SOAP-ENV:Body><Fax:EndJob xmlns:Fax="urn:Fax"><jobId xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xsd:string">$job_id</jobId></Fax:EndJob></SOAP-ENV:Body></SOAP-ENV:Envelope>""")

                        data = self.format_http(soap.encode('utf-8'))

                        log.log_data(data)

                        if log.is_debug():
                            open('endjob.log', 'wb').write(data)

                        self.dev.writeSoapFax(data)
                        ret = BytesIO()

                        while self.dev.readSoapFax(8192, ret, timeout=5):
                            pass

                        ret = ret.getvalue()

                        if log.is_debug():
                            open('endjob_ret.log', 'wb').write(ret)

                        log.log_data(ret)
                        self.dev.closeSoapFax()

                        if self.get_error_code(ret.decode('utf-8')) == HTTP_OK:
                            fax_send_state = FAX_SEND_STATE_SUCCESS
                        else:
                            fax_send_state = FAX_SEND_STATE_ERROR

                    elif fax_send_state == FAX_SEND_STATE_CANCELJOB: # -------------- CancelJob (110, 80, 0)
                        log.debug("%s State: CancelJob" % ("*"*20))

                        job_id = self.job_id

                        soap = utils.cat(
"""<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"><SOAP-ENV:Header><jobId xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xsd:string" SOAP-ENV:mustUnderstand="1">$job_id</jobId></SOAP-ENV:Header><SOAP-ENV:Body><Fax:CancelJob xmlns:Fax="urn:Fax"><jobId xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xsd:string">$job_id</jobId></Fax:CancelJob></SOAP-ENV:Body></SOAP-ENV:Envelope>""")

                        data = self.format_http(soap.encode('utf-8'))

                        log.log_data(data)

                        if log.is_debug():
                            open('canceljob.log', 'wb').write(data)

                        self.dev.writeSoapFax(data)
                        ret = BytesIO()

                        while self.dev.readSoapFax(8192, ret, timeout=5):
                            pass

                        ret = ret.getvalue()

                        if log.is_debug():
                            open('canceljob_ret.log', 'wb').write(ret)

                        log.log_data(ret)
                        self.dev.closeSoapFax()

                        if self.get_error_code(ret.decode('utf-8')) == HTTP_OK:
                            fax_send_state = FAX_SEND_STATE_CLOSE_SESSION
                        else:
                            fax_send_state = FAX_SEND_STATE_ERROR


                    elif fax_send_state == FAX_SEND_STATE_CLOSE_SESSION: # -------------- Close session (110, 170, 0)
                        log.debug("%s State: Close session" % ("*"*20))
                        log.debug("Closing session...")

                        try:
                            mm.close()
                        except NameError:
                            pass

                        try:
                            ff.close()
                        except NameError:
                            pass

                        time.sleep(1)

                        self.dev.closeSoapFax()
                        self.dev.close()

                        fax_send_state = FAX_SEND_STATE_DONE # Exit inner state machine


            elif state == STATE_CLEANUP: # --------------------------------- Cleanup (120, 0, 0)
                log.debug("%s State: Cleanup" % ("*"*20))

                if self.remove_temp_file:
                    log.debug("Removing merged file: %s" % self.f)
                    try:
                        os.remove(self.f)
                        log.debug("Removed")
                    except OSError:
                        log.debug("Not found")

                state = STATE_DONE # Exit outer state machine


    def get_error_code(self, ret):
        if not ret: return HTTP_ERROR

        match = http_result_pat.match(ret)

        if match is None: return HTTP_OK
        try:
            code = int(match.group(1))
        except (ValueError, TypeError):
            code = HTTP_ERROR

        return code


    def format_http(self, soap, content_type="text/xml; charset=utf-8"):
        host = self.http_host
        soap_len = len(soap)

        return (utils.cat(
"""POST / HTTP/1.1\r
Host: $host\r
User-Agent: hplip/2.0\r
Content-Type: $content_type\r
Content-Length: $soap_len\r
Connection: close\r
SOAPAction: ""\r
\r\n""")).encode('utf-8') + soap




