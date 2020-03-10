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
#from base import device, utils
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Ui
from .aboutdialog_base import Ui_AboutDlg_base


class AboutDialog(QDialog, Ui_AboutDlg_base):
    def __init__(self, parent, hplip_version, toolbox_version):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.initUi(hplip_version, toolbox_version)


    def initUi(self, hplip_version, toolbox_version):
        self.CloseButton.clicked.connect(self.CloseButton_clicked)

        self.HPLIPVersionText.setText(hplip_version)
        self.ToolboxVersionText.setText(toolbox_version)
        self.PythonPixmap.setPixmap(load_pixmap('powered_by_python.png'))
        self.OsiPixmap.setPixmap(load_pixmap('opensource-75x65.png'))
        self.HPLIPLogo.setPixmap(load_pixmap('hp-tux-printer.png'))



    def CloseButton_clicked(self):
        self.close()



