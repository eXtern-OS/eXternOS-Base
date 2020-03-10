#
#  Copyright (c) 2018 Canonical
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

import gi
gi.require_version('Goa', '1.0')
from gi.repository import Gio, GLib, Goa, GObject

import logging

class GoaAuth(GObject.GObject):

    # Properties
    logged = GObject.Property(type=bool, default=False)
    username = GObject.Property(type=str, default=None)

    def __init__(self):
        GObject.GObject.__init__(self)

        self.account = None
        self.cancellable = Gio.Cancellable()
        Goa.Client.new(self.cancellable, self._on_goa_client_ready)

        self.settings = Gio.Settings.new('com.ubuntu.SoftwareProperties')
        self.settings.connect('changed::goa-account-id', self._on_settings_changed)

    def _on_goa_client_ready(self, source, res):
        try:
            self.goa_client = Goa.Client.new_finish(res)
        except GLib.Error as e:
            logging.error('Failed to get a Gnome Online Account: {}'.format(e.message))
            self.goa_client = None
        else:
            self._load()

    def login(self, account):
        assert(account)
        self._update_state(account)
        self._store()

    def logout(self):
        self._update_state(None)
        self._store()

    @GObject.Property
    def token(self):
        if self.account is None or self.goa_client is None:
            return None

        obj = self.goa_client.lookup_by_id(self.account.props.id)
        if obj is None:
            return None

        pbased = obj.get_password_based()
        if pbased is None:
            return None

        return pbased.call_get_password_sync('livepatch')

    def _update_state_from_account_id(self, account_id):
        if account_id and self.goa_client is not None:
            # Make sure the account-id is valid
            obj = self.goa_client.lookup_by_id(account_id)
            if obj is None:
                self._update_state(None)
                return

            account = obj.get_account()
            if account is None:
                self._update_state(None)
                return

            self._update_state(account)
        else:
            self._update_state(None)

    def _update_state(self, account):
        self.account = account
        if self.account is None:
            self.username = None
            self.logged = False
        else:
            try:
                account.call_ensure_credentials_sync(None)
            except Exception:
                self.username = None
                self.logged = False
            else:
                self.account.connect('notify::attention-needed', lambda o, v: self.logout())
                self.username = self.account.props.presentation_identity
                self.logged = True

    def _on_settings_changed(self, settings, key):
        self._load()

    def _load(self):
        # Retrieve the stored account-id
        account_id = self.settings.get_string('goa-account-id')
        self._update_state_from_account_id(account_id)

    def _store(self):
        # Store the account-id
        if self.logged:
            account_id = self.account.props.id
            self.settings.set_string('goa-account-id', account_id)
        else:
            self.settings.set_string('goa-account-id', "")




