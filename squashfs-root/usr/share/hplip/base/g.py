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
# NOTE: This module is safe for 'from g import *'
#

# Std Lib
import sys
import os
import os.path
from .sixext import PY3
from .sixext.moves import configparser
import locale
import pwd
import stat
import re

# Local
from .codes import *
from . import logger
from . import os_utils
from .sixext import to_unicode
if PY3:
    QString = type("")
 
    def cmp(a, b):
        return (a > b) - (a < b)

# System wide logger
log = logger.Logger('', logger.Logger.LOG_LEVEL_INFO, logger.Logger.LOG_TO_CONSOLE)
log.set_level('info')


MINIMUM_PYQT_MAJOR_VER = 3
MINIMUM_PYQT_MINOR_VER = 14
MINIMUM_QT_MAJOR_VER = 3
MINIMUM_QT_MINOR_VER = 0


def to_bool(s, default=False):
    if isinstance(s, str) and s:
        if s[0].lower() in ['1', 't', 'y']:
            return True
        elif s[0].lower() in ['0', 'f', 'n']:
            return False
    elif isinstance(s, bool):
        return s

    return default


# System wide properties
class Properties(dict):

    def __getattr__(self, attr):
        if attr in list(self.keys()):
            return self.__getitem__(attr)
        else:
            return ""

    def __setattr__(self, attr, val):
        self.__setitem__(attr, val)

prop = Properties()



class ConfigBase(object):
    def __init__(self, filename):
        self.filename = filename
        self.conf = configparser.ConfigParser()
        self.read()


    def get(self, section, key, default=to_unicode('')):
        try:
            return self.conf.get(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError):
            return default


    def set(self, section, key, value):
        if not self.conf.has_section(section):
            self.conf.add_section(section)

        self.conf.set(section, key, value)
        self.write()


    def sections(self):
        return self.conf.sections()


    def has_section(self, section):
        return self.conf.has_section(section)


    def options(self, section):
        return self.conf.options(section)

    keys = options

    def read(self):
        if self.filename is not None:
            filename = self.filename
            if filename.startswith("/root/"):
                # Don't try opening a file in root's home directory.
                log.error("attempted to read from '%s'" % self.filename)
                return
            try:
                fp = open(self.filename, "r")
                try:
                    self.conf.readfp(fp)
                except configparser.MissingSectionHeaderError:
                    print("")
                    log.error("Found No Section in %s. Please set the http proxy for root and try again." % self.filename)
                except (configparser.DuplicateOptionError):
                    log.warn("Found Duplicate Entery in %s" % self.filename)
                    self.CheckDuplicateEntries()
                finally:
                    fp.close()
            except (OSError, IOError, configparser.MissingSectionHeaderError):
                log.debug("Unable to open file %s for reading." % self.filename)

    def write(self):
        if self.filename is not None:
            filename = self.filename
            if filename.startswith("/root/") or filename.startswith("/etc/"):
                # Don't try writing a file in root's home directory or
                # the system-wide config file.
                # See bug #479178.
                log.error("attempted to write to '%s'" % self.filename)
                return

            try:
                fp = open(self.filename, "w")
                self.conf.write(fp)
                fp.close()
            except (OSError, IOError):
                log.debug("Unable to open file %s for writing." % self.filename)
    
    def CheckDuplicateEntries(self):
        try:
            f = open(self.filename,'r')
            data = f.read()
            f.close()
        except IOError:
            data =""

        final_data =''
        for a in data.splitlines():
           if not a or a not in final_data:
                final_data = final_data +'\n' +a

        import tempfile
        fd, self.filename = tempfile.mkstemp()
        f = open(self.filename,'w')
        f.write(final_data)
        f.close()

        self.read()
        os.unlink(self.filename)
 
        
class SysConfig(ConfigBase):
    def __init__(self):
        ConfigBase.__init__(self, '/etc/hp/hplip.conf')


class State(ConfigBase):
    def __init__(self):
        if not os.path.exists('/var/lib/hp/') and os.geteuid() == 0:
            os.makedirs('/var/lib/hp/')
            cmd = 'chmod 755 /var/lib/hp/'
            os_utils.execute(cmd)
        ConfigBase.__init__(self, '/var/lib/hp/hplip.state')


