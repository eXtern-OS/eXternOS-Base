# Dialogs.py
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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
import warnings
warnings.filterwarnings(
    "ignore", "Accessed deprecated property", DeprecationWarning)

import logging
import datetime
import dbus
import distro_info
import os
import subprocess

import HweSupportStatus.consts
from .Core.LivePatchSocket import LivePatchSocket
from .Core.utils import get_dist

from gettext import gettext as _
from gettext import ngettext


class Dialog(object):
    def __init__(self, window_main):
        self.window_main = window_main

    def start(self):
        pass

    def close(self):
        return self.stop()

    def stop(self):
        pass

    def run(self, parent=None):
        pass


class BuilderDialog(Dialog, Gtk.Alignment):
    def __init__(self, window_main, ui_path, root_widget):
        Dialog.__init__(self, window_main)
        Gtk.Alignment.__init__(self)

        builder = self._load_ui(ui_path, root_widget)
        self.add(builder.get_object(root_widget))
        self.show()

    def _load_ui(self, path, root_widget, domain="update-manager"):
        builder = Gtk.Builder()
        builder.set_translation_domain(domain)
        builder.add_objects_from_file(path, [root_widget])
        builder.connect_signals(self)

        for o in builder.get_objects():
            if issubclass(type(o), Gtk.Buildable):
                name = Gtk.Buildable.get_name(o)
                setattr(self, name, o)
            else:
                logging.debug("WARNING: can not get name for '%s'" % o)

        return builder

    def run(self, parent=None):
        # FIXME: THIS WILL CRASH!
        if parent:
            self.window_dialog.set_transient_for(parent)
            self.window_dialog.set_modal(True)
        self.window_dialog.run()


class InternalDialog(BuilderDialog):
    def __init__(self, window_main, content_widget=None):
        ui_path = os.path.join(window_main.datadir, "gtkbuilder/Dialog.ui")
        BuilderDialog.__init__(self, window_main, ui_path, "pane_dialog")

        self.settings = Gio.Settings.new("com.ubuntu.update-manager")

        self.focus_button = None
        self.set_content_widget(content_widget)
        self.connect("realize", self._on_realize)

    def _on_realize(self, user_data):
        if self.focus_button:
            self.focus_button.set_can_default(True)
            self.focus_button.set_can_focus(True)
            self.focus_button.grab_default()
            self.focus_button.grab_focus()

    def add_button(self, label, callback, secondary=False):
        # from_stock tries stock first and falls back to mnemonic
        button = Gtk.Button.new_from_stock(label)
        button.connect("clicked", lambda x: callback())
        button.show()
        self.buttonbox.add(button)
        self.buttonbox.set_child_secondary(button, secondary)
        return button

    def add_settings_button(self):
        if os.path.exists("/usr/bin/software-properties-gtk"):
            return self.add_button(_("Settings…"),
                                   self.on_settings_button_clicked,
                                   secondary=True)
        else:
            return None

    def on_settings_button_clicked(self):
        self.window_main.show_settings()

    def set_header(self, label):
        if label:
            self.label_header.set_markup(
                "<span size='larger' weight='bold'>%s</span>" % label)
        self.label_header.set_visible(bool(label))

    def set_desc(self, label):
        if label:
            self.label_desc.set_markup(label)
        self.label_desc.set_visible(bool(label))

    def set_content_widget(self, content_widget):
        if content_widget:
            self.main_container.add(content_widget)
        self.main_container.set_visible(bool(content_widget))

    def _is_livepatch_supported(self):
        di = distro_info.UbuntuDistroInfo()
        codename = get_dist()
        return di.is_lts(codename)

    def on_livepatch_status_ready(self, active, cs, ps, fixes):
        self.set_desc(None)

        if not active:
            if self._is_livepatch_supported() and \
               self.settings_button and \
               self.settings.get_int('launch-count') >= 4:
                self.set_desc(_("<b>Tip:</b> You can use Livepatch to "
                                "keep your computer more secure between "
                                "restarts."))
                self.settings_button.set_label(_("Settings & Livepatch…"))
            return

        needs_reschedule = False

        if cs == "needs-check":
            needs_reschedule = True
        elif cs == "check-failed":
            pass
        elif cs == "checked":
            if ps == "unapplied" or ps == "applying":
                needs_reschedule = True
            elif ps == "applied":
                fixes = [fix for fix in fixes if fix.patched]
                d = ngettext("%d Livepatch update applied since the last "
                             "restart.",
                             "%d Livepatch updates applied since the last "
                             "restart.",
                             len(fixes)) % len(fixes)
                self.set_desc(d)
            elif ps == "applied-with-bug" or ps == "apply-failed":
                fixes = [fix for fix in fixes if fix.patched]
                d = ngettext("%d Livepatch update failed to apply since the "
                             "last restart.",
                             "%d Livepatch updates failed to apply since the "
                             "last restart.",
                             len(fixes)) % len(fixes)
                self.set_desc(d)
            elif ps == "nothing-to-apply":
                pass
            elif ps == "unknown":
                pass

        if needs_reschedule:
            self.lp_socket.get_status(self.on_livepatch_status_ready)

    def check_livepatch_status(self):
        self.lp_socket = LivePatchSocket()
        self.lp_socket.get_status(self.on_livepatch_status_ready)


