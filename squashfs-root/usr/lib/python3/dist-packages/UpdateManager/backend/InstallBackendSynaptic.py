#!/usr/bin/env python
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
# (c) 2005-2007 Canonical, GPL

import apt_pkg
import os
import tempfile
from gettext import gettext as _

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GObject
# Extra GdkX11 import for pygobject bug #673396
# https://bugzilla.gnome.org/show_bug.cgi?id=673396
from gi.repository import GdkX11
GdkX11  # pyflakes

from UpdateManager.backend import InstallBackend


class InstallBackendSynaptic(InstallBackend):
    """ Install backend based on synaptic """

    def update(self):
        opt = ["--update-at-startup"]
        tempf = None
        self._run_synaptic(self.ACTION_UPDATE, opt, tempf)

    def commit(self, pkgs_install, pkgs_upgrade, pkgs_remove,
               close_on_done=False):
        # close when update was successful (its ok to use a Synaptic::
        # option here, it will not get auto-saved, because synaptic does
        # not save options in non-interactive mode)
        opt = []
        if close_on_done:
            opt.append("-o")
            opt.append("Synaptic::closeZvt=true")
        # custom progress strings
        opt.append("--progress-str")
        opt.append("%s" % _("Please wait, this can take some time."))
        opt.append("--finish-str")
        opt.append("%s" % _("Update is complete"))
        tempf = tempfile.NamedTemporaryFile(mode="w+")
        for pkg_name in pkgs_install + pkgs_upgrade:
            tempf.write("%s\tinstall\n" % pkg_name)
        for pkg_name in pkgs_remove:
            tempf.write("%s\tdeinstall\n" % pkg_name)
        opt.append("--set-selections-file")
        opt.append("%s" % tempf.name)
        tempf.flush()
        self._run_synaptic(self.ACTION_INSTALL, opt, tempf)

    def _run_synaptic(self, action, opt, tempf):
        """Execute synaptic."""
        try:
            apt_pkg.pkgsystem_unlock()
        except SystemError:
            pass
        win = self.window_main.get_window()
        try:
            xid = win.get_xid()
        except AttributeError:
            xid = 0
        cmd = ["/usr/bin/pkexec", "/usr/sbin/synaptic", "--hide-main-window",
               "--non-interactive", "--parent-window-id",
               "%s" % xid]
        cmd.extend(opt)
        flags = GObject.SPAWN_DO_NOT_REAP_CHILD
        (pid, stdin, stdout, stderr) = GObject.spawn_async(cmd, flags=flags)
        # Keep a reference to the data tuple passed to
        # GObject.child_watch_add to avoid attempts to destroy it without a
        # thread context: https://bugs.launchpad.net/bugs/724687
        self.child_data = (action, tempf)
        GObject.child_watch_add(pid, self._on_synaptic_exit, self.child_data)

    def _on_synaptic_exit(self, pid, condition, data):
        action, tempf = data
        if tempf:
            tempf.close()
        self._action_done(action,
                          authorized=True,
                          success=os.WEXITSTATUS(condition) == 0,
                          error_string=None, error_desc=None)
