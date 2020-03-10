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

# Std Lib
import operator
import signal

# Local
from base.g import *
from base import device, utils
from prnt import cups
from base.codes import *
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Ui
from .firmwaredialog_base import Ui_Dialog


class FirmwareDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, device_uri):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.device_uri = device_uri
        self.initUi()
        QTimer.singleShot(0, self.updateUi)


    def initUi(self):
        self.DeviceComboBox.setFilter({'fw-download' : (operator.gt, 0)})

        self.DeviceComboBox.DeviceUriComboBox_noDevices.connect(self.DeviceUriComboBox_noDevices)
        self.DeviceComboBox.DeviceUriComboBox_currentChanged.connect(self.DeviceUriComboBox_currentChanged)
        self.CancelButton.clicked.connect(self.close)
        self.DownloadFirmwareButton.clicked.connect(self.downloadFirmware)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))

        if self.device_uri:
            self.DeviceComboBox.setInitialDevice(self.device_uri)


    def updateUi(self):
        self.DeviceComboBox.updateUi()


    def DeviceUriComboBox_currentChanged(self, device_uri):
        self.device_uri = device_uri
        # Update


    def DeviceUriComboBox_noDevices(self):
        FailureUI(self, self.__tr("<b>No devices that support firmware download found.</b>"))
        self.close()


    def downloadFirmware(self):
        d = None

        try:
            try:
                d = device.Device(self.device_uri)
            except Error:
                CheckDeviceUI(self)
                return

            try:
                d.open()
            except Error:
                CheckDeviceUI(self)
            else:
                if d.isIdleAndNoError():
                    ok = d.downloadFirmware()

                else:
                    CheckDeviceUI(self)

        finally:
            if d is not None:
                d.close()

        self.close()


    def __tr(self,s,c = None):
        return qApp.translate("FirmwareDialog",s,c)

