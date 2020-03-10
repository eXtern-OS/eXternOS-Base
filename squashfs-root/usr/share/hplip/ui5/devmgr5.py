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
# Authors: Don Welch, Naga Samrat Chowdary Narla
#

#from __future__ import generators

# Std Lib
import sys
import time
import os
import gzip
import select
import struct
import signal
from base.sixext.moves import configparser
# Local
from base.g import *
from base import device, utils, pml, maint, models, pkit, os_utils
from prnt import cups
from base.sixext import PY3
from base.codes import *
from .ui_utils import *
import hpmudext
from installer.core_install import *
# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import collections

# dbus
try:
    import dbus
    from dbus.mainloop.pyqt5 import DBusQtMainLoop
    from dbus import lowlevel
except ImportError:
    log.error("Unable to load DBus libraries. Please check your installation and try again.")
    if PY3:                        # Workaround due to incomplete Python3 support in Linux distros.
        log.error("Please upgrade your python installation to the latest available version.")
    sys.exit(1)

import warnings
# Ignore: .../dbus/connection.py:242: DeprecationWarning: object.__init__() takes no parameters
# (occurring on Python 2.6/dBus 0.83/Ubuntu 9.04)
warnings.simplefilter("ignore", DeprecationWarning)


# Main form
from .devmgr5_base import Ui_MainWindow
from .devmgr_ext import Ui_MainWindow_Derived
# Aux. dialogs
from .faxsetupdialog import FaxSetupDialog
from .plugindialog import PluginDialog
from .firmwaredialog import FirmwareDialog
from .aligndialog import AlignDialog
from .printdialog import PrintDialog
from .makecopiesdialog import MakeCopiesDialog
from .sendfaxdialog import SendFaxDialog
from .fabwindow import FABWindow
from .devicesetupdialog import DeviceSetupDialog
from .printtestpagedialog import PrintTestPageDialog
from .infodialog import InfoDialog
from .cleandialog import CleanDialog
from .colorcaldialog import ColorCalDialog
from .linefeedcaldialog import LineFeedCalDialog
from .pqdiagdialog import PQDiagDialog
from .nodevicesdialog import NoDevicesDialog
from .aboutdialog import AboutDialog

# Other forms and controls
from .settingsdialog import SettingsDialog
from .printsettingstoolbox import PrintSettingsToolbox


from base import os_utils

# all in seconds
MIN_AUTO_REFRESH_RATE = 5
MAX_AUTO_REFRESH_RATE = 60
DEF_AUTO_REFRESH_RATE = 30


device_list = {}    # { Device_URI : device.Device(), ... }
model_obj = models.ModelData() # Used to convert dbus xformed data back to plain Python types


# ***********************************************************************************
#
# ITEM/UTILITY UI CLASSES
#
# ***********************************************************************************


class FuncViewItem(QListWidgetItem):
    def __init__(self, parent, text, pixmap, tooltip_text, cmd):
        QListWidgetItem.__init__(self, QIcon(pixmap), text, parent)
        self.tooltip_text = tooltip_text
        self.cmd = cmd

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

class DeviceViewItem(QListWidgetItem):
    def __init__(self, parent, text, pixmap, device_uri, is_avail=True):
        QListWidgetItem.__init__(self, QIcon(pixmap), text, parent)
        self.device_uri = device_uri
        self.is_avail = is_avail
        self.setTextAlignment(Qt.AlignHCenter)

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

class PluginInstall(QObject):
    def __init__(self, parent, plugin_type, plugin_installed):
        self.parent = parent
        self.plugin_type = plugin_type
        self.plugin_installed = plugin_installed


    def exec_(self):
        install_plugin = True

        if self.plugin_installed:
            install_plugin = QMessageBox.warning(self.parent,
                                self.parent.windowTitle(),
                                self.__tr("<b>The HPLIP plugin is already installed.</b><p>Do you want to continue and re-install it?"),
                                QMessageBox.Yes,
                                QMessageBox.No,
                                QMessageBox.NoButton) == QMessageBox.Yes

        if install_plugin:
            ok, sudo_ok = pkit.run_plugin_command(self.plugin_type == PLUGIN_REQUIRED, self.parent.cur_device.mq['plugin-reason'])
            if not sudo_ok:
                QMessageBox.critical(self.parent,
                    self.parent.windowTitle(),
                    self.__tr("<b>Unable to find an appropriate su/sudo utility to run hp-plugin.</b><p>Install kdesu, gnomesu, or gksu.</p>"),
                    QMessageBox.Ok,
                    QMessageBox.NoButton,
                    QMessageBox.NoButton)


    def __tr(self,s,c = None):
        return qApp.translate("DevMgr5",s,c)



# ***********************************************************************************
#
# MAINWINDOW
#
# ***********************************************************************************

'''
class Ui_MainWindow_Derived(Ui_MainWindow):
    def setupUi(self, MainWindow, latest_available_version, Is_autoInstaller_distro):
        super().setupUi(MainWindow)
        self.DiagnoseQueueAction = QAction(MainWindow)
        self.DiagnoseQueueAction.setObjectName("DiagnoseQueueAction")
        self.DiagnoseHPLIPAction = QAction(MainWindow)
        self.DiagnoseHPLIPAction.setObjectName("DiagnoseHPLIPAction")
        
        self.latest_available_version = latest_available_version
        self.Is_autoInstaller_distro = Is_autoInstaller_distro
        if self.latest_available_version is not "":
            self.tab_3 = QWidget()
            self.tab_3.setObjectName("tab_3")
            self.label = QLabel(self.tab_3)
            self.label.setGeometry(QRect(30, 45, 300, 17))
            self.label.setObjectName("label")
            if self.Is_autoInstaller_distro:
                self.InstallLatestButton = QPushButton(self.tab_3)
                self.InstallLatestButton.setGeometry(QRect(351, 40, 96, 27))
                self.InstallLatestButton.setObjectName("pushButton")
            else:
                self.ManualInstalllabel = QLabel(self.tab_3)
                self.ManualInstalllabel.setGeometry(QRect(30, 70,300, 45))
                self.ManualInstalllabel.setObjectName("label")
                self.InstallLatestButton = QPushButton(self.tab_3)
                self.InstallLatestButton.setGeometry(QRect(295, 80, 110, 25))
                self.InstallLatestButton.setObjectName("pushButton")
            self.Tabs.addTab(self.tab_3, "")
        # super().setupUi(MainWindow)

    def retranslateUi(self, MainWindow):
        super().retranslateUi(MainWindow)
        if self.latest_available_version is not "":
            self.label.setText(QtGui.QApplication.translate("MainWindow", "New version of HPLIP-%s is available"%self.latest_available_version, None))
            self.Tabs.setTabText(self.Tabs.indexOf(self.tab_3), QtGui.QApplication.translate("MainWindow", "Upgrade", None))
            if self.Is_autoInstaller_distro:
                self.InstallLatestButton.setText(QtGui.QApplication.translate("MainWindow", "Install now", None))
            else:
                msg="Please install manually as mentioned in "
                self.ManualInstalllabel.setText(QtGui.QApplication.translate("MainWindow", msg, None))
                self.InstallLatestButton.setText(QtGui.QApplication.translate("MainWindow", "HPLIP website", None))
'''

class DevMgr5(Ui_MainWindow_Derived, Ui_MainWindow, QMainWindow):
    def __init__(self,  toolbox_version, initial_device_uri=None,
                 dbus_loop=None, parent=None, name=None, fl=0):

        # QMainWindow.__init__(self, parent)
        super(DevMgr5, self).__init__(parent)

        log.debug("Initializing toolbox UI (Qt5)...")
        log.debug("HPLIP Version: %s" % prop.installed_version)


        self.toolbox_version = toolbox_version
        self.initial_device_uri = initial_device_uri
        self.device_vars = {}
        self.num_devices = 0
        self.cur_device = None
        self.cur_printer = None
        self.updating = False
        self.init_failed = False
        self.service = None
        self.Is_autoInstaller_distro = False            # True-->tier1(supports auto installation). False--> tier2(manual installation)

        # Distro insformation
        core =  CoreInstall(MODE_CHECK)
