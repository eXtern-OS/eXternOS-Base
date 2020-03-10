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
from base import device
from prnt import cups
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Ui
from .printsettingsdialog_base import Ui_Dialog
from .printsettingstoolbox import PrintSettingsToolbox
from .printernamecombobox import PRINTERNAMECOMBOBOX_TYPE_PRINTER_AND_FAX, PRINTERNAMECOMBOBOX_TYPE_FAX_ONLY

#signal
import signal

class PrintSettingsDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, printer_name, fax_mode=False):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.fax_mode = fax_mode
        self.printer_name = printer_name
        self.device_uri = None
        self.devices = {}
        self.printer_index = {}

        # User settings
        self.user_settings = UserSettings()
        self.user_settings.load()
        self.user_settings.debug()
        #self.cur_printer = self.user_settings.last_used_printer

        self.initUi(printer_name)
        QTimer.singleShot(0, self.updateUi)


    def initUi(self, printer_name=None):
        self.OptionsToolBox.include_print_options = False

        if self.printer_name:
            self.PrinterName.setInitialPrinter(self.printer_name)

        if self.fax_mode:
            self.PrinterName.setType(PRINTERNAMECOMBOBOX_TYPE_FAX_ONLY)
            self.TitleLabel.setText(self.__tr("Fax Settings"))
        else:
            self.PrinterName.setType(PRINTERNAMECOMBOBOX_TYPE_PRINTER_AND_FAX)

        self.CloseButton.clicked.connect(self.CloseButton_clicked)
        self.PrinterName.PrinterNameComboBox_currentChanged.connect(self.PrinterNameComboBox_currentChanged)

        self.PrinterName.PrinterNameComboBox_noPrinters.connect(self.PrinterNameComboBox_noPrinters)


        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))


    def updateUi(self):
        self.PrinterName.updateUi()


    def PrinterNameComboBox_noPrinters(self):
        FailureUI(self, self.__tr("<b>No printers or faxes found.</b><p>Please setup a printer or fax and try again."))
        self.close()


    def PrinterNameComboBox_currentChanged(self, device_uri, printer_name):
        self.printer_name = printer_name
        self.device_uri = device_uri
        try:
            self.devices[device_uri]
        except KeyError:
            self.devices[device_uri] = device.Device(device_uri)

        self.OptionsToolBox.updateUi(self.devices[device_uri], self.printer_name)


    #
    # Misc
    #

    def CloseButton_clicked(self):
        self.close()


    def __tr(self,s,c = None):
        return qApp.translate("PrintSettingsDialog",s,c)


