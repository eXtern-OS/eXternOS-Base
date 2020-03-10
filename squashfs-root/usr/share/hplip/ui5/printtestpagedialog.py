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
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import signal

# Ui
from .printtestpagedialog_base import Ui_Dialog


class PrintTestPageDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, printer_name):
        QDialog.__init__(self, parent)

        self.printer_name = printer_name
        self.device_uri = ''
        self.setupUi(self)
        self.initUi()

        QTimer.singleShot(0, self.updateUi)


    def initUi(self):
        #print "PrintTestPageDialog.initUi()"
        self.HPLIPTestPageRadioButton.setChecked(True)
        self.LoadPaper.setButtonName(self.__tr("Print Test Page"))

        self.CancelButton.clicked.connect(self.CancelButton_clicked)
        self.PrintTestpageButton.clicked.connect(self.PrintTestpageButton_clicked)

        self.PrinterNameCombo.PrinterNameComboBox_currentChanged.connect(self.PrinterNameCombo_currentChanged)

        self.PrinterNameCombo.PrinterNameComboBox_noPrinters.connect(self.PrinterNameComboBox_noPrinters)
        

        signal.signal(signal.SIGINT, signal.SIG_DFL)

        if self.printer_name:
            self.PrinterNameCombo.setInitialPrinter(self.printer_name)

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))


    def updateUi(self):
        self.PrinterNameCombo.updateUi()
        self.LoadPaper.updateUi()
        #self.updatePrintButton()


    def PrinterNameComboBox_noPrinters(self):
        FailureUI(self, self.__tr("<b>No printers found.</b><p>Please setup a printer and try again."))
        self.close()


    def updatePrintButton(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.PrintTestpageButton.setEnabled(False)
        ok = False
        try:
            try:
                d = device.Device(self.device_uri, self.printer_name)
            except Error as e:
                log.error("Device error (%s)." % e.msg)
            else:
                try:
                    d.open()
                except Error:
                    log.error("Unable to print to printer. Please check device and try again.")
                else:
                    ok = d.isIdleAndNoError()

            self.PrintTestpageButton.setEnabled(ok)

            if not ok:
                QApplication.restoreOverrideCursor()
                FailureUI(self, self.__tr("<b>Unable to communicate with printer %s.</b><p>Please check the printer and try again." % self.printer_name))

            d.close()

        finally:
            QApplication.restoreOverrideCursor()


    def CancelButton_clicked(self):
        self.close()


    def PrinterNameCombo_currentChanged(self, device_uri, printer_name):
        self.printer_name = printer_name
        self.device_uri = device_uri
        self.updatePrintButton()
        #self.updateUi()


    def PrintTestpageButton_clicked(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        ok = False
        try:
            try:
                d = device.Device(self.device_uri, self.printer_name)
            except Error as e:
                log.error("Device error (%s)." % e.msg)
            else:
                try:
                    d.open()
                except Error:
                    log.error("Unable to print to printer. Please check device and try again.")
                else:
                    ok = d.isIdleAndNoError()

        finally:
            QApplication.restoreOverrideCursor()

        if ok:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            try:
                d.printTestPage(self.printer_name)
            finally:
                QApplication.restoreOverrideCursor()

            self.close()

        else:
            FailureUI(self, self.__tr("<b>A error occured sending the test page to printer %s.</b><p>Please check the printer and try again."% self.printer_name))

        d.close()


    def __tr(self, s, c=None):
        return qApp.translate("PrintTestPageDialog", s, c)


