# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pluginlicensedialog_base.ui'
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
        self.gridlayout1.addWidget(self.line, 1, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.page)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName("label_2")
        self.gridlayout1.addWidget(self.label_2, 2, 0, 1, 1)
        self.LicenseTextEdit = QtWidgets.QTextEdit(self.page)
        self.LicenseTextEdit.setAutoFormatting(QtWidgets.QTextEdit.AutoAll)
        self.LicenseTextEdit.setReadOnly(True)
        self.LicenseTextEdit.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.LicenseTextEdit.setObjectName("LicenseTextEdit")
        self.gridlayout1.addWidget(self.LicenseTextEdit, 3, 0, 1, 1)
        self.AgreeCheckBox = QtWidgets.QCheckBox(self.page)
        self.AgreeCheckBox.setObjectName("AgreeCheckBox")
        self.gridlayout1.addWidget(self.AgreeCheckBox, 4, 0, 1, 1)
        self.StackedWidget.addWidget(self.page)
        self.gridlayout.addWidget(self.StackedWidget, 0, 0, 1, 5)
        self.line_2 = QtWidgets.QFrame(Dialog)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridlayout.addWidget(self.line_2, 1, 0, 1, 5)
        spacerItem = QtWidgets.QSpacerItem(161, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem, 2, 1, 1, 1)
        self.BackButton = QtWidgets.QPushButton(Dialog)
        self.BackButton.setEnabled(False)
        self.BackButton.setObjectName("BackButton")
        self.gridlayout.addWidget(self.BackButton, 2, 2, 1, 1)
        self.NextButton = QtWidgets.QPushButton(Dialog)
        self.NextButton.setEnabled(False)
        self.NextButton.setObjectName("NextButton")
        self.gridlayout.addWidget(self.NextButton, 2, 3, 1, 1)
        self.CancelButton = QtWidgets.QPushButton(Dialog)
        self.CancelButton.setObjectName("CancelButton")
        self.gridlayout.addWidget(self.CancelButton, 2, 4, 1, 1)

        self.retranslateUi(Dialog)
        self.StackedWidget.setCurrentIndex(0)
        self.AgreeCheckBox.toggled['bool'].connect(self.NextButton.setEnabled)
        self.NextButton.clicked.connect(Dialog.accept)
        self.CancelButton.clicked.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "HP Device Manager - Plug-in Installer"))
        self.label.setText(_translate("Dialog", "Driver Plug-in License Agreement"))
        self.label_2.setText(_translate("Dialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Please read the driver plug-in license agreement and then check the <span style=\" font-style:italic;\">I agree</span> box and then click <span style=\" font-style:italic;\">Next</span> to continue.</p></body></html>"))
        self.AgreeCheckBox.setText(_translate("Dialog", "I agree to the terms of the driver plug-in license agreement"))
        self.BackButton.setText(_translate("Dialog", "< Back"))
        self.NextButton.setText(_translate("Dialog", "Next >"))
        self.CancelButton.setText(_translate("Dialog", "Cancel"))

