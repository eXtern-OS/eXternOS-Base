# -*- coding: utf-8 -*-
#
# (c) Copyright 2011-2015 HP Development Company, L.P.
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
# Authors: Amarnath Chitumalla
#

#global
import os
import os.path
import sys
import signal

# Local
from base.g import *
from base import utils
from prnt import cups
from base.codes import *
from base import validation
from .ui_utils import *


# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
HPLIP_INFO_SITE ="http://hplip.sourceforge.net/hplip_web.conf"

class Ui_Dialog(object):
    def setupUi(self, Dialog, printerName, device_uri,Error_msg):
        Dialog.setObjectName("Dialog")
        Dialog.resize(700, 180)
        self.printerName=printerName
        self.device_uri=device_uri
        self.Error_msg=Error_msg
        self.gridlayout = QGridLayout(Dialog)
        self.gridlayout.setObjectName("gridlayout")
        self.StackedWidget = QStackedWidget(Dialog)
        self.StackedWidget.setObjectName("StackedWidget")
        self.page = QWidget()
        self.page.setObjectName("page")
        self.gridlayout1 = QGridLayout(self.page)
        self.gridlayout1.setObjectName("gridlayout1")
        self.label = QLabel(self.page)
        font = QFont()
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridlayout1.addWidget(self.label, 0, 0, 1, 1)
        self.line = QFrame(self.page)
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridlayout1.addWidget(self.line, 1, 0, 1, 2)
        self.TitleLabel = QLabel(self.page)
        self.TitleLabel.setWordWrap(True)
        self.TitleLabel.setObjectName("TitleLabel")
        self.gridlayout1.addWidget(self.TitleLabel, 2, 0, 1, 2)
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        spacerItem2 = QSpacerItem(200, 51, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.gridlayout1.addItem(spacerItem2, 5, 1, 1, 1)
        self.StackedWidget.addWidget(self.page)
        self.gridlayout.addWidget(self.StackedWidget, 0, 0, 1, 5)
        self.line_2 = QFrame(Dialog)
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridlayout.addWidget(self.line_2, 1, 0, 1, 4)
        self.NextButton = QPushButton(Dialog)
        self.NextButton.setObjectName("NextButton")
        self.gridlayout.addWidget(self.NextButton, 2, 3, 1, 1)
        self.CancelButton = QPushButton(Dialog)
        self.CancelButton.setObjectName("CancelButton")
        self.gridlayout.addWidget(self.CancelButton, 2, 4, 1, 1)

        self.retranslateUi(Dialog)
        self.StackedWidget.setCurrentIndex(0)
        QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        if self.Error_msg ==  QUEUES_SMART_INSTALL_ENABLED:
            Dialog.setWindowTitle(QApplication.translate("Dialog", "HP SmartInstall/Mass storage Disabler", None))
        else:
            Dialog.setWindowTitle(QApplication.translate("Dialog", "HP Device Manager - Queues diagnose", None))
        if self.Error_msg == QUEUES_PAUSED:
            self.label.setText(QApplication.translate("Dialog", "Print/Fax Queue is Paused", None))
        elif self.Error_msg ==  QUEUES_SMART_INSTALL_ENABLED:
            self.label.setText(QApplication.translate("Dialog", "Smart Install Device(s) Detected", None))
        else:
            self.label.setText(QApplication.translate("Dialog", "Queue needs to be reconfigured", None))
            
        if self.Error_msg ==  QUEUES_SMART_INSTALL_ENABLED:
            text= "Smart Install is enabled in "+ self.printerName + " device(s). \nDo you want to download and disable smart install to perform device functionalities?"
        elif self.Error_msg == QUEUES_INCORRECT_PPD:
            text= "'"+ self.printerName + "' is using incorrect PPD file. Do you want to remove and reconfigure queue?"
        elif self.Error_msg == QUEUES_PAUSED:
            text="'"+ self.printerName + "' is paused. Do you want to enable queue?"
        elif self.Error_msg == QUEUES_CONFIG_ERROR:
            text="'"+ self.printerName + "' is not configured using hp-setup utility. Click 'Remove and Setup' to remove and reconfigure queue."

        if self.Error_msg != QUEUES_MSG_SENDING:
            self.TitleLabel.setText(QApplication.translate("Dialog", text, None))
#            if self.Error_msg == QUEUES_PAUSED or self.Error_msg == QUEUES_INCORRECT_PPD or self.Error_msg ==  QUEUES_SMART_INSTALL_ENABLED:
            if self.Error_msg == QUEUES_PAUSED or self.Error_msg == QUEUES_INCORRECT_PPD:
                self.NextButton.setText(QApplication.translate("Dialog", "Yes", None))
                self.CancelButton.setText(QApplication.translate("Dialog", "No", None))

            elif self.Error_msg ==  QUEUES_SMART_INSTALL_ENABLED:
                self.NextButton.setText(QApplication.translate("Dialog", "Download and Disable", None))
                self.CancelButton.setText(QApplication.translate("Dialog", "Cancel", None))

            else:
                self.NextButton.setText(QApplication.translate("Dialog", "Remove and Setup", None))
                self.CancelButton.setText(QApplication.translate("Dialog", "Cancel", None))


# Ui

class QueuesDiagnose(QDialog, Ui_Dialog):
    def __init__(self, parent, printerName, device_uri, Error_msg,passwordObj=None):
        QDialog.__init__(self, parent)
        self.result = False
        self.printerName = printerName
        self.device_uri = device_uri
        self.Error_msg = Error_msg
        self.passwordObj = passwordObj
        self.setupUi(self, self.printerName, self.device_uri,self.Error_msg)
        self.user_settings = UserSettings()
        self.user_settings.load()
        self.user_settings.debug()

        self.initUi()

    def init(self, printerName, device_uri, Error_msg):
        QDialog.__init__(self,None)
        self.printerName = printerName
        self.device_uri = device_uri
        self.Error_msg = Error_msg
        self.setupUi(self, printerName, device_uri,Error_msg)
        self.user_settings = UserSettings()
        self.user_settings.load()
        self.user_settings.debug()

        self.initUi()


    def initUi(self):
        # connect signals/slots
        self.CancelButton.clicked.connect(self.CancelButton_clicked)
        self.NextButton.clicked.connect(self.NextButton_clicked)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))


    #
    # Misc
    #
    def displayPage(self, page):
        self.updateStepText(page)
        self.StackedWidget.setCurrentIndex(page)

    def CancelButton_clicked(self):
        self.close()


    def NextButton_clicked(self):
        beginWaitCursor()
        try:
            if self.Error_msg ==  QUEUES_SMART_INSTALL_ENABLED:
                self.disable_smart_install()

            elif  self.Error_msg == QUEUES_PAUSED:
                cups.enablePrinter(self.printerName)
                msg ="'"+self.printerName+"' is enabled successfully"
                SuccessUI(self, self.__tr(msg))

            else:
                status, status_str = cups.cups_operation(cups.delPrinter, GUI_MODE, 'qt4', self, self.printerName)

                if status != cups.IPP_OK:
                    msg="Failed to remove ' "+self.printerName+" ' queue.\nRemove using hp-toolbox..."
                    FailureUI(self, self.__tr(msg))
                else:
                    msg="' "+self.printerName+" ' removed successfully.\nRe-configuring this printer by hp-setup..."
                    log.debug(msg)
                    path = utils.which('hp-setup')
                    if path:
                        log.debug("Starting hp-setup")
                        utils.run('hp-setup --gui')

        finally:
            endWaitCursor()
        self.result = True
        self.close()

    def showMessage(self,msg):
        FailureUI(self, self.__tr(msg))

    def showSuccessMessage(self,msg):
        SuccessUI(self, self.__tr(msg))

    def __tr(self,s,c = None):
        return qApp.translate("PluginDialog",s,c)


    def disable_smart_install(self):
        if not utils.check_network_connection():
            FailureUI(self, queryString(ERROR_NO_NETWORK))
        else:
            sts, HPLIP_file = utils.download_from_network(HPLIP_INFO_SITE)
            if sts == 0:
                hplip_si_conf = ConfigBase(HPLIP_file)
                source = hplip_si_conf.get("SMART_INSTALL","url","")
                if not source :
                    FailureUI(self, queryString(ERROR_FAILED_TO_DOWNLOAD_FILE, 0, HPLIP_INFO_SITE))
                    return 

            response_file, smart_install_run = utils.download_from_network(source)
            response_asc, smart_install_asc = utils.download_from_network(source+'.asc')
            
            if response_file == 0   and response_asc == 0:

                gpg_obj = validation.GPG_Verification()
                digsig_sts, error_str = gpg_obj.validate(smart_install_run, smart_install_asc)

                if ERROR_SUCCESS == digsig_sts:
                    sts, out = utils.run("sh %s"%smart_install_run)
                else:
                
                    if QMessageBox.question(self, " ",
                        self.__tr("<b>%s</b><p>Without this, it is not possible to authenticate and validate this tool prior to installation.</p>Do you still want to run Smart Install disabler?" %error_str),
                        QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                        # Disabling without verification.
                        sts, out = utils.run("sh %s"%smart_install_run)

            else:
                if response_asc:
                    FailureUI(self, queryString(ERROR_FAILED_TO_DOWNLOAD_FILE, 0, source + ".asc"))
                else:
                    FailureUI(self, queryString(ERROR_FAILED_TO_DOWNLOAD_FILE, 0, source))


