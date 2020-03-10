# MyCache.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2004-2008 Canonical
#
#  Author: Michael Vogt <mvo@debian.org>
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

import warnings
warnings.filterwarnings("ignore", "apt API not stable yet", FutureWarning)
import apt
import apt_pkg
import logging
import os
try:
    from urllib.error import HTTPError
    from urllib.request import urlopen
    from urllib.parse import urlsplit
except ImportError:
    from urllib2 import HTTPError, urlopen
    from urlparse import urlsplit
try:
    from http.client import BadStatusLine
except ImportError:
    from httplib import BadStatusLine
import socket
import subprocess
import re
import DistUpgrade.DistUpgradeCache
from gettext import gettext as _
try:
    from launchpadlib.launchpad import Launchpad
except ImportError:
    Launchpad = None

SYNAPTIC_PINFILE = "/var/lib/synaptic/preferences"
CHANGELOGS_POOL = "https://changelogs.ubuntu.com/changelogs/pool/"
CHANGELOGS_URI = CHANGELOGS_POOL + "%s/%s/%s/%s_%s/%s"


class HttpsChangelogsUnsupportedError(Exception):
    """ https changelogs with credentials are unsupported because of the
        lack of certitifcation validation in urllib2 which allows MITM
        attacks to steal the credentials
    """
    pass


