#  GtkCdomProgress - add a cdrom to the apt sources
#
#  Copyright (c) 2004-2007 Canonical Ltd.
#                2004-2005 Michiel Sikkes
#
#  Author: Michael Vogt <mvo@debian.org>
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

import apt
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gettext import gettext as _

from softwareproperties.gtk.utils import (
  setup_ui,
)


class CdromProgress(apt.progress.base.CdromProgress):
  def __init__(self, datadir, parent):
    # gtk stuff
    setup_ui(self, os.path.join(datadir, "gtkbuilder", "dialog-cdrom-progress.ui"), domain="software-properties")
    
    self.dialog_cdrom_progress.show()
    self.dialog_cdrom_progress.set_transient_for(parent)
    self.parent = parent
    self.button_cdrom_close.set_sensitive(False)
    
  def update(self, text, step):
    """ update is called regularly so that the gui can be redrawn """
    if step > 0:
      self.progressbar_cdrom.set_fraction(step/float(self.totalSteps))
      if step == self.totalSteps:
        self.button_cdrom_close.set_sensitive(True)
    if text != "":
      self.label_cdrom.set_text(text)
    while Gtk.events_pending():
      Gtk.main_iteration()
  def askCdromName(self):
    dialog = Gtk.MessageDialog(parent=self.dialog_cdrom_progress,
                               flags=Gtk.DialogFlags.MODAL,
                               type=Gtk.MessageType.QUESTION,
                               buttons=Gtk.ButtonsType.OK_CANCEL,
                               message_format=None)
    dialog.set_markup(_("Please enter a name for the disc"))
    entry = Gtk.Entry()
    entry.show()
    dialog.vbox.pack_start(entry, True, True, 0)
    res = dialog.run()
    dialog.destroy()
    if res == Gtk.ResponseType.OK:
      name = entry.get_text()
      return (True,name)
    return (False,"")
  def changeCdrom(self):
    dialog = Gtk.MessageDialog(parent=self.dialog_cdrom_progress,
                               flags=Gtk.DialogFlags.MODAL,
                               type=Gtk.MessageType.QUESTION,
                               buttons=Gtk.ButtonsType.OK_CANCEL,
                               message_format=None)
    dialog.set_markup(_("Please insert a disk in the drive:"))
    dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
    res = dialog.run()
    dialog.destroy()
    if res == Gtk.ResponseType.OK:
      return True
    return False
