# -*- coding: utf-8 -*-
#
# (c) Copyright 2001-2015 HP Development Company, L.P.
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
# Authors: Amarnath Chitumalla
#

#Global
import os
import time
import signal

# Local
from base.g import *
from base import device, utils, pkit, os_utils
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Ui
from .upgradedialog_base import Ui_Dialog

MANUAL_INSTALL_LINK = "http://hplipopensource.com/hplip-web/install/manual/index.html"


class UpgradeDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, distro_tier, msg):
        QDialog.__init__(self, parent)
        self.distro_tier = distro_tier
        self.msg = msg
        self.result = False
        self.setupUi(self, distro_tier, msg)
        self.initUi()


    def initUi(self):
        # connect signals/slots
        self.NextButton.clicked.connect(self.NextButton_clicked)
        self.CancelButton.clicked.connect(self.CancelButton_clicked)
#        self.connect (self.comboBox, SIGNAL ("currentIndexChanged (const QString&)"), self.slotIndexChanged)
        self.installRadioBtton.toggled[bool].connect(self.installRadioBtton_toggled)
        self.remindRadioBtton.toggled[bool].connect(self.remindRadioBtton_toggled)
        self.dontRemindRadioBtton.toggled[bool].connect(self.dontRemindRadioBtton_toggled)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))


    def installRadioBtton_toggled(self, radio_enabled):
        if radio_enabled is True:
            self.installRadioBtton.setChecked(True)
        else:
            self.installRadioBtton.setChecked(False)


    def remindRadioBtton_toggled(self, radio_enabled):
        if radio_enabled is True:
            self.remindRadioBtton.setChecked(True)
            self.daysSpinBox.setEnabled(True)
        else:
            self.remindRadioBtton.setChecked(False)
            self.daysSpinBox.setEnabled(False)


    def dontRemindRadioBtton_toggled(self, radio_enabled):
        if radio_enabled is True:
            self.dontRemindRadioBtton.setChecked(True)
        else:
            self.dontRemindRadioBtton.setChecked(False)


    def NextButton_clicked (self):
        if self.dontRemindRadioBtton.isChecked():
            log.debug("HPLIP Upgrade, selected Don't remind again radiobutton")
            user_conf.set('upgrade', 'notify_upgrade', 'false')
            msg= "Check for HPLIP updates is disabled. To enable it again, change 'Settings' in 'HP systemtray' "
            SuccessUI(self, self.__tr(msg))

        elif self.remindRadioBtton.isChecked():
            schedule_days = str(self.daysSpinBox.value())
            log.debug("HPLIP Upgrade, selected remind later radiobutton  days= %d" %(int(schedule_days)))
            next_time = time.time() + (int(schedule_days) *24 * 60 *60)
            user_conf.set('upgrade', 'pending_upgrade_time', str(int(next_time)))
        else:
            log.debug("HPLIP Upgrade, selected Install radiobutton  distro_type=%d" %self.distro_tier)
            self.NextButton.setEnabled(False)
            if self.distro_tier != 1:     # not tier 1 distro
                log.debug("OK pressed for tier 2 distro pressed")
                utils.openURL(MANUAL_INSTALL_LINK)

                ## TBD::open browser
            else:
                terminal_cmd = utils.get_terminal()
                if terminal_cmd is not None and utils.which("hp-upgrade"):
                    cmd = terminal_cmd + " 'hp-upgrade -w'"
                    os_utils.execute(cmd)
                    self.result = True
                else:
                    log.error("Failed to run hp-upgrade command from terminal =%s "%terminal_cmd)
                    FailureUI(self, self.__tr("Failed to run hp-upgrade"))

        self.close()


    def CancelButton_clicked(self):
        log.debug("User exit")
        self.close()

    def __tr(self,s,c = None):
        return qApp.translate("UpgradeDialog",s,c)

