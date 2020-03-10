# DistUpgradeViewKDE.py
#
#  Copyright (c) 2007 Canonical Ltd
#  Copyright (c) 2014-2018 Harald Sitter <sitter@kde.org>
#
#  Author: Jonathan Riddell <jriddell@ubuntu.com>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

try:
    # 14.04 has a broken pyqt5, so don't even try to import it and require
    # pyqt4.
    # In 14.04 various signals in pyqt5 can not be connected because it thinks
    # the signal does not exist or has an incompatible signature. Since this
    # potentially renders the GUI entirely broken and pyqt5 was not actively
    # used back then it is fair to simply require qt4 on trusty systems.
    from .utils import get_dist
    if get_dist() == 'trusty':
        raise ImportError

    from PyQt5 import uic
    from PyQt5.QtCore import Qt, QLocale, QTranslator, PYQT_VERSION, QTimer
    from PyQt5.QtWidgets import QTextEdit, QApplication, QDialog,\
        QMessageBox, QDialogButtonBox, QTreeWidgetItem, QPushButton, QWidget,\
        QHBoxLayout, QLabel
    from PyQt5.QtGui import QTextOption, QPixmap, QIcon, QTextCursor
    from PyQt5.QtDBus import QDBusConnection, QDBusInterface, QDBusReply
except ImportError:
    from PyQt4 import uic
    from PyQt4.QtCore import Qt, QLocale, QTranslator, PYQT_VERSION, QTimer
    from PyQt4.QtGui import QTextEdit, QDialog, QTextOption, QApplication,\
        QMessageBox, QDialogButtonBox, QTreeWidgetItem, QPixmap, QIcon,\
        QPushButton, QWidget, QTextCursor, QHBoxLayout, QLabel
    # If we still throw an exception, bounce back to Main to try another UI.

import atexit
import sys
import locale
import logging
import time
import subprocess
import traceback

import apt
import apt_pkg
import shlex # for osrelease
import os

import pty

from .DistUpgradeApport import run_apport, apport_crash

from .DistUpgradeView import DistUpgradeView, FuzzyTimeToStr, InstallProgress, AcquireProgress
from .telemetry import get as get_telemetry

import select
import gettext
from .DistUpgradeGettext import gettext as _
from .DistUpgradeGettext import unicode_gettext

from .QUrlOpener import QUrlOpener

# FIXME: what's the purpose?
def utf8(s, errors="strict"):
    if isinstance(s, bytes):
        return s.decode("UTF-8", errors)
    else:
        return s

# FIXME: what's the purpose?
def loadUi(file, parent):
    if os.path.exists(file):
        uic.loadUi(file, parent)
    else:
        #FIXME find file
        print("error, can't find file: " + file)

def _find_pixmap(path):
    if os.path.exists(path):
        return QPixmap(path)
    return None

def _icon(name, fallbacks = []):
    if type(PYQT_VERSION) == int:
        return QIcon.fromTheme(name)
    else:
        for path in fallbacks:
            pixmap = _find_pixmap(path)
            if pixmap:
                return QIcon(pixmap)
    return None

# QWidget adjustSize when run on a maximized window will make Qt 5.9, earlier,
# and probably also later, lose its state. Qt will think the window is no longer
# maximized, while in fact it is. This results in parts of the window no longer
# getting redrawn as the window manager will think it maximized but Qt thinks it
# is not and thus not send repaints for the regions it thinks do not exist.
# To prevent this from happening monkey patch adjustSize to not ever run on
# maximized windows.
def adjustSize(self):
    if not self.isMaximized():
        self.origAdjustSize(self)
QWidget.origAdjustSize = QWidget.adjustSize
QWidget.adjustSize = adjustSize

class _OSRelease:
    DEFAULT_OS_RELEASE_FILE = '/etc/os-release'
    OS_RELEASE_FILE = '/etc/os-release'

    def __init__(self, lsb_compat=True):
        self.result = {}
        self.valid = False
        self.file = _OSRelease.OS_RELEASE_FILE

        if not os.path.isfile(self.file):
            return

        self.parse()
        self.valid = True

        if lsb_compat:
            self.inject_lsb_compat()

    def inject_lsb_compat(self):
        self.result['Distributor ID'] = self.result['ID']
        self.result['Description'] = self.result['PRETTY_NAME']
        # Optionals as per os-release spec.
        self.result['Codename'] = self.result.get('VERSION_CODENAME')
        if not self.result['Codename']:
            # Transient Ubuntu 16.04 field (LP: #1598212)
            self.result['Codename'] = self.result.get('UBUNTU_CODENAME')
        self.result['Release'] = self.result.get('VERSION_ID')

    def parse(self):
        f = open(self.file, 'r')
        for line in f:
            line = line.strip()
            if not line:
                continue
            self.parse_entry(*line.split('=', 1))
        f.close()

    def parse_entry(self, key, value):
        value = self.parse_value(value) # Values can be shell strings...
        if key == "ID_LIKE" and isinstance(value, str):
            # ID_LIKE is specified as quoted space-separated list. This will
            # be parsed as string that we need to split manually.
            value = value.split(' ')
        self.result[key] = value

    def parse_value(self, value):
        values = shlex.split(value)
        if len(values) == 1:
            return values[0]
        return values


