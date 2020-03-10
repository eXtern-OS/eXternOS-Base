# dialog_cache_outdated.py - inform the user to update the apt cache
#  
#  Copyright (c) 2006 Canonical
#  
#  Authors: 
#       Sebastian Heinlein <sebastian.heinlein@web.de>
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

import aptdaemon.client
import aptdaemon.enums
from aptdaemon.gtk3widgets import AptErrorDialog, AptProgressDialog

from softwareproperties.gtk.utils import (
    setup_ui,
)


class DialogCacheOutdated:
    def __init__(self, parent, datadir):
        """setup up the gtk dialog"""
        self.parent = parent

        setup_ui(self, os.path.join(datadir, "gtkbuilder", "dialog-cache-outofdate.ui"), domain="software-properties")
        self.dialog = self.dialog_cache_outofdate
        self.dialog.set_transient_for(parent)

    def _run_transaction(self, transaction):
        transaction.connect('finished', self._on_transaction_done)
        dia = AptProgressDialog(transaction) #parent=self.parent.get_window())
        dia.run(close_on_finished=True, show_error=True,
                reply_handler=lambda: True,
                error_handler=self._on_error)

    def _on_transaction_done(self, transaction, exit_state):
        self.loop.quit()

    def _on_error(self, error):
        try:
            raise error
        except aptdaemon.errors.NotAuthorizedError:
            # Silently ignore auth failures
            return
        except aptdaemon.errors.TransactionFailed as _error:
            error = _error
        except Exception as _error:
            error = aptdaemon.errors.TransactionFailed(aptdaemon.enums.ERROR_UNKNOWN,
                                                       str(_error))
        dia = AptErrorDialog(error)
        dia.run()
        dia.hide()

    def run(self):
        """run the dialog, and if reload was pressed run cache update"""
        res = self.dialog.run()
        self.dialog.hide()
        if res == Gtk.ResponseType.APPLY:
            self.loop = GObject.MainLoop()

            ac = aptdaemon.client.AptClient()
            ac.update_cache(reply_handler=self._run_transaction,
                            error_handler=self._on_error)

            self.parent.set_sensitive(False)
            self.loop.run()
            self.parent.set_sensitive(True)

        return res
