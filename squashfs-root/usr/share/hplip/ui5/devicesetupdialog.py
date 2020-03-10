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
# Authors: Don Welch
#

# StdLib
import operator
import string

# Local
from base.g import *
from base import device, pml
from prnt import cups
from base.codes import *
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Ui
from .devicesetupdialog_base import Ui_Dialog

TAB_POWER_SETTINGS = 0

class DeviceSetupDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, device_uri):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.device_uri = device_uri
        self.mq = {}
        self.dev = None
        self.initUi()

        QTimer.singleShot(0, self.updateUi)


    def initUi(self):
        # connect signals/slots
        self.CancelButton.clicked.connect(self.CancelButton_clicked)
        #self.ApplyButton.clicked.connect(self.ApplyButton_clicked)
        self.DeviceComboBox.DeviceUriComboBox_noDevices.connect(self.DeviceUriComboBox_noDevices)
        self.DeviceComboBox.DeviceUriComboBox_currentChanged.connect(self.DeviceUriComboBox_currentChanged)
        
        self.DeviceComboBox.setFilter({'power-settings': (operator.gt, 0)})

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))

        if self.device_uri:
            self.DeviceComboBox.setInitialDevice(self.device_uri)

        self.DurationComboBox.addItem(self.__tr("15 minutes"), 15)
        self.DurationComboBox.addItem(self.__tr("30 minutes"), 30)
        self.DurationComboBox.addItem(self.__tr("45 minutes"), 45)
        self.DurationComboBox.addItem(self.__tr("1 hour"), 60)
        self.DurationComboBox.addItem(self.__tr("2 hours"), 120)
        self.DurationComboBox.addItem(self.__tr("3 hours"), 180)

        self.DurationComboBox.activated[int].connect(self.DurationComboBox_activated)

        self.OnRadioButton.toggled[bool].connect(self.OnRadioButton_toggled)


    def OnRadioButton_toggled(self, b):
        i = self.DurationComboBox.currentIndex()
        if i == -1:
            return
        v, ok = value_int(self.DurationComboBox.itemData(i))
        if not ok:
            return

        if self.power_settings == POWER_SETTINGS_EPML:
            if b:
                self.setPowerSettingsEPML('999')
            else:
                self.setPowerSettingsEPML(string.zfill(v, 3))

        elif self.power_settings == POWER_SETTINGS_PML:
            if b:
                self.setPowerSettingsPML(pml.OID_POWER_SETTINGS_NEVER)
            else:
                self.setPowerSettingsPML(self.getPMLSettingsValue(v))



    def updateUi(self):
        self.DeviceComboBox.updateUi()


    def updatePowerSettingsUi(self):
        pass


    def DeviceUriComboBox_currentChanged(self, device_uri):
        beginWaitCursor()
        try:
            self.device_uri = device_uri

            if self.dev is not None:
                self.dev.close()

            self.dev = device.Device(self.device_uri)

            # Update
            self.mq = device.queryModelByURI(self.device_uri)
            self.power_settings = self.mq.get('power-settings', POWER_SETTINGS_NONE)

            self.TabWidget.setTabEnabled(TAB_POWER_SETTINGS, self.power_settings != POWER_SETTINGS_NONE)

            if self.power_settings == POWER_SETTINGS_EPML:
                self.updatePowerSettingsEPML()

            elif self.power_settings == POWER_SETTINGS_PML:
                self.updatePowerSettingsPML()

        finally:
            endWaitCursor()

    # DJ 4x0 battery power settings

    # 15min = 015
    # 30min = 030
    # 45min = 045
    # 1hr   = 060
    # 2hr   = 120
    # 3hr   = 180
    # never = 999

    def updatePowerSettingsEPML(self):
        value = self.getPowerSettingsEPML()

        if value == '999':
            self.OnRadioButton.setChecked(True)
            self.OffRadioButton.setChecked(False)
        else:
            self.OnRadioButton.setChecked(False)
            self.OffRadioButton.setChecked(True)

            find = int(value)
            index = self.DurationComboBox.findData(find)

            if index != -1:
                self.DurationComboBox.setCurrentIndex(index)


    def getPowerSettingsEPML(self):
        value = self.dev.getDynamicCounter(256, False)
        log.debug("Current power settings: %s" % value)
        self.dev.closePrint()
        return value[6:9]


    def setPowerSettingsEPML(self, value):
        log.debug("Setting power setting to %s" % value)
        pcl= \
    """\x1b%%-12345X@PJL ENTER LANGUAGE=PCL3GUI\n\x1bE\x1b%%Pmech.set_battery_autooff %s;\nudw.quit;\x1b*rC\x1bE\x1b%%-12345X""" % value
        self.dev.printData(pcl, direct=True)
        self.dev.closePrint()

    # h470

    # PML
    # OID_POWER_SETTINGS = ('1.1.2.118', TYPE_ENUMERATION)
    # OID_POWER_SETTINGS_15MIN = 1
    # OID_POWER_SETTINGS_30MIN = 2
    # OID_POWER_SETTINGS_45MIN = 3
    # OID_POWER_SETTINGS_1HR = 4
    # OID_POWER_SETTINGS_2HR = 5
    # OID_POWER_SETTINGS_3HR = 6
    # OID_POWER_SETTINGS_NEVER = 999

    def updatePowerSettingsPML(self):
        value = self.getPowerSettingsPML()
        if value == pml.OID_POWER_SETTINGS_NEVER:
            self.OnRadioButton.setChecked(True)
            self.OffRadioButton.setChecked(False)
        else:
            self.OnRadioButton.setChecked(False)
            self.OffRadioButton.setChecked(True)

            find = 15
            if value == pml.OID_POWER_SETTINGS_15MIN:
                find = 15
            elif value == pml.OID_POWER_SETTINGS_30MIN:
                find = 30
            elif value == pml.OID_POWER_SETTINGS_45MIN:
                find = 45
            elif value == pml.OID_POWER_SETTINGS_1HR:
                find = 60
            elif value == pml.OID_POWER_SETTINGS_2HR:
                find = 120
            elif value == pml.OID_POWER_SETTINGS_3HR:
                find = 180

            index = self.DurationComboBox.findData(find)

            if index != -1:
                self.DurationComboBox.setCurrentIndex(index)



    def getPowerSettingsPML(self):
        pml_result_code, value = self.dev.getPML(pml.OID_POWER_SETTINGS)
        self.dev.closePML()
        log.debug("Current power settings: %s" % value)
        return value


    def setPowerSettingsPML(self, value):
        log.debug("Setting power setting to %s" % value)
        pml_result_code = self.dev.setPML(pml.OID_POWER_SETTINGS, value)
        self.dev.closePML()

    # #####################


    def DurationComboBox_activated(self, i):
        if i == -1:
            return
        v, ok = value_int(self.DurationComboBox.itemData(i))
        if not ok:
            return
        if self.power_settings == POWER_SETTINGS_EPML:
            beginWaitCursor()
            try:
                self.setPowerSettingsEPML(string.zfill(v, 3))
            finally:
                endWaitCursor()

        elif self.power_settings == POWER_SETTINGS_PML:
            beginWaitCursor()
            try:
                self.setPowerSettingsPML(self.getPMLSettingsValue(v))
            finally:
                endWaitCursor()


    def getPMLSettingsValue(self, v):
        x = pml.OID_POWER_SETTINGS_15MIN

        if v == 15:
            x = pml.OID_POWER_SETTINGS_15MIN
        elif v == 30:
            x = pml.OID_POWER_SETTINGS_30MIN
        elif v == 45:
            x = pml.OID_POWER_SETTINGS_45MIN
        elif v == 60:
            x = pml.OID_POWER_SETTINGS_1HR
        elif v == 120:
            x = pml.OID_POWER_SETTINGS_2HR
        elif v == 180:
            x = pml.OID_POWER_SETTINGS_3HR

        return x


    def DeviceUriComboBox_noDevices(self):
        FailureUI(self, self.__tr("<b>No devices that support device setup found.</b>"))
        self.close()


    def CancelButton_clicked(self):
        if self.dev is not None:
            self.dev.close()

        self.close()


#    def ApplyButton_clicked(self):
#        pass

    #
    # Misc
    #

    def __tr(self,s,c = None):
        return qApp.translate("DeviceSetupDialog",s,c)


