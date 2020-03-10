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
# Authors: Don Welch, Naga Samrat Chowdary Narla,
#

# StdLib
import operator
import signal

# Local
from base.g import *
from base import device, utils, maint, status
#from prnt import cups
from base.codes import *
from .ui_utils import *

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Ui
from .aligndialog_base import Ui_Dialog

PAGE_START = 0
PAGE_LOAD_PAPER = 1
PAGE_EDGE = 2
PAGE_ALIGNMENT_NUMBER = 3
PAGE_COLOR_ADJ = 4 # types 4, 5 & 7
PAGE_LBOW = 5 # types 10 & 11
PAGE_AIO = 6 # Place on scanner, ...
PAGE_FRONT_PANEL = 7 # Use front panel menu

BUTTON_ALIGN = 0
BUTTON_NEXT = 1
BUTTON_FINISH = 2

ALIGN_TYPE_INITIAL = 1000
ALIGN_TYPE_TEST = 1001

# xBow offset types
ALIGN_TYPE_XBOW_OFFSET = 100
ALIGN_TYPE_XBOW_BLACK_ONLY = ALIGN_TYPE_XBOW_OFFSET + AGENT_CONFIG_BLACK_ONLY
ALIGN_TYPE_XBOW_PHOTO_ONLY = ALIGN_TYPE_XBOW_OFFSET + AGENT_CONFIG_PHOTO_ONLY
ALIGN_TYPE_XBOW_COLOR_ONLY =  ALIGN_TYPE_XBOW_OFFSET + AGENT_CONFIG_COLOR_ONLY
ALIGN_TYPE_XBOW_COLOR_AND_BLACK =  ALIGN_TYPE_XBOW_OFFSET + AGENT_CONFIG_COLOR_AND_BLACK
ALIGN_TYPE_XBOW_COLOR_AND_PHOTO = ALIGN_TYPE_XBOW_OFFSET + AGENT_CONFIG_COLOR_AND_PHOTO


def true():
    return True


