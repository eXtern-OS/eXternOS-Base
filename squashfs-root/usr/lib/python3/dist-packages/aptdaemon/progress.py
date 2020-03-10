#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Progress handlers for APT operations"""
# Copyright (C) 2008-2009 Sebastian Heinlein <glatzor@ubuntu.com>
#
# Licensed under the GNU General Public License Version 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

__all__ = ("DaemonAcquireProgress", "DaemonOpenProgress",
           "DaemonInstallProgress", "DaemonDpkgInstallProgress",
           "DaemonForkProgress", "DaemonDpkgRecoverProgress",
           "DaemonLintianProgress")

import locale
import logging
import os
import platform
import re
import signal
import sys
import termios
import time
import traceback
import tty

import apt_pkg
import apt.progress.base
import apt.debfile
from gi.repository import GLib

from . import enums
from . import lock
from .loop import mainloop
from .utils import IsoCodes

# Required to get translatable strings extraced by xgettext
_ = lambda s: s

log = logging.getLogger("AptDaemon.Worker")
log_terminal = logging.getLogger("AptDaemon.Worker.Terminal")

INSTALL_TIMEOUT = 10 * 60

MAP_DPKG_STAGE = {"install": enums.PKG_INSTALLING,
                  "configure": enums.PKG_CONFIGURING,
                  "remove": enums.PKG_REMOVING,
                  "trigproc": enums.PKG_RUNNING_TRIGGER,
                  "purge": enums.PKG_PURGING,
                  "disappear": enums.PKG_DISAPPEARING,
                  "upgrade": enums.PKG_UPGRADING}

REGEX_ANSI_ESCAPE_CODE = chr(27) + "\[[;?0-9]*[A-Za-z]"


class DaemonOpenProgress(apt.progress.base.OpProgress):

    """Handles the progress of the cache opening."""

    def __init__(self, transaction, begin=0, end=100, quiet=False):
        """Initialize a new DaemonOpenProgress instance.

        Keyword arguments:
        transaction -- corresponding transaction D-Bus object
        begin -- begin of the progress range (defaults to 0)
        end -- end of the progress range (defaults to 100)
        quiet -- do not emit any progress information for the transaction
        """
        apt.progress.base.OpProgress.__init__(self)
        self._transaction = transaction
        self.steps = [begin + (end - begin) * modifier
                      # the final 1.00 will not be used but we still
                      # need it here for the final pop()
                      for modifier in [0.25, 0.50, 0.75, 1.00, 1.00]]
        self.progress_begin = float(begin)
        self.progress_end = self.steps.pop(0)
        self.progress = 0
        self.quiet = quiet

    def update(self, percent=None):
        """Callback for progress updates.

        Keyword argument:
        percent - current progress in percent
        """
        # python-apt 0.8 does not include "percent" anymore in the call
        percent = percent or self.percent
        if percent < 101:
            progress = int(self.progress_begin + (percent / 100) *
                           (self.progress_end - self.progress_begin))
            if self.progress == progress:
                return
        else:
            progress = 101
        self.progress = progress
        if not self.quiet:
            self._transaction.progress = progress

    def done(self):
        """Callback after completing a step.

        Sets the progress range to the next interval."""
        # ensure that progress is updated
        self.progress = self.progress_end
        # switch to new progress_{begin, end}
        self.progress_begin = self.progress_end
        try:
            self.progress_end = self.steps.pop(0)
        except:
            log.warning("An additional step to open the cache is required")


