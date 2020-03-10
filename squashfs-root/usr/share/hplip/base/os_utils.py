# -*- coding: utf-8 -*-
#
# (c) Copyright @ 2015 HP Development Company, L.P.
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
# Author: Amarnath Chitumalla, Goutam Kodu
#

# Global import
import os
import os.path
import locale
import stat

#Local
from . import logger

log = logger.Logger('', logger.Logger.LOG_LEVEL_INFO, logger.Logger.LOG_TO_CONSOLE)

def execute(cmd):
    if cmd:
        return os.system(cmd)
    else:
        log.error("Command not found \n" % cmd)
        return 127


# Returns the file size in bytes.
# If file is not exists, returns size as -1.
#
def getFileSize(filename):
    if not os.path.exists(filename):
        return -1

    return os.path.getsize(filename)

def getHPLIPDir():
    homedir = os.path.expanduser('~')
    hplipdir = os.path.join(homedir, ".hplip")
    status = 0
    if not os.path.exists(hplipdir):
        try:
            os.umask(0)
            s = os.stat(homedir)
            os.mkdir(hplipdir, 0o755)
            os.chown(hplipdir, s[stat.ST_UID], s[stat.ST_GID])
        except OSError:
            status = 1
            log.error("Failed to create %s" % hplipdir)
    return status, hplipdir
def changeOwner(path, user, group, Recursive = False ):
    status = 0
    try:
        if Recursive:
            for root, dirs, files in os.walk(path):  
                for dr in dirs:  
                    os.chown(os.path.join(root, dr), user, group)
                for fl in files:
                    os.chown(os.path.join(root, fl), user, group)
        else:
            os.chown(path, user, group)
    except OSError:
        status = 1
        log.error("Failed to change ownership of %s" %path)
    return status
