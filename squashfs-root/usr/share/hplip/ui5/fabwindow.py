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

# StdLib

# Local
from base.g import *
from .ui_utils import *
from base.sixext import to_unicode, from_unicode_to_str

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Main window
from .fabwindow_base import Ui_MainWindow

fax_avail = True
try:
    from fax import fax
except ImportError:
    # This can fail on Python < 2.3 due to the datetime module
    log.error("Fax address book disabled - Python 2.3+ required.")
    fax_avail = False



class FABWindow(QMainWindow,  Ui_MainWindow):

    databaseChanged = pyqtSignal([int, str], [int, str, str])
    editingFinished = pyqtSignal()

    def __init__(self, parent):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.group = to_unicode('All') # current group
        self.name = None # current name
        self.updating_group = False
        self.updating_name = False

        self.user_settings = UserSettings()
        self.user_settings.load()
        self.user_settings.debug()

        self.initDB()
        self.initUi()

        QTimer.singleShot(0, self.updateUi)


    def initDB(self):
        self.db =  fax.FaxAddressBook()

        # Fixup data from old-style database
        data = self.db.get_all_records()
        for d in data:
            if to_unicode('All') not in data[d]['groups']:
                data[d]['groups'].append(to_unicode('All'))

        if not data:
            self.db.set('__' + utils.gen_random_uuid(), '', '', '', '', [to_unicode('All')], '')


    def initUi(self):
        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))

        self.NewGroupAction.setIcon(QIcon(load_pixmap('new_group', '24x24')))
        self.NewGroupFromSelectionAction.setIcon(QIcon(load_pixmap('new_group_from_selection', '24x24')))
        self.RenameGroupAction.setIcon(QIcon(load_pixmap('rename_group', '24x24')))
        self.RemoveGroupAction.setIcon(QIcon(load_pixmap('remove_group', '24x24')))
        self.NewNameAction.setIcon(QIcon(load_pixmap('new_user', '24x24')))
        self.RemoveNameAction.setIcon(QIcon(load_pixmap('remove_user', '24x24')))
        self.AddToGroupAction.setIcon(QIcon(load_pixmap('add_to_group', '24x24')))
        self.RemoveFromGroupAction.setIcon(QIcon(load_pixmap('remove_from_group', '24x24')))

        self.QuitAction.triggered.connect(self.close)
        self.NewGroupAction.triggered.connect(self.NewGroupAction_triggered)
        self.NewGroupFromSelectionAction.triggered.connect(self.NewGroupFromSelectionAction_triggered)
        self.RenameGroupAction.triggered.connect(self.RenameGroupAction_triggered)
        self.RemoveGroupAction.triggered.connect(self.RemoveGroupAction_triggered)
        self.NewNameAction.triggered.connect(self.NewNameAction_triggered)
        self.RemoveNameAction.triggered.connect(self.RemoveNameAction_triggered)
        self.ImportAction.triggered.connect(self.ImportAction_triggered)
        self.RemoveFromGroupAction.triggered.connect(self.RemoveFromGroupAction_triggered)
        self.AddToGroupAction.triggered.connect(self.AddToGroupAction_triggered)

        self.GroupTableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.NameTableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.Splitter.splitterMoved[int, int].connect(self.Splitter_splitterMoved)
        self.Splitter.setChildrenCollapsible(False)
        self.Splitter.setHandleWidth(self.Splitter.handleWidth()+2)

        self.GroupTableWidget.verticalHeader().hide()
        self.GroupTableWidget.setShowGrid(False)
        self.GroupTableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.NameTableWidget.verticalHeader().hide()
        self.NameTableWidget.setShowGrid(False)

        self.NameTableWidget.setDragEnabled(True)
        self.GroupTableWidget.setAcceptDrops(True)
        self.GroupTableWidget.setDropIndicatorShown(True)

        self.GroupTableWidget.itemSelectionChanged.connect(self.GroupTableWidget_itemSelectionChanged)
        self.NameTableWidget.itemSelectionChanged.connect(self.NameTableWidget_itemSelectionChanged)
        self.NameLineEdit.editingFinished.connect(self.NameLineEdit_editingFinished)
        self.FaxNumberLineEdit.editingFinished.connect(self.FaxNumberLineEdit_editingFinished)
        self.NotesTextEdit.textChanged.connect(self.NotesTextEdit_textChanged)
        # self.NotesTextEdit.editingFinished.connect(self.NotesTextEdit_editingFinished)
        self.GroupTableWidget.namesAddedToGroup.connect(self.GroupTableWidget_namesAddedToGroup)


        self.FaxNumberLineEdit.setValidator(PhoneNumValidator(self.FaxNumberLineEdit))
        self.NameLineEdit.setValidator(AddressBookNameValidator(self.db, self.NameLineEdit))

        self.GroupTableWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.GroupTableWidget.addAction(self.NewGroupAction)
        self.GroupTableWidget.addAction(self.NewGroupFromSelectionAction)
        self.GroupTableWidget.addAction(self.RenameGroupAction)
        self.GroupTableWidget.addAction(self.RemoveGroupAction)

        self.NameTableWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.NameTableWidget.addAction(self.NewNameAction)
        self.NameTableWidget.addAction(self.AddToGroupAction)
        self.NameTableWidget.addAction(self.RemoveFromGroupAction)
        self.NameTableWidget.addAction(self.RemoveNameAction)
        self.NameTableWidget.addAction(self.NewGroupFromSelectionAction)

        self.GroupTableWidget.setDatabase(self.db)


    def updateUi(self):
        if not fax_avail:
            FailureUI(self, self.__tr("<b>Fax support disabled.</b><p>Fax support requires Python 2.3."))
            self.close()
            return

        self.updateGroupList()
        self.updateNameList()
        self.updateDetailsFrame()


    def closeEvent(self, e):
        #self.NameLineEdit.emit(SIGNAL("editingFinished()"))
        # self.FaxNumberLineEdit.emit(SIGNAL("editingFinished()"))
        self.FaxNumberLineEdit.editingFinished.emit()
        # self.NotesTextEdit.emit(SIGNAL("editingFinished()"))
        # XXX: qt5port: NotesTextEdit editingFinished requires attention
        # self.NotesTextEdit.editingFinished.emit()
        e.accept()


    def Splitter_splitterMoved(self, pos, index):
        self.GroupTableWidget.setColumnWidth(0, self.GroupTableWidget.width())
        self.NameTableWidget.setColumnWidth(0, self.NameTableWidget.width())


    def updateGroupList(self):
        self.updating_group = True
        all, k = None, None
        try:
            headerItem = QTableWidgetItem()
            headerItem.setText(self.__tr("Group"))
            self.GroupTableWidget.clear()
            self.GroupTableWidget.setColumnCount(1)
            self.GroupTableWidget.setHorizontalHeaderItem(0, headerItem)
            self.GroupTableWidget.setColumnWidth(0, self.GroupTableWidget.width())

            groups = self.db.get_all_groups()
            groups.sort()
            self.GroupTableWidget.setRowCount(len(groups))

            # Force All group to top of table
            all = QTableWidgetItem(self.__tr("All"))
            all.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.GroupTableWidget.setItem(0, 0, all)

            j = 1
            for g in groups:
                if g == to_unicode('All'):
                    continue

