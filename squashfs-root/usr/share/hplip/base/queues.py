# -*- coding: utf-8 -*-
#
# (c) Copyright 2011-2015 HP Development Company, L.P.
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
# Author: Amarnath Chitumalla
#

# Std Lib
import sys
import os
import re

# Local
from .g import *
from . import utils, tui, password, os_utils, smart_install
from prnt import cups
from installer import core_install
from .sixext import to_string_utf8

try:
    from importlib import import_module
except ImportError as e:
    log.debug(e)
    from .utils import dyn_import_mod as import_module


# ppd type
HPCUPS = 1
HPIJS = 2
HPPS = 3
HPOTHER = 4

DEVICE_URI_PATTERN = re.compile(r"""(.*):/(.*?)/(\S*?)\?(?:serial=(\S*)|device=(\S*)|ip=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[^&]*)|zc=(\S+))(?:&port=(\d))?""", re.I)
NICKNAME_PATTERN = re.compile(b'''\*NickName:\s*\"(.*)"''', re.MULTILINE)
NET_PATTERN = re.compile(r"""(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})""")
NET_ZC_PATTERN = re.compile(r'''zc=(.*)''',re.IGNORECASE)
NET_OTHER_PATTERN = re.compile(r'''(.*)://(.*)''',re.IGNORECASE)
USB_PATTERN = re.compile(r'''serial=(.*)''',re.IGNORECASE)
LPSTAT_PATTERN = re.compile(r"""(\S*): (.*)""", re.IGNORECASE)
#BACK_END_PATTERN = re.compile(r'''(.*):(.*)''',re.IGNORECASE)



##### Global variables ###
mapofDevices={}
Error_Found = False
####### Device class ########
class DetectedDevice:
    def __init__(self, Printer_Name,Device_URI,Device_Type, ppdType, PPDFileError = False, IsEnabled=True ):
        self.PrinterName =Printer_Name
        self.DeviceURI = Device_URI
        self.DeviceType = Device_Type
        self.PPDFileType = ppdType
        self.PPDFileError = PPDFileError
        self.IsEnabled = IsEnabled




##### METHODS #####

#Add Printer info to dictionary
def addToDeviceList(Key, printer_name, device_uri,back_end, ppd_fileType,PPDFileError, Is_Print_Q_Enabled):
    if ppd_fileType != None:
        device1 =DetectedDevice(printer_name, device_uri,back_end, ppd_fileType,PPDFileError, Is_Print_Q_Enabled)
        if Key in mapofDevices:
            mapofDevices[Key].append(device1)
        else:
            deviceList=[device1]
            mapofDevices[Key]=deviceList
    else:
        log.warn("%s is not HP Device." %(printer_name))

