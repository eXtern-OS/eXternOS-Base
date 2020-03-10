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


# Local
from base.g import *
from base import device, utils
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Ui
from .nodevicesdialog_base import Ui_NoDevicesDialog_base


class NoDevicesDialog(QDialog, Ui_NoDevicesDialog_base):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.initUi()


    def initUi(self):
        self.SetupButton.clicked.connect(self.SetupButton_clicked)
        self.CUPSButton.clicked.connect(self.CUPSButton_clicked)
        self.CloseButton.clicked.connect(self.CloseButton_clicked)
        self.Icon.setPixmap(load_pixmap("warning", '32x32'))


    def SetupButton_clicked(self):
        self.close()

        if utils.which('hp-setup'):
            cmd = 'hp-setup -u'
        else:
            cmd = 'python ./setup.py -u'

        log.debug(cmd)
        utils.run(cmd)

        try:
            self.parent().rescanDevices()
        except Error:
            QMessageBox.critical(self,
                                    self.windowTitle(),
                                    self.__tr("<b>An error occurred.</b><p>Please re-start the Device Manager and try again."),
                                    QMessageBox.Ok,
                                    QMessageBox.NoButton,
                                    QMessageBox.NoButton)


    def CUPSButton_clicked(self):
        self.close()
        utils.openURL("http://localhost:631/admin")


    def CloseButton_clicked(self):
        self.close()



