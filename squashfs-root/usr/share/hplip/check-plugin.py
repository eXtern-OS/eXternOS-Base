#!/usr/bin/python3
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
# Author: Suma Byrappa, Amarnath Chitumalla
#
#
from __future__ import print_function
__version__ = '1.1'
__title__ = 'AutoConfig Utility for Plug-in Installation'
__mod__ = 'hp-check-plugin'
__doc__ = "Auto config utility for HPLIP supported multifunction Devices for installing proprietary plug-ins."


# Std Lib
import sys
import os
import os.path
import getopt
import signal
import operator
import time

# Local
from base.g import *
from base import utils, device, tui, module, pkit, services
from installer import pluginhandler


# Temp values for testing; May not be needed
username = ""
device_uri = ""
printer_name = ""
LOG_FILE = "%s/hplip_ac.log"%prop.user_dir
DBUS_SERVICE='com.hplip.StatusService'

##### METHODS #####

# Send dbus event to hpssd on dbus system bus
def send_message(device_uri, printer_name, event_code, username, job_id, title, pipe_name=''):
    log.debug("send_message() entered")
    args = [device_uri, printer_name, event_code, username, job_id, title, pipe_name]
    msg = lowlevel.SignalMessage('/', DBUS_SERVICE, 'Event')
    msg.append(signature='ssisiss', *args)

    SystemBus().send_message(msg)
    log.debug("send_message() returning")

# Plugin installation
def install_Plugin(systray_running_status, run_directly=False):
    if run_directly:
        if not utils.canEnterGUIMode4():
            log.error("%s requires GUI support . Is Qt4 installed?" % __mod__)
            sys.exit(1)

        try:
            from PyQt4.QtGui import QApplication, QMessageBox
            from ui4.plugindiagnose import PluginDiagnose
            from installer import core_install
        except ImportError:
            log.error("Unable to load Qt4 support. Is it installed?")
            sys.exit(1)

        app = QApplication(sys.argv)
        plugin = PLUGIN_REQUIRED
        plugin_reason = PLUGIN_REASON_NONE
        ok, sudo_ok = pkit.run_plugin_command(plugin == PLUGIN_REQUIRED, plugin_reason)
        if not ok or not sudo_ok:
            log.error("Failed to install plug-in.")
    elif systray_running_status:
        send_message( device_uri,  "", EVENT_AUTO_CONFIGURE, username, 0, "AutoConfig")
        log.debug("Event EVENT_AUTO_CONFIGURE sent to hp-systray to invoke hp-plugin")
    else:
        log.error("Run hp-systray manually and re-plugin printer")
        #TBD: needs to run hp-plugin in silent mode. or needs to show error UI to user.


#Installs/Uploads the firmware to device once plugin installation is completed.
def install_firmware(pluginObj,Plugin_Installation_Completed, USB_param):
    #timeout check for plugin installation
    sleep_timeout = 6000    # 10 mins time out
    while Plugin_Installation_Completed is False and sleep_timeout != 0:
        time.sleep(0.3) #0.3 sec delay
        sleep_timeout = sleep_timeout -3

        ps_plugin,output = utils.Is_Process_Running('hp-plugin')
        ps_diagnose_plugin,output = utils.Is_Process_Running('hp-diagnose_plugin')

        if ps_plugin is False and ps_diagnose_plugin is False:
            Plugin_Installation_Completed = True
            if pluginObj.getStatus() == PLUGIN_INSTALLED:
                break
            else:
                log.error("Failed to download firmware required files. manually run hp-plugin command in terminal fisrt")
                sys.exit(1)

    execmd="hp-firmware"
    options=""
    if USB_param is not None:
        options += " -y3 %s"%(USB_param)
    if log_level is 'debug':
        options += " -g"

    cmd= execmd + options
    log.info("Starting Firmware installation.")
    log.debug("Running command : %s " %cmd)
    Status, out=utils.run(cmd)

#    if Status == 0:
#        log.info("Installed firmware ")
#    else:
#        log.error("Failed to install firmware = %s" %Status)


#Usage details
USAGE = [(__doc__, "", "name", True),
         ("Usage: %s [OPTIONS] [USB bus:device]" % __mod__, "", "summary", True),
         utils.USAGE_OPTIONS,
         ("Install Plug-in through HP System Tray:", "-m (Default)", "option", False),
         ("Install Plug-in through hp-plugin:", "-p", "option", False),
         ("Download firmware into the device:", "-f", "option", False),
         utils.USAGE_HELP,
         utils.USAGE_LOGGING1, utils.USAGE_LOGGING2, utils.USAGE_LOGGING3,
         utils.USAGE_EXAMPLES,
          ("Install plugin:", "$%s 001:002"%(__mod__), "example", False),
          ("Install plugin and firmware:", "$%s -f 001:002"%(__mod__), "example", False),
         utils.USAGE_NOTES,
         ("-m and -p options can't be used together. ","","note",False),
        ]


def usage(typ='text'):
    if typ == 'text':
        utils.log_title(__title__, __version__)

    utils.format_text(USAGE, typ, __title__, __mod__, __version__)
    sys.exit(0)

##### MAIN #####


