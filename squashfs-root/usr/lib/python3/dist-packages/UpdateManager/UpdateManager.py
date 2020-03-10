# UpdateManager.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2012 Canonical
#
#  Author: Michael Terry <michael.terry@canonical.com>
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

from __future__ import absolute_import, print_function

from gi.repository import Gtk
from gi.repository import Gdk, GdkX11
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

GdkX11  # pyflakes

import warnings
warnings.filterwarnings("ignore", "Accessed deprecated property",
                        DeprecationWarning)

import apt_pkg
import distro_info
import os
import subprocess
import sys
import time
from gettext import gettext as _

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

from .UnitySupport import UnitySupport
from .Dialogs import (DistUpgradeDialog,
                      ErrorDialog,
                      HWEUpgradeDialog,
                      NeedRestartDialog,
                      NoUpdatesDialog,
                      PartialUpgradeDialog,
                      StoppedUpdatesDialog,
                      UnsupportedDialog,
                      UpdateErrorDialog)
from .MetaReleaseGObject import MetaRelease
from .UpdatesAvailable import UpdatesAvailable
from .Core.AlertWatcher import AlertWatcher
from .Core.MyCache import MyCache
from .Core.roam import NetworkManagerHelper
from .Core.UpdateList import UpdateList
from .Core.utils import get_dist
from .backend import (InstallBackend,
                      get_backend)

# file that signals if we need to reboot
REBOOT_REQUIRED_FILE = "/var/run/reboot-required"


