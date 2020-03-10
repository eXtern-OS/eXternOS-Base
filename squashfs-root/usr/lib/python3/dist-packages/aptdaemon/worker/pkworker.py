# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a compatibility layer to PackageKit

Copyright (C) 2007 Ali Sabil <ali.sabil@gmail.com>
Copyright (C) 2007 Tom Parker <palfrey@tevp.net>
Copyright (C) 2008-2011 Sebastian Heinlein <glatzor@ubuntu.com>

Licensed under the GNU General Public License Version 2

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

import datetime
import glob
import gzip
import locale
import logging
import os
import platform
import re
import subprocess
import tempfile
import time

import apt_pkg

from gi.repository import GObject
from gi.repository import PackageKitGlib as pk

# for optional plugin support
try:
    import pkg_resources
except ImportError:
    pkg_resources = None

from ..pkutils import (bitfield_add, bitfield_remove, bitfield_summarize,
                       bitfield_contains)
from . import enums as aptd_enums
from ..errors import TransactionFailed
from ..progress import DaemonAcquireProgress
from . import aptworker


pklog = logging.getLogger("AptDaemon.PackageKitWorker")

# Check if update-manager-core is installed to get aware of the
# latest distro releases
try:
    from UpdateManager.Core.MetaRelease import MetaReleaseCore
except ImportError:
    META_RELEASE_SUPPORT = False
else:
    META_RELEASE_SUPPORT = True

# Xapian database is optionally used to speed up package description search
XAPIAN_DB_PATH = os.environ.get("AXI_DB_PATH", "/var/lib/apt-xapian-index")
XAPIAN_DB = XAPIAN_DB_PATH + "/index"
XAPIAN_DB_VALUES = XAPIAN_DB_PATH + "/values"
XAPIAN_SUPPORT = False
try:
    import xapian
except ImportError:
    pass
else:
    if os.access(XAPIAN_DB, os.R_OK):
        pklog.debug("Use XAPIAN for the search")
        XAPIAN_SUPPORT = True

# Regular expressions to detect bug numbers in changelogs according to the
# Debian Policy Chapter 4.4. For details see the footnote 16:
# http://www.debian.org/doc/debian-policy/footnotes.html#f16
MATCH_BUG_CLOSES_DEBIAN = (
    r"closes:\s*(?:bug)?\#?\s?\d+(?:,\s*(?:bug)?\#?\s?\d+)*")
MATCH_BUG_NUMBERS = r"\#?\s?(\d+)"
# URL pointing to a bug in the Debian bug tracker
HREF_BUG_DEBIAN = "http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=%s"

MATCH_BUG_CLOSES_UBUNTU = r"lp:\s+\#\d+(?:,\s*\#\d+)*"
HREF_BUG_UBUNTU = "https://bugs.launchpad.net/bugs/%s"

# Regular expression to find cve references
MATCH_CVE = "CVE-\d{4}-\d{4}"
HREF_CVE = "http://web.nvd.nist.gov/view/vuln/detail?vulnId=%s"

# Map Debian sections to the PackageKit group name space
SECTION_GROUP_MAP = {
    "admin": pk.GroupEnum.ADMIN_TOOLS,
    "base": pk.GroupEnum.SYSTEM,
    "cli-mono": pk.GroupEnum.PROGRAMMING,
    "comm": pk.GroupEnum.COMMUNICATION,
    "database": pk.GroupEnum.SERVERS,
    "debian-installer": pk.GroupEnum.SYSTEM,
    "debug": pk.GroupEnum.PROGRAMMING,
    "devel": pk.GroupEnum.PROGRAMMING,
    "doc": pk.GroupEnum.DOCUMENTATION,
    "editors": pk.GroupEnum.PUBLISHING,
    "education": pk.GroupEnum.EDUCATION,
    "electronics": pk.GroupEnum.ELECTRONICS,
    "embedded": pk.GroupEnum.SYSTEM,
    "fonts": pk.GroupEnum.FONTS,
    "games": pk.GroupEnum.GAMES,
    "gnome": pk.GroupEnum.DESKTOP_GNOME,
    "gnu-r": pk.GroupEnum.PROGRAMMING,
    "gnustep": pk.GroupEnum.DESKTOP_OTHER,
    "graphics": pk.GroupEnum.GRAPHICS,
    "hamradio": pk.GroupEnum.COMMUNICATION,
    "haskell": pk.GroupEnum.PROGRAMMING,
    "httpd": pk.GroupEnum.SERVERS,
    "interpreters": pk.GroupEnum.PROGRAMMING,
    "introspection": pk.GroupEnum.PROGRAMMING,
    "java": pk.GroupEnum.PROGRAMMING,
    "kde": pk.GroupEnum.DESKTOP_KDE,
    "kernel": pk.GroupEnum.SYSTEM,
    "libdevel": pk.GroupEnum.PROGRAMMING,
    "libs": pk.GroupEnum.SYSTEM,
    "lisp": pk.GroupEnum.PROGRAMMING,
    "localization": pk.GroupEnum.LOCALIZATION,
    "mail": pk.GroupEnum.INTERNET,
    "math": pk.GroupEnum.SCIENCE,
    "misc": pk.GroupEnum.OTHER,
    "net": pk.GroupEnum.NETWORK,
    "news": pk.GroupEnum.INTERNET,
    "ocaml": pk.GroupEnum.PROGRAMMING,
    "oldlibs": pk.GroupEnum.LEGACY,
    "otherosfs": pk.GroupEnum.SYSTEM,
    "perl": pk.GroupEnum.PROGRAMMING,
    "php": pk.GroupEnum.PROGRAMMING,
    "python": pk.GroupEnum.PROGRAMMING,
    "ruby": pk.GroupEnum.PROGRAMMING,
    "science": pk.GroupEnum.SCIENCE,
    "shells": pk.GroupEnum.ADMIN_TOOLS,
    "sound": pk.GroupEnum.MULTIMEDIA,
    "tex": pk.GroupEnum.PUBLISHING,
    "text": pk.GroupEnum.PUBLISHING,
    "utils": pk.GroupEnum.ACCESSORIES,
    "vcs": pk.GroupEnum.PROGRAMMING,
    "video": pk.GroupEnum.MULTIMEDIA,
    "virtual": pk.GroupEnum.COLLECTIONS,
    "web": pk.GroupEnum.INTERNET,
    "xfce": pk.GroupEnum.DESKTOP_OTHER,
    "x11": pk.GroupEnum.DESKTOP_OTHER,
    "zope": pk.GroupEnum.PROGRAMMING,
    "unknown": pk.GroupEnum.UNKNOWN,
    "alien": pk.GroupEnum.UNKNOWN,
    "translations": pk.GroupEnum.LOCALIZATION,
    "metapackages": pk.GroupEnum.COLLECTIONS,
    "tasks": pk.GroupEnum.COLLECTIONS}