class DaemonAcquireProgress(apt.progress.base.AcquireProgress):
    '''
    Handle the package download process
    '''
    def __init__(self, transaction, begin=0, end=100):
        apt.progress.base.AcquireProgress.__init__(self)
        self.transaction = transaction
        self.progress_end = end
        self.progress_begin = begin
        self.progress = 0

    def _emit_acquire_item(self, item, total_size=0, current_size=0):
        if item.owner.status == apt_pkg.AcquireItem.STAT_DONE:
            status = enums.DOWNLOAD_DONE
            # Workaround for a bug in python-apt, see lp: #581886
            current_size = item.owner.filesize
        elif item.owner.status == apt_pkg.AcquireItem.STAT_AUTH_ERROR:
            status = enums.DOWNLOAD_AUTH_ERROR
        elif item.owner.status == apt_pkg.AcquireItem.STAT_FETCHING:
            status = enums.DOWNLOAD_FETCHING
        elif item.owner.status == apt_pkg.AcquireItem.STAT_ERROR:
            status = enums.DOWNLOAD_ERROR
        elif item.owner.status == apt_pkg.AcquireItem.STAT_IDLE:
            status = enums.DOWNLOAD_IDLE
        else:
            # Workaround: The StatTransientNetworkError status isn't mapped
            # by python-apt, see LP #602578
            status = enums.DOWNLOAD_NETWORK_ERROR
        if (item.owner.status != apt_pkg.AcquireItem.STAT_DONE and
                item.owner.error_text):
            msg = item.owner.error_text
        elif item.owner.mode:
            msg = item.owner.mode
        else:
            msg = ""
        self.transaction.progress_download = (
            item.uri, status, item.shortdesc,
            total_size | item.owner.filesize,
            current_size | item.owner.partialsize,
            msg)

    def _emit_status_details(self, items):
        """Emit the transaction status details."""
        names = set()
        for item in items:
            if item.owner.id:
                names.add(item.owner.id)
            else:
                names.add(item.shortdesc)
        if names:
            # TRANSLATORS: %s is a list of package names
            msg = self.transaction.ngettext("Downloading %(files)s",
                                            "Downloading %(files)s",
                                            len(items)) % {"files":
                                                           " ".join(names)}
            self.transaction.status_details = msg

    def done(self, item):
        """Invoked when an item is successfully and completely fetched."""
        self._emit_acquire_item(item)

    def fail(self, item):
        """Invoked when an item could not be fetched."""
        self._emit_acquire_item(item)

    def fetch(self, item):
        """Invoked when some of the item's data is fetched."""
        self._emit_acquire_item(item)

    def ims_hit(self, item):
        """Invoked when an item is confirmed to be up-to-date.

        Invoked when an item is confirmed to be up-to-date. For instance,
        when an HTTP download is informed that the file on the server was
        not modified.
        """
        self._emit_acquire_item(item)

    def pulse(self, owner):
        """Callback to update progress information"""
        if self.transaction.cancelled:
            return False
        self.transaction.progress_details = (self.current_items,
                                             self.total_items,
                                             self.current_bytes,
                                             self.total_bytes,
                                             self.current_cps,
                                             self.elapsed_time)
        percent = (((self.current_bytes + self.current_items) * 100.0) /
                   float(self.total_bytes + self.total_items))
        progress = int(self.progress_begin + percent / 100 *
                       (self.progress_end - self.progress_begin))
        # If the progress runs backwards emit an illegal progress value
        # e.g. during cache updates.
        if self.progress > progress:
            self.transaction.progress = 101
        else:
            self.transaction.progress = progress
            self.progress = progress
        # Show all currently downloaded files
        items = []
        for worker in owner.workers:
            if not worker.current_item:
                continue
            self._emit_acquire_item(worker.current_item,
                                    worker.total_size,
                                    worker.current_size)
            items.append(worker.current_item)
        self._emit_status_details(items)
        while GLib.main_context_default().pending():
            GLib.main_context_default().iteration()
        return True

    def start(self):
        """Callback at the beginning of the operation"""
        self.transaction.status = enums.STATUS_DOWNLOADING
        self.transaction.cancellable = True

    def stop(self):
        """Callback at the end of the operation"""
        self.transaction.progress_details = (0, 0, 0, 0, 0.0, 0)
        self.transaction.progress = self.progress_end
        self.transaction.cancellable = False

    def media_change(self, medium, drive):
        """Callback for media changes"""
        self.transaction.required_medium = medium, drive
        self.transaction.paused = True
        self.transaction.status = enums.STATUS_WAITING_MEDIUM
        while self.transaction.paused:
            GLib.main_context_default().iteration()
        self.transaction.status = enums.STATUS_DOWNLOADING
        if self.transaction.cancelled:
            return False
        return True


