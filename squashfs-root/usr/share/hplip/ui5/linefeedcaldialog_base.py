# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'linefeedcaldialog_base.ui'
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
        self.LoadPaper = LoadPaperGroupBox(Dialog)
        self.LoadPaper.setTitle("")
        self.LoadPaper.setObjectName("LoadPaper")
        self.gridlayout.addWidget(self.LoadPaper, 3, 0, 1, 3)
        spacerItem = QtWidgets.QSpacerItem(410, 81, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem, 4, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(361, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem1, 5, 0, 1, 1)
        self.CalibrateButton = QtWidgets.QPushButton(Dialog)
        self.CalibrateButton.setObjectName("CalibrateButton")
        self.gridlayout.addWidget(self.CalibrateButton, 5, 1, 1, 1)
        self.CancelButton = QtWidgets.QPushButton(Dialog)
        self.CancelButton.setObjectName("CancelButton")
        self.gridlayout.addWidget(self.CancelButton, 5, 2, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "HP Device Manager - Line Feed Calibration"))
        self.label.setText(_translate("Dialog", "Line Feed Calibration"))
        self.CalibrateButton.setText(_translate("Dialog", "Calibrate"))
        self.CancelButton.setText(_translate("Dialog", "Cancel"))

from .deviceuricombobox import DeviceUriComboBox
from .loadpapergroupbox import LoadPaperGroupBox
