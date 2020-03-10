"""
 SimpleGladeApp.py
 Module that provides an object oriented abstraction to pygtk and gtkbuilder
 Copyright (C) 2009 Michael Vogt
 based on ideas from SimpleGladeBuilder by Sandino Flores Moreno
"""

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; version 3.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

import logging
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio
from softwareproperties.gtk.utils import setup_ui
LOG=logging.getLogger(__name__)

# based on SimpleGladeApp
class SimpleGtkbuilderApp(Gtk.Application):

    def __init__(self, path, domain):
        Gtk.Application.__init__(self, application_id="com.ubuntu.SoftwareProperties",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        setup_ui(self, path, domain)
        self.connect("activate", self.on_activate)

    def on_activate(self, data=None):
        self.add_window(self.window_main)

        if not self.window_main.is_visible():
            self.window_main.show()

    def run(self):
        """
        Starts the main loop of processing events checking for Control-C.

        The default implementation checks wheter a Control-C is pressed,
        then calls on_keyboard_interrupt().

        Use this method for starting programs.
        """
        try:
            Gtk.Application.run(self, None)
        except KeyboardInterrupt:
            self.on_keyboard_Interrupt() 

    def on_keyboard_interrupt(self):
        """
        This method is called by the default implementation of run()
        after a program is finished by pressing Control-C.
        """
        pass
        
    def quit(self):
        """
        Quit processing events.
        The default implementation calls Gtk.main_quit()
        
        Useful for applications that needs a non gtk main loop.
        For example, applications based on gstreamer needs to override
        this method with gst.main_quit()
        """
        Gtk.Application.quit(self)