class DaemonAcquireRepoProgress(DaemonAcquireProgress):

    """Handle the repository information download"""

    def __init__(self, transaction, begin=0, end=100):
        DaemonAcquireProgress.__init__(self, transaction, begin, end)
        self.languages = IsoCodes("iso_639", tag="iso_639_1_code",
                                  fallback_tag="iso_639_2T_code")
        self.regions = IsoCodes("iso_3166", "alpha_2_code")
        self.progress = 101

    def start(self):
        """Callback at the beginning of the operation"""
        self.transaction.status = enums.STATUS_DOWNLOADING_REPO
        self.transaction.cancellable = True

    def _emit_status_details(self, items):
        """Emit the transaction status details."""
        repos = set()
        for item in items:
            # We are only interested in the hostname currently
            try:
                repos.add(item.description.split()[0].split("://")[-1])
            except IndexError:
                # TRANSLATORS: the string is used as a fallback if we cannot
                #             get the URI of a local repository
                repos.add(self.transaction.gettext("local repository"))
        if repos:
            # TRANSLATORS: %s is a list of repository names
            msg = self.transaction.ngettext("Downloading from %s",
                                            "Downloading from %s",
                                            len(repos)) % " ".join(repos)
            self.transaction.status_details = msg

    def _emit_acquire_item(self, item, total_size=0, current_size=0):
        if item.owner.status == apt_pkg.AcquireItem.STAT_DONE:
            status = enums.DOWNLOAD_DONE
            # Workaround for a bug in python-apt, see lp: #581886
            current_size = item.owner.filesize
        elif item.owner.status == apt_pkg.AcquireItem.STAT_AUTH_ERROR:
            status = enums.DOWNLOAD_AUTH_ERROR
        elif item.owner.status == apt_pkg.AcquireItem.STAT_FETCHING:
            status = enums.DOWNLOAD_FETCHING
        elif item.owner.status == apt_pkg.AcquireItem.STAT_ERROR:
            status = enums.DOWNLOAD_ERROR
        elif item.owner.status == apt_pkg.AcquireItem.STAT_IDLE:
            status = enums.DOWNLOAD_IDLE
        else:
            # Workaround: The StatTransientNetworkError status isn't mapped
            # by python-apt, see LP #602578
            status = enums.DOWNLOAD_NETWORK_ERROR
        if (item.owner.status != apt_pkg.AcquireItem.STAT_DONE and
                item.owner.error_text):
            msg = item.owner.error_text
        elif item.owner.mode:
            msg = item.owner.mode
        else:
            msg = ""
        # Get a better description than e.g. Packages or Sources
        host, dist = item.description.split()[0:2]
        try:
            host = host.split("://")[1]
        except IndexError:
            # TRANSLATORS: the string is used as a fallback if we cannot
            #             get the URI of a local repository
            desc = self.transaction.gettext("local repository")
        repo = "%s %s" % (host, dist)
        if item.shortdesc == "InRelease":
            # TRANSLATORS: repo is the name of a repository
            desc = self.transaction.gettext("Structure of %s") % repo
        elif item.shortdesc == "Release":
            # TRANSLATORS: repo is the name of a repository
            desc = self.transaction.gettext("Description of %s") % repo
        elif item.shortdesc == "Release.gpg":
            # TRANSLATORS: repo is the name of a repository
            desc = self.transaction.gettext("Description signature "
                                            "of %s") % repo
        elif item.shortdesc.startswith("Packages"):
            # TRANSLATORS: repo is the name of a repository
            desc = self.transaction.gettext(
                "Available packages from %s") % repo
        elif item.shortdesc.startswith("Sources"):
            # TRANSLATORS: repo is the name of a repository
            desc = self.transaction.gettext(
                "Available sources from %s") % repo
        elif item.shortdesc == "TranslationIndex":
            # TRANSLATORS: repo is the name of a repository
            desc = self.transaction.gettext("Available translations from "
                                            "%s") % repo
        elif item.shortdesc.startswith("Translation-"):
            lang_code = item.shortdesc.split("-", 1)[-1]
            try:
                lang_code, region_code = lang_code.split("_")
            except ValueError:
                region_code = None
            lang = self.languages.get_localised_name(lang_code,
                                                     self.transaction.locale)
            region = self.regions.get_localised_name(region_code,
                                                     self.transaction.locale)
            if lang and region:
                # TRANSLATORS: The first %s is the name of a language. The
                #             second one the name of the region/country. Th
                #             third %s is the name of the repository
                desc = self.transaction.gettext(
                    "Translations for %s (%s) from %s") % (lang, region, repo)
            elif lang:
                # TRANSLATORS: %s is the name of a language. The second one is
                #             the name of the repository
                desc = self.transaction.gettext("Translations for %s from "
                                                "%s") % (lang, repo)
            else:
                # TRANSLATORS: %s is the code of a language, e.g. ru_RU.
                #             The second one is the name of the repository
                desc = self.transaction.gettext("Translations (%s) from "
                                                "%s") % (lang_code, repo)
        else:
            desc = item.shortdesc
        self.transaction.progress_download = (
            item.uri, status, desc, total_size | item.owner.filesize,
            current_size | item.owner.partialsize, msg)


