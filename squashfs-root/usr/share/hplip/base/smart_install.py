# -*- coding: utf-8 -*-
#
# (c) Copyright @2015 HP Development Company, L.P.
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
import os.path
import re
import os

# Local
from .g import *
from . import utils, tui
from base import password, validation
from base.codes import *
from base.strings import *


##### Global variables ###
HPLIP_INFO_SITE ="http://hplip.sourceforge.net/hplip_web.conf"



########### methods ###########


def get_usb_details(vid_pid):
    result_cnt = 0
    param_result = {"idVendor":'', "iProduct":'',  "bNumInterfaces":'', "bInterfaceClass":''}
    param_search = {"idVendor": re.compile(r"""\s*idVendor\s*([0-9a-fx]{1,})\s*.*""", re.I),
                    "iProduct" : re.compile(r"""\s*iProduct\s*[0-9a-fx]{1,}\s*(.*)""", re.I),
                    "bNumInterfaces" : re.compile(r"""\s*bNumInterfaces\s*(\d{1,})\s*.*""", re.I),
                    "bInterfaceClass" : re.compile(r"""\s*bInterfaceClass\s*(\d{1,})\s*.*""", re.I)  }

    lsusb_cmd = utils.which('lsusb',True)
    if lsusb_cmd:
        sts,out = utils.run("%s -d %s -v"%(lsusb_cmd, vid_pid), passwordObj = None, pswd_msg='', log_output=False)
        if sts == 0:
            for l in out.splitlines():
                for s in param_search:
                    if s in l:
                        result_cnt += 1
                        if param_search[s].match(l):
                            param_result[s] = param_search[s].match(l).group(1)
                        else:
                            log.warn("TBD... Shouldn't have entered into this condition. key[%s]"%s)

                        if "idVendor" ==  s and param_result[s].lower() != "0x03f0":  # if non-HP vendor, ignoring usb parsing.
                            return False, {}
                        elif "iProduct" == s and param_result[s] == "":
                            return False, {}

                        break

                if result_cnt == len(param_result):  # To avoid extra parsing...
                     break

    return True, param_result


# get_smartinstall_enabled_devices function checks CD-ROM enabled devices.
#Input:
#       None
# Output:
#       smartinstall_dev_list (list) --> Returns CD-ROM enabled device list.
#
def get_smartinstall_enabled_devices():
    smartinstall_dev_list=[]
    lsusb_cmd = utils.which('lsusb',True)

    if not lsusb_cmd:
        log.error("Failed to find the lsusb command")
        return smartinstall_dev_list

    try:
        sts,out = utils.run(lsusb_cmd)
        if sts !=  0:
            log.error("Failed to run the %s command"%lsusb_cmd)
            return smartinstall_dev_list

        for d in out.splitlines():
            usb_dev_pat = re.compile(r""".*([0-9a-f]{4}:([0-9a-f]{4}))\s*""", re.I)

            if usb_dev_pat.match(d):
                vid_pid = usb_dev_pat.match(d).group(1)

                bsts, usb_params = get_usb_details(vid_pid)
                if not bsts:
                    continue    # These are not HP-devices

                log.debug("Product['%s'],Interfaces[%s],InterfaceClass[%s]"%(usb_params["iProduct"], usb_params["bNumInterfaces"],usb_params["bInterfaceClass"]))
                if usb_params["bNumInterfaces"] == '1' and usb_params["bInterfaceClass"] == '8' and "laserjet" in usb_params["iProduct"].lower():    #'8' is MASS STORAGE
                    smartinstall_dev_list.append(usb_params["iProduct"])

            else:
                log.warn("Failed to find vid and pid for USB device[%s]"%d)

    except KeyError:
        pass

    if smartinstall_dev_list:
        smartinstall_dev_list = utils.uniqueList(smartinstall_dev_list)

    return smartinstall_dev_list


def check_SmartInstall():
    devices = get_smartinstall_enabled_devices()
    if devices:
        return True
    else:
        return False


def get_SmartInstall_tool_info():
    url, file_name = "", ""
    if not utils.check_network_connection():
        log.error("Internet connection not found.")
    else:
        sts, HPLIP_file = utils.download_from_network(HPLIP_INFO_SITE)
        if sts == 0:
            hplip_si_conf = ConfigBase(HPLIP_file)
            url = hplip_si_conf.get("SMART_INSTALL","reference","")
            if url:
                file_name = 'SmartInstallDisable-Tool.run'
            else:
                log.error("Failed to download %s."%HPLIP_INFO_SITE)
        else:
            log.error("Failed to download %s."%HPLIP_INFO_SITE)

    return url, file_name

def validate(mode, smart_install_run, smart_install_asc, req_checksum=''):

    #Validate Checksum
    calc_checksum = utils.get_checksum(open(smart_install_run, 'r').read())
    log.debug("File checksum=%s" % calc_checksum)

    if req_checksum and req_checksum != calc_checksum:
        return ERROR_FILE_CHECKSUM, queryString(ERROR_CHECKSUM_ERROR, 0, plugin_file)

    #Validate Digital Signature
    gpg_obj = validation.GPG_Verification()
    digsig_sts, error_str = gpg_obj.validate(smart_install_run, smart_install_asc)

    return digsig_sts, smart_install_run, smart_install_asc, error_str



