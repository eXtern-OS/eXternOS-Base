#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Provides AptWorker which processes transactions."""
# Copyright (C) 2008-2009 Sebastian Heinlein <devel@glatzor.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

__all__ = ("BaseWorker", "DummyWorker")

import logging
import os
import pkg_resources
import time
import traceback

from gi.repository import GObject, GLib

from .. import enums
from .. import errors

log = logging.getLogger("AptDaemon.Worker")

# Just required to detect translatable strings. The translation is done by
# core.Transaction.gettext
_ = lambda s: s


class BaseWorker(GObject.GObject):

    """Worker which processes transactions from the queue."""

    __gsignals__ = {"transaction-done": (GObject.SignalFlags.RUN_FIRST,
                                         None,
                                         (GObject.TYPE_PYOBJECT,)),
                    "transaction-simulated": (GObject.SignalFlags.RUN_FIRST,
                                              None,
                                              (GObject.TYPE_PYOBJECT,))}
    NATIVE_ARCH = None

    def __init__(self, chroot=None, load_plugins=True):
        """Initialize a new AptWorker instance."""
        GObject.GObject.__init__(self)
        self.trans = None
        self.last_action_timestamp = time.time()
        self.chroot = chroot
        # Store the the tid of the transaction whose changes are currently
        # marked in the cache
        self.marked_tid = None
        self.plugins = {}

    @staticmethod
    def _split_package_id(package):
        """Return the name, the version number and the release of the
        specified package."""
        if "=" in package:
            name, version = package.split("=", 1)
            release = None
        elif "/" in package:
            name, release = package.split("/", 1)
            version = None
        else:
            name = package
            version = release = None
        return name, version, release

    def run(self, transaction):
        """Process the given transaction in the background.

        Keyword argument:
        transaction -- core.Transcation instance to run
        """
        log.info("Processing transaction %s", transaction.tid)
        if self.trans:
            raise Exception("There is already a running transaction")
        self.trans = transaction
        GLib.idle_add(self._run_transaction_idle, transaction)

    def simulate(self, trans):
        """Return the dependencies which will be installed by the transaction,
        the content of the dpkg status file after the transaction would have
        been applied, the download size and the required disk space.

        Keyword arguments:
        trans -- the transaction which should be simulated
        """
        log.info("Simulating trans: %s" % trans.tid)
        trans.status = enums.STATUS_RESOLVING_DEP
        GLib.idle_add(self._simulate_transaction_idle, trans)

    def _emit_transaction_simulated(self, trans):
        """Emit the transaction-simulated signal.

        Keyword argument:
        trans -- the simulated transaction
        """
        log.debug("Emitting transaction-simulated: %s", trans.tid)
        self.emit("transaction-simulated", trans)

    def _emit_transaction_done(self, trans):
        """Emit the transaction-done signal.

        Keyword argument:
        trans -- the finished transaction
        """
        log.debug("Emitting transaction-done: %s", trans.tid)
        self.emit("transaction-done", trans)

    def _run_transaction_idle(self, trans):
        """Run the transaction"""
        self.last_action_timestamp = time.time()
        trans.status = enums.STATUS_RUNNING
        trans.progress = 11
        try:
            self._run_transaction(trans)
        except errors.TransactionCancelled:
            trans.exit = enums.EXIT_CANCELLED
        except errors.TransactionFailed as excep:
            trans.error = excep
            trans.exit = enums.EXIT_FAILED
        except (KeyboardInterrupt, SystemExit):
            trans.exit = enums.EXIT_CANCELLED
        except Exception as excep:
            tbk = traceback.format_exc()
            trans.error = errors.TransactionFailed(enums.ERROR_UNKNOWN, tbk)
            trans.exit = enums.EXIT_FAILED
            try:
                from . import crash
            except ImportError:
                pass
            else:
                crash.create_report("%s: %s" % (type(excep), str(excep)),
                                    tbk, trans)
        else:
            trans.exit = enums.EXIT_SUCCESS
        finally:
            trans.progress = 100
            self.last_action_timestamp = time.time()
            tid = trans.tid[:]
            self.trans = None
            self.marked_tid = None
            self._emit_transaction_done(trans)
            log.info("Finished transaction %s", tid)
        return False

    def _simulate_transaction_idle(self, trans):
        try:
            (trans.depends, trans.download, trans.space,
                trans.unauthenticated,
                trans.high_trust_packages) = self._simulate_transaction(trans)
        except errors.TransactionFailed as excep:
            trans.error = excep
            trans.exit = enums.EXIT_FAILED
        except Exception as excep:
            tbk = traceback.format_exc()
            trans.error = errors.TransactionFailed(enums.ERROR_UNKNOWN, tbk)
            try:
                from . import crash
            except ImportError:
                pass
            else:
                crash.create_report("%s: %s" % (type(excep), str(excep)),
                                    tbk, trans)
            trans.exit = enums.EXIT_FAILED
        else:
            trans.status = enums.STATUS_SETTING_UP
            trans.simulated = time.time()
            self.marked_tid = trans.tid
        finally:
            self._emit_transaction_simulated(trans)
            self.last_action_timestamp = time.time()
        return False

    def _load_plugins(self, plugins, entry_point="aptdaemon.plugins"):
        """Load the plugins from setuptools' entry points."""
        plugin_dirs = [os.path.join(os.path.dirname(__file__), "plugins")]
        env = pkg_resources.Environment(plugin_dirs)
        dists, errors = pkg_resources.working_set.find_plugins(env)
        for dist in dists:
            pkg_resources.working_set.add(dist)
        for name in plugins:
            for ept in pkg_resources.iter_entry_points(entry_point,
                                                       name):
                try:
                    self.plugins.setdefault(name, []).append(ept.load())
                except:
                    log.critical("Failed to load %s plugin: "
                                 "%s" % (name, ept.dist))
                else:
                    log.debug("Loaded %s plugin: %s", name, ept.dist)

    def _simulate_transaction(self, trans):
        """This method needs to be implemented by the backends."""
        depends = [[], [], [], [], [], [], []]
        unauthenticated = []
        high_trust_packages = []
        skip_pkgs = []
        size = 0
        installs = reinstalls = removals = purges = upgrades = upgradables = \
            downgrades = []

        return depends, 0, 0, [], []

    def _run_transaction(self, trans):
        """This method needs to be implemented by the backends."""
        raise errors.TransactionFailed(enums.ERROR_NOT_SUPPORTED)

    def set_config(self, option, value, filename):
        """Set a configuration option.

        This method needs to be implemented by the backends."""
        raise NotImplementedError

    def get_config(self, option):
        """Get a configuration option.

        This method needs to be implemented by the backends."""
        raise NotImplementedError

    def get_trusted_vendor_keys(self):
        """This method needs to be implemented by the backends."""
        return []

    def is_reboot_required(self):
        """This method needs to be implemented by the backends."""
        return False