class StoppedUpdatesDialog(InternalDialog):
    def __init__(self, window_main):
        InternalDialog.__init__(self, window_main)
        self.set_header(_("You stopped the check for updates."))
        self.add_settings_button()
        self.add_button(_("_Check Again"), self.check)
        self.focus_button = self.add_button(Gtk.STOCK_OK,
                                            self.window_main.close)

    def check(self):
        self.window_main.start_update()


class NoUpdatesDialog(InternalDialog):
    def __init__(self, window_main, error_occurred=False):
        InternalDialog.__init__(self, window_main)
        if error_occurred:
            self.set_header(_("No software updates are available."))
        else:
            self.set_header(_("The software on this computer is up to date."))
        self.settings_button = self.add_settings_button()
        self.focus_button = self.add_button(Gtk.STOCK_OK,
                                            self.window_main.close)
        self.check_livepatch_status()


class DistUpgradeDialog(InternalDialog):
    def __init__(self, window_main, meta_release):
        InternalDialog.__init__(self, window_main)
        self.meta_release = meta_release
        self.set_header(_("The software on this computer is up to date."))
        # Translators: these are Ubuntu version names like "Ubuntu 12.04"
        self.set_desc(_("However, %s %s is now available (you have %s).") % (
                      meta_release.flavor_name,
                      meta_release.upgradable_to.version,
                      meta_release.current_dist_version))
        self.add_settings_button()
        self.add_button(_("Upgrade…"), self.upgrade)
        self.focus_button = self.add_button(Gtk.STOCK_OK,
                                            self.window_main.close)

    def upgrade(self):
        # Pass on several arguments
        extra_args = ""
        if self.window_main and self.window_main.options:
            if self.window_main.options.devel_release:
                extra_args = extra_args + " -d"
            if self.window_main.options.use_proposed:
                extra_args = extra_args + " -p"
        os.execl("/bin/sh", "/bin/sh", "-c",
                 "/usr/bin/do-release-upgrade "
                 "--frontend=DistUpgradeViewGtk3%s" % extra_args)


class HWEUpgradeDialog(InternalDialog):
    def __init__(self, window_main):
        InternalDialog.__init__(self, window_main)
        self.set_header(_("New important security and hardware support "
                          "update."))
        if datetime.date.today() < HweSupportStatus.consts.HWE_EOL_DATE:
            self.set_desc(_(HweSupportStatus.consts.Messages.HWE_SUPPORT_ENDS))
        else:
            self.set_desc(
                _(HweSupportStatus.consts.Messages.HWE_SUPPORT_HAS_ENDED))
        self.add_settings_button()
        self.add_button(_("_Install…"), self.install)
        self.focus_button = self.add_button(Gtk.STOCK_OK,
                                            self.window_main.close)

    def install(self):
        self.window_main.start_install(hwe_upgrade=True)


class UnsupportedDialog(DistUpgradeDialog):
    def __init__(self, window_main, meta_release):
        DistUpgradeDialog.__init__(self, window_main, meta_release)
        # Translators: this is an Ubuntu version name like "Ubuntu 12.04"
        self.set_header(_("Software updates are no longer provided for "
                          "%s %s.") % (meta_release.flavor_name,
                                       meta_release.current_dist_version))
        # Translators: this is an Ubuntu version name like "Ubuntu 12.04"
        self.set_desc(_("To stay secure, you should upgrade to %s %s.") % (
            meta_release.flavor_name,
            meta_release.upgradable_to.version))

    def run(self, parent):
        # This field is used in tests/test_end_of_life.py
        self.window_main.no_longer_supported_nag = self.window_dialog
        DistUpgradeDialog.run(self, parent)


