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
# Authors: Don Welch, Yashwant Kumar Sahu, Sanjay Kumar Sharma
#

# Std Lib
import sys

# Local
from base.g import *
from base import utils
from prnt import cups
from base.codes import *
from .ui_utils import *
from base.sixext import PY3
from base.sixext import  to_unicode

# Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *



class RangeValidator(QValidator):
    def __init__(self, parent=None, name=None):
        QValidator.__init__(self, parent) #, name)


    def validate(self, input, pos):
        for x in to_unicode(input)[pos-1:]:
            if x not in to_unicode('0123456789,- '):
                return QValidator.Invalid, input, pos
            return QValidator.Acceptable, input, pos


class PinValidator(QValidator):
    def __init__(self, parent=None, name=None):
        QValidator.__init__(self, parent) #, name)


    def validate(self, input, pos):
        for x in to_unicode(input)[pos-1:]:
            if x not in to_unicode('0123456789'):
                return QValidator.Invalid, input, pos

            return QValidator.Acceptable, input, pos


class UsernameAndJobnameValidator(QValidator):
    def __init__(self, parent=None, name=None):
        QValidator.__init__(self, parent) #, name)


    def validate(self, input, pos):
        for x in to_unicode(input)[pos-1:]:
            if x in to_unicode(' /=,.:;\'"[]{}-+!@#$%^&*()'):
                return QValidator.Invalid, input, pos
            return QValidator.Acceptable, input, pos


class OptionComboBox(QComboBox):
    def __init__(self, rw, parent, name, group, option, choices, default,
                 typ=cups.PPD_UI_PICKONE, other=None, job_option=False):
        QComboBox.__init__(self, parent)
        # rw?
        self.group = group
        self.option = option
        self.choices = choices
        self.default = default
        self.typ = typ
        self.other = other
        self.job_option = job_option
        self.setObjectName(name)


    def setDefaultPushbutton(self, pushbutton):
        self.pushbutton = pushbutton


    def setOther(self, other):
        self.other = other



class OptionSpinBox(QSpinBox):
    def __init__(self,  parent, name, group, option, default, job_option=False):
        QSpinBox.__init__(self, parent)
        self.group = group
        self.option = option
        self.default = default
        self.job_option = job_option
        self.setObjectName(name)


    def setDefaultPushbutton(self, pushbutton):
        self.pushbutton = pushbutton



class OptionRadioButton(QRadioButton):
    def __init__(self, parent, name, group, option, default, job_option=False):
        QRadioButton.__init__(self, parent)
        self.group = group
        self.option = option
        self.default = default
        self.job_option = job_option
        self.setObjectName(name)


    def setDefaultPushbutton(self, pushbutton):
        self.pushbutton = pushbutton



class DefaultPushButton(QPushButton):
    def __init__(self,  parent, name, group, option, choices,
                 default, control, typ, job_option=False):
        QPushButton.__init__(self, parent)
        self.group = group
        self.option = option
        self.default = default
        self.control = control
        self.typ = typ
        self.choices = choices
        self.job_option = job_option
        self.setObjectName(name)


#class PageRangeRadioButton(QRadioButton):
#    def __init__(self, parent, page_range_edit):
#        QRadioButton.__init__(self, parent):
#            self.page_range_edit = page_range_edit


class PageRangeRadioButton(QRadioButton):
    def __init__(self, parent, name, group, option, default): #, edit_control=None ):
        QRadioButton.__init__(self, parent)
        self.group = group
        self.option = option
        self.default = default
        self.job_option = True
        self.setObjectName(name)


    def setRangeEdit(self, edit_control):
        self.edit_control = edit_control


    def setDefaultPushbutton(self, pushbutton):
        self.pushbutton = pushbutton



class PrintSettingsToolbox(QToolBox):
    def __init__(self, parent, include_job_options=False):
        QToolBox.__init__(self, parent)
        self.include_job_options = include_job_options
        self.plus_icon = QIcon(load_pixmap('plus', '16x16'))
        self.minus_icon = QIcon(load_pixmap('minus', '16x16'))
        self.last_item = 0
        self.job_options = {}
        self.job_storage_enable = False
        self.ppd_type = 0
        self.pin_count = 0

        # self.currentChanged[int].connect(self.PrintSettingsToolbox_currentChanged)
        self.currentChanged[int].connect(self.PrintSettingsToolbox_currentChanged)


    def getPrintCommands(self, file_list=None):
        # File list: [(path, mime_type, mime_desc, title, num_pages), ...]
        if file_list is None or not file_list:
            return []

        print_commands = []

        try:
            copies = int(self.job_options['copies'])
        except ValueError:
            copies = 1

        if copies < 1:
            copies = 1
            log.warning("Copies < 1, setting to 1.")
        elif copies > 99:
            copies = 99
            log.warning("Copies > 99, setting to 99.")

        #page_range = unicode(self.pageRangeEdit.text())
        page_range = self.job_options['pagerange']

        try:
            x = utils.expand_range(page_range)
        except ValueError:
            log.error("Invalid page range: %s" % page_range)
            return []

        all_pages = not page_range
        #page_set = int(self.pageSetComboBox.currentItem())
        page_set = self.job_options['pageset']

        cups.resetOptions()
        cups.openPPD(self.cur_printer)
        if self.ppd_type == 1 and self.pin_count == 0:
           self.setPrinterOption("HPDigit", "1111")
        current_options = dict(cups.getOptions())
        cups.closePPD()

        nup = int(current_options.get("number-up", 1))
        psnup = utils.which('psnup')

        for p, t, d, title, num_pages in file_list:
            alt_nup = (nup > 1 and t == 'application/postscript' and psnup)

            if utils.which('lpr'):
                if alt_nup:
                    cmd = ' '.join(['psnup', '-%d' % nup, ''.join(['"', p, '"']), '| lpr -P', self.cur_printer])
                else:
                    cmd = ' '.join(['lpr -P', self.cur_printer])

                if copies > 1:
                    cmd = ' '.join([cmd, '-#%d' % copies])

            else: # lp
                if alt_nup:
                    cmd = ' '.join(['psnup', '-%d' % nup, ''.join(['"', p, '"']), '| lp -c -d', self.cur_printer])
                else:
                    cmd = ' '.join(['lp -c -d', self.cur_printer])

                if copies > 1:
                    cmd = ' '.join([cmd, '-n%d' % copies])


            if not all_pages and page_range:
                cmd = ' '.join([cmd, '-o page-ranges=%s' % page_range])

            #fit_to_page = "fit-to-page"
            # code added for ps orientation issue but its on cups 
            #cmd = ' '.join([cmd, '-o %s' % fit_to_page])

            if page_set:
                cmd = ' '.join([cmd, '-o page-set=%s' % page_set])

            # Job Storage
            # self.job_storage_mode = (0=Off, 1=P&H, 2=PJ, 3=QC, 4=SJ)
            # self.job_storage_pin = u"" (dddd)
            # self.job_storage_use_pin = True|False
            # self.job_storage_username = u""
            # self.job_storage_auto_username = True|False
            # self.job_storage_jobname = u""
            # self.job_storage_auto_jobname = True|False
            # self.job_storage_job_exist = (0=replace, 1=job name+(1-99))

            if self.job_storage_enable:
                if self.job_storage_mode != JOB_STORAGE_TYPE_OFF:
                    if self.job_storage_mode == JOB_STORAGE_TYPE_PROOF_AND_HOLD:
                        cmd = ' '.join([cmd, '-o HOLD=PROOF'])

                    elif self.job_storage_mode == JOB_STORAGE_TYPE_PERSONAL:
                        if self.job_storage_use_pin:
                            cmd = ' '.join([cmd, '-o HOLD=ON'])
                            cmd = ' '.join([cmd, '-o HOLDTYPE=PRIVATE'])
                            cmd = ' '.join([cmd, '-o HOLDKEY=%s' % self.job_storage_pin.encode('ascii')])
                        else:
                            cmd = ' '.join([cmd, '-o HOLD=PROOF'])
                            cmd = ' '.join([cmd, '-o HOLDTYPE=PRIVATE'])

                    elif self.job_storage_mode == JOB_STORAGE_TYPE_QUICK_COPY:
                        cmd = ' '.join([cmd, '-o HOLD=ON'])
                        cmd = ' '.join([cmd, '-o HOLDTYPE=PUBLIC'])

                    elif self.job_storage_mode == JOB_STORAGE_TYPE_STORE:
                        if self.job_storage_use_pin:
                            cmd = ' '.join([cmd, '-o HOLD=STORE'])
                            cmd = ' '.join([cmd, '-o HOLDTYPE=PRIVATE'])
                            cmd = ' '.join([cmd, '-o HOLDKEY=%s' % self.job_storage_pin.encode('ascii')])
                        else:
                            cmd = ' '.join([cmd, '-o HOLD=STORE'])

                    cmd = ' '.join([cmd, '-o USERNAME=%s' % self.job_storage_username.encode('ascii')\
                        .replace(" ", "_")])

                    cmd = ' '.join([cmd, '-o JOBNAME=%s' % self.job_storage_jobname.encode('ascii')\
                        .replace(" ", "_")])

                    if self.job_storage_job_exist == 1:
                        cmd = ' '.join([cmd, '-o DUPLICATEJOB=APPEND'])
                    else:
                        cmd = ' '.join([cmd, '-o DUPLICATEJOB=REPLACE'])

                else: # Off
                    cmd = ' '.join([cmd, '-o HOLD=OFF'])

            if not alt_nup:
                cmd = ''.join([cmd, ' "', p, '"'])

            print_commands.append(cmd)

        return print_commands


    def PrintSettingsToolbox_currentChanged(self, i):
        if i != -1:
            self.setItemIcon(self.last_item, self.plus_icon)
            self.setItemIcon(i, self.minus_icon)
            self.last_item = i


    def updateUi(self, cur_device, cur_printer):
        #print "updateUi(%s, %s)" % (cur_device, cur_printer)
        self.cur_device = cur_device
        self.cur_printer = cur_printer
        self.current_options = None
        
        while self.count():
            self.removeItem(0)

        self.loading = True
        cups.resetOptions()
        cups.openPPD(self.cur_printer)
        cur_outputmode = ""

        try:
            if 1:
            #try:
                current_options = dict(cups.getOptions())
                self.current_options = current_options
                if self.include_job_options:
                    self.beginControlGroup("job_options", self.__tr("Job Options"))

                    # Num. copies (SPINNER)
                    try:
                        current = int(current_options.get('copies', '1'))
                    except ValueError:
                        current = 1

                    self.addControlRow("copies", self.__tr("Number of copies"),
                        cups.UI_SPINNER, current, (1, 99), 1, job_option=True)
                    self.job_options['copies'] = current

                    # page range RADIO + RANGE (custom)
                    current = current_options.get('pagerange', '')

                    self.addControlRow("pagerange", self.__tr("Page Range"),
                        cups.UI_PAGE_RANGE, current, None, None, job_option=True)

                    self.job_options['pagerange'] = current

                    # page set (COMBO/PICKONE)
                    current = current_options.get('pageset', 'all')
                    self.addControlRow("pageset", self.__tr("Page Set"),
                        cups.PPD_UI_PICKONE, current,
                        [('all', self.__tr("AllPages")),
                         ('even', self.__tr("Even")),
                         ('odd', self.__tr("Odd"))], 'all', job_option=True)

                    self.job_options['pageset'] = current
