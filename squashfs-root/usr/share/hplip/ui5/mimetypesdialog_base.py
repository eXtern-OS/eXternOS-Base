# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mimetypesdialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MimeTypesDialog_base(object):
    def setupUi(self, MimeTypesDialog_base):
        MimeTypesDialog_base.setObjectName("MimeTypesDialog_base")
        MimeTypesDialog_base.resize(500, 540)
        self.gridlayout = QtWidgets.QGridLayout(MimeTypesDialog_base)
        self.gridlayout.setContentsMargins(11, 11, 11, 11)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")
        self.textLabel3_2 = QtWidgets.QLabel(MimeTypesDialog_base)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textLabel3_2.sizePolicy().hasHeightForWidth())
        self.textLabel3_2.setSizePolicy(sizePolicy)
        self.textLabel3_2.setWordWrap(False)
        self.textLabel3_2.setObjectName("textLabel3_2")
        self.gridlayout.addWidget(self.textLabel3_2, 0, 0, 1, 2)
        self.line1_2 = QtWidgets.QFrame(MimeTypesDialog_base)
        self.line1_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line1_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line1_2.setObjectName("line1_2")
        self.gridlayout.addWidget(self.line1_2, 1, 0, 1, 2)
        self.TypesTableWidget = QtWidgets.QTableWidget(MimeTypesDialog_base)
        self.TypesTableWidget.setAlternatingRowColors(True)
        self.TypesTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.TypesTableWidget.setObjectName("TypesTableWidget")
        self.TypesTableWidget.setColumnCount(3)
        self.TypesTableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.TypesTableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.TypesTableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.TypesTableWidget.setHorizontalHeaderItem(2, item)
        self.gridlayout.addWidget(self.TypesTableWidget, 2, 0, 1, 2)
        self.textLabel1 = QtWidgets.QLabel(MimeTypesDialog_base)
        self.textLabel1.setWordWrap(True)
        self.textLabel1.setObjectName("textLabel1")
        self.gridlayout.addWidget(self.textLabel1, 3, 0, 1, 2)
        spacerItem = QtWidgets.QSpacerItem(301, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem, 4, 0, 1, 1)
        self.pushButton10 = QtWidgets.QPushButton(MimeTypesDialog_base)
        self.pushButton10.setObjectName("pushButton10")
        self.gridlayout.addWidget(self.pushButton10, 4, 1, 1, 1)

        self.retranslateUi(MimeTypesDialog_base)
        self.pushButton10.clicked.connect(MimeTypesDialog_base.accept)
        QtCore.QMetaObject.connectSlotsByName(MimeTypesDialog_base)

    def retranslateUi(self, MimeTypesDialog_base):
        _translate = QtCore.QCoreApplication.translate
        MimeTypesDialog_base.setWindowTitle(_translate("MimeTypesDialog_base", "HP Device Manager - MIME Types"))
        self.textLabel3_2.setText(_translate("MimeTypesDialog_base", "<b>File/document types that can be added to the file list.</b>"))
        item = self.TypesTableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MimeTypesDialog_base", "MIME Type"))
        item = self.TypesTableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MimeTypesDialog_base", "Description"))
        item = self.TypesTableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MimeTypesDialog_base", "Usual File Extension(s)"))
        self.textLabel1.setText(_translate("MimeTypesDialog_base", "<i>Note: To print or fax file/document types that do not appear on this list, print the document from the application that created it through the appropriate CUPS printer.</i>"))
        self.pushButton10.setText(_translate("MimeTypesDialog_base", "OK"))

