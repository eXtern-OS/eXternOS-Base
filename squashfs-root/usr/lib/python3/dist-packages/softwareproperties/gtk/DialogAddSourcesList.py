#!/usr/bin/env python

from __future__ import print_function

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gdk, Gtk
import os
from gettext import gettext as _
import gettext
try:
    from urllib.request import url2pathname
except ImportError:
    from urllib import url2pathname

from softwareproperties.gtk.utils import (
    setup_ui,
)

from aptsources.sourceslist import SourcesList, SourceEntryMatcher


class DialogAddSourcesList:
    def __init__(self, parent, sourceslist, source_renderer,
                 get_comparable, datadir, file):
        print(file)
        self.parent = parent
        self.source_renderer = source_renderer
        self.sourceslist = sourceslist
        self.get_comparable = get_comparable
        self.file = self.format_uri(file)
        
        setup_ui(self, os.path.join(datadir, "gtkbuilder", "dialog-add-sources-list.ui"), domain="software-properties")
        
        self.dialog = self.dialog_add_sources_list
        self.label = self.label_sources
        self.treeview = self.treeview_sources
        self.scrolled = self.scrolled_window
        self.image = self.image_sources_list

        self.dialog.realize()
        if self.parent != None:
            self.dialog.set_transient_for(parent)
        else:
            self.dialog.set_title(_("Add Software Channels"))
        self.dialog.get_window().set_functions(Gdk.WMFunction.MOVE)

        # Setup the treeview
        self.store = Gtk.ListStore(GObject.TYPE_STRING)
        self.treeview.set_model(self.store)
        cell = Gtk.CellRendererText()
        cell.set_property("xpad", 2)
        cell.set_property("ypad", 2)
        column = Gtk.TreeViewColumn("Software Channel", cell, markup=0)
        column.set_max_width(500)
        self.treeview.append_column(column)

        # Parse the source.list file
        try:
            self.new_sources = SingleSourcesList(self.file)
        except:
            self.error()
            return

        # show the found channels or an error message
        if len(self.new_sources.list) > 0:
            counter = 0

            for source in self.new_sources.list:
                if source.invalid or source.disabled:
                    continue
                self.new_sources.matcher.match(source)
            # sort the list
            self.new_sources.list.sort(key=self.get_comparable)
            
            for source in self.new_sources.list:
                if source.invalid or source.disabled:
                    continue
                counter = counter +1
                line = self.source_renderer(source)
                self.store.append([line])
            if counter == 0:
                self.error()
                return

            header = gettext.ngettext("Install software additionally or "
                                      "only from this source?",
                                      "Install software additionally or "
                                      "only from these sources?",
                                      counter)
            body = _("You can either add the following sources or replace your "
                     "current sources by them. Only install software from "
                     "trusted sources.")
            self.label.set_markup("<big><b>%s</b></big>\n\n%s" % (header, body))
        else:
            self.error()
            return

    def error(self):
        self.button_add.hide()
        self.button_cancel.set_use_stock(True)
        self.button_cancel.set_label("gtk-close")
        self.button_replace.hide()
        self.scrolled.hide()
        self.image.set_from_stock(Gtk.STOCK_DIALOG_ERROR, Gtk.IconSize.DIALOG)
        header = _("There are no sources to install software from")
        body = _("The file '%s' does not contain any valid "
                 "software sources." % self.file)
        self.label.set_markup("%s\n\n<small>%s</small>" % (header, body))

    def run(self):
        res = self.dialog.run()
        self.dialog.destroy()
        return res, self.new_sources

    def format_uri(self, uri):
        path = url2pathname(uri) # escape special chars
        path = path.strip('\r\n\x00') # remove \r\n and NULL
        if path.startswith('file:\\\\\\'): # windows
            path = path[8:] # 8 is len('file:///')
        elif path.startswith('file://'): #nautilus, rox
            path = path[7:] # 7 is len('file://')
        elif path.startswith('file:'): # xffm
            path = path[5:] # 5 is len('file:')
        return path

class SingleSourcesList(SourcesList):
    def __init__(self, file):
        self.matcher = SourceEntryMatcher("/usr/share/update-manager/channels/")
        self.list = []
        self.load(file)