#                    if current == u'even':
#                        self.job_options["pageset"] = PAGE_SET_EVEN
#                    elif current == u'odd':
#                        self.job_options["pageset"] = PAGE_SET_ODD
#                    else:
#                        self.job_options["pageset"] = PAGE_SET_ALL

                    self.endControlGroup() # job_options

                if not self.cur_device.device_type == DEVICE_TYPE_FAX:
                    self.beginControlGroup("basic", self.__tr("Basic"))

                    # Basic
                        # PageSize (in PPD section)
                        # orientation-requested
                        # sides
                        # outputorder
                        # Collate

                    current = current_options.get('orientation-requested', '3')

                    self.addControlRow("orientation-requested", self.__tr("Page Orientation"),
                        cups.PPD_UI_PICKONE, current,
                        [('3', self.__tr('Portrait')),
                         ('4', self.__tr('Landscape')),
                         ('5', self.__tr('Reverse landscape')),
                         ('6', self.__tr('Reverse portrait'))], '3')

                    log.debug("Option: orientation-requested")
                    log.debug("Current value: %s" % current)

                    duplexer = self.cur_device.dq.get('duplexer', 0)
                    log.debug("Duplexer = %d" % duplexer)

                    if duplexer:
                        current = current_options.get('sides', 'one-sided')
                        self.addControlRow("sides",
                            self.__tr("Duplex (Print on both sides of the page)"),
                            cups.PPD_UI_PICKONE, current,
                            [('one-sided',self.__tr('Single sided')),
                             ('two-sided-long-edge', self.__tr('Two sided (long edge)')),
                             ('two-sided-short-edge', self.__tr('Two sided (short edge)'))], 'one-sided')

                        log.debug("Option: sides")
                        log.debug("Current value: %s" % current)

                    current = current_options.get('outputorder', 'normal')

                    self.addControlRow("outputorder",
                        self.__tr("Output Order"),
                        cups.PPD_UI_PICKONE, current,
                        [('normal', self.__tr('Normal (Print first page first)')),
                         ('reverse', self.__tr('Reversed (Print last page first)'))], 'normal')

                    log.debug("Option: outputorder")
                    log.debug("Current value: %s" % current)

                    #If collate section is not in the PPD, only then add a collate section.
                    to_add = cups.duplicateSection("collate")
                    if to_add == 0:
                        current = utils.to_bool(current_options.get('Collate', '0'))

                        self.addControlRow("Collate",
                            self.__tr("Collate (Group together multiple copies)"),
                            cups.PPD_UI_BOOLEAN, current,
                            [], 0)

                        log.debug("Option: Collate")
                        log.debug("Current value: %s" % current)

                    self.endControlGroup()

                groups = cups.getGroupList()

                #print groups

                for g in groups:
                    if 'jobretention' in g.lower():
                        log.debug("HPJobRetention skipped.")
                        continue

                    try:
                        text, num_subgroups = cups.getGroup(g)
                        if text == "JCL":
                           text = "Secure Printing"
                           self.ppd_type = 1
                    except TypeError:
                        log.warn("Group %s returned None" % g)
                        continue

                    read_only = 'install' in g.lower()


                    if g.lower() == 'printoutmode':
                        text = self.__tr("Quality (also see 'Printout Mode' under 'General')")

                    self.beginControlGroup(g, str(text))

                    log.debug("  Text: %s" % str(text))
                    log.debug("Num subgroups: %d" % num_subgroups)

                    options = cups.getOptionList(g)

                    #print options

                    for o in options:
                        log.debug("  Option: %s" % repr(o))

                        if 'pageregion' in o.lower():
                            log.debug("Page Region skipped.")
                            continue

                        try:
                            option_text, defchoice, conflicted, ui  = cups.getOption(g, o)
                        except TypeError:
                            log.warn("Option %s in group %s returned None" % (o, g))
                            continue


                        if o.lower() == 'quality':
                            option_text = self.__tr("Quality")

                        log.debug("    Text: %s" % repr(option_text))
                        log.debug("    Defchoice: %s" % repr(defchoice))

                        choices = cups.getChoiceList(g, o)

                        value = None
                        choice_data = []
                        for c in choices:
                            log.debug("    Choice: %s" % repr(c))

                            # TODO: Add custom paper size controls
                            if 'pagesize' in o.lower() and 'custom' in c.lower():
                                log.debug("Skipped.")
                                continue

                            choice_text, marked = cups.getChoice(g, o, c)


                            log.debug("      Text: %s" % repr(choice_text))

                            if marked:
                                value = c

                            choice_data.append((c, choice_text))

                        if o.lower() == 'outputmode':
                            if value is not None:
                                cur_outputmode = value
                            else:
                                cur_outputmode = defchoice                                
                        if option_text == "[Pin-4 Digits]":
                           self.addControlRow(o, option_text, cups.UI_SPINNER, 1111, (1000, 9999), 1111)                          
                        else: 
                           self.addControlRow(o, option_text, ui, value, choice_data, defchoice, read_only)

                    self.endControlGroup()

##                        if 'pagesize' in o.lower(): # and 'custom' in c.lower():
##                            current = 0.0
##                            width_widget = self.addControlRow(widget, "custom", "custom-width", self.__tr("Custom Paper Width"), cups.UI_UNITS_SPINNER,
##                                current, (0.0, 0.0), 0.0)
##
##                            current = 0.0
##                            height_widget = self.addControlRow("custom", "custom-height", self.__tr("Custom Paper Height"), cups.UI_UNITS_SPINNER,
##                                current, (0.0, 0.0), 0.0)
##
##                            if value.lower() == 'custom':
##                                pass

                # N-Up
                    # number-up
                    # number-up-layout
                    # page-border

                self.beginControlGroup("nup", self.__tr("N-Up (Multiple document pages per printed page)"))
                current = current_options.get('number-up', '1')

                self.addControlRow("number-up", self.__tr("Pages per Sheet"),
                    cups.PPD_UI_PICKONE, current,
                    [('1', self.__tr('1 page per sheet')),
                     ('2', self.__tr('2 pages per sheet')),
                     ('4', self.__tr('4 pages per sheet'))], '1')

                log.debug("  Option: number-up")
                log.debug("  Current value: %s" % current)

                current = current_options.get('number-up-layout', 'lrtb')

                self.addControlRow("number-up-layout", self.__tr("Layout"),
                    cups.PPD_UI_PICKONE, current,
                    [('btlr', self.__tr('Bottom to top, left to right')),
                     ('btrl', self.__tr('Bottom to top, right to left')),
                     ('lrbt', self.__tr('Left to right, bottom to top')),
                     ('lrtb', self.__tr('Left to right, top to bottom')),
                     ('rlbt', self.__tr('Right to left, bottom to top')),
                     ('rltb', self.__tr('Right to left, top to bottom')),
                     ('tblr', self.__tr('Top to bottom, left to right')),
                     ('tbrl', self.__tr('Top to bottom, right to left')) ], 'lrtb')

                log.debug("  Option: number-up-layout")
                log.debug("  Current value: %s" % current)

                current = current_options.get('page-border', 'none')

                self.addControlRow("page-border",
                    self.__tr("Printed Border Around Each Page"),
                    cups.PPD_UI_PICKONE, current,
                    [('double', self.__tr("Two thin borders")),
                     ("double-thick", self.__tr("Two thick borders")),
                     ("none", self.__tr("No border")),
                     ("single", self.__tr("One thin border")),
                     ("single-thick", self.__tr("One thick border"))], 'none')

                log.debug("  Option: page-border")
                log.debug("  Current value: %s" % current)

                self.endControlGroup()

                # Adjustment
                    # brightness
                    # gamma

                if not self.cur_device.device_type == DEVICE_TYPE_FAX:
                    self.beginControlGroup("adjustment", self.__tr("Printout Appearance"))

                    current = int(current_options.get('brightness', 100))

                    log.debug("  Option: brightness")
                    log.debug("  Current value: %s" % current)

                    self.addControlRow("brightness", self.__tr("Brightness"),
                        cups.UI_SPINNER, current, (0, 200), 100, suffix=" %")

                    current = int(current_options.get('gamma', 1000))

                    log.debug("  Option: gamma")
                    log.debug("  Current value: %s" % current)

                    self.addControlRow("gamma", self.__tr("Gamma"), cups.UI_SPINNER, current,
                        (1, 10000), 1000)

                    self.endControlGroup()

                # Margins (pts)
                    # page-left
                    # page-right
                    # page-top
                    # page-bottom

