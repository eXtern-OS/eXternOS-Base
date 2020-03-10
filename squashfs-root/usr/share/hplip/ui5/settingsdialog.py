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
# Author: Don Welch
#

# Local
from base.g import *
from base.codes import *
from base.sixext import  to_unicode
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from .settingsdialog_base import Ui_SettingsDialog_base



class SettingsDialog(QDialog, Ui_SettingsDialog_base):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.SetDefaultsButton.clicked.connect(self.SetDefaultsButton_clicked)

        self.user_settings = UserSettings()
        self.user_settings.load()
        
        cur_vers = sys_conf.get('hplip', 'version')
        last_ver = user_conf.get('upgrade','latest_available_version')
        if utils.Is_HPLIP_older_version(cur_vers, last_ver):
            upgrade_msg ="Currently HPLIP-%s version is installed.\nLatest HPLIP-%s version is available for installation"%(cur_vers, last_ver)
        else:
            upgrade_msg ="HPLIP-%s version is installed"%(cur_vers)
            
        self.SystemTraySettings.initUi(self.user_settings.systray_visible,
                                       self.user_settings.polling,
                                       self.user_settings.polling_interval,
                                       self.user_settings.device_list,
                                       self.user_settings.systray_messages,
                                       self.user_settings.upgrade_notify,
                                       self.user_settings.upgrade_pending_update_time,
                                       upgrade_msg)

        self.updateControls()


    def updateControls(self):
        self.AutoRefreshCheckBox.setChecked(self.user_settings.auto_refresh)
        self.AutoRefreshRateSpinBox.setValue(self.user_settings.auto_refresh_rate) # min
        if self.user_settings.auto_refresh_type == 1:
            self.RefreshCurrentRadioButton.setChecked(True)
        else:
            self.RefreshAllRadioButton.setChecked(True)

        self.ScanCommandLineEdit.setText(self.user_settings.cmd_scan)
        self.SystemTraySettings.systray_visible = self.user_settings.systray_visible
        self.SystemTraySettings.systray_messages = self.user_settings.systray_messages
        self.SystemTraySettings.upgrade_notify = self.user_settings.upgrade_notify
        self.SystemTraySettings.updateUi()


    def updateData(self):
        self.user_settings.systray_visible = self.SystemTraySettings.systray_visible
        self.user_settings.systray_messages = self.SystemTraySettings.systray_messages
        self.user_settings.cmd_scan = to_unicode(self.ScanCommandLineEdit.text())
        self.user_settings.auto_refresh = bool(self.AutoRefreshCheckBox.isChecked())
        self.user_settings.upgrade_notify = self.SystemTraySettings.upgrade_notify

        if self.RefreshCurrentRadioButton.isChecked():
            self.user_settings.auto_refresh_type = 1
        else:
            self.user_settings.auto_refresh_type = 2

        self.user_settings.auto_refresh_rate = self.AutoRefreshRateSpinBox.value()


    def SetDefaultsButton_clicked(self):
        self.user_settings.loadDefaults()
        self.updateControls()


    def accept(self):
        self.updateData()
        self.user_settings.save()
        QDialog.accept(self)

        # TODO: Need a way to signal hp-systray if systray_visible has changed

    def __tr(self,s,c = None):
        return qApp.translate("SettingsDialog",s,c)


