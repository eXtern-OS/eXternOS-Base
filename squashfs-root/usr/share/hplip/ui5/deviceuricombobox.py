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

# Std Lib

# Local
from base.g import *
from .ui_utils import *
from base import device
from base.sixext import  to_unicode

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


DEVICEURICOMBOBOX_TYPE_PRINTER_ONLY = 0
DEVICEURICOMBOBOX_TYPE_FAX_ONLY = 1
DEVICEURICOMBOBOX_TYPE_PRINTER_AND_FAX = 2


class DeviceUriComboBox(QWidget):
    DeviceUriComboBox_oneDevice = pyqtSignal()
    DeviceUriComboBox_noDevices = pyqtSignal()
    DeviceUriComboBox_currentChanged = pyqtSignal(str)
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.device_uri = ''
        self.initial_device = None
        self.updating = False
        self.typ = DEVICEURICOMBOBOX_TYPE_PRINTER_ONLY
        self.filter = None
        self.devices = None

        self.user_settings = UserSettings()
        self.user_settings.load()
        self.user_settings.debug()

        self.initUi()


    def initUi(self):
        HBoxLayout = QHBoxLayout(self)
        HBoxLayout.setObjectName("HBoxLayout")

        self.NameLabel = QLabel(self)
        self.NameLabel.setObjectName("NameLabel")
        HBoxLayout.addWidget(self.NameLabel)

        SpacerItem = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)
        HBoxLayout.addItem(SpacerItem)

        self.ComboBox = QComboBox(self)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ComboBox.sizePolicy().hasHeightForWidth())
        self.ComboBox.setSizePolicy(sizePolicy)
        self.ComboBox.setObjectName("ComboBox")
        HBoxLayout.addWidget(self.ComboBox)

        self.NameLabel.setText(self.__tr("Device:"))

#        self.connect(self.ComboBox, SIGNAL("currentIndexChanged(int)"),
#            self.ComboBox_currentIndexChanged)

        # self.connect(self.ComboBox, SIGNAL("currentIndexChanged(const QString &)"),
        #     self.ComboBox_currentIndexChanged)
        self.ComboBox.currentIndexChanged["const QString &"].connect(self.ComboBox_currentIndexChanged)

    def setType(self, typ):
        if typ in (DEVICEURICOMBOBOX_TYPE_PRINTER_ONLY,
                   DEVICEURICOMBOBOX_TYPE_FAX_ONLY,
                   DEVICEURICOMBOBOX_TYPE_PRINTER_AND_FAX):
            self.typ = typ


    def setFilter(self, filter):
        self.filter = filter


    def setInitialDevice(self, device_uri):
        self.initial_device = device_uri


    def setDevices(self):
        if self.typ == DEVICEURICOMBOBOX_TYPE_PRINTER_ONLY:
            be_filter = ['hp']

        elif self.typ == DEVICEURICOMBOBOX_TYPE_FAX_ONLY:
            be_filter = ['hpfax']
            self.NameLabel.setText(self.__tr("Fax Device:"))

        else: # DEVICEURICOMBOBOX_TYPE_PRINTER_AND_FAX
            be_filter = ['hp', 'hpfax']

        self.devices = device.getSupportedCUPSDevices(be_filter, self.filter)
        return len(self.devices)


    def updateUi(self):
        if self.devices is None:
            self.setDevices()

        self.device_index = {}

        if self.devices:
            if self.initial_device is None:
                #self.initial_device = user_conf.get('last_used', 'device_uri')
                self.initial_device = self.user_settings.last_used_device_uri

            self.updating = True
            try:
                k = 0
                for i, d in enumerate(self.devices):
                    self.ComboBox.insertItem(i, d)

                    if self.initial_device is not None and d == self.initial_device:
                        self.initial_device = None
                        k = i

                self.ComboBox.setCurrentIndex(-1)
            finally:
                self.updating = False

            self.ComboBox.setCurrentIndex(k)

            if len(self.devices) == 1:
                # self.emit(SIGNAL("DeviceUriComboBox_oneDevice"))
                self.DeviceUriComboBox_oneDevice.emit()

        else:
            # self.emit(SIGNAL("DeviceUriComboBox_noDevices"))
            self.DeviceUriComboBox_noDevices.emit()

    def ComboBox_currentIndexChanged(self, t):
        if self.updating:
            return

        self.device_uri = to_unicode(t)
        if self.device_uri:
            #user_conf.set('last_used', 'device_uri', self.device_uri)
            self.user_settings.last_used_device_uri = self.device_uri
            self.user_settings.save()

            # self.emit(SIGNAL("DeviceUriComboBox_currentChanged"), self.device_uri)
            self.DeviceUriComboBox_currentChanged.emit(self.device_uri)

    def __tr(self,s,c = None):
        return qApp.translate("DeviceUriComboBox",s,c)
