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
# Author: Don Welch, Naga Samrat Chowdary Narla,

# Local
from .g import *
from . import utils
from .sixext import to_unicode
# StdLib
import os.path
import re

try:
    import datetime
    datetime_avail = True
except ImportError:
    datetime_avail = False
    datetime = None


pat_prod_num = re.compile("""(\d+)""", re.I)

TYPE_UNKNOWN = 0
TYPE_STRING = 1
TYPE_STR = 1
TYPE_LIST = 2
TYPE_BOOL = 3
TYPE_INT = 4
TYPE_HEX = 5
TYPE_BITFIELD = 6
TYPE_URI = TYPE_STR # (7) not used (yet)
TYPE_DATE = 8  # format: mm/dd/yyyy


TECH_CLASSES = [
    "Undefined", # This will show an error (and its the default)
    "Unsupported", # This is for unsupported models, and it will not show an error
    "Postscript",
    "DJGenericVIP",
    #"PSB9100", not used on HPLIP
    "LJMono",
    "LJColor",
    "LJFastRaster",
    "LJJetReady",
    "DJ350",
    #"DJ400", not used on HPLIP
    "DJ540",
    "DJ600",
    "DJ6xx",
    "DJ6xxPhoto",
    "DJ630",
    #"DJ660", not used in HPLIP
    "DJ8xx",
    "DJ8x5",
    "DJ850",
    "DJ890",
    "DJ9xx",
    "DJ9xxVIP",
    "DJ3600",
    "DJ3320",
    "DJ4100",
    "AP2xxx",
    "AP21xx",
    "AP2560",
    "PSP100",
    "PSP470",
    "LJZjsMono",
    "LJZjsColor",
    "LJm1005",
    "QuickConnect",
    "DJ55xx",
    "OJProKx50",
    'LJP1XXX',
    #'DJD2600', not used. Reassigned all these to ViperPlusTrim and ViperMinusTrim Class
    "Stabler",
    "ViperPlusVIP",
    "ViperMinusVIP",
    "ViperPlusTrim",
    "ViperMinusTrim",
    "Corbett",
    "Python",
    "OJ7000",
    "Pyramid",
    "Pyramid15",
    "Python10",
    "Mimas",
    "Mimas15",
    "Mimas17",
    "StingrayOJ",
    "Copperhead",
    "CopperheadXLP",
    "Copperhead12",
    "CopperheadIPH",
    "CopperheadIPH15",
    "PyramidRefresh15",
    "CopperheadIPH17",
    "Ampere",
    "Python11",
    "Saipan",
    "PyramidPlus",
    "Hbpl1",
    "Kapan",
    "MimasTDR",
    "Saipan15B",
    "Gemstone",
    "SPDOfficejetProAsize",
	"CLE",
     "CLE17",
    "SPDOfficejetProBsize",
    "PyramidRefresh17"
]

TECH_CLASSES.sort()

TECH_CLASS_PDLS = {
    #"Undefined"    : '?',
    "Postscript"   : 'ps',
    "DJGenericVIP" : 'pcl3',
    #"PSB9100"      : 'pcl3',
    "LJMono"       : 'pcl3',
    "LJColor"      : 'pcl3',
    "LJFastRaster" : 'pclxl',
    "LJJetReady"   : 'pclxl',
    "DJ350"        : 'pcl3',
    #"DJ400"        : 'pcl3',
    "DJ540"        : 'pcl3',
    "DJ600"        : 'pcl3',
    "DJ6xx"        : 'pcl3',
    "DJ6xxPhoto"   : 'pcl3',
    "DJ630"        : 'pcl3',
    #"DJ660"        : 'pcl3',
    "DJ8xx"        : 'pcl3',
    "DJ8x5"        : 'pcl3',
    "DJ850"        : 'pcl3',
    "DJ890"        : 'pcl3',
    "DJ9xx"        : 'pcl3',
    "DJ9xxVIP"     : 'pcl3',
    "DJ3600"       : 'lidil',
    "DJ3320"       : 'lidil',
    "DJ4100"       : 'lidil',
    "AP2xxx"       : 'pcl3',
    "AP21xx"       : 'pcl3',
    "AP2560"       : 'pcl3',
    "PSP100"       : 'pcl3',
    "PSP470"       : 'pcl3',
    "LJZjsMono"    : 'zjs',
    "LJZjsColor"   : 'zjs',
    "LJm1005"      : 'zxs',
    "QuickConnect" : 'jpeg',
    "DJ55xx"       : 'pcl3',
    "OJProKx50"    : 'pcl3',
    'LJP1XXX'      : 'zxs',
    "Stabler"      : 'pcl3',
    "ViperPlusVIP" : 'pcl3',
    "ViperMinusVIP": 'pcl3',
    "ViperPlusTrim" : 'lidil',
    "ViperMinusTrim": 'lidil',
    "Corbett"       : 'pcl3',
    "Python"        : 'pcl3',
    "OJ7000"        : 'pcl3',
    "Python10"      : 'pcl3',
    "Mimas"      : 'pcl3',
    "Mimas15"      : 'pcl3',
    "Mimas17"      : 'pcl3',
    "StingrayOJ"   : 'pcl3',
    "Pyramid15"   : 'pcl3',
    "Copperhead"   : 'pcl3',
    "CopperheadXLP"   : 'pcl3',
    "Copperhead12"   : 'pcl3',
    "CopperheadIPH"   : 'pcl3',
    "CopperheadIPH15"   : 'pcl3',
    "PyramidRefresh15": 'pcl3',
    "Ampere"        : 'pcl3',
    "Hbpl1"         : 'hbpl1',
    "Kapan"         : 'pcl3',
    "MimasTDR"      : 'pcl3',
    "Saipan15B"     : 'pcl3',
    "Gemstone"      : 'pcl3',
    "SPDOfficejetProAsize" : 'pcl3',
	"CLE"                  :'pcl3',
     "CLE17"                :'pcl3',
    "SPDOfficejetProBsize" : 'pcl3',
    "CopperheadIPH17"   : 'pcl3',
    "PyramidRefresh17"     : 'pcl3'
}

PDL_TYPE_PCL = 0  # less preferred
PDL_TYPE_PS = 1   #      /\
PDL_TYPE_HOST = 2 # more preferred (however, may req. plugin)

PDL_TYPES = { # Used to prioritize PPD file selection in prnt.cups.getPPDFile2()
    'pcl3' : PDL_TYPE_PCL,
    'pcl5' : PDL_TYPE_PCL,
    'pcl6' : PDL_TYPE_PCL,
    'pcl5e' : PDL_TYPE_PCL,
    'pcl' : PDL_TYPE_PCL,
    'pclxl' : PDL_TYPE_PCL,
    'ps' : PDL_TYPE_PS,
    'lidil' : PDL_TYPE_HOST,
    'zjs' : PDL_TYPE_HOST,
    'zjstream' : PDL_TYPE_HOST,
    'zxs' : PDL_TYPE_HOST,
    'zxstream' : PDL_TYPE_HOST,
    'jpeg' : PDL_TYPE_HOST,
    'jpg' : PDL_TYPE_HOST,
    'jetready' : PDL_TYPE_HOST,
    'jr' : PDL_TYPE_HOST,
    'hbpl1' : PDL_TYPE_HOST,
}


TECH_SUBCLASSES = [
    "LargeFormatSuperB",
    "LargeFormatA3",
    "CoverMedia", # 3425
    "FullBleed",
    "Duplex",
    "Normal",
    "Apollo2000",
    "Apollo2200",
    "Apollo2500",
    "NoPhotoMode",
    "NoPhotoBestHiresModes",
    "No1200dpiNoSensor",
    "NoFullBleed",
    "4x6FullBleed",
    "300dpiOnly",  # LaserJet 4L
    "GrayscaleOnly", # DJ540
    "NoAutoTray", # PS Pro 8850
    "NoEvenDuplex", # PS C8100
    "NoAutoDuplex",
    "NoCDDVD",
    "NoMaxDPI",
    "NoMaxDPI",
    "SmallMargins",
    "Trim",
    "4800x1200dpi",
    "Advanced",
    "Mono",
    "Color",
    "AutoDuplex",
    "K10"
]

