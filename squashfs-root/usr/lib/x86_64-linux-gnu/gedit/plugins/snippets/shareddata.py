#    Gedit snippets plugin
#    Copyright (C) 2011  Jesse van den Kieboom <jessevdk@gnome.org>
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

from .singleton import Singleton
import os

from gi.repository import Gtk

# To register the GeditSnippetsManager type
from .manager import Manager

class SharedData(object, metaclass=Singleton):
    def __init__(self):
        self.dlg = None
        self.dlg_default_size = None
        self.controller_registry = {}
        self.windows = {}

    def register_controller(self, view, controller):
        self.controller_registry[view] = controller
    
    def unregister_controller(self, view, controller):
        if self.controller_registry[view] == controller:
            del self.controller_registry[view]

    def register_window(self, window):
        self.windows[window.window] = window

    def unregister_window(self, window):
        if window.window in self.windows:
            del self.windows[window.window]

    def update_state(self, window):
        if window in self.windows:
            self.windows[window].do_update_state()

    def get_active_controller(self, window):
        view = window.get_active_view()

        if not view or not view in self.controller_registry:
            return None

        return self.controller_registry[view]

    def get_controller(self, view):
        if view in self.controller_registry:
            return self.controller_registry[view]
        else:
            return None

    def manager_destroyed(self, dlg):
        self.dlg_default_size = dlg.get_final_size()
        self.dlg = None

    def show_manager(self, window, datadir):
        if not self.dlg:
            builder = Gtk.Builder()
            builder.add_from_file(os.path.join(datadir, 'ui', 'snippets.ui'))

            self.dlg = builder.get_object('snippets_manager')
            self.dlg.connect('destroy', self.manager_destroyed)

            if self.dlg_default_size:
                self.dlg.set_default_size(self.dlg_default_size[0], self.dlg_default_size[1])

        self.dlg.set_transient_for(window)
        self.dlg.present()

# vi:ex:ts=4:et
