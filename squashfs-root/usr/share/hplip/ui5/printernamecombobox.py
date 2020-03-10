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
#import sys

# Local
from base.g import *
from .ui_utils import *
from base import device
from base.sixext import to_unicode

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


PRINTERNAMECOMBOBOX_TYPE_PRINTER_ONLY = 0
PRINTERNAMECOMBOBOX_TYPE_FAX_ONLY = 1
PRINTERNAMECOMBOBOX_TYPE_PRINTER_AND_FAX = 2


class PrinterNameComboBox(QWidget):

    PrinterNameComboBox_currentChanged = pyqtSignal(str, str)
    PrinterNameComboBox_noPrinters = pyqtSignal()

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.printer_name = ''
        self.device_uri = ''
        self.printer_index = {}
        self.initial_printer = None
        self.updating = False
        self.typ = PRINTERNAMECOMBOBOX_TYPE_PRINTER_ONLY

        self.user_settings = UserSettings()
        self.user_settings.load()
        self.user_settings.debug()

        self.initUi()


    def initUi(self):
        #print "PrinterNameComboBox.initUi()"
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

        self.NameLabel.setText(self.__tr("Printer:"))

        #self.connect(self.ComboBox, SIGNAL("currentIndexChanged(int)"),
        #    self.ComboBox_currentIndexChanged)

        # self.connect(self.ComboBox, SIGNAL("currentIndexChanged(const QString &)"),
        #    self.ComboBox_currentIndexChanged)
        self.ComboBox.currentIndexChanged["const QString &"].connect(self.ComboBox_currentIndexChanged)

    def setType(self, typ):
        if typ in (PRINTERNAMECOMBOBOX_TYPE_PRINTER_ONLY,
                   PRINTERNAMECOMBOBOX_TYPE_FAX_ONLY,
                   PRINTERNAMECOMBOBOX_TYPE_PRINTER_AND_FAX):
            self.typ = typ


    def setInitialPrinter(self, printer_name):
        self.initial_printer = printer_name


    def updateUi(self):
        #print "PrinterNameComboBox.updateUi()"
        if self.typ == PRINTERNAMECOMBOBOX_TYPE_PRINTER_ONLY:
            self.NameLabel.setText(self.__tr("Printer Name:"))
            be_filter = ['hp']

        elif self.typ == PRINTERNAMECOMBOBOX_TYPE_FAX_ONLY:
            self.NameLabel.setText(self.__tr("Fax Name:"))
            be_filter = ['hpfax']

        else: # PRINTERNAMECOMBOBOX_TYPE_PRINTER_AND_FAX
            self.NameLabel.setText(self.__tr("Printer/Fax Name:"))
            be_filter = ['hp', 'hpfax']

        self.printers = device.getSupportedCUPSPrinters(be_filter)
        self.printer_index.clear() # = {}

        if self.printers:
            if self.initial_printer is None:
                #user_conf.get('last_used', 'printer_name')
                self.initial_printer = self.user_settings.last_used_printer

            self.updating = True
            try:
                k = 0
                for i, p in enumerate(self.printers):
                    self.printer_index[p.name] = p.device_uri
                    self.ComboBox.insertItem(i, p.name)

                    if self.initial_printer is not None and to_unicode(p.name).lower() == to_unicode(self.initial_printer).lower():
                        self.initial_printer = None
                        k = i

                self.ComboBox.setCurrentIndex(-1)

            finally:
                self.updating = False

            self.ComboBox.setCurrentIndex(k)
        else:
            # self.emit(SIGNAL("PrinterNameComboBox_noPrinters"))
            self.PrinterNameComboBox_noPrinters.emit()


    def ComboBox_currentIndexChanged(self, t):
        self.printer_name = to_unicode(t)

        if self.updating:
            return

        self.device_uri = self.printer_index[self.printer_name]
        #user_conf.set('last_used', 'printer_name', self.printer_name)
        self.user_settings.last_used_printer = self.printer_name
        self.user_settings.save()

        # self.emit(SIGNAL("PrinterNameComboBox_currentChanged"), self.device_uri, self.printer_name)
        self.PrinterNameComboBox_currentChanged.emit(self.device_uri, self.printer_name)

    def __tr(self,s,c = None):
        return qApp.translate("PrinterNameComboBox",s,c)
