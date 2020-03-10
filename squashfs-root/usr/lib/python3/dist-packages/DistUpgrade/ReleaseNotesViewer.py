# ReleaseNotesViewer.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2006 Sebastian Heinlein
#
#  Author: Sebastian Heinlein <sebastian.heinlein@web.de>
#
#  This modul provides an inheritance of the Gtk.TextView that is
#  aware of http URLs and allows to open them in a browser.
#  It is based on the pygtk-demo "hypertext".
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

from gi.repository import Pango
from gi.repository import Gtk, GObject, Gdk
import os
import subprocess


def open_url(url):
    """Open the specified URL in a browser"""
    # Find an appropiate browser
    if os.path.exists("/usr/bin/xdg-open"):
        command = ["xdg-open", url]
    elif os.path.exists("/usr/bin/exo-open"):
        command = ["exo-open", url]
    elif os.path.exists('/usr/bin/gnome-open'):
        command = ['gnome-open', url]
    else:
        command = ['x-www-browser', url]
    # Avoid to run the browser as user root
    if os.getuid() == 0 and 'SUDO_USER' in os.environ:
        command = ['sudo', '-u', os.environ['SUDO_USER']] + command
    elif os.getuid() == 0 and 'PKEXEC_UID' in os.environ:
        command = ['sudo', '-H', '-u',
                   '#' + os.environ['PKEXEC_UID']] + command
    subprocess.Popen(command)


class ReleaseNotesViewer(Gtk.TextView):
    def __init__(self, notes):
        """Init the ReleaseNotesViewer as an Inheritance of the Gtk.TextView.
           Load the notes into the buffer and make links clickable"""
        # init the parent
        GObject.GObject.__init__(self)
        # global hovering over link state
        self.hovering = False
        self.first = True
        # setup the buffer and signals
        self.set_property("editable", False)
        self.set_cursor_visible(False)
        self.modify_font(Pango.FontDescription("monospace"))
        self.buffer = Gtk.TextBuffer()
        self.set_buffer(self.buffer)
        self.buffer.set_text(notes)
        self.connect("button-press-event", self.button_press_event)
        self.connect("motion-notify-event", self.motion_notify_event)
        self.connect("visibility-notify-event", self.visibility_notify_event)
        # search for links in the notes and make them clickable
        self.search_links()

    def tag_link(self, start, end, url):
        """Apply the tag that marks links to the specified buffer selection"""
        tag = self.buffer.create_tag(None, foreground="blue",
                                     underline=Pango.Underline.SINGLE)
        tag.url = url
        self.buffer.apply_tag(tag, start, end)

    def search_links(self):
        """Search for http URLs in the buffer and call the tag_link method
           for each one to tag them as links"""
        # start at the beginning of the buffer
        iter = self.buffer.get_iter_at_offset(0)
        while 1:
            # search for the next URL in the buffer
            ret = iter.forward_search("http://",
                                      Gtk.TextSearchFlags.VISIBLE_ONLY,
                                      None)
            # if we reach the end break the loop
            if not ret:
                break
            # get the position of the protocol prefix
            (match_start, match_end) = ret
            match_tmp = match_end.copy()
            while 1:
                # extend the selection to the complete URL
                if match_tmp.forward_char():
                    text = match_end.get_text(match_tmp)
                    if text in (" ", ")", "]", "\n", "\t"):
                        break
                else:
                    break
                match_end = match_tmp.copy()
            # call the tagging method for the complete URL
            url = match_start.get_text(match_end)
            self.tag_link(match_start, match_end, url)
            # set the starting point for the next search
            iter = match_end

    def button_press_event(self, text_view, event):
        """callback for mouse click events"""
        if event.button != 1:
            return False

        # try to get a selection
        try:
            (start, end) = self.buffer.get_selection_bounds()
        except ValueError:
            pass
        else:
            if start.get_offset() != end.get_offset():
                return False

        # get the iter at the mouse position
        (x, y) = self.window_to_buffer_coords(Gtk.TextWindowType.WIDGET,
                                              int(event.x), int(event.y))
        iter = self.get_iter_at_location(x, y)

        # call open_url if an URL is assigned to the iter
        tags = iter.get_tags()
        for tag in tags:
            url = getattr(tag, "url", None)
            if url != "":
                open_url(url)
                break

    def motion_notify_event(self, text_view, event):
        """callback for the mouse movement event, that calls the
           check_hovering method with the mouse postition coordiantes"""
        x, y = text_view.window_to_buffer_coords(Gtk.TextWindowType.WIDGET,
                                                 int(event.x), int(event.y))
        self.check_hovering(x, y)
        self.get_window(Gtk.TextWindowType.TEXT).get_pointer()
        return False

    def visibility_notify_event(self, text_view, event):
        """callback if the widgets gets visible (e.g. moves to the foreground)
           that calls the check_hovering method with the mouse position
           coordinates"""
        window = text_view.get_window(Gtk.TextWindowType.TEXT)
        (screen, wx, wy, mod) = window.get_pointer()
        (bx, by) = text_view.window_to_buffer_coords(
            Gtk.TextWindowType.WIDGET, wx, wy)
        self.check_hovering(bx, by)
        return False

    def check_hovering(self, x, y):
        """Check if the mouse is above a tagged link and if yes show
           a hand cursor"""
        _hovering = False
        # get the iter at the mouse position
        iter = self.get_iter_at_location(x, y)

        # set _hovering if the iter has the tag "url"
        tags = iter.get_tags()
        for tag in tags:
            url = getattr(tag, "url", None)
            if url != "":
                _hovering = True
                break

        # change the global hovering state
        if _hovering != self.hovering or self.first:
            self.first = False
            self.hovering = _hovering
            # Set the appropriate cursur icon
            if self.hovering:
                self.get_window(Gtk.TextWindowType.TEXT).set_cursor(
                    Gdk.Cursor.new(Gdk.CursorType.HAND2))
            else:
                self.get_window(Gtk.TextWindowType.TEXT).set_cursor(
                    Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR))


if __name__ == "__main__":
    # some simple test code
    win = Gtk.Window()
    rv = ReleaseNotesViewer(open("../DistUpgrade/ReleaseAnnouncement").read())
    win.add(rv)
    win.show_all()
    Gtk.main()
