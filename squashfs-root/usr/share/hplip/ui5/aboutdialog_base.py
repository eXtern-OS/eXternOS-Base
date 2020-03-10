# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'aboutdialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AboutDlg_base(object):
    def setupUi(self, AboutDlg_base):
        AboutDlg_base.setObjectName("AboutDlg_base")
        AboutDlg_base.resize(537, 543)
        self.gridlayout = QtWidgets.QGridLayout(AboutDlg_base)
        self.gridlayout.setContentsMargins(11, 11, 11, 11)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")
        self.textLabel1 = QtWidgets.QLabel(AboutDlg_base)
        self.textLabel1.setWordWrap(False)
        self.textLabel1.setObjectName("textLabel1")
        self.gridlayout.addWidget(self.textLabel1, 0, 0, 1, 2)
        self.hboxlayout = QtWidgets.QHBoxLayout()
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")
        spacerItem = QtWidgets.QSpacerItem(150, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.HPLIPLogo = QtWidgets.QLabel(AboutDlg_base)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.HPLIPLogo.sizePolicy().hasHeightForWidth())
        self.HPLIPLogo.setSizePolicy(sizePolicy)
        self.HPLIPLogo.setMinimumSize(QtCore.QSize(100, 110))
        self.HPLIPLogo.setMaximumSize(QtCore.QSize(100, 110))
        self.HPLIPLogo.setScaledContents(True)
        self.HPLIPLogo.setWordWrap(False)
        self.HPLIPLogo.setObjectName("HPLIPLogo")
        self.hboxlayout.addWidget(self.HPLIPLogo)
        spacerItem1 = QtWidgets.QSpacerItem(151, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem1)
        self.gridlayout.addLayout(self.hboxlayout, 1, 0, 1, 2)
        self.hboxlayout1 = QtWidgets.QHBoxLayout()
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")
        self.textLabel4 = QtWidgets.QLabel(AboutDlg_base)
        self.textLabel4.setWordWrap(False)
        self.textLabel4.setObjectName("textLabel4")
        self.hboxlayout1.addWidget(self.textLabel4)
        self.HPLIPVersionText = QtWidgets.QLabel(AboutDlg_base)
        self.HPLIPVersionText.setWordWrap(False)
        self.HPLIPVersionText.setObjectName("HPLIPVersionText")
        self.hboxlayout1.addWidget(self.HPLIPVersionText)
        self.gridlayout.addLayout(self.hboxlayout1, 2, 0, 1, 2)
        self.hboxlayout2 = QtWidgets.QHBoxLayout()
        self.hboxlayout2.setSpacing(6)
        self.hboxlayout2.setObjectName("hboxlayout2")
        self.textLabel4_2 = QtWidgets.QLabel(AboutDlg_base)
        self.textLabel4_2.setWordWrap(False)
        self.textLabel4_2.setObjectName("textLabel4_2")
        self.hboxlayout2.addWidget(self.textLabel4_2)
        self.ToolboxVersionText = QtWidgets.QLabel(AboutDlg_base)
        self.ToolboxVersionText.setWordWrap(False)
        self.ToolboxVersionText.setObjectName("ToolboxVersionText")
        self.hboxlayout2.addWidget(self.ToolboxVersionText)
        self.gridlayout.addLayout(self.hboxlayout2, 3, 0, 1, 2)
        self.textLabel3 = QtWidgets.QLabel(AboutDlg_base)
        self.textLabel3.setWordWrap(True)
        self.textLabel3.setObjectName("textLabel3")
        self.gridlayout.addWidget(self.textLabel3, 4, 0, 1, 2)
        self.textLabel2 = QtWidgets.QLabel(AboutDlg_base)
        self.textLabel2.setWordWrap(True)
        self.textLabel2.setObjectName("textLabel2")
        self.gridlayout.addWidget(self.textLabel2, 5, 0, 1, 2)
        self.hboxlayout3 = QtWidgets.QHBoxLayout()
        self.hboxlayout3.setSpacing(6)
        self.hboxlayout3.setObjectName("hboxlayout3")
        self.PythonPixmap = QtWidgets.QLabel(AboutDlg_base)
        self.PythonPixmap.setMinimumSize(QtCore.QSize(200, 62))
        self.PythonPixmap.setMaximumSize(QtCore.QSize(200, 62))
        self.PythonPixmap.setScaledContents(True)
        self.PythonPixmap.setWordWrap(False)
        self.PythonPixmap.setObjectName("PythonPixmap")
        self.hboxlayout3.addWidget(self.PythonPixmap)
        self.OsiPixmap = QtWidgets.QLabel(AboutDlg_base)
        self.OsiPixmap.setMinimumSize(QtCore.QSize(75, 65))
        self.OsiPixmap.setMaximumSize(QtCore.QSize(75, 65))
        self.OsiPixmap.setScaledContents(True)
        self.OsiPixmap.setWordWrap(False)
        self.OsiPixmap.setObjectName("OsiPixmap")
        self.hboxlayout3.addWidget(self.OsiPixmap)
        self.gridlayout.addLayout(self.hboxlayout3, 6, 0, 1, 2)
        spacerItem2 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem2, 7, 0, 1, 2)
        spacerItem3 = QtWidgets.QSpacerItem(411, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem3, 8, 0, 1, 1)
        self.CloseButton = QtWidgets.QPushButton(AboutDlg_base)
        self.CloseButton.setObjectName("CloseButton")
        self.gridlayout.addWidget(self.CloseButton, 8, 1, 1, 1)

        self.retranslateUi(AboutDlg_base)
        self.CloseButton.clicked.connect(AboutDlg_base.close)
        QtCore.QMetaObject.connectSlotsByName(AboutDlg_base)

    def retranslateUi(self, AboutDlg_base):
        _translate = QtCore.QCoreApplication.translate
        AboutDlg_base.setWindowTitle(_translate("AboutDlg_base", "HP Device Manager - About"))
        self.textLabel1.setText(_translate("AboutDlg_base", "<font size=\"+3\"><p align=\"center\">HP Linux Imaging and Printing (HPLIP)</p></font>"))
        self.textLabel4.setText(_translate("AboutDlg_base", "<b>HPLIP Software Version:</b>"))
        self.HPLIPVersionText.setText(_translate("AboutDlg_base", "0.0.0"))
        self.textLabel4_2.setText(_translate("AboutDlg_base", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'DejaVu Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Device Manager Version:</span></p></body></html>"))
        self.ToolboxVersionText.setText(_translate("AboutDlg_base", "0.0.0"))
        self.textLabel3.setText(_translate("AboutDlg_base", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'DejaVu Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">License and Copyright:</span> (c) Copyright 2015 HP Development Company, L.P. This software is licensed under the GNU General Public License (GPL), BSD, and MIT licenses. See the software sources for details.</p></body></html>"))
        self.textLabel2.setText(_translate("AboutDlg_base", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'DejaVu Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Authors and Contributors:</span> David Suffield, Don Welch, Shiyun Yie, Raghothama Cauligi, John Oleinik, Cory Meisch, Foster Nuffer, Pete Parks, Jacqueline Pitter, David Paschal, Steve DeRoos, Mark Overton, Aaron Albright, Smith Kennedy, John Hosszu, Chris Wiesner, Henrique M. Holschuh, Till Kamppeter, Linus Araque, Mark Crawford, Charlie Moore, Jason Callough, Stan Dolson, Don Mackliet, Paul Leclerc, Naga Samrat Choudary, Suma Byrappa, Yashwant Sahu, Sanjay Kumar, Sarbeswar Meher, Goutam Kodu, Gaurav Sood, Srikant Lokare, Parul Singh, Raghavendra Chitpadi</p></body></html>"))
        self.CloseButton.setText(_translate("AboutDlg_base", "Close"))

