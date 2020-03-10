# -*- coding: utf-8 -*-

#  Copyright (C) 2009 - Jesse van den Kieboom
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <http://www.gnu.org/licenses/>.

import os

import gi
gi.require_version('Gedit', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gio, GLib, Gtk, Gedit

from .popup import Popup
from .virtualdirs import RecentDocumentsDirectory
from .virtualdirs import CurrentDocumentsDirectory

try:
    import gettext
    gettext.bindtextdomain('gedit')
    gettext.textdomain('gedit')
    _ = gettext.gettext
except:
    _ = lambda s: s

class QuickOpenAppActivatable(GObject.Object, Gedit.AppActivatable):
    app = GObject.Property(type=Gedit.App)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self.app.add_accelerator("<Primary><Alt>O", "win.quickopen", None)

        self.menu_ext = self.extend_menu("file-section")
        item = Gio.MenuItem.new(_("Quick Open…"), "win.quickopen")
        self.menu_ext.prepend_menu_item(item)

    def do_deactivate(self):
        self.app.remove_accelerator("win.quickopen", None)


class QuickOpenPlugin(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "QuickOpenPlugin"

    window = GObject.Property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self._popup_size = (450, 300)
        self._popup = None

        action = Gio.SimpleAction(name="quickopen")
        action.connect('activate', self.on_quick_open_activate)
        self.window.add_action(action)

    def do_deactivate(self):
        self.window.remove_action("quickopen")

    def get_popup_size(self):
        return self._popup_size

    def set_popup_size(self, size):
        self._popup_size = size

    def _create_popup(self):
        paths = []

        # Open documents
        paths.append(CurrentDocumentsDirectory(self.window))

        doc = self.window.get_active_document()

        # Current document directory
        if doc and doc.get_file().is_local():
            gfile = doc.get_file().get_location()
            paths.append(gfile.get_parent())

        # File browser root directory
        bus = self.window.get_message_bus()

        if bus.is_registered('/plugins/filebrowser', 'get_root'):
            msg = bus.send_sync('/plugins/filebrowser', 'get_root')

            if msg:
                gfile = msg.props.location

                if gfile and gfile.is_native():
                    paths.append(gfile)

        # Recent documents
        paths.append(RecentDocumentsDirectory())

        # Local bookmarks
        for path in self._local_bookmarks():
            paths.append(path)

        # Desktop directory
        desktopdir = self._desktop_dir()

        if desktopdir:
            paths.append(Gio.file_new_for_path(desktopdir))

        # Home directory
        paths.append(Gio.file_new_for_path(os.path.expanduser('~')))

        self._popup = Popup(self.window, paths, self.on_activated)
        self.window.get_group().add_window(self._popup)

        self._popup.set_default_size(*self.get_popup_size())
        self._popup.set_transient_for(self.window)
        self._popup.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self._popup.connect('destroy', self.on_popup_destroy)

    def _local_bookmarks(self):
        filename = os.path.expanduser('~/.config/gtk-3.0/bookmarks')

        if not os.path.isfile(filename):
            return []

        paths = []

        for line in open(filename, 'r', encoding='utf-8'):
            uri = line.strip().split(" ")[0]
            f = Gio.file_new_for_uri(uri)

            if f.is_native():
                try:
                    info = f.query_info(Gio.FILE_ATTRIBUTE_STANDARD_TYPE,
                                        Gio.FileQueryInfoFlags.NONE,
                                        None)

                    if info and info.get_file_type() == Gio.FileType.DIRECTORY:
                        paths.append(f)
                except:
                    pass

        return paths

    def _desktop_dir(self):
        config = os.getenv('XDG_CONFIG_HOME')

        if not config:
            config = os.path.expanduser('~/.config')

        config = os.path.join(config, 'user-dirs.dirs')
        desktopdir = None

        if os.path.isfile(config):
            for line in open(config, 'r', encoding='utf-8'):
                line = line.strip()

                if line.startswith('XDG_DESKTOP_DIR'):
                    parts = line.split('=', 1)
                    desktopdir = parts[1].strip('"').strip("'")
                    desktopdir = os.path.expandvars(desktopdir)
                    break

        if not desktopdir:
            desktopdir = os.path.expanduser('~/Desktop')

        return desktopdir

    # Callbacks
    def on_quick_open_activate(self, action, parameter, user_data=None):
        if not self._popup:
            self._create_popup()

        self._popup.show()

    def on_popup_destroy(self, popup, user_data=None):
        self.set_popup_size(popup.get_final_size())

        self._popup = None

    def on_activated(self, gfile, user_data=None):
        Gedit.commands_load_location(self.window, gfile, None, -1, -1)
        return True

# ex:ts=4:et:
