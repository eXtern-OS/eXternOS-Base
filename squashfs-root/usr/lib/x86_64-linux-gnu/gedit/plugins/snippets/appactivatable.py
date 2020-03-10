#    Gedit snippets plugin
#    Copyright (C) 2005-2006  Jesse van den Kieboom <jesse@icecrew.nl>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import platform
from gi.repository import Gedit, Gtk, Gdk, GObject, Gio, GLib
from .library import Library
from .shareddata import SharedData

try:
    import gettext
    gettext.bindtextdomain('gedit')
    gettext.textdomain('gedit')
    _ = gettext.gettext
except:
    _ = lambda s: s

class AppActivatable(GObject.Object, Gedit.AppActivatable):
    __gtype_name__ = "GeditSnippetsAppActivatable"

    app = GObject.Property(type=Gedit.App)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        # Initialize snippets library
        library = Library()

        if platform.system() == 'Windows':
            snippetsdir = os.path.expanduser('~/gedit/snippets')
        else:
            snippetsdir = os.path.join(GLib.get_user_config_dir(), 'gedit/snippets')

        library.set_dirs(snippetsdir, self.system_dirs())

        self.css = Gtk.CssProvider()
        self.css.load_from_data("""
.gedit-snippet-manager-paned {
  border-style: solid;
  border-color: @borders;
}
.gedit-snippet-manager-paned:dir(ltr) {
  border-width: 0 1px 0 0;
}

.gedit-snippet-manager-paned:dir(rtl) {
  border-width: 0 0 0 1px;
}

.gedit-snippet-manager-view {
  border-width: 0 0 1px 0;
}

.gedit-snippet-manager-treeview {
  border-top-width: 0;
}

.gedit-snippet-manager-treeview:dir(ltr) {
  border-left-width: 0;
}

.gedit-snippet-manager-treeview:dir(rtl) {
  border-right-width: 0;
}
""".encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),
                             self.css, 600)

        action = Gio.SimpleAction(name="snippets")
        action.connect('activate', self.on_action_snippets_activate)
        self.app.add_action(action)

        item = Gio.MenuItem.new(_("Manage _Snippets…"), "app.snippets")
        self.menu = self.extend_menu("preferences-section")
        self.menu.append_menu_item(item)

    def do_deactivate(self):
        self.app.remove_action("snippets")
        self.menu = None
        Gtk.StyleContext.remove_provider_for_screen(Gdk.Screen.get_default(),
                                self.css)

    def system_dirs(self):
        dirs = []

        if 'XDG_DATA_DIRS' in os.environ:
            datadirs = os.environ['XDG_DATA_DIRS']
        elif platform.system() != 'Windows':
            datadirs = '/usr/local/share' + os.pathsep + '/usr/share'
        else:
            datadirs = GLib.win32_get_package_installation_directory_of_module(None)

        for d in datadirs.split(os.pathsep):
            d = os.path.join(d, 'gedit', 'plugins', 'snippets')

            if os.path.isdir(d):
                dirs.append(d)

        dirs.append(self.plugin_info.get_data_dir())
        return dirs

    def accelerator_activated(self, group, obj, keyval, mod):
        activatable = SharedData().lookup_window_activatable(obj)

        ret = False

        if activatable:
            ret = activatable.accelerator_activated(keyval, mod)

        return ret

    def create_configure_dialog(self):
        SharedData().show_manager(self.app.get_active_window(), self.plugin_info.get_data_dir())

    def on_action_snippets_activate(self, action, parameter):
        self.create_configure_dialog()

# vi:ex:ts=4:et