TECH_SUBCLASSES.sort()


# Items will be capitalized unless in this dict
MODEL_UI_REPLACEMENTS = {'laserjet'   : 'LaserJet',
                          'psc'        : 'PSC',
                          'hp'         : 'HP',
                          'mfp'        : 'MFP',
                        }


def normalizeModelUIName(model):
    ml = model.lower().strip()

    if 'apollo' in ml:
        z = ml.replace('_', ' ')
    else:
        if ml.startswith("hp"):
            z = ml[3:].replace('_', ' ')
        else:
            z = ml.replace('_', ' ')

    y = []
    for x in z.split():
        if pat_prod_num.search(x): # don't cap items like cp1700dn
            y.append(x)
        else:
            y.append(MODEL_UI_REPLACEMENTS.get(x, x.capitalize()))

    if 'apollo' in ml:
        return ' '.join(y)
    else:
        return "HP " + ' '.join(y)


def normalizeModelName(model):
    if not isinstance(model, str):
       try:
           model = model.encode('utf-8')
       except UnicodeEncodeError:
          log.error("Failed to encode model = %s  type=%s "%(model,type(model)))

    return utils.xstrip(model.replace(' ', '_').replace('__', '_').replace('~','').replace('/', '_'), '_')


class ModelData:
    def __init__(self, root_path=None):
        if root_path is None:
            self.root_path = prop.models_dir
        else:
            self.root_path = root_path

        self.__cache = {}
        self.reset_includes()
        self.sec = re.compile(r'^\[(.*)\]')
        self.inc = re.compile(r'^\%include (.*)', re.I)
        self.inc_line = re.compile(r'^\%(.*)\%')
        self.eq = re.compile(r'^([^=]+)=(.*)')
        self.date = re.compile(r'^(\d{1,2})/(\d{1,2})/(\d{4,4})')

        files = [(os.path.join(self.root_path, "models.dat"),
                  os.path.join(self.root_path, "unreleased", "unreleased.dat")),
                 (os.path.join(os.getcwd(), 'data', 'models', 'models.dat'),
                  os.path.join(os.getcwd(), 'data', 'models', 'unreleased', 'unreleased.dat'))]

        for self.released_dat, self.unreleased_dat in files:
            if os.path.exists(self.released_dat):
                break

        else:
            self.released_dat, self.unreleased_dat = None, None
            log.error("Unable to locate models.dat file")

        self.FIELD_TYPES = {
            # Static model query data (from models.dat)
            'align-type' : TYPE_INT,
            'clean-type' : TYPE_INT,
            'color-cal-type' : TYPE_INT,
            'copy-type' : TYPE_INT,
            'embedded-server-type' : TYPE_INT,
            'fax-type' : TYPE_INT,
            'fw-download' : TYPE_BOOL,
            'icon' : TYPE_STR,
            'io-mfp-mode' : TYPE_INT,
            'io-mode' : TYPE_INT,
            'io-support' : TYPE_BITFIELD,
            'job-storage' : TYPE_INT,
            'monitor-type' : TYPE_INT,
            'linefeed-cal-type' : TYPE_INT,
            'panel-check-type' : TYPE_INT,
            'pcard-type' : TYPE_INT,
            'plugin' : TYPE_INT,
            'plugin-reason' : TYPE_BITFIELD,
            'power-settings': TYPE_INT,
            'pq-diag-type' : TYPE_INT,
            'r-type' : TYPE_INT,
            'scan-type' : TYPE_INT,
            'scan-src' : TYPE_INT,
            #'scan-duplex' : TYPE_BOOL,
            'status-battery-check' : TYPE_INT,
            'status-dynamic-counters' : TYPE_INT,
            'status-type' : TYPE_INT,
            'support-subtype' : TYPE_HEX,
            'support-released' : TYPE_BOOL,
            'support-type' : TYPE_INT,
            'support-ver' : TYPE_STR,
            'tech-class' : TYPE_LIST,
            'tech-subclass' : TYPE_LIST,
            'tech-type' : TYPE_INT,
            'usb-pid' : TYPE_HEX,
            'usb-vid' : TYPE_HEX,
            'wifi-config': TYPE_INT,
            'ppd-name' : TYPE_STR,
            }

        self.FIELD_TYPES_DYN = {
            # Dynamic model data (from device query)
            'dev-file' : TYPE_STR,
            'fax-uri' : TYPE_STR,
            'scan-uri' : TYPE_STR,
            'is-hp' : TYPE_BOOL,
            'host' : TYPE_STR,
            'status-desc' : TYPE_STR,
            'cups-printers' : TYPE_STR,
            'serial' : TYPE_STR,
            'error-state' : TYPE_INT,
            'device-state' : TYPE_INT,
            'panel' : TYPE_INT,
            'device-uri' : TYPE_STR,
            'panel-line1' : TYPE_STR,
            'panel-line2' : TYPE_STR,
            'back-end' : TYPE_STR,
            'port' : TYPE_INT,
            'deviceid' : TYPE_STR,
            'cups-uri' : TYPE_STR,
            'status-code' : TYPE_INT,
            'rs' : TYPE_STR,
            'rr' : TYPE_STR,
            'rg' : TYPE_STR,
            'r' : TYPE_INT,
            'duplexer' : TYPE_INT,
            'supply-door' : TYPE_INT,
            'revision' : TYPE_INT,
            'media-path' : TYPE_INT,
            'top-door' : TYPE_BOOL,
            'photo-tray' : TYPE_BOOL,
            }

        self.RE_FIELD_TYPES = {
            re.compile('^r(\d+)-agent(\d+)-kind', re.IGNORECASE) : TYPE_INT,
            re.compile('^r(\d+)-agent(\d+)-type', re.IGNORECASE) : TYPE_INT,
            re.compile('^r(\d+)-agent(\d+)-sku', re.IGNORECASE) : TYPE_STR,
            re.compile('^agent(\d+)-desc', re.IGNORECASE) : TYPE_STR,
            re.compile('^agent(\d+)-virgin', re.IGNORECASE) : TYPE_BOOL,
            re.compile('^agent(\d+)-dvc', re.IGNORECASE) : TYPE_INT,
            re.compile('^agent(\d+)-kind', re.IGNORECASE) : TYPE_INT,
            re.compile('^agent(\d+)-type', re.IGNORECASE) : TYPE_INT,
            re.compile('^agent(\d+)-id', re.IGNORECASE) : TYPE_INT,
            re.compile('^agent(\d+)-hp-ink', re.IGNORECASE) : TYPE_BOOL,
            re.compile('^agent(\d+)-health-desc', re.IGNORECASE) : TYPE_STR,
            re.compile('^agent(\d+)-health$', re.IGNORECASE) : TYPE_INT,
            re.compile('^agent(\d+)-known', re.IGNORECASE) : TYPE_BOOL,
            re.compile('^agent(\d+)-level', re.IGNORECASE) : TYPE_INT,
            re.compile('^agent(\d+)-ack', re.IGNORECASE) : TYPE_BOOL,
            re.compile('^agent(\d+)-sku', re.IGNORECASE) : TYPE_STR,
            re.compile('^in-tray(\d+)', re.IGNORECASE) : TYPE_BOOL,
            re.compile('^out-tray(\d+)', re.IGNORECASE) : TYPE_BOOL,
            re.compile('^model(\d+)', re.IGNORECASE) : TYPE_STR,
            }

        self.TYPE_CACHE = {}


    def read_all_files(self, unreleased=True):
        if os.path.exists(self.released_dat):
            self.read_section(self.released_dat)

            if self.unreleased_dat is not None and os.path.exists(self.unreleased_dat):
                self.read_section(self.unreleased_dat )

        return self.__cache


    def read_section(self, filename, section=None, is_include=False): # section==None, read all sections
        found, in_section = False, False

        if section is not None:
            section = section.lower()

            if is_include:
                log.debug("Searching for include [%s] in file %s" % (section, filename))
            else:
                log.debug("Searching for section [%s] in file %s" % (section, filename))

        if is_include:
            cache = self.__includes
        else:
            cache = self.__cache

        try:
            fd = open(filename)
        except IOError as e:
            log.error("I/O Error: %s (%s)" % (filename, e.strerror))
            return False

        while True:
            line = fd.readline()

            if not line:
                break

            if line[0] in ('#', ';'):
                continue

            if line[0] == '[':
                if in_section and section is not None:
                    break

                match = self.sec.search(line)

                if match is not None:
                    in_section = True

                    read_section = match.group(1).lower()

                    if section is not None:
                        found = in_section = (read_section == section)

                    if in_section:
                        if section is not None:
                            log.debug("Found section [%s] in file %s" % (read_section, filename))

                        cache[read_section] = {}

                continue

            if line[0] == '%':
                match = self.inc.match(line)

                if match is not None:
                    inc_file = match.group(1)
                    log.debug("Found include file directive: %%include %s" % inc_file)
                    self.__include_files.append(os.path.join(os.path.dirname(filename), inc_file))
                    continue

                if in_section:
                    match = self.inc_line.match(line)

                    if match is not None:
                        inc_sect = match.group(1)
                        log.debug("Found include directive %%%s%%" % inc_sect)

                        try:
                            self.__includes[inc_sect]
                        except KeyError:
                            for inc in self.__include_files:

                                if self.read_section(inc, inc_sect, True):
                                    break
                            else:
                                log.error("Include %%%s%% not found." % inc_sect)

            if in_section:
                match = self.eq.search(line)

                if match is not None:
                    key = match.group(1)
                    value = match.group(2)
                    value = self.convert_data(key, value)
                    cache[read_section][key] = value

        fd.close()
        return found


    def reset_includes(self):
        self.__include_files = []
        self.__includes = {}


    def __getitem__(self, model):
        model = model.lower()

        try:
            return self.__cache[model]
        except:
            log.debug("Cache miss: %s" % model)

            log.debug("Reading file: %s" % self.released_dat)

            if self.read_section(self.released_dat, model):
                return self.__cache[model]

            if self.unreleased_dat is not None and os.path.exists(self.unreleased_dat):
                log.debug("Reading file: %s" % self.unreleased_dat)

                if self.read_section(self.unreleased_dat, model):
                    return self.__cache[model]

            return {}


    def all_models(self):
        return self.__cache


    def get_data_type(self, key):
        try:
            return self.FIELD_TYPES[key]
        except KeyError:
            try:
                return self.FIELD_TYPES_DYN[key]
            except KeyError:
                try:
                    return self.TYPE_CACHE[key]
                except KeyError:
                    for pat, typ in list(self.RE_FIELD_TYPES.items()):
                        match = pat.match(key)
                        if match is not None:
                            self.TYPE_CACHE[key] = typ
                            return typ

        log.error("get_data_type(): Field type lookup failed for key %s" % key)
        return None


    def convert_data(self, key, value, typ=None):
        if typ is None:
            typ = self.get_data_type(key)

        if  typ in (TYPE_BITFIELD, TYPE_INT):
            try:
                value = int(value)
            except (ValueError, TypeError):
                log.error("Invalid value in .dat file: %s=%s" % (key, value))
                value = 0

        elif typ == TYPE_BOOL:
            value = utils.to_bool(value)

        elif typ == TYPE_LIST:
            value = [x for x in value.split(',') if x]

        elif typ == TYPE_DATE: # mm/dd/yyyy
            if datetime_avail:
                # ...don't use datetime.strptime(), wasn't avail. until 2.5
                match = self.date.search(value)

                if match is not None:
                    month = int(match.group(1))
                    day = int(match.group(2))
                    year = int(match.group(3))

                    value = datetime.date(year, month, day)

        elif typ == TYPE_HEX:
            try:
                value = int(value, 16)
            except (ValueError, TypeError):
                log.error("Invalid hex value in .dat file: %s=%s" % (key, value))
                value = 0

        return value