try:
    import dbus
    from dbus import SystemBus, lowlevel
except ImportError:
        log.error("hp-check-plugin Tool requires dBus and python-dbus")
        sys.exit(1)
try:
    mod = module.Module(__mod__, __title__, __version__, __doc__, USAGE,
    (INTERACTIVE_MODE, GUI_MODE), (UI_TOOLKIT_QT3, UI_TOOLKIT_QT4, UI_TOOLKIT_QT5), run_as_root_ok=True, quiet=True)
    opts, device_uri, printer_name, mode, ui_toolkit, loc = \
         mod.parseStdOpts('l:hHuUmMfFpPgG',['gui','help', 'help-rest', 'help-man', 'help-desc','logging='],handle_device_printer=False)

except getopt.GetoptError as e:
        log.error(e.msg)
        usage()
        sys.exit(1)

if os.getenv("HPLIP_DEBUG"):
        log.set_level('debug')

log_level = 'info'
Systray_Msg_Enabled = False
Plugin_option_Enabled = False
Firmware_Option_Enabled = False
GUI_Mode = True
Is_Plugin_Already_Installed = False

for o, a in opts:
    if o in ('-h','-H', '--help'):
        usage()

    elif o == '--help-rest':
        usage('rest')

    elif o == '--help-man':
        usage('man')

    elif o in ('-u', '-U','--gui'):
        # currenlty only GUI mode is supported. hence not reading this option
        GUI_Mode = True

#    elif o in ('-i', '-I', '--interactive'):
#        #this is future use
#        GUI_Mode = False

    elif o == '--help-desc':
        print(__doc__, end=' ')
        sys.exit(0)

    elif o in ('-l', '--logging'):
        log_level = a.lower().strip()

    elif o in('-g', '-G'):
        log_level = 'debug'

    elif o in ('-m', '-M'):
        Systray_Msg_Enabled = True

    elif o in ('-p', '-P'):
        Plugin_option_Enabled = True

    elif o in ('-F','-f'):
        Firmware_Option_Enabled = True

if not log.set_level (log_level):
    usage()

try:
    param = mod.args[0]
except IndexError:
    param = ''

LOG_FILE = os.path.normpath(LOG_FILE)
log.info(log.bold("Saving output in log file: %s" % LOG_FILE))
if os.path.exists(LOG_FILE):
    try:
        os.remove(LOG_FILE)
    except OSError:
        pass

log.set_logfile(LOG_FILE)
log.set_where(log.LOG_TO_CONSOLE_AND_FILE)

log.debug(" hp-check-plugin started")

if Plugin_option_Enabled and Systray_Msg_Enabled:
    log.error("Both -m and -p options can't be used together.")
    usage()
    sys.exit(1)

log.debug("param=%s" % param)
if len(param) < 1:
    usage()
    sys.exit()

if param:
    device_uri, sane_uri, fax_uri = device.makeURI(param)
if not device_uri:
    log.error("This is not a valid device")
    sys.exit(0)

log.debug("\nSetting up device: %s\n" % device_uri)
#Query model and checks Plugin information.
mq = device.queryModelByURI(device_uri)
if not mq or mq.get('support-type', SUPPORT_TYPE_NONE) == SUPPORT_TYPE_NONE:
    log.error("Unsupported printer model.")
    sys.exit(1)

plugin = mq.get('plugin', PLUGIN_NONE)
if plugin == PLUGIN_NONE:
    log.debug("This is not a plugin device.")
    sys.exit()

if not Plugin_option_Enabled:
    Systray_Msg_Enabled = True

# checking whether HP-systray is running or not. Invokes, if systray is not running
Systray_Is_Running=False
status,output = utils.Is_Process_Running('hp-systray')
if status is False:
    if os.getuid() == 0:
        log.error(" hp-systray must be running.\n Run \'hp-systray &\' in a terminal. ")
    else:
        log.info("Starting hp-systray service")
        services.run_systray()
        status,output = utils.Is_Process_Running('hp-systray')

if status == True:
    Systray_Is_Running=True
    log.debug("hp-systray service is running\n")

pluginObj = pluginhandler.PluginHandle()
plugin_sts = pluginObj.getStatus()
if plugin_sts == pluginhandler.PLUGIN_INSTALLED:
    log.info("Device Plugin is already installed")
    Is_Plugin_Already_Installed = True

elif plugin_sts == pluginhandler.PLUGIN_NOT_INSTALLED :
    log.info("HP Device Plug-in is not found")
else:
    log.info("HP Device Plug-in version mismatch or some files are corrupted")

if Systray_Msg_Enabled:
    if not Is_Plugin_Already_Installed:
        install_Plugin( Systray_Is_Running)

elif Plugin_option_Enabled:
    if not Is_Plugin_Already_Installed:
        install_Plugin (Systray_Is_Running, True)        # needs to run hp-plugin without usig systray

if Firmware_Option_Enabled:
    if Is_Plugin_Already_Installed is False:
        Plugin_Installation_Completed = False
    else:
        Plugin_Installation_Completed = True

    install_firmware(pluginObj, Plugin_Installation_Completed, param)

log.info()
log.info("Done.")