def download(mode, passwordObj):
    if not utils.check_network_connection():
        log.error("Internet connection not found.")
        return ERROR_NO_NETWORK, "" , "" ,queryString(ERROR_NO_NETWORK)

    else:
        sts, HPLIP_file = utils.download_from_network(HPLIP_INFO_SITE)
        if sts == 0:
            hplip_si_conf = ConfigBase(HPLIP_file)
            source = hplip_si_conf.get("SMART_INSTALL","url","")
            if not source:
                log.error("Failed to download %s."%HPLIP_INFO_SITE)
                return ERROR_FAILED_TO_DOWNLOAD_FILE, "" , "", queryString(ERROR_FAILED_TO_DOWNLOAD_FILE, 0, HPLIP_INFO_SITE)

        sts, smart_install_run = utils.download_from_network(source)
        if sts:
            log.error("Failed to download %s."%source)
            return ERROR_FAILED_TO_DOWNLOAD_FILE, "" , "", queryString(ERROR_FAILED_TO_DOWNLOAD_FILE, 0, source)

        sts, smart_install_asc = utils.download_from_network(source+'.asc')
        if sts:
            log.error("Failed to download %s."%(source+'.asc'))
            return ERROR_FAILED_TO_DOWNLOAD_FILE, "" , "", queryString(ERROR_FAILED_TO_DOWNLOAD_FILE, 0, source + ".asc")

        digsig_sts, smart_install_run, smart_install_asc, error_str = validate(mode, smart_install_run, smart_install_asc)

        return digsig_sts, smart_install_run, smart_install_asc, error_str


def disable(mode, ui_toolkit='qt4', dialog=None, app=None, passwordObj = None):

    dev_list = get_smartinstall_enabled_devices()
    if not dev_list:
        log.debug("No Smart Install Device found")
        return ERROR_NO_SI_DEVICE, queryString(ERROR_NO_SI_DEVICE)

    return_val = ERROR_FAILED_TO_DISABLE_SI
    return_error_str = queryString(ERROR_FAILED_TO_DISABLE_SI)
    url, file_name = get_SmartInstall_tool_info()
    printer_names  = utils.list_to_string(dev_list)

    try:
        if mode == GUI_MODE:
            if ui_toolkit == 'qt3':
                try:
                    from ui.setupform import FailureMessageUI
                except ImportError:
                    log.error("Smart Install is enabled in %s device(s).\nAuto Smart Install disable is not supported in QT3.\nPlease refer link \'%s\' to disable manually"%(printer_names,url))
                else:
                    FailureMessageUI("Smart Install is enabled in %s device(s).\n\nAuto Smart Install disable is not supported in QT3.\nPlease refer link \'%s\' to disable manually"%(printer_names,url))

            else: #qt4
                if not utils.canEnterGUIMode4():
                    log.error("%s requires GUI support . Is Qt4 installed?" % __mod__)
                    return ERROR_FAILED_TO_DISABLE_SI, queryString(ERROR_FAILED_TO_DISABLE_SI)

                if dialog and app:  # If QT app already opened, re-using same object
                    dialog.init(printer_names, "", QUEUES_SMART_INSTALL_ENABLED)
                else:   # If QT object is not created, creating QT app
                    try:
                        from ui4.queuesconf import QueuesDiagnose
                    except ImportError:
                        log.error("Unable to load Qt4 support. Is it installed?")
                    else:       #  app = QApplication(sys.argv)   # caller needs to inoke this, if already QApplication object is not created.
                        dialog = QueuesDiagnose(None, printer_names ,"",QUEUES_SMART_INSTALL_ENABLED)

                log.debug("Starting GUI loop...")
                dialog.exec_()

                if check_SmartInstall():
                    dialog.showMessage("Failed to disable smart install.\nPlease refer link \'%s\' for more information" %url)
                else:
                    dialog.showSuccessMessage("Smart install disabled successfully.")


        #Interaction mode
        else: 
            log.error("Smart Install is enabled in %s device(s). "%printer_names)
            response, value = tui.enter_choice("Do you want to download and disable smart install?(y=yes*, n=no):",['y', 'n'], 'y')

            if not response or value != 'y':   #User exit
                return_val = ERROR_FAILED_TO_DISABLE_SI
                return_error_str = queryString(ERROR_FAILED_TO_DISABLE_SI)

            else:
                sts, smart_install_run, smart_install_asc, error_str = download(mode, passwordObj)

                disable_si = False
                return_val = sts

                if sts == ERROR_SUCCESS:
                    disable_si = True

                elif sts in (ERROR_UNABLE_TO_RECV_KEYS, ERROR_DIGITAL_SIGN_NOT_FOUND):
                    response, value = tui.enter_yes_no("Digital Sign verification failed, Do you want to continue?")
                    if not response or not value:
                        sys.exit(0)
                    else:   # Continue without validation succes.
                        disable_si = True
                else:
                    return_error_str = queryString(sts)

                if disable_si: 
                    sts, out = utils.run("sh %s"%smart_install_run)

                    # Once smart install disabler installation completed, cross verifying to ensure no smart install devices found
                    if sts or check_SmartInstall():
                        log.error("Failed to disable smart install .")
                        log.error("Please refer link \'%s\' to disable manually"%url)
                        return_val = ERROR_FAILED_TO_DISABLE_SI
                        return_error_str = queryString(ERROR_FAILED_TO_DISABLE_SI)
                    else:
                        log.info("Smart install disabled successfully.")
                        return_val = ERROR_SUCCESS
                        return_error_str = ""

    except KeyboardInterrupt:
        log.error("User exit")
        sys.exit(0)

    return return_val ,return_error_str

