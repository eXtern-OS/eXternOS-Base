# dialog_edit.py.in - edit a existing repository
#  
#  Copyright (c) 2004-2005 Canonical
#                2005 Michiel Sikkes
#  
#  Authors: 
#       Michael Vogt <mvo@debian.org>
#       Michiel Sikkes <michiels@gnome.org>
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

from __future__ import print_function

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from aptsources.sourceslist import SourceEntry
from softwareproperties.gtk.utils import (
    setup_ui,
)

class DialogEdit:
  def __init__(self, parent, sourceslist, source_entry, datadir):
    self.sourceslist = sourceslist
    self.source_entry = source_entry

    # gtk stuff
    setup_ui(self, os.path.join(datadir, "gtkbuilder", "dialog-edit-source.ui"), domain="software-properties")
    self.main = self.dialog_edit
    self.main.set_transient_for(parent)
    
    # type
    if source_entry.type == "deb":
      self.combobox_type.set_active(0)
    elif source_entry.type == "deb-src":
      self.combobox_type.set_active(1)
    else:
      print("Error, unknown source type: '%s'" % source_entry.type)

    # uri
    self.entry_uri.set_text(source_entry.uri)
    self.entry_dist.set_text(source_entry.dist)

    comps = ""
    for c in source_entry.comps:
      if len(comps) > 0:
        comps = comps + " " + c
      else:
        comps = c
    self.entry_comps.set_text(comps)

    self.entry_comment.set_text(source_entry.comment)

    # finally set the signal so that the check function is not tiggered 
    # during initialisation
    for entry in (self.entry_uri, self.entry_dist, self.entry_comps, self.entry_comment):
        entry.connect("changed", self.check_line)

  def check_line(self, *args):
    """Check for a valid apt line and set the sensitiveness of the
       button 'add' accordingly"""
    line = self.get_line()
    if line == False:
      self.button_edit_ok.set_sensitive(False)
      return
    source_entry = SourceEntry(line)
    if source_entry.invalid == True:
      self.button_edit_ok.set_sensitive(False)
    else:
      self.button_edit_ok.set_sensitive(True)

  def get_line(self):
    """Collect all values from the entries and create an apt line"""
    if self.source_entry.disabled == True:
      line = "#"
    else:
      line = ""

    if self.combobox_type.get_active() == 0:
      line = "%sdeb" % line
    else:
      line = "%sdeb-src" % line

    text = self.entry_uri.get_text()
    if len(text) < 1 or text.find(" ") != -1 or text.find("#") != -1:
      return False  
    line = line + " " + self.entry_uri.get_text()

    text = self.entry_dist.get_text()
    if len(text) < 1 or text.find(" ") != -1 or text.find("#") != -1:
      return False    
    line = line + " " + self.entry_dist.get_text()

    text = self.entry_comps.get_text()
    if text.find("#") != -1:
      return False    
    elif text != "":
      line = line + " " + self.entry_comps.get_text()

    if self.entry_comment.get_text() != "":
      line = line + " #" + self.entry_comment.get_text() + "\n"
    else:
      line = line + "\n"
    return line
          
  def run(self):
      res = self.main.run()
      if res == Gtk.ResponseType.OK:
        line = self.get_line()

        # change repository
        index = self.sourceslist.list.index(self.source_entry)
        file = self.sourceslist.list[index].file
        self.new_source_entry = SourceEntry(line,file)
        self.sourceslist.list[index] = self.new_source_entry
      self.main.hide()
      return res