class AptPackageKitWorker(aptworker.AptWorker):

    _plugins = None

    """Process PackageKit Query transactions."""

    def __init__(self, chroot=None, load_plugins=True):
        aptworker.AptWorker.__init__(self, chroot, load_plugins)

        self.roles = bitfield_summarize(pk.RoleEnum.REFRESH_CACHE,
                                        pk.RoleEnum.UPDATE_PACKAGES,
                                        pk.RoleEnum.INSTALL_PACKAGES,
                                        pk.RoleEnum.INSTALL_FILES,
                                        pk.RoleEnum.REMOVE_PACKAGES,
                                        pk.RoleEnum.GET_UPDATES,
                                        pk.RoleEnum.GET_UPDATE_DETAIL,
                                        pk.RoleEnum.GET_PACKAGES,
                                        pk.RoleEnum.GET_DETAILS,
                                        pk.RoleEnum.SEARCH_NAME,
                                        pk.RoleEnum.SEARCH_DETAILS,
                                        pk.RoleEnum.SEARCH_GROUP,
                                        pk.RoleEnum.SEARCH_FILE,
                                        pk.RoleEnum.WHAT_PROVIDES,
                                        pk.RoleEnum.REPO_ENABLE,
                                        pk.RoleEnum.INSTALL_SIGNATURE,
                                        pk.RoleEnum.REPAIR_SYSTEM,
                                        pk.RoleEnum.CANCEL,
                                        pk.RoleEnum.DOWNLOAD_PACKAGES)
        if META_RELEASE_SUPPORT:
            self.roles = bitfield_add(self.roles,
                                      pk.RoleEnum.GET_DISTRO_UPGRADES)
        self.filters = bitfield_summarize(pk.FilterEnum.INSTALLED,
                                          pk.FilterEnum.NOT_INSTALLED,
                                          pk.FilterEnum.FREE,
                                          pk.FilterEnum.NOT_FREE,
                                          pk.FilterEnum.GUI,
                                          pk.FilterEnum.NOT_GUI,
                                          pk.FilterEnum.COLLECTIONS,
                                          pk.FilterEnum.NOT_COLLECTIONS,
                                          pk.FilterEnum.SUPPORTED,
                                          pk.FilterEnum.NOT_SUPPORTED,
                                          pk.FilterEnum.ARCH,
                                          pk.FilterEnum.NOT_ARCH,
                                          pk.FilterEnum.NEWEST)
        self.groups = bitfield_summarize(*SECTION_GROUP_MAP.values())
        # FIXME: Add support for Plugins
        self.provides = (pk.ProvidesEnum.ANY)
        self.mime_types = ["application/x-deb"]

    def _run_transaction(self, trans):
        if (hasattr(trans, "pktrans") and
            bitfield_contains(trans.pktrans.flags,
                              pk.TransactionFlagEnum.SIMULATE)):
            self._simulate_and_emit_packages(trans)
            return False
        else:
            return aptworker.AptWorker._run_transaction(self, trans)

    def _simulate_and_emit_packages(self, trans):
        trans.status = aptd_enums.STATUS_RUNNING

        self._simulate_transaction_idle(trans)

        # The simulate method lets the transaction fail in the case of an
        # error
        if trans.exit == aptd_enums.EXIT_UNFINISHED:
            # It is a little bit complicated to get the packages but avoids
            # a larger refactoring of apt.AptWorker._simulate()
            for pkg in trans.depends[aptd_enums.PKGS_INSTALL]:
                self._emit_package(trans,
                                   self._cache[self._split_package_id(pkg)[0]],
                                   pk.InfoEnum.INSTALLING)
            for pkg in trans.depends[aptd_enums.PKGS_REINSTALL]:
                self._emit_package(trans,
                                   self._cache[self._split_package_id(pkg)[0]],
                                   pk.InfoEnum.REINSTALLING)
            for pkg in trans.depends[aptd_enums.PKGS_REMOVE]:
                self._emit_package(trans,
                                   self._cache[self._split_package_id(pkg)[0]],
                                   pk.InfoEnum.REMOVING)
            for pkg in trans.depends[aptd_enums.PKGS_PURGE]:
                self._emit_package(trans,
                                   self._cache[self._split_package_id(pkg)[0]],
                                   pk.InfoEnum.REMOVING)
            for pkg in trans.depends[aptd_enums.PKGS_UPGRADE]:
                self._emit_package(trans,
                                   self._cache[self._split_package_id(pkg)[0]],
                                   pk.InfoEnum.UPDATING, force_candidate=True)
            for pkg in trans.depends[aptd_enums.PKGS_DOWNGRADE]:
                self._emit_package(trans,
                                   self._cache[self._split_package_id(pkg)[0]],
                                   pk.InfoEnum.DOWNGRADING,
                                   force_candidate=True)
            for pkg in trans.depends[aptd_enums.PKGS_KEEP]:
                self._emit_package(trans,
                                   self._cache[self._split_package_id(pkg)[0]],
                                   pk.InfoEnum.BLOCKED, force_candidate=True)
            for pkg in trans.unauthenticated:
                self._emit_package(trans, self._cache[pkg],
                                   pk.InfoEnum.UNTRUSTED, force_candidate=True)
            trans.status = aptd_enums.STATUS_FINISHED
            trans.progress = 100
            trans.exit = aptd_enums.EXIT_SUCCESS
        tid = trans.tid[:]
        self.trans = None
        self.marked_tid = None
        self._emit_transaction_done(trans)
        pklog.info("Finished transaction %s", tid)

    def query(self, trans):
        """Run the worker"""
        if trans.role != aptd_enums.ROLE_PK_QUERY:
            raise TransactionFailed(aptd_enums.ERROR_UNKNOWN,
                                    "The transaction doesn't seem to be "
                                    "a query")
        if trans.pktrans.role == pk.RoleEnum.RESOLVE:
            self.resolve(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.GET_UPDATES:
            self.get_updates(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.GET_UPDATE_DETAIL:
            self.get_update_detail(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.GET_PACKAGES:
            self.get_packages(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.GET_FILES:
            self.get_files(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.SEARCH_NAME:
            self.search_names(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.SEARCH_GROUP:
            self.search_groups(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.SEARCH_DETAILS:
            self.search_details(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.SEARCH_FILE:
            self.search_files(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.GET_DETAILS:
            self.get_details(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.DOWNLOAD_PACKAGES:
            self.download_packages(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.WHAT_PROVIDES:
            self.what_provides(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.REPO_ENABLE:
            self.repo_enable(trans, **trans.kwargs)
        elif trans.pktrans.role == pk.RoleEnum.INSTALL_SIGNATURE:
            self.install_signature(trans, **trans.kwargs)
        else:
            raise TransactionFailed(aptd_enums.ERROR_UNKNOWN,
                                    "Role %s isn't supported",
                                    trans.pktrans.role)

    def search_files(self, trans, filters, values):
        """Implement org.freedesktop.PackageKit.Transaction.SearchFiles()

        Works only for installed file if apt-file isn't installed.
        """
        trans.progress = 101

        result_names = set()
        # Optionally make use of apt-file's Contents cache to search for not
        # installed files. But still search for installed files additionally
        # to make sure that we provide up-to-date results
        if (os.path.exists("/usr/bin/apt-file") and
                not bitfield_contains(filters, pk.FilterEnum.INSTALLED)):
            # FIXME: use rapt-file on Debian if the network is available
            # FIXME: Show a warning to the user if the apt-file cache is
            #        several weeks old
            pklog.debug("Using apt-file")
            filenames_regex = []
            for filename in values:
                if filename.startswith("/"):
                    pattern = "^%s$" % filename[1:].replace("/", "\/")
                else:
                    pattern = "\/%s$" % filename
                filenames_regex.append(pattern)
            cmd = ["/usr/bin/apt-file", "--regexp", "--non-interactive",
                   "--package-only", "find", "|".join(filenames_regex)]
            pklog.debug("Calling: %s" % cmd)
            apt_file = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            stdout, stderr = apt_file.communicate()
            if apt_file.returncode == 0:
                # FIXME: Actually we should check if the file is part of the
                #       candidate, e.g. if unstable and experimental are
                #       enabled and a file would only be part of the
                #       experimental version
                result_names.update(stdout.split())
                self._emit_visible_packages_by_name(trans, filters,
                                                    result_names)
            else:
                raise TransactionFailed(aptd_enums.ERROR_INTERNAL_ERROR,
                                        "%s %s" % (stdout, stderr))
        # Search for installed files
        filenames_regex = []
        for filename in values:
            if filename.startswith("/"):
                pattern = "^%s$" % filename.replace("/", "\/")
            else:
                pattern = ".*\/%s$" % filename
            filenames_regex.append(pattern)
        files_pattern = re.compile("|".join(filenames_regex))
        for pkg in self._iterate_packages():
            if pkg.name in result_names:
                continue
            for installed_file in self._get_installed_files(pkg):
                if files_pattern.match(installed_file):
                    self._emit_visible_package(trans, filters, pkg)
                    break

    def search_groups(self, trans, filters, values):
        """Implement org.freedesktop.PackageKit.Transaction.SearchGroups()"""
        # FIXME: Handle repo and category search
        trans.progress = 101

        for pkg in self._iterate_packages():
            group_str = pk.group_enum_to_string(self._get_package_group(pkg))
            if group_str in values:
                self._emit_visible_package(trans, filters, pkg)

    def search_names(self, trans, filters, values):
        """Implement org.freedesktop.PackageKit.Transaction.SearchNames()"""
        def matches(searches, text):
            for search in searches:
                if search not in text:
                    return False
            return True
        trans.progress = 101

        for pkg_name in list(self._cache.keys()):
            if matches(values, pkg_name):
                self._emit_all_visible_pkg_versions(trans, filters,
                                                    self._cache[pkg_name])

    def search_details(self, trans, filters, values):
        """Implement org.freedesktop.PackageKit.Transaction.SearchDetails()"""
        trans.progress = 101

        if XAPIAN_SUPPORT is True:
            search_flags = (xapian.QueryParser.FLAG_BOOLEAN |
                            xapian.QueryParser.FLAG_PHRASE |
                            xapian.QueryParser.FLAG_LOVEHATE |
                            xapian.QueryParser.FLAG_BOOLEAN_ANY_CASE)
            pklog.debug("Performing xapian db based search")
            db = xapian.Database(XAPIAN_DB)
            parser = xapian.QueryParser()
            parser.set_default_op(xapian.Query.OP_AND)
            query = parser.parse_query(" ".join(values), search_flags)
            enquire = xapian.Enquire(db)
            enquire.set_query(query)
            matches = enquire.get_mset(0, 1000)
            for pkg_name in (match.document.get_data()
                             for match in enquire.get_mset(0, 1000)):
                if pkg_name in self._cache:
                    self._emit_visible_package(trans, filters,
                                               self._cache[pkg_name])
        else:
            def matches(searches, text):
                for search in searches:
                    if search not in text:
                        return False
                return True
            pklog.debug("Performing apt cache based search")
            values = [val.lower() for val in values]
            for pkg in self._iterate_packages():
                txt = pkg.name
                try:
                    txt += pkg.candidate.raw_description.lower()
                    txt += pkg.candidate._translated_records.long_desc.lower()
                except AttributeError:
                    pass
                if matches(values, txt):
                    self._emit_visible_package(trans, filters, pkg)

    def get_updates(self, trans, filters):
        """Only report updates which can be installed safely: Which can depend
        on the installation of additional packages but which don't require
        the removal of already installed packages or block any other update.
        """
        def succeeds_security_update(pkg):
            """
            Return True if an update succeeds a previous security update

            An example would be a package with version 1.1 in the security
            archive and 1.1.1 in the archive of proposed updates or the
            same version in both archives.
            """
            for version in pkg.versions:
                # Only check versions between the installed and the candidate
                if (pkg.installed and
                    apt_pkg.version_compare(version.version,
                                            pkg.installed.version) <= 0 and
                    apt_pkg.version_compare(version.version,
                                            pkg.candidate.version) > 0):
                    continue
                for origin in version.origins:
                    if (origin.origin in ["Debian", "Ubuntu"] and
                            (origin.archive.endswith("-security") or
                             origin.label == "Debian-Security") and
                            origin.trusted):
                        return True
            return False
        # FIXME: Implment the basename filter
        self.cancellable = False
        self.progress = 101
        # Start with a safe upgrade
        try:
            self._cache.upgrade(dist_upgrade=True)
        except SystemError:
            pass
        for pkg in self._iterate_packages():
            if not pkg.is_upgradable:
                continue
            # This may occur on pinned packages which have been updated to
            # later version than the pinned one
            if not pkg.candidate.origins:
                continue
            if not pkg.marked_upgrade:
                # FIXME: Would be nice to all show why
                self._emit_package(trans, pkg, pk.InfoEnum.BLOCKED,
                                   force_candidate=True)
                continue
            # The update can be safely installed
            info = pk.InfoEnum.NORMAL
            # Detect the nature of the upgrade (e.g. security, enhancement)
            candidate_origin = pkg.candidate.origins[0]
            archive = candidate_origin.archive
            origin = candidate_origin.origin
            trusted = candidate_origin.trusted
            label = candidate_origin.label
            if origin in ["Debian", "Ubuntu"] and trusted is True:
                if archive.endswith("-security") or label == "Debian-Security":
                    info = pk.InfoEnum.SECURITY
                elif succeeds_security_update(pkg):
                    pklog.debug("Update of %s succeeds a security update. "
                                "Raising its priority." % pkg.name)
                    info = pk.InfoEnum.SECURITY
                elif archive.endswith("-backports"):
                    info = pk.InfoEnum.ENHANCEMENT
                elif archive.endswith("-updates"):
                    info = pk.InfoEnum.BUGFIX
            if origin in ["Backports.org archive"] and trusted is True:
                info = pk.InfoEnum.ENHANCEMENT
            self._emit_package(trans, pkg, info, force_candidate=True)
        self._emit_require_restart(trans)

    def _emit_require_restart(self, trans):
        """Emit RequireRestart if required."""
        # Check for a system restart
        if self.is_reboot_required():
            trans.pktrans.RequireRestart(pk.RestartEnum.SYSTEM, "")

    def get_update_detail(self, trans, package_ids):
        """
        Implement the {backend}-get-update-details functionality
        """
        def get_bug_urls(changelog):
            """
            Create a list of urls pointing to closed bugs in the changelog
            """
            urls = []
            for r in re.findall(MATCH_BUG_CLOSES_DEBIAN, changelog,
                                re.IGNORECASE | re.MULTILINE):
                urls.extend([HREF_BUG_DEBIAN % bug for bug in
                             re.findall(MATCH_BUG_NUMBERS, r)])
            for r in re.findall(MATCH_BUG_CLOSES_UBUNTU, changelog,
                                re.IGNORECASE | re.MULTILINE):
                urls.extend([HREF_BUG_UBUNTU % bug for bug in
                             re.findall(MATCH_BUG_NUMBERS, r)])
            return urls

        def get_cve_urls(changelog):
            """
            Create a list of urls pointing to cves referred in the changelog
            """
            return [HREF_CVE % c for c in re.findall(MATCH_CVE, changelog,
                                                     re.MULTILINE)]

        trans.progress = 0
        trans.cancellable = False
        trans.pktrans.status = pk.StatusEnum.DOWNLOAD_CHANGELOG
        total = len(package_ids)
        count = 1
        old_locale = locale.getlocale(locale.LC_TIME)
        locale.setlocale(locale.LC_TIME, "C")
        for pkg_id in package_ids:
            self._iterate_mainloop()
            trans.progress = count * 100 / total
            count += 1
            pkg = self._get_package_by_id(pkg_id)
            # FIXME add some real data
            if pkg.installed.origins:
                installed_origin = pkg.installed.origins[0].label
                # APT returns a str with Python 2
                if isinstance(installed_origin, bytes):
                    installed_origin = installed_origin.decode("UTF-8")
            else:
                installed_origin = ""
            updates = ["%s;%s;%s;%s" % (pkg.name, pkg.installed.version,
                                        pkg.installed.architecture,
                                        installed_origin)]
            # Get the packages which will be replaced by the update
            obsoletes = set()
            if pkg.candidate:
                for dep_group in pkg.candidate.get_dependencies("Replaces"):
                    for dep in dep_group:
                        try:
                            obs = self._cache[dep.name]
                        except KeyError:
                            continue
                        if not obs.installed:
                            continue
                        if dep.relation:
                            cmp = apt_pkg.version_compare(
                                obs.candidate.version,
                                dep.version)
                            # Same version
                            if cmp == 0 and dep.relation in [">", "<"]:
                                continue
                            # Installed version higer
                            elif cmp < 0 and dep.relation in ["<"]:
                                continue
                            # Installed version lower
                            elif cmp > 0 and dep.relation in [">"]:
                                continue
                        obs_id = self._get_id_from_version(obs.installed)
                        obsoletes.add(obs_id)
            vendor_urls = []
            restart = pk.RestartEnum.NONE
            update_text = ""
            state = pk.UpdateStateEnum.UNKNOWN
            # FIXME: Add support for Ubuntu and a better one for Debian
            if (pkg.candidate and pkg.candidate.origins[0].trusted and
                    pkg.candidate.origins[0].label == "Debian"):
                archive = pkg.candidate.origins[0].archive
                if archive == "stable":
                    state = pk.UpdateStateEnum.STABLE
                elif archive == "testing":
                    state = pk.UpdateStateEnum.TESTING
                elif archive == "unstable":
                    state = pk.UpdateStateEnum.UNSTABLE
            issued = ""
            updated = ""
            # FIXME: make this more configurable. E.g. a dbus update requires
            #       a reboot on Ubuntu but not on Debian
            if (pkg.name.startswith("linux-image-") or
                    pkg.name in ["libc6", "dbus"]):
                restart == pk.RestartEnum.SYSTEM
            changelog_dir = apt_pkg.config.find_dir("Dir::Cache::Changelogs")
            if changelog_dir == "/":
                changelog_dir = os.path.join(apt_pkg.config.find_dir("Dir::"
                                                                     "Cache"),
                                             "Changelogs")
            filename = os.path.join(changelog_dir,
                                    "%s_%s.gz" % (pkg.name,
                                                  pkg.candidate.version))
            changelog_raw = ""
            if os.path.exists(filename):
                pklog.debug("Reading changelog from cache")
                changelog_file = gzip.open(filename, "rb")
                try:
                    changelog_raw = changelog_file.read().decode("UTF-8")
                except:
                    pass
                finally:
                    changelog_file.close()
            if not changelog_raw:
                pklog.debug("Downloading changelog")
                changelog_raw = pkg.get_changelog()
                # The internal download error string of python-apt ist not
                # provided as unicode object
                if not isinstance(changelog_raw, str):
                    changelog_raw = changelog_raw.decode("UTF-8")
                # Cache the fetched changelog
                if not os.path.exists(changelog_dir):
                    os.makedirs(changelog_dir)
                # Remove old cached changelogs
                pattern = os.path.join(changelog_dir, "%s_*" % pkg.name)
                for old_changelog in glob.glob(pattern):
                    os.remove(os.path.join(changelog_dir, old_changelog))
                changelog_file = gzip.open(filename, mode="wb")
                try:
                    changelog_file.write(changelog_raw.encode("UTF-8"))
                finally:
                    changelog_file.close()
            # Convert the changelog to markdown syntax
            changelog = ""
            for line in changelog_raw.split("\n"):
                if line == "":
                    changelog += " \n"
                else:
                    changelog += "    %s  \n" % line
                if line.startswith(pkg.candidate.source_name):
                    match = re.match(r"(?P<source>.+) \((?P<version>.*)\) "
                                     "(?P<dist>.+); urgency=(?P<urgency>.+)",
                                     line)
                    update_text += "%s\n%s\n\n" % (match.group("version"),
                                                   "=" *
                                                   len(match.group("version")))
                elif line.startswith("  "):
                    # FIXME: The GNOME PackageKit markup parser doesn't support
                    #        monospaced yet
                    # update_text += "  %s  \n" % line
                    update_text += "%s\n\n" % line
                elif line.startswith(" --"):
                    # FIXME: Add %z for the time zone - requires Python 2.6
                    update_text += "  \n"
                    match = re.match("^ -- (?P<maintainer>.+) (?P<mail><.+>)  "
                                     "(?P<date>.+) (?P<offset>[-\+][0-9]+)$",
                                     line)
                    if not match:
                        continue
                    try:
                        date = datetime.datetime.strptime(match.group("date"),
                                                          "%a, %d %b %Y "
                                                          "%H:%M:%S")
                    except ValueError:
                        continue
                    issued = date.isoformat()
                    if not updated:
                        updated = date.isoformat()
            if issued == updated:
                updated = ""
            bugzilla_urls = get_bug_urls(changelog)
            cve_urls = get_cve_urls(changelog)
            trans.emit_update_detail(pkg_id, updates, obsoletes, vendor_urls,
                                     bugzilla_urls, cve_urls, restart,
                                     update_text, changelog,
                                     state, issued, updated)
        locale.setlocale(locale.LC_TIME, old_locale)

    def get_details(self, trans, package_ids):
        """Implement org.freedesktop.PackageKit.Transaction.GetDetails()"""
        trans.progress = 101

        for pkg_id in package_ids:
            version = self._get_version_by_id(pkg_id)
            # FIXME: We need more fine grained license information!
            origins = version.origins
            if (origins and
                    origins[0].component in ["main", "universe"] and
                    origins[0].origin in ["Debian", "Ubuntu"]):
                license = "free"
            else:
                license = "unknown"
            group = self._get_package_group(version.package)
            trans.emit_details(pkg_id, license, group, version.description,
                               version.homepage, version.size)

    def get_packages(self, trans, filters):
        """Implement org.freedesktop.PackageKit.Transaction.GetPackages()"""
        self.progress = 101

        for pkg in self._iterate_packages():
            if self._is_package_visible(pkg, filters):
                self._emit_package(trans, pkg)

    def resolve(self, trans, filters, packages):
        """Implement org.freedesktop.PackageKit.Transaction.Resolve()"""
        trans.status = aptd_enums.STATUS_QUERY
        trans.progress = 101
        self.cancellable = False

        for name in packages:
            try:
                # Check if the name is a valid package id
                version = self._get_version_by_id(name)
            except ValueError:
                pass
            else:
                if self._is_version_visible(version, filters):
                    self._emit_pkg_version(trans, version)
                continue
            # The name seems to be a normal name
            try:
                pkg = self._cache[name]
            except KeyError:
                raise TransactionFailed(aptd_enums.ERROR_NO_PACKAGE,
                                        "Package name %s could not be "
                                        "resolved.", name)
            else:
                self._emit_all_visible_pkg_versions(trans, filters, pkg)

    def get_depends(self, trans, filters, package_ids, recursive):
        """Emit all dependencies of the given package ids.

        Doesn't support recursive dependency resolution.
        """
        def emit_blocked_dependency(base_dependency, pkg=None,
                                    filters=pk.FilterEnum.NONE):
            """Send a blocked package signal for the given
            apt.package.BaseDependency.
            """
            if pk.FilterEnum.INSTALLED in filters:
                return
            if pkg:
                summary = pkg.candidate.summary
                filters = bitfield_remove(filters, pk.FilterEnum.NOT_INSTALLED)
                if not self._is_package_visible(pkg, filters):
                    return
            else:
                summary = ""
            if base_dependency.relation:
                version = "%s%s" % (base_dependency.relation,
                                    base_dependency.version)
            else:
                version = base_dependency.version
            trans.emit_package("%s;%s;;" % (base_dependency.name, version),
                               pk.InfoEnum.BLOCKED, summary)

        def check_dependency(pkg, base_dep):
            """Check if the given apt.package.Package can satisfy the
            BaseDepenendcy and emit the corresponding package signals.
            """
            if not self._is_package_visible(pkg, filters):
                return
            if base_dep.version:
                satisfied = False
                # Sort the version list to check the installed
                # and candidate before the other ones
                ver_list = list(pkg.versions)
                if pkg.installed:
                    ver_list.remove(pkg.installed)
                    ver_list.insert(0, pkg.installed)
                if pkg.candidate:
                    ver_list.remove(pkg.candidate)
                    ver_list.insert(0, pkg.candidate)
                for dep_ver in ver_list:
                    if apt_pkg.check_dep(dep_ver.version,
                                         base_dep.relation,
                                         base_dep.version):
                        self._emit_pkg_version(trans, dep_ver)
                        satisfied = True
                        break
                if not satisfied:
                    emit_blocked_dependency(base_dep, pkg, filters)
            else:
                self._emit_package(trans, pkg)

        # Setup the transaction
        self.status = aptd_enums.STATUS_RESOLVING_DEP
        trans.progress = 101
        self.cancellable = True

        dependency_types = ["PreDepends", "Depends"]
        if apt_pkg.config["APT::Install-Recommends"]:
            dependency_types.append("Recommends")
        for id in package_ids:
            version = self._get_version_by_id(id)
            for dependency in version.get_dependencies(*dependency_types):
                # Walk through all or_dependencies
                for base_dep in dependency.or_dependencies:
                    if self._cache.is_virtual_package(base_dep.name):
                        # Check each proivider of a virtual package
                        for provider in self._cache.get_providing_packages(
                                base_dep.name):
                            check_dependency(provider, base_dep)
                    elif base_dep.name in self._cache:
                        check_dependency(self._cache[base_dep.name], base_dep)
                    else:
                        # The dependency does not exist
                        emit_blocked_dependency(trans, base_dep,
                                                filters=filters)

    def get_requires(self, trans, filters, package_ids, recursive):
        """Emit all packages which depend on the given ids.

        Recursive searching is not supported.
        """
        self.status = aptd_enums.STATUS_RESOLVING_DEP
        self.progress = 101
        self.cancellable = True
        for id in package_ids:
            version = self._get_version_by_id(id)
            for pkg in self._iterate_packages():
                if not self._is_package_visible(pkg, filters):
                    continue
                if pkg.is_installed:
                    pkg_ver = pkg.installed
                elif pkg.candidate:
                    pkg_ver = pkg.candidate
                for dependency in pkg_ver.dependencies:
                    satisfied = False
                    for base_dep in dependency.or_dependencies:
                        if (version.package.name == base_dep.name or
                                base_dep.name in version.provides):
                            satisfied = True
                            break
                    if satisfied:
                        self._emit_package(trans, pkg)
                        break

    def download_packages(self, trans, store_in_cache, package_ids):
        """Implement the DownloadPackages functionality.

        The store_in_cache parameter gets ignored.
        """
        def get_download_details(ids):
            """Calculate the start and end point of a package download
            progress.
            """
            total = 0
            downloaded = 0
            versions = []
            # Check if all ids are vaild and calculate the total download size
            for id in ids:
                pkg_ver = self._get_version_by_id(id)
                if not pkg_ver.downloadable:
                    raise TransactionFailed(
                        aptd_enums.ERROR_PACKAGE_DOWNLOAD_FAILED,
                        "package %s isn't downloadable" % id)
                total += pkg_ver.size
                versions.append((id, pkg_ver))
            for id, ver in versions:
                start = downloaded * 100 / total
                end = start + ver.size * 100 / total
                yield id, ver, start, end
                downloaded += ver.size
        trans.status = aptd_enums.STATUS_DOWNLOADING
        trans.cancellable = True
        trans.progress = 10
        # Check the destination directory
        if store_in_cache:
            dest = apt_pkg.config.find_dir("Dir::Cache::archives")
        else:
            dest = tempfile.mkdtemp(prefix="aptdaemon-download")
        if not os.path.isdir(dest) or not os.access(dest, os.W_OK):
            raise TransactionFailed(aptd_enums.ERROR_INTERNAL_ERROR,
                                    "The directory '%s' is not writable" %
                                    dest)
        # Start the download
        for id, ver, start, end in get_download_details(package_ids):
            progress = DaemonAcquireProgress(trans, start, end)
            self._emit_pkg_version(trans, ver, pk.InfoEnum.DOWNLOADING)
            try:
                ver.fetch_binary(dest, progress)
            except Exception as error:
                raise TransactionFailed(
                    aptd_enums.ERROR_PACKAGE_DOWNLOAD_FAILED, str(error))
            else:
                path = os.path.join(dest, os.path.basename(ver.filename))
                trans.emit_files(id, [path])
                self._emit_pkg_version(trans, ver, pk.InfoEnum.FINISHED)

    def get_files(self, trans, package_ids):
        """Emit the Files signal which includes the files included in a package
        Apt only supports this for installed packages
        """
        for id in package_ids:
            pkg = self._get_package_by_id(id)
            trans.emit_files(id, self._get_installed_files(pkg))

    def what_provides(self, trans, filters, provides_type, values):
        """Emit all packages which provide the given type and search value."""
        self._init_plugins()

        supported_type = False
        provides_type_str = pk.provides_enum_to_string(provides_type)

        # run plugins
        for plugin in self._plugins.get("what_provides", []):
            pklog.debug("calling what_provides plugin %s %s",
                        str(plugin), str(filters))
            for search_item in values:
                try:
                    for package in plugin(self._cache, provides_type_str,
                                          search_item):
                        self._emit_visible_package(trans, filters, package)
                    supported_type = True
                except NotImplementedError:
                    # keep supported_type as False
                    pass

        if not supported_type and provides_type != pk.ProvidesEnum.ANY:
            # none of the plugins felt responsible for this type
            raise TransactionFailed(aptd_enums.ERROR_NOT_SUPPORTED,
                                    "Query type '%s' is not supported" %
                                    pk.provides_enum_to_string(provides_type))

    def repo_enable(self, trans, repo_id, enabled):
        """Enable or disable a repository."""
        if not enabled:
            raise TransactionFailed(aptd_enums.ERROR_NOT_SUPPORTED,
                                    "Disabling repositories is not "
                                    "implemented")

        fields = repo_id.split()
        if len(fields) < 3 or fields[0] not in ('deb', 'deb-src'):
            raise TransactionFailed(
                aptd_enums.ERROR_NOT_SUPPORTED,
                "Unknown repository ID format: %s" % repo_id)

        self.add_repository(trans, fields[0], fields[1], fields[2],
                            fields[3:], '', None)

    def install_signature(self, trans, sig_type, key_id, package_id):
        """Install an archive key."""
        if sig_type != pk.SigTypeEnum.GPG:
            raise TransactionFailed(aptd_enums.ERROR_NOT_SUPPORTED,
                                    "Type %s is not supported" % sig_type)
        try:
            keyserver = os.environ["APTDAEMON_KEYSERVER"]
        except KeyError:
            if platform.dist()[0] == "Ubuntu":
                keyserver = "hkp://keyserver.ubuntu.com:80"
            else:
                keyserver = "hkp://keys.gnupg.net"
        self.add_vendor_key_from_keyserver(trans, key_id, keyserver)

    # Helpers

    def _get_id_from_version(self, version):
        """Return the package id of an apt.package.Version instance."""
        if version.origins:
            origin = version.origins[0].label
            # APT returns a str with Python 2
            if isinstance(origin, bytes):
                origin = origin.decode("UTF-8")
        else:
            origin = ""
        if version.architecture in [self.NATIVE_ARCH, "all"]:
            name = version.package.name
        else:
            name = version.package.name.split(":")[0]
        id = "%s;%s;%s;%s" % (name, version.version,
                              version.architecture, origin)
        return id

    def _emit_package(self, trans, pkg, info=None, force_candidate=False):
        """
        Send the Package signal for a given apt package
        """
        if (not pkg.is_installed or force_candidate) and pkg.candidate:
            self._emit_pkg_version(trans, pkg.candidate, info)
        elif pkg.is_installed:
            self._emit_pkg_version(trans, pkg.installed, info)
        else:
            pklog.debug("Package %s hasn't got any version." % pkg.name)

    def _emit_pkg_version(self, trans, version, info=None):
        """Emit the Package signal of the given apt.package.Version."""
        id = self._get_id_from_version(version)
        section = version.section.split("/")[-1]
        if not info:
            if version == version.package.installed:
                if section == "metapackages":
                    info = pk.InfoEnum.COLLECTION_INSTALLED
                else:
                    info = pk.InfoEnum.INSTALLED
            else:
                if section == "metapackages":
                    info = pk.InfoEnum.COLLECTION_AVAILABLE
                else:
                    info = pk.InfoEnum.AVAILABLE
        trans.emit_package(info, id, version.summary)

    def _emit_all_visible_pkg_versions(self, trans, filters, pkg):
        """Emit all available versions of a package."""
        for version in pkg.versions:
            if self._is_version_visible(version, filters):
                self._emit_pkg_version(trans, version)

    def _emit_visible_package(self, trans, filters, pkg, info=None):
        """
        Filter and emit a package
        """
        if self._is_package_visible(pkg, filters):
            self._emit_package(trans, pkg, info)

    def _emit_visible_packages(self, trans, filters, pkgs, info=None):
        """
        Filter and emit packages
        """
        for pkg in pkgs:
            if self._is_package_visible(pkg, filters):
                self._emit_package(trans, pkg, info)

    def _emit_visible_packages_by_name(self, trans, filters, pkgs, info=None):
        """
        Find the packages with the given namens. Afterwards filter and emit
        them
        """
        for name in pkgs:
            if (name in self._cache and
                    self._is_package_visible(self._cache[name], filters)):
                self._emit_package(trans, self._cache[name], info)

    def _is_version_visible(self, version, filters):
        """Return True if the package version is matched by the given
        filters.
        """
        if filters == pk.FilterEnum.NONE:
            return True
        if (bitfield_contains(filters, pk.FilterEnum.NEWEST) and
                version.package.candidate != version):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.INSTALLED) and
                version.package.installed != version):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_INSTALLED) and
                version.package.installed == version):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.SUPPORTED) and
                not self._is_package_supported(version.package)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_SUPPORTED) and
                self._is_package_supported(version.package)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.FREE) and
                not self._is_version_free(version)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_FREE) and
                self._is_version_free(version)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.GUI) and
                not self._has_package_gui(version.package)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_GUI) and
                self._has_package_gui(version.package)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.COLLECTIONS) and
                not self._is_package_collection(version.package)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_COLLECTIONS) and
                self._is_package_collection(version.package)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.DEVELOPMENT) and
                not self._is_package_devel(version.package)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_DEVELOPMENT) and
                self._is_package_devel(version.package)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.ARCH) and
                version.architecture not in [self.NATIVE_ARCH, "all"]):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_ARCH) and
                version.architecture in [self.NATIVE_ARCH, "all"]):
            return False
        return True

    def _is_package_visible(self, pkg, filters):
        """Return True if the package is matched by the given filters."""
        if filters == pk.FilterEnum.NONE:
            return True
        if (bitfield_contains(filters, pk.FilterEnum.INSTALLED) and
                not pkg.is_installed):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_INSTALLED) and
                pkg.is_installed):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.SUPPORTED) and
                not self._is_package_supported(pkg)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_SUPPORTED) and
                self._is_package_supported(pkg)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.FREE) and
                not self._is_package_free(pkg)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_FREE) and
                self._is_package_free(pkg)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.GUI) and
                not self._has_package_gui(pkg)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_GUI) and
                self._has_package_gui(pkg)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.COLLECTIONS) and
                not self._is_package_collection(pkg)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_COLLECTIONS) and
                self._is_package_collection(pkg)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.DEVELOPMENT) and
                not self._is_package_devel(pkg)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_DEVELOPMENT) and
                self._is_package_devel(pkg)):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.ARCH) and
                ":" in pkg.name):
            return False
        if (bitfield_contains(filters, pk.FilterEnum.NOT_ARCH) and
                ":" not in pkg.name):
            return False
        return True

    def _is_package_free(self, pkg):
        """Return True if we can be sure that the package's license is a
        free one
        """
        if not pkg.candidate:
            return False
        return self._is_version_free(pkg.candidate)

    def _is_version_free(self, version):
        """Return True if we can be sure that the package version has got
        a free license.
        """
        origins = version.origins
        return (origins and
                ((origins[0].origin == "Ubuntu" and
                  origins[0].component in ["main", "universe"]) or
                 (origins[0].origin == "Debian" and
                  origins[0].component == "main")) and
                origins[0].trusted)

    def _is_package_collection(self, pkg):
        """Return True if the package is a metapackge
        """
        section = pkg.section.split("/")[-1]
        return section == "metapackages"

    def _has_package_gui(self, pkg):
        # FIXME: take application data into account. perhaps checking for
        #        property in the xapian database
        return pkg.section.split('/')[-1].lower() in ['x11', 'gnome', 'kde']

    def _is_package_devel(self, pkg):
        return (pkg.name.endswith("-dev") or pkg.name.endswith("-dbg") or
                pkg.section.split('/')[-1].lower() in ['devel', 'libdevel'])

    def _is_package_supported(self, pkg):
        if not pkg.candidate:
            return False
        origins = pkg.candidate.origins
        return (origins and
                ((origins[0].origin == "Ubuntu" and
                  origins[0].component in ["main", "restricted"]) or
                 (origins[0].origin == "Debian" and
                  origins[0].component == "main")) and
                origins[0].trusted)

    def _get_package_by_id(self, id):
        """Return the apt.package.Package corresponding to the given
        package id.

        If the package isn't available error out.
        """
        version = self._get_version_by_id(id)
        return version.package

    def _get_version_by_id(self, id):
        """Return the apt.package.Version corresponding to the given
        package id.

        If the version isn't available error out.
        """
        name, version_string, arch, data = id.split(";", 4)
        if arch and arch not in [self.NATIVE_ARCH, "all"]:
            name += ":%s" % arch
        try:
            pkg = self._cache[name]
        except KeyError:
            raise TransactionFailed(aptd_enums.ERROR_NO_PACKAGE,
                                    "There isn't any package named %s",
                                    name)
        try:
            version = pkg.versions[version_string]
        except:
            raise TransactionFailed(aptd_enums.ERROR_NO_PACKAGE,
                                    "Verion %s doesn't exist",
                                    version_string)
        if version.architecture != arch:
            raise TransactionFailed(aptd_enums.ERROR_NO_PACKAGE,
                                    "Version %s of %s isn't available "
                                    "for architecture %s",
                                    pkg.name, version.version, arch)
        return version

    def _get_installed_files(self, pkg):
        """
        Return the list of unicode names of the files which have
        been installed by the package

        This method should be obsolete by the
        apt.package.Package.installedFiles attribute as soon as the
        consolidate branch of python-apt gets merged
        """
        path = os.path.join(apt_pkg.config["Dir"],
                            "var/lib/dpkg/info/%s.list" % pkg.name)
        try:
            with open(path, 'rb') as f:
                files = f.read().decode('UTF-8').split("\n")
        except IOError:
            return []
        return files

    def _get_package_group(self, pkg):
        """
        Return the packagekit group corresponding to the package's section
        """
        section = pkg.section.split("/")[-1]
        if section in SECTION_GROUP_MAP:
            return SECTION_GROUP_MAP[section]
        else:
            pklog.warning("Unkown package section %s of %s" % (pkg.section,
                                                               pkg.name))
            return pk.GroupEnum.UNKNOWN

    def _init_plugins(self):
        """Initialize PackageKit apt backend plugins.
        Do nothing if plugins are already initialized.
        """
        if self._plugins is not None:
            return

        if not pkg_resources:
            return

        self._plugins = {}  # plugin_name -> [plugin_fn1, ...]

        # just look in standard Python paths for now
        dists, errors = pkg_resources.working_set.find_plugins(
            pkg_resources.Environment())
        for dist in dists:
            pkg_resources.working_set.add(dist)
        for plugin_name in ["what_provides"]:
            for entry_point in pkg_resources.iter_entry_points(
                    "packagekit.apt.plugins", plugin_name):
                try:
                    plugin = entry_point.load()
                except Exception as e:
                    pklog.warning("Failed to load %s from plugin %s: %s" % (
                        plugin_name, str(entry_point.dist), str(e)))
                    continue
                pklog.debug("Loaded %s from plugin %s" % (
                    plugin_name, str(entry_point.dist)))
                self._plugins.setdefault(plugin_name, []).append(plugin)

    def _apply_changes(self, trans, fetch_range=(15, 50),
                       install_range=(50, 90)):
        """Apply changes and emit RequireRestart accordingly."""
        if hasattr(trans, "pktrans"):
            # Cache the ids of the to be changed packages, since we will
            # only get the package name during download/install time
            for pkg in self._cache.get_changes():
                if pkg.marked_delete or pkg.marked_reinstall:
                    pkg_id = self._get_id_from_version(pkg.installed)
                else:
                    pkg_id = self._get_id_from_version(pkg.candidate)
                trans.pktrans.pkg_id_cache[pkg.name] = pkg_id

        aptworker.AptWorker._apply_changes(self, trans, fetch_range,
                                           install_range)

        if (hasattr(trans, "pktrans") and
            (trans.role == aptd_enums.ROLE_UPGRADE_SYSTEM or
             trans.packages[aptd_enums.PKGS_UPGRADE] or
             trans.depends[aptd_enums.PKGS_UPGRADE])):
            self._emit_require_restart(trans)


if META_RELEASE_SUPPORT:

    class GMetaRelease(GObject.GObject, MetaReleaseCore):

        __gsignals__ = {"download-done": (GObject.SignalFlags.RUN_FIRST,
                                          None,
                                          ())}

        def __init__(self):
            GObject.GObject.__init__(self)
            MetaReleaseCore.__init__(self, False, False)

        def download(self):
            MetaReleaseCore.download(self)
            self.emit("download-done")


def bitfield_summarize(*enums):
    """Return the bitfield with the given PackageKit enums."""
    field = 0
    for enum in enums:
        field |= 2 ** int(enum)
    return field


def bitfield_add(field, enum):
    """Add a PackageKit enum to a given field"""
    field |= 2 ** int(enum)
    return field


def bitfield_remove(field, enum):
    """Remove a PackageKit enum to a given field"""
    field = field ^ 2 ** int(enum)
    return field


def bitfield_contains(field, enum):
    """Return True if a bitfield contains the given PackageKit enum"""
    return field & 2 ** int(enum)


# vim: ts=4 et sts=4
