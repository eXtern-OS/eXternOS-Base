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
from prnt import cups
from base.codes import *
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Ui
from .printdialog_base import Ui_Dialog
from .filetable import FileTable, FILETABLE_TYPE_PRINT
from .printernamecombobox import PRINTERNAMECOMBOBOX_TYPE_PRINTER_ONLY

#signal
import signal

PAGE_FILE = 0
PAGE_OPTIONS = 1
PAGE_MAX = 1


class PrintDialog(QDialog, Ui_Dialog):

    def __init__(self, parent, printer_name, args=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.printer_name = printer_name

        # User settings
        self.user_settings = UserSettings()
        self.user_settings.load()
        self.user_settings.debug()

        self.initUi()

        self.file_list = []
        if args is not None:
            for a in args:
                self.Files.addFileFromUI(os.path.abspath(a))

        self.devices = {}


        QTimer.singleShot(0, self.updateFilePage)


    def initUi(self):
        self.OptionsToolBox.include_job_options = True

        # connect signals/slots
        self.CancelButton.clicked.connect(self.CancelButton_clicked)
        self.BackButton.clicked.connect(self.BackButton_clicked)
        self.NextButton.clicked.connect(self.NextButton_clicked)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self.initFilePage()
        self.initOptionsPage()

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))

        if self.printer_name:
            self.PrinterName.setInitialPrinter(self.printer_name)

        self.StackedWidget.setCurrentIndex(0)


    #
    # File Page
    #

    def initFilePage(self):
        self.Files.setType(FILETABLE_TYPE_PRINT)
        #self.Files.setWorkingDir(user_conf.workingDirectory())
        self.Files.setWorkingDir(self.user_settings.working_dir)
        self.Files.isEmpty.connect(self.Files_isEmpty)
        self.Files.isNotEmpt.connect(self.Files_isNotEmpty)


    def updateFilePage(self):
        self.NextButton.setText(self.__tr("Next >"))
        self.NextButton.setEnabled(self.Files.isNotEmpty())
        self.BackButton.setEnabled(False)
        self.updateStepText(PAGE_FILE)
        self.Files.updateUi()

    def Files_isEmpty(self):
        self.NextButton.setEnabled(False)


    def Files_isNotEmpty(self):
        self.NextButton.setEnabled(True)


    #
    # Options Page
    #

    def initOptionsPage(self):
        self.BackButton.setEnabled(True)
        self.PrinterName.setType(PRINTERNAMECOMBOBOX_TYPE_PRINTER_ONLY)

        self.PrinterName.PrinterNameComboBox_currentChanged.connect(self.PrinterNameComboBox_currentChanged)

        self.PrinterName.PrinterNameComboBox_noPrinters.connect(self.PrinterNameComboBox_noPrinters)


    def updateOptionsPage(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            self.PrinterName.updateUi()
            self.BackButton.setEnabled(True)
            num_files = len(self.Files.file_list)

            if  num_files > 1:
                self.NextButton.setText(self.__tr("Print %s Files"%num_files))
            else:
                self.NextButton.setText(self.__tr("Print File"))

            self.updateStepText(PAGE_OPTIONS)
            # TODO: Enable print button only if printer is accepting and all options are OK (esp. page range)
        finally:
            QApplication.restoreOverrideCursor()


    def PrinterNameComboBox_currentChanged(self, device_uri, printer_name):
        try:
            self.devices[device_uri]
        except KeyError:
            self.devices[device_uri] = device.Device(device_uri)

        self.OptionsToolBox.updateUi(self.devices[device_uri], printer_name)


    def PrinterNameComboBox_noPrinters(self):
        FailureUI(self, self.__tr("<b>No printers found.</b><p>Please setup a printer and try again."))
        self.close()


    #
    # Print
    #

    def executePrint(self):
        for cmd in self.OptionsToolBox.getPrintCommands(self.Files.file_list):
            log.debug(cmd)
            status, output = utils.run(cmd)
            if status != 0:
                FailureUI(self, self.__tr("<b>Print command failed with status code %s.</b><p>%s</p>"%(status,cmd)))

        self.close()
        #print file('/home/dwelch/.cups/lpoptions', 'r').read()

    #
    # Misc
    #

    def CancelButton_clicked(self):
        self.close()


    def BackButton_clicked(self):
        p = self.StackedWidget.currentIndex()
        if p == PAGE_OPTIONS:
            self.StackedWidget.setCurrentIndex(PAGE_FILE)
            self.updateFilePage()

        else:
            log.error("Invalid page!") # shouldn't happen!


    def NextButton_clicked(self):
        p = self.StackedWidget.currentIndex()
        if p == PAGE_FILE:
            self.StackedWidget.setCurrentIndex(PAGE_OPTIONS)
            self.updateOptionsPage()

        elif p == PAGE_OPTIONS:
            self.executePrint()


    def updateStepText(self, p):
        self.StepText.setText(self.__tr("Step %d of %d" %(p+1, PAGE_MAX+1)))


    def __tr(self,s,c = None):
        return qApp.translate("PrintDialog",s,c)



