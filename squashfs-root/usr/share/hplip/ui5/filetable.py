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


# Std Lib
import sys
import os.path
import os
import subprocess

# Local
from base.g import *
from base import utils, magic
from prnt import cups
from base.codes import *
from .ui_utils import *
from base.sixext import to_unicode, to_string_utf8, from_unicode_to_str
# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Other UI
from .mimetypesdialog import MimeTypesDialog


FILETABLE_TYPE_PRINT = 0
FILETABLE_TYPE_FAX = 1



class FileTable(QWidget):

    fileListChanged = pyqtSignal()
    isEmpty = pyqtSignal()
    isNotEmpt = pyqtSignal()

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.parent = parent

        self.initUi()
        self.file_list = []
        self.typ = FILETABLE_TYPE_PRINT
        self.selected_filename = None
        self.fax_add_callback = None
        self.allowable_mime_types = cups.getAllowableMIMETypes()

        self.user_settings = UserSettings()
        self.user_settings.load()
        self.user_settings.debug()

        self.working_dir = self.user_settings.working_dir #user_conf.workingDirectory()



    def initUi(self):
        self.gridlayout = QGridLayout(self)
        self.gridlayout.setObjectName("gridlayout")
        self.FileTable = QTableWidget(self)
        self.FileTable.setObjectName("FileTable")
        self.gridlayout.addWidget(self.FileTable,0,0,1,6)
        self.AddFileButton = QPushButton(self)
        self.AddFileButton.setObjectName("AddFileButton")
        self.gridlayout.addWidget(self.AddFileButton,1,0,1,1)
        self.RemoveFileButton = QPushButton(self)
        self.RemoveFileButton.setObjectName("RemoveFileButton")
        self.gridlayout.addWidget(self.RemoveFileButton,1,1,1,1)
        self.MoveFileUpButton = QPushButton(self)
        self.MoveFileUpButton.setObjectName("MoveFileUpButton")
        self.gridlayout.addWidget(self.MoveFileUpButton,1,2,1,1)
        self.MoveFileDownButton = QPushButton(self)
        self.MoveFileDownButton.setObjectName("MoveFileDownButton")
        self.gridlayout.addWidget(self.MoveFileDownButton,1,3,1,1)
        spacerItem = QSpacerItem(91,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem,1,4,1,1)
        self.ShowTypesButton = QPushButton(self)
        self.ShowTypesButton.setObjectName("ShowTypesButton")
        self.gridlayout.addWidget(self.ShowTypesButton,1,5,1,1)
        self.AddFileButton.setText(self.__tr("Add..."))
        self.AddFileButton.setIcon(QIcon(load_pixmap('list_add', '16x16')))
        self.AddFileButton.clicked.connect(self.AddFileButton_clicked)
        self.RemoveFileButton.setIcon(QIcon(load_pixmap('list_remove', '16x16')))
        self.RemoveFileButton.setText(self.__tr("Remove"))
        self.RemoveFileButton.clicked.connect(self.RemoveFileButton_clicked)
        self.MoveFileUpButton.setText(self.__tr("Move Up"))
        self.MoveFileUpButton.setIcon(QIcon(load_pixmap('up', '16x16')))
        self.MoveFileUpButton.clicked.connect(self.MoveFileUpButton_clicked)
        self.MoveFileDownButton.setText(self.__tr("Move Down"))
        self.MoveFileDownButton.setIcon(QIcon(load_pixmap('down', '16x16')))
        self.MoveFileDownButton.clicked.connect(self.MoveFileDownButton_clicked)
        self.ShowTypesButton.setText(self.__tr("Show Valid Types..."))
        self.ShowTypesButton.setIcon(QIcon(load_pixmap('mimetypes', '16x16')))
        self.ShowTypesButton.clicked.connect(self.ShowTypesButton_clicked)
        self.FileTable.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.connect(self.FileTable, SIGNAL("customContextMenuRequested(const QPoint &)"),
        #    self.FileTable_customContextMenuRequested)
        self.FileTable.customContextMenuRequested["const QPoint &"].connect(self.FileTable_customContextMenuRequested)
        self.headers = [self.__tr("Name"), self.__tr("Type"), self.__tr("Folder/Path")]

        self.FileTable.setSortingEnabled(False)
        self.FileTable.itemSelectionChanged.connect(self.FileTable_itemSelectionChanged)


    def setWorkingDir(self, d):
        if os.path.exists(d):
            self.working_dir = d


    def getWorkingDir(self):
        if self.file_list:
            self.working_dir = os.path.pathname(self.file_list[0][0])
            #user_conf.setWorkingDirectory(self.working_dir)
            self.user_settings.working_dir = self.working_dir
            self.user_settings.save()

        return self.working_dir


    def setType(self, t):
        self.typ = t
        if self.typ == FILETABLE_TYPE_FAX:
            self.headers = [self.__tr("Name"), self.__tr("Type"), self.__tr("Pages")]
            if log.is_debug():
                self.headers.append(self.__tr("File"))


    def setFaxCallback(self, callback):
        self.fax_add_callback = callback


    def isNotEmpty(self):
        return len(self.file_list)


    def FileTable_itemSelectionChanged(self):
        self.selected_filename = self.currentFilename()
        self.setUpDownButtons()


    def updateUi(self, show_add_file_if_empty=True):
        self.FileTable.clear()
        self.FileTable.setRowCount(len(self.file_list))
        self.FileTable.setColumnCount(0)

        if self.file_list:
            # self.emit(SIGNAL("isNotEmpty"))
            self.isNotEmpt.emit()
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            try:
                selected = None
                self.FileTable.setColumnCount(len(self.headers))
                self.FileTable.setHorizontalHeaderLabels(self.headers)
                flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled

                for row, f in enumerate(self.file_list):
                    filename, mime_type, mime_type_desc, title, num_pages = f
                    col = 0

                    if self.typ == FILETABLE_TYPE_FAX:
                        if title:
                            i = QTableWidgetItem(title)
                        else:
                            i = QTableWidgetItem(os.path.basename(filename))
                    else: # FILETABLE_TYPE_PRINT
                        # Filename (basename)
                        i = QTableWidgetItem(os.path.basename(filename))

                    i.setData(Qt.UserRole, to_unicode(filename))
                    i.setFlags(flags)

                    if self.selected_filename is not None and \
                        self.selected_filename == filename:
                        selected = i

                    self.FileTable.setItem(row, col, i)
                    col += 1

                    # MIME type
                    i = QTableWidgetItem(mime_type_desc)
                    i.setFlags(flags)
                    self.FileTable.setItem(row, col, i)
                    col += 1

                    if self.typ == FILETABLE_TYPE_PRINT:
                        # path/folder
                        i = QTableWidgetItem(os.path.dirname(filename))
                        i.setFlags(flags)
                        self.FileTable.setItem(row, col, i)
                        col += 1

                    if self.typ == FILETABLE_TYPE_FAX:
                        # num pages
                        if num_pages < 1:
                            i = QTableWidgetItem(self.__tr("(unknown)"))
                        else:
                            i = QTableWidgetItem(to_unicode(num_pages))
                        i.setFlags(flags)
                        self.FileTable.setItem(row, col, i)
                        col += 1

                        if self.typ == FILETABLE_TYPE_FAX and log.is_debug():
                            i = QTableWidgetItem(filename)
                            i.setFlags(flags)
                            self.FileTable.setItem(row, col, i)


                self.FileTable.resizeColumnsToContents()

                if selected is None:
                    selected = self.FileTable.item(0, 0)

                selected.setSelected(True)
                self.FileTable.setCurrentItem(selected)

            finally:
                QApplication.restoreOverrideCursor()

            self.RemoveFileButton.setEnabled(True)
            self.RemoveFileButton.setIcon(QIcon(load_pixmap('list_remove', '16x16')))

            self.setUpDownButtons()

        else:
            # self.emit(SIGNAL("isEmpty"))
            self.isEmpty.emit()
            self.RemoveFileButton.setEnabled(False)
            self.setUpDownButtons()

            if show_add_file_if_empty:
                # self.AddFileButton.emit(SIGNAL("clicked()"))
                self.AddFileButton.clicked.emit()


    def setUpDownButtons(self):
        if self.file_list:
            i = self.FileTable.currentRow()

            if len(self.file_list) > 1 and i != len(self.file_list)-1:
                self.MoveFileDownButton.setEnabled(True)
            else:
                self.MoveFileDownButton.setEnabled(False)

            if len(self.file_list) > 1 and i != 0:
                self.MoveFileUpButton.setEnabled(True)
            else:
                self.MoveFileUpButton.setEnabled(False)

        else:
            self.MoveFileDownButton.setEnabled(False)
            self.MoveFileUpButton.setEnabled(False)


    def AddFileButton_clicked(self):
        if self.typ == FILETABLE_TYPE_PRINT:
            s = self.__tr("Select File(s) to Print")
        else:
            stat = ''
            try :
                p = subprocess.Popen('getenforce', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stat, err = p.communicate()
                stat = to_string_utf8(stat)
            except OSError :
                pass
            except :
                log.exception()
            # if stat.strip('\n') == 'Enforcing' :
            #     FailureUI(self, self.__tr("<b>Unable to add file. Please disable SeLinux.</b><p>Either disable it manually or run hp-doctor from terminal.</p>"),
            #         self.__tr("HP Device Manager"))
            #     return

            s = self.__tr("Select File(s) to Send")

        files = QFileDialog.getOpenFileNames(self, s, self.working_dir, self.__tr("All files (*)"))

        files = [to_unicode(f) for f in files[0]]
        # log.error(files)
        if files:
            self.addFileList(files)

            if self.typ == FILETABLE_TYPE_PRINT:
                self.updateUi(False)


    def addFileList(self, file_list):
        for f in file_list:
            self.addFileFromUI(f)


    def addFileFromUI(self, f, title='', num_pages=0):
        f = os.path.abspath(os.path.expanduser(f))
        log.debug("Trying to add file: %s" % f)
        if os.path.exists(f) and os.access(f, os.R_OK):
            mime_type = magic.mime_type(f)
            mime_type_desc = mime_type
            log.debug("File type of file %s: %s" % (f, mime_type))
            try:
                mime_type_desc = MIME_TYPES_DESC[mime_type][0]
            except KeyError:
                if self.typ == FILETABLE_TYPE_PRINT:
                    FailureUI(self, self.__tr("<b>You are trying to add a file  that cannot be directly printed with this utility.</b><p>To print this file, use the print command in the application that created it.<p>Note: Click <i>Show Valid Types...</i> to view a list of compatible file types that can be directly printed from this utility."),
                        self.__tr("HP Device Manager"))
                else:
                    FailureUI(self, self.__tr("<b>You are trying to add a file  that cannot be directly faxed with this utility.</b><p>To fax this file, use the print command in the application that created it (using the appropriate fax print queue).<p>Note: Click <i>Show Valid Types...</i> to view a list of compatible file types that can be directly added to the fax file list in this utility."),
                        self.__tr("HP Device Manager"))
            else:
                if self.typ == FILETABLE_TYPE_PRINT:
                    self.addFile(f, mime_type, mime_type_desc, title, num_pages)
                else:
                    self.fax_add_callback(f)
        else:
            FailureUI(self, self.__tr("<b>Unable to add file '%s' to file list (file not found or insufficient permissions).</b><p>Check the file name and try again."%f),
                      self.__tr("HP Device Manager"))


    def addFile(self, f, mime_type, mime_type_desc, title, num_pages):
        log.debug("Adding file %s (%s,%s,%s,%d)" % (f, mime_type, mime_type_desc, title, num_pages))
        self.file_list.append((f, mime_type, mime_type_desc, title, num_pages))
        self.updateUi()
        # self.emit(SIGNAL("fileListChanged"))
        self.fileListChanged.emit()


    def currentFilename(self):
        i = self.FileTable.item(self.FileTable.currentRow(), 0)
        if i is None:
            return None

        return value_str(i.data(Qt.UserRole))


    def RemoveFileButton_clicked(self):
        filename = self.currentFilename()
        if filename is None:
            return

        return self.removeFile(filename)


    def removeFile(self, filename):
        temp = self.file_list[:]
        index = 0
        for f, mime_type, mime_type_desc, title, num_pages in temp:
            if f == to_unicode(filename):
                del self.file_list[index]
                # self.emit(SIGNAL("fileListChanged"))
                self.fileListChanged.emit()
                self.updateUi(False)
                break
            index += 1


    def removeFileByMIMEType(self, mime_type):
        temp = self.file_list[:]
        index = 0
        for filename, m, mime_type_desc, title, num_pages in temp:
            if m == mime_type:
                del self.file_list[index]
                # self.emit(SIGNAL("fileListChanged"))
                self.fileListChanged.emit()
                self.updateUi(False)
                break
            index += 1


    def isMIMETypeInList(self, mime_type):
        for filename, m, mime_type_desc, title, num_pages in self.file_list:
            if m == mime_type:
                return True

        return False


    def ShowTypesButton_clicked(self):
        x = {}
        for a in self.allowable_mime_types:
            x[a] = MIME_TYPES_DESC.get(a, ('Unknown', 'n/a'))

        dlg = MimeTypesDialog(x, self)
        dlg.exec_()


    def MoveFileUpButton_clicked(self):
        filename = self.currentFilename()
        if filename is None:
            return

        utils.list_move_up(self.file_list, filename, self.__compareFilenames)
        self.updateUi()


    def MoveFileDownButton_clicked(self):
        filename = self.currentFilename()
        if filename is None:
            return

        utils.list_move_down(self.file_list, filename, self.__compareFilenames)
        self.updateUi()


    def __compareFilenames(self, a, b):
        return a[0] == b


    def FileTable_customContextMenuRequested(self, p):
        print(p)


    def __tr(self,s,c = None):
        return qApp.translate("FileTable",s,c)



