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
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Ui
from .pluginlicensedialog_base import Ui_Dialog



class PluginLicenseDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, license_txt):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.license_txt = license_txt
        self.initUi()


    def initUi(self):
        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))

        self.LicenseTextEdit.setText(self.license_txt)


