#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2005-2007 Canonical, GPL

import apt_pkg
import os
import tempfile
from gettext import gettext as _

from gi.repository import GObject

from UpdateManager.backend import InstallBackend


class InstallBackendSynaptic(InstallBackend):
    """ Install backend based on synaptic """

    def __init__(self, window_main):
        InstallBackend.__init__(self, window_main, self.ACTION_INSTALL)

    def _run_synaptic(self, action, opt, tempf):
        """Execute synaptic."""
        try:
            apt_pkg.pkgsystem_unlock()
        except SystemError:
            pass
        cmd = ["/usr/bin/pkexec", "/usr/sbin/synaptic", "--hide-main-window",
               "--non-interactive", "--parent-window-id",
               "%s" % self.window_main.get_window().get_xid() ]
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
        self._action_done(action, True, os.WEXITSTATUS(condition) == 0, None, None)

    def update(self):
        opt = ["--update-at-startup"]
        tempf = None
        self._run_synaptic(self.UPDATE, opt, tempf)

    def commit(self, pkgs_install, pkgs_upgrade, close_on_done):
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
        opt.append("%s" %  _("Update is complete"))
        tempf = tempfile.NamedTemporaryFile(mode="w+")
        for pkg_name in pkgs_install + pkgs_upgrade:
            tempf.write("%s\tinstall\n" % pkg_name)
        opt.append("--set-selections-file")
        opt.append("%s" % tempf.name)
        tempf.flush()
        self._run_synaptic(self.ACTION_INSTALL, opt, tempf)
