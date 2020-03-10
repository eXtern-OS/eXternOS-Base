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
import operator
import struct
from base.sixext.moves import queue
from base.sixext import to_unicode
import signal

# Local
from base.g import *
from base import device, utils, pml
from prnt import cups
from base.codes import *
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Ui
from .sendfaxdialog_base import Ui_Dialog
from .filetable import FileTable, FILETABLE_TYPE_FAX
from .printernamecombobox import PrinterNameComboBox, PRINTERNAMECOMBOBOX_TYPE_FAX_ONLY
from .printsettingsdialog import PrintSettingsDialog
from .faxsetupdialog import FaxSetupDialog


PAGE_SELECT_FAX = 0
PAGE_COVERPAGE = 1
PAGE_FILES = 2
PAGE_RECIPIENTS = 3
PAGE_SEND_FAX = 4
PAGE_MAX = 4

STATUS_INFORMATION = 0
STATUS_WARNING = 1
STATUS_ERROR = 2

MIME_TYPE_COVERPAGE = "application/hplip-fax-coverpage"

fax_enabled = prop.fax_build

if fax_enabled:
    try:
        from fax import fax
    except ImportError:
        # This can fail on Python < 2.3 due to the datetime module
        # or if fax was diabled during the build
        fax_enabled = False

if not fax_enabled:
    log.warn("Fax disabled.")

coverpages_enabled = False
if fax_enabled:
    try:
        import reportlab
        ver = str(reportlab.Version)

        if ver >= "2.0":
            coverpages_enabled = True
        else:
            log.warn("Pre-2.0 version of Reportlab installed. Fax coverpages disabled.")

    except ImportError:
        log.warn("Reportlab not installed. Fax coverpages disabled.")

if not coverpages_enabled:
    log.warn("Please install version 2.0+ of Reportlab for coverpage support.")

if fax_enabled:
    from .fabwindow import FABWindow

if coverpages_enabled:
    from fax import coverpages


class SendFaxDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, printer_name, device_uri=None, args=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.printer_name = printer_name
        if device_uri is not None:
            self.device_uri = device_uri
        else:
            self.device_uri = device.getDeviceURIByPrinterName(self.printer_name)

        self.args = args
        self.dev = None

        self.dbus_avail, self.service, session_bus = device.init_dbus()

        self.CheckTimer = None
        self.lock_file = None
        self.file_list = []
        self.recipient_list = []

        self.initUi()

        if self.printer_name:
            if coverpages_enabled:
                QTimer.singleShot(0, self.displayCoverpagePage)
            else:
                self.lockAndLoad()
                QTimer.singleShot(0, self.displayFilesPage)
        else:
            QTimer.singleShot(0, self.displaySelectFaxPage)


    def initUi(self):
        # connect signals/slots
        self.CancelButton.clicked.connect(self.CancelButton_clicked)
        self.BackButton.clicked.connect(self.BackButton_clicked)
        self.NextButton.clicked.connect(self.NextButton_clicked)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self.initSelectFaxPage()
        self.initCoverpagePage()
        self.initFilesPage()
        self.initRecipientsPage()
        self.initSendFaxPage()

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))


    def lockAndLoad(self):
        # Start up check timer here, since the fax name is now known
        if self.CheckTimer is None:
            self.CheckTimer = QTimer(self)
            self.CheckTimer.timeout.connect(self.CheckTimer_timeout)
            self.CheckTimer.start(3000)

        # Lock the app
        if self.printer_name and self.lock_file is None:
            ok, self.lock_file = utils.lock_app('hp-sendfax-%s' % self.printer_name, True)

            if not ok:
                log.error("hp-sendfax is already running for fax %s" % self.printer_name)
                # TODO:

    #
    # Select Fax Page
    #

    def initSelectFaxPage(self):
        self.FaxComboBox.setType(PRINTERNAMECOMBOBOX_TYPE_FAX_ONLY)
        self.FaxComboBox.PrinterNameComboBox_currentChanged.connect(self.FaxComboBox_currentChanged)
        self.FaxComboBox.PrinterNameComboBox_noPrinters.connect(self.FaxComboBox_noPrinters)
        self.FaxOptionsButton.clicked.connect(self.FaxOptionsButton_clicked)
        self.FaxSetupButton.clicked.connect(self.FaxSetupButton_clicked)

        if self.printer_name is not None:
            self.FaxComboBox.setInitialPrinter(self.printer_name)


    def displaySelectFaxPage(self):
        self.BackButton.setEnabled(False)
        self.updateStepText(PAGE_SELECT_FAX)

        if not fax_enabled:
            FailureUI(self, self.__tr("<b>PC send fax support is not enabled.</b><p>Re-install HPLIP with fax support or use the device front panel to send a fax.</p><p>Click <i>OK</i> to exit.</p>"))
            self.close()
            return

        if not self.dbus_avail:
            FailureUI(self, self.__tr("<b>PC send fax support requires DBus and hp-systray.</b><p>Please check the HPLIP installation for proper installation of DBus and hp-systray support.</p><p>Click <i>OK</i> to exit.</p>"))
            self.close()
            return

        self.FaxComboBox.updateUi()
        self.displayPage(PAGE_SELECT_FAX)


    def FaxComboBox_currentChanged(self, device_uri, printer_name):
        self.printer_name = printer_name
        self.device_uri = device_uri


    def FaxComboBox_noPrinters(self):
        FailureUI(self, self
                  .__tr("<b>No installed fax devices found.</b><p>Please setup a fax device and try again (try using 'hp-setup').</p><p>Click <i>OK</i> to exit.</p>"))
        self.close()


    def FaxOptionsButton_clicked(self):
        dlg = PrintSettingsDialog(self, self.printer_name, fax_mode=True)
        dlg.exec_()


    def FaxSetupButton_clicked(self):
        dlg = FaxSetupDialog(self, self.device_uri)
        dlg.exec_()

    #
    # Coverpage Page
    #

    def initCoverpagePage(self):
        self.cover_page_message = ''
        self.cover_page_re = ''
        self.preserve_formatting = False
        self.cover_page_func, cover_page_png = None, None
        self.last_job_id = 0
        self.busy = False
        self.PrevCoverPageButton.setIcon(QIcon(load_pixmap("prev", "16x16")))
        self.NextCoverPageButton.setIcon(QIcon(load_pixmap("next", "16x16")))

        if coverpages_enabled:
            self.cover_page_list = list(coverpages.COVERPAGES.keys())
            self.cover_page_index = self.cover_page_list.index("basic")
            self.cover_page_max = len(self.cover_page_list)-1
            self.cover_page_name = self.cover_page_list[self.cover_page_index]

            self.PrevCoverPageButton.clicked.connect(self.PrevCoverPageButton_clicked)
            self.NextCoverPageButton.clicked.connect(self.NextCoverPageButton_clicked)
            self.CoverPageGroupBox.toggled[bool].connect(self.CoverPageGroupBox_toggled)
            self.MessageEdit.textChanged.connect(self.MessageEdit_textChanged)
            self.RegardingEdit.textChanged["const QString &"].connect(self.RegardingEdit_textChanged)
            self.PreserveFormattingCheckBox.toggled[bool].connect(self.PreserveFormattingCheckBox_toggled)
        else:
            self.CoverPageGroupBox.setEnabled(False)


    def displayCoverpagePage(self):
        self.BackButton.setEnabled(False) # No going back once printer is chosen
        self.NextButton.setEnabled(True)

        self.lockAndLoad()

        self.updateCoverpageButtons()
        self.displayCoverpagePreview()
        self.displayPage(PAGE_COVERPAGE)


    def MessageEdit_textChanged(self):
        self.cover_page_message = to_unicode(self.MessageEdit.toPlainText())


    def RegardingEdit_textChanged(self, t):
        self.cover_page_re = to_unicode(t)


    def PreserveFormattingCheckBox_toggled(self, b):
        self.preserve_formatting = b


    def PrevCoverPageButton_clicked(self):
        self.cover_page_index -= 1
        if self.cover_page_index < 0:
            self.cover_page_index = 0
        else:
            self.updateCoverpageButtons()
            self.displayCoverpagePage()


    def NextCoverPageButton_clicked(self):
        self.cover_page_index += 1
        if self.cover_page_index > self.cover_page_max:
            self.cover_page_index = self.cover_page_max
        else:
            self.updateCoverpageButtons()
            self.displayCoverpagePage()


    def displayCoverpagePreview(self):
        if coverpages_enabled:
            self.cover_page_name = self.cover_page_list[self.cover_page_index]
            self.cover_page_func = coverpages.COVERPAGES[self.cover_page_name][0]
            self.CoverPageName.setText(str('<i>"%s"</i>'%self.cover_page_name))
            self.CoverPagePreview.setPixmap(load_pixmap(coverpages.COVERPAGES[self.cover_page_name][1], 'other'))

        if self.CoverPageGroupBox.isChecked():
            self.addCoverPage()
        else:
            self.removeCoverPage()


    def updateCoverpageButtons(self):
        enabled = self.CoverPageGroupBox.isChecked()
        self.PrevCoverPageButton.setEnabled(enabled and self.cover_page_index != 0)
        self.NextCoverPageButton.setEnabled(enabled and self.cover_page_index != self.cover_page_max)


    def CoverPageGroupBox_toggled(self, b):
        self.updateCoverpageButtons()
        if b:
            self.addCoverPage()
        else:
            self.removeCoverPage()


    def addCoverPage(self):
        self.removeCoverPage()
        self.FilesTable.addFile(self.cover_page_name, MIME_TYPE_COVERPAGE,
                                self.__tr('HP Fax Coverpage: "%s"'%self.cover_page_name),
                                self.__tr("Cover Page"), 1)


    def removeCoverPage(self):
        self.FilesTable.removeFileByMIMEType(MIME_TYPE_COVERPAGE)


    def toggleCoverPage(self, b):
        # XXX: qt5port: disconnect method requires attention
        self.CoverPageGroupBox.toggled[bool].disconnect(self.CoverPageGroupBox_toggled)
        self.CoverPageGroupBox.setChecked(b)
        self.CoverPageGroupBox.toggled[bool].connect(self.CoverPageGroupBox_toggled)


    #
    # Files Page
    #

    def initFilesPage(self):
        self.FilesTable.setType(FILETABLE_TYPE_FAX)
        self.FilesTable.setFaxCallback(self.FileTable_callback)
        self.FilesTable.isEmpty.connect(self.FilesTable_isEmpty)
        self.FilesTable.isNotEmpt.connect(self.FilesTable_isNotEmpty)
        self.FilesTable.fileListChanged.connect(self.FilesTable_fileListChanged)


    def displayFilesPage(self):
        self.FilesTable.updateUi(False)

        if self.args is not None:
            for a in self.args:
                f = os.path.abspath(os.path.expanduser(a))
                if os.path.exists(f) and os.access(f, os.R_OK):
                    self.renderFile(f)

            self.args = None

        self.restoreNextButton()
        self.NextButton.setEnabled(self.FilesTable.isNotEmpty())
        self.BackButton.setEnabled(coverpages_enabled)
        self.FilesPageNote.setText(self.__tr("Note: You may also add files to the fax by printing from any application to the '%s' fax printer."%self.printer_name))
        self.displayPage(PAGE_FILES)


    def FilesTable_isEmpty(self):
        if self.StackedWidget.currentIndex() == PAGE_FILES:
            self.NextButton.setEnabled(False)


    def FilesTable_isNotEmpty(self):
        if self.StackedWidget.currentIndex() == PAGE_FILES:
            self.NextButton.setEnabled(True)


    def FilesTable_fileListChanged(self):
        self.file_list = self.FilesTable.file_list
        self.toggleCoverPage(self.FilesTable.isMIMETypeInList(MIME_TYPE_COVERPAGE))


    #
    # Recipients Page
    #

    def initRecipientsPage(self):
        # setup validators
        self.QuickAddFaxEdit.setValidator(PhoneNumValidator(self.QuickAddFaxEdit))

        # Fax address book database
        self.db = fax.FaxAddressBook()

        # Fax address book window
        self.fab = FABWindow(self)
        self.fab.setWindowFlags(Qt.Tool) # Keeps the Fab window on top

        self.fab.databaseChanged.connect(self.FABWindow_databaseChanged)

        # connect signals
        # self.connect(self.QuickAddFaxEdit, SIGNAL("textChanged(const QString &)"),
        #            self.QuickAddFaxEdit_textChanged)
        self.QuickAddFaxEdit.textChanged["const QString &"].connect(self.QuickAddFaxEdit_textChanged)
        # self.connect(self.QuickAddNameEdit, SIGNAL("textChanged(const QString &)"),
        #            self.QuickAddNameEdit_textChanged)
        self.QuickAddNameEdit.textChanged["const QString &"].connect(self.QuickAddNameEdit_textChanged)
        self.QuickAddButton.clicked.connect(self.QuickAddButton_clicked)
        self.FABButton.clicked.connect(self.FABButton_clicked)
        self.AddIndividualButton.clicked.connect(self.AddIndividualButton_clicked)
        self.AddGroupButton.clicked.connect(self.AddGroupButton_clicked)
        self.RemoveRecipientButton.clicked.connect(self.RemoveRecipientButton_clicked)
        self.MoveRecipientUpButton.clicked.connect(self.MoveRecipientUpButton_clicked)
        self.MoveRecipientDownButton.clicked.connect(self.MoveRecipientDownButton_clicked)
        # self.connect(self.RecipientsTable, SIGNAL("itemSelectionChanged()"),
        #            self.RecipientsTable_itemSelectionChanged)
        self.RecipientsTable.itemSelectionChanged.connect(self.RecipientsTable_itemSelectionChanged)

        #self.connect(self.RecipientsTable, SIGNAL("itemDoubleClicked(QTableWidgetItem *)"),
        #            self.RecipientsTable_itemDoubleClicked)
        self.RecipientsTable.itemDoubleClicked["QTableWidgetItem *"].connect(self.RecipientsTable_itemDoubleClicked)

        # setup icons
        self.FABButton.setIcon(QIcon(load_pixmap("fab", "16x16")))
        self.AddIndividualButton.setIcon(QIcon(load_pixmap("add_user", "16x16")))
        self.AddGroupButton.setIcon(QIcon(load_pixmap("add_users", "16x16")))
        self.RemoveRecipientButton.setIcon(QIcon(load_pixmap("remove_user", "16x16")))
        self.MoveRecipientUpButton.setIcon(QIcon(load_pixmap("up_user", "16x16")))
        self.MoveRecipientDownButton.setIcon(QIcon(load_pixmap("down_user", "16x16")))
        self.QuickAddButton.setIcon(QIcon(load_pixmap("add_user_quick", "16x16")))

        # setup initial state
        self.QuickAddButton.setEnabled(False)

        self.recipient_headers = [self.__tr("Name"), self.__tr("Fax number"), self.__tr("Notes")]


    def FABWindow_databaseChanged(self, action, s1='', s2=''):
        self.db.load()

        if action in (FAB_NAME_ADD, FAB_GROUP_ADD, FAB_GROUP_RENAME,
                      FAB_GROUP_REMOVE, FAB_GROUP_MEMBERSHIP_CHANGED):

            log.debug("Fax address book has changed")
            self.updateAddressBook()

        elif action == FAB_NAME_REMOVE:
            log.debug("Fax address book has changed: '%s' removed" % s1)
            all_names = self.db.get_all_names()
            self.recipient_list = [x for x in all_names if x in self.recipient_list]
            self.updateAddressBook()
            self.updateRecipientTable()

        elif action == FAB_NAME_RENAME:
            log.debug("Fax address book has changed: '%s' renamed to '%s'" % (s1, s2))
            for i, n in enumerate(self.recipient_list):
                if n == s1:
                    self.recipient_list[i] = s2
                    self.updateRecipientTable()
                    break
            else:
                self.updateAddressBook()

        elif action == FAB_NAME_DETAILS_CHANGED:
            log.debug("Fax address book has changed: '%s' details changed" % s1)
            self.updateRecipientTable()


    def displayRecipientsPage(self):
        self.updateAddressBook()
        self.updateRecipientTable()
        self.enableQuickAddButton()
        self.displayPage(PAGE_RECIPIENTS)
        self.restoreNextButton()
        self.BackButton.setEnabled(True)


    def updateAddressBook(self):
        names = [n for n in self.db.get_all_names() if not n.startswith('__')]
        groups = self.db.get_all_groups()
        self.AddIndividualComboBox.clear()
        self.AddGroupComboBox.clear()

        i = 0
        names.sort()
        for n in names:
            if n not in self.recipient_list:
                data = self.db.get(n)
                if data['fax']:
                    self.AddIndividualComboBox.addItem(n)
                    i += 1

        if i:
            self.AddIndividualButton.setEnabled(True)
            self.AddIndividualComboBox.setEnabled(True)
            #self.AddIndividualButton.setIcon(QIcon(load_pixmap("add_user", "16x16")))

        else:
            self.AddIndividualButton.setEnabled(False)
            self.AddIndividualComboBox.setEnabled(False)
            #self.AddIndividualButton.setIcon(QIcon(load_pixmap("add_user-disabled", "16x16")))

        i = 0
        groups.sort()
        for g in groups:
            for n in self.db.group_members(g):
                if not n.startswith('__') and n not in self.recipient_list:
                    self.AddGroupComboBox.addItem(g)
                    i += 1
                    break

        if i:
            self.AddGroupButton.setEnabled(True)
            self.AddGroupComboBox.setEnabled(True)
            #self.AddGroupButton.setIcon(QIcon(load_pixmap("add_users", "16x16")))

        else:
            self.AddGroupButton.setEnabled(False)
            self.AddGroupComboBox.setEnabled(False)
            #self.AddGroupButton.setIcon(QIcon(load_pixmap("add_users-disabled", "16x16")))


    def updateRecipientTable(self):
        try:
            prev = self.getCurrentRecipient()
        except (TypeError, AttributeError):
            prev = None

        self.RecipientsTable.clear()
        self.RecipientsTable.setRowCount(0)
        self.RecipientsTable.setColumnCount(0)

        if self.recipient_list:
            num_recipients = len(self.recipient_list)

            self.RecipientsTable.setColumnCount(len(self.recipient_headers))
            self.RecipientsTable.setHorizontalHeaderLabels(self.recipient_headers)
            self.RecipientsTable.setRowCount(num_recipients)
            flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled

            j = None
            for row, n in enumerate(self.recipient_list):
                i = QTableWidgetItem(str(n))
                i.setFlags(flags)
                self.RecipientsTable.setItem(row, 0, i)
                if prev is not None and n == prev:
                    j = i

                k = self.db.get(n)
                if not k:
                    continue

                i = QTableWidgetItem(str(k['fax']))
                i.setFlags(flags)
                self.RecipientsTable.setItem(row, 1, i)

                i = QTableWidgetItem(str(k['notes']))
                i.setFlags(flags)
                self.RecipientsTable.setItem(row, 2, i)

            self.RecipientsTable.resizeColumnsToContents()
            self.RecipientsTable.resizeRowsToContents()

            if j is not None:
                self.RecipientsTable.setCurrentItem(j)
            else:
                self.RecipientsTable.setCurrentItem(self.RecipientsTable.item(0, 0))

            self.NextButton.setEnabled(True)

        else:
            self.enableRecipientListButtons()
            self.NextButton.setEnabled(False)


    def RecipientsTable_itemSelectionChanged(self):
        current_row = self.RecipientsTable.currentRow()
        num_recipients = len(self.recipient_list)
        self.enableRecipientListButtons(num_recipients > 0,  # remove
                                            num_recipients > 1 and current_row > 0, # up
                                            num_recipients > 1 and current_row < (num_recipients-1)) # down


    def enableRecipientListButtons(self, enable_remove=False, enable_up_move=False, enable_down_move=False):
        if enable_remove:
            self.RemoveRecipientButton.setEnabled(True)
        else:
            self.RemoveRecipientButton.setEnabled(False)

        if enable_up_move:
            self.MoveRecipientUpButton.setEnabled(True)
        else:
            self.MoveRecipientUpButton.setEnabled(False)

        if enable_down_move:
            self.MoveRecipientDownButton.setEnabled(True)
        else:
            self.MoveRecipientDownButton.setEnabled(False)


    def QuickAddFaxEdit_textChanged(self, fax):
        self.enableQuickAddButton(None, to_unicode(fax))


    def QuickAddNameEdit_textChanged(self, name):
        self.enableQuickAddButton(to_unicode(name))


    def enableQuickAddButton(self, name=None, fax=None):
        if name is None:
            name = to_unicode(self.QuickAddNameEdit.text())
        if fax is None:
            fax = to_unicode(self.QuickAddFaxEdit.text())

        existing_name = False
        if name:
            existing_name = name in self.db.get_all_names()

        if existing_name:
            try:
                self.QuickAddNameEdit.setStyleSheet("background-color: yellow")
            except AttributeError:
                pass
        else:
            try:
                self.QuickAddNameEdit.setStyleSheet("")
            except AttributeError:
                pass

        if name and not existing_name and fax:
            self.QuickAddButton.setEnabled(True)
        else:
            self.QuickAddButton.setEnabled(False)


    def QuickAddButton_clicked(self):
        name = to_unicode(self.QuickAddNameEdit.text())
        fax = to_unicode(self.QuickAddFaxEdit.text())
        self.fab.addName(name, fax)
        self.addRecipient(name)
        self.updateRecipientTable()
        self.QuickAddNameEdit.clear()
        self.QuickAddFaxEdit.clear()
        self.enableQuickAddButton('', '')


    def AddIndividualButton_clicked(self):
        self.addRecipient(to_unicode(self.AddIndividualComboBox.currentText()))


    def AddGroupButton_clicked(self):
        self.addGroup(to_unicode(self.AddGroupComboBox.currentText()))


    def RemoveRecipientButton_clicked(self):
        name = self.getCurrentRecipient()
        temp = self.recipient_list[:]
        for i, n in enumerate(temp):
            if name == n:
                del self.recipient_list[i]
                self.updateRecipientTable()
                self.updateAddressBook()
                break


    def MoveRecipientUpButton_clicked(self):
        utils.list_move_up(self.recipient_list, self.getCurrentRecipient())
        self.updateRecipientTable()


    def MoveRecipientDownButton_clicked(self):
        utils.list_move_down(self.recipient_list, self.getCurrentRecipient())
        self.updateRecipientTable()


    def getCurrentRecipient(self):
        item = self.RecipientsTable.item(self.RecipientsTable.currentRow(), 0)
        if item is not None:
            return to_unicode(item.text())
        else:
            return to_unicode('')


    def addRecipient(self, name, update=True):
        if name not in self.recipient_list and not name.startswith('__'):
            self.recipient_list.append(name)
            if update:
                self.updateRecipientTable()
                self.updateAddressBook()


    def addGroup(self, group):
        for n in self.db.group_members(group):
            self.addRecipient(n, False)

        self.updateRecipientTable()
        self.updateAddressBook()


    def FABButton_clicked(self):
        self.fab.show()


    def RecipientsTable_itemDoubleClicked(self, item):
        if item is not None:
            row, col = item.row(), item.column()
            if col != 0:
                item = self.RecipientsTable.item(row, 0)

            self.fab.selectByName(to_unicode(item.text()))
            self.fab.show()


    #
    # Send Fax Page
    #

    def initSendFaxPage(self):
        self.info_icon = QIcon(load_pixmap("info", "16x16"))
        self.warn_icon = QIcon(load_pixmap("warning", "16x16"))
        self.error_icon = QIcon(load_pixmap("error", "16x16"))
        self.busy_icon = QIcon(load_pixmap("busy", "16x16"))
        self.update_queue = queue.Queue() # UI updates from send thread
        self.event_queue = queue.Queue() # UI events (cancel) to send thread
        self.send_fax_active = False


    def displaySendFaxPage(self):
        self.displayPage(PAGE_SEND_FAX)
        self.addStatusMessage(self.__tr("Ready to send fax."), self.info_icon)
        self.NextButton.setText(self.__tr("Send Fax"))



    #
    # Fax
    #

    def executeSendFax(self):
        self.NextButton.setEnabled(False)
        self.BackButton.setEnabled(False)
        self.CheckTimer.stop()
        self.busy = True
        phone_num_list = []

        ppd_file = cups.getPPD(self.printer_name)

        if ppd_file is not None and os.path.exists(ppd_file):
            if open(ppd_file, 'rb').read().find(b'HP Fax') == -1:
                FailureUI(self, self.__tr("<b>Fax configuration error.</b><p>The CUPS fax queue for '%s' is incorrectly configured.<p>Please make sure that the CUPS fax queue is configured with the 'HPLIP Fax' Model/Driver."%self.printer_name))
                self.close()
                return

        beginWaitCursor()

        mq = device.queryModelByURI(self.device_uri)

        self.dev = fax.getFaxDevice(self.device_uri,
                                   self.printer_name, None,
                                   mq['fax-type'])

        try:
            try:
                self.dev.open()
            except Error as e:
                log.warn(e.msg)

            try:
                self.dev.queryDevice(quick=True)
            except Error as e:
                log.error("Query device error (%s)." % e.msg)
                self.dev.error_state = ERROR_STATE_ERROR

        finally:
            self.dev.close()
            endWaitCursor()

        if self.dev.error_state > ERROR_STATE_MAX_OK and \
            self.dev.error_state not in (ERROR_STATE_LOW_SUPPLIES, ERROR_STATE_LOW_PAPER):

            FailureUI(self, self.__tr("<b>Device is busy or in an error state (code=%s)</b><p>Please wait for the device to become idle or clear the error and try again."%self.dev.status_code))
            self.NextButton.setEnabled(True)
            return

        # Check to make sure queue in CUPS is idle
        self.cups_printers = cups.getPrinters()
        for p in self.cups_printers:
            if p.name == self.printer_name:
                if p.state == cups.IPP_PRINTER_STATE_STOPPED:
                    FailureUI(self, self.__tr("<b>The CUPS queue for '%s' is in a stopped or busy state.</b><p>Please check the queue and try again."%self.printer_name))
                    self.NextButton.setEnabled(False)
                    return
                break

        log.debug("Recipient list:")

        for p in self.recipient_list:
            entry = self.db.get(p)
            phone_num_list.append(entry)
            log.debug("Name=%s Number=%s" % (entry["name"], entry["fax"]))

        log.debug("File list:")

        for f in self.file_list:
            log.debug(f)

        self.dev.sendEvent(EVENT_START_FAX_JOB, self.printer_name, 0, '')

        if not self.dev.sendFaxes(phone_num_list, self.file_list, self.cover_page_message,
                                  self.cover_page_re, self.cover_page_func, self.preserve_formatting,
                                  self.printer_name, self.update_queue, self.event_queue):

            FailureUI(self, self.__tr("<b>Send fax is active.</b><p>Please wait for operation to complete."))
            self.dev.sendEvent(EVENT_FAX_JOB_FAIL, self.printer_name, 0, '')
            self.busy = False
            self.send_fax_active = False
            #self.NextButton.setEnabled(False)
            self.setCancelCloseButton()
            return

        self.send_fax_active = True
        self.setCancelCloseButton()
        self.SendFaxTimer = QTimer(self)
        self.SendFaxTimer.timeout.connect(self.SendFaxTimer_timeout)
        self.SendFaxTimer.start(1000) # 1 sec UI updates


    def setCancelCloseButton(self):
        if self.send_fax_active:
            self.CancelButton.setText(self.__tr("Cancel Send"))
        else:
            self.CancelButton.setText(self.__tr("Close"))


    def CancelButton_clicked(self):
        if self.send_fax_active:
            self.addStatusMessage(self.__tr("Cancelling job..."), self.warn_icon)
            self.event_queue.put((fax.EVENT_FAX_SEND_CANCELED, '', '', ''))
            self.dev.sendEvent(EVENT_FAX_JOB_CANCELED, self.printer_name, 0, '')
        else:
            self.close()


    def SendFaxTimer_timeout(self):
        while self.update_queue.qsize():
            try:
                status, page_num, arg = self.update_queue.get(0)
            except queue.Empty:
                break

            if status == fax.STATUS_IDLE:
                self.busy = False
                self.send_fax_active = False
                self.setCancelCloseButton()
                self.SendFaxTimer.stop()

            elif status == fax.STATUS_PROCESSING_FILES:
                self.addStatusMessage(self.__tr("Processing page %s..."%page_num), self.busy_icon)

            elif status == fax.STATUS_SENDING_TO_RECIPIENT:
                self.addStatusMessage(self.__tr("Sending fax to %s..."%arg), self.busy_icon)

            elif status == fax.STATUS_DIALING:
                self.addStatusMessage(self.__tr("Dialing %s..."%arg), self.busy_icon)

            elif status == fax.STATUS_CONNECTING:
                self.addStatusMessage(self.__tr("Connecting to %s..."%arg), self.busy_icon)

            elif status == fax.STATUS_SENDING:
                self.addStatusMessage(self.__tr("Sending page %s to %s..."%(page_num,arg)),
                                      self.busy_icon)

            elif status == fax.STATUS_CLEANUP:
                self.addStatusMessage(self.__tr("Cleaning up..."), self.busy_icon)

            elif status in (fax.STATUS_ERROR, fax.STATUS_BUSY, fax.STATUS_COMPLETED, fax.STATUS_ERROR_IN_CONNECTING, 
                fax.STATUS_ERROR_IN_TRANSMITTING, fax.STATUS_ERROR_PROBLEM_IN_FAXLINE, fax.STATUS_JOB_CANCEL ):
                self.busy = False
                self.send_fax_active = False
                self.setCancelCloseButton()
                self.SendFaxTimer.stop()

                if status == fax.STATUS_ERROR:
                    result_code, error_state = self.dev.getPML(pml.OID_FAX_DOWNLOAD_ERROR)
                    #FailureUI(self, self.__tr("<b>Fax send error (%s).</b><p>" % pml.DN_ERROR_STR.get(error_state, "Unknown error")))
                    if error_state == pml.DN_ERROR_NONE:
                        self.addStatusMessage(self.__tr("Fax send error (Possible cause: No answer or dialtone)"), self.error_icon)
                    else:
                        self.addStatusMessage(self.__tr("Fax send error (%s)"%pml.DN_ERROR_STR.get(error_state, "Unknown error")), self.error_icon)
                    self.dev.sendEvent(EVENT_FAX_JOB_FAIL, self.printer_name, 0, '')

                elif status == fax.STATUS_ERROR_IN_CONNECTING:
                    self.addStatusMessage(self.__tr("Fax send error (Error in connecting)"), self.error_icon)
                    self.dev.sendEvent(EVENT_FAX_JOB_FAIL, self.printer_name, 0, '')

                elif status == fax.STATUS_ERROR_IN_TRANSMITTING:
                    self.addStatusMessage(self.__tr("Fax send error (Error in transmitting)"), self.error_icon)
                    self.dev.sendEvent(EVENT_FAX_JOB_FAIL, self.printer_name, 0, '')

                elif status == fax.STATUS_ERROR_PROBLEM_IN_FAXLINE:
                    self.addStatusMessage(self.__tr("Fax send error (Problem with the fax line)"), self.error_icon)
                    self.dev.sendEvent(EVENT_FAX_JOB_FAIL, self.printer_name, 0, '')

                elif status == fax.STATUS_JOB_CANCEL:
                    self.addStatusMessage(self.__tr("(Fax Job Cancelled)"), self.error_icon)
                    self.dev.sendEvent(EVENT_FAX_JOB_FAIL, self.printer_name, 0, '')  

                elif status == fax.STATUS_BUSY:
                    #FailureUI(self, self.__tr("<b>Fax device is busy.</b><p>Please try again later."))
                    self.addStatusMessage(self.__tr("Fax is busy."), self.error_icon)
                    self.dev.sendEvent(EVENT_FAX_JOB_FAIL, self.printer_name, 0, '')

                elif status == fax.STATUS_COMPLETED:
                    self.addStatusMessage(self.__tr("Send fax job complete."), self.info_icon)

                    self.dev.sendEvent(EVENT_END_FAX_JOB, self.printer_name, 0, '')


    def addStatusMessage(self, text, icon):
        log.debug(text)
        #self.StatusList.addItem(QListWidgetItem(icon, text, self.StatusList))
        QListWidgetItem(icon, text, self.StatusList)

    #
    # CheckTimer and Fax Rendering
    #

    def FileTable_callback(self, f):
        # Called by FileTable when user adds a file using "Add file..."
        log.debug("FileTable_callback(%s)" % f)
        self.renderFile(f)


    def renderFile(self, f):
        self.busy = True
        beginWaitCursor()
        try:
            self.last_job_id = cups.printFile(self.printer_name, f, os.path.basename(f))
        finally:
            self.busy = False
            endWaitCursor()


    def CheckTimer_timeout(self):
        if not self.busy:
            #log.debug("Checking for incoming faxes...")
            try:
                device_uri, printer_name, event_code, username, job_id, title, timedate, fax_file = \
                    self.service.CheckForWaitingFax(self.device_uri, prop.username, self.last_job_id)
            except Exception as e:
                log.debug("Exception caught in CheckTimer_timeout: %s" % e)
                fax_file = None

            if fax_file:
                self.last_job_id = 0
                log.debug("A new fax has arrived: %s (%d)" % (fax_file, job_id))
                self.addFileFromJob(fax_file, title)


    def addFileFromJob(self, fax_file, title):
        self.busy = True
        #beginWaitCursor()
        try:
            ok, num_pages, hort_dpi, vert_dpi, page_size, resolution, encoding = \
                self.getFileInfo(fax_file)
            if ok:
                self.FilesTable.addFile(fax_file, 'application/hplip-fax', 'HPLIP Fax', title, num_pages)

        finally:
            self.busy = False
            endWaitCursor()


    def getFileInfo(self, fax_file):
        f = open(fax_file, 'rb')
        header = f.read(fax.FILE_HEADER_SIZE)
        f.close()

        if len(header) != fax.FILE_HEADER_SIZE:
            log.error("Invalid fax file! (truncated header or no data)")
            return (False, 0, 0, 0, 0, 0, 0)

        mg, version, num_pages, hort_dpi, vert_dpi, page_size, \
            resolution, encoding, reserved1, reserved2 = \
            struct.unpack(">8sBIHHBBBII", header[:fax.FILE_HEADER_SIZE])

        log.debug("Magic=%s Ver=%d Pages=%d hDPI=%d vDPI=%d Size=%d Res=%d Enc=%d" %
                  (mg, version, num_pages, hort_dpi, vert_dpi, page_size, resolution, encoding))

        return (True, num_pages, hort_dpi, vert_dpi, page_size, resolution, encoding)


    #
    # Misc
    #

    def closeEvent(self, e):
        if self.lock_file is not None:
            utils.unlock(self.lock_file)
        e.accept()


    def displayPage(self, page):
        self.updateStepText(page)
        self.StackedWidget.setCurrentIndex(page)


