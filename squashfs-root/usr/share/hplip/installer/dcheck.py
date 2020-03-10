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
import os
import os.path
import re
import sys
from subprocess import Popen, PIPE
import codecs

# Local
from base.g import *
from base import utils, services
from base.sixext import to_bytes_utf8

ver1_pat = re.compile("""(\d+\.\d+\.\d+)""", re.IGNORECASE)
ver_pat = re.compile("""(\d+.\d+)""", re.IGNORECASE)
PID = 0
CMDLINE = 1


ld_output = ''
#ps_output = ''
mod_output = ''



def update_ld_output():
    # For library checks
    global ld_output
    status, ld_output = utils.run('%s -p' % os.path.join(utils.which('ldconfig'), 'ldconfig'), log_output=False)

    if status != 0:
        log.debug("ldconfig failed.")

def check_tool(cmd, min_ver=0.0):
    log.debug("Checking: %s (min ver=%f)" % (cmd, min_ver))
    status, output = utils.run(cmd)

    if status != 0:
        log.debug("Not found!")
        return False
    else:
        if min_ver:
            try:
                line = output.splitlines()[0]
            except IndexError:
                line = ''
            log.debug(line)
            match_obj = ver_pat.search(line)
            try:
                ver = match_obj.group(1)
            except AttributeError:
                ver = ''

            try:
                v_f = float(ver)
            except ValueError:
                return False
            else:
                log.debug("Ver=%f Min ver=%f" % (v_f, min_ver))

                if v_f < min_ver:
                    log.debug("Found, but newer version required.")

                return v_f >= min_ver
        else:
            log.debug("Found.")
            return True


def check_lib(lib, min_ver=0):
    log.debug("Checking for library '%s'..." % lib)

    if ld_output.find(lib) >= 0:
        log.debug("Found.")

        #if min_ver:
        #    pass
        #else:
        return True
    else:
        log.debug("Not found.")
        return False

def check_file(f, dir="/usr/include"):
    log.debug("Searching for file '%s' in '%s'..." % (f, dir))
    for w in utils.walkFiles(dir, recurse=True, abs_paths=True, return_folders=False, pattern=f):
        log.debug("File found at '%s'" % w)
        return True

    log.debug("File not found.")
    return False


def locate_files(f, dir):
    log.debug("Searching for file(s) '%s' in '%s'..." % (f, dir))
    found = []
    for w in utils.walkFiles(dir, recurse=True, abs_paths=True, return_folders=False, pattern=f):
        log.debug(w)
        found.append(w)

    if found:
        log.debug("Found files: %s" % found)
    else:
        log.debug("No files not found.")

    return found

def locate_file_contains(f, dir, s):
    """
        Find a list of files located in a directory
        that contain a specified sub-string.
    """
    log.debug("Searching for file(s) '%s' in '%s' that contain '%s'..." % (f, dir, s))
    found = []
    for w in utils.walkFiles(dir, recurse=True, abs_paths=True, return_folders=False, pattern=f):

        if check_file_contains(w, s):
            log.debug(w)
            found.append(w)

    if found:
        log.debug("Found files: %s" % found)
    else:
        log.debug("No files not found.")

    return found

def check_file_contains(f, s):
    log.debug("Checking file '%s' for contents '%s'..." % (f, s))
    try:
        if os.path.exists(f):
            s = to_bytes_utf8(s)
            for a in open(f, 'rb'):
                update_spinner()

                if s in a:
                    log.debug("'%s' found in file '%s'." % (s.replace(b'\n', b''), f))
                    return True

        log.debug("Contents not found.")
        return False

    finally:
        cleanup_spinner()


def check_ps(process_list):
    if process_list is not None:
        log.debug("Searching for '%s' in running processes..." % process_list)
    try:
        for p in process_list:
            update_spinner()
            status,process = utils.Is_Process_Running(p)
            if status is True:
                for p in process:
                    log.debug("Found: %s (%s)" % (process[p], p))
                return True

        log.debug("Not found")
        return False
    finally:
        cleanup_spinner()

def get_ps_pid(process_name_list):
    processes_list = {}

    if process_name_list is not None:
        log.debug("Searching for '%s' in running processes..." % process_name_list)

        try:
            for p in process_name_list:
                update_spinner()
                status,processes = utils.Is_Process_Running(p)
                if status is True:
                    log.debug("Found: %d processes" % len(processes))
                    for pid in processes:
                        processes_list[pid] =processes[pid]
                else:
                    log.debug("Not found")
        finally:
            cleanup_spinner()

    return processes_list

def check_lsmod(module):
    global mod_output

    if not mod_output:
        lsmod = utils.which('lsmod')
        status, mod_output = utils.run(os.path.join(lsmod, 'lsmod'), log_output=False)

    return mod_output.find(module) >= 0

