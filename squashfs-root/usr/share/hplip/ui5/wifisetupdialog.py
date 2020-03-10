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
from base import device, models, wifi, LedmWifi
from base.codes import *
from base.sixext import  to_unicode
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Ui
from .wifisetupdialog_base import Ui_Dialog



PAGE_INTRO = 0 # Ask user to plugin temp USB connection
PAGE_DEVICES = 1 # Select a probed USB device
PAGE_NETWORK = 2 # Select a discovered SSID
PAGE_CONFIGURE_WIFI = 3 # Configure USB device on network
PAGE_EXIT = 4 #  Tell user if successful, unplug USB onnection


BUTTON_NEXT = 0
BUTTON_FINISH = 1
BUTTON_CONNECT = 3

SUCCESS_NOT_CONNECTED = 0
SUCCESS_AUTO_IP = 1
SUCCESS_CONNECTED = 2

ASSOCIATE_DELAY = 30
REFRESH_INTERVAL = 20


class DeviceTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, device_uri):
        QTableWidgetItem.__init__(self, text, QTableWidgetItem.UserType)
        self.device_uri = device_uri


class WifiSetupDialog(QDialog, Ui_Dialog):

    itemSelectionChanged = pyqtSignal()
    def __init__(self, parent, device_uri=None, standalone=True):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.device_uri = device_uri
        self.devices = {}
        self.networks = {}
        self.ssid = ''
        self.directed = False
        self.show_extended = False
        self.bus = 'usb'
        self.search = ''
        self.max_page = PAGE_EXIT
        self.location_cache = {} # { 'bssid' : <location>, ... }
        self.dev = None
        self.success = SUCCESS_NOT_CONNECTED
        self.ip = '0.0.0.0'
        self.hn = ''
        self.standalone = standalone
        self.initUi()
        self.adapterName = 'Wifi0'
        self.wifiObj = wifi

        #if self.device_uri is None:
        #    QTimer.singleShot(0, self.showIntroPage)
        #else:
        #    QTimer.singleShot(0, self.showNetworkPage)

        QTimer.singleShot(0, self.showIntroPage)


    #
    # INIT
    #

    def initUi(self):
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))

        # connect signals/slots
        # self.CancelButton.clicked.connect(self.CancelButton_clicked)
        self.CancelButton.clicked.connect(self.CancelButton_clicked)
        self.BackButton.clicked.connect(self.BackButton_clicked)
        self.NextButton.clicked.connect(self.NextButton_clicked)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self.initIntroPage()
        self.initDevicesPage()
        self.initNetworkPage()
        self.initConfigWifiPage()
        self.initExitPage()

    #
    # INTRO PAGE
    #

    def initIntroPage(self):
        self.Picture.setPixmap(load_pixmap("usb_connection", "other"))
        self.InfoIcon.setPixmap(load_pixmap("info", "16x16"))

        if self.standalone:
            self.MainTitleLabel.setText(self.__tr("""This utility allows you configure your wireless capable printer using a temporary USB connection. You will be prompted to disconnect the USB cable once wireless network setup is complete.

<p><i>Note: This configuration utility does not setup (install) your printer on this computer. Use hp-setup to setup your printer after it has been configured on the network by this utility.</i></p>
<p><i>Note: Only select wireless capable printers are supported by this utility.</i></p>"""))
        else:
            self.MainTitleLabel.setText(self.__tr("""This utility allows you configure your wireless capable printer using a temporary USB connection. You will be prompted to disconnect the USB cable once wireless network setup is complete.

<p><i>Note: Printer setup (installation) will continue after your printer is configured on the network.</i></p>
<p><i>Note: Only select wireless capable printers are supported by this utility.</i></p>"""))


    def showIntroPage(self):
        self.BackButton.setEnabled(False)
        self.NextButton.setEnabled(True)

        self.displayPage(PAGE_INTRO)


    #
    # DEVICES PAGE
    #

    def initDevicesPage(self):
        self.RefreshButton.clicked.connect(self.RefreshButton_clicked)


    def showDevicesPage(self):
        self.BackButton.setEnabled(True)
        self.setNextButton(BUTTON_NEXT)

        beginWaitCursor()
        try:
            if not self.devices:
                log.info("Searching on USB bus...")
                filter_dict = {'wifi-config' : (operator.gt, WIFI_CONFIG_NONE)}

                try:
                    from base import smart_install
                except ImportError:
                    log.error("Failed to Import smart_install.py from base")
                else:
                    endWaitCursor()
                    smart_install.disable(GUI_MODE, 'qt4')
                    beginWaitCursor()

                self.devices = device.probeDevices([self.bus], 0, 0, filter_dict, self.search)

        finally:
            endWaitCursor()

        self.clearDevicesTable()

        if self.devices:
            self.NextButton.setEnabled(True)
            self.DevicesFoundIcon.setPixmap(load_pixmap('info', '16x16'))

            if len(self.devices) == 1:
                self.DevicesFoundLabel.setText(self.__tr("<b>1 wireless capable device found.</b> Click <i>Next</i> to continue."))
            else:
                self.DevicesFoundLabel.setText(self.__tr("<b>%s wireless capable devices found.</b> Select the device to install and click <i>Next</i> to continue." % len(self.devices)))

            self.loadDevicesTable()

        else:
            self.NextButton.setEnabled(False)
            self.DevicesFoundIcon.setPixmap(load_pixmap('error', '16x16'))
            log.error("No devices found on bus: %s" % self.bus)
            self.DevicesFoundLabel.setText(self.__tr("<b>No wireless capable devices found.</b><br>Plug in your printer with a USB cable and click <i>Refresh</i> to search again."))

        self.displayPage(PAGE_DEVICES)


    def loadDevicesTable(self):
        self.DevicesTableWidget.setSortingEnabled(False)
        self.DevicesTableWidget.setRowCount(len(self.devices))

        headers = [self.__tr('Model'), self.__tr('Device URI')]
        device_uri_col = 1

        self.DevicesTableWidget.setColumnCount(len(headers))
        self.DevicesTableWidget.setHorizontalHeaderLabels(headers)
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled

        for row, d in enumerate(self.devices):
            back_end, is_hp, bus, model, serial, dev_file, host, zc, port = device.parseDeviceURI(d)
            model_ui = models.normalizeModelUIName(model)

            i = DeviceTableWidgetItem(str(model_ui), d)
            i.setFlags(flags)
            self.DevicesTableWidget.setItem(row, 0, i)

            i = QTableWidgetItem(str(d))
            i.setFlags(flags)
            self.DevicesTableWidget.setItem(row, device_uri_col, i)

        self.DevicesTableWidget.resizeColumnsToContents()
        self.DevicesTableWidget.setSortingEnabled(True)
        self.DevicesTableWidget.sortItems(0)
        self.DevicesTableWidget.selectRow(0)


    def clearDevicesTable(self):
        self.DevicesTableWidget.clear()
        self.DevicesTableWidget.setRowCount(0)
        self.DevicesTableWidget.setColumnCount(0)


    def RefreshButton_clicked(self):
        self.clearDevicesTable()
        self.devices = []
        QTimer.singleShot(0, self.showDevicesPage)


    #
    # NETWORK
    #

    def initNetworkPage(self):
        self.NetworksTableWidget.setIconSize(QSize(34, 20))
        self.ShowExtendedCheckBox.setChecked(False)
        self.ShowExtendedCheckBox.clicked[bool].connect(self.ShowExtendedCheckBox_clicked)
        self.SearchPushButton.clicked.connect(self.SearchPushButton_clicked)
        self.UndirectedRadioButton.clicked[bool].connect(self.UndirectedRadioButton_clicked)
        self.DirectedRadioButton.clicked[bool].connect(self.DirectedRadioButton_clicked)
        self.NetworksTableWidget.itemSelectionChanged.connect(self.NetworksTableWidget_itemSelectionChanged)


    def showNetworkPage(self):
        if self.dev is None:
            try:
                self.dev = device.Device(self.device_uri)
            except Error as e:
                FailureUI(self, self.__tr("<b>Error opening device:</b><p>%s</p><p>(%s)</p>") %(self.device_uri, str(e[0])))

                if self.dev is not None:
                    self.dev.close()

                self.close()
                return

        self.networks.clear()
        self.num_networks = 0

        try:
            adaptor_list = self.wifiObj.getWifiAdaptorID(self.dev)           
        except Error as e:
            self.showIOError(e)
            return
        
        if len(adaptor_list) == 0: 
            FailureUI(self, self.__tr("<b>Unable to locate wireless hardware on device.</b>"))
            if self.dev is not None:
                self.dev.close()

            self.close()

        log.debug("Turning on wireless radio...")
        try:            
            self.adaptor_id, self.adapterName, state, presence =  self.wifiObj.setAdaptorPower(self.dev, adaptor_list )
        except Error as e:
            self.showIOError(e)
            return
        if self.adaptor_id == -1:
            FailureUI(self, self.__tr("<b>Unable to turn on wireless adaptor.</b>"))
            if self.dev is not None:
                self.dev.close()

        log.debug("Adaptor ID: %s" % self.adaptor_id)
        log.debug("Adaptor name: %s" % self.adapterName)
        log.debug("Adaptor state: %s" % state)
        log.debug("Adaptor presence: %s" % presence)

        self.performScan()
        self.setNextButton(BUTTON_NEXT)
        self.displayPage(PAGE_NETWORK)


    def performScan(self):
        beginWaitCursor()
        try:
            self.ssid = to_unicode(self.SSIDLineEdit.text())
            if self.directed and self.ssid:
                try:                    
                    self.networks = self.wifiObj.performScan(self.dev, self.adapterName, self.ssid)                     
                except Error as e:
                    self.showIOError(e)
                    return
            else:
                try:                    
                    self.networks = self.wifiObj.performScan(self.dev, self.adapterName)                     
                except Error as e:
                    self.showIOError(e)
                    return
        finally:
            self.dev.close()
            endWaitCursor()
        self.num_networks = self.networks['numberofscanentries']
        self.clearNetworksTable()

        if self.num_networks:
            self.NextButton.setEnabled(True)
            self.NetworksFoundIcon.setPixmap(load_pixmap('info', '16x16'))

            if self.num_networks == 1:
                self.NetworksFoundLabel.setText(self.__tr("<b>1 wireless network found. </b> If the wireless network you would like to connect to is not listed, try entering a wireless network name and/or press <i>Search</i> to search again."))
            else:
                self.NetworksFoundLabel.setText(self.__tr("<b>%d wireless networks found.</b> If the wireless network you would like to connect to is not listed, try entering a wireless network name and/or press <i>Search</i> to search again." %self.num_networks))

            self.loadNetworksTable()

        else:
            self.NextButton.setEnabled(False)
            self.NetworksFoundIcon.setPixmap(load_pixmap('error', '16x16'))
            log.warning("No wireless networks found.")
            self.NetworksFoundLabel.setText(self.__tr("<b>No wireless networks found.</b><br>Enter a wireless network name and/or press <i>Search</i> to search again."))


    def ShowExtendedCheckBox_clicked(self, b):
        self.show_extended = b
        self.loadNetworksTable()


    def SearchPushButton_clicked(self):
        self.performScan()
        self.loadNetworksTable()


    def UndirectedRadioButton_clicked(self, b):
        self.directed = not b
        self.SSIDLineEdit.setEnabled(not b)


    def DirectedRadioButton_clicked(self, b):
        self.directed = b
        self.SSIDLineEdit.setEnabled(b)


    def loadNetworksTable(self):
        self.n, self.network = 0, to_unicode('')
        if self.num_networks:
            beginWaitCursor()
            try:
                if self.show_extended:
                    for n in range(self.num_networks):
                        bssid = self.networks['bssid-%d' % n]
                        ss = self.networks['signalstrength-%d' % n]
                        try:
                            self.location_cache[bssid]
                        except KeyError:
                            location = wifi.getLocation(bssid, ss)
                            lat = self.networks['latitude-%d' % n] = location.get('latitude', 'Unknown')
                            lng  = self.networks['longitude-%d' % n] = location.get('longitude', 'Unknown')
                            address = self.networks['address-%d' % n] = location.get('address', 'Unknown')
                            self.location_cache[bssid] = (lat, lng, address)
                        else:
                            self.networks['latitude-%d' % n], self.networks['longitude-%d' % n], self.networks['address-%d' % n] = \
                                self.location_cache[bssid]

                self.NetworksTableWidget.setSortingEnabled(False)
                self.NetworksTableWidget.setRowCount(self.num_networks)

                headers = [self.__tr('Network Name (SSID)'), self.__tr('Signal Strength'),
                            self.__tr("Security"), self.__tr("Mode")]

                if self.show_extended:
                    headers.extend([self.__tr('Channel'),
                            self.__tr("Address (BSSID)"), self.__tr("Location"),
                            self.__tr("Lat/Long")])

                self.NetworksTableWidget.setColumnCount(len(headers))
                self.NetworksTableWidget.setHorizontalHeaderLabels(headers)
                enabled_flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
                for n in range(self.num_networks):
                    name = self.networks['ssid-%d' % n]

                    if name == '(unknown)':
                        flags = None
                    else:
                        flags = enabled_flags

                    ss = self.networks['signalstrength-%d' % n]
                    sec = self.networks['encryptiontype-%d' % n]
                    mode = self.networks['communicationmode-%d' % n]

                    log.debug("%d: Name=%s, strength=%s, security=%s, mode=%s" % #, channel=%d bssid=%s" %
                        (n, name, ss, sec, mode))

                    if self.show_extended:
                        chn = self.networks['channel-%d' % n]
                        dbm = self.networks['dbm-%d' % n]
                        bssid = self.networks['bssid-%d' % n]
                        address = self.networks['address-%d' % n]
                        lat = self.networks['latitude-%d' % n]
                        lng = self.networks['longitude-%d' % n]

                        log.debug("%d: channel=%d bssid=%s dbm=%s lat=%s long=%s address=%s" %
                            (n, chn, bssid, dbm, lat, lng, address))

                    i = QTableWidgetItem(str(name))
                    if flags is not None: i.setFlags(flags)
                    i.setData(Qt.UserRole, n)
                    self.NetworksTableWidget.setItem(n, 0, i)

                    pixmap = load_pixmap('signal%d' % ss, 'other')
                    if self.show_extended:
                        i = QTableWidgetItem(QIcon(pixmap), self.__tr("%s/5 (%s dBm)" %(ss, dbm)))
                    else:
                        i = QTableWidgetItem(QIcon(pixmap), self.__tr("%s/5" % ss))
                    if flags is not None: i.setFlags(flags)
                    self.NetworksTableWidget.setItem(n, 1, i)

                    i = QTableWidgetItem(str(sec))
                    if flags is not None: i.setFlags(flags)
                    self.NetworksTableWidget.setItem(n, 2, i)

                    i = QTableWidgetItem(str(mode))
                    if flags is not None: i.setFlags(flags)
                    self.NetworksTableWidget.setItem(n, 3, i)

                    if self.show_extended:
                        i = QTableWidgetItem(str(str(chn)))
                        if flags is not None: i.setFlags(flags)
                        self.NetworksTableWidget.setItem(n, 4, i)

                        i = QTableWidgetItem(str(bssid))
                        if flags is not None: i.setFlags(flags)
                        self.NetworksTableWidget.setItem(n, 5, i)

                        i = QTableWidgetItem(str(address))
                        if flags is not None: i.setFlags(flags)
                        self.NetworksTableWidget.setItem(n, 6, i)

                        i = QTableWidgetItem(str("%s/%s" % (lat, lng)))
                        if flags is not None: i.setFlags(flags)
                        self.NetworksTableWidget.setItem(n, 7, i)


                self.NetworksTableWidget.resizeColumnsToContents()
                self.NetworksTableWidget.setSortingEnabled(True)
                self.NetworksTableWidget.sortItems(1, Qt.DescendingOrder)
                self.NetworksTableWidget.selectRow(0)
                # itemSelectionChanged = pyqtSignal()
                # self.NetworksTableWidget.emit(SIGNAL("itemSelectionChanged()"))
                self.NetworksTableWidget.itemSelectionChanged.emit()

            finally:
                endWaitCursor()
                self.NextButton.setEnabled(True)

        else:
            self.NextButton.setEnabled(False)


    def NetworksTableWidget_itemSelectionChanged(self):
        row = self.NetworksTableWidget.currentRow()
        item = self.NetworksTableWidget.item(row, 0)
        n, ok = value_int(item.data(Qt.UserRole))
        if ok:
            sec = self.networks['encryptiontype-%d' % n]
            if sec.lower() == 'none':
                self.setNextButton(BUTTON_CONNECT)
            else:
                self.setNextButton(BUTTON_NEXT)


    def clearNetworksTable(self):
        self.DevicesTableWidget.clear()
        self.DevicesTableWidget.setRowCount(0)
        self.DevicesTableWidget.setColumnCount(0)


    def RefreshButton2_clicked(self):
        self.clearNetworksTable()
        self.networks = {}
        QTimer.singleShot(0, self.showNetworkPage)


    #
    # CONFIGURE WIFI
    #

    def initConfigWifiPage(self):
        self.ShowKeyCheckBox.toggled[bool].connect(self.ShowKeyCheckBox_toggled)


    def showConfigWifiPage(self):
        self.setNextButton(BUTTON_CONNECT)
        self.SSIDLabel.setText(self.network)
        font = QFont()
        font.setPointSize(12)
        self.SSIDLabel.setFont(font)
        self.KeyLineEdit.setText(str())
        self.ShowKeyCheckBox.setChecked(False)
        self.StrengthIcon.setPixmap(load_pixmap('signal%d' % self.ss, 'other'))
        self.ConfigureIcon.setPixmap(load_pixmap('info', '16x16'))
        self.KeysIcon.setPixmap(load_pixmap('keys', '32x32'))

        if 'wpa' in self.security.lower():
            self.WPARadioButton.setChecked(True)

        elif 'wep' in self.security.lower():
            self.WEPRadioButton.setChecked(True)

        self.KeyLineEdit.setFocus()
        self.KeyLineEdit.setEchoMode(QLineEdit.Password)
        self.displayPage(PAGE_CONFIGURE_WIFI)


    def ShowKeyCheckBox_toggled(self, b):
        if b:
            self.KeyLineEdit.setEchoMode(QLineEdit.Normal)
        else:
            self.KeyLineEdit.setEchoMode(QLineEdit.Password)


    #
    # EXIT/CONNECT PAGE
    #

    def initExitPage(self):
        self.PageSpinBox.valueChanged[int].connect(self.PageSpinBox_valueChanged)
        self.RefreshTimer = QTimer(self)
        # self.RefreshTimer.timeout.connect(self.RefreshTimer_timeout)
        self.RefreshTimer.timeout.connect(self.RefreshTimer_timeout)
        self.pages = []
        self.page_index = 0
        self.PageSpinBox.setMinimum(1)


    def showExitPage(self):
        self.setNextButton(BUTTON_FINISH)
        self.NextButton.setEnabled(False)
        self.CancelButton.setEnabled(True)
        self.SSIDLabel_2.setText(str(self.network))
        self.ip = '0.0.0.0'
        self.hn = ''
        self.success = SUCCESS_NOT_CONNECTED

        beginWaitCursor()
        try:
            try:                
                self.ip,_,addressmode, subnetmask, gateway, pridns, sec_dns= self.wifiObj.getIPConfiguration(self.dev, self.adapterName)
                if self.ip == "0.0.0.0":
                    self.ip, subnetmask, gateway, pri_dns, sec_dns, addressmode = self.wifiobj.getwifiotherdetails(self.dev,self.adapterName)
                vsa_codes = self.wifiObj.getVSACodes(self.dev, self.adapterName)
                ss_max, ss_min, ss_val, ss_dbm = self.wifiObj.getSignalStrength(self.dev, self.adapterName,self.network, self.adaptor_id)                 
                self.hn = self.wifiObj.getHostname(self.dev) 
            except Error as e:
                self.showIOError(e)
                return
        finally:
            self.dev.close()
            endWaitCursor()

        if 'dhcp' or 'default' in addressmode.lower():
            self.success = SUCCESS_CONNECTED

        elif addressmode.lower() == 'autoip':
            self.success = SUCCESS_AUTO_IP

        if self.ip == '0.0.0.0':
            self.success = SUCCESS_NOT_CONNECTED

        self.pages = []

        if self.success == SUCCESS_NOT_CONNECTED:
            self.pages.append((self.__tr("<b>Your printer has not been connected to the wireless network.</b> A valid connection to a wireless network can take up to 2 minutes. This screen will automatically refresh every %s seconds.<p>If your printer fails to connect within a reasonable time, there may be a problem with your configuration." % REFRESH_INTERVAL), load_pixmap('error', '16x16')))
            self.RefreshTimer.start(REFRESH_INTERVAL * 1000)

        elif self.success == SUCCESS_AUTO_IP:
#            self.pages.append((self.__tr("Your printer has been connected to the wireless network, but it has been assigned an address which may not be usable."), load_pixmap('warning', '16x16')))
            self.pages.append((self.__tr("Your printer has been connected to the wireless network and has been assinged a IP. Now run <pre>hp-setup %s</pre>  If IP is not accessible, try again for another IP."%self.ip), load_pixmap('warning', '16x16')))
       #     self.RefreshTimer.start(REFRESH_INTERVAL * 1000)
            self.CancelButton.setEnabled(False)
            self.BackButton.setEnabled(False)
            self.RefreshTimer.stop()

        else: # SUCCESS_CONNECTED
            self.pages.append((self.__tr("Your printer has been successfully configured on the wireless network. You may now unplug the USB cable. To setup the printer, now run <pre>hp-setup %s</pre>"%self.ip), load_pixmap('info', '16x16')))
            self.CancelButton.setEnabled(False)
            self.BackButton.setEnabled(False)
            self.RefreshTimer.stop()

        if addressmode is None:
            self.AddressModeLabel.setText(self.__tr("Unknown"))
        else:
            self.AddressModeLabel.setText(str(addressmode))

        if self.hn is None:
            self.HostnameLabel.setText(self.__tr("Unknown"))
        else:
            self.HostnameLabel.setText(str(self.hn))

        self.IPAddressLabel.setText(str(self.ip))
        self.GatewayLabel.setText(str(gateway))
        self.DNSLabel.setText(str(pridns))
        self.NextButton.setEnabled(True)

        self.SignalStrengthLabel.setText(str("%s/%s (%s dBm)" % (ss_val, ss_max, ss_dbm)))
        self.SignalStrengthIcon.setPixmap(load_pixmap('signal%d' % ss_val, 'other'))

        for c, s in vsa_codes:
            if c :
                ss = s.lower()
                if ss.startswith("info"):
                    pixmap = load_pixmap('info', '16x16')

                elif ss.startswith("warn"):
                    pixmap = load_pixmap('warning', '16x16')

                elif ss.startswith("crit"):
                    pixmap = load_pixmap('error', '16x16')

                else:
                    pixmap = load_pixmap('info', '16x16')

                self.pages.append((device.queryString("vsa_%s" % str(c).zfill(3)), pixmap))

        num_pages = len(self.pages)
        self.PageSpinBox.setMaximum(num_pages)
        self.PageSpinBox.setEnabled(num_pages>1)
        self.PageSpinBox.setValue(1)
        self.PageLabel.setEnabled(num_pages>1)
        self.PageLabel2.setEnabled(num_pages>1)
        self.PageLabel.setText(self.__tr("of %s", str(num_pages)))
        self.page_index = 0
        self.ExitLabel.setText(self.pages[self.page_index][0])
        self.ExitIcon.setPixmap(self.pages[self.page_index][1])
        self.displayPage(PAGE_EXIT)


    def PageSpinBox_valueChanged(self, i):
        self.page_index = i-1
        self.ExitLabel.setText(self.pages[self.page_index][0])
        self.ExitIcon.setPixmap(self.pages[self.page_index][1])


    def RefreshTimer_timeout(self):
        self.showExitPage()


    #
    # ASSOCIATE
    #

    def associate(self, key=to_unicode('')):
        beginWaitCursor()
        try:
            try:                
                alg, mode, secretid = self.wifiObj.getCryptoSuite(self.dev, self.adapterName)
            except Error as e:
                self.showIOError(e)
                return

            log.debug("Crypto algorithm: %s" % alg)
            log.debug("Crypto mode: %s" % mode)
        finally:
            endWaitCursor()

        beginWaitCursor()
        try:
            try:
                self.wifiObj.associate(self.dev, self.adapterName, self.network, self.mode, self.security, key) 
            except Error as e:
                self.showIOError(e)
                return
        finally:
            endWaitCursor()


    #
    # Misc
    #

    def NextButton_clicked(self):
        p = self.StackedWidget.currentIndex()
        if p == PAGE_INTRO:
            self.showDevicesPage()

        elif p == PAGE_DEVICES:
            row = self.DevicesTableWidget.currentRow()
            if row != -1:
                self.device_uri = self.DevicesTableWidget.item(row, 0).device_uri
                self.mq = device.queryModelByURI(self.device_uri)
                
                self.getWifiObject(self.mq['wifi-config'])               
                back_end, is_hp, bus, model, serial, dev_file, host, zc, port = device.parseDeviceURI(self.device_uri)
                self.model = models.normalizeModelName(model).lower()

            self.showNetworkPage()

        elif p == PAGE_NETWORK:
            self.security = 'None'
            self.mode = 'Infrastructure'
            self.ss = 0
            row = self.NetworksTableWidget.currentRow()
            if row != -1:
                i = self.NetworksTableWidget.item(row, 0)
                if i is not None:
                    self.network = to_unicode(i.text())
                    log.debug("Selected network SSID: %s" % self.network)
                    self.n, ok = value_int(i.data(Qt.UserRole))
                    if ok:
                        self.security = self.networks['encryptiontype-%d' % self.n]
                        log.debug("Security: %s" % self.security)

                        self.mode = self.networks['communicationmode-%d' % self.n]
                        log.debug("Mode: %s" % self.mode)

                        self.ss = self.networks['signalstrength-%d' % self.n]
                        log.debug("Signal strength: %s" % self.ss)

            if self.security.lower() != 'none':
                self.showConfigWifiPage()
            else:
                # Skip config page if no security to setup
                self.associate()
                self.showAssociateProgressDialog()
                self.showExitPage()

        elif p == PAGE_CONFIGURE_WIFI:
            key = to_unicode(self.KeyLineEdit.text())
            self.associate(key)
            self.showAssociateProgressDialog()
            self.showExitPage()

        elif p == PAGE_EXIT:
            if self.dev is not None:
                self.dev.close()

            self.close()

        else:
            log.error("Invalid page!") # shouldn't happen!


    def showAssociateProgressDialog(self):
        AssociateProgressDialog = QProgressDialog(self.__tr("Waiting for printer to connect to the wireless network..."), self.__tr("Cancel"), 0, ASSOCIATE_DELAY, self)
        AssociateProgressDialog.setWindowTitle(self.__tr("HP Device Manager - Please wait..."))
        AssociateProgressDialog.setWindowModality(Qt.WindowModal)
        AssociateProgressDialog.setMinimumDuration(0)
        AssociateProgressDialog.forceShow()
        canceled = False
        for x in range(ASSOCIATE_DELAY):
            AssociateProgressDialog.setValue(x)
            QThread.sleep(1)
            qApp.processEvents()

            if AssociateProgressDialog.wasCanceled():
                canceled = True
                break

        AssociateProgressDialog.setValue(ASSOCIATE_DELAY)
        AssociateProgressDialog.close()

        if canceled:
            if self.dev is not None:
                self.dev.close()

            self.close()


    def BackButton_clicked(self):
        p = self.StackedWidget.currentIndex()
        if p == PAGE_DEVICES:
            self.devices = {}
            self.showIntroPage()

        elif p == PAGE_NETWORK:
            self.showDevicesPage()

        elif p == PAGE_CONFIGURE_WIFI:
            self.showNetworkPage()

        elif p == PAGE_EXIT:
            self.RefreshTimer.stop()
            if self.security.lower() != 'none':
                self.showConfigWifiPage()
            else:
                self.showNetworkPage()

        else:
            log.error("Invalid page!") # shouldn't happen!


    def CancelButton_clicked(self):
        if self.dev is not None:
            self.dev.close()

        self.close()


    def displayPage(self, page):
        self.StackedWidget.setCurrentIndex(page)
        self.updateStepText(page)


    def setNextButton(self, typ=BUTTON_FINISH):
        if typ == BUTTON_NEXT:
            self.NextButton.setText(self.__tr("Next >"))

        elif typ == BUTTON_FINISH:
            self.NextButton.setText(self.__tr("Finish"))

        elif typ == BUTTON_CONNECT:
            self.NextButton.setText(self.__tr("Connect"))


    def updateStepText(self, p):
        self.StepText.setText(self.__tr("Step %s of %s" % (p+1, self.max_page+1)))


    def showIOError(self, e):
        FailureUI(self, self.__tr("<b>An I/O error occurred.</b><p>Please check the USB connection to your printer and try again.</p>(%s)" % str(e[0])))

        if self.dev is not None:
            self.dev.close()

        self.close()


    def __tr(self,s,c = None):
        return qApp.translate("WifiSetupDialog",s,c)

    # The Wifi object here is not actual object, Dynamically relevant modules are selected based on 
    # wifi-config value in the models file.
    def getWifiObject(self,wifiConfVal):
        if wifiConfVal == WIFI_CONFIG_LEDM:                    
            self.wifiObj = LedmWifi
        else:                    
            self.wifiObj = wifi
        