class UserConfig(ConfigBase):
    def __init__(self):

        sts, prop.user_dir = os_utils.getHPLIPDir()

        if not os.geteuid() == 0:
            prop.user_config_file = os.path.join(prop.user_dir, 'hplip.conf')

            if not os.path.exists(prop.user_config_file):
                try:
                    open(prop.user_config_file, 'w').close()
                    s = os.stat(os.path.dirname(prop.user_config_file))
                    os.chown(prop.user_config_file, s[stat.ST_UID], s[stat.ST_GID])
                except IOError:
                    pass

            ConfigBase.__init__(self, prop.user_config_file)

        else:
            # If running as root, conf file is None
            prop.user_config_file = None
            ConfigBase.__init__(self, None)


    def workingDirectory(self):
        t = self.get('last_used', 'working_dir', os.path.expanduser("~"))
        try:
            t = t.decode('utf-8')
        except UnicodeError:
            log.error("Invalid unicode: %s"  % t)
        log.debug("working directory: %s" % t)
        return t


    def setWorkingDirectory(self, t):
        self.set('last_used', 'working_dir', t.encode('utf-8'))
        log.debug("working directory: %s" % t.encode('utf-8'))



os.umask(0o037)

# System Config File: Directories and build settings. Not altered after installation.
sys_conf = SysConfig()

# System State File: System-wide runtime settings
sys_state = State()

# Per-user Settings File: (Note: For Qt4 code, limit the use of this to non-GUI apps. only)
user_conf = UserConfig()


# Language settings
try:
    prop.locale, prop.encoding = locale.getdefaultlocale()
except ValueError:
    prop.locale = 'en_US'
    prop.encoding = 'UTF8'

prop.version = sys_conf.get('hplip', 'version', '0.0.0') # e.g., 3.9.2b.10
_p, _x = re.compile(r'(\d\w*)', re.I), []
for _y in prop.version.split('.')[:3]:
    _z = _p.match(_y)
    if _z is not None:
        _x.append(_z.group(1))

prop.installed_version = '.'.join(_x) # e.g., '3.9.2'
try:
    prop.installed_version_int = int(''.join(['%02x' % int(_y) for _y in _x]), 16) # e.g., 0x030902 -> 198914
except ValueError:
    prop.installed_version_int = 0

prop.home_dir = sys_conf.get('dirs', 'home', os.path.realpath(os.path.normpath(os.getcwd())))
prop.username = pwd.getpwuid(os.getuid())[0]
pdb = pwd.getpwnam(prop.username)
prop.userhome = pdb[5]

prop.history_size = 50

prop.data_dir = os.path.join(prop.home_dir, 'data')
prop.image_dir = os.path.join(prop.home_dir, 'data', 'images')
prop.xml_dir = os.path.join(prop.home_dir, 'data', 'xml')
prop.models_dir = os.path.join(prop.home_dir, 'data', 'models')
prop.localization_dir = os.path.join(prop.home_dir, 'data', 'localization')

prop.max_message_len = 8192
prop.max_message_read = 65536
prop.read_timeout = 90

prop.ppd_search_path = '/usr/share;/usr/local/share;/usr/lib;/usr/local/lib;/usr/libexec;/opt;/usr/lib64'
prop.ppd_search_pattern = 'HP-*.ppd.*'
prop.ppd_download_url = 'http://www.linuxprinting.org/ppd-o-matic.cgi'
prop.ppd_file_suffix = '-hpijs.ppd'

# Build and install configurations
prop.gui_build = to_bool(sys_conf.get('configure', 'gui-build', '0'))
prop.net_build = to_bool(sys_conf.get('configure', 'network-build', '0'))
prop.par_build = to_bool(sys_conf.get('configure', 'pp-build', '0'))
prop.usb_build = True
prop.scan_build = to_bool(sys_conf.get('configure', 'scanner-build', '0'))
prop.fax_build = to_bool(sys_conf.get('configure', 'fax-build', '0'))
prop.doc_build = to_bool(sys_conf.get('configure', 'doc-build', '0'))
prop.foomatic_xml_install = to_bool(sys_conf.get('configure', 'foomatic-xml-install', '0'))
prop.foomatic_ppd_install = to_bool(sys_conf.get('configure', 'foomatic-ppd-install', '0'))
prop.hpcups_build = to_bool(sys_conf.get('configure', 'hpcups-install', '0'))
prop.hpijs_build = to_bool(sys_conf.get('configure', 'hpijs-install', '0'))

# Spinner, ala Gentoo Portage
spinner = "\|/-\|/-"
spinpos = 0
enable_spinner = True

def change_spinner_state(enable =True):
    global enable_spinner
    enable_spinner = enable

def update_spinner():
    global spinner, spinpos, enable_spinner
    if enable_spinner and not log.is_debug() and sys.stdout.isatty():
        sys.stdout.write("\b" + spinner[spinpos])
        spinpos=(spinpos + 1) % 8
        sys.stdout.flush()

def cleanup_spinner():
    global enable_spinner
    if enable_spinner and not log.is_debug() and sys.stdout.isatty():
        sys.stdout.write("\b \b")
        sys.stdout.flush()

# Convert string to int and return a list.
def xint(ver):
    try:
        l = [int(x) for x in ver.split('.')]
    except:
        pass
    return l

