# dialog_add.py.in - dialog to add a new repository
#  
#  Copyright (c) 2006 FSF Europe
#              
#  Authors: 
#       Sebastian Heinlein <glatzor@ubuntu.com>
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

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gtk
from gettext import gettext as _
import threading
import re
import sys

import softwareproperties.gtk.dialogs as dialogs
from softwareproperties.MirrorTest import MirrorTest
from softwareproperties.gtk.utils import (
    setup_ui,
)


(COLUMN_PROTO, COLUMN_DIR) = list(range(2))
(COLUMN_URI, COLUMN_SEPARATOR, COLUMN_CUSTOM, COLUMN_MIRROR) = list(range(4))

from softwareproperties.CountryInformation import CountryInformation

if sys.version >= '3':
    cmp = lambda a, b: (a > b) - (a < b)

def sort_mirrors(model, iter1, iter2, data=None):
      """ sort function for the mirror list:
           - at first show all custom urls
           - secondly the separator
           - show mirrors without a county first (e.g. the automatic mirror url)
           - third the official mirrors. if available
             sort the countries
      """

      #FIXME: comparison operators seem to prefer ASCII chars
      (url1, sep1, custom1, mirror1) = model.get(iter1, 0, 1, 2, 3)
      (url2, sep2, custom2, mirror2) = model.get(iter2, 0, 1, 2, 3)
      has_child1 = model.iter_has_child(iter1)
      has_child2 = model.iter_has_child(iter2)
      if custom1 and custom2:
          return cmp(url1, url2)
      elif custom1:
          return -1
      elif custom2:
          return 1
      if sep1:
          return -1
      elif sep2:
          return 1
      if has_child1 != has_child2:
            return cmp(has_child1, has_child2)
      return cmp(url1, url2)

