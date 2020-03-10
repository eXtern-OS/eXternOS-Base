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
# Author: Don Welch
#

# Local
from base.g import *
from prnt import cups
from base import device, codes
from .soapfax import SOAPFaxDevice
from .pmlfax import PMLFaxDevice
from .marvellfax import MarvellFaxDevice

def FaxDevice(device_uri=None, printer_name=None,
              callback=None, 
              fax_type=FAX_TYPE_NONE,
              disable_dbus=False):
                 
    if fax_type == FAX_TYPE_NONE:
        if device_uri is None and printer_name is not None:
            printers = cups.getPrinters()
    
            for p in printers:
                if p.name.lower() == printer_name.lower():
                    device_uri = p.device_uri
                    break
            else:
                raise Error(ERROR_DEVICE_NOT_FOUND)
                
        if device_uri is not None:
            mq = device.queryModelByURI(device_uri)
            fax_type = mq['fax-type']
            
    log.debug("fax-type=%d" % fax_type)
                    
    if fax_type in (FAX_TYPE_BLACK_SEND_EARLY_OPEN, FAX_TYPE_BLACK_SEND_LATE_OPEN):
        return PMLFaxDevice(device_uri, printer_name, callback, fax_type, disable_dbus)

    elif fax_type == FAX_TYPE_SOAP:
        return SOAPFaxDevice(device_uri, printer_name, callback, fax_type, disable_dbus)

    elif fax_type == FAX_TYPE_LEDMSOAP:
        from .ledmsoapfax import LEDMSOAPFaxDevice
        return LEDMSOAPFaxDevice(device_uri, printer_name, callback, fax_type, disable_dbus)

    elif fax_type == FAX_TYPE_MARVELL:
        return MarvellFaxDevice(device_uri, printer_name, callback, fax_type, disable_dbus)
        
    elif fax_type == FAX_TYPE_LEDM:
        from .ledmfax import LEDMFaxDevice
        return LEDMFaxDevice(device_uri, printer_name, callback, fax_type, disable_dbus)
        

    else:
        raise Error(ERROR_DEVICE_DOES_NOT_SUPPORT_OPERATION)
