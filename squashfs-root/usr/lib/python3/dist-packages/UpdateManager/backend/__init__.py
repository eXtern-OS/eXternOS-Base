#!/usr/bin/env python
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

"""Integration of package managers into UpdateManager"""
# (c) 2005-2009 Canonical, GPL

from __future__ import absolute_import

from gi.repository import GLib

from apt import Cache
import os

from UpdateManager.Core.utils import inhibit_sleep
from UpdateManager.Dialogs import Dialog


class InstallBackend(Dialog):
    ACTION_UPDATE = 0
    ACTION_INSTALL = 1

    def __init__(self, window_main, action):
        Dialog.__init__(self, window_main)
        self.action = action
        self.sleep_cookie = None

    def start(self):
        os.environ["APT_LISTCHANGES_FRONTEND"] = "none"

        # Do not suspend during the update process
        self.sleep_cookie = inhibit_sleep()

        if self.action == self.ACTION_INSTALL:
            # Get the packages which should be installed and update
            pkgs_install = []
            pkgs_upgrade = []
            pkgs_remove = []
            # Get a fresh cache in case update-manager's is outdated to
            # skip operations that already took place
            fresh_cache = Cache(rootdir=self.window_main.cache.rootdir)
            for pkg in self.window_main.cache:
                try:
                    if pkg.marked_install and \
                       not fresh_cache[pkg.name].is_installed:
                        pkgname = pkg.name
                        if pkg.is_auto_installed:
                            pkgname += "#auto"
                        pkgs_install.append(pkgname)
                    elif (pkg.marked_upgrade and
                          fresh_cache[pkg.name].is_upgradable):
                        pkgs_upgrade.append(pkg.name)
                    elif (pkg.marked_delete and
                          fresh_cache[pkg.name].is_installed):
                        pkgs_remove.append(pkg.name)
                except KeyError:
                    # pkg missing from fresh_cache can't be modified
                    pass
            self.commit(pkgs_install, pkgs_upgrade, pkgs_remove)
        else:
            self.update()

    def update(self):
        """Run a update to refresh the package list"""
        raise NotImplemented

    def commit(self, pkgs_install, pkgs_upgrade, pkgs_remove):
        """Commit the cache changes """
        raise NotImplemented

    def _action_done(self, action, authorized, success, error_string,
                     error_desc, trans_failed=False):

        # If the progress dialog should be closed automatically afterwards
        #settings = Gio.Settings.new("com.ubuntu.update-manager")
        #close_after_install = settings.get_boolean(
        #    "autoclose-install-window")
        # FIXME: confirm with mpt whether this should still be a setting
        #close_after_install = False

        if action == self.ACTION_INSTALL:
            if success:
                self.window_main.start_available()
            elif error_string:
                self.window_main.start_error(trans_failed, error_string,
                                             error_desc)
            else:
                # exit gracefuly, we can't just exit as this will trigger
                # a crash if system.exit() is called in a exception handler
                GLib.timeout_add(1, self.window_main.exit)
        else:
            if error_string:
                self.window_main.start_error(True, error_string, error_desc)
            else:
                is_cancelled_update = not success
                self.window_main.start_available(is_cancelled_update)


# try aptdaemon
if os.path.exists("/usr/sbin/aptd") \
   and "UPDATE_MANAGER_FORCE_BACKEND_SYNAPTIC" not in os.environ:
    # check if the gtkwidgets are installed as well
    try:
        from .InstallBackendAptdaemon import InstallBackendAptdaemon
    except ImportError:
        import logging
        logging.exception("importing aptdaemon")
# try synaptic
if os.path.exists("/usr/sbin/synaptic") \
   and "UPDATE_MANAGER_FORCE_BACKEND_APTDAEMON" not in os.environ:
    try:
        from .InstallBackendSynaptic import InstallBackendSynaptic
    except ImportError:
        import logging
        logging.exception("importing synaptic")


def get_backend(*args, **kwargs):
    """Select and return a package manager backend."""
    # try aptdaemon
    if (os.path.exists("/usr/sbin/aptd") and
            "UPDATE_MANAGER_FORCE_BACKEND_SYNAPTIC" not in os.environ):
        # check if the gtkwidgets are installed as well
        try:
            return InstallBackendAptdaemon(*args, **kwargs)
        except NameError:
            import logging
            logging.exception("using aptdaemon failed")
    # try synaptic
    if (os.path.exists("/usr/sbin/synaptic")
            and "UPDATE_MANAGER_FORCE_BACKEND_APTDAEMON" not in os.environ):
        try:
            return InstallBackendSynaptic(*args, **kwargs)
        except NameError:
            pass
    # nothing found, raise
    raise Exception("No working backend found, please try installing "
                    "aptdaemon or synaptic")