class PartialUpgradeDialog(InternalDialog):
    def __init__(self, window_main):
        InternalDialog.__init__(self, window_main)
        self.set_header(_("Not all updates can be installed"))
        self.set_desc(_(
            """Run a partial upgrade, to install as many updates as possible.

    This can be caused by:
     * A previous upgrade which didn't complete
     * Problems with some of the installed software
     * Unofficial software packages not provided by Ubuntu
     * Normal changes of a pre-release version of Ubuntu"""))
        self.add_settings_button()
        self.add_button(_("_Partial Upgrade"), self.upgrade)
        self.focus_button = self.add_button(_("_Continue"), Gtk.main_quit)

    def upgrade(self):
        os.execl("/bin/sh", "/bin/sh", "-c",
                 "/usr/lib/ubuntu-release-upgrader/do-partial-upgrade "
                 "--frontend=DistUpgradeViewGtk3")

    def start(self):
        Dialog.start(self)
        # Block progress until user has answered this question
        Gtk.main()


class ErrorDialog(InternalDialog):
    def __init__(self, window_main, header, desc=None):
        InternalDialog.__init__(self, window_main)
        self.set_header(header)
        if desc:
            self.set_desc(desc)
            self.label_desc.set_selectable(True)
        self.add_settings_button()
        self.focus_button = self.add_button(Gtk.STOCK_OK,
                                            self.window_main.close)

    def start(self):
        Dialog.start(self)
        # The label likes to start selecting everything (b/c it got focus
        # before we switched to our default button).
        self.label_desc.select_region(0, 0)


class UpdateErrorDialog(ErrorDialog):
    def __init__(self, window_main, header, desc=None):
        ErrorDialog.__init__(self, window_main, header, desc)
        # Get rid of normal error dialog button before adding our own
        self.focus_button.destroy()
        self.add_button(_("_Try Again"), self.update)
        self.focus_button = self.add_button(Gtk.STOCK_OK, self.available)

    def update(self):
        self.window_main.start_update()

    def available(self):
        self.window_main.start_available(error_occurred=True)


class NeedRestartDialog(InternalDialog):
    def __init__(self, window_main):
        InternalDialog.__init__(self, window_main)
        self.set_header(
            _("The computer needs to restart to finish installing updates."))
        self.add_settings_button()
        self.focus_button = self.add_button(_("Restart _Later"),
                                            self.window_main.close)
        self.add_button(_("_Restart Now"), self.restart)

    def start(self):
        Dialog.start(self)
        # Turn off close button
        self.window_main.realize()
        self.window_main.get_window().set_functions(Gdk.WMFunction.MOVE |
                                                    Gdk.WMFunction.MINIMIZE)

    def restart(self, *args, **kwargs):
        self._request_reboot_via_session_manager()
        self.window_main.close()

    def _request_reboot_via_session_manager(self):
        try:
            bus = dbus.SessionBus()
            proxy_obj = bus.get_object("org.gnome.SessionManager",
                                       "/org/gnome/SessionManager")
            iface = dbus.Interface(proxy_obj, "org.gnome.SessionManager")
            iface.RequestReboot()
        except dbus.DBusException:
            self._request_reboot_via_consolekit()
        except Exception as e:
            pass

    def _request_reboot_via_consolekit(self):
        try:
            bus = dbus.SystemBus()
            proxy_obj = bus.get_object("org.freedesktop.ConsoleKit",
                                       "/org/freedesktop/ConsoleKit/Manager")
            iface = dbus.Interface(
                proxy_obj, "org.freedesktop.ConsoleKit.Manager")
            iface.Restart()
        except dbus.DBusException:
            self._request_reboot_via_logind()
        except Exception as e:
            pass

    def _request_reboot_via_logind(self):
        try:
            bus = dbus.SystemBus()
            proxy_obj = bus.get_object("org.freedesktop.login1",
                                       "/org/freedesktop/login1")
            iface = dbus.Interface(
                proxy_obj, "org.freedesktop.login1.Manager")
            iface.Reboot(True)
        except dbus.DBusException:
            pass
