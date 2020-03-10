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
# Author: Amarnath Chitumalla, Sanjay Kumar
#
#Global imports
import os
import stat
import datetime

#Local imports
from base.codes import *
from base.strings import *
from base import utils
from base import os_utils
from base.g import *
from subprocess import Popen, PIPE


class DigiSign_Verification(object):
    def __init__(self):
        pass

    def validate(self):
        pass


class GPG_Verification(DigiSign_Verification):
    def __init__(self, pgp_site = 'pgp.mit.edu', key = 0x4ABA2F66DBD5A95894910E0673D770CDA59047B9):
        self.__pgp_site = pgp_site
        self.__key = key
        self.__gpg = utils.which('gpg',True)

        sts, self.__hplipdir = os_utils.getHPLIPDir()
        self.__gpg_dir = os.path.join(self.__hplipdir, ".gnupg")

        #Make sure gpg directory is present. GPG keys will be retrieved here from the key server
        

        if not os.path.exists(self.__gpg_dir):
            try:
                os.mkdir(self.__gpg_dir, 0o755)
            except OSError:
                log.error("Failed to create %s" % self.__gpg_dir)
        self.__change_owner()
    def __change_owner(self, Recursive = False):
        try:
            os.umask(0)
            s = os.stat(self.__hplipdir)
            os_utils.changeOwner(self.__gpg_dir, s[stat.ST_UID], s[stat.ST_GID], Recursive)

        except OSError:
            log.error("Failed to Change ownership of %s" %self.__gpg_dir)

    def __gpg_check(self, hplip_package, hplip_digsig):

        cmd = '%s --homedir %s -no-permission-warning --verify %s %s' % (self.__gpg, self.__gpg_dir, hplip_digsig, hplip_package)

        log.debug("Verifying file %s : cmd = [%s]" % (hplip_package,cmd))

        status, output = utils.run(cmd)

        log.debug("%s status: %d  output:%s" % (self.__gpg, status,output))

        return status


    def __acquire_gpg_key(self):

        cmd = '%s --homedir %s --no-permission-warning --keyserver %s --recv-keys 0x%X' \
              % (self.__gpg, self.__gpg_dir, self.__pgp_site, self.__key)

        log.info("Receiving digital keys: %s" % cmd)
        status, output = utils.run(cmd)
        log.debug(output)

        self.__change_owner(True)

        return status 


    def validate(self, hplip_package, hplip_digsig):      

        log.debug("Validating %s with %s signature file" %(hplip_package, hplip_digsig))
        if not self.__gpg:
            return ERROR_GPG_CMD_NOT_FOUND, queryString(ERROR_GPG_CMD_NOT_FOUND)

        if not os.path.exists(hplip_package):
            return ERROR_FILE_NOT_FOUND, queryString(ERROR_FILE_NOT_FOUND, 0, hplip_package)

        if not os.path.exists(hplip_digsig):
            return ERROR_DIGITAL_SIGN_NOT_FOUND, queryString(ERROR_DIGITAL_SIGN_NOT_FOUND, 0, hplip_digsig)

        status = self.__acquire_gpg_key()
        if status != 0:
            return ERROR_UNABLE_TO_RECV_KEYS, queryString(ERROR_UNABLE_TO_RECV_KEYS)

        status = self.__gpg_check(hplip_package, hplip_digsig)
        if status != 0:
            return ERROR_DIGITAL_SIGN_BAD, queryString(ERROR_DIGITAL_SIGN_BAD, 0, hplip_package)
        else:
            return ERROR_SUCCESS, ""