#Validate all the Queues
def parseQueues(mode):
    is_hpcups_installed = to_bool(sys_conf.get('configure', 'hpcups-install', '0'))
    is_hpijs_installed = to_bool(sys_conf.get('configure', 'hpijs-install', '0'))
    st, output = utils.run('lpstat -v')
    status = True

    cups_printers = []
    if output.find("No destinations added") != -1 or output.find("lpstat:") != -1:
        log.info("No Queue added")
    else:
        for p in output.splitlines():
            try:
                match = LPSTAT_PATTERN.search(p)
                printer_name = match.group(1)
                device_uri = match.group(2)
                cups_printers.append((printer_name, device_uri))
            except AttributeError:
                pass

    log.debug(cups_printers)
    log.debug("HPCups installation=%d  HPIJS installation =%d" %(is_hpcups_installed, is_hpijs_installed))
    if cups_printers:
        for p in cups_printers:
            printer_name, device_uri = p

            if device_uri.startswith("cups-pdf:/"):
                continue
            if device_uri.startswith("ipp:/"):
                continue

            log.debug(log.bold(printer_name))
            log.debug(log.bold('-'*len(printer_name)))

            try:
                back_end, is_hp, bus, model, serial, dev_file, host, zc, port = parseDeviceURI(device_uri)
            except Error:
                back_end, is_hp, bus, model, serial, dev_file, host, zc, port = '', False, '', '', '', '', '', '', 1
                if 'HP' in device_uri:
                    is_hp = True

            log.debug("Device URI: %s" % device_uri)
            ppd_file = os.path.join('/etc/cups/ppd', printer_name + '.ppd')
            ppd_fileType = None
            PPDFileError = False
            if not os.path.exists(ppd_file):
                log.error("PPD %s file not found" % ppd_file)
                addToDeviceList(HPOTHER,printer_name, device_uri,back_end, ppd_fileType, PPDFileError, True)
            else:
                log.debug("PPD: %s" % ppd_file)
            try:
                fileptr = open(ppd_file, 'rb').read()
            except IOError:
                log.warn("Fail to read ppd=%s file"%ppd_file)
                if os.access(ppd_file,os.R_OK):
                    log.debug("File %s has read permissions" %ppd_file)
                else:
                    log.warn("Insufficient permission to access file %s" %ppd_file)
                    status = False
                    return mapofDevices,status
                desc=''
            else:
                try:
                    desc = to_string_utf8( NICKNAME_PATTERN.search(fileptr).group(1) )
                except AttributeError:
                    desc = ''

            log.debug("PPD Description: %s" % desc)
            cmd= 'lpstat -p%s' % printer_name
            st, output = utils.run(cmd)
            log.debug("Printer status: %s" % output.replace("\n", ""))

            #### checking for USb devices ####
            if USB_PATTERN.search(device_uri):
                Key =USB_PATTERN.search(device_uri).group(1)
            #### checking for network devices ####
            elif NET_PATTERN.search(device_uri):
                Key = NET_PATTERN.search(device_uri).group(1)
            elif NET_ZC_PATTERN.search(device_uri):
                Key = NET_ZC_PATTERN.search(device_uri).group(1)
            elif NET_OTHER_PATTERN.search(device_uri):
                part_1 = NET_OTHER_PATTERN.search(device_uri).group(1)
                part_2 = NET_OTHER_PATTERN.search(device_uri).group(2)
                if 'HP' in part_2:
                    Key = part_2
                else:
                    log.info("unknown protocol device_uri=%s" %device_uri)
                    Key=None
            else:
                log.info("unknown protocol device_uri=%s" %device_uri)
                Key=None

            if Key is not None:
                Is_Print_Q_Enabled= True
                if output.find('Paused') !=  -1:
                    Is_Print_Q_Enabled= False
                Key=Key+"_"+back_end
                log.debug("Key'%s': deviceType '%s' is_hp '%s' bus '%s' model '%s' serial '%s' dev_file '%s' host '%s' zc '%s' port '%s' Enabled'%d'"\
                                           %( Key,back_end, is_hp, bus, model, serial, dev_file, host, zc, port,Is_Print_Q_Enabled))

                PPDFileError = False
                if back_end == 'hpfax' and not 'HP Fax' in desc:
                    log.warn("Incorrect PPD file for fax queue '%s'. Fax queue must use 'HP-Fax-hplip.ppd'." % printer_name)
                    PPDFileError = True
                elif back_end == 'hp' and 'HP Fax' in desc:
                    log.warn("Incorrect PPD file for print queue '%s'. Print queue must not use 'HP-Fax-hplip.ppd'." % printer_name)
                    PPDFileError = True
                elif back_end not in ('hp', 'hpfax'):
                    log.warn("Device %s is not HPLIP installed. Device must use the hp: or hpfax: to function in HPLIP."% printer_name)

                ppd_fileType = None
                if 'hpcups' in desc:
                    ppd_fileType = HPCUPS
                    if not is_hpcups_installed:
                        PPDFileError = True
                elif 'hpijs' in desc:
                    ppd_fileType = HPIJS
                    if not is_hpijs_installed:
                        PPDFileError = True
                elif 'Postscript' in desc:
                    ppd_fileType =HPPS
                elif is_hp:
                    ppd_fileType =HPOTHER
                    PPDFileError = True

                addToDeviceList(Key, printer_name, device_uri,back_end, ppd_fileType,PPDFileError, Is_Print_Q_Enabled)
    log.info("")
    return mapofDevices,status


