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
# Author: Amarnath Chitumalla
#
import os
import getpass
import time
import string

from . import utils, tui
from .g import *
from .sixext import BytesIO, StringIO
from .sixext.moves import input
from . import pexpect

PASSWORD_RETRY_COUNT = 3

AUTH_TYPES ={'mepis':'su',
             'debian':'su',
             'suse':'su',
             'mandriva':'su',
             'fedora':'su',
             'redhat':'su',
             'rhel':'su',
             'slackware':'su',
             'gentoo':'su',
             'redflag':'su',
             'ubuntu':'sudo',
             'xandros':'su',
             'freebsd':'su',
             'linspire':'su',
             'ark':'su',
             'pclinuxos':'su',
             'centos':'su',
             'igos':'su',
             'linuxmint':'sudo',
             'linpus':'sudo',
             'gos':'sudo',
             'boss':'su',
             'lfs':'su',
             }


# This function promts for the username and password and returns (username,password)
def showPasswordPrompt(prompt):
    import getpass
    print ("")
    print ("")
    print (log.bold(prompt))
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    return (username, password)



#TBD this function shoud be removed once distro class implemented
def get_distro_name():
    os_name = None
    try:
        import platform
        os_name = platform.dist()[0]
    except ImportError:
        os_name = None

    if not os_name: 
        name = os.popen('lsb_release -i | cut -f 2')
        os_name = name.read().strip()
        name.close()

    if not os_name:
       name = os.popen("cat /etc/issue | awk '{print $1}' | head -n 1")
       os_name = name.read().strip()
       name.close()

    os_name = os_name.lower()
    if "redhatenterprise" in os_name:
        os_name = 'rhel'
    elif "suse" in os_name:
        os_name = 'suse'

    return os_name




