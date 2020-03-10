# dialogs - provide common dialogs
#  
#  Copyright (c) 2006 FSF Europe
#              
#  Authors: 
#       Sebastian Heinlein <glatzor@ubuntu.com>
#       Michael Vogt <mvo@canonical.com>
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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

def show_error_dialog(parent, primary, secondary):
    p = "<span weight=\"bold\" size=\"larger\">%s</span>" % primary
    dialog = Gtk.MessageDialog(parent,Gtk.DialogFlags.MODAL,
                               Gtk.MessageType.ERROR,Gtk.ButtonsType.CLOSE,"")
    dialog.set_markup(p);
    dialog.format_secondary_text(secondary);
    dialog.run()
    dialog.hide()