class DummyWorker(BaseWorker):

    """Allows to test the daemon without making any changes to the system."""

    def run(self, transaction):
        """Process the given transaction in the background.

        Keyword argument:
        transaction -- core.Transcation instance to run
        """
        log.info("Processing transaction %s", transaction.tid)
        if self.trans:
            raise Exception("There is already a running transaction")
        self.trans = transaction
        self.last_action_timestamp = time.time()
        self.trans.status = enums.STATUS_RUNNING
        self.trans.progress = 0
        self.trans.cancellable = True
        GLib.timeout_add(200, self._run_transaction_idle, transaction)

    def _run_transaction_idle(self, trans):
        """Run the worker"""
        if trans.cancelled:
            trans.exit = enums.EXIT_CANCELLED
        elif trans.progress == 100:
            trans.exit = enums.EXIT_SUCCESS
        elif trans.role == enums.ROLE_UPDATE_CACHE:
            trans.exit = enums.EXIT_FAILED
        elif trans.role == enums.ROLE_UPGRADE_PACKAGES:
            trans.exit = enums.EXIT_SUCCESS
        elif trans.role == enums.ROLE_UPGRADE_SYSTEM:
            trans.exit = enums.EXIT_CANCELLED
        else:
            if trans.role == enums.ROLE_INSTALL_PACKAGES:
                if trans.progress == 1:
                    trans.status = enums.STATUS_RESOLVING_DEP
                elif trans.progress == 5:
                    trans.status = enums.STATUS_DOWNLOADING
                elif trans.progress == 50:
                    trans.status = enums.STATUS_COMMITTING
                    trans.status_details = "Heyas!"
                elif trans.progress == 55:
                    trans.paused = True
                    trans.status = enums.STATUS_WAITING_CONFIG_FILE_PROMPT
                    trans.config_file_conflict = "/etc/fstab", "/etc/mtab"
                    while trans.paused:
                        GLib.main_context_default().iteration()
                    trans.config_file_conflict_resolution = None
                    trans.config_file_conflict = None
                    trans.status = enums.STATUS_COMMITTING
                elif trans.progress == 60:
                    trans.required_medium = ("Debian Lenny 5.0 CD 1",
                                             "USB CD-ROM")
                    trans.paused = True
                    trans.status = enums.STATUS_WAITING_MEDIUM
                    while trans.paused:
                        GLib.main_context_default().iteration()
                    trans.status = enums.STATUS_DOWNLOADING
                elif trans.progress == 70:
                    trans.status_details = "Servus!"
                elif trans.progress == 90:
                    trans.status_deatils = ""
                    trans.status = enums.STATUS_CLEANING_UP
            elif trans.role == enums.ROLE_REMOVE_PACKAGES:
                if trans.progress == 1:
                    trans.status = enums.STATUS_RESOLVING_DEP
                elif trans.progress == 5:
                    trans.status = enums.STATUS_COMMITTING
                    trans.status_details = "Heyas!"
                elif trans.progress == 50:
                    trans.status_details = "Hola!"
                elif trans.progress == 70:
                    trans.status_details = "Servus!"
                elif trans.progress == 90:
                    trans.status_deatils = ""
                    trans.status = enums.STATUS_CLEANING_UP
            trans.progress += 1
            return True
        trans.status = enums.STATUS_FINISHED
        self.last_action_timestamp = time.time()
        tid = self.trans.tid[:]
        trans = self.trans
        self.trans = None
        self._emit_transaction_done(trans)
        log.info("Finished transaction %s", tid)
        return False

    def simulate(self, trans):
        depends = [[], [], [], [], [], [], []]
        return depends, 0, 0, [], []


# vim:ts=4:sw=4:et
