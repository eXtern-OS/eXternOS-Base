# DistUpgradeFetcherKDE.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2008 Canonical Ltd
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
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
    from PyQt5.QtCore import QTranslator, PYQT_VERSION, \
        QLocale
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, \
        QApplication
except ImportError:
    from PyKDE4.kdeui import KIcon, KMessageBox, KStandardGuiItem
    from PyQt4.QtGui import QDialog, QDialogButtonBox, QApplication, QIcon
    from PyQt4.QtCore import PYQT_VERSION
    from PyQt4 import uic

import apt_pkg

from DistUpgrade.DistUpgradeFetcherCore import DistUpgradeFetcherCore
from gettext import gettext as _
from urllib.request import urlopen
from urllib.error import HTTPError
import os

import apt

from .QUrlOpener import QUrlOpener


# TODO: uifile resolution is an utter mess and should be revised globally for
#       both the fetcher and the upgrader GUI.

# TODO: make this a singleton
# We have no globally constructed QApplication available so we need to
# make sure that one is created when needed. Since from a module POV
# this can be happening in any order of the two classes this function takes
# care of it for the classes, the classes only hold a ref to the qapp returned
# to prevent it from getting GC'd, so in essence this is a singleton scoped to
# the longest lifetime of an instance from the Qt GUI. Since the lifetime is
# pretty much equal to the process' one we might as well singleton up.
def _ensureQApplication():
    if not QApplication.instance():
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

        app = QApplication(["ubuntu-release-upgrader"])

        # Try to load default Qt translations so we don't have to worry about
        # QStandardButton translations.
        # FIXME: make sure we dep on l10n
        translator = QTranslator(app)
        if type(PYQT_VERSION) == int:
            translator.load(QLocale.system(), 'qt', '_',
                            '/usr/share/qt5/translations')
        else:
            translator.load(QLocale.system(), 'qt', '_',
                            '/usr/share/qt4/translations')
        app.installTranslator(translator)
        return app
    return QApplication.instance()


# Qt 5 vs. KDELibs4 compat functions
def _warning(text):
    if type(PYQT_VERSION) == int:
        QMessageBox.warning(None, "", text)
    else:
        KMessageBox.sorry(None, text, "")


def _icon(name):
    if type(PYQT_VERSION) == int:
        return QIcon.fromTheme(name)
    else:
        return KIcon(name)


class DistUpgradeFetcherKDE(DistUpgradeFetcherCore):

    def __init__(self, new_dist, progress, parent, datadir):
        DistUpgradeFetcherCore.__init__(self, new_dist, progress)

        self.app = _ensureQApplication()
        self.app.setWindowIcon(_icon("system-software-update"))

        self.datadir = datadir

        QUrlOpener().setupUrlHandles()

        QApplication.processEvents()

    def error(self, summary, message):
        if type(PYQT_VERSION) == int:
            QMessageBox.critical(None, summary, message)
        else:
            KMessageBox.sorry(None, message, summary)

    def runDistUpgrader(self):
        # now run it with sudo
        if os.getuid() != 0:
            os.execv("/usr/bin/pkexec",
                     ["pkexec",
                      self.script + " --frontend=DistUpgradeViewKDE"])
        else:
            os.execv(self.script,
                     [self.script, "--frontend=DistUpgradeViewKDE"] +
                     self.run_options)

    def showReleaseNotes(self):
        # FIXME: care about i18n! (append -$lang or something)
        # TODO:  ^ what is this supposed to mean?
        self.dialog = QDialog()
        uic.loadUi(self.datadir + "/dialog_release_notes.ui", self.dialog)
        upgradeButton = self.dialog.buttonBox.button(QDialogButtonBox.Ok)
        upgradeButton.setText(_("&Upgrade"))
        upgradeButton.setIcon(_icon("dialog-ok"))
        cancelButton = self.dialog.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.setText(_("&Cancel"))
        cancelButton.setIcon(_icon("dialog-cancel"))
        self.dialog.setWindowTitle(_("Release Notes"))
        self.dialog.show()
        if self.new_dist.releaseNotesHtmlUri is not None:
            uri = self._expandUri(self.new_dist.releaseNotesHtmlUri)
            # download/display the release notes
            # TODO: add some progress reporting here
            result = None
            try:
                release_notes = urlopen(uri)
                notes = release_notes.read().decode("UTF-8", "replace")
                self.dialog.scrolled_notes.setText(notes)
                result = self.dialog.exec_()
            except HTTPError:
                primary = "<span weight=\"bold\" size=\"larger\">%s</span>" % \
                          _("Could not find the release notes")
                secondary = _("The server may be overloaded. ")
                _warning(primary + "<br />" + secondary)
            except IOError:
                primary = "<span weight=\"bold\" size=\"larger\">%s</span>" % \
                          _("Could not download the release notes")
                secondary = _("Please check your internet connection.")
                _warning(primary + "<br />" + secondary)
            # user clicked cancel
            if result == QDialog.Accepted:
                return True
        return False


class KDEAcquireProgressAdapter(apt.progress.base.AcquireProgress):
    def __init__(self, parent, datadir, label):
        self.app = _ensureQApplication()
        self.dialog = QDialog()

        uiFile = os.path.join(datadir, "fetch-progress.ui")
        uic.loadUi(uiFile, self.dialog)
        self.dialog.setWindowTitle(_("Upgrade"))
        self.dialog.installingLabel.setText(label)
        self.dialog.buttonBox.rejected.connect(self.abort)

        # This variable is used as return value for AcquireProgress pulses.
        # Setting it to False will abort the Acquire and consequently the
        # entire fetcher.
        self._continue = True

        QApplication.processEvents()

    def abort(self):
        self._continue = False

    def start(self):
        self.dialog.installingLabel.setText(
            _("Downloading additional package files..."))
        self.dialog.installationProgress.setValue(0)
        self.dialog.show()

    def stop(self):
        self.dialog.hide()

    def pulse(self, owner):
        apt.progress.base.AcquireProgress.pulse(self, owner)
        self.dialog.installationProgress.setValue(
            (self.current_bytes + self.current_items) /
            float(self.total_bytes + self.total_items) * 100)
        current_item = self.current_items + 1
        if current_item > self.total_items:
            current_item = self.total_items
        label_text = _("Downloading additional package files...")
        if self.current_cps > 0:
            label_text += _("File %s of %s at %sB/s") % (
                self.current_items, self.total_items,
                apt_pkg.size_to_str(self.current_cps))
        else:
            label_text += _("File %s of %s") % (
                self.current_items, self.total_items)
        self.dialog.installingLabel.setText(label_text)
        QApplication.processEvents()
        return self._continue

    def mediaChange(self, medium, drive):
        msg = _("Please insert '%s' into the drive '%s'") % (medium, drive)
        if type(PYQT_VERSION) == int:
            change = QMessageBox.question(None, _("Media Change"), msg,
                                          QMessageBox.Ok, QMessageBox.Cancel)
            if change == QMessageBox.Ok:
                return True
        else:
            change = KMessageBox.questionYesNo(None, _("Media Change"),
                                               _("Media Change") + "<br>" +
                                               msg, KStandardGuiItem.ok(),
                                               KStandardGuiItem.cancel())
            if change == KMessageBox.Yes:
                return True
        return False
