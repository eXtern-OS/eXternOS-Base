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

# Local
from base.g import *
from base import device, utils
#from prnt import cups
from base.codes import *
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Ui
from .makecopiesdialog_base import Ui_Dialog


class MakeCopiesDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, device_uri):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.device_uri = device_uri
        self.initUi()
        QTimer.singleShot(0, self.updateUi)


    def initUi(self):
        # connect signals/slots
        self.CancelButton.clicked.connect(self.CancelButton_clicked)
        self.CopyButton.clicked.connect(self.CopyButton_clicked)
        self.DeviceComboBox.DeviceUriComboBox_noDevices.connect(self.DeviceUriComboBox_noDevices)
        self.DeviceComboBox.DeviceUriComboBox_currentChanged.connect(self.DeviceUriComboBox_currentChanged)
        self.DeviceComboBox.setFilter({'copy-type': (operator.gt, 0)})

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
        FailureUI(self, self.__tr("<b>No devices that support PC initiated copy found.</b><p>Click <i>OK</i> to exit.</p>"))
        self.close()

    def CancelButton_clicked(self):
        self.close()


    def CopyButton_clicked(self):
        pass

    #
    # Misc
    #

    def __tr(self,s,c = None):
        return qApp.translate("MakeCopiesDialog",s,c)


