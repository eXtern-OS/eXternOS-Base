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
import signal

# Local
from base.g import *
from base import device, utils
from prnt import cups
from base.codes import *
from .ui_utils import *
from base.sixext import to_unicode
# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Ui
from .faxsetupdialog_base import Ui_Dialog
from .deviceuricombobox import DEVICEURICOMBOBOX_TYPE_FAX_ONLY

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


class FaxSetupDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, device_uri):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.device_uri = device_uri
        self.initUi()
        self.dev = None

        self.user_settings = UserSettings()
        self.user_settings.load()
        self.user_settings.debug()

        QTimer.singleShot(0, self.updateUi)


    def initUi(self):
        # connect signals/slots
        self.CancelButton.clicked.connect(self.CancelButton_clicked)
        self.FaxComboBox.DeviceUriComboBox_noDevices.connect(self.FaxComboBox_noDevices)
        self.FaxComboBox.DeviceUriComboBox_currentChanged.connect(self.FaxComboBox_currentChanged)
        self.FaxComboBox.setType(DEVICEURICOMBOBOX_TYPE_FAX_ONLY)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))

        if self.device_uri:
            self.FaxComboBox.setInitialDevice(self.device_uri)

        self.NameCompanyLineEdit.setMaxLength(50)
        self.FaxNumberLineEdit.setMaxLength(50)
        self.FaxNumberLineEdit.setValidator(PhoneNumValidator(self.FaxNumberLineEdit))
        self.VoiceNumberLineEdit.setMaxLength(50)
        self.VoiceNumberLineEdit.setValidator(PhoneNumValidator(self.VoiceNumberLineEdit))
        self.EmailLineEdit.setMaxLength(50)

        self.NameCompanyLineEdit.editingFinished.connect( self.NameCompanyLineEdit_editingFinished)

        self.NameCompanyLineEdit.textChanged["const QString &"].connect( self.NameCompanyLineEdit_textChanged)

        self.FaxNumberLineEdit.editingFinished.connect( self.FaxNumberLineEdit_editingFinished)

        self.FaxNumberLineEdit.textChanged["const QString &"].connect( self.FaxNumberLineEdit_textChanged)

        self.VoiceNumberLineEdit.editingFinished.connect( self.VoiceNumberLineEdit_editingFinished)

        self.VoiceNumberLineEdit.textChanged["const QString &"].connect( self.VoiceNumberLineEdit_textChanged)

        self.EmailLineEdit.editingFinished.connect( self.EmailLineEdit_editingFinished)

        self.EmailLineEdit.textChanged["const QString &"].connect( self.EmailLineEdit_textChanged)

        self.tabWidget.currentChanged[int].connect(self.Tabs_currentChanged)

        self.name_company_dirty = False
        self.fax_number_dirty = False
        self.voice_number_dirty = False
        self.email_dirty = False


    def updateUi(self):
        if not fax_enabled:
            FailureUI(self, self.__tr("<b>PC send fax support is not enabled.</b><p>Re-install HPLIP with fax support or use the device front panel to send a fax.</p><p>Click <i>OK</i> to exit.</p>"))
            self.close()
            return

        self.FaxComboBox.updateUi()
        self.tabWidget.setCurrentIndex(0)


    def FaxComboBox_currentChanged(self, device_uri):
        self.device_uri = device_uri
        self.updateCoverpageTab()

        if self.dev is not None:
            self.dev.close()

        try:
            self.dev = fax.getFaxDevice(self.device_uri)
        except Error:
            CheckDeviceUI(self)
            return

        self.updateHeaderTab()



    def FaxComboBox_noDevices(self):
        FailureUI(self, self.__tr("<b>No devices that require fax setup found.</b>"))
        self.close()

    #
    # Name/Company (for TTI header) (stored in device)
    #

    def NameCompanyLineEdit_editingFinished(self):
        self.saveNameCompany(to_unicode(self.NameCompanyLineEdit.text()))


    def NameCompanyLineEdit_textChanged(self, s):
        self.name_company_dirty = True


    def saveNameCompany(self, s):
        self.name_company_dirty = False
        beginWaitCursor()
        try:
            try:
                log.debug("Saving station name %s to device" % s)
                self.dev.setStationName(s)
            except Error:
                CheckDeviceUI(self)
        finally:
            endWaitCursor()

    #
    # Fax Number (for TTI header) (stored in device)
    #

    def FaxNumberLineEdit_editingFinished(self):
        self.saveFaxNumber(to_unicode(self.FaxNumberLineEdit.text()))


    def FaxNumberLineEdit_textChanged(self, s):
        self.fax_number_dirty = True


    def saveFaxNumber(self, s):
        self.fax_number_dirty = False
        beginWaitCursor()
        try:
            try:
                log.debug("Saving fax number %s to device" % s)
                self.dev.setPhoneNum(s)
            except Error:
                CheckDeviceUI(self)
        finally:
            endWaitCursor()

    #
    # Voice Number (for coverpage) (stored in ~/.hplip/hplip.conf)
    #

    def VoiceNumberLineEdit_editingFinished(self):
        self.saveVoiceNumber(to_unicode(self.VoiceNumberLineEdit.text()))


    def VoiceNumberLineEdit_textChanged(self, s):
        self.voice_number_dirty = True


    def saveVoiceNumber(self, s):
        log.debug("Saving voice number (%s) to ~/.hplip/hplip.conf" % s)
        self.voice_number_dirty = False
        #user_conf.set('fax', 'voice_phone', s)
        self.user_settings.voice_phone = s
        self.user_settings.save()

    #
    # EMail (for coverpage) (stored in ~/.hplip/hplip.conf)
    #

    def EmailLineEdit_editingFinished(self):
        self.saveEmail(to_unicode(self.EmailLineEdit.text()))


    def EmailLineEdit_textChanged(self, s):
        self.email_dirty = True


    def saveEmail(self, s):
        log.debug("Saving email address (%s) to ~/.hplip/hplip.conf" % s)
        self.email_dirty = False
        #user_conf.set('fax', 'email_address', s)
        self.user_settings.email_address = s
        self.user_settings.save()

    #
    #
    #

    def CancelButton_clicked(self):
        self.close()

    def Tabs_currentChanged(self, tab=0):
        """ Called when the active tab changes.
            Update newly displayed tab.
        """        
        if tab == 0:
            self.updateHeaderTab()
        elif tab ==1:    
            self.updateCoverpageTab()
            

    def updateHeaderTab(self):
        beginWaitCursor()
        try:
            try:
                name_company = to_unicode(self.dev.getStationName())
                log.debug("name_company = '%s'" % name_company)
                self.NameCompanyLineEdit.setText(name_company)
                fax_number = str(self.dev.getPhoneNum())
                log.debug("fax_number = '%s'" % fax_number)
                self.FaxNumberLineEdit.setText(fax_number)
            except Error:
                CheckDeviceUI(self)
        finally:
            endWaitCursor()


    def updateCoverpageTab(self):
        #voice_phone = user_conf.get('fax', 'voice_phone')
        voice_phone = self.user_settings.voice_phone
        log.debug("voice_phone = '%s'" % voice_phone)
        self.VoiceNumberLineEdit.setText(voice_phone)
        #email_address = user_conf.get('fax', 'email_address')
        email_address = self.user_settings.email_address
        log.debug("email_address = '%s'" % email_address)
        self.EmailLineEdit.setText(email_address)


    def closeEvent(self, e):
        if self.voice_number_dirty:
            self.VoiceNumberLineEdit.editingFinished.emit()
        if self.name_company_dirty:
            self.NameCompanyLineEdit.editingFinished.emit()
        if self.email_dirty:
            self.EmailLineEdit.editingFinished.emit()
        if self.fax_number_dirty:
            self.FaxNumberLineEdit.editingFinished.emit()
        if self.dev is not None:
            self.dev.close()

        e.accept()

    #
    # Misc
    #

    def __tr(self,s,c = None):
        return qApp.translate("FaxSetupDialog",s,c)


