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
# Author: Don Welch
#

# Std Lib
import re
import os
import time

# Local
from base.g import *
from base.codes import *
from base import utils
from prnt import cups
from base.sixext import PY3, to_unicode


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
    # End
pat_html_remove = re.compile("(?is)<.*?>", re.I)

# databaseChanged signal values (for FABWindow)
FAB_NAME_ADD = 0  # s1 - new name
FAB_NAME_RENAME = 1 # s1 - old name, s2 - new name
FAB_NAME_REMOVE = 2 # s1 - removed name
FAB_NAME_DETAILS_CHANGED = 3 # s1 - name
FAB_GROUP_ADD = 4 # s1 - new group
FAB_GROUP_RENAME = 5 # s1 - old group, s2 - new group
FAB_GROUP_REMOVE = 6 # s1 - removed group
FAB_GROUP_MEMBERSHIP_CHANGED = 7 # s1 - group


def __translate(t):
    return QApplication.translate("ui_utils", t, None)


def beginWaitCursor():
    QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))


def endWaitCursor():
    QApplication.restoreOverrideCursor()


# TODO: Cache pixmaps
def load_pixmap(name, subdir=None, resize_to=None):
    name = ''.join([os.path.splitext(name)[0], '.png'])

    if subdir is None:
        image_dir = prop.image_dir
        ldir = os.path.join(os.getcwd(), 'data', 'images')
    else:
        image_dir = os.path.join(prop.image_dir, subdir)
        ldir = os.path.join(os.getcwd(), 'data', 'images', subdir)

    for d in [image_dir, ldir]:
        f = os.path.join(d, name)
        if os.path.exists(f):
            if resize_to is not None:
                img = QImage(f)
                x, y = resize_to
                return QPixmap.fromImage(img.scaled(x, y, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
            else:
                return QPixmap(f)

        for w in utils.walkFiles(image_dir, recurse=True, abs_paths=True, return_folders=False, pattern=name):
            if resize_to is not None:
                img = QImage(w)
                x, y = resize_to
                return QPixmap.fromImage(img.scaled(x, y, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
            else:
                return QPixmap(w)

    log.error("Pixmap '%s' not found!" % name)
    return QPixmap()

loadPixmap = load_pixmap


def getPynotifyIcon(name, subdir='32x32'):
    name = ''.join([os.path.splitext(name)[0], '.png'])
    return "file://" + os.path.join(prop.image_dir, subdir, name)


def value_str(data):
    if data is None:
        return ""
    try:
        if not PY3:
            try:
                data = data.toString()
            except AttributeError as e:
                return data
    except(ValueError, TypeError) as e:
        log.warn("value_str() Failed to convert data: %s" % e)
        
    return data


def value_int(data):
    i, ok = 0, False
    if data is None:
        return i, ok
    try:
        if PY3:
            i =  int(data)
            ok = True
        else:
            try:
                i, ok = data.toInt()
            except AttributeError as e:
                i = int(data)
                ok = True
    except (ValueError,TypeError) as e:
        log.warn("value_int() Failed to convert data[%s]:%s  "%(data,e))

    return i, ok


def value_bool( data ):
    b = False
    if data is None:
        return b
    try:
        if PY3:
            if type(data) == str and data.lower() in ['false', '0']:
                b = False
            elif data in [False, 0]:
                b = False
            else:
                b= True
        else:
            try:
                b = data.toBool()
            except AttributeError as e:
                if type(data) == str and data.lower() in ['false', '0']:
                    b = False
                elif data in [False, 0]:
                    b = False
                else:
                    b= True

    except (ValueError,TypeError) as e:
        log.warn("value_bool() Failed to convert data :%s"%e)

    return b



class UserSettings(QSettings):
    def __init__(self):
        if prop.user_dir is None:
            QSettings.__init__(self)
        else:
            QSettings.__init__(self, os.path.join(prop.user_dir,  'hplip.conf'),  QSettings.IniFormat)

        self.systray_visible = SYSTRAY_VISIBLE_SHOW_ALWAYS
        self.systray_messages = SYSTRAY_MESSAGES_SHOW_ALL
        self.last_used_device_uri = ''
        self.last_used_printer = ''
        self.version = ''
        self.date_time = ''
        self.auto_refresh = False
        self.auto_refresh_rate = 30
        self.auto_refresh_type = 1
        self.polling_interval = 5
        self.polling = True
        self.device_list = []
        self.working_dir = '.'
        self.voice_phone = ''
        self.email_address = ''
        self.upgrade_notify=True
        self.upgrade_last_update_time=0
        self.upgrade_pending_update_time=0
        self.latest_available_version=""
        self.loadDefaults()


    def __setup(self,  cmds):
        for c in cmds:
            basename = c.split()[0]
            path = utils.which(basename)
            if path:
                return ' '.join([os.path.join(path, basename), ' '.join(c.split()[1:])])

        return ''

    def loadDefaults(self):
        self.cmd_scan = self.__setup(['simple-scan %SANE_URI%', 'xsane -V %SANE_URI%', 'kooka', 'xscanimage'])
        self.cmd_fab = self.__setup(['hp-fab'])


    def load(self):
        log.debug("Loading user settings...")
        self.sync()

        self.beginGroup("settings")
        self.systray_visible = value_int(self.value("systray_visible"))[0]
        
        self.systray_messages = value_int(self.value("systray_messages"))[0]
 
        self.endGroup()

        self.beginGroup("last_used")
        self.last_used_device_uri = value_str(self.value("device_uri")) or self.last_used_device_uri
        self.last_used_printer = value_str(self.value("printer_name")) or self.last_used_printer
        self.working_dir = value_str(self.value("working_dir")) or self.working_dir
        self.endGroup()

        self.beginGroup("commands")
        self.cmd_scan = value_str(self.value("scan")) or self.cmd_scan
        self.endGroup()

        self.beginGroup("refresh")
        self.auto_refresh_rate = value_int(self.value("rate"))[0] or int(self.auto_refresh_rate)
        self.auto_refresh = value_bool(self.value("enable"))
        self.auto_refresh_type = value_int(self.value("type"))[0] or int(self.auto_refresh_type)
        self.endGroup()

        self.beginGroup("installation")
        self.version = value_str(self.value("version"))
        self.date_time = value_str(self.value("date_time"))
        self.endGroup()

        self.beginGroup("polling")
        self.polling = value_bool(self.value("enable"))
        self.polling_interval = value_int(self.value("interval"))[0] or int(self.polling_interval)
        self.polling_device_list = to_unicode(value_str(self.value("device_list"))).split(to_unicode(','))
        self.endGroup()

        self.beginGroup("fax")
        self.voice_phone = value_str(self.value("voice_phone"))
        self.email_address = to_unicode(value_str(self.value("email_address")))
        self.endGroup()
        
        self.beginGroup("upgrade")
        self.upgrade_notify= value_bool(self.value("notify_upgrade"))
        self.latest_available_version=value_str(self.value("latest_available_version"))
        
        self.upgrade_last_update_time = value_int(self.value("last_upgraded_time"))[0]
        
        self.upgrade_pending_update_time = value_int(self.value("pending_upgrade_time"))[0]
            
        self.endGroup()


    def save(self):
        log.debug("Saving user settings...")

        self.beginGroup("settings")
        self.setValue("systray_visible", self.systray_visible)
        self.setValue("systray_messages", self.systray_messages)
        self.endGroup()

        self.beginGroup("last_used")
        self.setValue("device_uri",  self.last_used_device_uri)
        self.setValue("printer_name", self.last_used_printer)
        self.setValue("working_dir", self.working_dir)
        self.endGroup()

        self.beginGroup("commands")
        self.setValue("scan",  self.cmd_scan)
        self.endGroup()

        self.beginGroup("refresh")
        self.setValue("rate", self.auto_refresh_rate)
        self.setValue("enable", self.auto_refresh)
        self.setValue("type", self.auto_refresh_type)
        self.endGroup()

        self.beginGroup("polling")
        self.setValue("enable", self.polling)
        self.setValue("interval", self.polling_interval)
        self.setValue("device_list", (to_unicode(',').join(self.polling_device_list)))
        self.endGroup()

        self.beginGroup("fax")
        self.setValue("voice_phone", self.voice_phone)
        self.setValue("email_address", self.email_address)
        self.endGroup()
        
        self.beginGroup("upgrade")
        self.setValue("notify_upgrade", self.upgrade_notify)
        if self.upgrade_last_update_time <1:
            self.upgrade_last_update_time = int(time.time())          # <---Need to verify code once
            
        self.setValue("last_upgraded_time", self.upgrade_last_update_time)
        self.setValue("pending_upgrade_time", self.upgrade_pending_update_time)
        self.endGroup()


        self.sync()


    def debug(self):
        log.debug("FAB command: %s" % self.cmd_fab)
        log.debug("Scan command: %s" % self.cmd_scan)
        log.debug("Auto refresh: %s" % self.auto_refresh)
        log.debug("Auto refresh rate: %s" % self.auto_refresh_rate)
        log.debug("Auto refresh type: %s" % self.auto_refresh_type)
        log.debug("Systray visible: %d" % self.systray_visible)
        log.debug("Systray messages: %d" % self.systray_messages)
        log.debug("Last used device URI: %s" % self.last_used_device_uri)
        log.debug("Last used printer: %s" % self.last_used_printer)
        log.debug("Working directory: %s" % self.working_dir)


DEFAULT_TITLE =  __translate("HP Device Manager")


def FailureUI(parent, error_text, title_text=None):
    log.error(pat_html_remove.sub(' ', to_unicode(error_text)))

    if title_text is None:
        if parent is not None:
            title_text = parent.windowTitle()
        else:
            title_text = DEFAULT_TITLE

    QMessageBox.critical(parent,
        title_text,
        error_text,
        QMessageBox.Ok|\
        QMessageBox.NoButton,
        QMessageBox.NoButton)

showFailureUi = FailureUI


def WarningUI(parent,  warn_text, title_text=None):
    log.warn(pat_html_remove.sub(' ', to_unicode(warn_text)))

    if title_text is None:
        if parent is not None:
            title_text = parent.windowTitle()
        else:
            title_text = DEFAULT_TITLE


    QMessageBox.warning(parent,
        title_text,
        warn_text,
        QMessageBox.Ok|\
        QMessageBox.NoButton,
        QMessageBox.NoButton)

showWarningUi = WarningUI


def SuccessUI(parent, text, title_text=None):
    log.info(pat_html_remove.sub(' ', to_unicode(text)))

    if title_text is None:
        if parent is not None:
            title_text = parent.windowTitle()
        else:
            title_text = DEFAULT_TITLE


    QMessageBox.information(parent,
        title_text,
        text,
        QMessageBox.Ok|\
        QMessageBox.NoButton,
        QMessageBox.NoButton)

showSuccessUi = SuccessUI


def CheckDeviceUI(parent, title_text=None):
    text = __translate("<b>Unable to communicate with device or device is in an error state.</b><p>Please check device setup and try again.</p>")
    return FailureUI(parent, text, title_text)

checkDeviceUi = CheckDeviceUI


class PrinterNameValidator(QValidator):
    def __init__(self, parent=None):
        QValidator.__init__(self, parent)

    def validate(self, input_data, pos):
        returnCode = QValidator.Invalid
        input_data = to_unicode(input_data)

        if not input_data:
            returnCode = QValidator.Acceptable
        elif input_data[pos-1] in cups.INVALID_PRINTER_NAME_CHARS:
            returnCode = QValidator.Invalid
        else:
            returnCode = QValidator.Acceptable

        # TODO: How to determine if unicode char is "printable" and acceptable
        # to CUPS?
        #elif input_data != utils.printable(input_data):
        #    return QValidator.Invalid, pos

        return returnCode, input_data, pos


class PhoneNumValidator(QValidator):
    def __init__(self, parent=None):
        QValidator.__init__(self, parent)

    def validate(self, input_data, pos):
        returnCode = QValidator.Invalid 
        input_data = to_unicode(input_data)

        if not input_data:
            returnCode =  QValidator.Acceptable
        elif input_data[pos-1] not in to_unicode('0123456789-(+).,#* '):
            returnCode = QValidator.Invalid
        else:
            returnCode = QValidator.Acceptable

        return returnCode, input_data, pos


class AddressBookNameValidator(QValidator):
    def __init__(self, db, parent=None):
        QValidator.__init__(self, parent)
        self.db = db

    def validate(self, input_data, pos):
        returnCode = QValidator.Invalid
        input_data = to_unicode(input_data)

        if not input_data:
            returnCode = QValidator.Acceptable
        elif input_data in self.db.get_all_names():
            returnCode = QValidator.Invalid
        elif input_data[pos-1] in to_unicode('''|\\/"'''): # | is the drag 'n drop separator
            returnCode = QValidator.Invalid
        else:
            returnCode = QValidator.Acceptable

        return returnCode, input_data, pos



MIME_TYPES_DESC = \
{
    "application/pdf" : (__translate("PDF Document"), '.pdf'),
    "application/postscript" : (__translate("Postscript Document"), '.ps'),
    "application/vnd.hp-HPGL" : (__translate("HP Graphics Language File"), '.hgl, .hpg, .plt, .prn'),
    "application/x-cshell" : (__translate("C Shell Script"), '.csh, .sh'),
    "application/x-csource" : (__translate("C Source Code"), '.c'),
    "text/cpp": (__translate("C/C++ Source Code"), '.c, .cpp, .cxx'),
    "application/x-perl" : (__translate("Perl Script"), '.pl'),
    "application/x-python" : (__translate("Python Program"), '.py'),
    "application/x-shell" : (__translate("Shell Script"), '.sh'),
    "application/x-sh" : (__translate("Shell Script"), '.sh'),
    "text/plain" : (__translate("Plain Text"), '.txt, .log'),
    "text/html" : (__translate("HTML Dcoument"), '.htm, .html'),
    "image/gif" : (__translate("GIF Image"), '.gif'),
    "image/png" : (__translate("PNG Image"), '.png'),
    "image/jpeg" : (__translate("JPEG Image"), '.jpg, .jpeg'),
    "image/tiff" : (__translate("TIFF Image"), '.tif, .tiff'),
    "image/x-bitmap" : (__translate("Bitmap (BMP) Image"), '.bmp'),
    "image/x-bmp" : (__translate("Bitmap (BMP) Image"), '.bmp'),
    "image/x-photocd" : (__translate("Photo CD Image"), '.pcd'),
    "image/x-portable-anymap" : (__translate("Portable Image (PNM)"), '.pnm'),
    "image/x-portable-bitmap" : (__translate("Portable B&W Image (PBM)"), '.pbm'),
    "image/x-portable-graymap" : (__translate("Portable Grayscale Image (PGM)"), '.pgm'),
    "image/x-portable-pixmap" : (__translate("Portable Color Image (PPM)"), '.ppm'),
    "image/x-sgi-rgb" : (__translate("SGI RGB"), '.rgb'),
    "image/x-xbitmap" : (__translate("X11 Bitmap (XBM)"), '.xbm'),
    "image/x-xpixmap" : (__translate("X11 Pixmap (XPM)"), '.xpm'),
    "image/x-sun-raster" : (__translate("Sun Raster Format"), '.ras'),
    "application/hplip-fax" : (__translate("HPLIP Fax File"), '.g3, .g4'),
}

# pixmaps for status list(s) (inkjet, laserjet)
status_icons = None

def getStatusListIcon(error_state):
    global status_icons
    if status_icons is None:
        status_icons = {
          ERROR_STATE_CLEAR : (load_pixmap('idle', '16x16'), load_pixmap('idle', '16x16')),
          ERROR_STATE_BUSY : (load_pixmap('busy', '16x16'), load_pixmap('busy', '16x16')),
          ERROR_STATE_ERROR : (load_pixmap('error', '16x16'), load_pixmap('error', '16x16')),
          ERROR_STATE_LOW_SUPPLIES : (load_pixmap('inkdrop', '16x16'), load_pixmap('toner', '16x16')),
          ERROR_STATE_OK : (load_pixmap('ok', '16x16'), load_pixmap('ok', '16x16')),
          ERROR_STATE_WARNING : (load_pixmap('warning', '16x16'), load_pixmap('warning', '16x16')),
          ERROR_STATE_LOW_PAPER: (load_pixmap('paper', '16x16'), load_pixmap('paper', '16x16')),
          ERROR_STATE_PRINTING : (load_pixmap("print", '16x16'), load_pixmap("print", '16x16')),
          ERROR_STATE_SCANNING : (load_pixmap("scan", '16x16'), load_pixmap("scan", '16x16')),
          ERROR_STATE_PHOTOCARD : (load_pixmap("pcard", '16x16'), load_pixmap("pcard", '16x16')),
          ERROR_STATE_FAXING : (load_pixmap("fax", '16x16'), load_pixmap("fax", '16x16')),
          ERROR_STATE_COPYING :  (load_pixmap("makecopies", '16x16'), load_pixmap("makecopies", '16x16')),
        }

    return status_icons.get(error_state, status_icons[ERROR_STATE_CLEAR])

# pixmaps for device icons (inkjet, laserjet)
overlay_icons = None

def getStatusOverlayIcon(error_state):
    global overlay_icons
    if overlay_icons is None:
        overlay_icons = {
            ERROR_STATE_CLEAR : (None, None),
            ERROR_STATE_BUSY : (load_pixmap('busy', '16x16'), load_pixmap('busy', '16x16')),
            ERROR_STATE_ERROR : (load_pixmap('error', '16x16'), load_pixmap('error', '16x16')),
            ERROR_STATE_LOW_SUPPLIES : (load_pixmap('inkdrop', '16x16'), load_pixmap('toner', '16x16')),
            ERROR_STATE_OK : (load_pixmap('ok', '16x16'), load_pixmap('ok', '16x16')),
            ERROR_STATE_WARNING : (load_pixmap('warning', '16x16'), load_pixmap('warning', '16x16')),
            ERROR_STATE_LOW_PAPER: (load_pixmap('paper', '16x16'), load_pixmap('paper', '16x16')),
            ERROR_STATE_PRINTING : (load_pixmap('busy', '16x16'), load_pixmap('busy', '16x16')),
            ERROR_STATE_SCANNING : (load_pixmap('busy', '16x16'), load_pixmap('busy', '16x16')),
            ERROR_STATE_PHOTOCARD : (load_pixmap('busy', '16x16'), load_pixmap('busy', '16x16')),
            ERROR_STATE_FAXING : (load_pixmap('busy', '16x16'), load_pixmap('busy', '16x16')),
            ERROR_STATE_COPYING : (load_pixmap('busy', '16x16'), load_pixmap('busy', '16x16')),
            ERROR_STATE_REFRESHING : (load_pixmap('refresh1', '16x16'), load_pixmap('refresh1', '16x16')),
        }

    return overlay_icons.get(error_state, overlay_icons[ERROR_STATE_CLEAR])


NUM_REPRS = {
      1 : __translate("one"),
      2 : __translate("two"),
      3 : __translate("three"),
      4 : __translate("four"),
      5 : __translate("five"),
      6 : __translate("six"),
      7 : __translate("seven"),
      8 : __translate("eight"),
      9 : __translate("nine"),
      10 : __translate("ten"),
      11 : __translate("eleven"),
      12 : __translate("twelve")
}

UNIT_NAMES = {
    "year" : (__translate("year"), __translate("years")),
    "month" : (__translate("month"), __translate("months")),
    "week" : (__translate("week"), __translate("weeks")),
    "day" : (__translate("day"), __translate("days")),
    "hour" : (__translate("hour"), __translate("hours")),
    "minute" : (__translate("minute"), __translate("minutes")),
    "second" : (__translate("second"), __translate("seconds")),
}


def getTimeDeltaDesc(past):
    t1 = QDateTime()
    t1.setTime_t(int(past))
    t2 = QDateTime.currentDateTime()
    delta = t1.secsTo(t2)
    return __translate("(%s ago)"%stringify(delta))


# "Nicely readable timedelta"
# Credit: Bjorn Lindqvist
# ASPN Python Recipe 498062
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/498062
# Note: Modified from recipe
def getSecondsInUnits(seconds):
    unit_limits = [("year", 31536000),
                   ("month", 2592000),
                   ("week", 604800),
                   ("day", 86400),
                   ("hour", 3600),
                   ("minute", 60)]

    for unit_name, limit in unit_limits:
        if seconds >= limit:
            amount = int(round(float(seconds) / limit))
            return amount, unit_name

    return seconds, "second"


def stringify(seconds):
    amount, unit_name = getSecondsInUnits(seconds)

    try:
        i18n_amount = NUM_REPRS[amount]
    except KeyError:
        i18n_amount = to_unicode(amount)

    if amount == 1:
        i18n_unit = UNIT_NAMES[unit_name][0]
    else:
        i18n_unit = UNIT_NAMES[unit_name][1]

    return "%s %s"%(i18n_amount, i18n_unit)