def check_version(inst_ver_str, min_ver_str='0.0'):
    log.debug("Checking: installed ver=%s  min ver=%s" % (inst_ver_str, min_ver_str))
    min_ver = 0
    if min_ver_str != '-':
        match_obj=ver_pat.search(min_ver_str)
        try:
            ver = match_obj.group(1)
        except AttributeError:
            ver = ''
        try:
            min_ver = float(ver)
        except ValueError:
            min_ver = 0

    inst_ver = 0
    if inst_ver_str != '-':
        match_obj=ver_pat.search(inst_ver_str)
        try:
            ver = match_obj.group(1)
        except AttributeError:
            ver = ''
        try:
            inst_ver = float(ver)
        except ValueError:
            inst_ver = 0


    if inst_ver < min_ver:
        log.debug("Found, but newer version required.")
        return False
    else:
        log.debug("Found.")
        return True


def get_version(cmd,def_ver='-'):
    log.debug("Checking: %s" % (cmd))
    status, output = utils.run(cmd)

    if status != 0:
        log.debug("Not found!")
        return def_ver
    else:
        try:
            line = output.splitlines()[0]
        except IndexError:
            line = ''

        log.debug(line)
        match_obj = ver1_pat.search(line)
        try:
            ver = match_obj.group(1)
        except AttributeError:
            match_obj = ver_pat.search(line)
            try:
                ver = match_obj.group(1)
            except AttributeError:
                return def_ver
            else:
                return ver
        else:
            return ver

def get_python_dbus_ver():
    try:
        import dbus
        dbus_version ="-"
        try:
            dbus_version = dbus.__version__
        except AttributeError:
            try:
                dbus_version = '.'.join([str(x) for x in dbus.version])
            except AttributeError:
                dbus_version = '-'
    except ImportError:
        dbus_version = '-'
    return dbus_version

def get_pyQt4_version():
    log.debug("Checking PyQt 4.x version...")
    ver ='-'
    # PyQt 4
    try:
        import PyQt4
    except ImportError:
        ver='-'
    else:
        from PyQt4 import QtCore
        ver = QtCore.PYQT_VERSION_STR
    return ver


def get_pyQt5_version():
    log.debug("Checking PyQt 5.x version...")
    ver ='-'
    # PyQt 5
    try:
        import PyQt5
    except ImportError:
        ver='-'
    else:
        from PyQt5 import QtCore
        ver = QtCore.PYQT_VERSION_STR
    return ver

def get_reportlab_version():
    try:
        log.debug("Trying to import 'reportlab'...")
        import reportlab
        ver = str(reportlab.Version)
    except ImportError:
        return '-'
    else:
        return ver

def  get_pyQt_version():
    log.debug("Checking PyQt 3.x version...")
    # PyQt 3
    try:
        import qt
    except ImportError:
        return '-'
    else:
        #check version of PyQt
        try:
            pyqtVersion = qt.PYQT_VERSION_STR
        except AttributeError:
            pyqtVersion = qt.PYQT_VERSION

        while pyqtVersion.count('.') < 2:
            pyqtVersion += '.0'

        return pyqtVersion

def get_xsane_version():
    installed_ver='-'
    try:
        p1 = Popen(["xsane", "--version","2",">","/dev/null"], stdout=PIPE)
    except:
        output =None
    else:
        output=p1.communicate()[0].decode('utf-8')
        

    if output:
        xsane_ver_pat =re.compile('''xsane-(\d{1,}\.\d{1,}).*''')
        xsane_ver_info = output.splitlines()[0]
        if xsane_ver_pat.search(xsane_ver_info):
            installed_ver = xsane_ver_pat.search(xsane_ver_info).group(1)
    return installed_ver

def get_pil_version():
    try:
        from PIL import Image
    except ImportError:
        return '-'
    else:
         return Image.VERSION

def get_libpthread_version():
    try:
        import sys, ctypes, ctypes.util
    except ImportError:
        return '-'
    else:
#        LIBC = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
        LIBC = ctypes.CDLL(ctypes.util.find_library('c'),ctypes.DEFAULT_MODE,None, True)
        LIBC.gnu_get_libc_version.restype = ctypes.c_char_p
        return LIBC.gnu_get_libc_version()

def get_python_xml_version():
    try:
        import xml.parsers.expat
    except ImportError:
        return '-'
    else:
         return '.'.join([str(x) for x in xml.parsers.expat.version_info])

def get_HPLIP_version():
    return prop.version


def get_libusb_version():
    
    if sys_conf.get('configure', 'libusb01-build', 'no') == "yes":
        return get_version('libusb-config --version')
    else:
        return '1.0'
