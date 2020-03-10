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
# Author: Goutam Kodu, Amarnath Chitumalla
#
#
#



# Std Lib
import sys
import os
from subprocess import Popen, PIPE
import grp
import fnmatch
import tempfile
import socket
import struct
import select
import time
import fcntl
import errno
import stat
import string
import glob
import subprocess # TODO: Replace with subprocess (commands is deprecated in Python 3.0)
import io
import re
import getpass
import locale
from .sixext.moves import html_entities

# Local
from .g import *
from .codes import *
from . import utils, tui
from . import logger


# System wide logger
log = logger.Logger('', logger.Logger.LOG_LEVEL_INFO, logger.Logger.LOG_TO_CONSOLE)
log.set_level('info')

def running_as_root():
    return os.geteuid() == 0

def restart_cups():
    if os.path.exists('/etc/init.d/cups'):
        return '/etc/init.d/cups restart'

    elif os.path.exists('/etc/init.d/cupsys'):
        return '/etc/init.d/cupsys restart'

    else:
        return 'killall -HUP cupsd'

def restart(passwordObj):
    ok = False
    shutdown = utils.which('shutdown')
    if shutdown and passwordObj:
        cmd = "%s -r now" % (os.path.join(shutdown, "shutdown"))
        cmd = passwordObj.getAuthCmd() % cmd
        status, output = utils.run(cmd, passwordObj, "Need authentication to restart system")

        ok = (status == 0)
    return ok


def run_open_mdns_port(core, passwordObj, callback=None):
    open_mdns_port_cmd = core.get_distro_ver_data('open_mdns_port')
    log.debug(open_mdns_port_cmd)
    if open_mdns_port_cmd and passwordObj:
        x = 1
        for cmd in open_mdns_port_cmd:
            cmd = passwordObj.getAuthCmd() % cmd
            status, output = utils.run(cmd, passwordObj, "Need authentication to open mdns port [%s]"%cmd)

            if status != 0:
                log.warn("An error occurred running '%s'" % cmd)
                log.warn(output)

            if callback is not None:
                callback(cmd, "Open mDNS/Bonjour step %d" % x)

            x += 1


def run_hp_tools(cmd):
    if cmd is not None:
        hpCommand = utils.which(cmd, True)

        if not hpCommand:
            hpCommand = cmd

        log.debug(hpCommand)
        status, output = utils.run(hpCommand)
        return status == 0
    else:
        log.error("Command not found")
        return False


def run_hp_tools_with_auth(cmd, passwordObj):
    if cmd is not None and passwordObj  is not None :
        hpCommand = utils.which(cmd,True)

        if not hpCommand:   #if it is local command like. ./setup.py
            hpCommand = cmd

        hpCommand = passwordObj.getAuthCmd() % hpCommand

        log.debug(hpCommand)
        status, output = utils.run(hpCommand, passwordObj, "Need authentication to run %s command"%cmd)
        return status == 0
    else:
        log.error("Command not found or password object is not valid")
        return False