#                i = QTableWidgetItem(str(g))
                if isinstance(g, int):
                    i = QTableWidgetItem(str(g))
                else:
                    i = QTableWidgetItem(from_unicode_to_str(g))
                

                if g == self.group:
                    k = i

                i.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDropEnabled)
                self.GroupTableWidget.setItem(j, 0, i)
                j += 1


        finally:
            self.updating_group = False

            if k is not None:
                k.setSelected(True)

            elif all is not None:
                all.setSelected(True)


    def GroupTableWidget_itemSelectionChanged(self):
        if not self.updating_group:
            selected_items = self.GroupTableWidget.selectedItems()
            if selected_items:
                self.group = to_unicode(selected_items[0].text())
                self.RemoveGroupAction.setEnabled(self.group != to_unicode('All'))
                self.RenameGroupAction.setEnabled(self.group != to_unicode('All'))
            else: # shouldn't happen?!
                self.RemoveGroupAction.setEnabled(False)
                self.RenameGroupAction.setEnabled(False)
                self.group = None

            self.updateNameList()


    def NameTableWidget_itemSelectionChanged(self):
        if not self.updating_name:
            selected_items = self.NameTableWidget.selectedItems()
            num_selected_items = len(selected_items)

            if num_selected_items == 0:
                self.name = None
                self.RemoveNameAction.setEnabled(False)
                self.NewGroupFromSelectionAction.setEnabled(False)
                self.RemoveFromGroupAction.setEnabled(False)
                self.AddToGroupAction.setEnabled(False)

            elif num_selected_items == 1:
                self.name = to_unicode(selected_items[0].text())
                self.RemoveNameAction.setEnabled(True)
                self.NewGroupFromSelectionAction.setEnabled(True)

                self.RemoveFromGroupAction.setEnabled(self.group != to_unicode('All'))
                self.AddToGroupAction.setEnabled(True) #self.group != u'All')

            else: # > 1
                self.RemoveNameAction.setEnabled(True)
                self.NewGroupFromSelectionAction.setEnabled(True)
                self.RemoveFromGroupAction.setEnabled(self.group != to_unicode('All'))
                self.AddToGroupAction.setEnabled(True) #self.group != u'All')
                self.name = None

            self.updateDetailsFrame()


    def updateNameList(self):
        self.updating_name = True
        m, k = None, None
        try:
            headerItem = QTableWidgetItem()
            headerItem.setText(self.__tr("Name"))
            self.NameTableWidget.clear()
            self.NameTableWidget.setColumnCount(1)
            self.NameTableWidget.setHorizontalHeaderItem(0,headerItem)
            self.NameTableWidget.setColumnWidth(0, self.NameTableWidget.width())

            names = self.db.group_members(self.group)
            filtered_names = [n for n in names if not n.startswith('__')]
            filtered_names.sort()
            self.NameTableWidget.setRowCount(len(filtered_names))

            for j, n in enumerate(filtered_names):
                if isinstance(n, int):
                    i = QTableWidgetItem(str(n))
                else:
                    i = QTableWidgetItem(from_unicode_to_str(n))
                i.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
                self.NameTableWidget.setItem(j, 0, i)

                if n == self.name:
                    m = i

                if j == 0:
                    k = i

        finally:
            self.updating_name = False

            if m is not None:
                m.setSelected(True)

            elif k is not None:
                k.setSelected(True)

            else: # no names, disable name frame and name actions
                self.name = None
                self.RemoveNameAction.setEnabled(False)
                self.NewGroupFromSelectionAction.setEnabled(False)
                self.RemoveFromGroupAction.setEnabled(False)
                self.AddToGroupAction.setEnabled(False)
                self.updateDetailsFrame()


    def selectByName(self, name):
        rows = self.NameTableWidget.rowCount()
        for r in range(rows):
            i = self.NameTableWidget.item(r, 0)
            i.setSelected(name == to_unicode(i.text()))


    def updateDetailsFrame(self):
        if self.name is None:
            self.NameFrame.setEnabled(False)
            self.NameLineEdit.setText(str())
            self.FaxNumberLineEdit.setText(str())
            self.NotesTextEdit.setText(str())

        else:
            self.NameFrame.setEnabled(True)
            data = self.db.get(self.name)
            self.NameLineEdit.setText(self.name)
            self.FaxNumberLineEdit.setText(data['fax'])
            self.NotesTextEdit.setText(data['notes'])


    def NameLineEdit_editingFinished(self):
        if self.name is not None:
            new_name = to_unicode(self.NameLineEdit.text())
            if new_name != self.name:
                if QMessageBox.question(self, self.__tr("Rename?"), "Rename '%s' to '%s'?"%(self.name,new_name), \
                                        QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:

                    self.db.rename(self.name, new_name)
                    log.debug("Rename %s to %s" % (self.name, new_name))
                    self.databaseChanged[int, str, str].emit(FAB_NAME_RENAME, self.name, new_name)
                    self.updateNameList()
                else:
                    self.NameLineEdit.setText(self.name)


    def FaxNumberLineEdit_editingFinished(self):
        if self.name is not None:
            self.db.set_key_value(self.name, 'fax', to_unicode(self.FaxNumberLineEdit.text()))
            self.databaseChanged.emit(FAB_NAME_DETAILS_CHANGED, self.name)


    def NotesTextEdit_textChanged(self):
        if self.name is not None:
            self.db.set_key_value(self.name, 'notes', to_unicode(self.NotesTextEdit.document().toPlainText()))


    def NotesTextEdit_editingFinished(self):
        if self.name is not None:
            self.databaseChanged.emit(FAB_NAME_DETAILS_CHANGED, self.name)


    def NewGroupAction_triggered(self):
        ok = False
        g, ok = QInputDialog.getText(self, self.__tr("Enter New Group Name"), self.__tr("Name for New Group:"))
        g = to_unicode(g)

        if g == to_unicode('All'):
            FailureUI(self, self.__tr("<b>Sorry, the group name cannot be 'All'.</b><p>Please choose a different name."))
            ok = False

        if ok:
            self.db.set('__' + utils.gen_random_uuid(), '', '', '', '', [to_unicode('All'), g], '')
            self.group = g
            log.debug("New empty group %s" % self.group)
            self.databaseChanged.emit(FAB_GROUP_ADD, self.group)
            self.updateGroupList()


    def NewGroupFromSelectionAction_triggered(self):
        selected_names = [to_unicode(n.text()) for n in self.NameTableWidget.selectedItems()]
        if selected_names:
            ok = False
            g, ok = QInputDialog.getText(self, self.__tr("Enter New Group Name"), self.__tr("Name for New Group:"))
            g = to_unicode(g)

            groups = self.db.get_all_groups()

            if g in groups:
                FailureUI(self, self.__tr("<b>Sorry, the group name cannot be the same as an existing group (or 'All').</b><p>Please choose a different name."))
                ok = False

            if ok:
                self.db.update_groups(g, selected_names)
                self.group = g
                log.debug("New group %s with names %s" % (self.group, ','.join(selected_names)))
                self.databaseChanged.emit(FAB_GROUP_ADD, self.group)
                self.updateGroupList()


    def RenameGroupAction_triggered(self):
        selected_items = self.GroupTableWidget.selectedItems()
        if selected_items:
            old_group = to_unicode(selected_items[0].text())
            ok = False
            new_group, ok = QInputDialog.getText(self, self.__tr("Rename Group"), "New Name for Group '%s':"%old_group)
            new_group = to_unicode(new_group)
            groups = self.db.get_all_groups()

            if new_group in groups:
                FailureUI(self, self.__tr("<b>Sorry, the group name cannot be the same as an existing group (or 'All').</b><p>Please choose a different name."))
                ok = False

            if ok:
                self.db.rename_group(old_group, new_group)
                log.debug("Rename group %s to %s" % (old_group, new_group))
                self.databaseChanged[int, str, str].emit(FAB_GROUP_RENAME, old_group, new_group)
                self.group = new_group
                self.updateGroupList()


    def RemoveGroupAction_triggered(self):
        self.db.delete_group(self.group)
        log.debug("Remove group %s" % self.group)
        self.databaseChanged.emit(FAB_GROUP_REMOVE, self.group)
        self.group = None
        self.updateGroupList()


    def NewNameAction_triggered(self):
        ok = False
        t, ok = QInputDialog.getText(self, self.__tr("Enter New Name"), self.__tr("New Name:"))
        if ok:
            t = to_unicode(t)
            self.addName(t)


    def addName(self, name, fax=''):
        if self.group == to_unicode('All'):
            g = [to_unicode('All')]
        else:
            g = [to_unicode('All'), self.group]

        self.db.set(name, '', '', '', fax, g, '')
        self.name = name
        log.debug("New name %s" % self.name)
        self.databaseChanged.emit(FAB_NAME_ADD, self.name)
        self.updateNameList()


    def RemoveNameAction_triggered(self):
        selected_names = [to_unicode(n.text()) for n in self.NameTableWidget.selectedItems()]
        if selected_names:
            for n in selected_names:
                self.db.delete(n)
                log.debug("Removing name %s" % n)
                self.databaseChanged.emit(FAB_NAME_REMOVE, n)

            self.name = None
            self.updateNameList()


    def RemoveFromGroupAction_triggered(self):
        selected_names = [str(n.text()) for n in self.NameTableWidget.selectedItems()]
        if selected_names:
            log.debug("%s leaving group %s" % (','.join(selected_names), self.group))
            self.db.remove_from_group(self.group, selected_names)
            self.databaseChanged.emit(FAB_GROUP_MEMBERSHIP_CHANGED, self.group)
            self.name = None
            self.updateGroupList()


    def GroupTableWidget_namesAddedToGroup(self, row, items): # drag n' drop handler
        self.group = to_unicode(self.GroupTableWidget.item(row, 0).text())
        self.db.add_to_group(self.group, items)
        log.debug("Adding %s to group %s" % (','.join(items), self.group))
        self.databaseChanged.emit(FAB_GROUP_MEMBERSHIP_CHANGED, self.group)
        self.updateGroupList()


    def AddToGroupAction_triggered(self):
        selected_names = [to_unicode(n.text()) for n in self.NameTableWidget.selectedItems()]
        if selected_names:
            ok = False
            all_groups = self.db.get_all_groups()

            if all_groups:
                all_groups = [g for g in all_groups if g != to_unicode('All')]
                all_groups.sort()

                dlg = JoinDialog(self, all_groups)

                if dlg.exec_() == QDialog.Accepted:
                    group = dlg.group
                    if group:
                        self.db.add_to_group(group, selected_names)
                        self.group = group
                        log.debug("Adding %s to group %s" % (','.join(selected_names), self.group))
                        self.databaseChanged.emit(FAB_GROUP_MEMBERSHIP_CHANGED, self.group)
                        self.updateGroupList()

            else:
                FailureUI(self, self.__tr("<b>There are no groups to join.</b><p>Use <i>New Group from Selection</i> to create a new group using these name(s)."))


    def ImportAction_triggered(self):
        result = str(QFileDialog.getOpenFileName(self,
                         self.__tr("Import fax addresses from LDIF or vCard"),
                         #user_conf.workingDirectory(),
                         self.user_settings.working_dir,
                         "vCard (*.vcf);;LDIF (*.ldif *.ldi)"))

        if result:
            working_directory = to_unicode(os.path.dirname(result))
            log.debug("result: %s" % result)
            #user_conf.setWorkingDirectory(working_directory)
            self.user_settings.working_dir = working_directory
            self.user_settings.save()

            if result:
                if result.endswith('.vcf'):
                    ok, error_str = self.db.import_vcard(result)
                else:
                    ok, error_str = self.db.import_ldif(result)

                if not ok:
                    FailureUI(self, error_str)

                else:
                    self.updateUi()


    def __tr(self,s,c = None):
        return qApp.translate("FABWindow",s.encode('utf-8'),c)




class JoinDialog(QDialog):
    def __init__(self, parent, groups):
        QDialog.__init__(self, parent)
        self.group = ''
        self.setupUi(groups)


    def setupUi(self, groups):
        self.setObjectName("Dialog")
        self.resize(QSize(QRect(0,0,271,107).size()).expandedTo(self.minimumSizeHint()))

        self.gridlayout = QGridLayout(self)
        self.gridlayout.setObjectName("gridlayout")

        self.hboxlayout = QHBoxLayout()
        self.hboxlayout.setObjectName("hboxlayout")

        self.label = QLabel(self)
        self.label.setObjectName("label")
        self.hboxlayout.addWidget(self.label)

        self.GroupJoinComboBox = QComboBox(self)

        sizePolicy = QSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.GroupJoinComboBox.sizePolicy().hasHeightForWidth())
        self.GroupJoinComboBox.setSizePolicy(sizePolicy)
        self.GroupJoinComboBox.setObjectName("comboBox")
        self.hboxlayout.addWidget(self.GroupJoinComboBox)
        self.gridlayout.addLayout(self.hboxlayout,0,0,1,3)

        spacerItem = QSpacerItem(20,40,QSizePolicy.Minimum,QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem,1,0,1,1)

        spacerItem1 = QSpacerItem(231,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem1,2,0,1,1)

        self.JoinButton = QPushButton(self)
        self.JoinButton.setObjectName("pushButton_2")
        self.gridlayout.addWidget(self.JoinButton,2,1,1,1)

        self.CancelButton = QPushButton(self)
        self.CancelButton.setObjectName("pushButton")
        self.gridlayout.addWidget(self.CancelButton,2,2,1,1)

        self.GroupJoinComboBox.currentIndexChanged[int].connect(self.GroupJoinComboBox_currentIndexChanged)

        for i, g in enumerate(groups):
            if i == 0:
                self.group = g
            self.GroupJoinComboBox.insertItem(i, g)

        self.JoinButton.clicked.connect(self.accept)
        self.CancelButton.clicked.connect(self.reject)

        self.retranslateUi()


    def GroupJoinComboBox_currentIndexChanged(self, i):
        self.group = to_unicode(self.GroupJoinComboBox.currentText())


    def retranslateUi(self):
        self.setWindowTitle(QApplication.translate("Dialog", "Join Group", None, QApplication.UnicodeUTF8))
        self.label.setText(QApplication.translate("Dialog", "Group to Join:", None, QApplication.UnicodeUTF8))
        self.JoinButton.setText(QApplication.translate("Dialog", "Join", None, QApplication.UnicodeUTF8))
        self.CancelButton.setText(QApplication.translate("Dialog", "Cancel", None, QApplication.UnicodeUTF8))
