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
import sys

# Local
from base.g import *
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


LOADPAPER_TYPE_PLAIN_PAPER = 0
LOADPAPER_TYPE_PHOTO_PAPER = 1


class LoadPaperGroupBox(QGroupBox):
    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.initUi()
        self.typ = LOADPAPER_TYPE_PLAIN_PAPER
        self.button_name = self.__tr("Next >")


    def initUi(self):
        #print "LoadPaperWidget.initUi()"

        self.GridLayout = QGridLayout(self)
        self.GridLayout.setObjectName("GridLayout")

        self.LoadPaperPix = QLabel(self)

        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.LoadPaperPix.sizePolicy().hasHeightForWidth())
        self.LoadPaperPix.setSizePolicy(sizePolicy)
        self.LoadPaperPix.setMinimumSize(QSize(96,96))
        self.LoadPaperPix.setMaximumSize(QSize(96,96))
        #self.LoadPaperPix.setFrameShape(QFrame.Box)
        self.LoadPaperPix.setObjectName("LoadPaperPix")
        self.GridLayout.addWidget(self.LoadPaperPix,0,0,1,1)

        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.GridLayout.addItem(spacerItem,0,1,1,1)

        self.Text = QLabel(self)

        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Text.sizePolicy().hasHeightForWidth())
        self.Text.setSizePolicy(sizePolicy)
        self.Text.setWordWrap(True)
        self.Text.setObjectName("Text")
        self.GridLayout.addWidget(self.Text,0,2,1,1)

        self.LoadPaperPix.setPixmap(load_pixmap("load_paper", "other"))


    def updateUi(self):
        #print "LoadPaperWidget.updateUi()"
        if self.typ == LOADPAPER_TYPE_PLAIN_PAPER:
            paper_name = self.__tr("plain paper")
        else:
            paper_name = self.__tr("photo paper")

        self.Text.setText(self.__tr("Please load <b>%s</b> in the printer and then click <i>%s</i> to continue." %(paper_name, self.button_name)))


    def setType(self, typ):
        if typ in (LOADPAPER_TYPE_PHOTO_PAPER, LOADPAPER_TYPE_PHOTO_PAPER):
            self.typ = typ


    def setButtonName(self, b):
        self.button_name = b


    def __tr(self,s,c = None):
        return qApp.translate("LoadPaperWidget",s,c)
