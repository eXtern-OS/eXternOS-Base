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
from base.sixext import BytesIO
import re

# Local
from base.g import *
from base.codes import *
from base import device, utils, codes, dime
from .fax import *
from .ledmfax import *
from .soapfax import SOAPFaxSendThread
from .soapfax import SOAPFaxDevice


# **************************************************************************** #
class LEDMSOAPFaxDevice(SOAPFaxDevice):


    def __init__(self, device_uri=None, printer_name=None,
                 callback=None,
                 fax_type=FAX_TYPE_NONE,
                 disable_dbus=False):

        SOAPFaxDevice.__init__(self, device_uri,
                           printer_name,
                           callback, fax_type,
                           disable_dbus)

    #LEDM Specific functions
    def put(self, url, post):
        data = """PUT %s HTTP/1.1\r
Connection: Keep-alive\r
User-agent: hplip/2.0\r
Host: %s\r
Content-length: %d\r
\r
%s""" % (url, self.http_host, len(post), post)
        log.log_data(data)
        self.writeEWS_LEDM(data.encode('utf-8'))
        response = BytesIO()

        while self.readEWS_LEDM(4096, response, timeout=5):
            pass

        response = response.getvalue()
        log.log_data(response.decode('utf-8'))
        self.closeEWS_LEDM()        
        
        match = http_result_pat.match(response)
        if match is None: return HTTP_OK
        try:
            code = int(match.group(1))
        except (ValueError, TypeError):
            code = HTTP_ERROR

        return code == HTTP_OK


    def setPhoneNum(self, num):
        xml = setPhoneNumXML %(num)
        log.debug("SetPhoneNum:xml Value:%s" %xml)
        return self.put("/DevMgmt/FaxConfigDyn.xml", xml)


    def getPhoneNum(self):
        return self.readAttributeFromXml_EWS("/DevMgmt/FaxConfigDyn.xml",'faxcfgdyn:faxconfigdyn-faxcfgdyn:systemsettings-dd:phonenumber')

    phone_num = property(getPhoneNum, setPhoneNum)


    def setStationName(self, name):
        try:
            xml = setStationNameXML %name
        except(UnicodeEncodeError, UnicodeDecodeError):
            log.error("Unicode Error")

        return self.put("/DevMgmt/FaxConfigDyn.xml", xml)


    def getStationName(self):
        return self.readAttributeFromXml_EWS("/DevMgmt/FaxConfigDyn.xml",'faxcfgdyn:faxconfigdyn-faxcfgdyn:systemsettings-dd:companyname')

    station_name = property(getStationName, setStationName) 


    def setDateAndTime(self):
        t = time.localtime()
        date_buf = "%4d-%02d-%02dT%02d:%02d:%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
        xml = setDateTimeXML %(date_buf)
        log.debug("setDateTimeXML Value:%s" %xml)
        
        if self.put("/DevMgmt/ProductConfigDyn.xml", xml):
            return True
        else:
            log.debug ("Failed to set date and time. Set date and time using front panel.")
            return False