class UpdateManager(Gtk.Window):
    """ This class is the main window and work flow controller. The main
        window will show panes, and it will morph between them. """

    def __init__(self, datadir, options):
        Gtk.Window.__init__(self)

        # Public members
        self.datadir = datadir
        self.options = options
        self.unity = UnitySupport()
        self.controller = None
        self.cache = None
        self.update_list = None
        self.meta_release = None
        self.hwe_replacement_packages = None

        # Basic GTK+ parameters
        self.set_title(_("Software Updater"))
        self.set_icon_name("system-software-update")
        self.set_position(Gtk.WindowPosition.CENTER)

        # Keep window at a constant size
        ctx = self.get_style_context()
        self.style_changed = ctx.connect("changed",
                                         lambda ctx:
                                             self.resize_to_standard_width())

        # Signals
        self.connect("delete-event", self._on_close)

        self._setup_dbus()

        # deal with no-focus-on-map
        if self.options and self.options.no_focus_on_map:
            self.set_focus_on_map(False)
            self.iconify()
            self.stick()
            self.set_urgency_hint(True)
            self.unity.set_urgency(True)
            self.initial_focus_id = self.connect(
                "focus-in-event", self.on_initial_focus_in)

        # Look for a new release in a thread
        self.meta_release = MetaRelease(
            self.options and self.options.devel_release,
            self.options and self.options.use_proposed)

    def begin_user_resizable(self, stored_width=0, stored_height=0):
        self.set_resizable(True)
        if stored_width > 0 and stored_height > 0:
            # There is a race here.  If we immediately resize, it often doesn't
            # take.  Using idle_add helps, but we *still* occasionally don't
            # restore the size correctly.  Help needed to track this down!
            GLib.idle_add(lambda: self.resize(stored_width, stored_height))

    def end_user_resizable(self):
        self.set_resizable(False)

    def resize_to_standard_width(self):
        if self.get_resizable():
            return  # only size to a specific em if we are a static size
        num_em = 33  # per SoftwareUpdates spec
        dpi = self.get_screen().get_resolution()
        if dpi <= 0:
            dpi = 96
        ctx = self.get_style_context()
        GObject.signal_handler_block(ctx, self.style_changed)
        size = ctx.get_property("font-size", Gtk.StateFlags.NORMAL)
        width = dpi / 72 * size * num_em
        self.set_size_request(width, -1)
        GObject.signal_handler_unblock(ctx, self.style_changed)

    def on_initial_focus_in(self, widget, event):
        """callback run on initial focus-in (if started unmapped)"""
        self.unstick()
        self.set_urgency_hint(False)
        self.unity.set_urgency(False)
        self.disconnect(self.initial_focus_id)
        return False

    def _start_pane(self, pane):
        if self.controller is not None:
            self.controller.stop()
            if isinstance(self.controller, Gtk.Widget):
                self.controller.destroy()

        self.controller = pane
        self._look_ready()
        self.end_user_resizable()

        if pane is None:
            return

        if isinstance(pane, Gtk.Widget):
            self.add(pane)
            pane.start()
            self.show_all()
        else:
            pane.start()
            self.hide()

    def _on_close(self, widget, data=None):
        return self.close()

    def close(self):
        if not self.get_sensitive():
            return True

        if self.controller:
            controller_close = self.controller.close()
            if controller_close:
                return controller_close
        self.exit()

    def exit(self):
        """ exit the application, save the state """
        self._start_pane(None)
        sys.exit(0)

    def show_settings(self):
        try:
            apt_pkg.pkgsystem_unlock()
        except SystemError:
            pass
        cmd = ["/usr/bin/software-properties-gtk",
               "--open-tab", "2"]

        if "WAYLAND_DISPLAY" not in os.environ:
            cmd += ["--toplevel", "%s" % self.get_window().get_xid()]

        self._look_busy()
        try:
            p = subprocess.Popen(cmd)
        except OSError:
            pass
        else:
            while p.poll() is None:
                while Gtk.events_pending():
                    Gtk.main_iteration()
                time.sleep(0.05)
        finally:
            self.start_available()

    def start_update(self):
        if self.options.no_update:
            self.start_available()
            return

        update_backend = get_backend(self, InstallBackend.ACTION_UPDATE)
        self._start_pane(update_backend)

    def start_install(self, hwe_upgrade=False):
        install_backend = get_backend(self, InstallBackend.ACTION_INSTALL)
        if hwe_upgrade:
            for pkgname in self.hwe_replacement_packages:
                try:
                    self.cache[pkgname].mark_install()
                except SystemError:
                    pass
        self._start_pane(install_backend)

    def start_available(self, cancelled_update=False, error_occurred=False):
        self._look_busy()
        self.refresh_cache()

        pane = self._make_available_pane(self.cache.install_count,
                                         os.path.exists(REBOOT_REQUIRED_FILE),
                                         cancelled_update, error_occurred)
        self._start_pane(pane)

    def _make_available_pane(self, install_count, need_reboot=False,
                             cancelled_update=False, error_occurred=False):
        self._check_hwe_support_status()
        if install_count == 0:
            # Need Restart > New Release > No Updates
            if need_reboot:
                return NeedRestartDialog(self)
            dist_upgrade = self._check_meta_release()
            if dist_upgrade:
                return dist_upgrade
            elif cancelled_update:
                return StoppedUpdatesDialog(self)
            elif self.hwe_replacement_packages:
                return HWEUpgradeDialog(self)
            else:
                return NoUpdatesDialog(self, error_occurred=error_occurred)
        else:
            header = None
            desc = None
            if error_occurred:
                desc = _("Some software couldn’t be checked for updates.")
            elif cancelled_update:
                header = _("You stopped the check for updates.")
                desc = _("Updated software is available from "
                         "a previous check.")
            # Display HWE updates first as an old HWE stack is vulnerable
            elif self.hwe_replacement_packages:
                return HWEUpgradeDialog(self)
            return UpdatesAvailable(self, header, desc, need_reboot)

    def start_error(self, update_and_retry, header, desc):
        if update_and_retry:
            self._start_pane(UpdateErrorDialog(self, header, desc))
        else:
            self._start_pane(ErrorDialog(self, header, desc))

    def _look_busy(self):
        self.set_sensitive(False)
        if self.get_window() is not None:
            self.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.WATCH))

    def _look_ready(self):
        self.set_sensitive(True)
        if self.get_window() is not None:
            self.get_window().set_cursor(None)
            self.get_window().set_functions(Gdk.WMFunction.ALL)

    def _check_meta_release(self):
        if self.meta_release is None:
            return None

        if self.meta_release.downloading:
            # Block until we get an answer
            GLib.idle_add(self._meta_release_wait_idle)
            Gtk.main()

        # Check if there is anything to upgrade to or a known-broken upgrade
        next = self.meta_release.upgradable_to
        if not next or next.upgrade_broken:
            return None

        # Check for end-of-life
        if self.meta_release.no_longer_supported:
            return UnsupportedDialog(self, self.meta_release)

        # Check for new fresh release
        settings = Gio.Settings.new("com.ubuntu.update-manager")
        if (self.meta_release.new_dist and
                (self.options.check_dist_upgrades or
                 settings.get_boolean("check-dist-upgrades"))):
            return DistUpgradeDialog(self, self.meta_release)

        return None

    def _meta_release_wait_idle(self):
        # 'downloading' is changed in a thread, but the signal
        # 'done_downloading' is done in our thread's event loop.  So we know
        # that it won't fire while we're in this function.
        if not self.meta_release.downloading:
            Gtk.main_quit()
        else:
            self.meta_release.connect("done_downloading", Gtk.main_quit)
        return False

    def _check_hwe_support_status(self):
        di = distro_info.UbuntuDistroInfo()
        codename = get_dist()
        lts = di.is_lts(codename)
        if not lts:
            return None
        HWE = "/usr/bin/hwe-support-status"
        if not os.path.exists(HWE):
            return None
        cmd = [HWE, "--show-replacements"]
        self._parse_hwe_support_status(cmd)

    def _parse_hwe_support_status(self, cmd):
        try:
            subprocess.check_output(cmd)
            # for debugging
            # print("nothing unsupported running")
        except subprocess.CalledProcessError as e:
            if e.returncode == 10:
                packages = e.output.strip().split()
                self.hwe_replacement_packages = []
                for pkgname in packages:
                    pkgname = pkgname.decode('utf-8')
                    if pkgname in self.cache and \
                            not self.cache[pkgname].is_installed:
                        self.hwe_replacement_packages.append(pkgname)
                # for debugging
                # print(self.hwe_replacement_packages)

    # fixme: we should probably abstract away all the stuff from libapt
    def refresh_cache(self):
        # get the lock
        try:
            apt_pkg.pkgsystem_lock()
        except SystemError:
            pass

        try:
            if self.cache is None:
                self.cache = MyCache(None)
            else:
                self.cache.open(None)
                self.cache._initDepCache()
        except AssertionError:
            # if the cache could not be opened for some reason,
            # let the release upgrader handle it, it deals
            # a lot better with this
            self._start_pane(PartialUpgradeDialog(self))
            # we assert a clean cache
            header = _("Software index is broken")
            desc = _("It is impossible to install or remove any software. "
                     "Please use the package manager \"Synaptic\" or run "
                     "\"sudo apt-get install -f\" in a terminal to fix "
                     "this issue at first.")
            self.start_error(True, header, desc)
        except SystemError as e:
            header = _("Could not initialize the package information")
            desc = _("An unresolvable problem occurred while "
                     "initializing the package information.\n\n"
                     "Please report this bug against the 'update-manager' "
                     "package and include the following error "
                     "message:\n") + str(e)
            self.start_error(True, header, desc)

        # Let the Gtk event loop breath if it hasn't had a chance.
        def iterate():
            while Gtk.events_pending():
                Gtk.main_iteration()
        iterate()

        self.update_list = UpdateList(self)
        try:
            self.update_list.update(self.cache, eventloop_callback=iterate)
        except SystemError as e:
            header = _("Could not calculate the upgrade")
            desc = _("An unresolvable problem occurred while "
                     "calculating the upgrade.\n\n"
                     "Please report this bug against the 'update-manager' "
                     "package and include the following error "
                     "message:\n") + str(e)
            self.start_error(True, header, desc)

        if self.update_list.distUpgradeWouldDelete > 0:
            self._start_pane(PartialUpgradeDialog(self))

    def _setup_dbus(self):
        """ this sets up a dbus listener if none is installed already """
        # check if there is another g-a-i already and if not setup one
        # listening on dbus
        try:
            bus = dbus.SessionBus()
        except Exception as e:
            print("warning: could not initiate dbus")
            return
        try:
            proxy_obj = bus.get_object('org.freedesktop.UpdateManager',
                                       '/org/freedesktop/UpdateManagerObject')
            iface = dbus.Interface(proxy_obj,
                                   'org.freedesktop.UpdateManagerIFace')
            iface.bringToFront()
            #print("send bringToFront")
            sys.exit(0)
        except dbus.DBusException:
            #print("no listening object (%s) " % e)
            bus_name = dbus.service.BusName('org.freedesktop.UpdateManager',
                                            bus)
            self.dbusController = UpdateManagerDbusController(self, bus_name)


class UpdateManagerDbusController(dbus.service.Object):
    """ this is a helper to provide the UpdateManagerIFace """
    def __init__(self, parent, bus_name,
                 object_path='/org/freedesktop/UpdateManagerObject'):
        dbus.service.Object.__init__(self, bus_name, object_path)
        self.parent = parent
        self.alert_watcher = AlertWatcher()
        self.alert_watcher.connect("network-alert", self._on_network_alert)
        self.connected = False

    @dbus.service.method('org.freedesktop.UpdateManagerIFace')
    def bringToFront(self):
        self.parent.present()
        return True

    @dbus.service.method('org.freedesktop.UpdateManagerIFace')
    def upgrade(self):
        try:
            self.parent.start_install()
            return True
        except Exception as e:
            return False

    def _on_network_alert(self, watcher, state):
        if state in NetworkManagerHelper.NM_STATE_CONNECTED_LIST:
            self.connected = True
        else:
            self.connected = False
