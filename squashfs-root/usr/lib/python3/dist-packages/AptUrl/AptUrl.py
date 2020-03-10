# Copyright (c) 2007-2008 Canonical
#
# AUTHOR:
# Michael Vogt <mvo@ubuntu.com>
# With contributions by Siegfried-A. Gevatter <rainct@ubuntu.com>
#
# This file is part of AptUrl
#
# AptUrl is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# AptUrl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with AptUrl; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import apt
import apt_pkg

import aptsources.distro
from . import Parser
from . import Helpers
from .Helpers import _

from aptsources.sourceslist import SourcesList
from optparse import OptionParser

import os
import os.path

# adding new repositories is currently disabled because some people have
# security concerns about this feature
allow_new_repositories = False

# channels that we know about
channelsdir = "/usr/share/app-install/channels"

# return codes
(RESULT_OK,
 RESULT_CANCELT,
 RESULT_ERROR,
 RESULT_BADARGS) = list(range(4))

class AptUrlController(object):

    def __init__(self, ui):
        self.ui = ui

    def enableSection(self, apturl):
        # parse sources.list
        sourceslist = SourcesList()
        distro = aptsources.distro.get_distro()
        distro.get_sources(sourceslist)

        # check if we actually need to enable anything
        requested_components = []
        for component in apturl.section:
            if not component in distro.enabled_comps:
                requested_components.append(component)
        # if not, we are fine
        if not requested_components:
            return RESULT_OK
        # otherwise ask the user if the really wants to anble them
        if not self.ui.askEnableSections(apturl.section):
            return RESULT_CANCELT
        if not self.ui.doEnableSection(apturl.section):
            self.ui.error(_("Enabling '%s' failed") %
                          ", ".join(apturl.section))
            return RESULT_ERROR
        self.ui.doUpdate()
        self.openCache()
        return RESULT_OK

    def enableChannel(self, apturl):
        # ensure that no funny path tricks can be played
        # by e.g. passing "apt:foo?channel=../../"
        channel = os.path.basename(apturl.channel)

        channelpath = "%s/%s.list" % (channelsdir,channel)
        channelkey = "%s/%s.key" % (channelsdir,channel)
        channelhtml = "%s/%s.eula" % (channelsdir,channel)

        # check
        if not os.path.exists(channelpath):
            self.ui.error(_("Unknown channel '%s'") % channel,
                          _("The channel '%s' is not known") % channel)
            return RESULT_ERROR
        channel_info_html = ""
        if os.path.exists(channelhtml):
            channel_info_html = open(channelhtml).read()
        if not self.ui.askEnableChannel(apturl.channel, channel_info_html):
            return RESULT_CANCELT
        if not self.ui.doEnableChannel(channelpath, channelkey):
            self.ui.error(_("Enabling channel '%s' failed") % apturl.channel)
            return RESULT_ERROR
        self.ui.doUpdate()
        self.openCache()
        return RESULT_OK

    def openCache(self):
        try:
            self.cache = apt.Cache()
        except SystemError as strerr:
            if not '/etc/apt/sources.list' in str(strerr):
                raise
            self.ui.error(_("Invalid /etc/apt/sources.list file"), strerr)
            return False
        if self.cache._depcache.broken_count > 0:
            err_header = _("Software index is broken")
            err_body = _("This is a major failure of your software "
                         "management system. Please check for broken packages "
                         "with synaptic, check the file permissions and "
                         "correctness of the file '/etc/apt/sources.list' and "
                         "reload the software information with: "
                         "'sudo apt-get update' and 'sudo apt-get install -f'."
                         )
            self.ui.error(err_header, err_body)
            return False
        return True

    def parseArgs(self):
        parser = OptionParser()
        parser.add_option("-p", "--http-proxy", dest="http_proxy",
                          default=None, help="use http proxy")
        (options, args) = parser.parse_args()

        # eval and add proxy
        if options.http_proxy is not None:
            proxy = options.http_proxy
            if not ":" in proxy:
                proxy += ":3128"
            os.environ["http_proxy"] = "http://%s" % proxy

        # parse
        try:
            apturl_list = Parser.parse(args[0])
        except IndexError as e:
            self.ui.error(_("Need a url to continue, exiting"))
            return []
        except Parser.InvalidUrlException as e:
            self.ui.error(_("Invalid url: '%s' given, exiting") % e.url,
                          str(e))
            return []
        return (apturl_list)

    def verifyInstall(self, apturl):
        " verify that the install package actually is installed "
        # check if the package got actually installed
        self.openCache()
        pkg = self.cache[apturl.package]
        if (not pkg.is_installed or
            pkg._pkg.current_state != apt_pkg.CURSTATE_INSTALLED or
            self.cache._depcache.broken_count > 0):
            return False
        return True

    def main(self):
        # global return code
        ret = RESULT_OK
        ui = self.ui

        # parse arguments
        apturl_list = self.parseArgs()
        if not apturl_list:
            return RESULT_BADARGS

        # open cache
        if not self.openCache():
            return RESULT_ERROR

        # now go over the url list
        for apturl in apturl_list:
            # FIXME: move this code block into a func like
            #        evalAptUrl()

            if not apturl.schema in ("apt", "apt+http"):
                self.ui.error(_("Can not deal with protocol '%s' ")
                              % apturl.schema)
                continue

            if apturl.section:
                if self.enableSection(apturl) != RESULT_OK:
                    continue
            elif apturl.channel:
                if self.enableChannel(apturl) != RESULT_OK:
                    continue
            elif apturl.refresh is not None:
                ui.doUpdate()
                if not self.openCache():
                    return RESULT_ERROR

            # now check the package
            if apturl.package not in self.cache:
                try:
                    package_in_cache = bool(self.cache._cache[apturl.package])
                except KeyError:
                    package_in_cache = False
                if package_in_cache:
                    ui.error(_("Package '%s' is virtual.") % apturl.package)
                    continue
                else:
                    ui.error(_("Could not find package '%s'.")
                             % apturl.package)
                    continue

            if (self.cache[apturl.package].is_installed and
                apturl.minver is None):
                ui.message(_("Package '%s' is already installed")
                           % apturl.package)
                continue

            # ask the user
            pkg = self.cache[apturl.package]
            (sum, desc, homepage) = Helpers.parse_pkg(pkg)
            if not ui.askInstallPackage(apturl.package, sum, desc, homepage):
                ret = RESULT_CANCELT
                continue

            # try to install it
            try:
                self.cache[apturl.package].mark_install()
            except SystemError as e:
                ui.error(_("Can not install '%s' (%s) ") % (apturl.package, e))
                continue
            if apturl.minver is not None:
                verStr = self.cache[apturl.package].candidate.version
                if apt_pkg.version_compare(verStr, apturl.minver) < 1:
                    ui.error(_(
                        "Package '%s' requests minimal version '%s', but "
                        "only '%s' is available") % (apturl.package,
                                                     apturl.minver,
                                                     verStr))
                    continue

            # install it
            ui.doInstall(apturl)

            if not self.verifyInstall(apturl):
                ret = RESULT_ERROR

        # return values
        return ret
