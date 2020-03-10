# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2015 HP Development Company, L.P.
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
from base.sixext import  to_unicode

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class FABGroupTable(QTableWidget):
    
    namesAddedToGroup = pyqtSignal()

    def __init__(self, parent):
        QTableWidget.__init__(self, parent)
        
        self.db = None
        
        
    def setDatabase(self, db):
        self.db = db
        

    def dragMoveEvent(self, e):
        item = self.itemAt(e.pos())
        if item is not None:
            group = to_unicode(item.text())
            
            if group  == to_unicode('All'):
                e.ignore()
                return

            names = to_unicode(e.mimeData().data(to_unicode('text/plain'))).split(to_unicode('|'))
            group_members = self.db.group_members(group)
            
            if not group_members:
                e.accept()
                return
            
            for n in names:
                if n not in group_members:
                    e.accept()
                    return
                
        e.ignore()
        
        
    def dropMimeData(self, row, col, data, action):
        items = to_unicode(data.data(to_unicode('text/plain'))).split(to_unicode('|'))
        # self.emit(SIGNAL("namesAddedToGroup"), row, items)
        self.namesAddedToGroup.emit(row, items)
        return False
        
        
    def mimeTypes(self):
        return QStringList([to_unicode('text/plain')])
        
        