class MyCache(DistUpgrade.DistUpgradeCache.MyCache):

    CHANGELOG_ORIGIN = "Ubuntu"

    def __init__(self, progress, rootdir=None):
        apt.Cache.__init__(self, progress, rootdir)
        # save for later
        self.rootdir = rootdir
        # raise if we have packages in reqreinst state
        # and let the caller deal with that (runs partial upgrade)
        assert len(self.req_reinstall_pkgs) == 0
        # check if the dpkg journal is ok (we need to do that here
        # too because libapt will only do it when it tries to lock
        # the packaging system)
        assert(not self._dpkgJournalDirty())
        # init the regular cache
        self._initDepCache()
        self.all_changes = {}
        self.all_news = {}
        # on broken packages, try to fix via saveDistUpgrade()
        if self._depcache.broken_count > 0:
            self.saveDistUpgrade()
        assert (self._depcache.broken_count == 0 and
                self._depcache.del_count == 0)
        self.launchpad = None
        # generate versioned_kernel_pkgs_regexp for later use
        apt_versioned_kernel_pkgs = apt_pkg.config.value_list(
            "APT::VersionedKernelPackages")
        if apt_versioned_kernel_pkgs:
            self.versioned_kernel_pkgs_regexp = re.compile("(" + "|".join(
                ["^" + p for p in apt_versioned_kernel_pkgs]) + ")")
            running_kernel_version = subprocess.check_output(
                ["uname", "-r"], universal_newlines=True).rstrip()
            self.running_kernel_pkgs_regexp = re.compile("(" + "|".join(
                [("^" + p + ".*" + running_kernel_version)
                 if not p.startswith(".*") else (running_kernel_version + p)
                 for p in apt_versioned_kernel_pkgs]) + ")")
        else:
            self.versioned_kernel_pkgs_regexp = None
            self.running_kernel_pkgs_regexp = None

    def _dpkgJournalDirty(self):
        """
        test if the dpkg journal is dirty
        (similar to debSystem::CheckUpdates)
        """
        d = os.path.dirname(
            apt_pkg.config.find_file("Dir::State::status")) + "/updates"
        for f in os.listdir(d):
            if re.match("[0-9]+", f):
                return True
        return False

    def _initDepCache(self):
        #apt_pkg.config.set("Debug::pkgPolicy","1")
        #self.depcache = apt_pkg.GetDepCache(self.cache)
        #self._depcache = apt_pkg.GetDepCache(self._cache)
        self._depcache.read_pinfile()
        if os.path.exists(SYNAPTIC_PINFILE):
            self._depcache.read_pinfile(SYNAPTIC_PINFILE)
        self._depcache.init()

    def clear(self):
        self._initDepCache()

    @property
    def required_download(self):
        """ get the size of the packages that are required to download """
        pm = apt_pkg.PackageManager(self._depcache)
        fetcher = apt_pkg.Acquire()
        pm.get_archives(fetcher, self._list, self._records)
        return fetcher.fetch_needed

    @property
    def install_count(self):
        return self._depcache.inst_count

    def keep_count(self):
        return self._depcache.keep_count

    def _check_dependencies(self, target, deps):
        """Return True if any of the dependencies in deps match target."""
        # TODO: handle virtual packages
        for dep_or in deps:
            if not dep_or:
                continue
            match = True
            for base_dep in dep_or:
                if (base_dep.name != target.package.shortname or
                    not apt_pkg.check_dep(
                        target.version, base_dep.relation, base_dep.version)):
                    match = False
            if match:
                return True
        return False

    def find_removal_justification(self, pkg):
        target = pkg.installed
        if not target:
            return False
        for cpkg in self:
            candidate = cpkg.candidate
            if candidate is not None:
                if (self._check_dependencies(
                        target, candidate.get_dependencies("Conflicts")) and
                    self._check_dependencies(
                        target, candidate.get_dependencies("Replaces"))):
                    logging.info(
                        "%s Conflicts/Replaces %s; allowing removal" % (
                            candidate.package.shortname, pkg.shortname))
                    return True
        return False

    def saveDistUpgrade(self):
        """ this functions mimics a upgrade but will never remove anything """
        #self._apply_dselect_upgrade()
        self._depcache.upgrade(True)
        wouldDelete = self._depcache.del_count
        if wouldDelete > 0:
            deleted_pkgs = [pkg for pkg in self if pkg.marked_delete]
            assert wouldDelete == len(deleted_pkgs)
            for pkg in deleted_pkgs:
                if self.find_removal_justification(pkg):
                    wouldDelete -= 1
        if wouldDelete > 0:
            self.clear()
            assert (self._depcache.broken_count == 0 and
                    self._depcache.del_count == 0)
        else:
            assert self._depcache.broken_count == 0
        #self._apply_dselect_upgrade()
        self._depcache.upgrade()
        return wouldDelete

    def _strip_epoch(self, verstr):
        " strip of the epoch "
        vers_no_epoch = verstr.split(":")
        if len(vers_no_epoch) > 1:
            verstr = "".join(vers_no_epoch[1:])
        return verstr

    def _get_changelog_or_news(self, name, fname, strict_versioning=False,
                               changelogs_uri=None):
        " helper that fetches the file in question "
        # don't touch the gui in this function, it needs to be thread-safe
        pkg = self[name]

        # get the src package name
        srcpkg = pkg.candidate.source_name

        # assume "main" section
        src_section = "main"
        # use the section of the candidate as a starting point
        section = pkg._pcache._depcache.get_candidate_ver(pkg._pkg).section

        # get the source version, start with the binaries version
        srcver_epoch = pkg.candidate.version
        srcver = self._strip_epoch(srcver_epoch)
        #print("bin: %s" % binver)

        split_section = section.split("/")
        if len(split_section) > 1:
            src_section = split_section[0]

        # lib is handled special
        prefix = srcpkg[0]
        if srcpkg.startswith("lib"):
            prefix = "lib" + srcpkg[3]

        # the changelogs_uri argument overrides the default changelogs_uri,
        # this is useful for e.g. PPAs where we construct the changelogs
        # path differently
        if changelogs_uri:
            uri = changelogs_uri
        else:
            uri = CHANGELOGS_URI % (src_section, prefix, srcpkg, srcpkg,
                                    srcver, fname)

        # https uris are not supported when they contain a username/password
        # because the urllib2 https implementation will not check certificates
        # and so its possible to do a man-in-the-middle attack to steal the
        # credentials
        res = urlsplit(uri)
        if res.scheme == "https" and res.username:
            raise HttpsChangelogsUnsupportedError(
                "https locations with username/password are not"
                "supported to fetch changelogs")

        # print("Trying: %s " % uri)
        changelog = urlopen(uri)
        #print(changelog.read())
        # do only get the lines that are new
        alllines = ""
        regexp = "^%s \((.*)\)(.*)$" % (re.escape(srcpkg))

        while True:
            line = changelog.readline().decode("UTF-8", "replace")
            if line == "":
                break
            match = re.match(regexp, line)
            if match:
                # strip epoch from installed version
                # and from changelog too
                installed = getattr(pkg.installed, "version", None)
                if installed and ":" in installed:
                    installed = installed.split(":", 1)[1]
                changelogver = match.group(1)
                if changelogver and ":" in changelogver:
                    changelogver = changelogver.split(":", 1)[1]
                # we test for "==" here for changelogs
                # to ensure that the version
                # is actually really in the changelog - if not
                # just display it all, this catches cases like:
                # gcc-defaults with "binver=4.3.1" and srcver=1.76
                #
                # for NEWS.Debian we do require the changelogver > installed
                if strict_versioning:
                    if (installed and
                            apt_pkg.version_compare(changelogver,
                                                    installed) < 0):
                        break
                else:
                    if (installed and
                            apt_pkg.version_compare(changelogver,
                                                    installed) == 0):
                        break
            alllines = alllines + line
        return alllines

    def _extract_ppa_changelog_uri(self, name):
        """Return the changelog URI from the Launchpad API

        Return None in case of an error.
        """
        if not Launchpad:
            logging.warning("Launchpadlib not available, cannot retrieve PPA "
                            "changelog")
            return None

        cdt = self[name].candidate
        for uri in cdt.uris:
            if urlsplit(uri).hostname != 'ppa.launchpad.net':
                continue
            match = re.search('http.*/(.*)/(.*)/ubuntu/.*', uri)
            if match is not None:
                user, ppa = match.group(1), match.group(2)
                break
        else:
            logging.error("Unable to find a valid PPA candidate URL.")
            return

        # Login on launchpad if we are not already
        if self.launchpad is None:
            self.launchpad = Launchpad.login_anonymously('update-manager',
                                                         'production',
                                                         version='devel')

        archive = self.launchpad.archives.getByReference(
            reference='~%s/ubuntu/%s' % (user, ppa)
        )
        if archive is None:
            logging.error("Unable to retrieve the archive from the Launchpad "
                          "API.")
            return

        spphs = archive.getPublishedSources(source_name=cdt.source_name,
                                            exact_match=True,
                                            version=cdt.version)
        if not spphs:
            logging.error("No published sources were retrieved from the "
                          "Launchpad API.")
            return

        return spphs[0].changelogUrl()

    def _guess_third_party_changelogs_uri_by_source(self, name):
        pkg = self[name]
        deb_uri = pkg.candidate.uri
        if deb_uri is None:
            return None
        srcrec = pkg.candidate.record.get("Source")
        if not srcrec:
            return None
        # srcpkg can be "apt" or "gcc-default (1.0)"
        srcpkg = srcrec.split("(")[0].strip()
        if "(" in srcrec:
            srcver = srcrec.split("(")[1].rstrip(")")
        else:
            srcver = pkg.candidate.version
        base_uri = deb_uri.rpartition("/")[0]
        return base_uri + "/%s_%s.changelog" % (srcpkg, srcver)

    def _guess_third_party_changelogs_uri_by_binary(self, name):
        """ guess changelogs uri based on ArchiveURI by replacing .deb
            with .changelog
        """
        # there is always a pkg and a pkg.candidate, no need to add
        # check here
        pkg = self[name]
        deb_uri = pkg.candidate.uri
        if deb_uri:
            return "%s.changelog" % deb_uri.rsplit(".", 1)[0]
        return None

    def get_news_and_changelog(self, name, lock):
        self.get_news(name)
        self.get_changelog(name)
        try:
            lock.release()
        except Exception as e:
            pass

    def get_news(self, name):
        " get the NEWS.Debian file from the changelogs location "
        try:
            news = self._get_changelog_or_news(name, "NEWS.Debian", True)
        except Exception:
            return
        if news:
            self.all_news[name] = news

    def _fetch_changelog_for_third_party_package(self, name, origins):
        # Special case for PPAs
        changelogs_uri_ppa = None
        for origin in origins:
            if origin.origin.startswith('LP-PPA-'):
                try:
                    changelogs_uri_ppa = self._extract_ppa_changelog_uri(name)
                    break
                except Exception:
                    logging.exception("Unable to connect to the Launchpad "
                                      "API.")
        # Try non official changelog location
        changelogs_uri_binary = \
            self._guess_third_party_changelogs_uri_by_binary(name)
        changelogs_uri_source = \
            self._guess_third_party_changelogs_uri_by_source(name)
        error_message = ""
        for changelogs_uri in [changelogs_uri_ppa,
                               changelogs_uri_binary,
                               changelogs_uri_source]:
            if changelogs_uri:
                try:
                    changelog = self._get_changelog_or_news(
                        name, "changelog", False, changelogs_uri)
                    self.all_changes[name] += changelog
                except (HTTPError, HttpsChangelogsUnsupportedError):
                    # no changelogs_uri or 404
                    error_message = _(
                        "This update does not come from a "
                        "source that supports changelogs.")
                except (IOError, BadStatusLine, socket.error):
                    # network errors and others
                    logging.exception("error on changelog fetching")
                    error_message = _(
                        "Failed to download the list of changes. \n"
                        "Please check your Internet connection.")
        self.all_changes[name] += error_message

    def get_changelog(self, name):
        " get the changelog file from the changelog location "
        origins = self[name].candidate.origins
        self.all_changes[name] = _("Changes for %s versions:\n"
                                   "Installed version: %s\n"
                                   "Available version: %s\n\n") % \
            (name, getattr(self[name].installed, "version", None),
             self[name].candidate.version)
        if self.CHANGELOG_ORIGIN not in [o.origin for o in origins]:
            self._fetch_changelog_for_third_party_package(name, origins)
            return
        # fixup epoch handling version
        srcpkg = self[name].candidate.source_name
        srcver_epoch = self[name].candidate.version.replace(':', '%3A')
        try:
            changelog = self._get_changelog_or_news(name, "changelog")
            if len(changelog) == 0:
                changelog = _("The changelog does not contain any relevant "
                              "changes.\n\n"
                              "Please use http://launchpad.net/ubuntu/+source/"
                              "%s/%s/+changelog\n"
                              "until the changes become available or try "
                              "again later.") % (srcpkg, srcver_epoch)
        except HTTPError as e:
            changelog = _("The list of changes is not available yet.\n\n"
                          "Please use http://launchpad.net/ubuntu/+source/"
                          "%s/%s/+changelog\n"
                          "until the changes become available or try again "
                          "later.") % (srcpkg, srcver_epoch)
        except (IOError, BadStatusLine, socket.error) as e:
            print("caught exception: ", e)
            changelog = _("Failed to download the list "
                          "of changes. \nPlease "
                          "check your Internet "
                          "connection.")
        self.all_changes[name] += changelog
