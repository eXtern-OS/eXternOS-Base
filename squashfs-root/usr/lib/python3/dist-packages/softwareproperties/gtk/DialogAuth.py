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

from enum import IntEnum
import os

from gettext import gettext as _
from softwareproperties.gtk.utils import (
    setup_ui,
)

import gi
gi.require_version('Goa', '1.0')
from gi.repository import Gio, GLib, Goa, Gtk
import logging

class Column(IntEnum):
    ID = 0
    MAIL = 1
    ACCOUNT = 2

class DialogAuth:

    def __init__(self, parent, datadir):
        """setup up the gtk dialog"""
        self.parent = parent

        setup_ui(self, os.path.join(datadir, "gtkbuilder", "dialog-auth.ui"),
            domain="software-properties")

        self.dialog = self.dialog_auth
        self.dialog.set_title('')
        self.dialog.set_deletable(False)
        self.dialog.set_transient_for(parent)

        self.button_continue.grab_focus()

        self.account = None
        self.dispose_on_new_account = False
        self.goa_client = Goa.Client.new_sync(None)

        self._setup_model()
        self._check_ui(select=False)

        # Be ready to other accounts
        self.goa_client.connect('account-added', self._account_added_cb)
        self.goa_client.connect('account-removed', self._account_removed_cb)

    def run(self):
        res = self.dialog.run()
        self.dialog.hide()
        return res

    def _setup_model(self):
        for obj in self.goa_client.get_accounts():
            self._add_account(obj.get_account(), select=False)

    def _set_header(self, label):
        self.label_header.set_markup(
            "<span size='larger' weight='bold'>%s</span>" % label)

    def _check_ui(self, select):
        naccounts = len(self.liststore_account)

        if naccounts == 0:
            self._set_header(
                _('To use Livepatch, you need to use an Ubuntu One account.'))
            self.combobox_account.set_visible(False)
            self.label_account.set_visible(False)
            self.button_add_another.set_visible(False)
            self.button_continue.set_label(_('Sign In / Register…'))
        elif naccounts == 1:
            self._set_header(
                _('To use Livepatch, you need to use your Ubuntu One account.'))
            self.combobox_account.set_visible(False)
            self.label_account.set_visible(True)
            self.label_account.set_text(self.liststore_account[0][Column.MAIL])
            self.button_add_another.set_visible(True)
            self.button_continue.set_label(_('Continue'))
        else:
            self._set_header(
                _('To use Livepatch, you need to use an Ubuntu One account.'))
            self.button_add_another.set_visible(True)
            self.combobox_account.set_visible(True)
            self.label_account.set_visible(False)
            self.button_continue.set_label(_('Use'))
            if select:
                self.combobox_account.set_active(naccounts-1)
            elif self.combobox_account.get_active() == -1:
                self.combobox_account.set_active(0)

    def _ignore_account(self, account):
        return account.props.provider_type != 'ubuntusso'

    def _get_account_iter(self, account):
        row = self.liststore_account.get_iter_first()
        while row is not None:
            account_id =  self.liststore_account.get_value(row, Column.ID)
            if account_id == account.props.id:
                return row
            row = self.liststore_account.iter_next(row)
        return None

    def _add_account(self, account, select):
        if self._ignore_account(account):
            return

        account_iter = self._get_account_iter(account)
        if account_iter is not None:
            return

        account_iter = self.liststore_account.append()
        self.liststore_account.set(account_iter,
            [Column.ID, Column.MAIL, Column.ACCOUNT],
            [account.props.id, account.props.presentation_identity, account])
        self._check_ui(select)

    def _remove_account(self, account):
        if self._ignore_account(account):
            return

        account_iter = self._get_account_iter(account)
        if account_iter is None:
            return

        self.liststore_account.remove(account_iter)
        self._check_ui(select=False)

    def _response_if_valid(self, account):
        def cb(source, res, data):
            try:
                source.call_ensure_credentials_finish(res)
                valid = True
            except GLib.Error as e:
                logging.warning("call_ensure_credentials_finish exception: %s",
                   e.message)
                valid = False
            
            if not valid:
                try:
                    self._spawn_goa_with_args(account.props.id, None)
                except GLib.Error as e:
                    logging.warning ('Failed to spawn gnome-control-center: %s',
                        e.message)
            else:
                self.account = account
                self.dialog.response(Gtk.ResponseType.OK)

        account.call_ensure_credentials(None, cb, None)

    def _build_dbus_params(self, action, arg):
        builder = GLib.VariantBuilder.new(GLib.VariantType.new('av'))

        if action is None and arg is None:
            s = GLib.Variant.new_string('')
            v = GLib.Variant.new_variant(s)
            builder.add_value(v)
        else:
            if action is not None:
                s = GLib.Variant.new_string(action)
                v = GLib.Variant.new_variant(s)
                builder.add_value(v)
            if arg is not None:
                s = GLib.Variant.new_string(arg)
                v = GLib.Variant.new_variant(s)
                builder.add_value(v)

        array = GLib.Variant.new_tuple(
            GLib.Variant.new_string('online-accounts'), builder.end())
        array = GLib.Variant.new_variant(array)

        param = GLib.Variant.new_tuple(
            GLib.Variant.new_string('launch-panel'),
            GLib.Variant.new_array(GLib.VariantType.new('v'), [array]),
            GLib.Variant.new_array(GLib.VariantType.new('{sv}'), None))
        return param

    def _spawn_goa_with_args(self, action, arg):
        proxy = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE, None,
            'org.gnome.ControlCenter',
            '/org/gnome/ControlCenter',
            'org.gtk.Actions', None)

        param = self._build_dbus_params(action, arg)
        proxy.call_sync('Activate', param, Gio.DBusCallFlags.NONE, -1, None)

    def _account_added_cb(self, goa_client, goa_object):
        account = goa_object.get_account()
        if self._ignore_account(account):
            return
        if not self.dispose_on_new_account:
            self._add_account(account, True)
        else:
            self._response_if_valid(account)

    def _account_removed_cb(self, goa_client, goa_object):
        account = goa_object.get_account()
        if not self._ignore_account(account):
            self._remove_account(account)

    def _button_add_another_clicked_cb(self, button):
        try:
            # There is no easy way to put this to false if the user close the
            # windows without adding an account.
            self._spawn_goa_with_args('add', 'ubuntusso')
            self.dispose_on_new_account = True
        except GLib.Error as e:
            logging.warning ('Failed to spawn control-center: %s', e.message)

    def _button_cancel_clicked_cb(self, button):
        self.dialog.response(Gtk.ResponseType.CANCEL)

    def _button_continue_clicked_cb(self, button):
        naccounts = len(self.liststore_account)

        account = None
        if naccounts >= 1:
            active_index = self.combobox_account.get_active()
            account = self.liststore_account[active_index][Column.ACCOUNT]

        if account is None:
            self._button_add_another_clicked_cb(self.button_add_another)
        else:
            self._response_if_valid(account)
