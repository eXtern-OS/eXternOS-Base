#!/usr/bin/env python
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
# (c) 2005-2012 Canonical, GPL
# (C) 2008-2009 Sebastian Heinlein <devel@glatzor.de>

from __future__ import print_function

from gi.repository import Gtk

from aptdaemon import client, errors
from defer import inline_callbacks
from aptdaemon.gtk3widgets import (AptCancelButton,
                                   AptConfigFileConflictDialog,
                                   AptDetailsExpander,
                                   AptMediumRequiredDialog,
                                   AptProgressBar)
from aptdaemon.enums import (EXIT_SUCCESS,
                             EXIT_FAILED,
                             STATUS_COMMITTING,
                             get_error_description_from_enum,
                             get_error_string_from_enum,
                             get_status_string_from_enum)

from UpdateManager.backend import InstallBackend
from UpdateManager.UnitySupport import UnitySupport
from UpdateManager.Dialogs import BuilderDialog

from gettext import gettext as _

import apt
import dbus
import os


class InstallBackendAptdaemon(InstallBackend, BuilderDialog):
    """Makes use of aptdaemon to refresh the cache and to install updates."""

    def __init__(self, window_main, action):
        InstallBackend.__init__(self, window_main, action)
        ui_path = os.path.join(window_main.datadir,
                               "gtkbuilder/UpdateProgress.ui")
        BuilderDialog.__init__(self, window_main, ui_path,
                               "pane_update_progress")

        self.client = client.AptClient()
        self.unity = UnitySupport()
        self._expanded_size = None
        self.button_cancel = None
        self.trans_failed_msg = None

    def close(self):
        if self.button_cancel and self.button_cancel.get_sensitive():
            try:
                self.button_cancel.clicked()
            except Exception:
                # there is not much left to do if the transaction can't be
                # canceled
                pass
            return True
        else:
            return False

    @inline_callbacks
    def update(self):
        """Refresh the package list"""
        try:
            apt.apt_pkg.pkgsystem_unlock()
        except SystemError:
            pass
        try:
            trans = yield self.client.update_cache(defer=True)
            yield self._show_transaction(trans, self.ACTION_UPDATE,
                                         _("Checking for updates…"), False)
        except errors.NotAuthorizedError:
            self._action_done(self.ACTION_UPDATE,
                              authorized=False, success=False,
                              error_string=None, error_desc=None)
        except Exception as e:
            self._action_done(self.ACTION_UPDATE,
                              authorized=True, success=False,
                              error_string=None, error_desc=None)
            raise

    @inline_callbacks
    def commit(self, pkgs_install, pkgs_upgrade, pkgs_remove):
        """Commit a list of package adds and removes"""
        try:
            apt.apt_pkg.pkgsystem_unlock()
        except SystemError:
            pass
        try:
            reinstall = purge = downgrade = []
            trans = yield self.client.commit_packages(
                pkgs_install, reinstall, pkgs_remove, purge, pkgs_upgrade,
                downgrade, defer=True)
            trans.connect("progress-changed", self._on_progress_changed)
            yield self._show_transaction(trans, self.ACTION_INSTALL,
                                         _("Installing updates…"), True)
        except errors.NotAuthorizedError as e:
            self._action_done(self.ACTION_INSTALL,
                              authorized=False, success=False,
                              error_string=None, error_desc=None)
        except errors.TransactionFailed as e:
            self.trans_failed_msg = str(e)
        except dbus.DBusException as e:
            #print(e, e.get_dbus_name())
            if e.get_dbus_name() != "org.freedesktop.DBus.Error.NoReply":
                raise
            self._action_done(self.ACTION_INSTALL,
                              authorized=False, success=False,
                              error_string=None, error_desc=None)
        except Exception as e:
            self._action_done(self.ACTION_INSTALL,
                              authorized=True, success=False,
                              error_string=None, error_desc=None)
            raise

    def _on_progress_changed(self, trans, progress):
        #print("_on_progress_changed", progress)
        self.unity.set_progress(progress)

    def _on_details_changed(self, trans, details, label_details):
        label_details.set_label(details)

    def _on_status_changed(self, trans, status, label_details, expander):
        label_details.set_label(get_status_string_from_enum(status))
        # Also resize the window if we switch from download details to
        # the terminal window
        if (status == STATUS_COMMITTING and expander and
                expander.terminal.get_visible()):
            self._resize_to_show_details(expander)

    @inline_callbacks
    def _show_transaction(self, trans, action, header, show_details):
        self.label_header.set_label(header)

        progressbar = AptProgressBar(trans)
        progressbar.show()
        self.progressbar_slot.add(progressbar)

        self.button_cancel = AptCancelButton(trans)
        if action == self.ACTION_UPDATE:
            self.button_cancel.set_label(Gtk.STOCK_STOP)
        self.button_cancel.show()
        self.button_cancel_slot.add(self.button_cancel)

        if show_details:
            expander = AptDetailsExpander(trans)
            expander.set_vexpand(True)
            expander.set_hexpand(True)
            expander.show_all()
            expander.connect("notify::expanded", self._on_expanded)
            self.expander_slot.add(expander)
            self.expander_slot.show()
        else:
            expander = None

        trans.connect("status-details-changed", self._on_details_changed,
                      self.label_details)
        trans.connect("status-changed", self._on_status_changed,
                      self.label_details, expander)
        trans.connect("finished", self._on_finished, action)
        trans.connect("medium-required", self._on_medium_required)
        trans.connect("config-file-conflict", self._on_config_file_conflict)

        yield trans.set_debconf_frontend("gnome")
        yield trans.run()

    def _on_expanded(self, expander, param):
        # Make the dialog resizable if the expander is expanded
        # try to restore a previous size
        if not expander.get_expanded():
            self._expanded_size = (expander.terminal.get_visible(),
                                   self.window_main.get_size())
            self.window_main.end_user_resizable()
        elif self._expanded_size:
            term_visible, (stored_width, stored_height) = self._expanded_size
            # Check if the stored size was for the download details or
            # the terminal widget
            if term_visible != expander.terminal.get_visible():
                # The stored size was for the download details, so we need
                # get a new size for the terminal widget
                self._resize_to_show_details(expander)
            else:
                self.window_main.begin_user_resizable(stored_width,
                                                      stored_height)
        else:
            self._resize_to_show_details(expander)

    def _resize_to_show_details(self, expander):
        """Resize the window to show the expanded details.

        Unfortunately the expander only expands to the preferred size of the
        child widget (e.g showing all 80x24 chars of the Vte terminal) if
        the window is rendered the first time and the terminal is also visible.
        If the expander is expanded afterwards the window won't change its
        size anymore. So we have to do this manually. See LP#840942
        """
        if expander.get_expanded():
            win_width, win_height = self.window_main.get_size()
            exp_width = expander.get_allocation().width
            exp_height = expander.get_allocation().height
            if expander.terminal.get_visible():
                terminal_width = expander.terminal.get_char_width() * 80
                terminal_height = expander.terminal.get_char_height() * 24
                new_width = terminal_width - exp_width + win_width
                new_height = terminal_height - exp_height + win_height
            else:
                new_width = win_width + 100
                new_height = win_height + 200
            self.window_main.begin_user_resizable(new_width, new_height)

    def _on_medium_required(self, transaction, medium, drive):
        dialog = AptMediumRequiredDialog(medium, drive, self.window_main)
        res = dialog.run()
        dialog.hide()
        if res == Gtk.ResponseType.OK:
            transaction.provide_medium(medium)
        else:
            transaction.cancel()

    def _on_config_file_conflict(self, transaction, old, new):
        dialog = AptConfigFileConflictDialog(old, new, self.window_main)
        res = dialog.run()
        dialog.hide()
        if res == Gtk.ResponseType.YES:
            transaction.resolve_config_file_conflict(old, "replace")
        else:
            transaction.resolve_config_file_conflict(old, "keep")

    def _on_finished(self, trans, status, action):
        error_string = None
        error_desc = None
        trans_failed = False
        if status == EXIT_FAILED:
            error_string = get_error_string_from_enum(trans.error.code)
            error_desc = get_error_description_from_enum(trans.error.code)
            if self.trans_failed_msg:
                trans_failed = True
                error_desc = error_desc + "\n" + self.trans_failed_msg
        # tell unity to hide the progress again
        self.unity.set_progress(-1)
        is_success = (status == EXIT_SUCCESS)
        try:
            self._action_done(action,
                              authorized=True, success=is_success,
                              error_string=error_string, error_desc=error_desc,
                              trans_failed=trans_failed)
        except TypeError:
            # this module used to be be lazily imported and in older code
            # trans_failed= is not accepted
            # TODO: this workaround can be dropped in Ubuntu 20.10
            self._action_done(action,
                              authorized=True, success=is_success,
                              error_string=error_string, error_desc=error_desc)


if __name__ == "__main__":
    import mock
    options = mock.Mock()
    data_dir = "/usr/share/update-manager"

    from UpdateManager.UpdateManager import UpdateManager
    app = UpdateManager(data_dir, options)

    b = InstallBackendAptdaemon(app, None)
    b.commit(["2vcard"], [], [])
    Gtk.main()