class AlignDialog(QDialog, Ui_Dialog):
    def __init__(self, parent, device_uri):
        QDialog.__init__(self, parent)
        self.device_uri = device_uri
        self.mq = {}
        self.step_max = 0
        self.align_type = ALIGN_TYPE_INITIAL
        self.step = 1
        self.a, self.b, self.c, self.d, self.zca = 0, 0, 0, 0, 0
        self.e, self.f, self.g = 0, 0, 0
        self.num_inks = 0 # type 8
        self.pattern = 0 # type 10
        self.values = [] # type 10
        self.abort = False
        self.seq_index = 0

        self.max_steps = {
            ALIGN_TYPE_UNSUPPORTED : 1,
            ALIGN_TYPE_AUTO : 2,
            ALIGN_TYPE_9XX : 7,
            ALIGN_TYPE_8XX : 7,
            ALIGN_TYPE_LIDIL_0_3_8 : 0,
            ALIGN_TYPE_LIDIL_0_4_3 : 0,
            ALIGN_TYPE_LIDIL_AIO : 3,
            ALIGN_TYPE_LIDIL_VIP : 0,
            ALIGN_TYPE_DESKJET_450 : 0,
            ALIGN_TYPE_9XX_NO_EDGE_ALIGN : 6,
            ALIGN_TYPE_LBOW : 0,
            ALIGN_TYPE_LIDIL_0_5_4 : 0,
            ALIGN_TYPE_OJ_PRO : 0,
            ALIGN_TYPE_TEST : 0,
            ALIGN_TYPE_AIO : 3,
            ALIGN_TYPE_LIDIL_DJ_D1600: 0,
            ALIGN_TYPE_LEDM: 0,
            ALIGN_TYPE_LEDM_MANUAL: 0,
            ALIGN_TYPE_LEDM_FF_CC_0: 0,
            }

        self.seq = { # (func|method, tuple of params|None)
            ALIGN_TYPE_TEST : [ # testing only
                               (self.showColorAdjustPage, ('F', 21)),
                               (self.endColorAdjustPage, ('F',)),
                               (self.showColorAdjustPage, ('G', 11)),
                               (self.endColorAdjustPage, ('G',)),
                               (self.close, None),
                            ],

            ALIGN_TYPE_INITIAL : [ # (used when starting up and align-type isn't known)
                               (self.showStartPage, None),
                               (self.endStartPage, None), # switch to a valid align-type here
                            ],

            ALIGN_TYPE_UNSUPPORTED : [ # -1
                                (self.showFrontPanelPage, None),
                                (self.endFronPanelPage, None),
                                (self.close, None),
                            ],

#            ALIGN_TYPE_NONE : [ # 0
#                               (self.close, None)
#                            ],

            ALIGN_TYPE_AUTO : [ # 1
                               (self.showLoadPaperPage, None),
                               (maint.AlignType1PML, (lambda : self.dev, lambda: true)),
                               (self.closeAll, None),
                               (self.close, None),
                            ],

            ALIGN_TYPE_8XX : [ # 2
                                (self.checkType2PenConfig, None),
                                (self.showLoadPaperPage, None),
                                (maint.alignType2Phase1, (lambda: self.dev,)),
                                (self.showAlignmentNumberPage, ('A', 'h', 'kc', 2, 11)),
                                (self.endAlignmentNumberPage, ('A',)),
                                (self.showAlignmentNumberPage, ('B', 'v', 'kc', 2, 11)),
                                (self.endAlignmentNumberPage, ('B',)),
                                (self.showAlignmentNumberPage, ('C', 'v', 'kc', 2, 5)),
                                (self.endAlignmentNumberPage, ('C',)),
                                (self.showAlignmentNumberPage, ('D', 'v', 'c', 2, 5)),
                                (self.endAlignmentNumberPage, ('D',)),
                                (self.setAlignButton, (BUTTON_ALIGN,)),
                                (self.showLoadPaperPage, (lambda: True,)),
                                (maint.alignType2Phase2, (lambda: self.dev, lambda: self.a, lambda: self.b,
                                                          lambda: self.c, lambda: self.d)),
                                (self.closeAll, None),
                                (self.close, None),
                              ],

            ALIGN_TYPE_9XX : [  # 3
                                (self.showLoadPaperPage, None),
                                (self.showAlignmentNumberPage, ('A', 'h', 'kc', 2, 11)),
                                (self.endAlignmentNumberPage, ('A',)),
                                (self.showAlignmentNumberPage, ('B', 'v', 'kc', 2, 11)),
                                (self.endAlignmentNumberPage, ('B',)),
                                (self.showAlignmentNumberPage, ('C', 'v', 'k', 2, 11)),
                                (self.endAlignmentNumberPage, ('C',)),
                                (self.setAlignButton, (BUTTON_ALIGN,)),
                                (self.showAlignmentNumberPage, ('D', 'v', 'kc', 2, 11)),
                                (self.endAlignmentNumberPage, ('D',)),
                                (maint.alignType3Phase2, (lambda: self.dev, lambda: self.a, lambda: self.b,
                                                          lambda: self.c, lambda: self.d)),
                                (maint.alignType3Phase3, (lambda: self.dev,)),
                                (self.showPageEdgePage, None),
                                (self.endPageEdgePage, None),
                                (maint.alignType3Phase4, (lambda: self.dev, lambda: self.zca)),
                                (self.closeAll, None),
                                (self.close, None),
                             ],

            ALIGN_TYPE_LIDIL_0_3_8 : [ # 4
                                (self.showLoadPaperPage, None),
                                (self.setPenConfig, None),
                                (maint.alignType4Phase1, (lambda: self.dev,)),
                                (self.setXBow, None),
                                # switches to offset align_type here
                            ],

            ALIGN_TYPE_LIDIL_0_4_3 : [ # 5
                                (self.showLoadPaperPage, None),
                                (self.setPenConfig, None),
                                (maint.alignType5Phase1, (lambda: self.dev,)),
                                (self.showPageEdgePage, ('A',)),
                                (self.endPageEdgePage, None),
                                (self.setXBow, None),
                                # switches to offset align_type here
                            ],

            ALIGN_TYPE_LIDIL_VIP : [ # 7
                                (self.showLoadPaperPage, None),
                                (self.setPenConfig, None),
                                (maint.alignType7Phase1, (lambda: self.dev,)),
                                (self.showPageEdgePage, ('A',)),
                                (self.endPageEdgePage, None),
                                (self.setXBow, None),
                                # switches to offset align_type here (next 5 types)
                            ],

            # xBow offset alignment type
            ALIGN_TYPE_XBOW_BLACK_ONLY : [ # 4, 5 & 7
                            (self.showAlignmentNumberPage, ('B', 'v', 'k', 2, 11)),
                            (self.endAlignmentNumberPage, ('B',)),
                            (self.setXBowValues, None),
                            (self.closeAll, None),
                            (self.close, None),
                            ],

            # xBow offset alignment type
            ALIGN_TYPE_XBOW_PHOTO_ONLY : [ # 4, 5 & 7
                            (self.showAlignmentNumberPage, ('B', 'v', 'k', 2, 11)),
                            (self.endAlignmentNumberPage, ('B',)),
                            (self.setXBowValues, None),
                            (self.closeAll, None),
                            (self.close, None),
                            ],

            # xBow offset alignment type
            ALIGN_TYPE_XBOW_COLOR_ONLY : [ # 4, 5 & 7
                            (self.showAlignmentNumberPage, ('B', 'v', 'kc', 2, 11)),
                            (self.endAlignmentNumberPage, ('B',)),
                            (self.setXBowValues, None),
                            (self.closeAll, None),
                            (self.close, None),
                            ],

            # xBow offset alignment type
            ALIGN_TYPE_XBOW_COLOR_AND_BLACK : [ # 4, 5 & 7
                            (self.showAlignmentNumberPage, ('B', 'h', 'kc', 2, 17)),
                            (self.endAlignmentNumberPage, ('B',)),
                            (self.showAlignmentNumberPage, ('C', 'v', 'kc', 2, 17)),
                            (self.endAlignmentNumberPage, ('C',)),
                            (self.showAlignmentNumberPage, ('D', 'v', 'k', 2, 11)),
                            (self.endAlignmentNumberPage, ('D',)),
                            (self.showAlignmentNumberPage, ('E', 'v', 'kc', 2, 11)),
                            (self.endAlignmentNumberPage, ('E',)),
                            (self.setXBowValues, None),
                            (self.closeAll, None),
                            (self.close, None),
                            ],

            # xBow offset alignment type
            ALIGN_TYPE_XBOW_COLOR_AND_PHOTO : [ # 4, 5 & 7
                            (self.showAlignmentNumberPage, ('B', 'h', 'kc', 2, 17)),
                            (self.endAlignmentNumberPage, ('B',)),
                            (self.showAlignmentNumberPage, ('C', 'v', 'kc', 2, 17)),
                            (self.endAlignmentNumberPage, ('C',)),
                            (self.showAlignmentNumberPage, ('D', 'v', 'k', 2, 11)),
                            (self.endAlignmentNumberPage, ('D',)),
                            (self.showAlignmentNumberPage, ('E', 'v', 'kc', 2, 11)),
                            (self.endAlignmentNumberPage, ('E',)),
                            (self.showColorAdjustPage, ('F', 21)),
                            (self.endColorAdjustPage, ('F',)),
                            (self.showColorAdjustPage, ('G', 21)),
                            (self.endColorAdjustPage, ('G',)),
                            (self.setXBowValues, None),
                            (self.close, None),
                            ],

            ALIGN_TYPE_LIDIL_AIO : [ # 6 (semi-auto)
                                (self.showLoadPaperPage, None),
                                (maint.alignType6Phase1, (lambda: self.dev,)),
                                (self.setAlignButton, (BUTTON_FINISH,)),
                                (self.showAioPage, None),
                                (self.closeAll, None),
                                (self.close, None),
                            ],

            ALIGN_TYPE_DESKJET_450 : [ # 8
                                (self.showLoadPaperPage, None),
                                (self.alignType8Phase1, None), # sets num_inks
                                (self.showAlignmentNumberPage, ('A', 'v', 'k', 3, 9)),
                                (self.endAlignmentNumberPage, ('A',)),
                                (self.showAlignmentNumberPage, ('B', 'v', 'c', 3, 9)),
                                (self.endAlignmentNumberPage, ('B',)),
                                (self.showAlignmentNumberPage, ('C', 'v', 'kc', 3, 9)),
                                (self.endAlignmentNumberPage, ('C',)),
                                (self.setAlignButton, (BUTTON_ALIGN,)),
                                (self.showAlignmentNumberPage, ('D', 'h', 'kc', 3, 9)),
                                (self.endAlignmentNumberPage, ('D',)),
                                (maint.alignType3Phase2, (lambda: self.dev, lambda: self.num_inks, lambda: self.a,
                                                          lambda: self.b, lambda: self.c, lambda: self.d)),
                                (self.closeAll, None),
                                (self.close, None),
                            ],

            ALIGN_TYPE_9XX_NO_EDGE_ALIGN : [  # 9
                                (self.showLoadPaperPage, None),
                                (self.showAlignmentNumberPage, ('A', 'h', 'kc', 2, 11)),
                                (self.endAlignmentNumberPage, ('A',)),
                                (self.showAlignmentNumberPage, ('B', 'v', 'kc', 2, 11)),
                                (self.endAlignmentNumberPage, ('B',)),
                                (self.showAlignmentNumberPage, ('C', 'v', 'k', 2, 11)),
                                (self.endAlignmentNumberPage, ('C',)),
                                (self.setAlignButton, (BUTTON_ALIGN,)),
                                (self.showAlignmentNumberPage, ('D', 'v', 'kc', 2, 11)),
                                (self.endAlignmentNumberPage, ('D',)),
                                (maint.alignType3Phase2, (lambda: self.dev, lambda: self.a, lambda: self.b,
                                                          lambda: self.c, lambda: self.d)),
                                (self.closeAll, None),
                                (self.close, None),
                            ],

            ALIGN_TYPE_LBOW : [ # 10
                               (self.showLoadPaperPage, None),
                               (maint.alignType10Phase1, (lambda: self.dev,)),
                               (self.setAlignButton, (BUTTON_ALIGN,)),
                               (self.showLBowPage, (lambda: self.pattern,)),
                               (self.endLBowPage, None), # sets values
                               (maint.alignType10Phase2, (lambda: self.dev, lambda: self.values,
                                                          lambda: self.pattern)),
                               (self.setAlignButton, (BUTTON_FINISH,)),
                               (self.showLoadPaperPage, (lambda: True,)),
                               (maint.alignType10Phase3, (lambda: self.dev,)),
                               (self.closeAll, None),
                               (self.close, None),
                            ],

            ALIGN_TYPE_LIDIL_0_5_4 : [ # 11
                               (self.showLoadPaperPage, None),
                               (maint.alignType11Phase1, (lambda: self.dev,)),
                               (self.setAlignButton, (BUTTON_ALIGN,)),
                               (self.showLBowPage, (lambda: self.pattern,)),
                               (self.endLBowPage, None), # sets values
                               (maint.alignType11Phase2, (lambda: self.dev, lambda: self.values,
                                                          lambda: self.pattern, lambda: self.dev.pen_config)),
                               (self.setAlignButton, (BUTTON_FINISH,)),
                               (self.showLoadPaperPage, (lambda: True,)),
                               (maint.alignType11Phase3, (lambda: self.dev,)),
                               (self.closeAll, None),
                               (self.close, None),
                            ],

            ALIGN_TYPE_OJ_PRO : [ # 12
                                (self.showLoadPaperPage, None),
                                (maint.AlignType12, (lambda : self.dev, lambda: true)),
                                (self.closeAll, None),
                                (self.close, None),
                            ],

            ALIGN_TYPE_AIO : [ #13
                              (self.showLoadPaperPage, None),
                              (maint.alignType13Phase1, (lambda: self.dev,)),
                              (self.setAlignButton, (BUTTON_FINISH,)),
                              (self.showAioPage, None),
                              (self.closeAll, None),
                              (self.close, None),
                            ],

            ALIGN_TYPE_LIDIL_DJ_D1600 : [ # 14
                               (self.showLoadPaperPage, None),
                               (maint.alignType14Phase1, (lambda: self.dev,)),
                               (self.setAlignButton, (BUTTON_ALIGN,)),
                               (self.showLBowPage, (lambda: self.pattern,)),
                               (self.endLBowPage, None), # sets values
                               (maint.alignType14Phase2, (lambda: self.dev, lambda: self.values,
                                                          lambda: self.pattern, lambda: self.dev.pen_config)),
                               (self.setAlignButton, (BUTTON_FINISH,)),
                               (self.showLoadPaperPage, (lambda: True,)),
                               (maint.alignType14Phase3, (lambda: self.dev,)),
                               (self.closeAll, None),
                               (self.close, None),
                            ],

            ALIGN_TYPE_LEDM : [ # 15
                               (self.showLoadPaperPage, None),
                               (maint.AlignType15Phase1, (lambda : self.dev, lambda: self.showAioPage)),
                               (self.close, None),
                            ],

            ALIGN_TYPE_LEDM_MANUAL : [ # 16
                               (self.showLoadPaperPage, None),
                               (maint.AlignType15Phase1, (lambda : self.dev, lambda: true)),
                               (self.showAlignmentNumberPage, ('A', 'v', 'kc', 3, 23)),
                               (self.endAlignmentNumberPage, ('A',)),
                               (self.showAlignmentNumberPage, ('B', 'h', 'kc', 3, 17)),
                               (self.endAlignmentNumberPage, ('B',)),
                               (self.showAlignmentNumberPage, ('C', 'v', 'k', 3, 23)),
                               (self.endAlignmentNumberPage, ('C',)),
                               (self.showAlignmentNumberPage, ('D', 'v', 'c', 3, 23)),
                               (self.endAlignmentNumberPage, ('D',)),
                               (self.showAlignmentNumberPage, ('E', 'h', 'k', 3, 11)),
                               (self.endAlignmentNumberPage, ('E',)),
                               (self.showAlignmentNumberPage, ('F', 'h', 'k', 3, 11)),
                               (self.endAlignmentNumberPage, ('F',)),
                               (self.showAlignmentNumberPage, ('G', 'h', 'k', 3, 11)),
                               (self.endAlignmentNumberPage, ('G',)),
                               (self.showAlignmentNumberPage, ('H', 'v', 'k', 3, 11)),
                               (self.endAlignmentNumberPage, ('H',)),
                               (self.showAlignmentNumberPage, ('I', 'v', 'c', 3, 19)),
                               (self.endAlignmentNumberPage, ('I',)),
                               (self.showAlignmentNumberPage, ('J', 'v', 'c', 3, 19)),
                               (self.endAlignmentNumberPage, ('J',)),
                               (maint.AlignType16Phase1, (lambda: self.dev, lambda: self.a, lambda: self.b,
                                                          lambda: self.c, lambda: self.d, lambda: self.e,
                                                          lambda: self.f, lambda: self.g, lambda: self.h,
                                                          lambda: self.i, lambda: self.j)),
                               (self.closeAll, None),
                               (self.close, None),
                            ],
           ALIGN_TYPE_LEDM_FF_CC_0 : [ # 17
                               (self.showLoadPaperPage, None),
                               (maint.AlignType17Phase1, (lambda : self.dev, lambda: self.showAioPage)),
                               (self.close, None),
                            ],
            }

        self.setupUi(self)
        self.initUi()

        QTimer.singleShot(0, self.nextSequence)


    def initUi(self):
        # connect signals/slots
        self.CancelButton.clicked.connect(self.CancelButton_clicked)
        self.NextButton.clicked.connect(self.NextButton_clicked)
        #self.BackButton.clicked.connect(self.BackButton_clicked)
        self.DeviceComboBox.DeviceUriComboBox_noDevices.connect(self.DeviceUriComboBox_noDevices)
        self.DeviceComboBox.DeviceUriComboBox_currentChanged.connect(self.DeviceUriComboBox_currentChanged)
        self.DeviceComboBox.setFilter({'align-type': (operator.ne, ALIGN_TYPE_NONE)})

        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Application icon
        self.setWindowIcon(QIcon(load_pixmap('hp_logo', '128x128')))

        if self.device_uri:
            self.DeviceComboBox.setInitialDevice(self.device_uri)


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
                seq, params = self.seq[self.align_type][self.seq_index]
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
#       self.BackButton.setEnabled(False)
        num_devices = self.DeviceComboBox.setDevices()

        if num_devices == 1:
            self.skipPage()
            return

        self.DeviceComboBox.updateUi()
        self.displayPage(PAGE_START)


    def endStartPage(self):
        self.mq = device.queryModelByURI(self.device_uri)
        self.align_type = self.mq.get('align-type', ALIGN_TYPE_NONE)
        self.seq_index = -1

        #self.align_type = ALIGN_TYPE_TEST# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

        log.debug("align-type=%d" % self.align_type)
        self.step_max = self.max_steps[self.align_type]

        try:
            self.dev = device.Device(self.device_uri)
        except Error:
            CheckDeviceUI(self)
            return


    def showLoadPaperPage(self, finish=False):
        if finish:
            self.LoadPaper.button_name = self.__tr("Finish >")
        self.LoadPaper.updateUi()
        self.displayPage(PAGE_LOAD_PAPER)


    def endLoadPaperPage(self):
        pass


    def showAlignmentNumberPage(self, line_id, orientation, colors, line_count, choice_count):
        # line_id: 'A', 'B', etc.
        # orientation: 'v' or 'h'
        # colors: 'k' or 'c' or 'kc'
        # line_count: 2 or 3
        # choice_count: 5, 7, 9, 11, etc. (odd)
        self.AlignmentNumberTitle.setText(self.__tr("From the printed Alignment page, Choose the set of lines in group %s where the line segments are <b>best</b> aligned." % line_id))
        self.AlignmentNumberIcon.setPixmap(load_pixmap('%s-%s-%d' % (orientation, colors, line_count), 'other'))
        self.AlignmentNumberComboBox.clear()

        for x in range(choice_count):
            self.AlignmentNumberComboBox.addItem(str("%s%s"% (line_id, x+1)))

        self.displayPage(PAGE_ALIGNMENT_NUMBER)
        return


    def endAlignmentNumberPage(self, line_id):
        v = int(str(self.AlignmentNumberComboBox.currentText())[1:])

        if line_id == 'A':
            self.a = v
            log.debug("A=%d" % v)

        elif line_id == 'B':
            self.b = v
            log.debug("B=%d" % v)

        elif line_id == 'C':
            self.c = v
            log.debug("C=%d" % v)

        elif line_id == 'D':
            self.d = v
            log.debug("D=%d" % v)

        elif line_id == 'E':
            self.e = v
            log.debug("E=%d" % v)

        elif line_id == 'F':
            self.f = v
            log.debug("F=%d" % v)

        elif line_id == 'G':
            self.g = v
            log.debug("G=%d" % v)

        elif line_id == 'H':
            self.h = v
            log.debug("H=%d" % v)

        elif line_id == 'I':
            self.i = v
            log.debug("I=%d" % v)

        elif line_id == 'J':
            self.j = v
            log.debug("J=%d" % v)

    def showPageEdgePage(self, prefix=None, count=13):
        self.PageEdgeTitle.setText(self.__tr("Choose the <b>numbered arrow</b> that <b>best </b>marks the edge of the paper."))
        self.PageEdgeIcon.setPixmap(load_pixmap('zca.png', 'other'))

        self.PageEdgeComboBox.clear()
        for x in range(count):
            if prefix is None:
                self.PageEdgeComboBox.addItem(str("%s" % x+1))
            else:
                self.PageEdgeComboBox.addItem(str("%s%s" % (prefix, x+1))) # for xBow

        self.displayPage(PAGE_EDGE)


    def endPageEdgePage(self):
        v = int(str(self.PageEdgeComboBox.currentText())[1:])
        self.zca = v
        log.debug("ZCA=%d" % v)


    def showLBowPage(self, pattern):
        self.LBowIcon.setPixmap(load_pixmap('align10', 'other'))

        if self.align_type == ALIGN_TYPE_LBOW:
            pattern = maint.alignType10SetPattern(self.dev)

        elif self.align_type == ALIGN_TYPE_LIDIL_DJ_D1600:
            pattern = maint.alignType14SetPattern(self.dev)

        else: # ALIGN_TYPE_LIDIL_0_5_4
            pattern = maint.alignType11SetPattern(self.dev)

        if pattern is None:
            log.error("Invalid pattern!")
            # TODO: ...

        self.controls = maint.align10and11and14Controls(pattern, self.align_type)
        keys = list(self.controls.keys())
        keys.sort()
        max_line = 'A'
        for line in keys:
            if self.controls[line][0]:
                max_line = line
            else:
                break

        self.LBowTitle.setText(self.__tr("For each row A - %s, select the label representing the box in which in the inner lines are the <b>least</b> visible." % max_line))

        for line in self.controls:
            if not self.controls[line][0]:
                eval('self.%sComboBox.setEnabled(False)' % line.lower())
            else:
                for x in range(self.controls[line][1]):
                    eval('self.%sComboBox.addItem("%s%d")' % (line.lower(), line, x + 1))

        self.displayPage(PAGE_LBOW)



    def endLBowPage(self):
        self.values = []
        controls = list(self.controls.keys())
        controls.sort()

        for line in controls:
            if not self.controls[line][0]:
                self.values.append(0)
            else:
                exec('selected = unicode(self.%sComboBox.currentText())' % line.lower())
                try:
                    selected = int(selected[1:])
                except ValueError:
                    selected = 0

                self.values.append(selected)


    def showAioPage(self):
        self.AioIcon.setPixmap(load_pixmap('aio_align', 'other'))
        self.displayPage(PAGE_AIO)


    def endAioPage(self):
        pass


    def showColorAdjustPage(self, line_id, count=21):
        self.ColorAdjustComboBox.clear()
        self.ColorAdjustIcon.setPixmap(load_pixmap('color_adj', 'other'))
        self.ColorAdjustLabel.setText(self.__tr("Line %s:" % line_id))

        for x in range(count):
            self.ColorAdjustComboBox.addItem(str("%s%s" % (line_id, x+1)))

        self.displayPage(PAGE_COLOR_ADJ)


    def endColorAdjustPage(self, line_id):
        v = int(str(self.ColorAdjustComboBox.currentText())[1:])

        if line_id == 'F':
            self.f = v
            log.debug("F=%d" % v)

        elif line_id == 'G':
            self.g = v
            log.debug("G=%d" % v)


    def showFrontPanelPage(self):
