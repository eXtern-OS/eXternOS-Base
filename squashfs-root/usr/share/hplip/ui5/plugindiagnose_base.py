# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plugindiagnose_base.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(500, 180)
        self.gridlayout = QtWidgets.QGridLayout(Dialog)
        self.gridlayout.setObjectName("gridlayout")
        self.StackedWidget = QtWidgets.QStackedWidget(Dialog)
        self.StackedWidget.setObjectName("StackedWidget")
        self.page = QtWidgets.QWidget()
        self.page.setObjectName("page")
        self.gridlayout1 = QtWidgets.QGridLayout(self.page)
        self.gridlayout1.setObjectName("gridlayout1")
        self.label = QtWidgets.QLabel(self.page)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridlayout1.addWidget(self.label, 0, 0, 1, 1)
        self.line = QtWidgets.QFrame(self.page)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridlayout1.addWidget(self.line, 1, 0, 1, 2)
        self.TitleLabel = QtWidgets.QLabel(self.page)
        self.TitleLabel.setWordWrap(True)
        self.TitleLabel.setObjectName("TitleLabel")
        self.gridlayout1.addWidget(self.TitleLabel, 2, 0, 1, 2)
        self.StackedWidget.addWidget(self.page)
        self.gridlayout.addWidget(self.StackedWidget, 0, 0, 1, 4)
        self.line_2 = QtWidgets.QFrame(Dialog)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridlayout.addWidget(self.line_2, 1, 0, 1, 4)
        self.NextButton = QtWidgets.QPushButton(Dialog)
        self.NextButton.setEnabled(True)
        self.NextButton.setObjectName("NextButton")
        self.gridlayout.addWidget(self.NextButton, 2, 2, 1, 1)
        self.CancelButton = QtWidgets.QPushButton(Dialog)
        self.CancelButton.setObjectName("CancelButton")
        self.gridlayout.addWidget(self.CancelButton, 2, 3, 1, 1)

        self.retranslateUi(Dialog)
        self.StackedWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "HP Device Manager - Plug-in Installer"))
        self.label.setText(_translate("Dialog", "Driver Plug-in Installation is required"))
        self.TitleLabel.setText(_translate("Dialog", "HP Device requires proprietary plug-in which is missing. Click \'Next\' to continue plug-in installation"))
        self.NextButton.setText(_translate("Dialog", "Next >"))
        self.CancelButton.setText(_translate("Dialog", "Cancel"))