class DumbTerminal(QTextEdit):
    """ A very dumb terminal """
    def __init__(self, installProgress, parent_frame):
        " really dumb terminal with simple editing support "
        QTextEdit.__init__(self, "", parent_frame)
        self.installProgress = installProgress
        self.setFontFamily("Monospace")
        # FIXME: fixed font size set!!!
        self.setFontPointSize(8)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.setUndoRedoEnabled(False)
        self.setOverwriteMode(True)
        self._block = False
        #self.connect(self, SIGNAL("cursorPositionChanged()"),
        #             self.onCursorPositionChanged)

    def fork(self):
        """pty voodoo"""
        (self.child_pid, self.installProgress.master_fd) = pty.fork()
        if self.child_pid == 0:
            os.environ["TERM"] = "dumb"
        return self.child_pid

    def update_interface(self):
        (rlist, wlist, xlist) = select.select([self.installProgress.master_fd],[],[], 0)
        if len(rlist) > 0:
            line = os.read(self.installProgress.master_fd, 255)
            self.insertWithTermCodes(utf8(line))
        QApplication.processEvents()

    def insertWithTermCodes(self, text):
        """ support basic terminal codes """
        display_text = ""
        for c in text:
            # \b - backspace - this seems to comes as "^H" now ??!
            if ord(c) == 8:
                self.insertPlainText(display_text)
                self.textCursor().deletePreviousChar()
                display_text=""
            # \r - is filtered out
            elif c == chr(13):
                pass
            # \a - bell - ignore for now
            elif c == chr(7):
                pass
            else:
                display_text += c
        self.insertPlainText(display_text)

    def keyPressEvent(self, ev):
        """ send (ascii) key events to the pty """
        # no master_fd yet
        if not hasattr(self.installProgress, "master_fd"):
            return
        # special handling for backspace
        if ev.key() == Qt.Key_Backspace:
            #print("sent backspace")
            os.write(self.installProgress.master_fd, chr(8))
            return
        # do nothing for events like "shift"
        if not ev.text():
            return
        # now sent the key event to the termianl as utf-8
        os.write(self.installProgress.master_fd, ev.text().toUtf8())

    def onCursorPositionChanged(self):
        """ helper that ensures that the cursor is always at the end """
        if self._block:
            return
        # block signals so that we do not run into a recursion
        self._block = True
        self.moveCursor(QTextCursor.End)
        self._block = False


class KDECdromProgressAdapter(apt.progress.base.CdromProgress):
    """ Report the cdrom add progress """
    def __init__(self, parent):
        self.status = parent.window_main.label_status
        self.progressbar = parent.window_main.progressbar_cache
        self.parent = parent

    def update(self, text, step):
        """ update is called regularly so that the gui can be redrawn """
        if text:
          self.status.setText(text)
        self.progressbar.setValue(step.value/float(self.totalSteps))
        QApplication.processEvents()

    def ask_cdrom_name(self):
        return (False, "")

    def change_cdrom(self):
        return False


class KDEOpProgress(apt.progress.base.OpProgress):
  """ methods on the progress bar """
  def __init__(self, progressbar, progressbar_label):
      self.progressbar = progressbar
      self.progressbar_label = progressbar_label
      #self.progressbar.set_pulse_step(0.01)
      #self.progressbar.pulse()

  def update(self, percent=None):
      super(KDEOpProgress, self).update(percent)
      #if self.percent > 99:
      #    self.progressbar.set_fraction(1)
      #else:
      #    self.progressbar.pulse()
      #self.progressbar.set_fraction(self.percent/100.0)
      self.progressbar.setValue(self.percent)
      QApplication.processEvents()

  def done(self):
      self.progressbar_label.setText("")


class KDEAcquireProgressAdapter(AcquireProgress):
    """ methods for updating the progress bar while fetching packages """
    # FIXME: we really should have some sort of "we are at step"
    # xy in the gui
    # FIXME2: we need to thing about mediaCheck here too
    def __init__(self, parent):
        AcquireProgress.__init__(self)
        # if this is set to false the download will cancel
        self.status = parent.window_main.label_status
        self.progress = parent.window_main.progressbar_cache
        self.parent = parent

    def media_change(self, medium, drive):
      msg = _("Please insert '%s' into the drive '%s'") % (medium,drive)
      change = QMessageBox.question(self.parent.window_main, _("Media Change"), msg, QMessageBox.Ok, QMessageBox.Cancel)
      if change == QMessageBox.Ok:
        return True
      return False

    def start(self):
        AcquireProgress.start(self)
        #self.progress.show()
        self.progress.setValue(0)
        self.status.show()

    def stop(self):
        self.parent.window_main.progress_text.setText("  ")
        self.status.setText(_("Fetching is complete"))

    def pulse(self, owner):
        """ we don't have a mainloop in this application, we just call processEvents here and elsewhere"""
        # FIXME: move the status_str and progress_str into python-apt
        # (python-apt need i18n first for this)
        AcquireProgress.pulse(self, owner)
        self.progress.setValue(self.percent)
        current_item = self.current_items + 1
        if current_item > self.total_items:
            current_item = self.total_items

        if self.current_cps > 0:
            current_cps = apt_pkg.size_to_str(self.current_cps)
            if isinstance(current_cps, bytes):
                current_cps = current_cps.decode(locale.getpreferredencoding())
            self.status.setText(_("Fetching file %li of %li at %sB/s") % (current_item, self.total_items, current_cps))
            self.parent.window_main.progress_text.setText("<i>" + _("About %s remaining") % FuzzyTimeToStr(self.eta) + "</i>")
        else:
            self.status.setText(_("Fetching file %li of %li") % (current_item, self.total_items))
            self.parent.window_main.progress_text.setText("  ")

        QApplication.processEvents()
        return True


