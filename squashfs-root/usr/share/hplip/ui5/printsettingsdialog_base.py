# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'printsettingsdialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(700, 500)
        self.gridlayout = QtWidgets.QGridLayout(Dialog)
        self.gridlayout.setObjectName("gridlayout")
        self.TitleLabel = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.TitleLabel.setFont(font)
        self.TitleLabel.setObjectName("TitleLabel")
        self.gridlayout.addWidget(self.TitleLabel, 0, 0, 1, 1)
        self.line = QtWidgets.QFrame(Dialog)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridlayout.addWidget(self.line, 1, 0, 1, 2)
        self.PrinterName = PrinterNameComboBox(Dialog)
        self.PrinterName.setObjectName("PrinterName")
        self.gridlayout.addWidget(self.PrinterName, 2, 0, 1, 2)
        self.OptionsToolBox = PrintSettingsToolbox(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.OptionsToolBox.sizePolicy().hasHeightForWidth())
        self.OptionsToolBox.setSizePolicy(sizePolicy)
        self.OptionsToolBox.setObjectName("OptionsToolBox")
        self.gridlayout.addWidget(self.OptionsToolBox, 3, 0, 1, 2)
        spacerItem = QtWidgets.QSpacerItem(461, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem, 4, 0, 1, 1)
        self.CloseButton = QtWidgets.QPushButton(Dialog)
        self.CloseButton.setObjectName("CloseButton")
        self.gridlayout.addWidget(self.CloseButton, 4, 1, 1, 1)

        self.retranslateUi(Dialog)
        self.OptionsToolBox.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "HP Device Manager - Print Settings"))
        self.TitleLabel.setText(_translate("Dialog", "Print Settings"))
        self.CloseButton.setText(_translate("Dialog", "Close"))

from .printernamecombobox import PrinterNameComboBox
from .printsettingstoolbox import PrintSettingsToolbox
