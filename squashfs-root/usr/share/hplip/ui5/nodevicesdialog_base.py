# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'nodevicesdialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_NoDevicesDialog_base(object):
    def setupUi(self, NoDevicesDialog_base):
        NoDevicesDialog_base.setObjectName("NoDevicesDialog_base")
        NoDevicesDialog_base.resize(539, 335)
        self.gridlayout = QtWidgets.QGridLayout(NoDevicesDialog_base)
        self.gridlayout.setContentsMargins(11, 11, 11, 11)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")
        self.Icon = QtWidgets.QLabel(NoDevicesDialog_base)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Icon.sizePolicy().hasHeightForWidth())
        self.Icon.setSizePolicy(sizePolicy)
        self.Icon.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.Icon.setScaledContents(True)
        self.Icon.setWordWrap(False)
        self.Icon.setObjectName("Icon")
        self.gridlayout.addWidget(self.Icon, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 280, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem, 1, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 16, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem1, 2, 2, 1, 1)
        self.textLabel7 = QtWidgets.QLabel(NoDevicesDialog_base)
        self.textLabel7.setAlignment(QtCore.Qt.AlignVCenter)
        self.textLabel7.setWordWrap(True)
        self.textLabel7.setObjectName("textLabel7")
        self.gridlayout.addWidget(self.textLabel7, 0, 1, 2, 4)
        spacerItem2 = QtWidgets.QSpacerItem(400, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem2, 3, 0, 1, 2)
        self.SetupButton = QtWidgets.QPushButton(NoDevicesDialog_base)
        self.SetupButton.setObjectName("SetupButton")
        self.gridlayout.addWidget(self.SetupButton, 3, 2, 1, 1)
        self.CUPSButton = QtWidgets.QPushButton(NoDevicesDialog_base)
        self.CUPSButton.setObjectName("CUPSButton")
        self.gridlayout.addWidget(self.CUPSButton, 3, 3, 1, 1)
        self.CloseButton = QtWidgets.QPushButton(NoDevicesDialog_base)
        self.CloseButton.setDefault(True)
        self.CloseButton.setObjectName("CloseButton")
        self.gridlayout.addWidget(self.CloseButton, 3, 4, 1, 1)

        self.retranslateUi(NoDevicesDialog_base)
        QtCore.QMetaObject.connectSlotsByName(NoDevicesDialog_base)

    def retranslateUi(self, NoDevicesDialog_base):
        _translate = QtCore.QCoreApplication.translate
        NoDevicesDialog_base.setWindowTitle(_translate("NoDevicesDialog_base", "HP Device Manager - No Installed HP Devices Found"))
        self.textLabel7.setText(_translate("NoDevicesDialog_base", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:x-large; font-weight:600;\">No Installed HP Devices Found.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">To setup a new device in the HP Device Manager (toolbox), use one of the following methods:</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">1.Run <span style=\" font-weight:600;\">hp-setup</span> (in a shell/terminal or click <span style=\" font-family:\'Courier New,courier\';\">Setup Device...</span> below).</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">2. <span style=\" font-weight:600;\">CUPS web interface</span> (open a browser to: <span style=\" text-decoration: underline;\">http://localhost:631</span> or press the button below),</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">3. The <span style=\" font-weight:600;\">printer installation utility</span> that came with your operating system (YaST, PrinterDrake, etc). </p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">After setting up a printer, you may have to press <span style=\" font-family:\'Courier New,courier\';\">F6</span> or chose <span style=\" font-family:\'Courier New,courier\';\">Device | Refresh All</span> for the printer to appear in the HP Device Manager.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600; font-style:italic;\">Note: Only devices installed with the </span><span style=\" font-family:\'Courier New,courier\'; font-weight:600; font-style:italic;\">hp:</span><span style=\" font-weight:600; font-style:italic;\"> or </span><span style=\" font-family:\'Courier New,courier\'; font-weight:600; font-style:italic;\">hpfax:</span><span style=\" font-weight:600; font-style:italic;\"> CUPS backend will appear in the HP Device Manager.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"></p></body></html>"))
        self.SetupButton.setText(_translate("NoDevicesDialog_base", "Setup Device..."))
        self.CUPSButton.setText(_translate("NoDevicesDialog_base", "CUPS Web Interface"))
        self.CloseButton.setText(_translate("NoDevicesDialog_base", "Close"))