#        core.init()
        self.Is_autoInstaller_distro = core.is_auto_installer_support()
        # User settings
        self.user_settings = UserSettings()
        self.user_settings.load()
        self.user_settings.debug()
        self.cur_device_uri = self.user_settings.last_used_device_uri
        installed_version=sys_conf.get('hplip','version')
        if not utils.Is_HPLIP_older_version( installed_version,  self.user_settings.latest_available_version):
            self.setupUi(self,"",self.Is_autoInstaller_distro)
        else:
            self.setupUi(self, self.user_settings.latest_available_version,self.Is_autoInstaller_distro)

        # Other initialization
        self.initDBus()
        self.initPixmaps()
        self.initMisc()
        self.initUI()

        cups.setPasswordCallback(showPasswordUI)

        if not prop.doc_build:
            self.ContentsAction.setEnabled(False)

        self.allow_auto_refresh = True
        QTimer.singleShot(0, self.initalUpdate)


    # ***********************************************************************************
    #
    # INIT
    #
    # ***********************************************************************************

    # TODO: Make sbus init mandatory success, else exit
    def initDBus(self):
        self.dbus_loop = DBusQtMainLoop(set_as_default=True)
        self.dbus_avail, self.service, self.session_bus = device.init_dbus(self.dbus_loop)

        if not self.dbus_avail:
            log.error("dBus initialization error. Exiting.")
            self.init_failed = True
            return

        # Receive events from the session bus
        self.session_bus.add_signal_receiver(self.handleSessionSignal, sender_keyword='sender',
            destination_keyword='dest', interface_keyword='interface',
            member_keyword='member', path_keyword='path')


    def initPixmaps(self):
        self.func_icons_cached = False
        self.func_icons = {}
        self.device_icons = {}

         # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))

        self.fax_icon = load_pixmap("fax2", "other")


    def initUI(self):
        # Setup device icon list
        self.DeviceList.setSortingEnabled(True)
        self.DeviceList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setDeviceListViewMode(QListView.IconMode)

        self.ViewAsIconsAction.triggered.connect(lambda: self.setDeviceListViewMode(QListView.IconMode))
        self.ViewAsListAction.triggered.connect(lambda: self.setDeviceListViewMode(QListView.ListMode))

        self.DeviceList.customContextMenuRequested["const QPoint &"].connect(self.DeviceList_customContextMenuRequested)

        # Setup main menu
        self.DeviceRefreshAction.setIcon(QIcon(load_pixmap("refresh1", "16x16")))
        self.DeviceRefreshAction.triggered.connect(self.DeviceRefreshAction_activated)

        self.RefreshAllAction.setIcon(QIcon(load_pixmap("refresh", "16x16")))
        self.RefreshAllAction.triggered.connect(self.RefreshAllAction_activated)

        self.SetupDeviceAction.setIcon(QIcon(load_pixmap('list_add', '16x16')))
        self.SetupDeviceAction.triggered.connect(self.SetupDeviceAction_activated)

        self.RemoveDeviceAction.setIcon(QIcon(load_pixmap('list_remove', '16x16')))
        self.RemoveDeviceAction.triggered.connect(self.RemoveDeviceAction_activated)

        self.PreferencesAction.setIcon(QIcon(load_pixmap('settings', '16x16')))
        self.PreferencesAction.triggered.connect(self.PreferencesAction_activated)

        self.DiagnoseQueueAction.setIcon(QIcon(load_pixmap('warning', '16x16')))
        self.DiagnoseQueueAction.triggered.connect(self.DiagnoseQueue_activated)

        self.DiagnoseHPLIPAction.setIcon(QIcon(load_pixmap('troubleshoot', '16x16')))
        self.DiagnoseHPLIPAction.triggered.connect(self.DiagnoseHPLIP_activated)

        self.ContentsAction.setIcon(QIcon(load_pixmap("help", "16x16")))
        self.ContentsAction.triggered.connect(self.helpContents)

        self.QuitAction.setIcon(QIcon(load_pixmap("quit", "16x16")))
        self.QuitAction.triggered.connect(self.quit)

        self.AboutAction.triggered.connect(self.helpAbout)

        self.PrintControlPrinterNameCombo.activated["const QString &"].connect(self.PrintControlPrinterNameCombo_activated)
        self.PrintSettingsPrinterNameCombo.activated["const QString &"].connect(self.PrintSettingsPrinterNameCombo_activated)
        signal.signal(signal.SIGINT, signal.SIG_IGN)


         # Init tabs/controls
        self.initActionsTab()
        self.initStatusTab()
        self.initSuppliesTab()
        self.initPrintSettingsTab()
        self.initPrintControlTab()


        self.Tabs.currentChanged[int].connect(self.Tabs_currentChanged)

        # Resize the splitter so that the device list starts as a single column
        self.splitter.setSizes([80, 600])

        # Setup the Device List
        self.DeviceList.setIconSize(QSize(60, 60))
        self.DeviceList.currentItemChanged["QListWidgetItem *", "QListWidgetItem *"].connect(self.DeviceList_currentChanged)


    def initMisc(self):
        self.TabIndex = { 0: self.updateActionsTab,
                          1: self.updateStatusTab,
                          2: self.updateSuppliesTab,
                          3: self.updatePrintSettingsTab,
                          4: self.updatePrintControlTab,
                          5:self.updateHPLIPupgrade,
                        }

        # docs
        self.docs = "http://hplip.sf.net"

        if prop.doc_build:
            g = os.path.join(sys_conf.get('dirs', 'doc'), 'index.html')
            if os.path.exists(g):
                self.docs = "file://%s" % g

        # support
        self.support = "https://launchpad.net/hplip"



    def initalUpdate(self):
        if self.init_failed:
            self.close()
            return

        self.rescanDevices()

        cont = True
        if self.initial_device_uri is not None:
            if not self.activateDevice(self.initial_device_uri):
                log.error("Device %s not found" % self.initial_device_uri)
                cont = False

        if self.cur_printer:
            self.getPrinterState()

            if self.printer_state == cups.IPP_PRINTER_STATE_STOPPED:
                self.cur_device.sendEvent(EVENT_PRINTER_QUEUE_STOPPED, self.cur_printer)

            if not self.printer_accepting:
                self.cur_device.sendEvent(EVENT_PRINTER_QUEUE_REJECTING_JOBS, self.cur_printer)


    def activateDevice(self, device_uri):
        log.debug(log.bold("Activate: %s %s %s" % ("*"*20, device_uri, "*"*20)))
        index = 0
        d = self.DeviceList.item(index) #firstItem()
        found = False

        while d is not None:
            if d.device_uri == device_uri:
                found = True
                self.DeviceList.setSelected(d, True)
                self.DeviceList.setCurrentItem(d)
                break

            index += 1
            d = self.DeviceList.item(index)

        return found



    # ***********************************************************************************
    #
    # UPDATES/NOTIFICATIONS
    #
    # ***********************************************************************************

    def handleSessionSignal(self, *args, **kwds):
        if kwds['interface'] == 'com.hplip.Toolbox' and \
            kwds['member'] == 'Event':

            log.debug("Handling event...")
            event = device.Event(*args[:6])
            event.debug()

            if event.event_code < EVENT_MIN_USER_EVENT:
                pass

            elif event.event_code == EVENT_DEVICE_UPDATE_REPLY:
                log.debug("EVENT_DEVICE_UPDATE_REPLY (%s)" % event.device_uri)
                dev = self.findDeviceByURI(event.device_uri)

                if dev is not None:
                    try:
                        self.service.GetStatus(event.device_uri, reply_handler=self.handleStatusReply,
                            error_handler=self.handleStatusError)

                    except dbus.exceptions.DBusException as e:
                        log.error("dbus call to GetStatus() failed.")

            elif event.event_code == EVENT_USER_CONFIGURATION_CHANGED:
                log.debug("EVENT_USER_CONFIGURATION_CHANGED")
                self.user_settings.load()

            elif event.event_code == EVENT_HISTORY_UPDATE:
                log.debug("EVENT_HISTORY_UPDATE (%s)" % event.device_uri)
                dev = self.findDeviceByURI(event.device_uri)
                if dev is not None:
                    self.updateHistory(dev)

            elif event.event_code == EVENT_SYSTEMTRAY_EXIT:
                log.debug("EVENT_SYSTEMTRAY_EXIT")
                log.warn("HPLIP Status Service was closed. HPLIP Device Manager will now exit.")
                cups.releaseCupsInstance()
                self.close()

            elif event.event_code == EVENT_RAISE_DEVICE_MANAGER:
                log.debug("EVENT_RAISE_DEVICE_MANAGER")
                self.showNormal()
                self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                self.raise_()

            elif event.event_code in (EVENT_DEVICE_START_POLLING,
                                      EVENT_DEVICE_STOP_POLLING,
                                      EVENT_POLLING_REQUEST):
                pass

            else:
                log.error("Unhandled event: %d" % event.event_code)


    def handleStatusReply(self, device_uri, data):
        dev = self.findDeviceByURI(device_uri)
        if dev is not None:
            t = {}
            for key in data:
                value = model_obj.convert_data(str(key), str(data[key]))
                t.setdefault(key, value)

            dev.dq = t.copy()
            for d in dev.dq:
                dev.__dict__[d.replace('-','_')] = dev.dq[d]

            self.updateDevice(dev)


    def handleStatusError(self, e):
        log.error(str(e))


    def updateHistory(self, dev=None):
        if dev is None:
            dev = self.cur_device

        try:
            self.service.GetHistory(dev.device_uri, reply_handler=self.handleHistoryReply,
                                    error_handler=self.handleHistoryError)
        except dbus.exceptions.DBusException as e:
            log.error("dbus call to GetHistory() failed.")


    def handleHistoryReply(self, device_uri, history):
        dev = self.findDeviceByURI(device_uri)
        if dev is not None:
            result = []
            history.reverse()

            for h in history:
                result.append(device.Event(*tuple(h)))

            try:
                self.error_code = result[0].event_code
            except IndexError:
                self.error_code = STATUS_UNKNOWN

            dev.error_state = STATUS_TO_ERROR_STATE_MAP.get(self.error_code, ERROR_STATE_CLEAR)
            dev.hist = result

            self.updateDevice(dev)


    def handleHistoryError(self, e):
        log.error(str(e))


    def sendMessage(self, device_uri, printer_name, event_code, username=prop.username,
                    job_id=0, title=''):

        device.Event(device_uri, printer_name, event_code, username,
                    job_id, title).send_via_dbus(self.session_bus)


    def timedRefresh(self):
        if not self.updating and self.user_settings.auto_refresh and self.allow_auto_refresh:
            log.debug("Refresh timer...")
            self.cleanupChildren()

            if self.user_settings.auto_refresh_type == 0:
                self.requestDeviceUpdate()
            else:
                self.rescanDevices()


    # ***********************************************************************************
    #
    # TAB/DEVICE CHANGE SLOTS
    #
    # ***********************************************************************************

    def Tabs_currentChanged(self, tab=0):
        """ Called when the active tab changes.
            Update newly displayed tab.
        """
        if self.cur_device is not None:
            self.TabIndex[tab]()

    def updateAllTabs(self):
        for tab in self.TabIndex:
            self.TabIndex[tab]()


    def updateCurrentTab(self):
        log.debug("updateCurrentTab()")
        self.TabIndex[self.Tabs.currentIndex()]()



    # ***********************************************************************************
    #
    # DEVICE ICON LIST/DEVICE UPDATE(S)
    #
    # ***********************************************************************************


    def DeviceRefreshAction_activated(self):
        self.DeviceRefreshAction.setEnabled(False)
        self.requestDeviceUpdate()
        self.DeviceRefreshAction.setEnabled(True)


    def RefreshAllAction_activated(self):
        self.rescanDevices()


    def setDeviceListViewMode(self, mode):
        if mode == QListView.ListMode:
            self.DeviceList.setViewMode(QListView.ListMode)
            self.ViewAsListAction.setEnabled(False)
            self.ViewAsIconsAction.setEnabled(True)
        else:
            self.DeviceList.setViewMode(QListView.IconMode)
            self.ViewAsListAction.setEnabled(True)
            self.ViewAsIconsAction.setEnabled(False)


    def createDeviceIcon(self, dev=None):
        if dev is None:
            dev = self.cur_device

        try:
            dev.icon
        except AttributeError:
            dev.icon = "default_printer"

        try:
            self.device_icons[dev.icon]
        except:
            self.device_icons[dev.icon] = load_pixmap(dev.icon, 'devices')

        pix = self.device_icons[dev.icon]

        w, h = pix.width(), pix.height()
        error_state = dev.error_state
        icon = QPixmap(w, h)
        p = QPainter(icon)
        p.eraseRect(0, 0, icon.width(), icon.height())
        p.drawPixmap(0, 0, pix)

        try:
            tech_type = dev.tech_type
        except AttributeError:
            tech_type = TECH_TYPE_NONE

        if dev.device_type == DEVICE_TYPE_FAX:
            p.drawPixmap(w - self.fax_icon.width(), 0, self.fax_icon)

        if error_state != ERROR_STATE_CLEAR:
            if tech_type in (TECH_TYPE_COLOR_INK, TECH_TYPE_MONO_INK):
                status_icon = getStatusOverlayIcon(error_state)[0] # ink
            else:
                status_icon = getStatusOverlayIcon(error_state)[1] # laser

            if status_icon is not None:
                p.drawPixmap(0, 0, status_icon)

        p.end()
        return icon


    def refreshDeviceList(self):
        global devices
        log.debug("Rescanning device list...")

        if 1:
            beginWaitCursor()
            self.updating = True

            self.setWindowTitle(self.__tr("Refreshing Device List - HP Device Manager"))
            self.statusBar().showMessage(self.__tr("Refreshing device list..."))

            self.cups_devices = device.getSupportedCUPSDevices(['hp', 'hpfax'])

            current = None

            try:
                adds = []
                for d in self.cups_devices:
                    if d not in device_list:
                        adds.append(d)

                log.debug("Adds: %s" % ','.join(adds))

                removals = []
                for d in device_list:
                    if d not in self.cups_devices:
                        removals.append(d)

                log.debug("Removals (1): %s" % ','.join(removals))

                updates = []
                for d in device_list:
                    if d not in adds and d not in removals:
                        updates.append(d)

                log.debug("Updates: %s" % ','.join(updates))

                for d in adds:
                    log.debug("adding: %s" % d)
                    # Note: Do not perform any I/O with this device.
                    dev = device.Device(d, service=self.service, disable_dbus=False)

                    if not dev.supported:
                        log.debug("Unsupported model - removing device.")
                        removals.append(d)
                        continue

                    icon = self.createDeviceIcon(dev)

                    if dev.device_type == DEVICE_TYPE_FAX:
                        DeviceViewItem(self.DeviceList,  self.__tr("%s (Fax)"%dev.model_ui),
                            icon, d)
                    else:
                        if dev.fax_type:
                            DeviceViewItem(self.DeviceList, self.__tr("%s (Printer)"%dev.model_ui),
                                icon, d)
                        else:
                            DeviceViewItem(self.DeviceList, dev.model_ui,
                                icon, d)

                    device_list[d] = dev

                log.debug("Removals (2): %s" % ','.join(removals))
                removed_device=None
                for d in removals:
                    removed_device = d
                    index = self.DeviceList.count()-1
                    item = self.DeviceList.item(index)
                    log.debug("removing: %s" % d)

                    try:
                        del device_list[d]
                    except KeyError:
                        pass

                    while index >= 0 and item is not None:
                        if item.device_uri == d:
                            self.DeviceList.takeItem(index)
                            break

                        index -= 1
                        item = self.DeviceList.item(index)

                    qApp.processEvents()

                self.DeviceList.updateGeometry()
                qApp.processEvents()

                if len(device_list):
                    for tab in self.TabIndex:
                        self.Tabs.setTabEnabled(tab, True)

                    if self.cur_device_uri:
                        index = 0
                        item = first_item = self.DeviceList.item(index)

                        while item is not None:
                            qApp.processEvents()
                            if item.device_uri == self.cur_device_uri:
                                current = item
                                self.statusBar().showMessage(self.cur_device_uri)
                                break

                            index += 1
                            item = self.DeviceList.item(index)

                        else:
                            self.cur_device = None
                            self.cur_device_uri = ''

                    if self.cur_device is None:
                        i = self.DeviceList.item(0)
                        if i is not None:
                            self.cur_device_uri = i.device_uri
                            self.cur_device = device_list[self.cur_device_uri]
                            current = i

                    self.updatePrinterCombos()

                    if self.cur_device_uri:
                        #user_conf.set('last_used', 'device_uri',self.cur_device_uri)
                        self.user_settings.last_used_device_uri = self.cur_device_uri
                        self.user_settings.save()

                    for d in updates + adds:
                        if d not in removals:
                            self.requestDeviceUpdate(device_list[d])

                else: # no devices
                    self.cur_device = None
                    self.DeviceRefreshAction.setEnabled(False)
                    self.RemoveDeviceAction.setEnabled(False)
                    self.DiagnoseQueueAction.setEnabled(False)
                    self.updating = False
                    self.statusBar().showMessage(self.__tr("Press F6 to refresh."))

                    for tab in self.TabIndex:
                        self.Tabs.setTabEnabled(tab, False)

                    endWaitCursor()

                    dlg = NoDevicesDialog(self)
                    dlg.exec_()

            finally:
                self.updating = False
                endWaitCursor()

            if current is not None:
                self.DeviceList.setCurrentItem(current)

            self.DeviceRefreshAction.setEnabled(True)

            if self.cur_device is not None:
                self.RemoveDeviceAction.setEnabled(True)
                self.DiagnoseQueueAction.setEnabled(True)

                self.statusBar().showMessage(self.cur_device_uri)
                self.updateWindowTitle()


    def updateWindowTitle(self):
        if self.cur_device.device_type == DEVICE_TYPE_FAX:
                self.setWindowTitle(self.__tr("HP Device Manager - %s (Fax)"%self.cur_device.model_ui))
        else:
            if self.cur_device.fax_type:
                self.setWindowTitle(self.__tr("HP Device Manager - %s (Printer)"%self.cur_device.model_ui))
            else:
                self.setWindowTitle(self.__tr("HP Device Manager - %s"%self.cur_device.model_ui))

        self.statusBar().showMessage(self.cur_device_uri)


    def updateDeviceByURI(self, device_uri):
        return self.updateDevice(self.findDeviceByURI(device_uri))


    def updateDevice(self, dev=None, update_tab=True):

        """ Update the device icon and currently displayed tab.
        """
        if dev is None:
            dev = self.cur_device

        log.debug("updateDevice(%s)" % dev.device_uri)

        item = self.findItem(dev)

        if item is not None:
            item.setIcon(QIcon(self.createDeviceIcon(dev)))

        if dev is self.cur_device and update_tab:
            self.updatePrinterCombos()
            self.updateCurrentTab()
            self.statusBar().showMessage(self.cur_device_uri)
            if self.cur_device.device_type == DEVICE_TYPE_PRINTER:
                self.Tabs.setTabText(self.Tabs.indexOf(self.Settings), QApplication.translate("MainWindow", "Print Settings", None))
                self.Tabs.setTabText(self.Tabs.indexOf(self.Control), QApplication.translate("MainWindow", "Printer Control", None))
            else:
                self.Tabs.setTabText(self.Tabs.indexOf(self.Settings), QApplication.translate("MainWindow", "Fax Settings", None))
                self.Tabs.setTabText(self.Tabs.indexOf(self.Control), QApplication.translate("MainWindow", "Fax Control", None))


    def DeviceList_currentChanged(self, i,  j):
        if i is not None and not self.updating:
            self.cur_device_uri = self.DeviceList.currentItem().device_uri
            self.cur_device = device_list[self.cur_device_uri]
            #user_conf.set('last_used', 'device_uri', self.cur_device_uri)
            self.user_settings.last_used_device_uri = self.cur_device_uri
            self.user_settings.save()

            self.updateDevice()
            self.updateWindowTitle()


    def findItem(self, dev):
        if dev is None:
            dev = self.cur_device

        return self.findItemByURI(dev.device_uri)


    def findItemByURI(self, device_uri):
        index = 0
        item = self.DeviceList.item(index)

        while item is not None:
            if item.device_uri == device_uri:
                return item

            index += 1
            item = self.DeviceList.item(index)


    def findDeviceByURI(self, device_uri):
        try:
            return device_list[device_uri]
        except:
            return None


    def requestDeviceUpdate(self, dev=None, item=None):
        """ Submit device update request to update thread. """

        if dev is None:
            dev = self.cur_device

        if dev is not None:
            dev.error_state = ERROR_STATE_REFRESHING
            self.updateDevice(dev, update_tab=False)

            self.sendMessage(dev.device_uri, '', EVENT_DEVICE_UPDATE_REQUESTED)


    def rescanDevices(self):
        """ Rescan and update all devices. """
        if not self.updating:
            self.RefreshAllAction.setEnabled(False)
            try:
                self.refreshDeviceList()
            finally:
                self.RefreshAllAction.setEnabled(True)


    def callback(self):
        qApp.processEvents()


    # ***********************************************************************************
    #
    # DEVICE LIST RIGHT CLICK
    #
    # ***********************************************************************************

    def DeviceList_customContextMenuRequested(self, p):
        d = self.cur_device

        if d is not None:
            avail = d.device_state != DEVICE_STATE_NOT_FOUND and d.supported
            printer = d.device_type == DEVICE_TYPE_PRINTER and avail

            fax = d.fax_type > FAX_TYPE_NONE and prop.fax_build and d.device_type == DEVICE_TYPE_FAX and \
                sys.hexversion >= 0x020300f0 and avail

            scan = d.scan_type > SCAN_TYPE_NONE and prop.scan_build and \
                            printer and self.user_settings.cmd_scan

            cpy = d.copy_type > COPY_TYPE_NONE and printer

            popup = QMenu(self)

            item = self.DeviceList.currentItem()
            if item is not None:
                if self.cur_device.error_state != ERROR_STATE_ERROR:
                    if printer:
                        popup.addAction(self.__tr("Print..."), lambda: self.contextMenuFunc(PrintDialog(self, self.cur_printer)))

                        if scan:
                            popup.addAction(self.__tr("Scan..."),  lambda: self.contextMenuFunc(self.user_settings.cmd_scan)) #self.ScanButton_clicked)

                        if cpy:
                            popup.addAction(self.__tr("Make Copies..."),  lambda: MakeCopiesDialog(self, self.cur_device_uri)) #self.MakeCopiesButton_clicked)

                    else: # self.cur_device.device_type == DEVICE_TYPE_FAX:
                        if fax:
                            popup.addAction(self.__tr("Send Fax..."),  lambda: self.contextMenuFunc(SendFaxDialog(self, self.cur_printer, self.cur_device_uri))) #self.SendFaxButton_clicked)

                    popup.addSeparator()

                if not self.updating:
                    popup.addAction(self.__tr("Refresh Device"),  self.requestDeviceUpdate) #self.DeviceRefreshAction_activated)

            if not self.updating:
                popup.addAction(self.__tr("Refresh All"),  self.rescanDevices) #self.RefreshAllAction_activated)

            popup.addSeparator()

            if self.DeviceList.viewMode() == QListView.IconMode:
                popup.addAction(self.__tr("View as List"), lambda: self.setDeviceListViewMode(QListView.ListMode))
            else:
                popup.addAction(self.__tr("View as Icons"), lambda: self.setDeviceListViewMode(QListView.IconMode))

            popup.exec_(self.DeviceList.mapToGlobal(p))


    def contextMenuFunc(self, f):
        self.sendMessage('', '', EVENT_DEVICE_STOP_POLLING)
        try:
            try:
                f.exec_() # Dialog
            except AttributeError:
                beginWaitCursor()

                if f.split(':')[0] in ('http', 'https', 'file'):
                    log.debug("Opening browser to: %s" % f)
                    utils.openURL(f)
                else:
                    self.runExternalCommand(f)

                QTimer.singleShot(1000, self.unlockClick)
        finally:
            self.sendMessage('', '', EVENT_DEVICE_START_POLLING)



    # ***********************************************************************************
    #
    # PRINTER NAME COMBOS
    #
    # ***********************************************************************************


    def updatePrinterCombos(self):
        self.PrintSettingsPrinterNameCombo.clear()
        self.PrintControlPrinterNameCombo.clear()

        if self.cur_device is not None and \
            self.cur_device.supported:

            self.cur_device.updateCUPSPrinters()

            for c in self.cur_device.cups_printers:
                self.PrintSettingsPrinterNameCombo.insertItem(0, c)
                self.PrintControlPrinterNameCombo.insertItem(0, c)

            self.cur_printer = to_unicode(self.PrintSettingsPrinterNameCombo.currentText())


    def PrintSettingsPrinterNameCombo_activated(self, s):
        self.cur_printer = to_unicode(s)
        self.updateCurrentTab()


    def PrintControlPrinterNameCombo_activated(self, s):
        self.cur_printer = to_unicode(s)
        self.updateCurrentTab()



    # ***********************************************************************************
    #
    # FUNCTIONS/ACTION TAB
    #
    # ***********************************************************************************

    def initActionsTab(self):
        self.click_lock = None
        self.ActionsList.setIconSize(QSize(32, 32))
        self.ActionsList.itemClicked["QListWidgetItem *"].connect(self.ActionsList_clicked)
        self.ActionsList.itemDoubleClicked["QListWidgetItem *"].connect(self.ActionsList_clicked)


    def updateActionsTab(self):
        beginWaitCursor()
        try:
            self.ActionsList.clear()

            d = self.cur_device

            if d is not None:
                avail = d.device_state != DEVICE_STATE_NOT_FOUND and d.supported
                fax = d.fax_type > FAX_TYPE_NONE and prop.fax_build and d.device_type == DEVICE_TYPE_FAX and \
                    sys.hexversion >= 0x020300f0 and avail
                printer = d.device_type == DEVICE_TYPE_PRINTER and avail
                scan = d.scan_type > SCAN_TYPE_NONE and prop.scan_build and \
                        printer and self.user_settings.cmd_scan
                cpy = d.copy_type > COPY_TYPE_NONE and printer
                req_plugin = d.plugin == PLUGIN_REQUIRED
                opt_plugin = d.plugin == PLUGIN_OPTIONAL

                try:
                    back_end, is_hp, bus, model, serial, dev_file, host, zc, port = \
                        device.parseDeviceURI(self.cur_device_uri)
                except Error:
                    return

                hplip_conf = configparser.ConfigParser()
                fp = open("/etc/hp/hplip.conf", "r")
                hplip_conf.readfp(fp)
                fp.close()

                try:
                    plugin_installed = utils.to_bool(hplip_conf.get("hplip", "plugin"))
                except configparser.NoOptionError:
                    plugin_installed = False

                if d.plugin != PLUGIN_NONE:
                    if req_plugin and plugin_installed:
                        x = self.__tr("Download and install<br>required plugin (already installed).")

                    elif req_plugin and not plugin_installed:
                        x = self.__tr("Download and install<br>required plugin (needs installation).")

                    elif opt_plugin and plugin_installed:
                        x = self.__tr("Download and install<br>optional plugin (already installed).")

                    elif opt_plugin and not plugin_installed:
                        x = self.__tr("Download and install<br>optional plugin (needs installation).")

                else:
                    x = ''

                # TODO: Cache this data structure
                #       -- add a field that specifies if the icon should always show, or only when device is avail.
                # TODO: Tooltips
                # TODO: Right-click icon/list view menu

                self.ICONS = [

                    # PRINTER

                    (lambda : printer,
                    self.__tr("Print"),                        # Text
                    "print",                                   # Icon
                    self.__tr("Print documents or files."),    # Tooltip
                    lambda : PrintDialog(self, self.cur_printer)),  # command/action

                    (lambda :scan,
                    self.__tr("Scan"),
                    "scan",
                    self.__tr("Scan a document, image, or photograph.<br>"),
                    self.user_settings.cmd_scan),

                    (lambda : cpy,
                    self.__tr("Make Copies"),
                    "makecopies",
                    self.__tr("Make copies on the device controlled by the PC.<br>"),
                    lambda : MakeCopiesDialog(self, self.cur_device_uri)),

                    # FAX

                    (lambda: fax,
                    self.__tr("Send Fax"),
                    "fax",
                    self.__tr("Send a fax from the PC."),
                    lambda : SendFaxDialog(self, self.cur_printer, self.cur_device_uri)),

                    (lambda: fax,
                    self.__tr("Fax Setup"),
                    "fax_setup",
                    self.__tr("Fax support must be setup before you can send faxes."),
                    lambda : FaxSetupDialog(self, self.cur_device_uri)),

                    (lambda: fax and self.user_settings.cmd_fab,
                    self.__tr("Fax Address Book"),
                    "fab",
                    self.__tr("Setup fax phone numbers to use when sending faxes from the PC."),
                    self.user_settings.cmd_fab),

                    # SETTINGS/TOOLS

                    (lambda : d.power_settings != POWER_SETTINGS_NONE and avail,
                    self.__tr("Device Settings"),
                    "settings",
                    self.__tr("Your device has special device settings.<br>You may alter these settings here."),
                    lambda : DeviceSetupDialog(self, self.cur_device_uri)),

                    (lambda : printer,
                    self.__tr("Print Test Page"),
                    "testpage",
                    self.__tr("Print a test page to test the setup of your printer."),
                    lambda : PrintTestPageDialog(self, self.cur_printer)),

                     (lambda : True,
                    self.__tr("View Printer and Device Information"),
                    "cups",
                    self.__tr("View information about the device and all its CUPS queues."),
                    lambda : InfoDialog(self, self.cur_device_uri)),

                    (lambda: printer and d.align_type != ALIGN_TYPE_NONE,
                    self.__tr("Align Cartridges (Print Heads)"),
                    "align",
                    self.__tr("This will improve the quality of output when a new cartridge is installed."),
                    lambda : AlignDialog(self, self.cur_device_uri)),

                    (lambda: printer and d.clean_type != CLEAN_TYPE_NONE,
                    self.__tr("Clean Printheads"),
                    "clean",
                    self.__tr("You only need to perform this action if you are<br>having problems with poor printout quality due to clogged ink nozzles."),
                    lambda : CleanDialog(self, self.cur_device_uri)),

                    (lambda: printer and d.color_cal_type != COLOR_CAL_TYPE_NONE and d.color_cal_type == COLOR_CAL_TYPE_TYPHOON,
                    self.__tr("Color Calibration"),
                    "colorcal",
                    self.__tr("Use this procedure to optimimize your printer's color output<br>(requires glossy photo paper)."),
                    lambda : ColorCalDialog(self, self.cur_device_uri)),

                    (lambda: printer and d.color_cal_type != COLOR_CAL_TYPE_NONE and d.color_cal_type != COLOR_CAL_TYPE_TYPHOON,
                    self.__tr("Color Calibration"),
                    "colorcal",
                    self.__tr("Use this procedure to optimimize your printer's color output."),
                    lambda : ColorCalDialog(self, self.cur_device_uri)),

                    (lambda: printer and d.linefeed_cal_type != LINEFEED_CAL_TYPE_NONE,
                    self.__tr("Line Feed Calibration"),
                    "linefeed_cal",
                    self.__tr("Use line feed calibration to optimize print quality<br>(to remove gaps in the printed output)."),
                    lambda : LineFeedCalDialog(self, self.cur_device_uri)),

                    (lambda: printer and d.pq_diag_type != PQ_DIAG_TYPE_NONE,
                    self.__tr("Print Diagnostic Page"),
                    "pq_diag",
                    self.__tr("Your printer can print a test page <br>to help diagnose print quality problems."),
                    lambda : PQDiagDialog(self, self.cur_device_uri)),

                    (lambda: printer and d.wifi_config >= WIFI_CONFIG_USB_XML and bus == 'usb',
                     self.__tr("Wireless/wifi setup using USB"),
                     "wireless",
                     self.__tr("Configure your wireless capable printer using a temporary USB connection."),
                     'hp-wificonfig -d %s' % self.cur_device_uri),

                    # FIRMWARE

                    (lambda : printer and d.fw_download ,
                    self.__tr("Download Firmware"),
                    "firmware",
                    self.__tr("Download firmware to your printer <br>(required on some devices after each power-up)."),
                    lambda : FirmwareDialog(self, self.cur_device_uri)),

                    # PLUGIN

                    (lambda : printer and req_plugin,
                    self.__tr("Install Required Plugin"),
                    "plugin",
                    x,
                    lambda : PluginInstall(self, d.plugin, plugin_installed)),

                    (lambda : printer and opt_plugin,
                    self.__tr("Install Optional Plugin"),
                    "plugin",
                    x,
                    lambda : PluginInstall(self, d.plugin, plugin_installed)),

                    # EWS

                    (lambda : printer and d.embedded_server_type > EWS_NONE and bus == 'net',
                     self.__tr("Open printer's web page in a browser"),
                     "ews",
                     self.__tr("The printer's web page has supply, status, and other information."),
                     openEWS(host, zc)),

                    # HELP/WEBSITE

                    (lambda : True,
                    self.__tr("Visit HPLIP Support Website"),
                    "hp_logo",
                    self.__tr("Visit HPLIP Support Website."),
                    self.support),

                    (lambda : True,
                    self.__tr("Help"),
                    "help",
                    self.__tr("View HPLIP help."),
                    self.docs),

                ]

                if not self.func_icons_cached:
                    for filte, text, icon, tooltip, cmd in self.ICONS:
                        self.func_icons[icon] = load_pixmap(icon, '32x32')
                    self.func_icons_cached = True

                for fltr, text, icon, tooltip, cmd in self.ICONS:
                    if fltr is not None:
                        if not fltr():
                            continue

                    FuncViewItem(self.ActionsList, text,
                        self.func_icons[icon],
                        tooltip,
                        cmd)
        finally:
            endWaitCursor()


    def ActionsList_clicked(self, item):
        if item is not None and self.click_lock is not item:
            self.click_lock = item
            if item.cmd and isinstance(item.cmd, collections.Callable):
                dlg = item.cmd()
                self.sendMessage('', '', EVENT_DEVICE_STOP_POLLING)
                try:
                    dlg.exec_()
                finally:
                    self.sendMessage('', '', EVENT_DEVICE_START_POLLING)

            else:
                beginWaitCursor()
                if item.cmd.split(':')[0] in ('http', 'https', 'file'):
                    log.debug("Opening browser to: %s" % item.cmd)
                    utils.openURL(item.cmd)
                else:
                    self.runExternalCommand(str(item.cmd))

            QTimer.singleShot(1000, self.unlockClick)


    def unlockClick(self):
        self.click_lock = None
        endWaitCursor()


    def ActionsList_customContextMenuRequested(self, p):
        print(p)
        #pass


    # ***********************************************************************************
    #
    # STATUS TAB
    #
    # ***********************************************************************************

    def initStatusTab(self):
        self.StatusTable.setColumnCount(0)
        self.status_headers = [self.__tr(""), self.__tr("Status"), self.__tr("Date and Time"),
                               self.__tr("Code"), self.__tr("Job ID"), self.__tr("Description")]


    def updateStatusTab(self):
        self.updateStatusLCD()
        self.updateStatusTable()


    def updateStatusLCD(self):
        if self.cur_device is not None and \
            self.cur_device.hist and \
            self.cur_device.supported:

            dq = self.cur_device.dq

            if dq.get('panel', 0) == 1:
                line1 = dq.get('panel-line1', '')
                line2 = dq.get('panel-line2', '')
            else:
                try:
                    line1 = device.queryString(self.cur_device.hist[0].event_code)
                except (AttributeError, TypeError):
                    line1 = ''

                line2 = ''

            self.drawStatusLCD(line1, line2)

        else:
            if self.cur_device.status_type == STATUS_TYPE_NONE:
                self.drawStatusLCD(self.__tr("Status information not"), self.__tr("available for this device."))

            elif not self.cur_device.supported:
                self.drawStatusLCD(self.__tr("Device not supported."))

            elif not self.cur_device.hist:
                self.drawStatusLCD(self.__tr("No status history available."))

            else:
                self.drawStatusLCD()


    def drawStatusLCD(self, line1='', line2=''):
        pm = load_pixmap('panel_lcd', 'other')

        p = QPainter()
        p.begin(pm)
        p.setPen(QColor(0, 0, 0))
        p.setFont(self.font())

        x, y_line1, y_line2 = 10, 17, 33

        # TODO: Scroll long lines
        if line1:
            p.drawText(x, y_line1, line1)

        if line2:
            p.drawText(x, y_line2, line2)

        p.end()

        self.LCD.setPixmap(pm)



    def updateStatusTable(self):
        self.StatusTable.clear()
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled

        row = 0
        hist = self.cur_device.hist[:]

        if hist:
            self.StatusTable.setRowCount(len(hist))
            self.StatusTable.setColumnCount(len(self.status_headers))
            self.StatusTable.setHorizontalHeaderLabels(self.status_headers)
            self.StatusTable.verticalHeader().hide()
            self.StatusTable.horizontalHeader().show()

            hist.reverse()
            row = len(hist)-1

            for e in hist:
                if e is None:
                    continue

                ess = device.queryString(e.event_code, 0)
                esl = device.queryString(e.event_code, 1)

                if row == 0:
                    desc = self.__tr("(most recent)")

                else:
                    desc = getTimeDeltaDesc(e.timedate)

                dt = QDateTime()
                dt.setTime_t(int(e.timedate)) #, Qt.LocalTime)

                # TODO: In Qt4.x, use QLocale.toString(date, format)
                tt = str("%s %s"%(dt.toString(),desc))

                if e.job_id:
                    job_id = to_unicode(e.job_id)
                else:
                    job_id = to_unicode('')

                error_state = STATUS_TO_ERROR_STATE_MAP.get(e.event_code, ERROR_STATE_CLEAR)
                tech_type = self.cur_device.tech_type

                if tech_type in (TECH_TYPE_COLOR_INK, TECH_TYPE_MONO_INK):
                    status_pix = getStatusListIcon(error_state)[0] # ink
                else:
                    status_pix = getStatusListIcon(error_state)[1] # laser

                event_code = to_unicode(e.event_code)

                i = QTableWidgetItem(QIcon(status_pix), self.__tr(""))
                i.setFlags(flags)
                self.StatusTable.setItem(row, 0, i)

                for col, t in [(1, ess), (2, tt), (3, event_code), (4, job_id), (5, esl)]:
                    i = QTableWidgetItem(str(t))
                    i.setFlags(flags)

                    self.StatusTable.setItem(row, col, i)

                row -= 1

            self.StatusTable.resizeColumnsToContents()
            self.StatusTable.setColumnWidth(0, 24)

        else:
            self.StatusTable.setRowCount(1)
            self.StatusTable.setColumnCount(2)
            self.StatusTable.setHorizontalHeaderLabels(["", ""])
            self.StatusTable.verticalHeader().hide()
            self.StatusTable.horizontalHeader().hide()

            flags = Qt.ItemIsEnabled

            pixmap = getStatusListIcon(ERROR_STATE_ERROR)[0]
            i = QTableWidgetItem(QIcon(pixmap), self.__tr(""))
            i.setFlags(flags)
            self.StatusTable.setItem(row, 0, i)

            i = QTableWidgetItem(self.__tr("Status information not available for this device."))
            i.setFlags(flags)
            self.StatusTable.setItem(0, 1, i)

            self.StatusTable.resizeColumnsToContents()
            self.StatusTable.setColumnWidth(0, 24)


    # ***********************************************************************************
    #
    # SUPPLIES TAB
    #
    # ***********************************************************************************

    def initSuppliesTab(self):
        self.pix_battery = load_pixmap('battery', '16x16')

        yellow = "#ffff00"
        light_yellow = "#ffffcc"
        cyan = "#00ffff"
        light_cyan = "#ccffff"
        magenta = "#ff00ff"
        light_magenta = "#ffccff"
        black = "#000000"
        blue = "#0000ff"
        gray = "#808080"
        dark_gray = "#a9a9a9"
        light_gray = "#c0c0c0"
        red = "#ff0000"

        self.TYPE_TO_PIX_MAP = {
                               AGENT_TYPE_UNSPECIFIED : [black],
                               AGENT_TYPE_BLACK: [black],
                               AGENT_TYPE_MATTE_BLACK : [black],
                               AGENT_TYPE_PHOTO_BLACK : [dark_gray],
                               AGENT_TYPE_BLACK_B8800: [black],
                               AGENT_TYPE_CMY: [cyan, magenta, yellow],
                               AGENT_TYPE_KCM: [light_cyan, light_magenta, light_yellow],
                               AGENT_TYPE_GGK: [dark_gray],
                               AGENT_TYPE_YELLOW: [yellow],
                               AGENT_TYPE_MAGENTA: [magenta],
                               AGENT_TYPE_CYAN : [cyan],
                               AGENT_TYPE_CYAN_LOW: [light_cyan],
                               AGENT_TYPE_YELLOW_LOW: [light_yellow],
                               AGENT_TYPE_MAGENTA_LOW: [light_magenta],
                               AGENT_TYPE_BLUE: [blue],
                               AGENT_TYPE_KCMY_CM: [yellow, cyan, magenta],
                               AGENT_TYPE_LC_LM: [light_cyan, light_magenta],
                               #AGENT_TYPE_Y_M: [yellow, magenta],
                               #AGENT_TYPE_C_K: [black, cyan],
                               AGENT_TYPE_LG_PK: [light_gray, dark_gray],
                               AGENT_TYPE_LG: [light_gray],
                               AGENT_TYPE_G: [gray],
                               AGENT_TYPE_DG: [dark_gray],
                               AGENT_TYPE_PG: [light_gray],
                               AGENT_TYPE_C_M: [cyan, magenta],
                               AGENT_TYPE_K_Y: [black, yellow],
                               AGENT_TYPE_LC: [light_cyan],
                               AGENT_TYPE_RED : [red],
                               }

        self.supplies_headers = [self.__tr(""), self.__tr("Description"),
                                 self.__tr("HP Part No."), self.__tr("Approx. Level"),
                                 self.__tr("Status")]


    def updateSuppliesTab(self):
        beginWaitCursor()
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled

        try:
            self.SuppliesTable.clear()
            self.SuppliesTable.setRowCount(0)
            self.SuppliesTable.setColumnCount(0)

            if self.cur_device is not None and \
                self.cur_device.supported and \
                self.cur_device.status_type != STATUS_TYPE_NONE and \
                self.cur_device.device_state != DEVICE_STATE_NOT_FOUND:
                self.cur_device.sorted_supplies = []
                a = 1
                while True:
                    try:
                        agent_type = int(self.cur_device.dq['agent%d-type' % a])
                        agent_kind = int(self.cur_device.dq['agent%d-kind' % a])
                        agent_sku = self.cur_device.dq['agent%d-sku' % a]
                    except KeyError:
                        break
                    else:
                        self.cur_device.sorted_supplies.append((a, agent_kind, agent_type, agent_sku))

                    a += 1

                self.cur_device.sorted_supplies.sort(key=utils.cmp_to_key(utils.levelsCmp))

                self.SuppliesTable.setRowCount(len(self.cur_device.sorted_supplies))
                self.SuppliesTable.setColumnCount(len(self.supplies_headers))
                self.SuppliesTable.setHorizontalHeaderLabels(self.supplies_headers)
                self.SuppliesTable.verticalHeader().hide()
                self.SuppliesTable.horizontalHeader().show()
                self.SuppliesTable.setIconSize(QSize(100, 18))

                for row, x in enumerate(self.cur_device.sorted_supplies):
                    a, agent_kind, agent_type, agent_sku = x
                    try:
                        agent_level = int(self.cur_device.dq['agent%d-level' % a])
                        agent_desc = self.cur_device.dq['agent%d-desc' % a]
                        agent_health_desc = self.cur_device.dq['agent%d-health-desc' % a]
                    except KeyError:
                        break
                    # Bar graph level
                    level_pixmap = None
                    if agent_kind in (AGENT_KIND_SUPPLY,
                                      #AGENT_KIND_HEAD,
                                      AGENT_KIND_HEAD_AND_SUPPLY,
                                      AGENT_KIND_TONER_CARTRIDGE,
                                      AGENT_KIND_MAINT_KIT,
                                      AGENT_KIND_ADF_KIT,
                                      AGENT_KIND_INT_BATTERY,
                                      AGENT_KIND_DRUM_KIT,
                                      ):

                        level_pixmap = self.createStatusLevelGraphic(agent_level, agent_type)

                    # Color icon
                    pixmap = None
                    if agent_kind in (AGENT_KIND_SUPPLY,
                                      AGENT_KIND_HEAD,
                                      AGENT_KIND_HEAD_AND_SUPPLY,
                                      AGENT_KIND_TONER_CARTRIDGE,
                                      #AGENT_KIND_MAINT_KIT,
                                      #AGENT_KIND_ADF_KIT,
                                      AGENT_KIND_INT_BATTERY,
                                      #AGENT_KIND_DRUM_KIT,
                                      ):

                        pixmap = self.getStatusIcon(agent_kind, agent_type)

                    if pixmap is not None:
                        i = QTableWidgetItem(QIcon(pixmap), self.__tr(""))
                        i.setFlags(flags)
                        self.SuppliesTable.setItem(row, 0, i)

                    for col, t in [(1, agent_desc), (2, agent_sku), (4, agent_health_desc)]:
                        i = QTableWidgetItem(str(t))
                        i.setFlags(flags)
                        self.SuppliesTable.setItem(row, col, i)

                    if level_pixmap is not None:
                        i = QTableWidgetItem(QIcon(level_pixmap), self.__tr(""))
                        i.setFlags(flags)
                        self.SuppliesTable.setItem(row, 3, i)

                self.SuppliesTable.resizeColumnsToContents()
                self.SuppliesTable.setColumnWidth(0, 24)
                self.SuppliesTable.setColumnWidth(3, 120)

            else: # No supplies info
                log.warning("Supplies information not available for this device.")
                flags = Qt.ItemIsEnabled
                self.SuppliesTable.setRowCount(1)
                self.SuppliesTable.setColumnCount(2)
                self.SuppliesTable.setHorizontalHeaderLabels(["", ""])
                self.SuppliesTable.verticalHeader().hide()
                self.SuppliesTable.horizontalHeader().hide()

                i = QTableWidgetItem(self.__tr("Supplies information not available for this device."))
                i.setFlags(flags)
                self.SuppliesTable.setItem(0, 1, i)

                pixmap = getStatusListIcon(ERROR_STATE_ERROR)[0]
                i = QTableWidgetItem(QIcon(pixmap), self.__tr(""))
                i.setFlags(flags)
                self.SuppliesTable.setItem(0, 0, i)

                self.SuppliesTable.resizeColumnsToContents()
                self.SuppliesTable.setColumnWidth(0, 24)

        finally:
            endWaitCursor()


    def getStatusIcon(self, agent_kind, agent_type):
        if agent_kind in (AGENT_KIND_SUPPLY,
                          AGENT_KIND_HEAD,
                          AGENT_KIND_HEAD_AND_SUPPLY,
                          AGENT_KIND_TONER_CARTRIDGE):

            map = self.TYPE_TO_PIX_MAP[agent_type]

            if isinstance(map, list):
                map_len = len(map)
                pix = QPixmap(16, 16)
                pix.fill(QColor(0, 0, 0, 0))
                p = QPainter()

                p.begin(pix)
                p.setRenderHint(QPainter.Antialiasing)

                if map_len == 1:
                    p.setPen(QColor(map[0]))
                    p.setBrush(QBrush(QColor(map[0]), Qt.SolidPattern))
                    p.drawPie(2, 2, 10, 10, 0, 5760)

                elif map_len == 2:
                    p.setPen(QColor(map[0]))
                    p.setBrush(QBrush(QColor(map[0]), Qt.SolidPattern))
                    p.drawPie(2, 4, 8, 8, 0, 5760)

                    p.setPen(QColor(map[1]))
                    p.setBrush(QBrush(QColor(map[1]), Qt.SolidPattern))
                    p.drawPie(6, 4, 8, 8, 0, 5760)

                elif map_len == 3:
                    p.setPen(QColor(map[2]))
                    p.setBrush(QBrush(QColor(map[2]), Qt.SolidPattern))
                    p.drawPie(6, 6, 8, 8, 0, 5760)

                    p.setPen(QColor(map[1]))
                    p.setBrush(QBrush(QColor(map[1]), Qt.SolidPattern))
                    p.drawPie(2, 6, 8, 8, 0, 5760)

                    p.setPen(QColor(map[0]))
                    p.setBrush(QBrush(QColor(map[0]), Qt.SolidPattern))
                    p.drawPie(4, 2, 8, 8, 0, 5760)

                p.end()
                return pix

            else:
                return map

        elif agent_kind == AGENT_KIND_INT_BATTERY:
                return self.pix_battery


    def createStatusLevelGraphic(self, percent, agent_type, w=100, h=18):
        if percent:
            fw = w/100*percent
        else:
            fw = 0

        px = QPixmap(w, h)
        px.fill(QColor(0, 0, 0, 0))
        pp = QPainter()
        pp.begin(px)
        pp.setRenderHint(QPainter.Antialiasing)
        pp.setPen(Qt.black)

        map = self.TYPE_TO_PIX_MAP[agent_type]
        map_len = len(map)

        if map_len == 1 or map_len > 3:
            pp.fillRect(0, 0, fw, h, QBrush(QColor(map[0])))

        elif map_len == 2:
            h2 = h / 2
            pp.fillRect(0, 0, fw, h2, QBrush(QColor(map[0])))
            pp.fillRect(0, h2, fw, h, QBrush(QColor(map[1])))

        elif map_len == 3:
            h3 = h / 3
            h23 = 2 * h3
            pp.fillRect(0, 0, fw, h3, QBrush(QColor(map[0])))
            pp.fillRect(0, h3, fw, h23, QBrush(QColor(map[1])))
            pp.fillRect(0, h23, fw, h, QBrush(QColor(map[2])))

        # draw black frame
        pp.drawRect(0, 0, w, h)

        if percent > 75 and agent_type in \
          (AGENT_TYPE_BLACK, AGENT_TYPE_UNSPECIFIED, AGENT_TYPE_BLUE):
            pp.setPen(Qt.white)

        # 75% ticks
        w1 = 3 * w / 4
        h6 = h / 6
        pp.drawLine(w1, 0, w1, h6)
        pp.drawLine(w1, h, w1, h-h6)

        if percent > 50 and agent_type in \
          (AGENT_TYPE_BLACK, AGENT_TYPE_UNSPECIFIED, AGENT_TYPE_BLUE):
            pp.setPen(Qt.white)

        # 50% ticks
        w2 = w / 2
        h4 = h / 4
        pp.drawLine(w2, 0, w2, h4)
        pp.drawLine(w2, h, w2, h-h4)

        if percent > 25 and agent_type in \
          (AGENT_TYPE_BLACK, AGENT_TYPE_UNSPECIFIED, AGENT_TYPE_BLUE):
            pp.setPen(Qt.white)

        # 25% ticks
        w4 = w / 4
        pp.drawLine(w4, 0, w4, h6)
        pp.drawLine(w4, h, w4, h-h6)

        pp.end()

        return px



    # ***********************************************************************************
    #
    # PRINTER SETTINGS TAB
    #
    # ***********************************************************************************

    def initPrintSettingsTab(self):
        pass


    def updatePrintSettingsTab(self):
        beginWaitCursor()
        try:
            if self.cur_device.device_type == DEVICE_TYPE_PRINTER:
                self.PrintSettingsPrinterNameLabel.setText(self.__tr("Printer Name:"))
            else:
                self.PrintSettingsPrinterNameLabel.setText(self.__tr("Fax Name:"))

            self.PrintSettingsToolbox.updateUi(self.cur_device, self.cur_printer)
        finally:
            endWaitCursor()


    # ***********************************************************************************
    #
    # PRINTER CONTROL TAB
    #
    # ***********************************************************************************

    def initPrintControlTab(self):
        self.JOB_STATES = { cups.IPP_JOB_PENDING : self.__tr("Pending"),
                            cups.IPP_JOB_HELD : self.__tr("On hold"),
                            cups.IPP_JOB_PROCESSING : self.__tr("Printing"),
                            cups.IPP_JOB_STOPPED : self.__tr("Stopped"),
                            cups.IPP_JOB_CANCELLED : self.__tr("Canceled"),
                            cups.IPP_JOB_ABORTED : self.__tr("Aborted"),
                            cups.IPP_JOB_COMPLETED : self.__tr("Completed"),
                           }

        self.CancelJobButton.setIcon(QIcon(load_pixmap('cancel', '16x16')))
        self.RefreshButton.setIcon(QIcon(load_pixmap('refresh', '16x16')))

        self.JOB_STATE_ICONS = { cups.IPP_JOB_PENDING: QIcon(load_pixmap("busy", "16x16")),
                                 cups.IPP_JOB_HELD : QIcon(load_pixmap("busy", "16x16")),
                                 cups.IPP_JOB_PROCESSING : QIcon(load_pixmap("print", "16x16")),
                                 cups.IPP_JOB_STOPPED : QIcon(load_pixmap("warning", "16x16")),
                                 cups.IPP_JOB_CANCELLED : QIcon(load_pixmap("warning", "16x16")),
                                 cups.IPP_JOB_ABORTED : QIcon(load_pixmap("error", "16x16")),
                                 cups.IPP_JOB_COMPLETED : QIcon(load_pixmap("ok", "16x16")),
                                }

        self.StartStopButton.clicked.connect(self.StartStopButton_clicked)
        self.AcceptRejectButton.clicked.connect(self.AcceptRejectButton_clicked)
        self.SetDefaultButton.clicked.connect(self.SetDefaultButton_clicked)
        self.CancelJobButton.clicked.connect(self.CancelJobButton_clicked)
        self.RefreshButton.clicked.connect(self.RefreshButton_clicked)

        self.job_headers = [self.__tr("Status"), self.__tr("Title/Description"), self.__tr("Job ID")]

        # TODO: Check queues at startup and send events if stopped or rejecting


    def initUpgradeTab(self):
        self.InstallLatestButton.clicked.connect(self.InstallLatestButton_clicked)
        self.InstallLatestButton_lock = False


    def InstallLatestButton_clicked(self):
        if self.InstallLatestButton_lock is True:
            return
        if self.Is_autoInstaller_distro:
            self.InstallLatestButton.setEnabled(False)
            terminal_cmd = utils.get_terminal()
            if terminal_cmd is not None and utils.which("hp-upgrade"):
                cmd = terminal_cmd + " 'hp-upgrade -w'"
                os_utils.execute(cmd)
            else:
                log.error("Failed to run hp-upgrade command from terminal =%s "%terminal_cmd)
            self.InstallLatestButton.setEnabled(True)
        else:
            self.InstallLatestButton_lock = True
            utils.openURL("http://hplipopensource.com/hplip-web/install/manual/index.html")
            QTimer.singleShot(1000, self.InstallLatestButton_unlock)


    def InstallLatestButton_unlock(self):
        self.InstallLatestButton_lock = False


    def CancelJobButton_clicked(self):
        item = self.JobTable.currentItem()

        if item is not None:
            job_id, ok = value_int(item.data(Qt.UserRole))
            if ok and job_id:
               self.cur_device.cancelJob(job_id)
               QTimer.singleShot(1000, self.updatePrintControlTab)


    def RefreshButton_clicked(self):
        self.updatePrintControlTab()

    def  updateHPLIPupgrade(self):
        self.initUpgradeTab()




    def updatePrintControlTab(self):
        if self.cur_device.device_type == DEVICE_TYPE_PRINTER:
            self.PrintControlPrinterNameLabel.setText(self.__tr("Printer Name:"))
            self.groupBox.setTitle(QApplication.translate("MainWindow", "Printer Queue Control", None))
        else:
            self.PrintControlPrinterNameLabel.setText(self.__tr("Fax Name:"))
            self.groupBox.setTitle(QApplication.translate("MainWindow", "Fax Queue Control", None))

        self.JobTable.clear()
        self.JobTable.setRowCount(0)
        self.JobTable.setColumnCount(0)
        self.updatePrintController()
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        jobs = cups.getJobs()
        num_jobs = 0
        for j in jobs:
            if j.dest == self.cur_printer:
                num_jobs += 1

        if num_jobs:
            self.CancelJobButton.setEnabled(True)
            self.JobTable.setRowCount(num_jobs)
            self.JobTable.setColumnCount(len(self.job_headers))
            self.JobTable.setHorizontalHeaderLabels(self.job_headers)

            for row, j in enumerate(jobs):
                if j.dest == self.cur_printer:
                    i = QTableWidgetItem(self.JOB_STATE_ICONS[j.state], self.JOB_STATES[j.state])
                    i.setData(Qt.UserRole, j.id)
                    i.setFlags(flags)
                    self.JobTable.setItem(row, 0, i)

                    i = QTableWidgetItem(j.title)
                    i.setFlags(flags)
                    self.JobTable.setItem(row, 1, i)

                    i = QTableWidgetItem(to_unicode(j.id))
                    i.setFlags(flags)
                    self.JobTable.setItem(row, 2, i)


            self.JobTable.setCurrentCell(0, 0)
            self.JobTable.resizeColumnsToContents()

        else:
            self.CancelJobButton.setEnabled(False)


    def getPrinterState(self):
        self.printer_state = cups.IPP_PRINTER_STATE_IDLE
        self.printer_accepting = True
        cups_printers = cups.getPrinters()

        for p in cups_printers:
            if p.name == self.cur_printer:
                self.printer_state = p.state
                self.printer_accepting = p.accepting
                break


    def updatePrintController(self):
        # default printer
        self.SetDefaultButton.setText(self.__tr("Set as Default"))
        
        default_printer = cups.getDefaultPrinter()
            
        if self.cur_device.device_type == DEVICE_TYPE_PRINTER:
            device_string = "Printer"
        else:
            device_string = "Fax"

        if default_printer == self.cur_printer:
            self.SetDefaultLabel.setText(self.__tr("Default %s"%device_string))
            self.SetDefaultIcon.setPixmap(load_pixmap("ok", "16x16"))
            self.SetDefaultButton.setEnabled(False)

        else:
            self.SetDefaultLabel.setText(self.__tr("Not Default %s"%device_string))
            self.SetDefaultIcon.setPixmap(load_pixmap("info", "16x16"))
            self.SetDefaultButton.setEnabled(True)

        self.getPrinterState()

        # start/stop
        if self.printer_state == cups.IPP_PRINTER_STATE_IDLE:
            self.StartStopLabel.setText(self.__tr("Started/Idle"))
            self.StartStopIcon.setPixmap(load_pixmap("idle", "16x16"))
            self.StartStopButton.setText(self.__tr("Stop %s"%device_string))


        elif self.printer_state == cups.IPP_PRINTER_STATE_PROCESSING:
            self.StartStopLabel.setText(self.__tr("Started/Processing"))
            self.StartStopIcon.setPixmap(load_pixmap("busy", "16x16"))
            self.StartStopButton.setText(self.__tr("Stop %s"%device_string))

        else:
            self.StartStopLabel.setText(self.__tr("Stopped"))
            self.StartStopIcon.setPixmap(load_pixmap("warning", "16x16"))
            self.StartStopButton.setText(self.__tr("Start %s"%device_string))

        # reject/accept
        if self.printer_accepting:
            self.AcceptRejectLabel.setText(self.__tr("Accepting Jobs"))
            self.AcceptRejectIcon.setPixmap(load_pixmap("idle", "16x16"))
            self.AcceptRejectButton.setText(self.__tr("Reject Jobs"))

        else:
            self.AcceptRejectLabel.setText(self.__tr("Rejecting Jobs"))
            self.AcceptRejectIcon.setPixmap(load_pixmap("warning", "16x16"))
            self.AcceptRejectButton.setText(self.__tr("Accept Jobs"))



    def StartStopButton_clicked(self):
        beginWaitCursor()
        try:
            if self.printer_state in (cups.IPP_PRINTER_STATE_IDLE, cups.IPP_PRINTER_STATE_PROCESSING):
                result, result_str = cups.cups_operation(cups.stop, GUI_MODE, 'qt4', self, self.cur_printer)
                if result == cups.IPP_OK:
                    if self.cur_device.device_type == DEVICE_TYPE_PRINTER:
                        e = EVENT_PRINTER_QUEUE_STOPPED
                    else:
                        e = EVENT_FAX_QUEUE_STOPPED

            else:
                result, result_str = cups.cups_operation(cups.start, GUI_MODE, 'qt4', self, self.cur_printer)
                if result == cups.IPP_OK:
                    if self.cur_device.device_type == DEVICE_TYPE_PRINTER:
                        e = EVENT_PRINTER_QUEUE_STARTED
                    else:
                        e = EVENT_FAX_QUEUE_STARTED

            if result == cups.IPP_OK:
                self.updatePrintController()
                self.cur_device.sendEvent(e, self.cur_printer)
            else:
                FailureUI(self, self.__tr("<b>Start/Stop printer queue operation fails. </b><p>Error : %s"%result_str))
                cups.releaseCupsInstance()

        finally:
            endWaitCursor()



    def AcceptRejectButton_clicked(self):
        beginWaitCursor()
        try:
            if self.printer_accepting:
                result, result_str = cups.cups_operation(cups.reject, GUI_MODE, 'qt4', self, self.cur_printer)
                if result == cups.IPP_OK:
                    if self.cur_device.device_type == DEVICE_TYPE_PRINTER:
                        e = EVENT_PRINTER_QUEUE_REJECTING_JOBS
                    else:
                        e = EVENT_FAX_QUEUE_REJECTING_JOBS

            else:
                result, result_str = cups.cups_operation(cups.accept, GUI_MODE, 'qt4', self, self.cur_printer)
                if result == cups.IPP_OK:
                    if self.cur_device.device_type == DEVICE_TYPE_PRINTER:
                        e = EVENT_PRINTER_QUEUE_ACCEPTING_JOBS
                    else:
                        e = EVENT_FAX_QUEUE_ACCEPTING_JOBS

            if result == cups.IPP_OK:
                self.updatePrintController()
                self.cur_device.sendEvent(e, self.cur_printer)
            else:
                FailureUI(self, self.__tr("<b>Accept/Reject printer queue operation fails.</b><p>Error : %s"%result_str))
                cups.releaseCupsInstance()

        finally:
            endWaitCursor()



    def SetDefaultButton_clicked(self):
        beginWaitCursor()
        try:
            result, result_str = cups.cups_operation(cups.setDefaultPrinter, GUI_MODE, 'qt4', self, self.cur_printer.encode('utf8'))
            if result != cups.IPP_OK:
                FailureUI(self, self.__tr("<b>Set printer queue as default operation fails. </b><p>Error : %s"%result_str))
                cups.releaseCupsInstance()
            else:
                self.updatePrintController()
                if self.cur_device.device_type == DEVICE_TYPE_PRINTER:
                    e = EVENT_PRINTER_QUEUE_SET_AS_DEFAULT
                else:
                    e = EVENT_FAX_QUEUE_SET_AS_DEFAULT

                self.cur_device.sendEvent(e, self.cur_printer)

        finally:
            endWaitCursor()



    def cancelCheckedJobs(self):
        beginWaitCursor()
        try:
            item = self.JobTable.firstChild()
            while item is not None:
                if item.isOn():
                    self.cur_device.cancelJob(item.job_id)

                item = item.nextSibling()

        finally:
            endWaitCursor()


        self.updatePrintControlTab()




    # ***********************************************************************************
    #
    # EXIT/CHILD CLEANUP
    #
    # ***********************************************************************************

    def closeEvent(self, event):
        self.cleanup()
        event.accept()


    def cleanup(self):
        self.cleanupChildren()


    def cleanupChildren(self):
        log.debug("Cleaning up child processes.")
        try:
            os.waitpid(-1, os.WNOHANG)
        except OSError:
            pass


    def quit(self):
        self.cleanupChildren()
        cups.releaseCupsInstance()
        self.close()


    # ***********************************************************************************
    #
    # DEVICE SETTINGS PLUGIN
    #
    # ***********************************************************************************


    # ***********************************************************************************
    #
    # SETTINGS DIALOG
    #
    # ***********************************************************************************

    def PreferencesAction_activated(self, tab_to_show=0):
        dlg = SettingsDialog(self)
        dlg.TabWidget.setCurrentIndex(tab_to_show)

        if dlg.exec_() == QDialog.Accepted:
            self.user_settings.load()

            if self.cur_device is not None:
                self.cur_device.sendEvent(EVENT_USER_CONFIGURATION_CHANGED, self.cur_printer)


    # ***********************************************************************************
    #
    # SETUP/REMOVE
    #
    # ***********************************************************************************

    def SetupDeviceAction_activated(self):
        if utils.which('hp-setup'):
            cmd = 'hp-setup --gui'
        else:
            cmd = 'python ./setup.py --gui'

        log.debug(cmd)
        utils.run(cmd)
        self.rescanDevices()
        self.updatePrinterCombos()


    def RemoveDeviceAction_activated(self):
        if utils.which('hp-setup'):
            cmd = 'hp-setup --gui --remove'
        else:
            cmd = 'python ./setup.py --gui --remove'

        if self.cur_device_uri is not None:
            cmd += ' --device=%s' % self.cur_device_uri

        log.debug(cmd)
        utils.run(cmd)
        self.rescanDevices()
        self.updatePrinterCombos()


    def DiagnoseQueue_activated(self):
        if utils.which('hp-diagnose_queues'):
            cmd= 'hp-diagnose_queues --gui'
        else:
            cmd= 'python ./diagnose_queues.py --gui'
        log.debug(cmd)
