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
# Authors: Amarnath Chitumalla
#


# Local
from base.g import *
from base import device, utils, pkit
from prnt import cups
from base.codes import *
from .ui_utils import *
from installer import pluginhandler
from base.sixext import  to_unicode

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import signal

# Ui
from .plugindiagnose_base import Ui_Dialog



class PluginDiagnose(QDialog, Ui_Dialog):
    def __init__(self, parent, install_mode=PLUGIN_NONE, plugin_reason=PLUGIN_REASON_NONE, upgrade=False):
        QDialog.__init__(self, parent)
        self.install_mode = install_mode
        self.plugin_reason = plugin_reason
        self.plugin_path = None
        self.result = False
        self.pluginObj = pluginhandler.PluginHandle()
        self.setupUi(self)

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


    def PathLineEdit_textChanged(self, t):
        self.plugin_path = to_unicode(t)
        self.setPathIndicators()


    #
    # Misc
    #

    def displayPage(self, page):
        self.updateStepText(page)
        self.StackedWidget.setCurrentIndex(page)

    def CancelButton_clicked(self):
        self.close()


    def NextButton_clicked(self):
        self.NextButton.setEnabled(False)
        self.CancelButton.setEnabled(False)
        try:
            plugin = PLUGIN_REQUIRED 
            plugin_reason = PLUGIN_REASON_NONE
            ok, sudo_ok = pkit.run_plugin_command(plugin == PLUGIN_REQUIRED, plugin_reason)

            if not ok or self.pluginObj.getStatus() != pluginhandler.PLUGIN_INSTALLED:
                FailureUI(self, self.__tr("Failed to install Plug-in.\nEither you have chosen to skip the Plug-in installation  or entered incorrect Password."))

        finally:
            endWaitCursor()
        self.result = True
        self.close()


    def __tr(self,s,c = None):
        return qApp.translate("PluginDialog",s,c)

