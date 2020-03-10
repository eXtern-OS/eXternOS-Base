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



# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class ReadOnlyRadioButton(QRadioButton):
    def __init__(self, parent):
        QRadioButton.__init__(self, parent)
        self.setFocusPolicy(Qt.NoFocus)
        self.clearFocus()


    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            return

        QRadioButton.mousePressEvent(e)


    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            return

        QRadioButton.mouseReleaseEvent(e)


    def mouseMoveEvent(self, e):
        return


    def keyPressEvent(self, e):
        if e.key() not in (Qt.Key_Up, Qt.Key_Left, Qt.Key_Right,
                           Qt.Key_Down, Qt.Key_Escape):
            return

        QRadioButton.keyPressEvent(e)


    def keyReleaseEvent(self, e):
        return