class KDEInstallProgressAdapter(InstallProgress):
    """methods for updating the progress bar while installing packages"""
    # timeout with no status change when the terminal is expanded
    # automatically
    TIMEOUT_TERMINAL_ACTIVITY = 240

    def __init__(self,parent):
        InstallProgress.__init__(self)
        self._cache = None
        self.label_status = parent.window_main.label_status
        self.progress = parent.window_main.progressbar_cache
        self.progress_text = parent.window_main.progress_text
        self.parent = parent
        try:
            self._terminal_log = open("/var/log/dist-upgrade/term.log","wb")
        except Exception as e:
            # if something goes wrong (permission denied etc), use stdout
            logging.error("Can not open terminal log: '%s'" % e)
            if sys.version >= '3':
                self._terminal_log = sys.stdout.buffer
            else:
                self._terminal_log = sys.stdout
        # some options for dpkg to make it die less easily
        apt_pkg.config.set("DPkg::StopOnError","False")

    def start_update(self):
        InstallProgress.start_update(self)
        self.finished = False
        # FIXME: add support for the timeout
        # of the terminal (to display something useful then)
        # -> longer term, move this code into python-apt
        self.label_status.setText(_("Applying changes"))
        self.progress.setValue(0)
        self.progress_text.setText(" ")
        # do a bit of time-keeping
        self.start_time = 0.0
        self.time_ui = 0.0
        self.last_activity = 0.0
        self.parent.window_main.showTerminalButton.setEnabled(True)

    def error(self, pkg, errormsg):
        InstallProgress.error(self, pkg, errormsg)
        logging.error("got an error from dpkg for pkg: '%s': '%s'" % (pkg, errormsg))
        # we do not report followup errors from earlier failures
        if gettext.dgettext('dpkg', "dependency problems - leaving unconfigured") in errormsg:
          return False
        summary = _("Could not install '%s'") % pkg
        msg = _("The upgrade will continue but the '%s' package may not "
                "be in a working state. Please consider submitting a "
                "bug report about it.") % pkg
        msg = "<big><b>%s</b></big><br />%s" % (summary, msg)

        dialogue = QDialog(self.parent.window_main)
        loadUi("dialog_error.ui", dialogue)
        self.parent.translate_widget_children(dialogue)
        dialogue.label_error.setText(msg)
        if errormsg != None:
            dialogue.textview_error.setText(errormsg)
            dialogue.textview_error.show()
        else:
            dialogue.textview_error.hide()
        # Make sure we have a suitable size depending on whether or not the view is shown
        dialogue.adjustSize()
        dialogue.exec_()

    def conffile(self, current, new):
        """ask question in case conffile has been changed by user"""
        logging.debug("got a conffile-prompt from dpkg for file: '%s'" % current)
        start = time.time()
        prim = _("Replace the customized configuration file\n'%s'?") % current
        sec = _("You will lose any changes you have made to this "
                "configuration file if you choose to replace it with "
                "a newer version.")
        markup = "<span weight=\"bold\" size=\"larger\">%s </span> \n\n%s" % (prim, sec)
        self.confDialogue = QDialog(self.parent.window_main)
        loadUi("dialog_conffile.ui", self.confDialogue)
        self.confDialogue.label_conffile.setText(markup)
        self.confDialogue.textview_conffile.hide()
        #FIXME, below to be tested
        #self.confDialogue.resize(self.confDialogue.minimumSizeHint())
        self.confDialogue.show_difference_button.clicked.connect(self.showConffile)

        # workaround silly dpkg
        if not os.path.exists(current):
          current = current+".dpkg-dist"

        # now get the diff
        if os.path.exists("/usr/bin/diff"):
          cmd = ["/usr/bin/diff", "-u", current, new]
          diff = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
          diff = diff.decode("UTF-8", "replace")
          self.confDialogue.textview_conffile.setText(diff)
        else:
          self.confDialogue.textview_conffile.setText(_("The 'diff' command was not found"))
        result = self.confDialogue.exec_()
        self.time_ui += time.time() - start
        # if replace, send this to the terminal
        if result == QDialog.Accepted:
            os.write(self.master_fd, b"y\n")
        else:
            os.write(self.master_fd, b"n\n")

    def showConffile(self):
        if self.confDialogue.textview_conffile.isVisible():
            self.confDialogue.textview_conffile.hide()
            self.confDialogue.show_difference_button.setText(_("Show Difference >>>"))
        else:
            self.confDialogue.textview_conffile.show()
            self.confDialogue.show_difference_button.setText(_("<<< Hide Difference"))

    def fork(self):
        """pty voodoo"""
        (self.child_pid, self.master_fd) = pty.fork()
        if self.child_pid == 0:
            os.environ["TERM"] = "dumb"
            if ("DEBIAN_FRONTEND" not in os.environ or
                os.environ["DEBIAN_FRONTEND"] == "kde"):
                os.environ["DEBIAN_FRONTEND"] = "noninteractive"
            os.environ["APT_LISTCHANGES_FRONTEND"] = "none"
        logging.debug(" fork pid is: %s" % self.child_pid)
        return self.child_pid

    def status_change(self, pkg, percent, status):
        """update progress bar and label"""
        # start the timer when the first package changes its status
        if self.start_time == 0.0:
          #print("setting start time to %s" % self.start_time)
          self.start_time = time.time()
        self.progress.setValue(self.percent)
        self.label_status.setText(utf8(status.strip()))
        # start showing when we gathered some data
        if percent > 1.0:
          self.last_activity = time.time()
          self.activity_timeout_reported = False
          delta = self.last_activity - self.start_time
          # time wasted in conffile questions (or other ui activity)
          delta -= self.time_ui
          time_per_percent = (float(delta)/percent)
          eta = (100.0 - self.percent) * time_per_percent
          # only show if we have some sensible data (60sec < eta < 2days)
          if eta > 61.0 and eta < (60*60*24*2):
            self.progress_text.setText(_("About %s remaining") % FuzzyTimeToStr(eta))
          else:
            self.progress_text.setText(" ")

    def finish_update(self):
        self.label_status.setText("")

    def update_interface(self):
        """
        no mainloop in this application, just call processEvents lots here
        it's also important to sleep for a minimum amount of time
        """
        # log the output of dpkg (on the master_fd) to the terminal log
        while True:
            try:
                (rlist, wlist, xlist) = select.select([self.master_fd],[],[], 0)
                if len(rlist) > 0:
                    line = os.read(self.master_fd, 255)
                    self._terminal_log.write(line)
                    self.parent.terminal_text.insertWithTermCodes(
                        utf8(line, errors="replace"))
                else:
                    break
            except Exception as e:
                print(e)
                logging.debug("error reading from self.master_fd '%s'" % e)
                break

        # now update the GUI
        try:
          InstallProgress.update_interface(self)
        except ValueError as e:
          logging.error("got ValueError from InstallProgress.update_interface. Line was '%s' (%s)" % (self.read, e))
          # reset self.read so that it can continue reading and does not loop
          self.read = ""
        # check about terminal activity
        if self.last_activity > 0 and \
           (self.last_activity + self.TIMEOUT_TERMINAL_ACTIVITY) < time.time():
          if not self.activity_timeout_reported:
            #FIXME bug 95465, I can't recreate this, so here's a hacky fix
            try:
                logging.warning("no activity on terminal for %s seconds (%s)" % (self.TIMEOUT_TERMINAL_ACTIVITY, self.label_status.text()))
            except UnicodeEncodeError:
                logging.warning("no activity on terminal for %s seconds" % (self.TIMEOUT_TERMINAL_ACTIVITY))
            self.activity_timeout_reported = True
          self.parent.window_main.konsole_frame.show()
        QApplication.processEvents()
        time.sleep(0.02)

    def wait_child(self):
        while True:
            self.update_interface()
            (pid, res) = os.waitpid(self.child_pid,os.WNOHANG)
            if pid == self.child_pid:
                break
        # we need the full status here (not just WEXITSTATUS)
        return res