#    def CancelButton_clicked(self):
#        self.close()


    def BackButton_clicked(self):
        p = self.StackedWidget.currentIndex()
        if p == PAGE_SELECT_FAX:
            log.error("Invalid!")

        elif p == PAGE_COVERPAGE:
            log.error("Invalid!")

        elif p == PAGE_FILES:
            self.StackedWidget.setCurrentIndex(PAGE_COVERPAGE)
            self.displayCoverpagePage()

        elif p == PAGE_RECIPIENTS:
            self.StackedWidget.setCurrentIndex(PAGE_FILES)
            self.displayFilesPage()

        elif p == PAGE_SEND_FAX:
            self.StackedWidget.setCurrentIndex(PAGE_RECIPIENTS)
            self.displayRecipientsPage()


    def NextButton_clicked(self):
        p = self.StackedWidget.currentIndex()
        if p == PAGE_SELECT_FAX:
            self.StackedWidget.setCurrentIndex(PAGE_COVERPAGE)
            self.displayCoverpagePage()

        elif p == PAGE_COVERPAGE:
            self.StackedWidget.setCurrentIndex(PAGE_FILES)
            self.displayFilesPage()

        elif p == PAGE_FILES:
            self.StackedWidget.setCurrentIndex(PAGE_RECIPIENTS)
            self.displayRecipientsPage()

        elif p == PAGE_RECIPIENTS:
            self.StackedWidget.setCurrentIndex(PAGE_SEND_FAX)
            self.displaySendFaxPage()

        elif p == PAGE_SEND_FAX:
            self.executeSendFax()


    def updateStepText(self, p):
        self.StepText.setText(self.__tr("Step %s of %s"%(p+1,PAGE_MAX+1)))


    def restoreNextButton(self):
        self.NextButton.setText(self.__tr("Next >"))


    def __tr(self,s,c = None):
        return qApp.translate("SendFaxDialog",s.encode('utf-8'),c)


