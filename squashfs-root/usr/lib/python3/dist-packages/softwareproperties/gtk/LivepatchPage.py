#
#  Copyright (c) 2019 Canonical
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

import datetime
import gettext
from gettext import gettext as _
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, GObject, Gtk
import logging

from softwareproperties.GoaAuth import GoaAuth
from softwareproperties.LivepatchService import (
    LivepatchService,
    LivepatchAvailability)
from .DialogAuth import DialogAuth
from .DialogLivepatchError import DialogLivepatchError


class LivepatchPage(object):

    # Constants
    COMMON_ISSUE_URL = 'https://wiki.ubuntu.com/Kernel/Livepatch#CommonIssues'
    GENERIC_ERR_MSG = _('Canonical Livepatch has experienced an internal error.'
        ' Please refer to {} for further information.'.format(COMMON_ISSUE_URL))

    def __init__(self, parent):
        self._parent = parent

        self._timeout_handler = -1
        self._waiting_livepatch_response = False

        self._lps = LivepatchService()
        self._auth = GoaAuth()

        self._un_settings = None
        source = Gio.SettingsSchemaSource.get_default()
        if source is not None:
            schema = source.lookup('com.ubuntu.update-notifier', True)
            if schema is not None:
                settings = Gio.Settings.new('com.ubuntu.update-notifier')
                if schema.has_key('show-livepatch-status-icon'):
                    self._un_settings = settings

        # Connect signals
        self._lps.connect(
            'notify::availability', self._lps_availability_changed_cb)
        self._lps.connect(
            'notify::enabled', self._lps_enabled_changed_cb)
        self._auth.connect(
            'notify', self._auth_changed_cb)
        self._state_set_handler = self._parent.switch_livepatch.connect(
            'state-set', self._switch_state_set_cb)
        self._parent.button_livepatch_login.connect(
            'clicked', self._button_livepatch_login_clicked_cb)
        self._parent.checkbutton_livepatch_topbar.connect(
            'toggled', self._checkbutton_livepatch_topbar_toggled_cb)

        if self._un_settings is not None:
            self._un_settings_handler = self._un_settings.connect(
                'changed::show-livepatch-status-icon', self._un_settings_changed_cb)

        self._lps.trigger_availability_check()

    @property
    def waiting_livepatch_response(self):
        return self._waiting_livepatch_response

    # Private methods
    def _trigger_ui_update(self, skip=False, error_message=None):
        """Trigger the update of every single user interface component according
        to the current state.

        Args:
            skip (bool): whether to trigger the update after a small timeout.
                Defaults to False.
            error_message (str): error message to display. Defaults to None.
        """
        def do_ui_update():
            self._timeout_handler = -1

            self._update_switch()
            self._update_spinner()
            self._update_switch_label()
            self._update_auth_button()
            self._update_stack(error_message)
            self._update_topbar_checkbutton()

            return False

        if self._timeout_handler > 0:
            GObject.source_remove(self._timeout_handler)
            self._timeout_handler = -1

        if skip:
            do_ui_update()
        else:
            self._timeout_handler = GLib.timeout_add_seconds(2, do_ui_update)

    def _update_switch(self):
        """Update the state of the on/off switch."""
        switch = self._parent.switch_livepatch

        availability = self._lps.props.availability
        enabled = self._lps.props.enabled
        logged = self._auth.logged

        switch.set_sensitive(
            availability == LivepatchAvailability.TRUE and
            (enabled or logged))

        if self._waiting_livepatch_response:
            return

        self._parent.switch_livepatch.handler_block(self._state_set_handler)
        switch.set_state(switch.get_sensitive() and enabled)
        self._parent.switch_livepatch.handler_unblock(self._state_set_handler)

    def _update_spinner(self):
        """Update the state of the in-progress spinner."""
        spinner = self._parent.spinner_livepatch
        availability = self._lps.props.availability

        spinner.set_visible(availability == LivepatchAvailability.CHECKING)
        spinner.props.active = (availability == LivepatchAvailability.CHECKING)

    def _update_switch_label(self):
        """Update the text of the label next to the on/off switch."""
        availability = self._lps.props.availability
        logged = self._auth.logged

        if availability == LivepatchAvailability.CHECKING:
            msg = _('Checking availability…')
        elif availability == LivepatchAvailability.NO_CONNECTIVITY:
            msg = _('Livepatch requires an Internet connection.')
        elif availability == LivepatchAvailability.FALSE:
            msg = _('Livepatch is not available for this system.')
        else:
            if self._parent.switch_livepatch.get_active():
                msg = _("Livepatch is on.")
            elif not logged:
                msg = _("To use Livepatch you need to sign in.")
            else:
                msg = _("Livepatch is off.")

        self._parent.label_livepatch_switch.set_label(msg)

    def _update_auth_button(self):
        """Update the state and the label of the authentication button."""
        button = self._parent.button_livepatch_login

        availability = self._lps.props.availability
        logged = self._auth.logged

        button.set_visible(
            availability == LivepatchAvailability.TRUE and
            not self._parent.switch_livepatch.get_active())
        button.set_label(_('Sign Out') if logged else _('Sign In…'))

    def _update_stack(self, error_message):
        """Update the state of the stack.

        If livepatch is not available nothing will be shown, if an error
        occurred an error message will be shown in a text view, otherwise the
        current livepatch status (e.g. a list of CVE fixes) will be shown.

        Args:
            error_message (str): error message to display.
        """
        availability = self._lps.props.availability
        availability_message = self._lps.props.availability_message

        has_error = (
            error_message is not None or
            (availability == LivepatchAvailability.FALSE and
             availability_message is not None))

        if has_error:
            self._parent.stack_livepatch.set_visible_child_name('page_livepatch_message')
            self._parent.stack_livepatch.set_visible(True)
            text_buffer = self._parent.textview_livepatch.get_buffer()
            text_buffer.delete(
                text_buffer.get_start_iter(), text_buffer.get_end_iter())
            text_buffer.insert_markup(
                text_buffer.get_end_iter(),
                error_message or availability_message, -1)
            return

        if availability == LivepatchAvailability.CHECKING or not self._parent.switch_livepatch.get_active():
            self._parent.stack_livepatch.set_visible(False)
        else:
            self._update_status()

    def _update_topbar_checkbutton(self):
        """Update the state of the checkbutton to show/hide Livepatch status in
        the top bar.
        """
        visibile = self._un_settings is not None
        self._parent.checkbutton_livepatch_topbar.set_visible(visibile)

        if visibile:
            availability = self._lps.props.availability

            self._parent.checkbutton_livepatch_topbar.set_sensitive(
                availability == LivepatchAvailability.TRUE and
                self._lps.props.enabled)
            self._parent.checkbutton_livepatch_topbar.set_active(
                availability == LivepatchAvailability.TRUE and
                self._lps.props.enabled and
                self._un_settings.get_boolean('show-livepatch-status-icon'))

    def _format_timedelta(self, td):
        days = td.days
        hours = td.seconds // 3600
        minutes = td.seconds // 60

        if days > 0:
            return gettext.ngettext(
                    '({} day ago)',
                    '({} days ago)',
                    days).format(days)
        elif hours > 0:
            return gettext.ngettext(
                    '({} hour ago)',
                    '({} hours ago)',
                    hours).format(hours)
        elif minutes > 0:
            return gettext.ngettext(
                    '({} minute ago)',
                    '({} minutes ago)',
                    minutes).format(minutes)
        else:
            return ''

    def _datetime_to_str(self, dt):
        gdt = GLib.DateTime.new_from_unix_utc(dt.timestamp())
        td = datetime.datetime.now(dt.tzinfo) - dt
        return '{} {}'.format(
            gdt.to_local().format('%x %H:%M'),
            self._format_timedelta(td))

    def _update_status(self):
        """Populate the UI to reflect the Livepatch status"""
        status = self._lps.get_status()

        if status is None:
            if not self._waiting_livepatch_response:
                self._trigger_ui_update(skip=True, error_message=_('Failed to retrieve Livepatch status.'))
                return

        self._parent.stack_livepatch.set_visible_child_name('page_livepatch_status')
        self._parent.stack_livepatch.set_visible(True)

        check_state = status['Status'][0]['Livepatch']['CheckState'] if status else None
        state = status['Status'][0]['Livepatch']['State'] if status else None

        if check_state == 'check-failed':
            self._trigger_ui_update(skip=True, error_message=self.GENERIC_ERR_MSG)
            return

        if state in ['applied-with-bug', 'apply-failed', 'unknown']:
            self._trigger_ui_update(skip=True, error_message=self.GENERIC_ERR_MSG)
            return

        self._parent.label_livepatch_last_update.set_label(
                _("Last check for updates: {}").format(
                    self._datetime_to_str(status['Last-Check']) if status else _('None yet')))

        if state in ['unapplied', 'nothing-to-apply'] or state == None:
            self._parent.label_livepatch_header.set_label(_('No updates currently applied.'))
            self._parent.scrolledwindow_livepatch_fixes.set_visible(False)
        elif state == 'applied':
            self._parent.label_livepatch_header.set_label(_('Updates currently applied:'))
            self._parent.scrolledwindow_livepatch_fixes.set_visible(True)
            self._update_fixes(status['Status'][0]['Livepatch']['Fixes'])
        else:
            logging.warning('Livepatch status contains an invalid state: {}'.format(state))

        if check_state == 'needs-check' or state == 'unapplied' or state == 'applying':
            self._trigger_ui_update()

    def _update_fixes(self, fixes):
        """Populate the UI to show the list of applied CVE fixes."""
        treeview = self._parent.treeview_livepatch
        liststore = treeview.get_model()
        liststore.clear()

        for fix in fixes:
            fix_iter = liststore.append()
            liststore.set(fix_iter, [0], [self._format_fix(fix)])

    def _format_fix(self, fix):
        """Format a fix in a UI friendly text."""
        return '<b>{}</b>\n{}'.format(
            fix['Name'], fix['Description'].replace('\n', ' '))

    def _do_login(self):
        """Start the authentication flow to retrieve the livepatch token."""
        dialog = DialogAuth(self._parent.window_main, self._parent.datadir)

        if dialog.run() == Gtk.ResponseType.OK:
            self._auth.login(dialog.account)
            self._parent.switch_livepatch.set_state(True)

    def _do_logout(self):
        """Start the de-authentication flow."""
        self._auth.logout()

    # Signals handler
    def _lps_availability_changed_cb(self, o, v):
        self._trigger_ui_update(skip=True)

    def _lps_enabled_changed_cb(self, o, v):
        if self._waiting_livepatch_response:
            return
        self._trigger_ui_update(skip=False)

    def _auth_changed_cb(self, o, v):
        self._trigger_ui_update(skip=True)

    def _switch_state_set_cb(self, widget, state):
        if not self._waiting_livepatch_response:
            self._waiting_livepatch_response = True

            token = self._auth.token or ''
            self._parent.backend.SetLivepatchEnabled(
                state, token,
                reply_handler=self._enabled_reply_handler,
                error_handler=self._enabled_error_handler,
                timeout=1200)

        self._trigger_ui_update(skip=True)
        self._parent.switch_livepatch.set_state(state)

        return False

    def _button_livepatch_login_clicked_cb(self, button):
        if self._auth.logged:
            self._do_logout()
        else:
            self._do_login()

    def _checkbutton_livepatch_topbar_toggled_cb(self, button):
        if not button.get_sensitive():
            return
        self._un_settings.handler_block(self._un_settings_handler)
        self._un_settings.set_boolean('show-livepatch-status-icon', button.get_active())
        self._un_settings.handler_unblock(self._un_settings_handler)


    def _un_settings_changed_cb(self, settings, key):
        self._trigger_ui_update(skip=True)

    def _show_error_dialog(self, message):
        dialog = DialogLivepatchError(
            self._parent.window_main,
            self._parent.datadir)

        response = dialog.run(
            error=message,
            show_settings_button=not self._parent.window_main.is_visible())

        if response == DialogLivepatchError.RESPONSE_SETTINGS:
            self._parent.window_main.show()
            self._parent.notebook_main.set_current_page(6)
        elif not self._parent.window_main.is_visible():
            self._parent.on_close_button(None)

    # DBus replay handlers
    def _enabled_reply_handler(self, is_error, prompt):
        if self._parent.switch_livepatch.get_active() == self._lps.props.enabled:
            self._waiting_livepatch_response = False
            self._trigger_ui_update(skip=True)

            if not self._parent.window_main.is_visible():
                self._parent.on_close_button(None)
        else:
            if is_error:
                self._waiting_livepatch_response = False
                self._trigger_ui_update(skip=True)
                self._show_error_dialog(prompt)
            else:
                # The user tooggled on/off the switch while we were waiting
                # livepatch to respond back.
                token = self._auth.token or ''
                self._parent.backend.SetLivepatchEnabled(
                    self._parent.switch_livepatch.get_active(),
                    token,
                    reply_handler=self._enabled_reply_handler,
                    error_handler=self._enabled_error_handler,
                    timeout=1200)

    def _enabled_error_handler(self, e):
        self._waiting_livepatch_response = False
        self._trigger_ui_update(skip=True)

        if e._dbus_error_name == 'com.ubuntu.SoftwareProperties.PermissionDeniedByPolicy':
            logging.warning("Authentication canceled, changes have not been saved")

            if not self._parent.window_main.is_visible():
                self._parent.on_close_button(None)
        else:
            self._show_error_dialog(str(e))