#       self.BackButton.setEnabled(False)
        self.setAlignButton(BUTTON_FINISH)
        self.displayPage(PAGE_FRONT_PANEL)


    def endFronPanelPage(self):
        pass

    #
    #  ALIGN-TYPE SPECIFIC
    #

    def checkType2PenConfig(self):
        pass
        # TODO: set abort if problem


    def alignType8Phase1(self):
        self.num_inks = maint.alignType8Phase1(self.dev)


    def setXBow(self):
        # TODO: set abort if invalid pen config
        self.real_align_type = self.align_type
        self.align_type = ALIGN_TYPE_XBOW_OFFSET + self.dev.pen_config
        self.seq_index = -1


    def setXBowValues(self):
        if self.real_align_type ==  ALIGN_TYPE_LIDIL_0_3_8:
            maint.alignType4Phase2(self.dev, self.zca, self.b, self.c, self.d, self.e)
            maint.alignType4Phase3(self.dev)

        elif self.real_align_type == ALIGN_TYPE_LIDIL_0_4_3:
            maint.alignType5Phase2(self.dev, self.zca, self.b, self.c, self.d, self.e, self.f, self.g)
            maint.alignType5Phase3(self.dev)

        elif self.real_align_type == ALIGN_TYPE_LIDIL_VIP:
            maint.alignType7Phase2(self.dev, self.zca, self.b, self.c, self.d, self.e, self.f, self.g)
            maint.alignType7Phase3(self.dev)


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
            self.StepText.setText(self.__tr("Step %s of %s" % (p, self.step_max)))


    def setAlignButton(self, typ=BUTTON_ALIGN):
        if typ == BUTTON_ALIGN:
            self.NextButton.setText(self.__tr("Align"))
        elif typ == BUTTON_NEXT:
            self.NextButton.setText(self.__tr("Next >"))
        elif typ == BUTTON_FINISH:
            self.NextButton.setText(self.__tr("Finish"))


    def setPenConfig(self):
        self.dev.pen_config = status.getPenConfiguration(self.dev.getStatusFromDeviceID())


    def closeAll(self):
        if self.dev is not None:
            self.dev.close()


    def __tr(self,s,c = None):
        return qApp.translate("AlignDialog",s,c)
