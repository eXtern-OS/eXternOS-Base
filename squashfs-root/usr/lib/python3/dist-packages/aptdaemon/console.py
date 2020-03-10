"""
This module provides a command line client for the aptdaemon
"""
# Copyright (C) 2008-2009 Sebastian Heinlein <sevel@glatzor.de>
#
# Licensed under the GNU General Public License Version 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

__all__ = ("ConsoleClient", "main")

import array
import fcntl
from gettext import gettext as _
from gettext import ngettext
import locale
from optparse import OptionParser
import os
import pty
import re
import termios
import time
import tty
import signal
import sys

from aptsources.sourceslist import SourceEntry
from gi.repository import GLib
import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

import aptdaemon
from . import client
from . import enums
from . import errors

ANSI_BOLD = chr(27) + "[1m"
ANSI_RESET = chr(27) + "[0m"

PY3K = sys.version_info.major > 2


class ConsoleClient:
    """
    Command line interface client to aptdaemon
    """
    def __init__(self, show_terminal=True, allow_unauthenticated=False,
                 details=False):
        self._client = client.AptClient()
        self.master_fd, self.slave_fd = pty.openpty()
        self._signals = []
        signal.signal(signal.SIGINT, self._on_cancel_signal)
        signal.signal(signal.SIGQUIT, self._on_cancel_signal)
        signal.signal(signal.SIGWINCH, self._on_terminal_resize)
        self._terminal_width = self._get_terminal_width()
        self._watchers = []
        self._old_tty_mode = None
        self._show_status = True
        self._status = ""
        self._percent = 0
        self._show_terminal = show_terminal
        self._details = details
        self._allow_unauthenticated = allow_unauthenticated
        self._show_progress = True
        self._status_details = ""
        self._progress_details = ""
        # Used for a spinning line to indicate a still working transaction
        self._spin_elements = "|/-\\"
        self._spin_cur = -1
        self._spin_stamp = time.time()
        self._transaction = None
        self._loop = GLib.MainLoop()

    def add_repository(self, line="", sourcesfile=""):
        """Add repository to the sources list."""
        entry = SourceEntry(line)
        self._client.add_repository(entry.type, entry.uri, entry.dist,
                                    entry.comps, entry.comment,
                                    sourcesfile,
                                    reply_handler=self._run_transaction,
                                    error_handler=self._on_exception)

    def add_vendor_key_from_file(self, path):
        """Install repository key file."""
        self._client.add_vendor_key_from_file(
            path,
            reply_handler=self._run_transaction,
            error_handler=self._on_exception)

    def add_vendor_key_from_keyserver(self, keyid, keyserver):
        """Install repository key file."""
        self._client.add_vendor_key_from_keyserver(
            keyid, keyserver,
            reply_handler=self._run_transaction,
            error_handler=self._on_exception)

    def remove_vendor_key(self, fingerprint):
        """Remove repository key."""
        self._client.remove_vendor_key(fingerprint,
                                       reply_handler=self._run_transaction,
                                       error_handler=self._on_exception)

    def install_file(self, path):
        """Install package file."""
        self._client.install_file(path, reply_handler=self._run_transaction,
                                  error_handler=self._on_exception)

    def list_trusted_vendor_keys(self):
        """List the keys of the trusted vendors."""
        def on_done(keys):
            for key in keys:
                print(key)
            self._loop.quit()
        self._client.get_trusted_vendor_keys(reply_handler=on_done,
                                             error_handler=self._on_exception)

    def commit_packages(self, install, reinstall, remove, purge, upgrade,
                        downgrade):
        """Commit changes"""
        self._client.commit_packages(install, reinstall, remove, purge,
                                     upgrade, downgrade,
                                     reply_handler=self._run_transaction,
                                     error_handler=self._on_exception)

    def fix_incomplete_install(self):
        """Fix incomplete installs"""
        self._client.fix_incomplete_install(
            reply_handler=self._run_transaction,
            error_handler=self._on_exception)

    def fix_broken_depends(self):
        """Repair broken dependencies."""
        self._client.fix_broken_depends(reply_handler=self._run_transaction,
                                        error_handler=self._on_exception)

    def update_cache(self):
        """Update cache"""
        self._client.update_cache(reply_handler=self._run_transaction,
                                  error_handler=self._on_exception)

    def upgrade_system(self, safe_mode):
        """Upgrade system"""
        self._client.upgrade_system(safe_mode,
                                    reply_handler=self._run_transaction,
                                    error_handler=self._on_exception)

    def reconfigure(self, packages, priority):
        """Reconfigure packages."""
        self._client.reconfigure(packages, priority,
                                 reply_handler=self._run_transaction,
                                 error_handler=self._on_exception)

    def clean(self):
        """Clean archives."""
        self._client.clean(reply_handler=self._run_transaction,
                           error_handler=self._on_exception)

    def run(self):
        """Start the console client application."""
        try:
            self._loop.run()
        except KeyboardInterrupt:
            pass

    def _set_transaction(self, transaction):
        """Monitor the given transaction"""
        for handler in self._signals:
            GLib.source_remove(handler)
        self._transaction = transaction
        self._signals = []
        self._signals.append(transaction.connect("terminal-attached-changed",
                                                 self._on_terminal_attached))
        self._signals.append(transaction.connect("status-changed",
                                                 self._on_status))
        self._signals.append(transaction.connect("status-details-changed",
                                                 self._on_status_details))
        self._signals.append(transaction.connect("progress-changed",
                                                 self._on_progress))
        self._signals.append(transaction.connect("progress-details-changed",
                                                 self._on_progress_details))
        self._signals.append(transaction.connect("finished", self._on_exit))
        if self._show_terminal:
            transaction.set_terminal(os.ttyname(self.slave_fd))
        transaction.set_allow_unauthenticated(self._allow_unauthenticated)

    def _on_exit(self, trans, enum):
        """Callback for the exit state of the transaction"""
        # Make sure to dettach the terminal
        self._detach()
        if self._show_progress:
            output = "[+] 100%% %s %-*.*s%s\n" % (
                ANSI_BOLD,
                self._terminal_width - 9,
                self._terminal_width - 9,
                enums.get_exit_string_from_enum(enum),
                ANSI_RESET)
            sys.stderr.write(output)

        if enum == enums.EXIT_FAILED:
            msg = "%s: %s\n%s\n\n%s" % (
                _("ERROR"),
                enums.get_error_string_from_enum(trans.error_code),
                enums.get_error_description_from_enum(trans.error_code),
                trans.error_details)
            print(msg)
        self._loop.quit()

    def _on_terminal_attached(self, transaction, attached):
        """Callback for the terminal-attachabed-changed signal of the
        transaction.
        """
        if self._show_terminal and attached and not self._watchers:
            self._clear_progress()
            self._show_progress = False
            self._attach()
        elif not attached:
            self._show_progress = True
            self._detach()

    def _on_status(self, transaction, status):
        """Callback for the Status signal of the transaction"""
        self._status = enums.get_status_string_from_enum(status)
        self._update_progress()

    def _on_status_details(self, transaction, text):
        """Callback for the StatusDetails signal of the transaction."""
        self._status_details = text
        self._update_progress()

    def _on_progress_details(self, transaction, items_done, items_total,
                             bytes_done, bytes_total, speed, eta):
        """Callback for the ProgressDetails signal of the transaction."""
        if bytes_total and speed:
            self._progress_details = (
                _("Downloaded %(cur)sB of %(total)sB at %(rate)sB/s") %
                {'cur': client.get_size_string(bytes_done),
                 'total': client.get_size_string(bytes_total),
                 'rate': client.get_size_string(speed)})
        elif bytes_total:
            self._progress_details = (
                _("Downloaded %(cur)sB of %(total)sB") %
                {'cur': client.get_size_string(bytes_done),
                 'total': client.get_size_string(bytes_total)})
        else:
            self._progress_details = ""
        self._update_progress()

    def _on_progress(self, transaction, percent):
        """Callback for the Progress signal of the transaction"""
        self._percent = percent
        self._update_progress()

    def _update_progress(self):
        """Update the progress bar."""
        if not self._show_progress:
            return
        text = ANSI_BOLD + self._status + ANSI_RESET
        if self._status_details:
            text += " " + self._status_details
        if self._progress_details:
            text += " (%s)" % self._progress_details
        text_width = self._terminal_width - 9
        # Spin the progress line (maximum 5 times a second)
        if self._spin_stamp + 0.2 < time.time():
            self._spin_cur = (self._spin_cur + 1) % len(self._spin_elements)
            self._spin_stamp = time.time()
        spinner = self._spin_elements[self._spin_cur]
        # Show progress information if available
        if self._percent > 100:
            percent = "---"
        else:
            percent = self._percent
        sys.stderr.write("[%s] " % spinner +
                         "%3.3s%% " % percent +
                         "%-*.*s" % (text_width, text_width, text) + "\r")

    def _update_custom_progress(self, msg, percent=None, spin=True):
        """Update the progress bar with a custom status message."""
        text = ANSI_BOLD + msg + ANSI_RESET
        text_width = self._terminal_width - 9
        # Spin the progress line (maximum 5 times a second)
        if spin:
            self._spin_cur = (self._spin_cur + 1) % len(self._spin_elements)
            self._spin_stamp = time.time()
            spinner = self._spin_elements[self._spin_cur]
        else:
            spinner = "+"
        # Show progress information if available
        if percent is None:
            percent = "---"
        sys.stderr.write("[%s] " % spinner +
                         "%3.3s%% " % percent +
                         "%-*.*s" % (text_width, text_width, text) + "\r")
        return True

    def _stop_custom_progress(self):
        """Stop the spinner which shows non trans status messages."""
        if self._progress_id is not None:
            GLib.source_remove(self._progress_id)

    def _clear_progress(self):
        """Clear progress information on stderr."""
        sys.stderr.write("%-*.*s\r" % (self._terminal_width,
                                       self._terminal_width,
                                       " "))

    def _on_cancel_signal(self, signum, frame):
        """Callback for a cancel signal."""
        if (self._transaction and
                self._transaction.status != enums.STATUS_SETTING_UP):
            self._transaction.cancel()
        else:
            self._loop.quit()

    def _on_terminal_resize(self, signum, frame):
        """Callback for a changed terminal size."""
        self._terminal_width = self._get_terminal_width()
        self._update_progress()

    def _detach(self):
        """Dettach the controlling terminal to aptdaemon."""
        for wid in self._watchers:
            GLib.source_remove(wid)
        if self._old_tty_mode:
            tty.tcsetattr(pty.STDIN_FILENO, tty.TCSAFLUSH,
                          self._old_tty_mode)

    def _attach(self):
        """Attach the controlling terminal to aptdaemon.
        Based on pty.spwan()
        """
        try:
            self._old_tty_mode = tty.tcgetattr(pty.STDIN_FILENO)
            tty.setraw(pty.STDIN_FILENO)
        except tty.error:    # This is the same as termios.error
            self._old_tty_mode = None
        flags = GLib.IO_IN | GLib.IO_ERR | GLib.IO_HUP
        self._watchers.append(
            GLib.io_add_watch(pty.STDIN_FILENO,
                              GLib.PRIORITY_HIGH_IDLE, flags,
                              self._copy_io, self.master_fd))
        self._watchers.append(
            GLib.io_add_watch(self.master_fd, GLib.PRIORITY_HIGH_IDLE,
                              flags, self._copy_io, pty.STDOUT_FILENO))

    def _copy_io(self, source, condition, target):
        """Callback to copy data between terminals."""
        if condition == GLib.IO_IN:
            data = os.read(source, 1024)
            if target:
                os.write(target, data)
            return True
        os.close(source)
        return False

    def _get_terminal_width(self):
        """Return the witdh in characters of the current terminal."""
        try:
            return array.array("h", fcntl.ioctl(sys.stderr, termios.TIOCGWINSZ,
                                                "\0" * 8))[1]
        except IOError:
            # Fallback to the "default" size
            return 80

    def _on_exception(self, error):
        """Error callback."""
        self._detach()
        try:
            raise error
        except errors.PolicyKitError:
            msg = "%s %s\n\n%s" % (_("ERROR:"),
                                   _("You are not allowed to perform "
                                     "this action."),
                                   error.get_dbus_message())
        except dbus.DBusException:
            msg = "%s %s - %s" % (_("ERROR:"), error.get_dbus_name(),
                                  error.get_dbus_message())
        except:
            msg = str(error)
        self._loop.quit()
        sys.exit(msg)

    def _run_transaction(self, trans):
        """Callback which runs a requested transaction."""
        self._set_transaction(trans)
        self._stop_custom_progress()
        if self._transaction.role in [enums.ROLE_UPDATE_CACHE,
                                      enums.ROLE_ADD_VENDOR_KEY_FILE,
                                      enums.ROLE_ADD_VENDOR_KEY_FROM_KEYSERVER,
                                      enums.ROLE_REMOVE_VENDOR_KEY,
                                      enums.ROLE_FIX_INCOMPLETE_INSTALL]:
            # TRANSLATORS: status message
            self._progress_id = GLib.timeout_add(250,
                                                 self._update_custom_progress,
                                                 _("Queuing"))
            self._transaction.run(
                error_handler=self._on_exception,
                reply_handler=lambda: self._stop_custom_progress())
        else:
            # TRANSLATORS: status message
            self._progress_id = GLib.timeout_add(250,
                                                 self._update_custom_progress,
                                                 _("Resolving dependencies"))
            self._transaction.simulate(reply_handler=self._show_changes,
                                       error_handler=self._on_exception)

    def _show_changes(self):
        def show_packages(pkgs):
            """Format the pkgs in a nice way."""
            line = " "
            pkgs.sort()
            for pkg in pkgs:
                try:
                    name, version = pkg.split("=", 1)[0:2]
                except ValueError:
                    name = pkg
                    version = None
                if self._details and version:
                    output = "%s=%s" % (name, version)
                else:
                    output = name
                if (len(line) + 1 + len(output) > self._terminal_width and
                        line != " "):
                    print(line)
                    line = " "
                line += " %s" % output
            if line != " ":
                print(line)
        self._stop_custom_progress()
        self._clear_progress()
        (installs, reinstalls, removals, purges, upgrades,
            downgrades) = self._transaction.packages
        (dep_installs, dep_reinstalls, dep_removals, dep_purges, dep_upgrades,
            dep_downgrades, dep_kepts) = self._transaction.dependencies
        installs.extend(dep_installs)
        upgrades.extend(dep_upgrades)
        removals.extend(purges)
        removals.extend(dep_removals)
        removals.extend(dep_purges)
        reinstalls.extend(dep_reinstalls)
        downgrades.extend(dep_downgrades)
        kepts = dep_kepts
        if installs:
            # TRANSLATORS: %s is the number of packages
            print((ngettext("The following NEW package will be installed "
                            "(%(count)s):",
                            "The following NEW packages will be installed "
                            "(%(count)s):",
                            len(installs)) % {"count": len(installs)}))
            show_packages(installs)
        if upgrades:
            # TRANSLATORS: %s is the number of packages
            print((ngettext("The following package will be upgraded "
                            "(%(count)s):",
                            "The following packages will be upgraded "
                            "(%(count)s):",
                            len(upgrades)) % {"count": len(upgrades)}))
            show_packages(upgrades)
        if removals:
            # TRANSLATORS: %s is the number of packages
            print((ngettext("The following package will be REMOVED "
                            "(%(count)s):",
                            "The following packages will be REMOVED "
                            "(%(count)s):",
                            len(removals)) % {"count": len(removals)}))
            # FIXME: mark purges
            show_packages(removals)
        if downgrades:
            # TRANSLATORS: %s is the number of packages
            print((ngettext("The following package will be DOWNGRADED "
                            "(%(count)s):",
                            "The following packages will be DOWNGRADED "
                            "(%(count)s):",
                            len(downgrades)) % {"count": len(downgrades)}))
            show_packages(downgrades)
        if reinstalls:
            # TRANSLATORS: %s is the number of packages
            print((ngettext("The following package will be reinstalled "
                            "(%(count)s):",
                            "The following packages will be reinstalled "
                            "(%(count)s):",
                            len(reinstalls)) % {"count": len(reinstalls)}))
            show_packages(reinstalls)
        if kepts:
            print((ngettext("The following package has been kept back "
                            "(%(count)s):",
                            "The following packages have been kept back "
                            "(%(count)s):",
                            len(kepts)) % {"count": len(kepts)}))
            show_packages(kepts)

        if self._transaction.download:
            print(_("Need to get %sB of archives.") %
                  client.get_size_string(self._transaction.download))
        if self._transaction.space > 0:
            print(_("After this operation, %sB of additional disk space "
                    "will be used.") %
                  client.get_size_string(self._transaction.space))
        elif self._transaction.space < 0:
            print(_("After this operation, %sB of additional disk space "
                    "will be freed.") %
                  client.get_size_string(self._transaction.space))
        if (self._transaction.space or self._transaction.download or
                installs or upgrades or downgrades or removals or kepts or
                reinstalls):
            try:
                if PY3K:
                    cont = input(_("Do you want to continue [Y/n]?"))
                else:
                    cont = raw_input(_("Do you want to continue [Y/n]?"))
            except EOFError:
                cont = "n"
            # FIXME: Listen to changed dependencies!
            if (not re.match(locale.nl_langinfo(locale.YESEXPR), cont) and
                    cont != ""):
                msg = enums.get_exit_string_from_enum(enums.EXIT_CANCELLED)
                self._update_custom_progress(msg, None, False)
                self._loop.quit()
                sys.exit(1)
        # TRANSLATORS: status message
        self._progress_id = GLib.timeout_add(250,
                                             self._update_custom_progress,
                                             _("Queuing"))
        self._transaction.run(
            error_handler=self._on_exception,
            reply_handler=lambda: self._stop_custom_progress())