# In case of import failure of extension modules, check whether its a mixed python environment issue.   
def check_extension_module_env(ext_mod):

    flag = 0
    ext_mod_so = ext_mod + '.so'

    python_ver = xint((sys.version).split(' ')[0])              #find the current python version ; xint() to convert string to int, returns a list
    if python_ver[0] == 3 :
        python_ver = 3
    else :
        python_ver = 2

    for dirpath, dirname, filenames in os.walk('/usr/lib/'):    #find the .so path
        if ext_mod_so in filenames:
            ext_path = dirpath
            flag = 1

    if flag == 0:
        log.error('%s not present in the system. Please re-install HPLIP.' %ext_mod)
        sys.exit(1)

    m = re.search('python(\d(\.\d){0,2})', ext_path)            #get the python version where the .so file is found
    ext_ver = xint(m.group(1))

    if ext_ver[0] == 3:
        ver = 3
    else:
        ver = 2

    if python_ver != ver :                                      #compare the python version and the version where .so files are present
        log.error("%s Extension module is missing from Python's path." %ext_mod)
        log.info("To fix this issue, please refer to this 'http://hplipopensource.com/node/372'")
        sys.exit(1)

# Internal/messaging errors

ERROR_STRINGS = {
                ERROR_SUCCESS : 'No error',
                ERROR_UNKNOWN_ERROR : 'Unknown error',
                ERROR_DEVICE_NOT_FOUND : 'Device not found',
                ERROR_INVALID_DEVICE_ID : 'Unknown/invalid device-id field',
                ERROR_INVALID_DEVICE_URI : 'Unknown/invalid device-uri field',
                ERROR_DATA_LENGTH_EXCEEDS_MAX : 'Data length exceeds maximum',
                ERROR_DEVICE_IO_ERROR : 'Device I/O error',
                ERROR_NO_PROBED_DEVICES_FOUND : 'No probed devices found',
                ERROR_DEVICE_BUSY : 'Device busy',
                ERROR_DEVICE_STATUS_NOT_AVAILABLE : 'DeviceStatus not available',
                ERROR_INVALID_SERVICE_NAME : 'Invalid service name',
                ERROR_ERROR_INVALID_CHANNEL_ID : 'Invalid channel-id (service name)',
                ERROR_CHANNEL_BUSY : 'Channel busy',
                ERROR_DEVICE_DOES_NOT_SUPPORT_OPERATION : 'Device does not support operation',
                ERROR_DEVICEOPEN_FAILED : 'Device open failed',
                ERROR_INVALID_DEVNODE : 'Invalid device node',
                ERROR_INVALID_HOSTNAME : "Invalid hostname ip address",
                ERROR_INVALID_PORT_NUMBER : "Invalid JetDirect port number",
                ERROR_NO_CUPS_QUEUE_FOUND_FOR_DEVICE : "No CUPS queue found for device.",
                ERROR_DATFILE_ERROR: "DAT file error",
                ERROR_INVALID_TIMEOUT: "Invalid timeout",
                ERROR_IO_TIMEOUT: "I/O timeout",
                ERROR_FAX_INCOMPATIBLE_OPTIONS: "Incompatible fax options",
                ERROR_FAX_INVALID_FAX_FILE: "Invalid fax file",
                ERROR_FAX_FILE_NOT_FOUND: "Fax file not found",
                ERROR_INTERNAL : 'Unknown internal error',
               }


class Error(Exception):
    def __init__(self, opt=ERROR_INTERNAL):
        self.opt = opt
        self.msg = ERROR_STRINGS.get(opt, ERROR_STRINGS[ERROR_INTERNAL])
        log.debug("Exception: %d (%s)" % (opt, self.msg))
        Exception.__init__(self, self.msg, opt)


# Make sure True and False are avail. in pre-2.2 versions
#try:
#    True
#except NameError:
#    True = (1==1)
#    False = not True

# as new translations are completed, add them here
supported_locales =  { 'en_US': ('us', 'en', 'en_us', 'american', 'america', 'usa', 'english'),}
# Localization support was disabled in 3.9.2
                       #'zh_CN': ('zh', 'cn', 'zh_cn' , 'china', 'chinese', 'prc'),
                       #'de_DE': ('de', 'de_de', 'german', 'deutsche'),
                       #'fr_FR': ('fr', 'fr_fr', 'france', 'french', 'français'),
                       #'it_IT': ('it', 'it_it', 'italy', 'italian', 'italiano'),
                       #'ru_RU': ('ru', 'ru_ru', 'russian'),
                       #'pt_BR': ('pt', 'br', 'pt_br', 'brazil', 'brazilian', 'portuguese', 'brasil', 'portuguesa'),
                       #'es_MX': ('es', 'mx', 'es_mx', 'mexico', 'spain', 'spanish', 'espanol', 'español'),
                     #}


