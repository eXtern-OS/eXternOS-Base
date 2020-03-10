# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'devicesetupdialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(700, 500)
        self.gridlayout = QtWidgets.QGridLayout(Dialog)
        self.gridlayout.setObjectName("gridlayout")
        self.label = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridlayout.addWidget(self.label, 0, 0, 1, 1)
        self.line = QtWidgets.QFrame(Dialog)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridlayout.addWidget(self.line, 1, 0, 1, 3)
        self.DeviceComboBox = DeviceUriComboBox(Dialog)
        self.DeviceComboBox.setObjectName("DeviceComboBox")
        self.gridlayout.addWidget(self.DeviceComboBox, 2, 0, 1, 3)
        self.TabWidget = QtWidgets.QTabWidget(Dialog)
        self.TabWidget.setObjectName("TabWidget")
        self.PowerSettingsTab = QtWidgets.QWidget()
        self.PowerSettingsTab.setObjectName("PowerSettingsTab")
        self.gridlayout1 = QtWidgets.QGridLayout(self.PowerSettingsTab)
        self.gridlayout1.setObjectName("gridlayout1")
        self.groupBox = QtWidgets.QGroupBox(self.PowerSettingsTab)
        self.groupBox.setObjectName("groupBox")
        self.gridlayout2 = QtWidgets.QGridLayout(self.groupBox)
        self.gridlayout2.setObjectName("gridlayout2")
        self.OnRadioButton = QtWidgets.QRadioButton(self.groupBox)
        self.OnRadioButton.setObjectName("OnRadioButton")
        self.gridlayout2.addWidget(self.OnRadioButton, 0, 0, 1, 2)
        self.hboxlayout = QtWidgets.QHBoxLayout()
        self.hboxlayout.setObjectName("hboxlayout")
        self.OffRadioButton = QtWidgets.QRadioButton(self.groupBox)
        self.OffRadioButton.setEnabled(True)
        self.OffRadioButton.setObjectName("OffRadioButton")
        self.hboxlayout.addWidget(self.OffRadioButton)
        self.DurationComboBox = QtWidgets.QComboBox(self.groupBox)
        self.DurationComboBox.setEnabled(False)
        self.DurationComboBox.setObjectName("DurationComboBox")
        self.hboxlayout.addWidget(self.DurationComboBox)
        self.gridlayout2.addLayout(self.hboxlayout, 1, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridlayout2.addItem(spacerItem, 1, 1, 1, 1)
        self.gridlayout1.addWidget(self.groupBox, 0, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(282, 51, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridlayout1.addItem(spacerItem1, 1, 0, 1, 1)
        self.TabWidget.addTab(self.PowerSettingsTab, "")
        self.gridlayout.addWidget(self.TabWidget, 3, 0, 1, 3)
        spacerItem2 = QtWidgets.QSpacerItem(510, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.gridlayout.addItem(spacerItem2, 4, 0, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(361, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem3, 5, 0, 1, 1)
        self.CancelButton = QtWidgets.QPushButton(Dialog)
        self.CancelButton.setObjectName("CancelButton")
        self.gridlayout.addWidget(self.CancelButton, 5, 2, 1, 1)

        self.retranslateUi(Dialog)
        self.TabWidget.setCurrentIndex(0)
        self.OffRadioButton.toggled['bool'].connect(self.DurationComboBox.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "HP Device Manager - Device Setup"))
        self.label.setText(_translate("Dialog", "Device Setup"))
        self.groupBox.setTitle(_translate("Dialog", "Automatic Power Off"))
        self.OnRadioButton.setText(_translate("Dialog", "Always leave printer on"))
        self.OffRadioButton.setText(_translate("Dialog", "Automatically turn printer off after:"))
        self.TabWidget.setTabText(self.TabWidget.indexOf(self.PowerSettingsTab), _translate("Dialog", "Power Settings"))
        self.CancelButton.setText(_translate("Dialog", "Close"))

from .deviceuricombobox import DeviceUriComboBox