class DialogMirror:

  def __init__(self, parent, datadir, distro, custom_mirrors):
    """
    Initialize the dialog that allows to choose a custom or official mirror
    """
    def is_separator(model, iter, data=None):
        return model.get_value(iter, COLUMN_SEPARATOR)

    self.custom_mirrors = custom_mirrors
    self.country_info = CountryInformation()

    setup_ui(self, os.path.join(datadir, "gtkbuilder", "dialog-mirror.ui"), domain="software-properties")
    
    self.dialog = self.dialog_mirror
    self.dialog.set_transient_for(parent)
    
    self.dialog_test = self.dialog_mirror_test
    self.dialog_test.set_transient_for(self.dialog)
    self.distro = distro
    self.treeview = self.treeview_mirrors
    self.button_edit = self.button_mirror_edit
    self.button_remove = self.button_mirror_remove
    self.button_choose = self.button_mirror_choose
    self.button_cancel = self.button_test_cancel
    self.label_test = self.label_test_mirror
    self.progressbar_test = self.progressbar_test_mirror
    self.combobox = self.combobox_mirror_proto
    self.progress = self.progressbar_test_mirror
    self.label_action = self.label_test_mirror

    # store each proto and its dir
    model_proto = Gtk.ListStore(GObject.TYPE_STRING,
                                GObject.TYPE_STRING)
    self.combobox.set_model(model_proto)
    cr = Gtk.CellRendererText()
    self.combobox.pack_start(cr, True)
    self.combobox.add_attribute(cr, "markup", 0)

    self.model = Gtk.TreeStore(GObject.TYPE_STRING,  # COLUMN_URI
                               GObject.TYPE_BOOLEAN, # COLUMN_SEPARATOR
                               GObject.TYPE_BOOLEAN, # COLUMN_CUSTOM
                               GObject.TYPE_PYOBJECT)# COLUMN_MIRROR
    self.treeview.set_row_separator_func(is_separator, None)
    self.model_sort = Gtk.TreeModelSort(model=self.model)

    self.distro = distro

    self.treeview.set_model(self.model_sort)
    # the cell renderer for the mirror uri
    self.renderer_mirror = Gtk.CellRendererText()
    self.renderer_mirror.connect('edited', 
                                 self.on_edited_custom_mirror, 
                                 self.model)
    # the visible column that holds the mirror uris
    self.column_mirror = Gtk.TreeViewColumn("URI", 
                                            self.renderer_mirror, 
                                            text=COLUMN_URI)
    self.treeview.append_column(self.column_mirror)

    # used to find the corresponding iter of a location
    map_loc = {}
    patriot = None
    model = self.treeview.get_model().get_model()
    # at first add all custom mirrors and a separator
    if len(self.custom_mirrors) > 0:
        for mirror in self.custom_mirrors:
            model.append(None, [mirror, False, True, None])
            self.column_mirror.add_attribute(self.renderer_mirror, 
                                             "editable", 
                                             COLUMN_CUSTOM)
        model.append(None, [None, True, False, None])
    # secondly add all official mirrors
    for hostname in self.distro.source_template.mirror_set.keys():
        mirror = self.distro.source_template.mirror_set[hostname]
        if mirror.location in map_loc:
            model.append(map_loc[mirror.location],
                         [hostname, False, False, mirror])
        elif mirror.location != None:
            parent = model.append(None, 
                                  [self.country_info.get_country_name(mirror.location), False, False, None])
            if mirror.location == self.country_info.code and patriot == None:
                patriot = parent
            model.append(parent, [hostname, False, False, mirror]),
            map_loc[mirror.location] = parent
        else:
            model.append(None, [hostname, False, False, mirror])
    # Scroll to the local mirror set
    if patriot != None:
        path_sort = self.model_sort.get_path(self.model_sort.convert_child_iter_to_iter(patriot)[1])
        self.treeview.expand_row(path_sort, False)
        self.treeview.set_cursor(path_sort, None, False)
        self.treeview.scroll_to_cell(path_sort, use_align=True, row_align=0.5)
    # set the sort function, this will also trigger a sort
    self.model_sort.set_default_sort_func(sort_mirrors, None)

  def on_edited_custom_mirror(self, cell, path, new_text, model):
    ''' Check if the new mirror uri is faild, if yes change it, if not
        remove the mirror from the list '''
    iter = model.get_iter(path)
    iter_next = model.iter_next(iter)
    if new_text != "":
        model.set_value(iter, COLUMN_URI, new_text)
        # Add a separator if the next mirror is a not a separator or 
        # a custom one
        if iter_next != None and not \
           (model.get_value(iter_next, COLUMN_SEPARATOR) or \
            model.get_value(iter_next, COLUMN_CUSTOM)):
            model.insert(1, [None, True, False])
        self.button_choose.set_sensitive(self.is_valid_mirror(new_text))
    else:
        model.remove(iter)
        # Remove the separator if this was the last custom mirror
        if model.get_value(model.get_iter_first(), COLUMN_SEPARATOR):
            model.remove(model.get_iter_first())
        self.treeview.set_cursor((0,))
    return

  def is_valid_mirror(self, uri):
    ''' Check if a given uri is a vaild one '''
    if uri == None:
        return False
    elif re.match("^((ftp)|(http)|(file)|(rsync)|(https))://([a-z]|[A-Z]|[0-9]|:|/|\.|~)+$", uri) == None:
        return False
    else:
        return True

  def on_treeview_mirrors_cursor_changed(self, treeview, data=None):
    ''' Check if the currently selected row in the mirror list
        contains a mirror and or is editable '''
    (row, column) = treeview.get_cursor()
    if row == None:
        self.button_remove.set_sensitive(False)
        self.button_edit.set_sensitive(False)
        self.button_choose.set_sensitive(False)
        return
    model = treeview.get_model()
    iter = model.get_iter(row)
    # Update the list of available protocolls
    mirror = model.get_value(iter, COLUMN_MIRROR)
    model_protos = self.combobox.get_model()
    model_protos.clear()
    if mirror != None:
        self.combobox.set_sensitive(True)
        seen_protos = []
        for repo in mirror.repositories:
            # Only add a repository for a protocoll once
            if repo.proto in seen_protos:
                continue
            seen_protos.append(repo.proto)
            model_protos.append(repo.get_info())
        self.combobox.set_active(0)
        self.button_choose.set_sensitive(True)
    else:
        # Allow to edit and remove custom mirrors
        self.button_remove.set_sensitive(model.get_value(iter, COLUMN_CUSTOM))
        self.button_edit.set_sensitive(model.get_value(iter, COLUMN_CUSTOM))
        self.button_choose.set_sensitive(self.is_valid_mirror(model.get_value(iter, COLUMN_URI)))
        self.combobox.set_sensitive(False)

  def on_button_mirror_remove_clicked(self, button, data=None):
    ''' Remove the currently selected mirror '''
    path, column = self.treeview.get_cursor()
    iter = self.treeview.get_model().get_iter(path)
    model = self.treeview.get_model().get_model()
    model.remove(iter)
    # Remove the separator if this was the last custom mirror
    if model.get_value(model.get_iter_first(), COLUMN_SEPARATOR):
        model.remove(model.get_iter_first())
    self.treeview.set_cursor((0,))

  def on_button_mirror_add_clicked(self, button, data=None):
    ''' Add a new mirror at the beginning of the list and start
        editing '''
    model = self.treeview.get_model().get_model()
    model.append(None, [_("New mirror"), False, True, None])
    self.treeview.grab_focus()
    self.treeview.set_cursor((0,),
                             focus_column=self.column_mirror, 
                             start_editing=True)

  def on_button_mirror_edit_clicked(self, button, data=None):
    ''' Grab the focus and start editing the currently selected mirror '''
    path, column = self.treeview.get_cursor()
    self.treeview.grab_focus()
    self.treeview.set_cursor(path, focus_column=column, start_editing=True)

  def on_dialog_mirror_test_delete_event(self, dialog, event, data=None):
    ''' If anybody wants to close the dialog, stop the test before '''
    self.on_button_cancel_test_clicked(None)
    return True

  def run(self):
    ''' Run the chooser dialog and return the chosen mirror or None '''
    res = self.dialog.run()
    self.dialog.hide()

    (row, column) = self.treeview.get_cursor()
    if not row:
        return None

    model = self.treeview.get_model()
    iter = model.get_iter(row)
    mirror = model.get_value(iter, COLUMN_MIRROR)

    # FIXME: we should also return the list of custom servers
    if res == Gtk.ResponseType.OK:
        if mirror == None:
            # Return the URL of the selected custom mirror
            return model.get_value(iter, COLUMN_URI)
        else:
            # Return an URL created from the hostname and the selected
            # repository
            model_proto = self.combobox.get_model()
            iter_proto = model_proto.get_iter(self.combobox.get_active())
            proto = model_proto.get_value(iter_proto, COLUMN_PROTO)
            dir = model_proto.get_value(iter_proto, COLUMN_DIR)
            return "%s://%s/%s" % (proto, mirror.hostname, dir)
    else:
        return None

  def on_button_test_clicked(self, button, data=None):
    ''' Perform a test to find the best mirror and select it 
        afterwards in the treeview '''
    self.button_cancel.set_sensitive(True)
    self.dialog_test.show()
    self.running = threading.Event()
    self.running.set()
    progress_update = threading.Event()
    pipe = os.popen("dpkg --print-architecture")
    arch = pipe.read().strip()
    test_file = "dists/%s/%s/binary-%s/Packages.gz" % \
                 (self.distro.source_template.name,
                  self.distro.source_template.components[0].name,
                  arch)
    test = MirrorTest(list(self.distro.source_template.mirror_set.values()),
                         test_file,
                         progress_update,
                         self.running)
    test.start()

    # now run the tests in a background thread, and update the UI on each event
    while self.running.is_set():
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)

        # don't spin the CPU until there's something to update; but update the
        # UI at least every 100 ms
        progress_update.wait(0.1)

        if progress_update.is_set():
            self.progress.set_text(_("Completed %s of %s tests") % \
                                   (test.progress[0], test.progress[1]))
            self.progress.set_fraction(test.progress[2])
            progress_update.clear()
    self.dialog_test.hide()
    self.label_test.set_label("")
    # Select the mirror in the list or show an error dialog
    if test.best != None:
        self.model_sort.foreach(self.select_mirror, test.best)
    else:
        dialogs.show_error_dialog(self.dialog, 
                                  _("No suitable download server was found"),
                                  _("Please check your Internet connection."))

  def select_mirror(self, model, path, iter, mirror):
    """Select and expand the path to a matching mirror in the list"""
    if model.get_value(iter, COLUMN_URI) == mirror:
        self.treeview.expand_to_path(path)
        self.treeview.set_cursor(path, None, False)
        self.treeview.scroll_to_cell(path, use_align=True, row_align=0.5)
        self.treeview.grab_focus()
        # breaks foreach
        return True

  def on_button_cancel_test_clicked(self, button):
    ''' Abort the mirror performance test '''
    self.running.clear()
    self.label_test.set_label("<i>%s</i>" % _("Canceling..."))
    self.button_cancel.set_sensitive(False)
    self.progressbar_test.set_fraction(1)