# inherit from the class created in window_main.ui
# to add the handler for closing the window
class UpgraderMainWindow(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        #uic.loadUi("window_main.ui", self)
        loadUi("window_main.ui", self)

    def setParent(self, parentRef):
        self.parent = parentRef

    def closeEvent(self, event):
        close = self.parent.on_window_main_delete_event()
        if close:
            event.accept()
        else:
            event.ignore()


class DistUpgradeViewKDE(DistUpgradeView):
    """KDE frontend of the distUpgrade tool"""
    def __init__(self, datadir=None, logdir=None):
        DistUpgradeView.__init__(self)

        get_telemetry().set_updater_type('KDE')
        # silence the PyQt4 logger
        logger = logging.getLogger("PyQt4")
        logger.setLevel(logging.INFO)
        if not datadir or datadir == '.':
          localedir=os.path.join(os.getcwd(),"mo")
        else:
          localedir="/usr/share/locale/ubuntu-release-upgrader"

        # FIXME: i18n must be somewhere relative do this dir
        try:
          gettext.bindtextdomain("ubuntu-release-upgrader", localedir)
          gettext.textdomain("ubuntu-release-upgrader")
        except Exception as e:
          logging.warning("Error setting locales (%s)" % e)

        # we test for DISPLAY here, QApplication does not throw a
        # exception when run without DISPLAY but dies instead
        if not "DISPLAY" in os.environ:
            raise Exception("No DISPLAY in os.environ found")

        # Force environment to make sure Qt uses suitable theming and UX.
        os.environ["QT_PLATFORM_PLUGIN"] = "kde"
        # For above settings to apply automatically we need to indicate that we
        # are inside a full KDE session.
        os.environ["KDE_FULL_SESSION"] = "TRUE"
        # We also need to indicate version as otherwise KDElibs3 compatibility
        # might kick in such as in QIconLoader.cpp:QString fallbackTheme.
        os.environ["KDE_SESSION_VERSION"] = "5"
        # Pretty much all of the above but for Qt5
        os.environ["QT_QPA_PLATFORMTHEME"] = "kde"

        self.app = QApplication(["ubuntu-release-upgrader"])

        # Try to load default Qt translations so we don't have to worry about
        # QStandardButton translations.
        translator = QTranslator(self.app)
        if type(PYQT_VERSION) == int:
            translator.load(QLocale.system(), 'qt', '_', '/usr/share/qt5/translations')
        else:
            translator.load(QLocale.system(), 'qt', '_', '/usr/share/qt4/translations')
        self.app.installTranslator(translator)

        QUrlOpener().setupUrlHandles()

        messageIcon = _icon("system-software-update",
                            fallbacks=["/usr/share/icons/oxygen/48x48/apps/system-software-update.png",
                                       "/usr/share/icons/hicolor/48x48/apps/adept_manager.png"])
        self.app.setWindowIcon(messageIcon)

        self.window_main = UpgraderMainWindow()
        self.window_main.setParent(self)
        self.window_main.show()

        self.prev_step = None # keep a record of the latest step

        self._opCacheProgress = KDEOpProgress(self.window_main.progressbar_cache, self.window_main.progress_text)
        self._acquireProgress = KDEAcquireProgressAdapter(self)
        self._cdromProgress = KDECdromProgressAdapter(self)

        self._installProgress = KDEInstallProgressAdapter(self)

        # reasonable fault handler
        sys.excepthook = self._handleException

        self.window_main.showTerminalButton.setEnabled(False)
        self.window_main.showTerminalButton.clicked.connect(self.showTerminal)

        # init gettext
        gettext.bindtextdomain("ubuntu-release-upgrader",localedir)
        gettext.textdomain("ubuntu-release-upgrader")
        self.translate_widget_children()
        name = _OSRelease().result["PRETTY_NAME"]
        if not name or name == "Ubuntu":
            name = "Kubuntu"
        self.window_main.label_title.setText(self.window_main.label_title.text().replace("Ubuntu", name))

        # setup terminal text in hidden by default spot
        self.window_main.konsole_frame.hide()
        self.konsole_frame_layout = QHBoxLayout(self.window_main.konsole_frame)
        self.window_main.konsole_frame.setMinimumSize(600, 400)
        self.terminal_text = DumbTerminal(self._installProgress, self.window_main.konsole_frame)
        self.konsole_frame_layout.addWidget(self.terminal_text)
        self.terminal_text.show()

        self.inhibitScreenlock()
        atexit.register(self.uninhibitScreenlock)

        # Register on the system bus to allow session-side services to detect
        # our presence.
        service_name = 'com.ubuntu.ReleaseUpgrader.KDE'
        if not QDBusConnection.systemBus().registerService(service_name):
            logger.error('Failed to register on system bus %s', service_name)

        # Mask packagekit to avoid discover getting notifications or doing
        # any manipulations. The UX of this isn't ideal but since we can't
        # switch pk into an upgrade state it's the best we can do.
        self.maskPackageKit()
        atexit.register(self.unmaskPackageKit)

        # for some reason we need to start the main loop to get everything displayed
        # this app mostly works with processEvents but run main loop briefly to keep it happily displaying all widgets
        QTimer.singleShot(10, self.exitMainLoopMidFlight)
        self.app.exec_()

    def exitMainLoopMidFlight(self):
        # This is run shortly after startup. Do not add actual exit logic here!
        print("exitMainLoopMidFlight")
        self.app.exit()

    def inhibitScreenlock(self):
        if not QDBusConnection.sessionBus().isConnected():
            sys.stderr.write("Cannot connect to the D-Bus session bus.\n"
                    "To start it, run:\n"
                    "\teval `dbus-launch --auto-syntax`\n");
            return

        iface = QDBusInterface('org.kde.screensaver', '/ScreenSaver', '',
                QDBusConnection.sessionBus())

        if iface.isValid():
            msg = iface.call('Inhibit', 'DisUpgradeViewKDE', 'Upgrading base OS')
            reply = QDBusReply(msg)
            self.screenLockCookie = reply.value()

    def uninhibitScreenlock(self):
        if not QDBusConnection.sessionBus().isConnected():
            sys.stderr.write("Cannot connect to the D-Bus session bus.\n"
                    "To start it, run:\n"
                    "\teval `dbus-launch --auto-syntax`\n");
            return

        iface = QDBusInterface('org.kde.screensaver', '/ScreenSaver', '',
                QDBusConnection.sessionBus())

        if iface.isValid():
            iface.call('UnInhibit', self.screenLockCookie)

    def maskPackageKit(self):
        subprocess.run(['systemctl', 'mask', '--runtime', '--now', 'packagekit.socket'])
        subprocess.run(['systemctl', 'mask', '--runtime', '--now', 'packagekit.service'])

    def unmaskPackageKit(self):
        subprocess.run(['systemctl', 'unmask', '--runtime', 'packagekit.service'])
        subprocess.run(['systemctl', 'unmask', '--runtime', 'packagekit.socket'])

    def translate_widget_children(self, parentWidget=None):
        if parentWidget == None:
            parentWidget = self.window_main
        if isinstance(parentWidget, QDialog) or isinstance(parentWidget, QWidget):
            if str(parentWidget.windowTitle()) == "Error":
                parentWidget.setWindowTitle( gettext.dgettext("kdelibs", "Error"))
            else:
                parentWidget.setWindowTitle(_( str(parentWidget.windowTitle()) ))

        if parentWidget.children() != None:
            for widget in parentWidget.children():
                self.translate_widget(widget)
                self.translate_widget_children(widget)

    def translate_widget(self, widget):
        if isinstance(widget, QLabel) or isinstance(widget, QPushButton):
            if str(widget.text()) == "&Cancel":
                kdelibs = gettext.translation(
                    "kdelibs", gettext.textdomain("kdelibs"), fallback=True)
                widget.setText(unicode_gettext(kdelibs, "&Cancel"))
            elif str(widget.text()) == "&Close":
                kdelibs = gettext.translation(
                    "kdelibs", gettext.textdomain("kdelibs"), fallback=True)
                widget.setText(unicode_gettext(kdelibs, "&Close"))
            elif str(widget.text()) != "":
                widget.setText( _(str(widget.text())).replace("_", "&") )

    def _handleException(self, exctype, excvalue, exctb):
        """Crash handler."""

        if (issubclass(exctype, KeyboardInterrupt) or
            issubclass(exctype, SystemExit)):
            return

        # we handle the exception here, hand it to apport and run the
        # apport gui manually after it because we kill u-m during the upgrade
        # to prevent it from popping up for reboot notifications or FF restart
        # notifications or somesuch
        lines = traceback.format_exception(exctype, excvalue, exctb)
        logging.error("not handled exception in KDE frontend:\n%s" % "\n".join(lines))
        # we can't be sure that apport will run in the middle of a upgrade
        # so we still show a error message here
        apport_ran = apport_crash(exctype, excvalue, exctb)
        logging.debug("run apport? %s; ran apport? %s",
                      str(run_apport()), str(ran_apport))
        if not run_apport() or not apport_ran:
            tbtext = ''.join(traceback.format_exception(exctype, excvalue, exctb))
            dialog = QDialog(self.window_main)
            loadUi("dialog_error.ui", dialog)
            self.translate_widget_children(dialog)
            dialog.label_error.setText(_('A fatal error occurred'))
            dialog.image.setPixmap(QIcon.fromTheme('dialog-error').pixmap(48, 48))
            dialog.textview_error.setText(tbtext)
            # Make sure we have a suitable size depending on whether or not the view is shown
            dialog.adjustSize()
            dialog.exec_()
        sys.exit(1)

    def showTerminal(self):
        if self.window_main.konsole_frame.isVisible():
            self.window_main.konsole_frame.hide()
            self.window_main.showTerminalButton.setText(_("Show Terminal >>>"))
        else:
            self.window_main.konsole_frame.show()
            self.window_main.showTerminalButton.setText(_("<<< Hide Terminal"))
        self.window_main.adjustSize()

    def getAcquireProgress(self):
        return self._acquireProgress

    def getInstallProgress(self, cache):
        self._installProgress._cache = cache
        return self._installProgress

    def getOpCacheProgress(self):
        return self._opCacheProgress

    def getCdromProgress(self):
        return self._cdromProgress

    def update_status(self, msg):
        self.window_main.label_status.setText(msg)

    def hideStep(self, step):
        image = getattr(self.window_main,"image_step%i" % step.value)
        label = getattr(self.window_main,"label_step%i" % step.value)
        image.hide()
        label.hide()

    def abort(self):
        step = self.prev_step
        if step:
            image = getattr(self.window_main,"image_step%i" % step.value)
            cancelIcon = _icon("dialog-cancel",
                               fallbacks=["/usr/share/icons/oxygen/16x16/actions/dialog-cancel.png",
                                          "/usr/lib/kde4/share/icons/oxygen/16x16/actions/dialog-cancel.png",
                                          "/usr/share/icons/crystalsvg/16x16/actions/cancel.png"])
            image.setPixmap(cancelIcon.pixmap(16, 16))
            image.show()

    def setStep(self, step):
        super(DistUpgradeViewKDE , self).setStep(step)
        okIcon = _icon("dialog-ok",
                       fallbacks=["/usr/share/icons/oxygen/16x16/actions/dialog-ok.png",
                                  "/usr/lib/kde4/share/icons/oxygen/16x16/actions/dialog-ok.png",
                                  "/usr/share/icons/crystalsvg/16x16/actions/ok.png"])
        arrowIcon = _icon("arrow-right",
                          fallbacks=["/usr/share/icons/oxygen/16x16/actions/arrow-right.png",
                                     "/usr/lib/kde4/share/icons/oxygen/16x16/actions/arrow-right.png",
                                     "/usr/share/icons/crystalsvg/16x16/actions/1rightarrow.png"])

        if self.prev_step:
            image = getattr(self.window_main,"image_step%i" % self.prev_step.value)
            label = getattr(self.window_main,"label_step%i" % self.prev_step.value)
            image.setPixmap(okIcon.pixmap(16, 16))
            image.show()
            ##arrow.hide()
        self.prev_step = step
        # show the an arrow for the current step and make the label bold
        image = getattr(self.window_main,"image_step%i" % step.value)
        label = getattr(self.window_main,"label_step%i" % step.value)
        image.setPixmap(arrowIcon.pixmap(16, 16))
        image.show()
        label.setText("<b>" + label.text() + "</b>")

    def information(self, summary, msg, extended_msg=None):
        msg = "<big><b>%s</b></big><br />%s" % (summary,msg)

        dialogue = QDialog(self.window_main)
        loadUi("dialog_error.ui", dialogue)
        self.translate_widget_children(dialogue)
        dialogue.label_error.setText(msg)
        if extended_msg != None:
            dialogue.textview_error.setText(extended_msg)
            dialogue.textview_error.show()
        else:
            dialogue.textview_error.hide()
        dialogue.setWindowTitle(_("Information"))

        messageIcon = _icon("dialog-information",
                            fallbacks=["/usr/share/icons/oxygen/48x48/status/dialog-information.png",
                                       "/usr/lib/kde4/share/icons/oxygen/48x48/status/dialog-information.png",
                                       "/usr/share/icons/crystalsvg/32x32/actions/messagebox_info.png"])
        dialogue.image.setPixmap(messageIcon.pixmap(48, 48))
        # Make sure we have a suitable size depending on whether or not the view is shown
        dialogue.adjustSize()
        dialogue.exec_()

    def error(self, summary, msg, extended_msg=None):
        msg="<big><b>%s</b></big><br />%s" % (summary, msg)

        dialogue = QDialog(self.window_main)
        loadUi("dialog_error.ui", dialogue)
        self.translate_widget_children(dialogue)
        dialogue.label_error.setText(msg)
        if extended_msg != None:
            dialogue.textview_error.setText(extended_msg)
            dialogue.textview_error.show()
        else:
            dialogue.textview_error.hide()

        messageIcon = _icon("dialog-error",
                            fallbacks=["/usr/share/icons/oxygen/48x48/status/dialog-error.png",
                                       "/usr/lib/kde4/share/icons/oxygen/48x48/status/dialog-error.png",
                                       "/usr/share/icons/crystalsvg/32x32/actions/messagebox_critical.png"])
        dialogue.image.setPixmap(messageIcon.pixmap(48, 48))
        # Make sure we have a suitable size depending on whether or not the view is shown
        dialogue.adjustSize()
        dialogue.exec_()

        return False

    def confirmChanges(self, summary, changes, demotions, downloadSize,
                       actions=None, removal_bold=True):
        """show the changes dialogue"""
        # FIXME: add a whitelist here for packages that we expect to be
        # removed (how to calc this automatically?)
        DistUpgradeView.confirmChanges(self, summary, changes, demotions,
                                       downloadSize)
        self.changesDialogue = QDialog(self.window_main)
        loadUi("dialog_changes.ui", self.changesDialogue)

        self.changesDialogue.treeview_details.hide()
        self.changesDialogue.buttonBox.helpRequested.connect(self.showChangesDialogueDetails)
        self.translate_widget_children(self.changesDialogue)
        self.changesDialogue.buttonBox.button(QDialogButtonBox.Ok).setText(_("&Start Upgrade"))
        self.changesDialogue.buttonBox.button(QDialogButtonBox.Help).setIcon(QIcon())
        self.changesDialogue.buttonBox.button(QDialogButtonBox.Help).setText(_("Details") + " >>>")

        messageIcon = _icon("dialog-warning",
                            fallbacks=["/usr/share/icons/oxygen/48x48/status/dialog-warning.png",
                                       "/usr/lib/kde4/share/icons/oxygen/48x48/status/dialog-warning.png",
                                       "/usr/share/icons/crystalsvg/32x32/actions/messagebox_warning.png"])
        self.changesDialogue.question_pixmap.setPixmap(messageIcon.pixmap(48, 48))

        if actions != None:
            cancel = actions[0].replace("_", "")
            self.changesDialogue.buttonBox.button(QDialogButtonBox.Cancel).setText(cancel)
            confirm = actions[1].replace("_", "")
            self.changesDialogue.buttonBox.button(QDialogButtonBox.Ok).setText(confirm)

        summaryText = "<big><b>%s</b></big>" % summary
        self.changesDialogue.label_summary.setText(summaryText)
        self.changesDialogue.label_changes.setText(self.confirmChangesMessage)
        # fill in the details
        self.changesDialogue.treeview_details.clear()
        self.changesDialogue.treeview_details.setHeaderLabels(["Packages"])
        self.changesDialogue.treeview_details.header().hide()
        for demoted in self.demotions:
            self.changesDialogue.treeview_details.insertTopLevelItem(0, QTreeWidgetItem(self.changesDialogue.treeview_details, [_("No longer supported %s") % demoted.name]) )
        for rm in self.toRemove:
            self.changesDialogue.treeview_details.insertTopLevelItem(0, QTreeWidgetItem(self.changesDialogue.treeview_details, [_("Remove %s") % rm.name]) )
        for rm in self.toRemoveAuto:
            self.changesDialogue.treeview_details.insertTopLevelItem(0, QTreeWidgetItem(self.changesDialogue.treeview_details, [_("Remove (was auto installed) %s") % rm.name]) )
        for inst in self.toInstall:
            self.changesDialogue.treeview_details.insertTopLevelItem(0, QTreeWidgetItem(self.changesDialogue.treeview_details, [_("Install %s") % inst.name]) )
        for up in self.toUpgrade:
            self.changesDialogue.treeview_details.insertTopLevelItem(0, QTreeWidgetItem(self.changesDialogue.treeview_details, [_("Upgrade %s") % up.name]) )

        # Use a suitable size for the window given the current content.
        self.changesDialogue.adjustSize()

        #FIXME resize label, stop it being shrinkable
        res = self.changesDialogue.exec_()
        if res == QDialog.Accepted:
            return True
        return False

    def showChangesDialogueDetails(self):
        if self.changesDialogue.treeview_details.isVisible():
            self.changesDialogue.treeview_details.hide()
            self.changesDialogue.buttonBox.button(QDialogButtonBox.Help).setText(_("Details") + " >>>")
        else:
            self.changesDialogue.treeview_details.show()
            self.changesDialogue.buttonBox.button(QDialogButtonBox.Help).setText("<<< " + _("Details"))
        self.changesDialogue.adjustSize()

    def askYesNoQuestion(self, summary, msg, default='No'):
        answer = QMessageBox.question(self.window_main, summary, "<font>" + msg, QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            return True
        return False

    def confirmRestart(self):
        messageBox = QMessageBox(QMessageBox.Question, _("Restart required"), _("<b><big>Restart the system to complete the upgrade</big></b>"), QMessageBox.NoButton, self.window_main)
        yesButton = messageBox.addButton(QMessageBox.Yes)
        noButton = messageBox.addButton(QMessageBox.No)
        yesButton.setText(_("_Restart Now").replace("_", "&"))
        noButton.setText(gettext.dgettext("kdelibs", "&Close"))
        answer = messageBox.exec_()
        if answer == QMessageBox.Yes:
            return True
        return False

    def processEvents(self):
        QApplication.processEvents()

    def pulseProgress(self, finished=False):
        # FIXME: currently we do nothing here because this is
        # run in a different python thread and QT explodes if the UI is
        # touched from a non QThread
        pass

    def on_window_main_delete_event(self):
        #FIXME make this user friendly
        text = _("""<b><big>Cancel the running upgrade?</big></b>

The system could be in an unusable state if you cancel the upgrade. You are strongly advised to resume the upgrade.""")
        text = text.replace("\n", "<br />")
        cancel = QMessageBox.warning(self.window_main, _("Cancel Upgrade?"), text, QMessageBox.Yes, QMessageBox.No)
        if cancel == QMessageBox.Yes:
            return True
        return False


if __name__ == "__main__":

  view = DistUpgradeViewKDE()
  view.askYesNoQuestion("input box test","bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar bar ")

  if sys.argv[1] == "--test-term":
      pid = view.terminal_text.fork()
      if pid == 0:
          subprocess.call(["bash"])
          sys.exit()
      while True:
          view.terminal_text.update_interface()
          QApplication.processEvents()
          time.sleep(0.01)

  if sys.argv[1] == "--show-in-terminal":
      with open(sys.argv[2]) as f:
          chars = f.read()
      for c in chars:
          view.terminal_text.insertWithTermCodes( c )
          #print(c, ord(c))
          QApplication.processEvents()
          time.sleep(0.05)
      while True:
          QApplication.processEvents()

  cache = apt.Cache()
  for pkg in sys.argv[1:]:
    if cache[pkg].is_installed and not cache[pkg].is_upgradable:
      cache[pkg].mark_delete(purge=True)
    else:
      cache[pkg].mark_install()
  cache.commit(view._acquireProgress,view._installProgress)

  # keep the window open
  while True:
      QApplication.processEvents()