class DaemonForkProgress(object):

    """Forks and executes a given method in the child process while
    monitoring the output and return state.

    During the run() call the mainloop will be iterated.

    Furthermore a status file descriptor is available to communicate
    with the child process.
    """

    def __init__(self, transaction, begin=50, end=100):
        self.transaction = transaction
        self.status = ""
        self.progress = 0
        self.progress_begin = begin
        self.progress_end = end
        self._child_exit = -1
        self.last_activity = 0
        self.child_pid = 0
        self.status_parent_fd, self.status_child_fd = os.pipe()
        if hasattr(os, "set_inheritable"):
            os.set_inheritable(self.status_parent_fd, True)
            os.set_inheritable(self.status_child_fd, True)
        self.output = ""
        self._line_buffer = ""

    def __enter__(self):
        self.start_update()
        return self

    def __exit__(self, etype, evalue, etb):
        self.finish_update()

    def start_update(self):
        log.debug("Start update")
        self.transaction.status = enums.STATUS_COMMITTING
        self.transaction.term_attached = True
        self.last_activity = time.time()
        self.start_time = time.time()

    def finish_update(self):
        """Callback at the end of the operation"""
        self.transaction.term_attached = False

    def _child(self, method, *args):
        """Call the given method or function with the
        corrsponding arguments in the child process.

        This method should be replace in subclasses.
        """
        method(*args)
        time.sleep(0.5)
        os._exit(0)

    def run(self, *args, **kwargs):
        """Setup monitoring, fork and call the self._child() method in the
        child process with the given arguments.
        """
        log.debug("Run")
        terminal_fd = None
        if self.transaction.terminal:
            try:
                # Save the settings of the transaction terminal and set to
                # raw mode
                terminal_fd = os.open(self.transaction.terminal,
                                      os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
                terminal_attr = termios.tcgetattr(terminal_fd)
                tty.setraw(terminal_fd, termios.TCSANOW)
            except (OSError, termios.error):
                # Switch to non-interactive
                self.transaction.terminal = ""
        pid = self._fork()
        if pid == 0:
            os.close(self.status_parent_fd)
            try:
                self._setup_child()
                self._child(*args, **kwargs)
            except Exception:
                traceback.print_exc()
            finally:
                # Give the parent process enough time to catch the output
                time.sleep(1)
                # Abort the subprocess immediatelly on any unhandled
                # failure - otherwise the atexit methods would
                # be called, e.g. the frozen status decorator
                os._exit(apt_pkg.PackageManager.RESULT_FAILED)
        else:
            self.child_pid = pid
            os.close(self.status_child_fd)
        log.debug("Child pid: %s", pid)
        watchers = []
        flags = GLib.IO_IN | GLib.IO_ERR | GLib.IO_HUP
        if self.transaction.terminal:
            # Setup copying of i/o between the controlling terminals
            watchers.append(GLib.io_add_watch(terminal_fd,
                                              GLib.PRIORITY_HIGH_IDLE,
                                              flags,
                                              self._copy_io))
        watchers.append(GLib.io_add_watch(self.master_fd,
                                          GLib.PRIORITY_HIGH_IDLE, flags,
                                          self._copy_io_master, terminal_fd))
        # Monitor the child process
        watchers.append(
            GLib.child_watch_add(GLib.PRIORITY_HIGH_IDLE,
                                 pid, self._on_child_exit))
        # Watch for status updates
        watchers.append(GLib.io_add_watch(self.status_parent_fd,
                                          GLib.PRIORITY_HIGH_IDLE,
                                          GLib.IO_IN,
                                          self._on_status_update))
        while self._child_exit == -1:
            GLib.main_context_default().iteration()
        for id in watchers:
            GLib.source_remove(id)
        # Restore the settings of the transaction terminal
        if terminal_fd:
            try:
                termios.tcsetattr(terminal_fd, termios.TCSADRAIN,
                                  terminal_attr)
            except termios.error:
                pass
        # Make sure all file descriptors are closed
        for fd in [self.master_fd, self.status_parent_fd, terminal_fd]:
            try:
                os.close(fd)
            except (OSError, TypeError):
                pass
        return os.WEXITSTATUS(self._child_exit)

    def _on_child_exit(self, pid, condition):
        log.debug("Child exited: %s", condition)
        self._child_exit = condition
        return False

    def _on_status_update(self, source, condition):
        """Callback for changes on the status file descriptor.

        The method has to return True to keep the monitoring alive. If
        it returns False the monitoring will stop.

        Replace this method in your subclass if you use the status fd.
        """
        return False

    def _fork(self):
        """Fork and create a master/slave pty pair by which the forked process
        can be controlled.
        """
        pid, self.master_fd = os.forkpty()
        return pid

    def _setup_child(self):
        """Setup the environment of the child process."""
        def interrupt_handler(signum, frame):
            # Exit the child immediately if we receive the interrupt
            # signal or a Ctrl+C - otherwise the atexit methods would
            # be called, e.g. the frozen status decorator
            os._exit(apt_pkg.PackageManager.RESULT_FAILED)
        signal.signal(signal.SIGINT, interrupt_handler)
        # Make sure that exceptions of the child are not caught by apport
        sys.excepthook = sys.__excepthook__

        mainloop.quit()
        # force terminal messages in dpkg to be untranslated, the
        # status-fd or debconf prompts will not be affected
        os.environ["DPKG_UNTRANSLATED_MESSAGES"] = "1"
        # We also want untranslated status messages from apt
        locale.setlocale(locale.LC_ALL, "C")
        # Switch to the language of the user
        if self.transaction.locale:
            os.putenv("LANG", self.transaction.locale)
        # Either connect to the controllong terminal or switch to
        # non-interactive mode
        if not self.transaction.terminal:
            # FIXME: we should check for "mail" or "gnome" here
            #        and not unset in this case
            os.putenv("APT_LISTCHANGES_FRONTEND", "none")
            os.putenv("APT_LISTBUGS_FRONTEND", "none")
        else:
            os.putenv("TERM", "linux")
        # Run debconf through a proxy if available
        if self.transaction.debconf:
            os.putenv("DEBCONF_PIPE", self.transaction.debconf)
            os.putenv("DEBIAN_FRONTEND", "passthrough")
            if log.level == logging.DEBUG:
                os.putenv("DEBCONF_DEBUG", ".")
        elif not self.transaction.terminal:
            os.putenv("DEBIAN_FRONTEND", "noninteractive")
        # Proxy configuration
        if self.transaction.http_proxy:
            apt_pkg.config.set("Acquire::http::Proxy",
                               self.transaction.http_proxy)
        # Mark changes as being make by aptdaemon
        cmd = "aptdaemon role='%s' sender='%s'" % (self.transaction.role,
                                                   self.transaction.sender)
        apt_pkg.config.set("CommandLine::AsString", cmd)

    def _copy_io_master(self, source, condition, target):
        if condition == GLib.IO_IN:
            self.last_activity = time.time()
            try:
                char_byte = os.read(source, 1)
            except OSError:
                log.debug("Faild to read from master")
                return True
            # Write all the output from dpkg to a log
            char = char_byte.decode("UTF-8", "ignore")
            if char == "\n":
                # Skip ANSI characters from the console output
                line = re.sub(REGEX_ANSI_ESCAPE_CODE, "", self._line_buffer)
                if line:
                    log_terminal.debug(line)
                    self.output += line + "\n"
                self._line_buffer = ""
            else:
                self._line_buffer += char
            if target:
                try:
                    os.write(target, char_byte)
                except OSError:
                    log.debug("Failed to write to controlling terminal")
            return True
        try:
            os.close(source)
        except OSError:
            # Could already be closed by the clean up in run()
            pass
        return False

    def _copy_io(self, source, condition):
        if condition == GLib.IO_IN:
            try:
                char = os.read(source, 1)
                os.write(self.master_fd, char)
            except OSError:
                pass
            else:
                # Detect config file prompt answers on the console
                if (self.transaction.paused and
                        self.transaction.config_file_conflict):
                    self.transaction.config_file_conflict_resolution = None
                    self.transaction.paused = False
                return True
        os.close(source)
        return False


class DaemonLintianProgress(DaemonForkProgress):

    """Performs a lintian call."""

    def _child(self, path):
        # Avoid running lintian as root
        try:
            os.setgroups([self.transaction.gid])
        except OSError:
            pass
        os.setgid(self.transaction.gid)
        os.setuid(self.transaction.uid)

        if platform.dist()[1] == "debian":
            profile = "debian/aptdaemon"
        else:
            profile = "ubuntu/aptdaemon"
        # If HOME isn't set lintian won't try to load user profiles
        os.unsetenv("HOME")

        lintian_path = apt_pkg.config.find_file("Dir::Bin::Lintian",
                                                "/usr/bin/lintian")
        os.execlp(lintian_path, lintian_path, "--no-cfg", "--fail-on-warnings",
                  "--profile", profile, path)
        os._exit(1)


class DaemonInstallProgress(DaemonForkProgress):

    """Progress to execute APT package operations in a child process."""

    def start_update(self):
        DaemonForkProgress.start_update(self)
        lock.status_lock.release()

    def finish_update(self):
        """Callback at the end of the operation"""
        DaemonForkProgress.finish_update(self)
        lock.wait_for_lock(self.transaction, lock.status_lock)

    def _child(self, pm):
        try:
            res = pm.do_install(self.status_child_fd)
        except:
            os._exit(apt_pkg.PackageManager.RESULT_FAILED)
        else:
            os._exit(res)

    def _on_status_update(self, source, condition):
        """Parse messages from APT on the status fd."""
        log.debug("UpdateInterface")
        status_msg = ""
        try:
            while not status_msg.endswith("\n"):
                self.last_activity = time.time()
                status_msg += os.read(source, 1).decode("UTF-8", "ignore")
        except:
            return False
        try:
            (status, pkg, percent, message_raw) = status_msg.split(":", 3)
        except ValueError:
            # silently ignore lines that can't be parsed
            return True
        message = message_raw.strip()
        # print "percent: %s %s" % (pkg, float(percent)/100.0)
        if status == "pmerror":
            self._error(pkg, message)
        elif status == "pmconffile":
            # we get a string like this:
            # 'current-conffile' 'new-conffile' useredited distedited
            match = re.match("\s*\'(.*)\'\s*\'(.*)\'.*", message_raw)
            if match:
                new, old = match.group(1), match.group(2)
                self._conffile(new, old)
        elif status == "pmstatus":
            if message.startswith("Installing"):
                status_enum = enums.PKG_INSTALLING
            elif message.startswith("Installed"):
                status_enum = enums.PKG_INSTALLED
            elif message.startswith("Configuring"):
                status_enum = enums.PKG_CONFIGURING
            elif message.startswith("Preparing to configure"):
                status_enum = enums.PKG_PREPARING_CONFIGURE
            elif message.startswith("Preparing for removal of"):
                status_enum = enums.PKG_PREPARING_REMOVE
            elif message.startswith("Removing"):
                status_enum = enums.PKG_REMOVING
            elif message.startswith("Removed"):
                status_enum = enums.PKG_REMOVED
            elif message.startswith("Preparing to completely remove"):
                status_enum = enums.PKG_PREPARING_PURGE
            elif message.startswith("Completely removing"):
                status_enum = enums.PKG_PURGING
            elif message.startswith("Completely removed"):
                status_enum = enums.PKG_PURGED
            elif message.startswith("Unpacking"):
                status_enum = enums.PKG_UNPACKING
            elif message.startswith("Preparing"):
                status_enum = enums.PKG_PREPARING_INSTALL
            elif message.startswith("Noting disappearance of"):
                status_enum = enums.PKG_DISAPPEARING
            elif message.startswith("Running"):
                status_enum = enums.PKG_RUNNING_TRIGGER
            else:
                status_enum = enums.PKG_UNKNOWN
            self._status_changed(pkg, float(percent), status_enum)
        # catch a time out by sending crtl+c
        if (self.last_activity + INSTALL_TIMEOUT < time.time() and
                self.child_pid):
            log.critical("Killing child since timeout of %s s",
                         INSTALL_TIMEOUT)
            os.kill(self.child_pid, 15)
        return True

    def _status_changed(self, pkg, percent, status_enum):
        """Callback to update status information"""
        log.debug("APT status: %s, %s, %s", pkg, percent, status_enum)
        progress = self.progress_begin + percent / 100 * (self.progress_end -
                                                          self.progress_begin)
        if self.progress < progress:
            self.transaction.progress = int(progress)
            self.progress = progress
        # We use untranslated messages from apt.
        # So convert them to an enum to allow translations, see LP #641262
        # The strings are taken from apt-pkg/deb/dpkgpm.cc
        desc = enums.get_package_status_from_enum(status_enum)
        msg = self.transaction.gettext(desc) % pkg
        self.transaction.status_details = msg
        self.transaction.progress_package = (pkg, status_enum)

    def _conffile(self, current, new):
        """Callback for a config file conflict"""
        log.warning("Config file prompt: '%s' (%s)" % (current, new))
        self.transaction.config_file_conflict = (current, new)
        self.transaction.paused = True
        self.transaction.status = enums.STATUS_WAITING_CONFIG_FILE_PROMPT
        while self.transaction.paused:
            GLib.main_context_default().iteration()
        log.debug("Sending config file answer: %s",
                  self.transaction.config_file_conflict_resolution)
        if self.transaction.config_file_conflict_resolution == "replace":
            os.write(self.master_fd, b"y\n")
        elif self.transaction.config_file_conflict_resolution == "keep":
            os.write(self.master_fd, b"n\n")
        self.transaction.config_file_conflict_resolution = None
        self.transaction.config_file_conflict = None
        self.transaction.status = enums.STATUS_COMMITTING
        return True

    def _error(self, pkg, msg):
        """Callback for an error"""
        log.critical("%s: %s" % (pkg, msg))


class DaemonDpkgInstallProgress(DaemonInstallProgress):

    """Progress handler for a local Debian package installation."""

    def __init__(self, transaction, begin=101, end=101):
        DaemonInstallProgress.__init__(self, transaction, begin, end)

    def _child(self, debfile):
        args = [apt_pkg.config["Dir::Bin::DPkg"], "--status-fd",
                str(self.status_child_fd)]
        args.extend(apt_pkg.config.value_list("DPkg::Options"))
        if not self.transaction.terminal:
            args.extend(["--force-confdef", "--force-confold"])
        args.extend(["-i", debfile])
        os.execlp(apt_pkg.config["Dir::Bin::DPkg"], *args)

    def _on_status_update(self, source, condition):
        log.debug("UpdateInterface")
        status_raw = ""
        try:
            while not status_raw.endswith("\n"):
                status_raw += os.read(source, 1).decode("UTF-8", "ignore")
        except:
            return False
        try:
            status = [s.strip() for s in status_raw.split(":", 3)]
        except ValueError:
            # silently ignore lines that can't be parsed
            return True
        # Parse the status message. It can be of the following types:
        #  - "status: PACKAGE: STATUS"
        #  - "status: PACKAGE: error: MESSAGE"
        #  - "status: FILE: conffile: 'OLD' 'NEW' useredited distedited"
        #  - "processing: STAGE: PACKAGE" with STAGE is one of upgrade,
        #    install, configure, trigproc, remove, purge
        if status[0] == "status":
            # FIXME: Handle STATUS
            if status[2] == "error":
                self._error(status[1], status[3])
            elif status[2] == "conffile":
                match = re.match("\s*\'(.*)\'\s*\'(.*)\'.*", status[3])
                if match:
                    new, old = match.group(1), match.group(2)
                    self._conffile(new, old)
        elif status[0] == "processing":
            try:
                status_enum = MAP_DPKG_STAGE[status[1]]
            except KeyError:
                status_enum = enums.PKG_UNKONWN
            self._status_changed(status[2], 101, status_enum)
        return True


class DaemonDpkgRecoverProgress(DaemonDpkgInstallProgress):

    """Progress handler for dpkg --confiure -a call."""

    def _child(self):
        args = [apt_pkg.config["Dir::Bin::Dpkg"], "--status-fd",
                str(self.status_child_fd), "--configure", "-a"]
        args.extend(apt_pkg.config.value_list("Dpkg::Options"))
        if not self.transaction.terminal:
            args.extend(["--force-confdef", "--force-confold"])
        os.execlp(apt_pkg.config["Dir::Bin::DPkg"], *args)


class DaemonDpkgReconfigureProgress(DaemonDpkgInstallProgress):

    """Progress handler for dpkg-reconfigure call."""

    def _child(self, packages, priority, ):
        args = ["/usr/sbin/dpkg-reconfigure"]
        if priority != "default":
            args.extend(["--priority", priority])
        args.extend(packages)
        os.execlp("/usr/sbin/dpkg-reconfigure", *args)


# vim:ts=4:sw=4:et