class Password(object):
    def __init__(self, Mode = INTERACTIVE_MODE):
        self.__password =""
        self.__password_prompt_str=""
        self.__passwordValidated = False
        self.__mode = Mode
        self.__readAuthType()  #self.__authType   
        self.__expectList =[]

        if not utils.to_bool(sys_conf.get('configure','qt5', '0')) and not not utils.to_bool(sys_conf.get('configure','qt4', '0')) and utils.to_bool(sys_conf.get('configure','qt3', '0')):
            self.__ui_toolkit = 'qt3'
        elif not utils.to_bool(sys_conf.get('configure','qt5', '0')) and not utils.to_bool(sys_conf.get('configure','qt3', '0')) and utils.to_bool(sys_conf.get('configure','qt4', '0')):
            self.__ui_toolkit = 'qt4'
        elif not utils.to_bool(sys_conf.get('configure','qt3', '0')) and not utils.to_bool(sys_conf.get('configure','qt4', '0')) and utils.to_bool(sys_conf.get('configure','qt5', '0')):
            self.__ui_toolkit = 'qt5'
            
        for s in utils.EXPECT_WORD_LIST:
            try:
                p = re.compile(s, re.I)
            except TypeError:
                self.__expectList.append(s)
            else:
                self.__expectList.append(p)

    ##################### Private functions ######################


    def __readAuthType(self):
        #TBD: Getting distro name should get distro class
        distro_name =  get_distro_name().lower()

        self.__authType = user_conf.get('authentication', 'su_sudo', '')
        if self.__authType != "su" and self.__authType != "sudo":
            try:
                self.__authType = AUTH_TYPES[distro_name]
            except KeyError:
                log.warn("%s distro is not found in AUTH_TYPES"%distro_name)
                self.__authType = 'su'

    def __getPasswordDisplayString(self):
        if self.__authType == "su":
            return "Please enter the root/superuser password: "
        else:
            return "Please enter the sudoer (%s)'s password: " % os.getenv('USER')


    def __changeAuthType(self):
        if self.__authType == "sudo":
            self.__authType = "su"
        else:
            self.__authType = "sudo"
        user_conf.set('authentication', 'su_sudo', self.__authType)


    def __get_password(self,pswd_msg=''):
        if pswd_msg == '':
            if self.__authType == "su":
                pswd_msg = "Please enter the root/superuser password: "
            else:
                pswd_msg = "Please enter the sudoer (%s)'s password: " % os.getenv('USER')
        return getpass.getpass(log.bold(pswd_msg))



    def __get_password_ui(self,pswd_msg='', user ="root"):
        if pswd_msg == '':
            pswd_msg = "Your HP Device requires to install HP proprietary plugin\nPlease enter root/superuser password to continue"

        if self.__ui_toolkit == "qt3":
            from ui.setupform import showPasswordUI
            username, password = showPasswordUI(pswd_msg, user, False)
        elif self.__ui_toolkit == "qt5":
            from ui5.setupdialog import showPasswordUI
            username, password = showPasswordUI(pswd_msg, user, False)
        else:       #self.__ui_toolkit == "qt4" --> default qt4
            from ui4.setupdialog import showPasswordUI
            username, password = showPasswordUI(pswd_msg, user, False)

        if username == "" and password == "":
            raise Exception("User Cancel")
            
        return  password


    def __password_check(self, cmd, timeout=1):
        import io
        output = io.StringIO()
        ok, ret = False, ''

        try:
            child = pexpect.spawnu(cmd, timeout=timeout)
        except pexpect.ExceptionPexpect:
            return 1, ''

        try:
            try:
                start = time.time()

                while True:
                    update_spinner()

                    i = child.expect(self.__expectList)
                    
                    cb = child.before
                    if cb:  
                        start = time.time()
                        output.write(cb)

                    if i == 0: # EOF
                        ok, ret = True, output.getvalue()
                        break

                    elif i == 1: # TIMEOUT                        
                        if('true' in cmd and self.__password_prompt_str == ""): #sudo true or su -c "true"
                            cb = cb.replace("[", "\[")
                            cb = cb.replace("]", "\]")

                            self.__password_prompt_str = cb
                            try:
                                p = re.compile(cb, re.I)
                            except TypeError:
                                self.__expectList.append(cb)
                            else:
                                self.__expectList.append(p)
                            log.debug("Adding missing password prompt string [%s]"%self.__password_prompt_str)
                        continue

                    else: # password
                        if(self.__password_prompt_str == ""): 
                            self.__password_prompt_str = utils.EXPECT_WORD_LIST[i]
                            log.debug("Updating password prompt string [%s]"%self.__password_prompt_str)

                        child.sendline(self.__password)

            except (Exception, pexpect.ExceptionPexpect) as e:          
                log.exception()

        finally:
            cleanup_spinner()

            try:
                child.close()
            except OSError:
                pass

        if ok:
            return child.exitstatus, ret
        else:
            
            return 1, ''


    def __validatePassword(self ,pswd_msg):
        x = 1
        while True:
            if self.__mode == INTERACTIVE_MODE:
                self.__password = self.__get_password(pswd_msg)
            else:
                try:
                    if self.getAuthType() == 'su':
                        self.__password = self.__get_password_ui(pswd_msg, "root")
                    else:
                        self.__password = self.__get_password_ui(pswd_msg, os.getenv("USER"))
                except Exception as ex:
                    log.debug(ex)
                    break

            cmd = self.getAuthCmd() % "true"
            log.debug(cmd)

            status, output = self.__password_check(cmd)
            log.debug("status = %s  output=%s "%(status,output))

            if self.__mode == GUI_MODE:
                if self.__ui_toolkit == "qt4":
                    from ui4.setupdialog import FailureMessageUI
                elif self.__ui_toolkit == "qt5":
                    from ui5.setupdialog import FailureMessageUI
                elif self.__ui_toolkit == "qt3":
                    from ui.setupform import FailureMessageUI


            if status == 0:
                self.__passwordValidated = True
                break
            elif "not in the sudoers file" in output:
                #TBD.. IF user doesn't have sudo permissions, needs to change to "su" type and query for password
                self.__changeAuthType()
                msg = "User doesn't have sudo permissions.\nChanging Authentication Type. Try again."
                if self.__mode == GUI_MODE:
                    FailureMessageUI(msg)
                else:
                    log.error(msg)
                raise Exception("User is not in the sudoers file.")

            else:
                self.__password = ""
                x += 1
                if self.__mode == GUI_MODE:
                    if x > PASSWORD_RETRY_COUNT:
                        FailureMessageUI("Password incorrect. ")
                        return
                    else:
                        FailureMessageUI("Password incorrect. %d attempt(s) left." % (PASSWORD_RETRY_COUNT +1 -x ))
                else:
                    if x > PASSWORD_RETRY_COUNT:
                        log.error("Password incorrect. ")
                        return
                    else:
                        log.error("Password incorrect. %d attempt(s) left." % (PASSWORD_RETRY_COUNT +1 -x ))


    def __get_password_utils(self):
        if self.__authType == "su":
            AuthType, AuthCmd = 'su', 'su -c "%s"'
        else:
            AuthType, AuthCmd = 'sudo', 'sudo %s'

        return AuthType, AuthCmd


    def __get_password_utils_ui(self):
        distro_name =  get_distro_name().lower()
        if self.__authType == "sudo":
            AuthType, AuthCmd = 'sudo', 'sudo %s'
        else:
            AuthType, AuthCmd  = 'su', 'su -c "%s"'
        '''
        if utils.which('kdesu'):
            AuthType, AuthCmd = 'kdesu', 'kdesu -- %s'
        elif utils.which('kdesudo'):
            AuthType, AuthCmd = 'kdesudo', 'kdesudo -- %s'
        elif utils.which('gnomesu'):
            AuthType, AuthCmd = 'gnomesu', 'gnomesu -c "%s"'
        elif utils.which('gksu'):
            AuthType, AuthCmd = 'gksu' , 'gksu "%s"'
        '''

        return AuthType, AuthCmd


    ##################### Public functions ######################

    def clearPassword(self):
        log.debug("Clearing password...")
        self.__password =""
        self.__passwordValidated = False
        if self.__authType == 'sudo':
            utils.run("sudo -K")


    def getAuthType(self):
        if self.__mode == INTERACTIVE_MODE:
            retValue = self.__authType
        else:
            retValue, AuthCmd = self.__get_password_utils_ui()

        return retValue


    def getAuthCmd(self):
        if self.__mode == INTERACTIVE_MODE:
            AuthType, AuthCmd = self.__get_password_utils()
        else:
            AuthType, AuthCmd = self.__get_password_utils_ui()

        return AuthCmd


    def getPassword(self, pswd_msg='', psswd_queried_cnt = 0):
        if self.__passwordValidated:
            return self.__password

        if psswd_queried_cnt:
            return self.__password

        self.__validatePassword( pswd_msg)
        return self.__password

    def getPasswordPromptString(self):
        return self.__password_prompt_str


