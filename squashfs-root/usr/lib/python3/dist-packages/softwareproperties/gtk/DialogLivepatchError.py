#
#  Copyright (c) 2017-2019 Canonical
#
#  Authors:
#       Andrea Azzarone <andrea.azzarone@canonical.com>
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

from gettext import gettext as _

from softwareproperties.gtk.utils import (
    setup_ui,
)


class DialogLivepatchError:

    RESPONSE_SETTINGS = 100
    RESPONSE_IGNORE = 101

    primary = _("Sorry, there's been a problem with setting up Canonical Livepatch.")

    def __init__(self, parent, datadir):
        """setup up the gtk dialog"""
        self.parent = parent

        setup_ui(
            self,
            os.path.join(datadir, "gtkbuilder", "dialog-livepatch-error.ui"),
            domain="software-properties")

        self.dialog = self.messagedialog_livepatch
        self.dialog.set_transient_for(parent)

    def run(self, error, show_settings_button):
        p = "<span weight=\"bold\" size=\"larger\">{}</span>".format(self.primary)
        self.label_primary.set_markup(p)

        textbuffer = self.treeview_message.get_buffer()
        textbuffer.set_text(error)

        self.button_settings.set_visible(show_settings_button)
        res = self.dialog.run()
        self.dialog.hide()
        return res

    def on_button_settings_clicked(self, b, d=None):
        self.dialog.response(self.RESPONSE_SETTINGS)

    def on_button_ignore_clicked(self, b, d=None):
        self.dialog.response(self.RESPONSE_IGNORE)
