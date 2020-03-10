# ChangelogViewer.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2006 Sebastian Heinlein
#                2007 Canonical
#
#  Author: Sebastian Heinlein <sebastian.heinlein@web.de>
#          Michael Vogt <michael.vogt@ubuntu.com>
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


from __future__ import absolute_import

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import Pango
from gettext import gettext as _

from DistUpgrade.ReleaseNotesViewer import open_url


class ChangelogViewer(Gtk.TextView):
    def __init__(self, changelog=None):
        """Init the ChangelogViewer as an Inheritance of the Gtk.TextView"""
        # init the parent
        GObject.GObject.__init__(self)
        # global hovering over link state
        self.hovering = False
        self.first = True
        # setup the buffer and signals
        self.set_property("editable", False)
        self.set_cursor_visible(False)
        # set some margin
        self.set_right_margin(4)
        self.set_left_margin(4)
        self.set_pixels_above_lines(4)
        # fill the area
        self.set_vexpand(True)
        self.buffer = Gtk.TextBuffer()
        self.set_buffer(self.buffer)
        self.connect("button-press-event", self.button_press_event)
        self.connect("motion-notify-event", self.motion_notify_event)
        self.connect("visibility-notify-event", self.visibility_notify_event)
        #self.buffer.connect("changed", self.search_links)
        self.buffer.connect_after("insert-text", self.on_insert_text)
        # search for links in the changelog and make them clickable
        if changelog is not None:
            self.buffer.set_text(changelog)

    def create_context_menu(self, url):
        """Create the context menu to be displayed when links are right
           clicked"""
        self.menu = Gtk.Menu()

        # create menu items
        item_grey_link = Gtk.MenuItem()
        item_grey_link.set_label(url)
        item_grey_link.connect("activate", self.handle_context_menu, "open",
                               url)
        item_seperator = Gtk.MenuItem()
        item_open_link = Gtk.MenuItem()
        item_open_link.set_label(_("Open Link in Browser"))
        item_open_link.connect("activate", self.handle_context_menu, "open",
                               url)
        item_copy_link = Gtk.MenuItem()
        item_copy_link.set_label(_("Copy Link to Clipboard"))
        item_copy_link.connect("activate", self.handle_context_menu, "copy",
                               url)

        # add menu items
        self.menu.add(item_grey_link)
        self.menu.add(item_seperator)
        self.menu.add(item_open_link)
        self.menu.add(item_copy_link)
        self.menu.show_all()

    def handle_context_menu(self, menuitem, action, url):
        """Handle activate event for the links' context menu"""
        if action == "open":
            open_url(url)
        if action == "copy":
            # the following two lines used to be enough - then gtk3/pygi
            # came along ...
            #cb = Gtk.Clipboard()
            #cb.set_text(url)
            display = Gdk.Display.get_default()
            selection = Gdk.Atom.intern("CLIPBOARD", False)
            cb = Gtk.Clipboard.get_for_display(display, selection)
            cb.set_text(url, -1)
            cb.store()

    def tag_link(self, start, end, url):
        """Apply the tag that marks links to the specified buffer selection"""
        tags = start.get_tags()
        for tag in tags:
            url = getattr(tag, "url", None)
            if url != "":
                return
        tag = self.buffer.create_tag(None, foreground="blue",
                                     underline=Pango.Underline.SINGLE)
        tag.url = url
        self.buffer.apply_tag(tag, start, end)

    def on_insert_text(self, buffer, iter_end, content, *args):
        """Search for http URLs in newly inserted text
           and tag them accordingly"""

        # some convenient urls
        MALONE = "https://launchpad.net/bugs/"
        DEBIAN = "http://bugs.debian.org/"
        CVE = "http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-"
        # some convinient end-markers
        ws = [" ", "\t", "\n"]
        brak = [")", "]", ">"]
        punct = [",", "!", ":"]
        dot = ["."] + punct
        dot_cr = [".\n"]

        # search items are start-str, list-of-end-strs, url-prefix
        # a lot of this search is "TEH SUCK"(tm) because of limitations
        # in iter.forward_search()
        # - i.e. no insensitive searching, no regexp
        search_items = [("http://", ws + brak + punct + dot_cr, "http://"),
                        ("LP#", ws + brak + dot, MALONE),
                        ("lp#", ws + brak + dot, MALONE),
                        ("LP: #", ws + brak + dot, MALONE),
                        ("lp: #", ws + brak + dot, MALONE),
                        ("LP:#", ws + brak + dot, MALONE),
                        ("lp:#", ws + brak + dot, MALONE),
                        ("Malone: #", ws + brak + dot, MALONE),
                        ("Malone:#", ws + brak + dot, MALONE),
                        ("Ubuntu: #", ws + brak + dot, MALONE),
                        ("Ubuntu:#", ws + brak + dot, MALONE),
                        ("Closes: #", ws + brak + dot, DEBIAN),
                        ("Closes:#", ws + brak + dot, DEBIAN),
                        ("closes:#", ws + brak + dot, DEBIAN),
                        ("closes: #", ws + brak + dot, DEBIAN),
                        ("CVE-", ws + brak + dot, CVE),
                        ]

        # search for the next match in the buffer
        for (start_str, end_list, url_prefix) in search_items:
            # init
            iter = buffer.get_iter_at_offset(iter_end.get_offset() -
                                             len(content))
            while True:
                ret = iter.forward_search(start_str,
                                          Gtk.TextSearchFlags.VISIBLE_ONLY,
                                          iter_end)
                # if we reach the end break the loop
                if not ret:
                    break
                # get the position of the protocol prefix
                (match_start, match_end) = ret
                match_suffix = match_end.copy()
                match_tmp = match_end.copy()
                while True:
                    # extend the selection to the complete search item
                    if match_tmp.forward_char():
                        text = match_end.get_text(match_tmp)
                        if text in end_list:
                            break
                        # move one char futher to get two char
                        # end-markers (and back later) LP: #396393
                        match_tmp.forward_char()
                        text = match_end.get_text(match_tmp)
                        if text in end_list:
                            break
                        match_tmp.backward_char()
                    else:
                        break
                    match_end = match_tmp.copy()

                # call the tagging method for the complete URL
                url = url_prefix + match_suffix.get_text(match_end)

                self.tag_link(match_start, match_end, url)
                # set the starting point for the next search
                iter = match_end

    def button_press_event(self, text_view, event):
        """callback for mouse click events"""
        # we only react on left or right mouse clicks
        if event.button != 1 and event.button != 3:
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
        # call open_url or menu.popup if an URL is assigned to the iter
        try:
            iter = self.get_iter_at_location(x, y)
            tags = iter.get_tags()
        except AttributeError:
            # GTK > 3.20 added a return type to this function
            (over_text, iter) = self.get_iter_at_location(x, y)
            tags = iter.get_tags()

        for tag in tags:
            if hasattr(tag, "url"):
                if event.button == 1:
                    open_url(tag.url)
                    break
                if event.button == 3:
                    self.create_context_menu(tag.url)
                    self.menu.popup(None, None, None, None, event.button,
                                    event.time)
                    return True

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
        (bx, by) = text_view.window_to_buffer_coords(Gtk.TextWindowType.WIDGET,
                                                     wx, wy)
        self.check_hovering(bx, by)
        return False

    def check_hovering(self, x, y):
        """Check if the mouse is above a tagged link and if yes show
           a hand cursor"""
        _hovering = False
        # get the iter at the mouse position
        try:
            iter = self.get_iter_at_location(x, y)
            tags = iter.get_tags()
        except AttributeError:
            # GTK > 3.20 added a return type to this function
            (over_text, iter) = self.get_iter_at_location(x, y)
            tags = iter.get_tags()

        # set _hovering if the iter has the tag "url"
        for tag in tags:
            if hasattr(tag, "url"):
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
    w = Gtk.Window()
    cv = ChangelogViewer()
    changes = cv.get_buffer()
    changes.create_tag("versiontag", weight=Pango.Weight.BOLD)
    changes.set_text("""

Version 6-14-0ubuntu1.9.04:

  * New upstream version. LP: #382918.
    Release notes at http://java.sun.com/javase/6/webnotes/ReleaseNotes.html.

""")

    w.add(cv)
    w.show_all()
    Gtk.main()
