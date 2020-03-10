# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'printtestpagedialog_base.ui'
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
        self.gridlayout.addWidget(self.line, 1, 0, 1, 4)
        self.PrinterNameCombo = PrinterNameComboBox(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.PrinterNameCombo.sizePolicy().hasHeightForWidth())
        self.PrinterNameCombo.setSizePolicy(sizePolicy)
        self.PrinterNameCombo.setObjectName("PrinterNameCombo")
        self.gridlayout.addWidget(self.PrinterNameCombo, 2, 0, 1, 4)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.gridlayout1 = QtWidgets.QGridLayout(self.groupBox)
        self.gridlayout1.setObjectName("gridlayout1")
        self.HPLIPTestPageRadioButton = QtWidgets.QRadioButton(self.groupBox)
        self.HPLIPTestPageRadioButton.setObjectName("HPLIPTestPageRadioButton")
        self.gridlayout1.addWidget(self.HPLIPTestPageRadioButton, 0, 0, 1, 1)
        self.PrinterDiagnosticRadioButto = QtWidgets.QRadioButton(self.groupBox)
        self.PrinterDiagnosticRadioButto.setEnabled(False)
        self.PrinterDiagnosticRadioButto.setObjectName("PrinterDiagnosticRadioButto")
        self.gridlayout1.addWidget(self.PrinterDiagnosticRadioButto, 1, 0, 1, 1)
        self.gridlayout.addWidget(self.groupBox, 3, 0, 1, 4)
        self.LoadPaper = LoadPaperGroupBox(Dialog)
        self.LoadPaper.setTitle("")
        self.LoadPaper.setObjectName("LoadPaper")
        self.gridlayout.addWidget(self.LoadPaper, 4, 0, 1, 4)
        spacerItem = QtWidgets.QSpacerItem(189, 61, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        self.gridlayout.addItem(spacerItem, 5, 1, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(400, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem1, 6, 0, 1, 2)
        self.PrintTestpageButton = QtWidgets.QPushButton(Dialog)
        self.PrintTestpageButton.setObjectName("PrintTestpageButton")
        self.gridlayout.addWidget(self.PrintTestpageButton, 6, 2, 1, 1)
        self.CancelButton = QtWidgets.QPushButton(Dialog)
        self.CancelButton.setObjectName("CancelButton")
        self.gridlayout.addWidget(self.CancelButton, 6, 3, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "HP Device Manager - Print Test Page"))
        self.label.setText(_translate("Dialog", "Print Test Page"))
        self.groupBox.setTitle(_translate("Dialog", "Type"))
        self.HPLIPTestPageRadioButton.setText(_translate("Dialog", "HPLIP test page (tests print driver)"))
        self.PrinterDiagnosticRadioButto.setText(_translate("Dialog", "Printer diagnostic page (does not test print driver)"))
        self.PrintTestpageButton.setText(_translate("Dialog", "Print Test Page"))
        self.CancelButton.setText(_translate("Dialog", "Cancel"))

from .loadpapergroupbox import LoadPaperGroupBox
from .printernamecombobox import PrinterNameComboBox
