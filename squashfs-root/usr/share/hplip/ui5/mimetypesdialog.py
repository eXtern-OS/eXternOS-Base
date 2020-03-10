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
from base.codes import *
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .mimetypesdialog_base import Ui_MimeTypesDialog_base



class MimeTypesDialog(QDialog, Ui_MimeTypesDialog_base):
    def __init__(self, mime_types, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.TypesTableWidget.setRowCount(len(mime_types))
        t = list(mime_types.keys())
        t.sort()
        for row, m in enumerate(t):
            i = QTableWidgetItem(m)
            self.TypesTableWidget.setItem(row, 0, i)

            i = QTableWidgetItem(mime_types[m][0])
            self.TypesTableWidget.setItem(row, 1, i)

            i = QTableWidgetItem(mime_types[m][1])
            self.TypesTableWidget.setItem(row, 2, i)

        self.TypesTableWidget.resizeColumnsToContents()


    def __tr(self,s,c = None):
        return qApp.translate("SettingsDialog",s,c)