def main():
    """Run a command line client for aptdaemon"""
    epilog = _("To operate on more than one package put the package "
               "names in quotation marks:\naptdcon --install "
               "\"foo bar\"")
    parser = OptionParser(version=aptdaemon.__version__, epilog=epilog)
    parser.add_option("-c", "--refresh", default="",
                      action="store_true", dest="refresh",
                      help=_("Refresh the cache"))
    parser.add_option("", "--fix-depends", default="",
                      action="store_true", dest="fix_depends",
                      help=_("Try to resolve broken dependencies. "
                             "Potentially dangerous operation since it could "
                             "try to remove many packages."))
    parser.add_option("", "--fix-install", default="",
                      action="store_true", dest="fix_install",
                      help=_("Try to finish a previous incompleted "
                             "installation"))
    parser.add_option("-i", "--install", default="",
                      action="store", type="string", dest="install",
                      help=_("Install the given packages"))
    parser.add_option("", "--reinstall", default="",
                      action="store", type="string", dest="reinstall",
                      help=_("Reinstall the given packages"))
    parser.add_option("-r", "--remove", default="",
                      action="store", type="string", dest="remove",
                      help=_("Remove the given packages"))
    parser.add_option("-p", "--purge", default="",
                      action="store", type="string", dest="purge",
                      help=_("Remove the given packages including "
                             "configuration files"))
    parser.add_option("-u", "--upgrade", default="",
                      action="store", type="string", dest="upgrade",
                      help=_("Install the given packages"))
    parser.add_option("", "--downgrade", default="",
                      action="store", type="string", dest="downgrade",
                      help=_("Downgrade the given packages"))
    parser.add_option("", "--upgrade-system",
                      action="store_true", dest="safe_upgrade",
                      help=_("Deprecated: Please use "
                             "--safe-upgrade"))
    parser.add_option("", "--safe-upgrade",
                      action="store_true", dest="safe_upgrade",
                      help=_("Upgrade the system in a safe way"))
    parser.add_option("", "--full-upgrade",
                      action="store_true", dest="full_upgrade",
                      help=_("Upgrade the system, possibly installing and "
                             "removing packages"))
    parser.add_option("", "--add-vendor-key", default="",
                      action="store", type="string", dest="add_vendor_key",
                      help=_("Add the vendor to the trusted ones"))
    parser.add_option("", "--add-vendor-key-from-keyserver", default="",
                      action="store", type="string",
                      help=_("Add the vendor keyid (also needs "
                             "--keyserver)"))
    parser.add_option("", "--keyserver", default="",
                      action="store", type="string",
                      help=_("Use the given keyserver for looking up "
                             "keys"))
    parser.add_option("", "--add-repository", default="",
                      action="store", type="string", dest="add_repository",
                      help=_("Add new repository from the given "
                             "deb-line"))
    parser.add_option("", "--sources-file", action="store", default="",
                      type="string", dest="sources_file",
                      help=_("Specify an alternative sources.list.d file to "
                             "which repositories should be added."))
    parser.add_option("", "--list-trusted-vendors", default="",
                      action="store_true", dest="list_trusted_vendor_keys",
                      help=_("List trusted vendor keys"))
    parser.add_option("", "--remove-vendor-key", default="",
                      action="store", type="string", dest="remove_vendor_key",
                      help=_("Remove the trusted key of the given "
                             "fingerprint"))
    parser.add_option("", "--clean",
                      action="store_true", dest="clean",
                      help=_("Remove downloaded package files"))
    parser.add_option("", "--reconfigure", default="",
                      action="store", type="string", dest="reconfigure",
                      help=_("Reconfigure installed packages. Optionally the "
                             "minimum priority of questions can be "
                             "specified"))
    parser.add_option("", "--priority", default="default",
                      action="store", type="string", dest="priority",
                      help=_("The minimum debconf priority of question to "
                             "be displayed"))
    parser.add_option("", "--hide-terminal",
                      action="store_true", dest="hide_terminal",
                      help=_("Do not attach to the apt terminal"))
    parser.add_option("", "--allow-unauthenticated",
                      action="store_true", dest="allow_unauthenticated",
                      default=False,
                      help=_("Allow packages from unauthenticated "
                             "sources"))
    parser.add_option("-d", "--show-details",
                      action="store_true", dest="details",
                      help=_("Show additional information about the packages. "
                             "Currently only the version number"))
    (options, args) = parser.parse_args()
    con = ConsoleClient(show_terminal=not options.hide_terminal,
                        allow_unauthenticated=options.allow_unauthenticated,
                        details=options.details)
    # TRANSLATORS: status message
    con._progress_id = GLib.timeout_add(250, con._update_custom_progress,
                                        _("Waiting for authentication"))
    if options.safe_upgrade:
        con.upgrade_system(True)
    elif options.full_upgrade:
        con.upgrade_system(False)
    elif options.refresh:
        con.update_cache()
    elif options.reconfigure:
        con.reconfigure(options.reconfigure.split(), options.priority)
    elif options.clean:
        con.clean()
    elif options.fix_install:
        con.fix_incomplete_install()
    elif options.fix_depends:
        con.fix_broken_depends()
    elif options.install and options.install.endswith(".deb"):
        con.install_file(options.install)
    elif (options.install or options.reinstall or options.remove or
          options.purge or options.upgrade or options.downgrade):
        con.commit_packages(options.install.split(),
                            options.reinstall.split(),
                            options.remove.split(),
                            options.purge.split(),
                            options.upgrade.split(),
                            options.downgrade.split())
    elif options.add_repository:
        con.add_repository(options.add_repository, options.sources_file)
    elif options.add_vendor_key:
        # FIXME: Should detect if from stdin or file
        con.add_vendor_key_from_file(options.add_vendor_key)
    elif options.add_vendor_key_from_keyserver and options.keyserver:
        con.add_vendor_key_from_keyserver(
            options.add_vendor_key_from_keyserver,
            options.keyserver)
    elif options.remove_vendor_key:
        con.remove_vendor_key(options.remove_vendor_key)
    elif options.list_trusted_vendor_keys:
        con.list_trusted_vendor_keys()
    else:
        parser.print_help()
        sys.exit(1)
    con.run()

if __name__ == "__main__":
    main()
