# DistUpgradeFetcher.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2006 Canonical
#
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
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

from gi.repository import Gtk, Gdk

from .ReleaseNotesViewer import ReleaseNotesViewer
from .utils import error
from .DistUpgradeFetcherCore import DistUpgradeFetcherCore
from .SimpleGtk3builderApp import SimpleGtkbuilderApp
from gettext import gettext as _
from urllib.request import urlopen
from urllib.error import HTTPError
import os
import socket


class DistUpgradeFetcherGtk(DistUpgradeFetcherCore):

    def __init__(self, new_dist, progress, parent, datadir):
        DistUpgradeFetcherCore.__init__(self, new_dist, progress)
        uifile = os.path.join(datadir, "gtkbuilder", "ReleaseNotes.ui")
        self.widgets = SimpleGtkbuilderApp(uifile, "ubuntu-release-upgrader")
        self.window_main = parent

    def error(self, summary, message):
        return error(self.window_main, summary, message)

    def runDistUpgrader(self):
        os.execv(self.script, [self.script] + self.run_options)

    def showReleaseNotes(self):
        # first try showing the webkit version, this may fail (return None
        # because e.g. there is no webkit installed)
        res = self._try_show_release_notes_webkit()
        if res is not None:
            return res
        else:
            # fallback to text
            return self._try_show_release_notes_textview()

    def _try_show_release_notes_webkit(self):
        if self.new_dist.releaseNotesHtmlUri is not None:
            try:
                from .ReleaseNotesViewerWebkit import ReleaseNotesViewerWebkit
                webkit_release_notes = ReleaseNotesViewerWebkit(
                    self.new_dist.releaseNotesHtmlUri)
                webkit_release_notes.show()
                self.widgets.scrolled_notes.add(webkit_release_notes)
                res = self.widgets.dialog_release_notes.run()
                self.widgets.dialog_release_notes.hide()
                if res == Gtk.ResponseType.OK:
                    return True
                return False
            except ImportError:
                pass
        return None

    def _try_show_release_notes_textview(self):
        # FIXME: care about i18n! (append -$lang or something)
        if self.new_dist.releaseNotesURI is not None:
            uri = self._expandUri(self.new_dist.releaseNotesURI)
            if self.window_main:
                self.window_main.set_sensitive(False)
                self.window_main.get_window().set_cursor(
                    Gdk.Cursor.new(Gdk.CursorType.WATCH))
            while Gtk.events_pending():
                Gtk.main_iteration()

            # download/display the release notes
            # FIXME: add some progress reporting here
            res = Gtk.ResponseType.CANCEL
            timeout = socket.getdefaulttimeout()
            try:
                socket.setdefaulttimeout(5)
                release_notes = urlopen(uri)
                notes = release_notes.read().decode("UTF-8", "replace")
                textview_release_notes = ReleaseNotesViewer(notes)
                textview_release_notes.show()
                self.widgets.scrolled_notes.add(textview_release_notes)
                release_widget = self.widgets.dialog_release_notes
                release_widget.set_transient_for(self.window_main)
                res = self.widgets.dialog_release_notes.run()
                self.widgets.dialog_release_notes.hide()
            except HTTPError:
                primary = "<span weight=\"bold\" size=\"larger\">%s</span>" % \
                          _("Could not find the release notes")
                secondary = _("The server may be overloaded. ")
                dialog = Gtk.MessageDialog(self.window_main,
                                           Gtk.DialogFlags.MODAL,
                                           Gtk.MessageType.ERROR,
                                           Gtk.ButtonsType.CLOSE, "")
                dialog.set_title("")
                dialog.set_markup(primary)
                dialog.format_secondary_text(secondary)
                dialog.run()
                dialog.destroy()
            except IOError:
                primary = "<span weight=\"bold\" size=\"larger\">%s</span>" % \
                          _("Could not download the release notes")
                secondary = _("Please check your internet connection.")
                dialog = Gtk.MessageDialog(self.window_main,
                                           Gtk.DialogFlags.MODAL,
                                           Gtk.MessageType.ERROR,
                                           Gtk.ButtonsType.CLOSE, "")
                dialog.set_title("")
                dialog.set_markup(primary)
                dialog.format_secondary_text(secondary)
                dialog.run()
                dialog.destroy()
            socket.setdefaulttimeout(timeout)
            if self.window_main:
                self.window_main.set_sensitive(True)
                self.window_main.get_window().set_cursor(None)
            # user clicked cancel
            if res == Gtk.ResponseType.OK:
                return True
        return False