##                if 0:
##                    # TODO: cupsPPDPageSize() fails on LaserJets. How do we get margins in this case? Defaults?
##                    # PPD file for LJs has a HWMargin entry...
##                    page, page_width, page_len, left, bottom, right, top = cups.getPPDPageSize()
##
##                    right = page_width - right
##                    top = page_len - top
##
##                    self.addGroupHeading("margins", self.__tr("Margins"))
##                    current_top = current_options.get('page-top', 0) # pts
##                    current_bottom = current_options.get('page-bottom', 0) # pts
##                    current_left = current_options.get('page-left', 0) # pts
##                    current_right = current_options.get('page-right', 0) # pts
##
##                    log.debug("  Option: page-top")
##                    log.debug("  Current value: %s" % current_top)
##
##                    self.addControlRow("margins", "page-top", self.__tr("Top margin"),
##                        cups.UI_UNITS_SPINNER, current_top,
##                        (0, page_len), top)
##
##                    self.addControlRow("margins", "page-bottom", self.__tr("Bottom margin"),
##                        cups.UI_UNITS_SPINNER, current_bottom,
##                        (0, page_len), bottom)
##
##                    self.addControlRow("margins", "page-left", self.__tr("Right margin"),
##                        cups.UI_UNITS_SPINNER, current_left,
##                        (0, page_width), left)
##
##                    self.addControlRow("margins", "page-right", self.__tr("Left margin"),
##                        cups.UI_UNITS_SPINNER, current_right,
##                        (0, page_width), right)

                # Image Printing
                    # position
                    # natural-scaling
                    # saturation
                    # hue

                self.beginControlGroup("image", self.__tr("Image Printing"))

                current = utils.to_bool(current_options.get('fitplot', 'false'))

                self.addControlRow("fitplot",
                    self.__tr("Fit to Page"),
                    cups.PPD_UI_BOOLEAN, current,
                    [], 0)

                current = current_options.get('position', 'center')

                self.addControlRow("position", self.__tr("Position on Page"),
                    cups.PPD_UI_PICKONE, current,
                    [('center', self.__tr('Centered')),
                     ('top', self.__tr('Top')),
                     ('left', self.__tr('Left')),
                     ('right', self.__tr('Right')),
                     ('top-left', self.__tr('Top left')),
                     ('top-right', self.__tr('Top right')),
                     ('bottom', self.__tr('Bottom')),
                     ('bottom-left', self.__tr('Bottom left')),
                     ('bottom-right', self.__tr('Bottom right'))], 'center')

                log.debug("  Option: position")
                log.debug("  Current value: %s" % current)

                if not self.cur_device.device_type == DEVICE_TYPE_FAX:
                    current = int(current_options.get('saturation', 100))

                    log.debug("  Option: saturation")
                    log.debug("  Current value: %s" % current)

                    self.addControlRow("saturation", self.__tr("Saturation"),
                        cups.UI_SPINNER, current, (0, 200), 100, suffix=" %")

                    current = int(current_options.get('hue', 0))

                    log.debug("  Option: hue")
                    log.debug("  Current value: %s" % current)

                    self.addControlRow("hue", self.__tr("Hue (color shift/rotation)"),
                        cups.UI_SPINNER, current,
                        (-100, 100), 0)

                current = int(current_options.get('natural-scaling', 100))

                log.debug("  Option: natural-scaling")
                log.debug("  Current value: %s" % current)

                self.addControlRow("natural-scaling",
                    self.__tr('"Natural" Scaling (relative to image)'),
                    cups.UI_SPINNER, current, (1, 800), 100, suffix=" %")

                current = int(current_options.get('scaling', 100))

                log.debug("  Option: scaling")
                log.debug("  Current value: %s" % current)

                self.addControlRow("scaling", self.__tr("Scaling (relative to page)"),
                    cups.UI_SPINNER, current,
                    (1, 800), 100, suffix=" %")

                self.endControlGroup()

                # Misc
                    # PrettyPrint
                    # job-sheets
                    # mirror

                self.beginControlGroup("misc", self.__tr("Miscellaneous"))

                log.debug("Group: Misc")

                current = utils.to_bool(current_options.get('prettyprint', '0'))

                self.addControlRow("prettyprint",
                    self.__tr('"Pretty Print" Text Documents (Add headers and formatting)'),
                    cups.PPD_UI_BOOLEAN, current, [], 0)

                log.debug("  Option: prettyprint")
                log.debug("  Current value: %s" % current)

                if not self.cur_device.device_type == DEVICE_TYPE_FAX:
                    current = current_options.get('job-sheets', 'none').split(',')

                    try:
                        start = current[0]
                    except IndexError:
                        start = 'none'

                    try:
                        end = current[1]
                    except IndexError:
                        end = 'none'

                    # TODO: Look for locally installed banner pages beyond the default CUPS ones?
                    self.addControlRow("job-sheets", self.__tr("Banner Pages"), cups.UI_BANNER_JOB_SHEETS,
                        (start, end),
                        [("none", self.__tr("No banner page")),
                         ('classified', self.__tr("Classified")),
                         ('confidential', self.__tr("Confidential")),
                         ('secret', self.__tr("Secret")),
                         ('standard', self.__tr("Standard")),
                         ('topsecret', self.__tr("Top secret")),
                         ('unclassified', self.__tr("Unclassified"))], ('none', 'none'))

                    log.debug("  Option: job-sheets")
                    log.debug("  Current value: %s,%s" % (start, end))

                current = utils.to_bool(current_options.get('mirror', '0'))

                self.addControlRow("mirror", self.__tr('Mirror Printing'),
                    cups.PPD_UI_BOOLEAN, current, [], 0)

                log.debug("  Option: mirror")
                log.debug("  Current value: %s" % current)

                self.endControlGroup()
                
                #Summary
                    #color input
                    #quality
                quality_attr_name = "OutputModeDPI"
                cur_outputmode_dpi = cups.findPPDAttribute(quality_attr_name, cur_outputmode)
                if cur_outputmode_dpi is not None:
                    log.debug("Adding Group: Summary outputmode is : %s" % cur_outputmode)
                    log.debug("Adding Group: Summary outputmode dpi is : %s" % to_unicode (cur_outputmode_dpi))
                    self.beginControlGroup("sumry", self.__tr("Summary"))
                    self.addControlRow("colorinput", self.__tr('Color Input / Black Render'),
                        cups.UI_INFO, to_unicode (cur_outputmode_dpi), [], read_only)
                    self.addControlRow("quality", self.__tr('Print Quality'),
                        cups.UI_INFO, cur_outputmode, [], read_only)
                    self.endControlGroup()
                    log.debug("End adding Group: Summary")
                   

                self.job_storage_enable = 0 #self.cur_device.mq.get('job-storage', JOB_STORAGE_DISABLE) == JOB_STORAGE_ENABLE


                if self.job_storage_enable:
                    self.job_storage_pin = to_unicode(current_options.get('HOLDKEY', '0000')[:4])
                    self.job_storage_username = to_unicode(current_options.get('USERNAME', prop.username)[:16])
                    self.job_storage_jobname = to_unicode(current_options.get('JOBNAME', to_unicode('Untitled'))[:16])
                    hold = to_unicode(current_options.get('HOLD', to_unicode('OFF')))
                    holdtype = to_unicode(current_options.get('HOLDTYPE', to_unicode('PUBLIC')))
                    self.job_storage_use_pin = False
                    duplicate = to_unicode(current_options.get('DUPLICATEJOB', to_unicode('REPLACE')))
                    self.job_storage_auto_username = True
                    self.job_storage_auto_jobname = True
                    self.job_storage_mode = JOB_STORAGE_TYPE_OFF

                    if hold == 'OFF':
                        self.job_storage_mode = JOB_STORAGE_TYPE_OFF

                    elif hold == 'ON':
                        if holdtype == to_unicode('PUBLIC'):
                            self.job_storage_mode = JOB_STORAGE_TYPE_QUICK_COPY

                        else: # 'PRIVATE'
                            self.job_storage_mode = JOB_STORAGE_TYPE_PERSONAL
                            self.job_storage_use_pin = True

                    elif hold == to_unicode('PROOF'):
                        if holdtype == to_unicode('PUBLIC'):
                            self.job_storage_mode = JOB_STORAGE_TYPE_PROOF_AND_HOLD
                        else:
                            self.job_storage_mode = JOB_STORAGE_TYPE_PERSONAL
                            self.job_storage_use_pin = True

                    elif hold == to_unicode('STORE'):
                        self.job_storage_mode = JOB_STORAGE_TYPE_STORE
                        self.job_storage_use_pin = (holdtype == 'PRIVATE')

                    if duplicate == to_unicode('REPLACE'):
                        self.job_storage_job_exist = JOB_STORAGE_EXISTING_JOB_REPLACE
                    else: # u'APPEND'
                        self.job_storage_job_exist = JOB_STORAGE_EXISTING_JOB_APPEND_1_99

                    # option, text, typ, value, choices, default, read_only=False, suffix="", job_option=False)

                    self.beginControlGroup("jobstorage", self.__tr("Job Storage and Secure Printing"))

                    self.addControlRow("job-storage-mode", self.__tr("Mode"),
                                       cups.UI_JOB_STORAGE_MODE, None, None, None)

                    self.addControlRow("job-storage-pin", self.__tr("Make job private (use PIN to print)"),
                                      cups.UI_JOB_STORAGE_PIN, None, None, None )

                    self.addControlRow("job-storage-username", self.__tr("User name (for job identification)"),
                                       cups.UI_JOB_STORAGE_USERNAME, None, None, None)

                    self.addControlRow("job-storage-id", self.__tr("Job name/ID (for job identification)"),
                                      cups.UI_JOB_STORAGE_ID, None, None, None)

                    self.addControlRow("job-storage-id-exists", self.__tr("If job name/ID already exists..."),
                                       cups.UI_JOB_STORAGE_ID_EXISTS, None, None, None)

                    self.endControlGroup()
                    self.updateJobStorageControls()

                # use: self.job_options['xxx'] so that values can be picked up by getPrintCommand(


            #except Exception, e:
                #log.exception()
            #    pass

        finally:
            cups.closePPD()
            self.loading = False


    def beginControlGroup(self, group, text):
        log.debug("BeginGroup: %s" % group)
        self.row = 0
        self.widget = QWidget()
        self.gridlayout = QGridLayout(self.widget)
        self.group = group
        self.text = text


    def endControlGroup(self):
        log.debug("EndGroup: %s" % self.group)
        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.row += 1
        self.gridlayout.addItem(spacer, self.row, 0, 1, 1)
        i = self.addItem(self.widget, self.text)

        if i:
            self.setItemIcon(i, self.plus_icon)
        else:
            self.setItemIcon(i, self.minus_icon)

        self.widget, self.gridlayout = None, None


    def addControlRow(self, option, text, typ, value, choices, default, read_only=False, suffix="", job_option=False):

        if typ == cups.PPD_UI_BOOLEAN: # () On (*) Off widget
            HBoxLayout = QHBoxLayout()
            HBoxLayout.setObjectName("HBoxLayout")

            OptionLabel = QLabel(self.widget)
            OptionLabel.setObjectName("OptionLabel")
            HBoxLayout.addWidget(OptionLabel)

            SpacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            HBoxLayout.addItem(SpacerItem)

            GroupBox = QFrame(self.widget)

            gridlayout1 = QGridLayout(GroupBox)
            OnRadioButton = OptionRadioButton(GroupBox, "OnRadioButton", self.group,
                                              option, default, job_option)
            gridlayout1.addWidget(OnRadioButton,0,0,1,1)
            OffRadioButton = OptionRadioButton(GroupBox, "OffRadioButton", self.group,
                                               option, default, job_option)
            gridlayout1.addWidget(OffRadioButton,0,1,1,1)
            HBoxLayout.addWidget(GroupBox)

            DefaultButton = DefaultPushButton(self.widget, "defaultPushButton", self.group, option,
                choices, default, (OnRadioButton, OffRadioButton), typ, job_option)

            #GroupBox.setDefaultPushbutton(DefaultButton)
            OnRadioButton.setDefaultPushbutton(DefaultButton)
            OffRadioButton.setDefaultPushbutton(DefaultButton)

            HBoxLayout.addWidget(DefaultButton)
            self.gridlayout.addLayout(HBoxLayout, self.row, 0, 1, 1)

            OptionLabel.setText(text)
            OnRadioButton.setText(self.__tr("On"))
            OffRadioButton.setText(self.__tr("Off"))

            DefaultButton.setText("Default")

            #type of 'value' and 'default' can be unicode (ppd values), str, int or boolean, so we need to typecast it to bool for easy comparison
            if value == True or value == 'True' or value == 'true':
               value = True;
            else:
               value = False;

            if default == True or default == 'True' or default == 'true':
               default = True;
            else:
               default = False;

            if value == default:
                DefaultButton.setEnabled(False)
            DefaultButton.clicked.connect(self.DefaultButton_clicked)

            if value:
                OnRadioButton.setChecked(True)
            else:
                OffRadioButton.setChecked(True)
            OnRadioButton.toggled[bool].connect(self.BoolRadioButtons_clicked)

            if read_only:
                OnRadioButton.setEnabled(False)
                OffRadioButton.setEnabled(False)
                DefaultButton.setEnabled(False)



        elif typ == cups.PPD_UI_PICKONE: # Combo box widget
            #print option, job_option
            HBoxLayout = QHBoxLayout()
            HBoxLayout.setObjectName("HBoxLayout")

            OptionLabel = QLabel(self.widget)
            OptionLabel.setObjectName("OptionLabel")
            HBoxLayout.addWidget(OptionLabel)

            SpacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            HBoxLayout.addItem(SpacerItem)

            ComboBox = OptionComboBox(0, self.widget, "ComboBox", self.group, option,
                                      choices, default, typ, None, job_option)

            HBoxLayout.addWidget(ComboBox)

            DefaultButton = DefaultPushButton(self.widget, "DefaultButton", self.group, option,
                choices, default, ComboBox, typ, job_option)

            ComboBox.setDefaultPushbutton(DefaultButton)
            HBoxLayout.addWidget(DefaultButton)

            self.gridlayout.addLayout(HBoxLayout, self.row, 0, 1, 1)

            OptionLabel.setText(text)
            DefaultButton.setText("Default")

            i, x, y = 0, None, None
            for c, t in choices:
                d = c.lower()
                if value is not None and d == value.lower():
                    x = i

                if d == default.lower():
                    y = t

                ComboBox.insertItem(i, t)
                i += 1

            if x is not None:
                ComboBox.setCurrentIndex(x)
            else:
                ComboBox.setCurrentIndex(0)

            if value is not None and value.lower() == default.lower():
                DefaultButton.setEnabled(False)

            #self.linkPrintoutModeAndQuality(option, value)
