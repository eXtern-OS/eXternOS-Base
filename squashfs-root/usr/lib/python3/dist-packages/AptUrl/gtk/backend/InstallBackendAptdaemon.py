#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2005-2009 Canonical, GPL

from aptdaemon import client, errors
from defer import inline_callbacks
from aptdaemon.gtk3widgets import AptProgressDialog
from aptdaemon.enums import EXIT_SUCCESS

from UpdateManager.backend import InstallBackend
from UpdateManager.UnitySupport import UnitySupport

import apt_pkg
import dbus

class InstallBackendAptdaemon(InstallBackend):

    """Makes use of aptdaemon to refresh the cache and to install updates."""

    def __init__(self, window_main):
        # Pass None for datadir because of LP: #1026257
        InstallBackend.__init__(self, window_main, self.ACTION_INSTALL)
        self.client = client.AptClient()
        self.unity = UnitySupport()

    @inline_callbacks
    def update(self):
        """Refresh the package list"""
        try:
            apt_pkg.pkgsystem_unlock()
        except SystemError:
            pass
        try:
            trans = yield self.client.update_cache(defer=True)
            yield self._run_in_dialog(trans, self.ACTION_UPDATE)
        except errors.NotAuthorizedError as e:
            self._action_done(self.ACTION_UPDATE, False, False, str(e), None)
        except:
            self.action_done(self.ACTION_UPDATE, True, False, None, None)
            raise

    @inline_callbacks
    def commit(self, pkgs_install, pkgs_upgrade, close_on_done):
        """Commit a list of package adds and removes"""
        try:
            apt_pkg.pkgsystem_unlock()
        except SystemError:
            pass
        try:
            reinstall = remove = purge = downgrade = []
            trans = yield self.client.commit_packages(
                pkgs_install, reinstall, remove, purge, pkgs_upgrade, 
                downgrade, defer=True)
            trans.connect("progress-changed", self._on_progress_changed)
            yield self._run_in_dialog(trans, self.ACTION_INSTALL)
        except errors.NotAuthorizedError as e:
            self._action_done(self.ACTION_INSTALL, False, False, str(e), None)
        except dbus.DBusException as e:
            if e.get_dbus_name() != "org.freedesktop.DBus.Error.NoReply":
                raise
            self._action_done(self.ACTION_INSTALL, False, False, None, None)
        except Exception as e:
            self._action_done(self.ACTION_INSTALL, True, False, None, None)
            raise

    def _on_progress_changed(self, trans, progress):
        #print("_on_progress_changed", progress)
        self.unity.set_progress(progress)

    @inline_callbacks
    def _run_in_dialog(self, trans, action):
        dia = AptProgressDialog(trans, parent=self.window_main)
        dia.set_icon_name("update-manager")
        dia.connect("finished", self._on_finished, action)
        yield dia.run()

    def _on_finished(self, dialog, action):
        dialog.hide()
        # tell unity to hide the progress again
        self.unity.set_progress(-1)
        self._action_done(action, 
                  True, dialog._transaction.exit == EXIT_SUCCESS, None, None)

if __name__ == "__main__":
    b = InstallBackendAptdaemon(None)
    b.commit(["2vcard"], [], False)

    from gi.repository import Gtk
    Gtk.main()