# Validate and remove Queue
def reconfigure_Queue(que, mode, dialog= None,app=None):
    global Error_Found
    Error_msg =None
    if mode == INTERACTIVE_MODE:
        if 'hp' in que.DeviceType or 'hpfax' in que.DeviceType:
            if que.PPDFileError ==  False:
                log.debug("'%s' is configured correctly." %(que.PrinterName))
            else:
                Error_msg = "PPD file for '%s' is not correct. Need to choose correct PPD file." %(que.PrinterName)
        else:
            Error_msg ="'%s' is not configured using HPLIP. Need to remove and re-cofigure using hp-setup." %(que.PrinterName)


        if Error_msg != None:
            Error_Found = True
            log.error(Error_msg)
            response, value = tui.enter_yes_no("Do you want to remove and re-configure?")
            if response == False:
                log.debug("User Exit")
                sys.exit(1)
            elif value == True:
                status, status_str = cups.cups_operation(cups.delPrinter, INTERACTIVE_MODE, '', None, que.PrinterName)

                if status != cups.IPP_OK:
                    log.error("Failed to remove '%s' queue.\nRemove using hp-toolbox."%que.PrinterName)
                else:
                    log.info("' %s' removed successfully.\nRe-configuring this printer by hp-setup..."%que.PrinterName)
                    if utils.which('hp-setup'):
                        cmd = 'hp-setup -i'
                        os_utils.execute(cmd)

        elif que.IsEnabled == False:
            Error_Found = True
            responce, value =tui.enter_yes_no("'%s Queue is paused. Do you want to enable queue?"%(que.PrinterName))
            if responce == False:
                log.debug("User Exit")
                sys.exit(1)
            elif value == True:
                cups.enablePrinter(que.PrinterName)
                log.info("'%s' is enabled successfully"%que.PrinterName)
            else:
                log.info("Manually enable '%s'."%que.PrinterName)
    else:
        if 'hp' in que.DeviceType or 'hpfax' in que.DeviceType:
            if que.PPDFileError ==  False:
                log.debug("'%s' is configured correctly." %(que.PrinterName))
            else:
                log.error("PPD file for '%s' is not correct. Need to choose correct PPD file." %(que.PrinterName))
                Error_msg = QUEUES_INCORRECT_PPD
        else:
            log.error("'%s' is not configured using HPLIP. Need to remove and re-cofigure using hp-setup." %(que.PrinterName))
            Error_msg =QUEUES_CONFIG_ERROR

        if Error_msg == None and que.IsEnabled == False:
            Error_msg = QUEUES_PAUSED

        if Error_msg and dialog and app:
            Error_Found = True
            dialog.init(que.PrinterName, que.DeviceURI, Error_msg)
            dialog.show()
            log.debug("Starting GUI loop...")
            app.exec_()


# This parse the given Device URI. and provides the details.
def parseDeviceURI(device_uri):
    m = DEVICE_URI_PATTERN.match(device_uri)
    if m is None:
        raise Error(ERROR_INVALID_DEVICE_URI)

    back_end = m.group(1).lower() or ''
    is_hp = (back_end in ('hp', 'hpfax', 'hpaio'))
    bus = m.group(2).lower() or ''

    if bus not in ('usb', 'net', 'bt', 'fw', 'par'):
        raise Error(ERROR_INVALID_DEVICE_URI)

    model =m.group(3) or ''
    serial = m.group(4) or ''
    dev_file = m.group(5) or ''
    host = m.group(6) or ''
    zc = ''
    if not host:
        zc = host = m.group(7) or ''
    port = m.group(8) or 1

    if bus == 'net':
        try:
            port = int(port)
        except (ValueError, TypeError):
            port = 1

        if port == 0:
            port = 1

