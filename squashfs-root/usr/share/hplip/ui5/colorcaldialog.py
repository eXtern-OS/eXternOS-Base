# -*- coding: utf-8 -*-
#
# (c) Copyright 2001-2015 HP Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Authors: Don Welch
#

# StdLib
import operator
import signal

# Local
from base.g import *
from base import device, utils, maint
from prnt import cups
from base.codes import *
from base.sixext import  to_unicode
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Ui
from .colorcaldialog_base import Ui_Dialog


COLOR_CAL_TYPE_INITIAL = 1000
COLOR_CAL_TYPE_TEST = 1001

PAGE_START = 0
PAGE_LOAD_PAPER = 1
PAGE_DESKJET_450 = 2
PAGE_CRICK = 3
PAGE_LBOW = 4
PAGE_CONNERY = 5
PAGE_FRONT_PANEL = 6


BUTTON_CALIBRATE = 0
BUTTON_NEXT = 1
BUTTON_FINISH = 2


def true():
    return True


class ColorCalDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, device_uri):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.device_uri = device_uri
        self.color_cal_type = COLOR_CAL_TYPE_INITIAL
        self.a, self.b = 0, 0
        self.step = 1
        self.abort = False
        self.seq_index = 0
        self.value = 0
        self.values = []
        self.step_max = 0

        self.max_steps = {
                    COLOR_CAL_TYPE_UNSUPPORTED : 1,
                    COLOR_CAL_TYPE_DESKJET_450 : 2,
                    COLOR_CAL_TYPE_MALIBU_CRICK : 0,
                    COLOR_CAL_TYPE_STRINGRAY_LONGBOW_TORNADO : 0,
                    COLOR_CAL_TYPE_CONNERY : 0,
                    COLOR_CAL_TYPE_COUSTEAU : 0,
                    COLOR_CAL_TYPE_CARRIER : 0,
                    COLOR_CAL_TYPE_TYPHOON : 0,
                   }

        self.seq = { # (func|method, tuple of params|None)
                    COLOR_CAL_TYPE_INITIAL: [ # (used when starting up and align-type isn't known)
                               (self.showStartPage, None),
                               (self.endStartPage, None), # switch to a valid align-type here
                            ],

                    COLOR_CAL_TYPE_UNSUPPORTED : [
                                (self.showFrontPanelPage, None),
                                (self.endFrontPanelPage, None),
                                (self.close, None),
                                    ],

                    COLOR_CAL_TYPE_DESKJET_450 : [ # 1
                                (self.colorCalType1PenCheck, None),
                                (self.showLoadPaperPage, None),
                                (self.endLoadPaperPage, None),
                                (maint.colorCalType1Phase1, (lambda: self.dev,)),
                                (self.setColorCalButton, (BUTTON_CALIBRATE,)),
                                (self.showDeskjet450Page, None),
                                (self.endDeskjet450Page, None),
                                (maint.colorCalType1Phase2, (lambda: self.dev, lambda: self.value)),
                                (self.close, None),
                                    ],

                    COLOR_CAL_TYPE_MALIBU_CRICK : [ # 2
                                (self.colorCalType2PenCheck, None),
                                (self.showLoadPaperPage, None),
                                (self.endLoadPaperPage, None),
                                (maint.colorCalType1Phase1, (lambda: self.dev,)),
                                (self.setColorCalButton, (BUTTON_CALIBRATE,)),
                                (self.showCrick, None),
                                (self.endCrick, None),
                                (maint.colorCalType2Phase2, (lambda: self.dev, lambda: self.value)),
                                (self.close, None),
                                    ],

                    COLOR_CAL_TYPE_STRINGRAY_LONGBOW_TORNADO : [ # 3
                                (self.colorCalType3PenCheck, None),
                                (self.showLoadPaperPage, None),
                                (self.endLoadPaperPage, None),
                                (maint.colorCalType3Phase1, (lambda: self.dev,)),
                                (self.showLBowPage, ('A', 21)),
                                (self.endLBowPage, ('A',)),
                                (self.setColorCalButton, (BUTTON_CALIBRATE,)),
                                (self.showLBowPage, ('B', 21)),
                                (self.endLBowPage, ('B',)),
                                (maint.colorCalType3Phase2, (lambda: self.dev, lambda: self.a,
                                                             lambda: self.b)),
                                (self.close, None),
                                    ],

                    COLOR_CAL_TYPE_CONNERY : [ #4
                                (self.showLoadPaperPage, None),
                                (self.endLoadPaperPage, None),
                                (maint.colorCalType4Phase1, (lambda: self.dev,)),
                                (self.setColorCalButton, (BUTTON_CALIBRATE,)),
                                (self.showConneryPage, None),
                                (self.endConneryPage, None), # sets self.values (list)
                                (maint.colorCalType4Phase2, (lambda: self.dev, lambda: self.values)),
                                (self.showLoadPaperPage, None),
                                (self.endLoadPaperPage, None),
                                (maint.colorCalType4Phase3, (lambda: self.dev,)),
                                (self.close, None),
                                    ],

                    COLOR_CAL_TYPE_COUSTEAU : [ #5
                                (self.setColorCalButton, (BUTTON_CALIBRATE,)),
                                (self.showLoadPaperPage, None),
                                (self.endLoadPaperPage, None),
                                (maint.colorCalType5, (lambda: self.dev, lambda: true)),
                                (self.showConneryPage, None),
                                (self.endConneryPage, None),
                                (self.close, None),
                                    ],

                    COLOR_CAL_TYPE_CARRIER : [ #6
                                (self.setColorCalButton, (BUTTON_CALIBRATE,)),
                                (self.showLoadPaperPage, None),
                                (self.endLoadPaperPage, None),
                                (maint.colorCalType6, (lambda: self.dev, lambda: true)),
                                (self.close, None),
                                    ],

                    COLOR_CAL_TYPE_TYPHOON : [ #7
                                (self.setColorCalButton, (BUTTON_CALIBRATE,)),
                                (self.showLoadPaperPage, None),
                                (self.endLoadPaperPage, None),
                                (maint.colorCalType7, (lambda: self.dev, lambda: true)),
                                (self.close, None),
                                    ],
        }


        self.initUi()

        QTimer.singleShot(0, self.nextSequence)


    def initUi(self):
        # connect signals/slots
        self.CancelButton.clicked.connect(self.CancelButton_clicked)
        self.NextButton.clicked.connect(self.NextButton_clicked)
        self.DeviceComboBox.DeviceUriComboBox_noDevices.connect(self.DeviceUriComboBox_noDevices)
        self.DeviceComboBox.DeviceUriComboBox_currentChanged.connect(self.DeviceUriComboBox_currentChanged)
        self.DeviceComboBox.setFilter({'color-cal-type': (operator.gt, 0)})
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        if self.device_uri:
            self.DeviceComboBox.setInitialDevice(self.device_uri)

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))
        self.updateStepText()




    def DeviceUriComboBox_noDevices(self):
        FailureUI(self, self.__tr("<b>No devices that support print cartridge alignment found.</b><p>Click <i>OK</i> to exit.</p>"))
        self.close()


    def DeviceUriComboBox_currentChanged(self, device_uri):
        self.device_uri = device_uri


    def CancelButton_clicked(self):
        self.close()


    def NextButton_clicked(self):
        self.nextSequence()


    def nextSequence(self):
        while True:
            try:
                seq, params = self.seq[self.color_cal_type][self.seq_index]
            except IndexError:
                break

            if seq is None:
                self.seq_index += 1
                continue

            self.new_page = False

            t = []
            if params is not None:
                for p in params:
                    try:
                        t.append(p())
                    except:
                        t.append(p)

            try:
                log.debug("%s(%s)" % (seq.__name__, ','.join([repr(x) for x in t])))
            except AttributeError:
                pass

            try:
                seq(*t)
            except Error:
                CheckDeviceUI(self)
                break

            self.seq_index += 1

            if self.new_page:
                break

            if self.abort:
                self.close()



    def showStartPage(self):
        self.BackButton.setEnabled(False)
        num_devices = self.DeviceComboBox.setDevices()

        if num_devices == 1:
            self.skipPage()
            return

        self.DeviceComboBox.updateUi()
        self.displayPage(PAGE_START)


    def endStartPage(self):
        self.mq = device.queryModelByURI(self.device_uri)
        self.color_cal_type = self.mq.get('color-cal-type', COLOR_CAL_TYPE_NONE)
        self.seq_index = -1

        #self.color_cal_type = COLOR_CAL_TYPE_TEST # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

        log.debug("color-cal-type=%d" % self.color_cal_type)
        self.step_max = self.max_steps[self.color_cal_type]

        try:
            self.dev = device.Device(self.device_uri)
        except Error:
            CheckDeviceUI(self)
            return


    def showLoadPaperPage(self):
        self.LoadPaper.updateUi()
        self.displayPage(PAGE_LOAD_PAPER)


    def endLoadPaperPage(self):
        pass


    def showDeskjet450Page(self):
        self.displayPage(PAGE_DESKJET_450)


    def endDeskjet450Page(self):
        self.value = int(to_unicode(self.Deskjet450ComboBox.currentText()))


    def showCrick(self):
        self.displayPage(PAGE_CRICK)


    def endCrick(self):
        self.value = self.CrickSpinBox.value()

    def showLBowPage(self, line_id, count=21):
        self.LBowComboBox.clear()
        self.LBowIcon.setPixmap(load_pixmap('color_adj', 'other'))
        self.LBowLabel.setText(self.__tr("Line %s:"%line_id))

        for x in range(count):
            self.LBowComboBox.addItem(str("%s%s"%(line_id, x+1)))

        self.displayPage(PAGE_LBOW)


    def endLBowPage(self, line_id):
        v = int(str(self.LBowComboBox.currentText())[1:])

        if line_id == 'A':
            self.a = v
            log.debug("A=%d" % v)

        elif line_id == 'B':
            self.b = v
            log.debug("B=%d" % v)


    def showConneryPage(self):
        self.ConneryGrayPatchIcon.setPixmap(load_pixmap('type4_gray_patch', 'other'))
        self.ConneryColorPatchIcon.setPixmap(load_pixmap('type4_color_patch', 'other'))

        for x in 'ABCDEFGHIJKLMN':
            self.ConneryGrayLetterComboBox.addItem(str(x))

        for x in range(13):
            self.ConneryGrayNumberComboBox.addItem(str("%s"%x+1))

        for x in 'PQRSTUV':
            self.ConneryColorLetterComboBox.addItem(str(x))

        for x in range(6):
            self.ConneryColorNumberComboBox.addItem(str("%s"%x+1))

        self.displayPage(PAGE_CONNERY)


    def endConneryPage(self):
        if self.ConneryUseFactoryDefaultsCheckBox.checkState() == Qt.Checked:
            log.debug("Using factory defaults")
            self.values = [-1, -1, -1, -1]
        else:
            self.values = [
                (ord(str(self.ConneryGrayLetterComboBox.currentText())) - ord('A')),
                int(str(self.ConneryGrayNumberComboBox.currentText())),
                (ord(str(self.ConneryColorLetterComboBox.currentText())) - ord('P')),
                int(str(self.ConneryColorNumberComboBox.currentText()))
            ]


    def showFrontPanelPage(self):
        self.BackButton.setEnabled(False)
        self.setColorCalButton(BUTTON_FINISH)
        self.displayPage(PAGE_FRONT_PANEL)


    def endFrontPanelPage(self):
        pass

    #
    # Color cal specific
    #

    def colorCalType1PenCheck(self):
        if not maint.colorCalType1PenCheck(self.dev):
            pass # TODO: Error message (photo pen must be inserted)


    def colorCalType2PenCheck(self):
        if not maint.colorCalType2PenCheck(self.dev):
            pass # TODO: Error message (photo pen must be inserted)


    def colorCalType3PenCheck(self):
        if not maint.colorCalType3PenCheck(self.dev):
            pass # TODO:

    #
    # Misc
    #

    def displayPage(self, page):
        self.updateStepText(self.step)
        self.step += 1
        self.new_page = True
        self.StackedWidget.setCurrentIndex(page)


    def skipPage(self):
        self.step += 1
        self.new_page = False


    def updateStepText(self, p=None):
        if p is None or not self.step_max:
            self.StepText.setText(str(""))
        else:
            self.StepText.setText(self.__tr("Step %s of %s"%(p,self.step_max)))


    def setColorCalButton(self, typ=BUTTON_CALIBRATE):
        if typ == BUTTON_CALIBRATE:
            self.NextButton.setText(self.__tr("Calibrate"))
        elif typ == BUTTON_NEXT:
            self.NextButton.setText(self.__tr("Next >"))
        elif typ == BUTTON_FINISH:
            self.NextButton.setText(self.__tr("Finish"))


#    def setPenConfig(self):
#        self.dev.pen_config = status.getPenConfiguration(dev.getStatusFromDeviceID())


    def __tr(self,s,c = None):
        return qApp.translate("ColorCalDialog",s,c)