#        ok, output = utils.run(cmd)
        os_utils.execute(cmd)


    def DiagnoseHPLIP_activated(self):
        if utils.which('hp-doctor'):
            cmd = 'hp-doctor -i -w'
        else:
            cmd = 'python ./doctor.py -i -w'

        terminal_cmd = utils.get_terminal()
        if terminal_cmd:
            cmd = terminal_cmd + " '%s'"%cmd
            os_utils.execute(cmd)



    # ***********************************************************************************
    #
    # MISC
    #
    # ***********************************************************************************

    def runExternalCommand(self, cmd, macro_char='%'):
        beginWaitCursor()

        try:
            if len(cmd) == 0:
                FailureUI(self,self.__tr("<p><b>Unable to run command. No command specified.</b><p>Use <pre>Configure...</pre> to specify a command to run."))
                log.error("No command specified. Use settings to configure commands.")
            else:
                log.debug("Run: %s %s (%s) %s" % ("*"*20, cmd, self.cur_device_uri, "*"*20))
                log.debug(cmd)

                try:
                    cmd = ''.join([self.cur_device.device_vars.get(x, x) \
           for x in cmd.split(macro_char)])
                except AttributeError:
                    pass

                log.debug(cmd)

                path = cmd.split()[0]
                args = cmd.split()

                log.debug(path)
                log.debug(args)

                self.cleanupChildren()
                os.spawnvp(os.P_NOWAIT, path, args)
                qApp.processEvents()

        finally:
            endWaitCursor()


    def helpContents(self):
        utils.openURL(self.docs)


    def helpAbout(self):
        dlg = AboutDialog(self, prop.version, self.toolbox_version + " (Qt4)")
        dlg.exec_()


    def __tr(self,s,c = None):
        return qApp.translate("DevMgr5",s,c)


# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

class PasswordDialog(QDialog):
    def __init__(self, prompt, parent=None, name=None, modal=0, fl=0):
        QDialog.__init__(self, parent)
        self.prompt = prompt

        Layout= QGridLayout(self)
        Layout.setMargin(11)
        Layout.setSpacing(6)

        self.PromptTextLabel = QLabel(self)
        Layout.addWidget(self.PromptTextLabel,0,0,1,3)

        self.UsernameTextLabel = QLabel(self)
        Layout.addWidget(self.UsernameTextLabel,1,0)

        self.UsernameLineEdit = QLineEdit(self)
        self.UsernameLineEdit.setEchoMode(QLineEdit.Normal)
        Layout.addWidget(self.UsernameLineEdit,1,1,1,2)

        self.PasswordTextLabel = QLabel(self)
        Layout.addWidget(self.PasswordTextLabel,2,0)

        self.PasswordLineEdit = QLineEdit(self)
        self.PasswordLineEdit.setEchoMode(QLineEdit.Password)
        Layout.addWidget(self.PasswordLineEdit,2,1,1,2)

        self.OkPushButton = QPushButton(self)
        Layout.addWidget(self.OkPushButton,3,2)

        self.languageChange()

        self.resize(QSize(420,163).expandedTo(self.minimumSizeHint()))

        self.OkPushButton.clicked.connect(self.accept)
        self.PasswordLineEdit.returnPressed.connect(self.accept)


    def getUsername(self):
        return to_unicode(self.UsernameLineEdit.text())


    def getPassword(self):
        return to_unicode(self.PasswordLineEdit.text())


    def languageChange(self):
        self.setWindowTitle(self.__tr("HP Device Manager - Enter Username/Password"))
        self.PromptTextLabel.setText(self.__tr(self.prompt))
        self.UsernameTextLabel.setText(self.__tr("Username:"))
        self.PasswordTextLabel.setText(self.__tr("Password:"))
        self.OkPushButton.setText(self.__tr("OK"))


    def __tr(self,s,c = None):
        return qApp.translate("DevMgr5",s,c)

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

def showPasswordUI(prompt):
    try:
        dlg = PasswordDialog(prompt, None)

        if dlg.exec_() == QDialog.Accepted:
            return (dlg.getUsername(), dlg.getPassword())

    finally:
        pass

    return ("", "")


def openEWS(host, zc):
    if zc:
        status, ip = hpmudext.get_zc_ip_address(zc)
        if status != hpmudext.HPMUD_R_OK:
            ip = "hplipopensource.com"
    else:
        ip = host
    return "http://%s" % ip
