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
import os.path

# Local
from base.g import *
from base import device
from prnt import cups
from base.codes import *
from base.sixext import  to_unicode
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Ui
from .infodialog_base import Ui_Dialog
from .deviceuricombobox import DEVICEURICOMBOBOX_TYPE_PRINTER_AND_FAX


class InfoDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, device_uri):
        QDialog.__init__(self, parent)
        self.device_uri = device_uri
        #self.tabs = []
        self.setupUi(self)
        self.initUi()

        QTimer.singleShot(0, self.updateUi)


    def initUi(self):
        # connect signals/slots
        self.CancelButton.clicked.connect(self.CancelButton_clicked)
        self.DeviceComboBox.DeviceUriComboBox_noDevices.connect(self.DeviceUriComboBox_noDevices)
        self.DeviceComboBox.DeviceUriComboBox_currentChanged.connect(self.DeviceUriComboBox_currentChanged)

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))

        if self.device_uri:
            self.DeviceComboBox.setInitialDevice(self.device_uri)

        self.DeviceComboBox.setType(DEVICEURICOMBOBOX_TYPE_PRINTER_AND_FAX)

        self.headers = [self.__tr("Key"), self.__tr("Value")]
        self.history_headers = [self.__tr("Date/Time"), None,
                                self.__tr("Event Code"), self.__tr("Description"),
                                self.__tr("User"), self.__tr("CUPS Job ID"),
                                self.__tr("Doc. Title")]


    def updateUi(self):
        self.DeviceComboBox.updateUi()
        #self.updateInfoTable()


    def updateInfoTable(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.DynamicTableWidget.clear()
        self.DynamicTableWidget.setRowCount(0)
        self.DynamicTableWidget.setColumnCount(0)
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled

        while self.TabWidget.count() > 3:
            self.TabWidget.removeTab(3)

        self.DynamicTableWidget.clear()
        self.DynamicTableWidget.setRowCount(0)
        self.DynamicTableWidget.setColumnCount(len(self.headers))
        self.DynamicTableWidget.setHorizontalHeaderLabels(self.headers)

        #
        # Static Data
        #

        try:
            d = device.Device(self.device_uri, None)
        except Error:
            QApplication.restoreOverrideCursor()
            FailureUI(self, self.__tr("<b>Unable to open device %s.</b>"%(self.device_uri)))
            #self.close()
            return

        self.StaticTableWidget.clear()

        self.StaticTableWidget.setColumnCount(len(self.headers))
        self.StaticTableWidget.setHorizontalHeaderLabels(self.headers)

        mq_keys = list(d.mq.keys())
        mq_keys.sort()

        self.StaticTableWidget.setRowCount(len(mq_keys))

        for row, key in enumerate(mq_keys):
            i = QTableWidgetItem(str(key))
            i.setFlags(flags)
            self.StaticTableWidget.setItem(row, 0, i)

            i = QTableWidgetItem(str(d.mq[key]))
            i.setFlags(flags)
            self.StaticTableWidget.setItem(row, 1, i)

        self.StaticTableWidget.resizeColumnToContents(0)
        self.StaticTableWidget.resizeColumnToContents(1)
        self.StaticTableWidget.setSortingEnabled(True)
        self.StaticTableWidget.sortItems(0)

        #
        # Dynamic Data
        #

        try:
            try:
                d.open()
                d.queryDevice()
            except Error as e:
                QApplication.restoreOverrideCursor()
                FailureUI(self, self.__tr("<b>Unable to open device %s.</b>"%(self.device_uri)))
                #self.close()
                return

            dq_keys = list(d.dq.keys())
            dq_keys.sort()

            self.DynamicTableWidget.setRowCount(len(dq_keys))

            for row, key in enumerate(dq_keys):
                i = QTableWidgetItem(str(key))
                i.setFlags(flags)
                self.DynamicTableWidget.setItem(row, 0, i)

                i = QTableWidgetItem(str(d.dq[key]))
                i.setFlags(flags)
                self.DynamicTableWidget.setItem(row, 1, i)


            self.DynamicTableWidget.resizeColumnToContents(0)
            self.DynamicTableWidget.resizeColumnToContents(1)
            self.DynamicTableWidget.setSortingEnabled(True)
            self.DynamicTableWidget.sortItems(0)

        finally:
            d.close()

        #
        # History Table
        #

        self.HistoryTableWidget.clear()
        self.HistoryTableWidget.setRowCount(0)

        if d.device_type == DEVICE_TYPE_FAX:
            self.history_headers[1] = self.__tr("Fax")
        else:
            self.history_headers[1] = self.__tr("Printer")

        self.HistoryTableWidget.setColumnCount(len(self.history_headers))
        self.HistoryTableWidget.setHorizontalHeaderLabels(self.history_headers)

        history = d.queryHistory()
        history.reverse()
        self.HistoryTableWidget.setRowCount(len(history))

        for row, h in enumerate(history):
            dt = QDateTime()
            dt.setTime_t(int(h.timedate))
            dt = value_str(dt)

            ess = device.queryString(h.event_code, 0)

            for col, t in enumerate([dt, h.printer_name,
                           to_unicode(h.event_code), ess,
                           h.username, to_unicode(h.job_id),
                           h.title]):

                i = QTableWidgetItem(str(t))
                i.setFlags(flags)
                self.HistoryTableWidget.setItem(row, col, i)

        self.HistoryTableWidget.resizeColumnToContents(0)
        self.HistoryTableWidget.resizeColumnToContents(1)
        self.HistoryTableWidget.setSortingEnabled(True)
        self.HistoryTableWidget.sortItems(0)

        #
        # Printer Data
        #

        printers = cups.getPrinters()

        for p in printers:
            if p.device_uri == self.device_uri:
                Tab = QWidget()
                Tab.setObjectName(str(p.name))

                GridLayout = QGridLayout(Tab)
                GridLayout.setObjectName(str("GridLayout-%s" % p.name))

                Table = QTableWidget(Tab)
                Table.setAlternatingRowColors(True)
                Table.setSelectionMode(QAbstractItemView.SingleSelection)
                Table.setSelectionBehavior(QAbstractItemView.SelectRows)
                Table.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)
                Table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
                Table.setGridStyle(Qt.DotLine)
                Table.setObjectName(str("Table-%s" % p.name))
                GridLayout.addWidget(Table, 0, 0, 1, 1)
                self.TabWidget.addTab(Tab, str(p.name))

                Table.setColumnCount(len(self.headers))
                Table.setHorizontalHeaderLabels(self.headers)

                cups.resetOptions()
                cups.openPPD(p.name)
                current_options = dict(cups.getOptions())

                #current_options['cups_error_log_level'] = cups.getErrorLogLevel()

                try:
                    f = open(os.path.expanduser('~/.cups/lpoptions'))
                except IOError as e:
                    log.debug(str(e))
                    current_options['lpoptions_file_data'] = str("(%s)"%str(e))
                else:
                    text = f.read()
                    for d in text.splitlines():
                        if p.name in d:
                            current_options['lpoptions_file_data'] = d
                            break
                    else:
                        current_options['lpoptions_file_data'] = self.__tr("(no data)")

                keys = list(current_options.keys())
                keys.sort()

                Table.setRowCount(len(keys))

                for row, key in enumerate(keys):
                    i = QTableWidgetItem(str(key))
                    i.setFlags(flags)
                    Table.setItem(row, 0, i)

                    if key == 'printer-state':
                        state = int(current_options[key])
                        if state == cups.IPP_PRINTER_STATE_IDLE:
                            i = QTableWidgetItem(self.__tr("idle (%s)"%state))
                        elif state == cups.IPP_PRINTER_STATE_PROCESSING:
                            i = QTableWidgetItem(self.__tr("busy/printing (%s)"%state))
                        elif state == cups.IPP_PRINTER_STATE_STOPPED:
                            i = QTableWidgetItem(self.__tr("stopped (%s)"%state))
                        else:
                            i = QTableWidgetItem(str(state))
                    else:
                        i = QTableWidgetItem(str(current_options[key]))

                    i.setFlags(flags)
                    Table.setItem(row, 1, i)

                Table.resizeColumnToContents(0)
                Table.resizeColumnToContents(1)
                Table.setSortingEnabled(True)
                Table.sortItems(0)

        cups.closePPD()
        self.TabWidget.setCurrentIndex(0)
        QApplication.restoreOverrideCursor()


    def DeviceUriComboBox_currentChanged(self, device_uri):
        self.device_uri = device_uri
        self.updateInfoTable()


    def DeviceUriComboBox_noDevices(self):
        FailureUI(self, self.__tr("<b>No devices found.</b>"))
        self.close()


    def CancelButton_clicked(self):
        self.close()

    #
    # Misc
    #

    def __tr(self,s,c = None):
        return qApp.translate("InfoDialog",s,c)