#    log.warning("++++: back_end '%s' is_hp '%s' bus '%s' model '%s' serial '%s' dev_file '%s' host '%s' zc '%s' port '%s' " %
#       ( back_end, is_hp, bus, model, serial, dev_file, host, zc, port))

    return back_end, is_hp, bus, model, serial, dev_file, host, zc, port


def main_function(passwordObj = None, mode = GUI_MODE, ui_toolkit= UI_TOOLKIT_QT4, quiet_mode = False, DEVICE_URI=None):
    global Error_Found
    try:
        from . import device, pml
        # This can fail due to hpmudext not being present
    except ImportError:
        log.error("Device library is not avail.")
        sys.exit(1)

    if mode == INTERACTIVE_MODE:
        try:
            from . import password
        except ImportError:
            log.warn("Failed to import password object")
        else:
            cups.setPasswordCallback(password.showPasswordPrompt)

        mapofDevices,status = parseQueues(mode)
        if status:
            if list(mapofDevices.items()) == 0:
                log.debug("No queues found.")

            for key,val in list(mapofDevices.items()):
                if len(val) >1:
                    if not quiet_mode:
                        Error_Found = True
                        log.warn("%d queues of same device %s is configured.\nRemove unwanted queues."%(len(val),val[0].PrinterName))

                    for que in val:
                        reconfigure_Queue(que, mode)
                else:
                    log.debug("")
                    log.debug("Single print queue is configured for '%s'. " %val[0].PrinterName)
                    reconfigure_Queue(val[0], mode)

            SI_sts, error_str = smart_install.disable(mode, '', None, None, passwordObj)
            if SI_sts != ERROR_NO_SI_DEVICE:
                Error_Found = True

            if Error_Found is False:
                if not quiet_mode:
                    if len(mapofDevices) == 0:
                        log.warn("No Queue(s) configured.")
                    else:
                        log.info("Queue(s) configured correctly using HPLIP.")
        else:
            log.warn("Could not complete Queue(s) configuration check")

        cups.releaseCupsInstance()

    elif mode == GUI_MODE:
        # Only Qt4 is supported.
        if ui_toolkit == 'qt3':
            log.error("This is not supported in Qt3, requires GUI support (try running with --qt4). Also, try using interactive (-i) mode.")
            sys.exit(1)

        QApplication, ui_package = utils.import_dialog(ui_toolkit)
        ui = import_module(ui_package + ".queuesconf")
        setupdialog = import_module(ui_package + ".setupdialog")

        app = QApplication(sys.argv)
        dialog = ui.QueuesDiagnose(None, "","",QUEUES_MSG_SENDING,passwordObj)

        cups.setPasswordCallback(setupdialog.showPasswordUI)
        mapofDevices,status = parseQueues(mode)
        if status:
            if list(mapofDevices.items()) == 0:
                log.debug("No queues found.")

            for key,val in list(mapofDevices.items()):
                if len(val) >1:
                    log.warn('%d queues of same device %s is configured.  Remove unwanted queues.' %(len(val),val[0].PrinterName))
                    if not quiet_mode:
                        Error_Found = True
                        dialog.showMessage("%d queues of same device %s is configured.\nRemove unwanted queues."%(len(val),val[0].PrinterName))
                    for que in val:
                        reconfigure_Queue(que, mode, dialog,app)

                else:
                    log.debug("")
                    log.debug("Single print queue is configured for '%s'. " %val[0].PrinterName)
                    reconfigure_Queue(val[0], mode, dialog, app)

            SI_sts, error_str = smart_install.disable(mode, ui_toolkit, dialog, app, passwordObj)
            if SI_sts != ERROR_NO_SI_DEVICE:
                Error_Found = True

            if Error_Found is False:
                if not quiet_mode:
                    if len(mapofDevices) == 0:
                        msg= "No Queue(s) configured."
                    else:
                        msg= "Queue(s) configured correctly using HPLIP."
                    dialog.showSuccessMessage(msg)
        else:
            log.warn("Could not complete Queue(s) configuration check")

        cups.releaseCupsInstance()