#
#            if read_only:
#                optionComboBox.setEnabled(False)
#                defaultPushButton.setEnabled(False)
#            elif y is not None:
#                QToolTip.add(defaultPushButton, self.__tr('Set to default value of "%1".').arg(y))
#

            DefaultButton.clicked.connect(self.DefaultButton_clicked)
            ComboBox.currentIndexChanged["const QString &"].connect(self.ComboBox_indexChanged)
            ComboBox.highlighted["const QString &"].connect(self.ComboBox_highlighted)

            control = ComboBox

        elif typ == cups.UI_SPINNER: # Spinner widget

            HBoxLayout = QHBoxLayout()
            HBoxLayout.setObjectName("HBoxLayout")

            OptionLabel = QLabel(self.widget)
            OptionLabel.setObjectName("OptionLabel")
            HBoxLayout.addWidget(OptionLabel)

            SpacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            HBoxLayout.addItem(SpacerItem)

            SpinBox = OptionSpinBox(self.widget,"SpinBox", self.group, option, default, job_option)
            HBoxLayout.addWidget(SpinBox)

            DefaultButton = DefaultPushButton(self.widget,"DefaultButton", self.group, option,
                choices, default, SpinBox, typ, job_option)

            SpinBox.setDefaultPushbutton(DefaultButton)
            HBoxLayout.addWidget(DefaultButton)

            self.gridlayout.addLayout(HBoxLayout, self.row, 0, 1, 1)

            min, max = choices
            SpinBox.setMinimum(min)
            SpinBox.setMaximum(max)
            SpinBox.setValue(value)

            if suffix:
                SpinBox.setSuffix(suffix)

            OptionLabel.setText(text)
            DefaultButton.setText("Default")

            SpinBox.valueChanged[int].connect(self.SpinBox_valueChanged)
            DefaultButton.clicked.connect(self.DefaultButton_clicked)

            DefaultButton.setEnabled(not value == default)

            if read_only:
                SpinBox.setEnabled(False)
                DefaultButton.setEnabled(False)

        elif typ == cups.UI_BANNER_JOB_SHEETS:  # Job sheets widget
            HBoxLayout = QHBoxLayout()
            HBoxLayout.setObjectName("HBoxLayout")

            OptionLabel = QLabel(self.widget)
            OptionLabel.setObjectName("OptionLabel")
            HBoxLayout.addWidget(OptionLabel)

            SpacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            HBoxLayout.addItem(SpacerItem)

            StartLabel = QLabel(self.widget)
            HBoxLayout.addWidget(StartLabel)

            StartComboBox = OptionComboBox(0, self.widget, "StartComboBox", self.group,
                "start", choices, default, typ)

            HBoxLayout.addWidget(StartComboBox)

            EndLabel = QLabel(self.widget)
            HBoxLayout.addWidget(EndLabel)

            EndComboBox = OptionComboBox(0, self.widget, "EndComboBox", self.group, "end", choices,
                default, typ, StartComboBox)

            HBoxLayout.addWidget(EndComboBox)

            StartComboBox.setOther(EndComboBox)

            DefaultButton = DefaultPushButton(self.widget, "DefaultButton", self.group, option, choices,
                default, (StartComboBox, EndComboBox), typ, job_option)

            HBoxLayout.addWidget(DefaultButton)

            self.gridlayout.addLayout(HBoxLayout, self.row, 0, 1, 1)

            StartComboBox.setDefaultPushbutton(DefaultButton)
            EndComboBox.setDefaultPushbutton(DefaultButton)

            OptionLabel.setText(text)
            DefaultButton.setText("Default")

            StartLabel.setText(self.__tr("Start:"))
            EndLabel.setText(self.__tr("End:"))

            s, e, y, z = None, None, None, None
            for c, t in choices:
                d = c.lower()
                if value is not None:
                    if d == value[0].lower():
                        s = t

                    if d == value[1].lower():
                        e = t

                if d == default[0].lower():
                    y = t

                if d == default[1].lower():
                    z = t

                StartComboBox.insertItem(0, t)
                EndComboBox.insertItem(0, t)

            if s is not None:
                StartComboBox.setCurrentIndex(StartComboBox.findText(s))

            if e is not None:
                EndComboBox.setCurrentIndex(EndComboBox.findText(e))

            if value is not None and \
                value[0].lower() == default[0].lower() and \
                value[1].lower() == default[1].lower():

                DefaultButton.setEnabled(False)

            StartComboBox.activated["const QString&"].connect(self.BannerComboBox_activated)
            EndComboBox.activated["const QString&"].connect(self.BannerComboBox_activated)
            DefaultButton.clicked.connect(self.DefaultButton_clicked)

        elif typ == cups.PPD_UI_PICKMANY:
            log.error("Unrecognized type: pickmany")

        elif typ == cups.UI_UNITS_SPINNER:
            log.error("Unrecognized type: units spinner")

        elif typ == cups.UI_PAGE_RANGE:
            HBoxLayout = QHBoxLayout()
            HBoxLayout.setObjectName("HBoxLayout")

            OptionLabel = QLabel(self.widget)
            OptionLabel.setObjectName("OptionLabel")
            HBoxLayout.addWidget(OptionLabel)

            SpacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            HBoxLayout.addItem(SpacerItem)

            GroupBox = QFrame(self.widget)

            gridlayout1 = QGridLayout(GroupBox)

            AllRadioButton = PageRangeRadioButton(GroupBox, "AllRadioButton",
                                               self.group, option, default)

            gridlayout1.addWidget(AllRadioButton,0,0,1,1)
            RangeRadioButton = PageRangeRadioButton(GroupBox, "RangeRadioButton",
                                                 self.group, option, default)

            gridlayout1.addWidget(RangeRadioButton,0,1,1,1)
            HBoxLayout.addWidget(GroupBox)

            PageRangeEdit = QLineEdit(self.widget)
            HBoxLayout.addWidget(PageRangeEdit)
            PageRangeEdit.setValidator(RangeValidator(PageRangeEdit))

            AllRadioButton.setRangeEdit(PageRangeEdit)
            RangeRadioButton.setRangeEdit(PageRangeEdit)

            DefaultButton = DefaultPushButton(self.widget, "defaultPushButton", self.group, option,
                choices, default, (AllRadioButton, RangeRadioButton, PageRangeEdit), typ, job_option)

            AllRadioButton.setDefaultPushbutton(DefaultButton)
            RangeRadioButton.setDefaultPushbutton(DefaultButton)

            HBoxLayout.addWidget(DefaultButton)
            self.gridlayout.addLayout(HBoxLayout, self.row, 0, 1, 1)

            OptionLabel.setText(text)
            AllRadioButton.setText(self.__tr("All pages"))
            RangeRadioButton.setText(self.__tr("Page Range:"))

            DefaultButton.setText("Default")
            DefaultButton.setEnabled(False)

            AllRadioButton.setChecked(True)
            PageRangeEdit.setEnabled(False)

            # TODO: Set current

            AllRadioButton.toggled[bool].connect(self.PageRangeAllRadio_toggled)
            RangeRadioButton.toggled[bool].connect(self.PageRangeRangeRadio_toggled)
            DefaultButton.clicked.connect(self.DefaultButton_clicked)
            PageRangeEdit.textChanged["const QString &"].connect(self.PageRangeEdit_textChanged)
            PageRangeEdit.editingFinished.connect(self.PageRangeEdit_editingFinished)

        elif typ == cups.UI_JOB_STORAGE_MODE:
            HBoxLayout = QHBoxLayout()
            HBoxLayout.setObjectName("HBoxLayout")

            OptionLabel = QLabel(self.widget)
            OptionLabel.setObjectName("OptionLabel")
            HBoxLayout.addWidget(OptionLabel)

            SpacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            HBoxLayout.addItem(SpacerItem)

            self.JobStorageModeComboBox = QComboBox(self.widget)
            HBoxLayout.addWidget(self.JobStorageModeComboBox)

            self.JobStorageModeDefaultButton = QPushButton(self.widget)
            HBoxLayout.addWidget(self.JobStorageModeDefaultButton)

            self.gridlayout.addLayout(HBoxLayout, self.row, 0, 1, 1)

            OptionLabel.setText(text)
            self.JobStorageModeDefaultButton.setText(self.__tr("Default"))

            self.JobStorageModeComboBox.addItem(self.__tr("Off/Disabled"), JOB_STORAGE_TYPE_OFF)
            self.JobStorageModeComboBox.addItem(self.__tr("Proof and Hold"), JOB_STORAGE_TYPE_PROOF_AND_HOLD)
            self.JobStorageModeComboBox.addItem(self.__tr("Personal/Private Job"), JOB_STORAGE_TYPE_PERSONAL)
            self.JobStorageModeComboBox.addItem(self.__tr("Quick Copy"), JOB_STORAGE_TYPE_QUICK_COPY)
            self.JobStorageModeComboBox.addItem(self.__tr("Stored Job"), JOB_STORAGE_TYPE_STORE)

            self.JobStorageModeComboBox.activated[int].connect( self.JobStorageModeComboBox_activated)

            self.JobStorageModeDefaultButton.clicked.connect( self.JobStorageModeDefaultButton_clicked)


        elif typ == cups.UI_JOB_STORAGE_PIN:
            HBoxLayout = QHBoxLayout()
            HBoxLayout.setObjectName("HBoxLayout")

            OptionLabel = QLabel(self.widget)
            OptionLabel.setObjectName("OptionLabel")
            HBoxLayout.addWidget(OptionLabel)

            SpacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            HBoxLayout.addItem(SpacerItem)

            self.JobStoragePinGroupBox = QFrame(self.widget)

            gridlayout1 = QGridLayout(self.JobStoragePinGroupBox)
            self.JobStoragePinOffRadioButton = QRadioButton(self.JobStoragePinGroupBox)
            gridlayout1.addWidget(self.JobStoragePinOffRadioButton, 0, 0, 1, 1)

            self.JobStoragePinPrivateRadioButton = QRadioButton(self.JobStoragePinGroupBox)
            gridlayout1.addWidget(self.JobStoragePinPrivateRadioButton, 0, 1, 1, 1)

            self.JobStoragePinEdit = QLineEdit(self.JobStoragePinGroupBox)
            self.JobStoragePinEdit.setMaxLength(4)
            self.JobStoragePinEdit.setValidator(PinValidator(self.JobStoragePinEdit))
            gridlayout1.addWidget(self.JobStoragePinEdit, 0, 2, 1, 1)

            HBoxLayout.addWidget(self.JobStoragePinGroupBox)

            self.JobStoragePinDefaultButton = QPushButton(self.widget)
            HBoxLayout.addWidget(self.JobStoragePinDefaultButton)

            self.JobStoragePinOffRadioButton.setText(self.__tr("Public/Off"))
            self.JobStoragePinPrivateRadioButton.setText(self.__tr("Private/Use PIN:"))

            self.gridlayout.addLayout(HBoxLayout, self.row, 0, 1, 1)

            OptionLabel.setText(text)
            self.JobStoragePinDefaultButton.setText(self.__tr("Default"))

            self.JobStoragePinOffRadioButton.toggled[bool].connect( self.JobStoragePinOffRadioButton_toggled)

            self.JobStoragePinPrivateRadioButton.toggled[bool].connect( self.JobStoragePinPrivateRadioButton_toggled)

            self.JobStoragePinDefaultButton.clicked.connect( self.JobStoragePinDefaultButton_clicked)

            self.JobStoragePinEdit.textEdited["const QString &"].connect( self.JobStoragePinEdit_textEdited)


        elif typ == cups.UI_JOB_STORAGE_USERNAME:
            HBoxLayout = QHBoxLayout()
            HBoxLayout.setObjectName("HBoxLayout")

            OptionLabel = QLabel(self.widget)
            OptionLabel.setObjectName("OptionLabel")
            HBoxLayout.addWidget(OptionLabel)
            OptionLabel.setText(text)

            SpacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            HBoxLayout.addItem(SpacerItem)

            self.JobStorageUsernameGroupBox = QFrame(self.widget)

            gridlayout1 = QGridLayout(self.JobStorageUsernameGroupBox)
            self.JobStorageUsernameAutoRadioButton = QRadioButton(self.JobStorageUsernameGroupBox)
            gridlayout1.addWidget(self.JobStorageUsernameAutoRadioButton, 0, 0, 1, 1)

            self.JobStorageUsernameCustomRadioButton = QRadioButton(self.JobStorageUsernameGroupBox)
            gridlayout1.addWidget(self.JobStorageUsernameCustomRadioButton, 0, 1, 1, 1)

            self.JobStorageUsernameEdit = QLineEdit(self.JobStorageUsernameGroupBox)
            self.JobStorageUsernameEdit.setValidator(UsernameAndJobnameValidator(self.JobStorageUsernameEdit))
            self.JobStorageUsernameEdit.setMaxLength(16)
            gridlayout1.addWidget(self.JobStorageUsernameEdit, 0, 2, 1, 1)

            HBoxLayout.addWidget(self.JobStorageUsernameGroupBox)

            self.JobStorageUsernameDefaultButton = QPushButton(self.widget)
            HBoxLayout.addWidget(self.JobStorageUsernameDefaultButton)

            self.JobStorageUsernameAutoRadioButton.setText(self.__tr("Automatic"))
            self.JobStorageUsernameCustomRadioButton.setText(self.__tr("Custom:"))
            self.JobStorageUsernameDefaultButton.setText(self.__tr("Default"))

            self.JobStorageUsernameAutoRadioButton.toggled[bool].connect( self.JobStorageUsernameAutoRadioButton_toggled)

            self.JobStorageUsernameCustomRadioButton.toggled[bool].connect( self.JobStorageUsernameCustomRadioButton_toggled)

            self.JobStorageUsernameDefaultButton.clicked.connect( self.JobStorageUsernameDefaultButton_clicked)

            self.JobStorageUsernameEdit.textEdited["const QString &"].connect( self.JobStorageUsernameEdit_textEdited)

            self.gridlayout.addLayout(HBoxLayout, self.row, 0, 1, 1)

        elif typ == cups.UI_JOB_STORAGE_ID:
            HBoxLayout = QHBoxLayout()
            HBoxLayout.setObjectName("HBoxLayout")

            OptionLabel = QLabel(self.widget)
            OptionLabel.setObjectName("OptionLabel")
            HBoxLayout.addWidget(OptionLabel)
            OptionLabel.setText(text)

            SpacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            HBoxLayout.addItem(SpacerItem)

            self.JobStorageIDGroupBox = QFrame(self.widget)

            gridlayout1 = QGridLayout(self.JobStorageIDGroupBox)
            self.JobStorageIDAutoRadioButton = QRadioButton(self.JobStorageIDGroupBox)
            gridlayout1.addWidget(self.JobStorageIDAutoRadioButton, 0, 0, 1, 1)

            self.JobStorageIDCustomRadioButton = QRadioButton(self.JobStorageIDGroupBox)
            gridlayout1.addWidget(self.JobStorageIDCustomRadioButton, 0, 1, 1, 1)

            self.JobStorageIDEdit = QLineEdit(self.JobStorageIDGroupBox)
            self.JobStorageIDEdit.setValidator(UsernameAndJobnameValidator(self.JobStorageIDEdit))
            self.JobStorageIDEdit.setMaxLength(16)
            gridlayout1.addWidget(self.JobStorageIDEdit, 0, 2, 1, 1)

            HBoxLayout.addWidget(self.JobStorageIDGroupBox)

            self.JobStorageIDDefaultButton = QPushButton(self.widget)
            HBoxLayout.addWidget(self.JobStorageIDDefaultButton)

            self.JobStorageIDAutoRadioButton.setText(self.__tr("Automatic"))
            self.JobStorageIDCustomRadioButton.setText(self.__tr("Custom:"))
            self.JobStorageIDDefaultButton.setText(self.__tr("Default"))

            self.JobStorageIDAutoRadioButton.toggled[bool].connect( self.JobStorageIDAutoRadioButton_toggled)

            self.JobStorageIDCustomRadioButton.toggled[bool].connect( self.JobStorageIDCustomRadioButton_toggled)

            self.JobStorageIDDefaultButton.clicked.connect( self.JobStorageIDDefaultButton_clicked)

            self.JobStorageIDEdit.textEdited["const QString &"].connect( self.JobStorageIDEdit_textEdited)

            self.gridlayout.addLayout(HBoxLayout, self.row, 0, 1, 1)

        elif typ == cups.UI_JOB_STORAGE_ID_EXISTS:
            HBoxLayout = QHBoxLayout()
            HBoxLayout.setObjectName("HBoxLayout")

            OptionLabel = QLabel(self.widget)
            OptionLabel.setObjectName("OptionLabel")
            HBoxLayout.addWidget(OptionLabel)
            OptionLabel.setText(text)

            SpacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            HBoxLayout.addItem(SpacerItem)

            self.JobStorageExistingComboBox = QComboBox(self.widget)
            HBoxLayout.addWidget(self.JobStorageExistingComboBox)

            self.JobStorageExistingDefaultButton = QPushButton(self.widget)
            HBoxLayout.addWidget(self.JobStorageExistingDefaultButton)

            self.JobStorageExistingComboBox.addItem(self.__tr("Replace existing job"),
                             JOB_STORAGE_EXISTING_JOB_REPLACE)

            self.JobStorageExistingComboBox.addItem(self.__tr("Use job name appended with 1-99"),
                             JOB_STORAGE_EXISTING_JOB_APPEND_1_99)

            self.JobStorageExistingDefaultButton.setText(self.__tr("Default"))

            self.gridlayout.addLayout(HBoxLayout, self.row, 0, 1, 1)

            self.JobStorageExistingComboBox.activated[int].connect( self.JobStorageExistingComboBox_activated)

            self.JobStorageExistingDefaultButton.clicked.connect( self.JobStorageExistingDefaultButton_clicked)
                        
        elif typ == cups.UI_INFO:
            HBoxLayout = QHBoxLayout()
            HBoxLayout.setObjectName("HBoxLayout")

            OptionName = QLabel(self.widget)
            OptionName.setObjectName("OptionLabel")
            HBoxLayout.addWidget(OptionName)
            OptionName.setText(text)

            SpacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            HBoxLayout.addItem(SpacerItem)
            
            if text == 'Print Quality':
                self.PQValueLabel = QLabel(self.widget)
                self.PQValueLabel.setObjectName("PQValueLabel")
                HBoxLayout.addWidget(self.PQValueLabel)
                self.PQValueLabel.setText(value)
            elif text == 'Color Input / Black Render':
                self.PQColorInputLabel = QLabel(self.widget)
                self.PQColorInputLabel.setObjectName("PQColorInputLabel")
                HBoxLayout.addWidget(self.PQColorInputLabel)
                self.PQColorInputLabel.setText(value)
            else:
                OptionValue = QLabel(self.widget)
                OptionValue.setObjectName("OptionValue")
                HBoxLayout.addWidget(OptionValue)
                OptionValue.setText(value)
                
            self.gridlayout.addLayout(HBoxLayout, self.row, 0, 1, 1)

        else:
            log.error("Invalid UI value: %s/%s" % (self.group, option))

        self.row += 1



    def BannerComboBox_activated(self, a): # cups.UI_BANNER_JOB_SHEETS
        a = to_unicode(a)
        sender = self.sender()
        choice = None

        start, end = None, None
        for c, t in sender.choices:
            if t == a:
                start = c
                break

        for c, t in sender.other.choices:
            if t == sender.other.currentText():
                end = c
                break

        if sender.option == 'end':
            start, end = end, start

        if start is not None and \
            end is not None and \
            start.lower() == sender.default[0].lower() and \
            end.lower() == sender.default[1].lower():
                self.removePrinterOption('job-sheets')
                sender.pushbutton.setEnabled(False)
        else:
            sender.pushbutton.setEnabled(True)

            if start is not None and \
                end is not None:

                self.setPrinterOption('job-sheets', ','.join([start, end]))


    def ComboBox_highlighted(self, t):
        t = to_unicode(t)
        sender = self.sender()
        choice = None

        #print sender, sender.option, sender.job_option

        choice = None
        for c, a in sender.choices:
            if a == t:
                choice = c
                break

        if choice is not None and choice == sender.default:
            if sender.job_option:
                self.job_options[sender.option] = sender.default
            else:
                self.removePrinterOption(sender.option)
            sender.pushbutton.setEnabled(False)

        else:
            sender.pushbutton.setEnabled(True)

            if choice is not None:
                if sender.job_option:
                    self.job_options[sender.option] = choice
                else:
                    self.setPrinterOption(sender.option, choice)

            #self.linkPrintoutModeAndQuality(sender.option, choice)

    if 0:
        pass
        #    def linkPrintoutModeAndQuality(self, option, choice):
        #        if option.lower() == 'quality' and \
        #            choice is not None:
        #
        #            try:
        #                c = self.items['o:PrintoutMode'].control
        #            except KeyError:
        #                return
        #            else:
        #                if c is not None:
        #                    if choice.lower() == 'fromprintoutmode':
        #                        # from printoutmode selected
        #                        # determine printoutmode option combo enable state
        #                        c.setEnabled(True)
        #                        QToolTip.remove(c)
        #                        a = unicode(c.currentText())
        #
        #                        # determine printoutmode default button state
        #                        link_choice = None
        #                        for x, t in c.choices:
        #                            if t == a:
        #                                link_choice = x
        #                                break
        #
        #                        if link_choice is not None and \
        #                            link_choice.lower() == c.default.lower():
        #
        #                            c.pushbutton.setEnabled(False)
        #                        else:
        #                            c.pushbutton.setEnabled(True)
        #
        #                    else: # fromprintoutmode not selected, disable printoutmode
        #                        c.setEnabled(False)
        #                        QToolTip.add(c, self.__tr("""Set Quality to "Controlled by 'Printout Mode'" to enable."""))
        #                        c.pushbutton.setEnabled(False)
        #

    def SpinBox_valueChanged(self, i): # cups.UI_SPINNER
        sender = self.sender()
        if sender.option == "HPDigit":
           self.pin_count = 1
        if not sender.job_option:
            if i == sender.default:
                self.removePrinterOption(sender.option)
                sender.pushbutton.setEnabled(False)
                if sender.option == "HPDigit":
                   self.pin_count = 0
            else:
                sender.pushbutton.setEnabled(True)
                self.setPrinterOption(sender.option, str(i))

        else:
            try:
                self.job_options[sender.option] = int(i)
            except ValueError:
                self.job_options[sender.option] = sender.default


    def BoolRadioButtons_clicked(self, b): # cups.PPD_UI_BOOLEAN
        sender = self.sender()
        b = int(b)
        if sender.default == True or sender.default == "True" or sender.default == "true":
            sender.default = int(True)
        else:
            sender.default = int(False)

        if b == sender.default:
            self.removePrinterOption(sender.option)
            sender.pushbutton.setEnabled(False)
        else:
            sender.pushbutton.setEnabled(True)

            if b:
                self.setPrinterOption(sender.option, "true")
            else:
                self.setPrinterOption(sender.option, "false")

    def ComboBox_indexChanged(self, currentItem):
        sender = self.sender()
        currentItem = to_unicode(currentItem)
        # Checking for summary control
        labelPQValaue = getattr(self, 'PQValueLabel', None)
        labelPQColorInput = getattr(self, 'PQColorInputLabel', None)
        # When output mode combo item is changed, we need to update the summary information      
        if currentItem is not None and sender.option == 'OutputMode' and labelPQValaue is not None and labelPQColorInput is not None:
            # Setting output mode
            self.PQValueLabel.setText(currentItem)
            
            # Getting DPI custom attributefrom the PPD
            # Setting color input
            quality_attr_name = "OutputModeDPI"
            cups.openPPD(self.cur_printer)
            outputmode_dpi = cups.findPPDAttribute(quality_attr_name, currentItem)
            log.debug("Outputmode changed, setting outputmode_dpi: %s" % outputmode_dpi)
            cups.closePPD()            
            self.PQColorInputLabel.setText(outputmode_dpi)
            
            log.debug("Outputmode changed, setting value outputmode: %s" % currentItem)            

    def DefaultButton_clicked(self):
        sender = self.sender()
        sender.setEnabled(False)

        if sender.typ == cups.PPD_UI_BOOLEAN: # () On  (*) Off
            if sender.default == True or sender.default == 'True' or sender.default == 'true': 
                sender.default = True
            else:
                sender.default = False
            if sender.default:
                sender.control[0].setChecked(True)
                sender.control[0].setFocus(Qt.OtherFocusReason)
            else:
                sender.control[1].setChecked(True)
                sender.control[1].setFocus(Qt.OtherFocusReason)

            if not sender.job_option:
                self.removePrinterOption(sender.option)

        elif sender.typ == cups.PPD_UI_PICKONE: # [     \/]
            choice, text = None, None

            for c, t in sender.choices:
                if c == sender.default:
                    choice = c
                    text = t
                    self.job_options[sender.option] = t
                    break

            if choice is not None:
                if not sender.job_option:
                    self.removePrinterOption(sender.option)
                index = sender.control.findText(text)
                sender.control.setCurrentIndex(index)

                #self.linkPrintoutModeAndQuality(sender.option, choice) # TODO:
                sender.control.setFocus(Qt.OtherFocusReason)

        elif sender.typ == cups.UI_SPINNER: # [ x /\|\/]
            sender.control.setValue(sender.default)
            if not sender.job_option:
                self.removePrinterOption(sender.option)

            sender.control.setFocus(Qt.OtherFocusReason)

        elif sender.typ == cups.UI_BANNER_JOB_SHEETS: # start: [     \/]  end: [     \/]
            start, end, start_text, end_text = None, None, None, None
            for c, t in sender.choices:
                if c == sender.default[0]:
                    start = c
                    start_text = t

                if c == sender.default[1]:
                    end = c
                    end_text = t

            if start is not None:
                index = sender.control[0].findText(start_text)
                sender.control[0].setCurrentIndex(index)

            if end is not None:
                index = sender.control[1].findText(end_text)
                sender.control[1].setCurrentIndex(index)

            if not sender.job_option:
                self.removePrinterOption('job-sheets')

            sender.control[0].setFocus(Qt.OtherFocusReason)

        elif sender.typ == cups.UI_PAGE_RANGE: # (*) All () Pages: [    ]
            sender.control[0].setChecked(True) # all radio button
            sender.control[0].setFocus(Qt.OtherFocusReason)
            sender.control[2].setEnabled(False) # range edit box


    def PageRangeAllRadio_toggled(self, b):
        if b:
            sender = self.sender()
            sender.edit_control.setEnabled(False)
            sender.pushbutton.setEnabled(False)
            self.job_options['pagerange'] = ''


    def PageRangeRangeRadio_toggled(self, b):
        if b:
            sender = self.sender()
            sender.pushbutton.setEnabled(True)
            sender.edit_control.setEnabled(True)
            self.job_options['pagerange'] = to_unicode(sender.edit_control.text())


    def PageRangeEdit_editingFinished(self):
        sender = self.sender()
        t, ok, x = self.job_options['pagerange'], True, []


        try:
            x = utils.expand_range(t)   
        except ValueError:
            ok = False

        if ok:
            for y in x:
                if y <= 0  or y > 999:
                    ok = False
                    break

        if not ok:
            self.job_options['pagerange'] = ''
            log.error("Invalid page range: %s" % t)
            FailureUI(self, self.__tr("<b>Invalid page range.</b><p>Please enter a range using page numbers (1-999), dashes, and commas. For example: 1-2,3,5-7</p>"))
            sender.setFocus(Qt.OtherFocusReason)


    def PageRangeEdit_textChanged(self, t):
        self.job_options['pagerange'] = to_unicode(t) # Do range validation only in PageRangeEdit_editingFinished method

    #
    # Job Storage
    #

    def updateJobStorageControls(self):
        beginWaitCursor()
        try:
            # Mode
            self.JobStorageModeComboBox.setCurrentIndex(self.JobStorageModeComboBox.findData(self.job_storage_mode))
            self.JobStorageModeDefaultButton.setEnabled(self.job_storage_mode != JOB_STORAGE_TYPE_OFF)

            # PIN
            self.JobStoragePinPrivateRadioButton.setChecked(self.job_storage_use_pin)

            # Username
            self.JobStorageUsernameAutoRadioButton.setChecked(self.job_storage_auto_username)

            # Jobname/ID
            self.JobStorageIDAutoRadioButton.setChecked(self.job_storage_auto_jobname)

            # Dup/existing ID
            self.JobStorageExistingComboBox.setCurrentIndex(self.JobStorageExistingComboBox.findData(self.job_storage_job_exist))

            if self.job_storage_mode == JOB_STORAGE_TYPE_OFF:
                # PIN
                self.JobStoragePinGroupBox.setEnabled(False)
                self.JobStoragePinEdit.setEnabled(False)
                self.JobStoragePinDefaultButton.setEnabled(False)
                self.JobStoragePinEdit.setText(str())

                # Username
                self.JobStorageUsernameGroupBox.setEnabled(False)
                self.JobStorageUsernameEdit.setEnabled(False)
                self.JobStorageUsernameDefaultButton.setEnabled(False)

                # Jobname/ID
                self.JobStorageIDGroupBox.setEnabled(False)
                self.JobStorageIDEdit.setEnabled(False)
                self.JobStorageIDDefaultButton.setEnabled(False)

                # Duplicate/existing Jobname/ID
                self.JobStorageExistingComboBox.setEnabled(False)

            else:
                # PIN
                if self.job_storage_mode in (JOB_STORAGE_TYPE_PERSONAL, JOB_STORAGE_TYPE_STORE):
                    self.JobStoragePinGroupBox.setEnabled(True)
                    self.JobStoragePinDefaultButton.setEnabled(self.job_storage_use_pin)
                    self.JobStoragePinEdit.setEnabled(self.job_storage_use_pin)
                    self.JobStoragePinEdit.setText(str(self.job_storage_pin))
                else:
                    self.JobStoragePinGroupBox.setEnabled(False)
                    self.JobStoragePinEdit.setEnabled(False)
                    self.JobStoragePinDefaultButton.setEnabled(False)
                    self.JobStoragePinEdit.setText(str())

                # Username
                self.JobStorageUsernameGroupBox.setEnabled(True)
                self.JobStorageUsernameEdit.setEnabled(not self.job_storage_auto_username)
                self.JobStorageUsernameDefaultButton.setEnabled(not self.job_storage_auto_username)
                self.JobStorageUsernameEdit.setText(str(self.job_storage_username))

                # Jobname/ID
                self.JobStorageIDGroupBox.setEnabled(True)
                self.JobStorageIDEdit.setEnabled(not self.job_storage_auto_jobname)
                self.JobStorageIDDefaultButton.setEnabled(not self.job_storage_auto_jobname)
                self.JobStorageIDEdit.setText(str(self.job_storage_jobname))

                # Duplicate/existing JobName/ID
                self.JobStorageExistingComboBox.setEnabled(not self.job_storage_auto_jobname)
                self.JobStorageExistingDefaultButton.setEnabled(not self.job_storage_auto_jobname and self.job_storage_job_exist != JOB_STORAGE_EXISTING_JOB_REPLACE)

        finally:
            endWaitCursor()


    def saveJobStorageOptions(self):
        beginWaitCursor()
        try:
            log.debug("Saving job storage options...")

            if self.job_storage_mode == JOB_STORAGE_TYPE_OFF:
                log.debug("Job storage mode = JOB_STORAGE_TYPE_OFF")
                self.setPrinterOption('HOLD', 'OFF')
                self.removePrinterOption('HOLDTYPE')
                self.removePrinterOption('USERNAME')
                self.removePrinterOption('JOBNAME')
                self.removePrinterOption('DUPLICATEJOB')

            elif self.job_storage_mode == JOB_STORAGE_TYPE_PROOF_AND_HOLD:
                log.debug("Job storage mode = JOB_STORAGE_TYPE_PROOF_AND_HOLD")
                self.setPrinterOption('HOLD', 'PROOF')
                #self.removePrinterOption('HOLDTYPE')
                self.setPrinterOption('HOLDTYPE', 'PUBLIC')

            elif self.job_storage_mode == JOB_STORAGE_TYPE_PERSONAL:
                log.debug("Job storage mode = JOB_STORAGE_TYPE_PERSONAL")

                if self.job_storage_use_pin:
                    self.setPrinterOption('HOLD', 'ON')
                else:
                    self.setPrinterOption('HOLD', 'PROOF')
                    self.setPrinterOption('HOLDTYPE', 'PUBLIC')


            elif self.job_storage_mode == JOB_STORAGE_TYPE_QUICK_COPY:
                log.debug("Job storage mode = JOB_STORAGE_TYPE_QUICK_COPY")
                self.setPrinterOption('HOLD', 'ON')
                self.setPrinterOption('HOLDTYPE', 'PUBLIC')

            elif self.job_storage_mode == JOB_STORAGE_TYPE_STORE:
                log.debug("Job storage mode = JOB_STORAGE_TYPE_STORE")
                self.setPrinterOption('HOLD', 'STORE')

                if not self.job_storage_use_pin:
                    self.removePrinterOption('HOLDTYPE')

            # PIN
            log.debug("Job storage use pin = %d" % self.job_storage_use_pin)
            if self.job_storage_use_pin:
                self.setPrinterOption('HOLDTYPE', 'PRIVATE')

            #else:
            #    self.removePrinterOption('HOLDKEY')

            # Dup/exisiting
            if self.job_storage_job_exist == JOB_STORAGE_EXISTING_JOB_REPLACE:
                log.debug("Job storage duplicate = JOB_STORAGE_EXISTING_JOB_REPLACE")
                self.setPrinterOption('DUPLICATEJOB', 'REPLACE')

            else: # JOB_STORAGE_EXISTING_JOB_APPEND_1_99
                log.debug("Job storage duplicate = JOB_STORAGE_EXISTING_JOB_APPEND_1_99")
                self.setPrinterOption('DUPLICATEJOB', 'APPEND')


        finally:
            endWaitCursor()


    #
    # Mode
    #

    def JobStorageModeComboBox_activated(self, i):
        sender = self.sender()
        mode, ok = value_int(sender.itemData(i))
        if ok:
            self.job_storage_mode = mode
            self.saveJobStorageOptions()
            self.updateJobStorageControls()


    def JobStorageModeDefaultButton_clicked(self):
        self.JobStorageModeComboBox.emit(SIGNAL("activated(int)"), JOB_STORAGE_TYPE_OFF)


    #
    # PIN
    #

    def JobStoragePinOffRadioButton_toggled(self, b):
        self.job_storage_use_pin = not b
        self.updateJobStorageControls()
        self.saveJobStorageOptions()


    def JobStoragePinPrivateRadioButton_toggled(self, b):
        self.job_storage_use_pin = b
        self.updateJobStorageControls()
        self.saveJobStorageOptions()


    def JobStoragePinDefaultButton_clicked(self):
        self.JobStoragePinOffRadioButton.emit(SIGNAL("toggled(bool)"), True)


    def JobStoragePinEdit_textEdited(self, s):
        self.job_storage_pin = to_unicode(s)
        self.setPrinterOption('HOLDKEY', self.job_storage_pin.encode('ascii'))



    #
    # Username
    #

    def JobStorageUsernameAutoRadioButton_toggled(self, b):
        self.job_storage_auto_username = b
        self.updateJobStorageControls()
        self.saveJobStorageOptions()


    def JobStorageUsernameCustomRadioButton_toggled(self, b):
        self.job_storage_auto_username = not b
        self.updateJobStorageControls()
        self.saveJobStorageOptions()


    def JobStorageUsernameDefaultButton_clicked(self):
        self.JobStorageUsernameAutoRadioButton.emit(SIGNAL("toggled(bool)"), True)


    def JobStorageUsernameEdit_textEdited(self, s):
        self.job_storage_username = to_unicode(s)
        self.setPrinterOption('USERNAME', self.job_storage_username.encode('ascii'))

    #
    # Jobname/ID
    #

    def JobStorageIDAutoRadioButton_toggled(self, b):
        self.job_storage_auto_jobname = b
        self.updateJobStorageControls()
        self.saveJobStorageOptions()


    def JobStorageIDCustomRadioButton_toggled(self, b):
        self.job_storage_auto_jobname = not b
        self.updateJobStorageControls()
        self.saveJobStorageOptions()


    def JobStorageIDDefaultButton_clicked(self):
        self.JobStorageIDAutoRadioButton.emit(SIGNAL("toggled(bool)"), True)


    def JobStorageIDEdit_textEdited(self, s):
        self.job_storage_jobname = to_unicode(s)
        self.setPrinterOption('JOBNAME', self.job_storage_jobname.encode('ascii'))

    #
    # Duplicate/existing Jobname/ID
    #

    def JobStorageExistingComboBox_activated(self, i):
        sender = self.sender()
        opt, ok = value_int(sender.itemData(i))
        if ok:
            self.job_storage_job_exist = opt
            self.updateJobStorageControls()
            self.saveJobStorageOptions()


    def JobStorageExistingDefaultButton_clicked(self):
        self.JobStorageExistingComboBox.emit(SIGNAL("activated(int)"), JOB_STORAGE_EXISTING_JOB_REPLACE)


    #
    # Printer I/O
    #

    def setPrinterOption(self, option, value):
        log.debug("setPrinterOption(%s, %s)" % (option, value))
        cups.openPPD(self.cur_printer)

        try:
            if option == "HPDigit":
               if len(value) == 1:
                  value = '000' + value
               if len(value) == 2:
                  value += '00' + value
               if len(value) == 3:
                  value += '0' + value
               if len(value) != 4:
                  value = value[-4:]
            cups.addOption("%s=%s" % (option, value))
            cups.setOptions()
        finally:
            cups.closePPD()

    def removePrinterOption(self, option):
        log.debug("removePrinterOption(%s)" % option)
        cups.openPPD(self.cur_printer)

        try:
            cups.removeOption(option)
            cups.setOptions()
        finally:
            cups.closePPD()


    def __tr(self,s,c = None):
        return qApp.translate("PrintSettingsToolbox",s,c)

