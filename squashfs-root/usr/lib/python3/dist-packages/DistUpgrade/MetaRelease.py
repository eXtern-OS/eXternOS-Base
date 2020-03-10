# MetaRelease.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2004,2005 Canonical
#
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
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

import apt
import apt_pkg
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
try:
    from http.client import BadStatusLine
except ImportError:
    from httplib import BadStatusLine
import logging
import email.utils
import os
import socket
import sys
import time
import threading
try:
    from urllib.parse import quote
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import HTTPError, Request, URLError, urlopen, quote

from .utils import (get_lang, get_dist, get_dist_version, get_ubuntu_flavor,
                    get_ubuntu_flavor_name)


class MetaReleaseParseError(Exception):
    pass


class Dist(object):
    def __init__(self, name, version, date, supported):
        self.name = name
        self.version = version
        self.date = date
        self.supported = supported
        self.releaseNotesURI = None
        self.releaseNotesHtmlUri = None
        self.upgradeTool = None
        self.upgradeToolSig = None
        # the server may report that the upgrade is broken currently
        self.upgrade_broken = None


class MetaReleaseCore(object):
    """
    A MetaReleaseCore object abstracts the list of released
    distributions.
    """

    DEBUG = "DEBUG_UPDATE_MANAGER" in os.environ

    # some constants
    CONF = "/etc/update-manager/release-upgrades"
    CONF_METARELEASE = "/etc/update-manager/meta-release"

    def __init__(self,
                 useDevelopmentRelease=False,
                 useProposed=False,
                 forceLTS=False,
                 forceDownload=False,
                 cache=None):
        self._debug("MetaRelease.__init__() useDevel=%s useProposed=%s" %
                    (useDevelopmentRelease, useProposed))
        # force download instead of sending if-modified-since
        self.forceDownload = forceDownload
        self.useDevelopmentRelease = useDevelopmentRelease
        # information about the available dists
        self.downloaded = threading.Event()
        self.upgradable_to = None
        self.new_dist = None
        if cache is None:
            cache = apt.Cache()
        self.flavor = get_ubuntu_flavor(cache=cache)
        self.flavor_name = get_ubuntu_flavor_name(cache=cache)
        self.current_dist_name = get_dist()
        self.current_dist_version = get_dist_version()
        self.no_longer_supported = None
        self.prompt = None

        # default (if the conf file is missing)
        base_uri = "https://changelogs.ubuntu.com/"
        self.METARELEASE_URI = base_uri + "meta-release"
        self.METARELEASE_URI_LTS = base_uri + "meta-release-lts"
        self.METARELEASE_URI_UNSTABLE_POSTFIX = "-development"
        self.METARELEASE_URI_PROPOSED_POSTFIX = "-development"

        # check the meta-release config first
        parser = configparser.ConfigParser()
        if os.path.exists(self.CONF_METARELEASE):
            try:
                parser.read(self.CONF_METARELEASE)
            except configparser.Error as e:
                sys.stderr.write("ERROR: failed to read '%s':\n%s" % (
                                 self.CONF_METARELEASE, e))
                return
            # make changing the metarelease file and the location
            # for the files easy
            if parser.has_section("METARELEASE"):
                sec = "METARELEASE"
                for k in ["URI",
                          "URI_LTS",
                          "URI_UNSTABLE_POSTFIX",
                          "URI_PROPOSED_POSTFIX"]:
                    if parser.has_option(sec, k):
                        self._debug("%s: %s " % (self.CONF_METARELEASE,
                                                 parser.get(sec, k)))
                        setattr(self, "%s_%s" % (sec, k), parser.get(sec, k))

        # check the config file first to figure if we want lts upgrades only
        parser = configparser.ConfigParser()
        if os.path.exists(self.CONF):
            try:
                parser.read(self.CONF)
            except configparser.Error as e:
                sys.stderr.write("ERROR: failed to read '%s':\n%s" % (
                                 self.CONF, e))
                return
            # now check which specific url to use
            if parser.has_option("DEFAULT", "Prompt"):
                type = parser.get("DEFAULT", "Prompt").lower()
                if (type == "never" or type == "no"):
                    self.prompt = 'never'
                    # nothing to do for this object
                    # FIXME: what about no longer supported?
                    self.downloaded.set()
                    return
                elif type == "lts":
                    self.prompt = 'lts'
                    self.METARELEASE_URI = self.METARELEASE_URI_LTS
                else:
                    self.prompt = 'normal'
        # needed for the _tryUpgradeSelf() code in DistUpgradeController
        if forceLTS:
            self.METARELEASE_URI = self.METARELEASE_URI_LTS
        # devel and proposed "just" change the postfix
        if useDevelopmentRelease:
            self.METARELEASE_URI += self.METARELEASE_URI_UNSTABLE_POSTFIX
        elif useProposed:
            self.METARELEASE_URI += self.METARELEASE_URI_PROPOSED_POSTFIX

        self._debug("metarelease-uri: %s" % self.METARELEASE_URI)
        self.metarelease_information = None
        if not self._buildMetaReleaseFile():
            self._debug("_buildMetaReleaseFile failed")
            return
        # we start the download thread here and we have a timeout
        threading.Thread(target=self.download).start()
        #threading.Thread(target=self.check).start()

    def _buildMetaReleaseFile(self):
        # build the metarelease_file name
        self.METARELEASE_FILE = os.path.join(
            "/var/lib/update-manager/",
            os.path.basename(self.METARELEASE_URI))
        # check if we can write to the global location, if not,
        # write to homedir
        try:
            open(self.METARELEASE_FILE, "a").close()
        except IOError as e:
            cache_dir = os.getenv(
                "XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
            # Take special care when creating this directory; ~/.cache needs
            # to be created with mode 0700, but the other directories do
            # not.
            cache_parent_dir = os.path.split(cache_dir)[0]
            if not os.path.exists(cache_parent_dir):
                try:
                    os.makedirs(cache_parent_dir)
                except OSError as e:
                    sys.stderr.write("mkdir() failed: '%s'" % e)
                    return False
            if not os.path.exists(cache_dir):
                try:
                    os.mkdir(cache_dir, 0o700)
                except OSError as e:
                    sys.stderr.write("mkdir() failed: '%s'" % e)
                    return False
            path = os.path.join(cache_dir, 'update-manager-core')
            if not os.path.exists(path):
                try:
                    os.mkdir(path)
                except OSError as e:
                    sys.stderr.write("mkdir() failed: '%s'" % e)
                    return False
            self.METARELEASE_FILE = os.path.join(
                path,
                os.path.basename(self.METARELEASE_URI))
        # if it is empty, remove it to avoid I-M-S hits on empty file
        try:
            if os.path.getsize(self.METARELEASE_FILE) == 0:
                os.unlink(self.METARELEASE_FILE)
        except Exception as e:
            pass
        return True

    def dist_no_longer_supported(self, dist):
        """ virtual function that is called when the distro is no longer
            supported
        """
        self.no_longer_supported = dist

    def new_dist_available(self, dist):
        """ virtual function that is called when a new distro release
            is available
        """
        self.new_dist = dist

    def parse(self):
        self._debug("MetaRelease.parse()")
        current_dist_name = self.current_dist_name
        self._debug("current dist name: '%s'" % current_dist_name)
        current_dist = None
        dists = []

        # parse the metarelease_information file
        index_tag = apt_pkg.TagFile(self.metarelease_information)
        try:
            while index_tag.step():
                for required_key in ("Dist", "Version", "Supported", "Date"):
                    if required_key not in index_tag.section:
                        raise MetaReleaseParseError(
                            "Required key '%s' missing" % required_key)
                name = index_tag.section["Dist"]
                self._debug("found distro name: '%s'" % name)
                rawdate = index_tag.section["Date"]
                parseddate = list(email.utils.parsedate(rawdate))
                parseddate[8] = 0  # assume no DST
                date = time.mktime(tuple(parseddate))
                supported = int(index_tag.section["Supported"])
                version = index_tag.section["Version"]
                # add the information to a new date object
                dist = Dist(name, version, date, supported)
                if "ReleaseNotes" in index_tag.section:
                    dist.releaseNotesURI = index_tag.section["ReleaseNotes"]
                    lang = get_lang()
                    if lang:
                        dist.releaseNotesURI += "?lang=%s" % lang
                if "ReleaseNotesHtml" in index_tag.section:
                    dist.releaseNotesHtmlUri = index_tag.section[
                        "ReleaseNotesHtml"]
                    query = self._get_release_notes_uri_query_string(dist)
                    if query:
                        dist.releaseNotesHtmlUri += query
                if "UpgradeTool" in index_tag.section:
                    dist.upgradeTool = index_tag.section["UpgradeTool"]
                if "UpgradeToolSignature" in index_tag.section:
                    dist.upgradeToolSig = index_tag.section[
                        "UpgradeToolSignature"]
                if "UpgradeBroken" in index_tag.section:
                    dist.upgrade_broken = index_tag.section["UpgradeBroken"]
                dists.append(dist)
                if name == current_dist_name:
                    current_dist = dist
        except apt_pkg.Error:
            raise MetaReleaseParseError("Unable to parse %s" %
                                        self.METARELEASE_URI)

        self.metarelease_information.close()
        self.metarelease_information = None

        # first check if the current runing distro is in the meta-release
        # information. if not, we assume that we run on something not
        # supported and silently return
        if current_dist is None:
            self._debug("current dist not found in meta-release file\n")
            return False

        # then see what we can upgrade to
        upgradable_to = ""
        for dist in dists:
            if dist.date > current_dist.date:
                # Only offer to upgrade to an unsupported release if running
                # with useDevelopmentRelease, this way one can upgrade from an
                # LTS release to the next supported non-LTS release e.g. from
                # 14.04 to 15.04.
                if not dist.supported and not self.useDevelopmentRelease:
                    continue
                upgradable_to = dist
                self._debug("new dist: %s" % upgradable_to)
                break

        # only warn if unsupported and a new dist is available (because
        # the development version is also unsupported)
        if upgradable_to != "" and not current_dist.supported:
            self.upgradable_to = upgradable_to
            self.dist_no_longer_supported(current_dist)
        if upgradable_to != "":
            self.upgradable_to = upgradable_to
            self.new_dist_available(upgradable_to)

        # parsing done and sucessfully
        return True

    # the network thread that tries to fetch the meta-index file
    # can't touch the gui, runs as a thread
    def download(self):
        self._debug("MetaRelease.download()")
        lastmodified = 0
        req = Request(self.METARELEASE_URI)
        # make sure that we always get the latest file (#107716)
        req.add_header("Cache-Control", "No-Cache")
        req.add_header("Pragma", "no-cache")
        if os.access(self.METARELEASE_FILE, os.W_OK):
            try:
                lastmodified = os.stat(self.METARELEASE_FILE).st_mtime
            except OSError as e:
                pass
        if lastmodified > 0 and not self.forceDownload:
            req.add_header("If-Modified-Since",
                           time.asctime(time.gmtime(lastmodified)))
        try:
            # open
            uri = urlopen(req, timeout=20)
            # sometime there is a root owned meta-relase file
            # there, try to remove it so that we get it
            # with proper permissions
            if (os.path.exists(self.METARELEASE_FILE) and
                    not os.access(self.METARELEASE_FILE, os.W_OK)):
                try:
                    os.unlink(self.METARELEASE_FILE)
                except OSError as e:
                    print("Can't unlink '%s' (%s)" % (self.METARELEASE_FILE,
                                                      e))
            # we may get exception here on e.g. disk full
            try:
                f = open(self.METARELEASE_FILE, "w+")
                for line in uri.readlines():
                    f.write(line.decode("UTF-8"))
                f.flush()
                f.seek(0, 0)
                self.metarelease_information = f
            except IOError as e:
                pass
            uri.close()
        # http error
        except HTTPError as e:
            # mvo: only reuse local info on "not-modified"
            if e.code == 304 and os.path.exists(self.METARELEASE_FILE):
                self._debug("reading file '%s'" % self.METARELEASE_FILE)
                self.metarelease_information = open(self.METARELEASE_FILE, "r")
            else:
                self._debug("result of meta-release download: '%s'" % e)
        # generic network error
        except (URLError, BadStatusLine, socket.timeout) as e:
            self._debug("result of meta-release download: '%s'" % e)
            print("Failed to connect to %s. Check your Internet connection "
                  "or proxy settings" % self.METARELEASE_URI)
        # now check the information we have
        if self.metarelease_information is not None:
            self._debug("have self.metarelease_information")
            try:
                self.parse()
            except Exception as e:
                logging.exception("parse failed for '%s'" %
                                  self.METARELEASE_FILE)
                # no use keeping a broken file around
                os.remove(self.METARELEASE_FILE)
            # we don't want to keep a meta-release file around when it
            # has a "Broken" flag, this ensures we are not bitten by
            # I-M-S/cache issues
            if self.new_dist and self.new_dist.upgrade_broken:
                os.remove(self.METARELEASE_FILE)
        else:
            self._debug("NO self.metarelease_information")
        self.downloaded.set()

    @property
    def downloading(self):
        return not self.downloaded.is_set()

    def _get_release_notes_uri_query_string(self, dist):
        q = "?"
        # get the lang
        lang = get_lang()
        if lang:
            q += "lang=%s&" % lang
        # get the os
        q += "os=%s&" % self.flavor
        # get the version to upgrade to
        q += "ver=%s" % dist.version
        # the archive didn't respond well to ? being %3F
        return quote(q, '/?')

    def _debug(self, msg):
        if self.DEBUG:
            sys.stderr.write(msg + "\n")


if __name__ == "__main__":
    meta = MetaReleaseCore(False, False)
