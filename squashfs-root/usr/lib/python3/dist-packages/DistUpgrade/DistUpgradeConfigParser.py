# DistUpgradeConfigParser.py 
#  
#  Copyright (c) 2004-2014 Canonical
#  
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
# 
#  This program is free software; you can redistribute it and/or 
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA


from configparser import NoOptionError, NoSectionError
from configparser import ConfigParser as SafeConfigParser
import subprocess
import os.path
import logging
import glob

CONFIG_OVERRIDE_DIR = "/etc/update-manager/release-upgrades.d"


class DistUpgradeConfig(SafeConfigParser):
    def __init__(self, datadir, name="DistUpgrade.cfg", 
                 override_dir=None, defaults_dir=None):
        SafeConfigParser.__init__(self)
        # we support a config overwrite, if DistUpgrade.cfg.dapper exists
        # and the user runs dapper, that one will be used
        from_release = subprocess.Popen(
            ["lsb_release", "-c", "-s"], stdout=subprocess.PIPE,
            universal_newlines=True).communicate()[0].strip()
        self.datadir = datadir
        if os.path.exists(name + "." + from_release):
            name = name + "." + from_release
        maincfg = os.path.join(datadir, name)
        # defaults are read first
        self.config_files = []
        if defaults_dir:
            for cfg in glob.glob(defaults_dir + "/*.cfg"):
                self.config_files.append(cfg)
        # our config file
        self.config_files += [maincfg]
        # overrides are read later
        if override_dir is None:
            override_dir = CONFIG_OVERRIDE_DIR
        if override_dir is not None:
            for cfg in glob.glob(override_dir + "/*.cfg"):
                self.config_files.append(cfg)
        self.read(self.config_files)

    def getWithDefault(self, section, option, default):
        try:
            if type(default) == bool:
                return self.getboolean(section, option)
            elif type(default) == float:
                return self.getfloat(section, option)
            elif type(default) == int:
                return self.getint(section, option)
            return self.get(section, option)
        except (NoSectionError, NoOptionError):
            return default

    def getlist(self, section, option):
        try:
            tmp = self.get(section, option)
        except (NoSectionError, NoOptionError):
            return []
        items = [x.strip() for x in tmp.split(",")]
        return items

    def getListFromFile(self, section, option):
        try:
            filename = self.get(section, option)
        except NoOptionError:
            return []
        p = os.path.join(self.datadir, filename)
        if not os.path.exists(p):
            logging.error("getListFromFile: no '%s' found" % p)
        with open(p) as f:
            items = [x.strip() for x in f]
        return [s for s in items if not s.startswith("#") and not s == ""]


if __name__ == "__main__":
    c = DistUpgradeConfig(".")
    print(c.getlist("Distro", "MetaPkgs"))
    print(c.getlist("Distro", "ForcedPurges"))
    print(c.getListFromFile("Sources", "ValidMirrors"))
    print(c.getWithDefault("Distro", "EnableApport", True))
    print(c.set("Distro", "Foo", "False"))
    print(c.getWithDefault("Distro", "Foo", True))
