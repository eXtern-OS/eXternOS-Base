from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class Ui_MainWindow_Derived(object):
    def setupUi(self, MainWindow, latest_available_version, Is_autoInstaller_distro):
        super(Ui_MainWindow_Derived, self).setupUi(MainWindow)
        self.DiagnoseQueueAction = QAction(MainWindow)
        self.DiagnoseQueueAction.setObjectName("DiagnoseQueueAction")
        self.DiagnoseHPLIPAction = QAction(MainWindow)
        self.DiagnoseHPLIPAction.setObjectName("DiagnoseHPLIPAction")

        self.latest_available_version = latest_available_version
        self.Is_autoInstaller_distro = Is_autoInstaller_distro
        if self.latest_available_version is not "":
            self.tab_3 = QWidget()
            self.tab_3.setObjectName("tab_3")
            self.label = QLabel(self.tab_3)
            self.label.setGeometry(QRect(30, 45, 300, 17))
            self.label.setObjectName("label")
            if self.Is_autoInstaller_distro:
                self.InstallLatestButton = QPushButton(self.tab_3)
                self.InstallLatestButton.setGeometry(QRect(351, 40, 96, 27))
                self.InstallLatestButton.setObjectName("pushButton")
            else:
                self.ManualInstalllabel = QLabel(self.tab_3)
                self.ManualInstalllabel.setGeometry(QRect(30, 70,300, 45))
                self.ManualInstalllabel.setObjectName("label")
                self.InstallLatestButton = QPushButton(self.tab_3)
                self.InstallLatestButton.setGeometry(QRect(295, 80, 110, 25))
                self.InstallLatestButton.setObjectName("pushButton")
            self.Tabs.addTab(self.tab_3, "")
        self.retranslateUi(MainWindow)

    def retranslateUi(self, MainWindow):
        super(Ui_MainWindow_Derived, self).retranslateUi(MainWindow)
        if self.latest_available_version is not "":
            self.label.setText(QApplication.translate("MainWindow", "New version of HPLIP-%s is available"%self.latest_available_version, None))
            self.Tabs.setTabText(self.Tabs.indexOf(self.tab_3), QApplication.translate("MainWindow", "Upgrade", None))
            if self.Is_autoInstaller_distro:
                self.InstallLatestButton.setText(QApplication.translate("MainWindow", "Install now", None))
            else:
                msg="Please install manually as mentioned in "
                self.ManualInstalllabel.setText(QApplication.translate("MainWindow", msg, None))
                self.InstallLatestButton.setText(QApplication.translate("MainWindow", "HPLIP website", None))