# start_service() starts the services
# Input:
#       service_name (string) --> service name to be started.
#       passwordObj     --> root required services, needs to pass base/password object
# Output:
#       ret_val (bool)  --> returns True, if service is started or already running also.
#                       --> returns False, if failed to start service.
def start_service( service_name, passwordObj):
    ret_Val = False
    if not service_name or not passwordObj:
        return ret_Val

    if utils.which('systemctl'):
        cmd_status = passwordObj.getAuthCmd()%("systemctl status %s.service"%service_name)
        log.debug(cmd_status)
        sts,out = utils.run(cmd_status, passwordObj, "Need authentication to get %s service status"%service_name)
        if sts ==0:
            if 'stop' in out or 'inactive' in out:
                cmd_start = passwordObj.getAuthCmd()%("systemctl start %s.service"%service_name)
                log.debug("cmd_start=%s"%cmd_start)
                sts,out = utils.run(cmd_start, passwordObj, "Need authentication to start/restart %s service"%service_name)
                if sts ==0:
                    ret_Val = True
            else:
                ret_Val = True
        else:
            log.error("Fail to start %s service, please start %s service manually."%(service_name,service_name))

    elif utils.which('service'):
        cmd_status = passwordObj.getAuthCmd()%("service %s status"%service_name)
        log.debug(cmd_status)
        sts,out = utils.run(cmd_status, passwordObj, "Need authentication to get %s service status"%service_name)
        if sts ==0:
            if 'stop' in out or 'inactive' in out:
                cmd_start = passwordObj.getAuthCmd()%("service %s start"%service_name)
                log.debug("cmd_start=%s"%cmd_start)
                sts,out = utils.run(cmd_start, passwordObj, "Need authentication to start/restart %s service"%service_name)
                if sts ==0:
                    ret_Val = True
            elif 'unrecognized service' in out:
                log.error("Failed to Start since %s is unrecognized service"%service_name)
            else:
                ret_Val = True
        else:
            log.error("Fail to start %s service, please start %s service manually."%(service_name,service_name))

    elif os.path.exists('/etc/init.d/%s'%service_name):
        cmd_status = passwordObj.getAuthCmd()%('/etc/init.d/%s status'%service_name)
        log.debug(cmd_status)
        sts,out = utils.run(cmd_status, passwordObj, "Need authentication to get %s service status"%service_name)
        if sts ==0:
            if 'stop' in out or 'inactive' in out:
                cmd_start = passwordObj.getAuthCmd()%('/etc/init.d/%s start'%service_name)
                log.debug("cmd_start=%s"%cmd_start)
                sts,out = utils.run(cmd_start, passwordObj, "Need authentication to start/restart %s service"%service_name)
                if sts ==0:
                    ret_Val = True
            else:
                ret_Val = True
        else:
            log.error("Fail to start %s service, please start %s service manually."%(service_name,service_name))
    else:
        if service_name == 'cups':
            cmd = 'lpstat -r'
            sts,out = utils.run(cmd, passwordObj, "Need authentication to get %s service status"%service_name)
            if sts ==0 and 'is running' in out:
                ret_Val = True
            else:
                log.error("service command not found, please start cups service manually.")
        else:
            log.error("Fail to start %s service, please start %s service manually."%(service_name,service_name))

    return ret_Val


def run_systray():
    path = utils.which('hp-systray')
    if path:
        path = os.path.join(path, 'hp-systray')
    else:
        path = os.path.join(prop.home_dir, 'systray.py')

    if not os.path.exists(path):
        log.warn("Unable to start hp-systray")

    log.debug("Running hp-systray: %s --force-startup" % path)
    os.spawnlp(os.P_NOWAIT, path, 'hp-systray', '--force-startup', "--ignore-update-firsttime")
    log.debug("Waiting for hp-systray to start...")
    time.sleep(1)

def disable_SmartInstall():
    path = utils.which('hp-SIDisable',True)
    if path:
        param = '-'
        sicmd = "%s %s" % (path,param)
        if run_hp_tools(sicmd):
            log.debug("Smart Install is disabled\n")
        else:
            log.error("Smart Install could not be disabled\n")
    else:
        try:
            from . import pkit
            plugin = PLUGIN_REQUIRED
            plugin_reason = PLUGIN_REASON_NONE
            ok, sudo_ok = pkit.run_plugin_command(plugin == PLUGIN_REQUIRED, plugin_reason)
            if not ok or not sudo_ok:
                log.error("Failed to install plug-in.")
        except ImportError:
            log.warn("Import error\n")


def close_running_hp_processes():
    # check systray is running?  
    status,output = utils.Is_Process_Running('hp-systray')
    if status is True:
        ok,choice = tui.enter_choice("\nSome HPLIP applications are running. Press 'y' to close applications or press 'n' to quit upgrade(y=yes*, n=no):",['y','n'],'y')
        if not ok or choice =='n':
            log.info("Manually close HPLIP applications and run hp-upgrade again.")
            return False

        try:
        # dBus
            from dbus import SystemBus, lowlevel
        except ImportError:
            log.error("Unable to load DBus.")
            pass
        else:
            try:
                args = ['', '', EVENT_SYSTEMTRAY_EXIT, prop.username, 0, '', '']
                msg = lowlevel.SignalMessage('/', 'com.hplip.StatusService', 'Event')
                msg.append(signature='ssisiss', *args)
                log.debug("Sending close message to hp-systray ...")
                SystemBus().send_message(msg)
                time.sleep(0.5)
            except:
                log.error("Failed to send DBus message to hp-systray/hp-toolbox.")
                pass

    toolbox_status,output = utils.Is_Process_Running('hp-toolbox')

    if toolbox_status is True:
        log.error("Failed to close either HP-Toolbox/HP-Systray. Manually close and run hp-upgrade again.")
        return False

    return True
