# DistUpgradeController.py 
#  
#  Copyright (c) 2004-2008 Canonical
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


import apt
import apt_pkg
import sys
import os
import subprocess
import locale
import logging
import shutil
import glob
import time
import copy
from configparser import NoOptionError
from configparser import ConfigParser as SafeConfigParser
from .telemetry import get as get_telemetry
from .utils import (country_mirror,
                    url_downloadable,
                    check_and_fix_xbit,
                    get_arch,
                    iptables_active,
                    inside_chroot,
                    get_string_with_no_auth_from_source_entry,
                    is_child_of_process_name,
                    inhibit_sleep)
from string import Template
from urllib.parse import urlsplit

from .DistUpgradeView import Step
from .DistUpgradeCache import MyCache
from .DistUpgradeConfigParser import DistUpgradeConfig
from .DistUpgradeQuirks import DistUpgradeQuirks
from .DistUpgradeAptCdrom import AptCdrom

# workaround broken relative import in python-apt (LP: #871007), we
# want the local version of distinfo.py from oneiric, but because of
# a bug in python-apt we will get the natty version that does not
# know about "Component.parent_component" leading to a crash
from . import distinfo
from . import sourceslist
sourceslist.DistInfo = distinfo.DistInfo

from .sourceslist import SourcesList, is_mirror
from .distro import get_distro, NoDistroTemplateException

from .DistUpgradeGettext import gettext as _
from .DistUpgradeGettext import ngettext
import gettext

from .DistUpgradeCache import (CacheExceptionDpkgInterrupted,
                               CacheExceptionLockingFailed,
                               NotEnoughFreeSpaceError)
from .DistUpgradeApport import run_apport

REBOOT_REQUIRED_FILE = "/var/run/reboot-required"


def component_ordering_key(a):
    """ key() function for sorted to ensure "correct" component ordering """
    ordering = ["main", "restricted", "universe", "multiverse"]
    try:
        return ordering.index(a)
    except ValueError:
        # ensure to sort behind the "official" components, order is not
        # really important for those
        return len(ordering)+1


class NoBackportsFoundException(Exception):
    pass


class DistUpgradeController(object):
    """ this is the controller that does most of the work """
    
    def __init__(self, distUpgradeView, options=None, datadir=None):
        # setup the paths
        localedir = "/usr/share/locale/"
        if datadir == None or datadir == '.':
            datadir = os.getcwd()
            localedir = os.path.join(datadir,"mo")
        self.datadir = datadir
        self.options = options

        # init gettext
        gettext.bindtextdomain("ubuntu-release-upgrader",localedir)
        gettext.textdomain("ubuntu-release-upgrader")

        # setup the view
        logging.debug("Using '%s' view" % distUpgradeView.__class__.__name__)
        self._view = distUpgradeView
        self._view.updateStatus(_("Reading cache"))
        self.cache = None
        self.fetcher = None

        if not self.options or self.options.withNetwork == None:
            self.useNetwork = True
        else:
            self.useNetwork = self.options.withNetwork
        if options:
            cdrompath = options.cdromPath
        else:
            cdrompath = None
        self.aptcdrom = AptCdrom(distUpgradeView, cdrompath)

        # the configuration
        self.config = DistUpgradeConfig(datadir)
        self.sources_backup_ext = "."+self.config.get("Files","BackupExt")

        # move some of the options stuff into the self.config, 
        # ConfigParser deals only with strings it seems *sigh*
        self.config.add_section("Options")
        self.config.set("Options","withNetwork", str(self.useNetwork))
        if self.options:
            if self.options.devel_release:
                self.config.set("Options","devRelease", "True")
            else:
                self.config.set("Options","devRelease", "False")

        # some constants here
        self.fromDist = self.config.get("Sources","From")
        self.toDist = self.config.get("Sources","To")
        self.origin = self.config.get("Sources","ValidOrigin")
        self.arch = get_arch()

        # we run with --force-overwrite by default
        if "RELEASE_UPGRADE_NO_FORCE_OVERWRITE" not in os.environ:
            logging.debug("enable dpkg --force-overwrite")
            apt_pkg.config.set("DPkg::Options::","--force-overwrite")

        # we run in full upgrade mode by default
        self._partialUpgrade = False
        
        # install the quirks handler
        self.quirks = DistUpgradeQuirks(self, self.config)

        # install a logind sleep inhibitor
        self.inhibitor_fd = inhibit_sleep()

        # setup env var 
        os.environ["RELEASE_UPGRADE_IN_PROGRESS"] = "1"
        os.environ["PYCENTRAL_FORCE_OVERWRITE"] = "1"
        os.environ["PATH"] = "%s:%s" % (os.getcwd()+"/imported",
                                        os.environ["PATH"])
        check_and_fix_xbit("./imported/invoke-rc.d")

        # set max retries
        maxRetries = self.config.getint("Network","MaxRetries")
        apt_pkg.config.set("Acquire::Retries", str(maxRetries))
        # max sizes for dpkgpm for large installs (see linux/limits.h and 
        #                                          linux/binfmts.h)
        apt_pkg.config.set("Dpkg::MaxArgs", str(64*1024))
        apt_pkg.config.set("Dpkg::MaxArgBytes", str(128*1024))

        # smaller to avoid hangs
        apt_pkg.config.set("Acquire::http::Timeout","20")
        apt_pkg.config.set("Acquire::ftp::Timeout","20")

        # no list cleanup here otherwise a "cancel" in the upgrade
        # will not restore the full state (lists will be missing)
        apt_pkg.config.set("Apt::Get::List-Cleanup", "false")

        # forced obsoletes
        self.forced_obsoletes = self.config.getlist("Distro","ForcedObsoletes")
        # list of valid mirrors that we can add
        self.valid_mirrors = self.config.getListFromFile("Sources","ValidMirrors")
        # third party mirrors
        self.valid_3p_mirrors = []
        if self.config.has_section('ThirdPartyMirrors'):
            self.valid_3p_mirrors = [pair[1] for pair in
                                     self.config.items('ThirdPartyMirrors')]
        # debugging
        #apt_pkg.config.set("DPkg::Options::","--debug=0077")

        # apt cron job
        self._aptCronJobPerms = 0o755
        # for inhibiting idle
        self._uid = ''
        self._user_env = {}

    def openCache(self, lock=True, restore_sources_list_on_fail=False):
        logging.debug("openCache()")
        if self.cache is None:
            self.quirks.run("PreCacheOpen")
        else:
            self.cache.release_lock()
            self.cache.unlock_lists_dir()
        # this loop will try getting the lock a couple of times
        MAX_LOCK_RETRIES = 20
        lock_retry = 0
        while True:
            try:
                # exit here once the cache is ready
                return self._openCache(lock)
            except CacheExceptionLockingFailed as e:
                # wait a bit
                lock_retry += 1
                self._view.processEvents()
                time.sleep(0.1)
                logging.debug(
                    "failed to lock the cache, retrying (%i)" % lock_retry)
                # and give up after some time
                if lock_retry > MAX_LOCK_RETRIES:
                    logging.error("Cache can not be locked (%s)" % e)
                    self._view.error(_("Unable to get exclusive lock"),
                                     _("This usually means that another "
                                       "package management application "
                                       "(like apt-get or aptitude) "
                                       "already running. Please close that "
                                       "application first."));
                    if restore_sources_list_on_fail:
                        self.abort()
                    else:
                        sys.exit(1)

    def _openCache(self, lock):
        try:
            self.cache = MyCache(self.config,
                                 self._view,
                                 self.quirks,
                                 self._view.getOpCacheProgress(),
                                 lock)
            # alias name for the plugin interface code
            self.apt_cache = self.cache
        # if we get a dpkg error that it was interrupted, just
        # run dpkg --configure -a
        except CacheExceptionDpkgInterrupted:
            logging.warning("dpkg interrupted, calling dpkg --configure -a")
            cmd = ["/usr/bin/dpkg","--configure","-a"]
            if os.environ.get("DEBIAN_FRONTEND") == "noninteractive":
                cmd.append("--force-confold")
            self._view.getTerminal().call(cmd)
            self.cache = MyCache(self.config,
                                 self._view,
                                 self.quirks,
                                 self._view.getOpCacheProgress())
        self.cache.partialUpgrade = self._partialUpgrade
        logging.debug("/openCache(), new cache size %i" % len(self.cache))

    def _viewSupportsSSH(self):
      """
      Returns True if this view support upgrades over ssh.
      In theory all views should support it, but for savety
      we do only allow text ssh upgrades (see LP: #322482)
      """
      supported = self.config.getlist("View","SupportSSH")
      if self._view.__class__.__name__ in supported:
          return True
      return False

    def _sshMagic(self):
        """ this will check for server mode and if we run over ssh.
            if this is the case, we will ask and spawn a additional
            daemon (to be sure we have a spare one around in case
            of trouble)
        """
        pidfile = os.path.join("/var/run/release-upgrader-sshd.pid")
        if (not os.path.exists(pidfile) and 
            os.path.isdir("/proc") and
            is_child_of_process_name("sshd")):
            # check if the frontend supports ssh upgrades (see lp: #322482)
            if not self._viewSupportsSSH():
                logging.error("upgrade over ssh not allowed")
                self._view.error(_("Upgrading over remote connection not supported"),
                                 _("You are running the upgrade over a "
                                   "remote ssh connection with a frontend "
                                   "that does "
                                   "not support this. Please try a text "
                                   "mode upgrade with 'do-release-upgrade'."
                                   "\n\n"
                                   "The upgrade will "
                                   "abort now. Please try without ssh.")
                                 )
                sys.exit(1)
                return False
            # ask for a spare one to start (and below 1024)
            port = 1022
            res = self._view.askYesNoQuestion(
                _("Continue running under SSH?"),
                _("This session appears to be running under ssh. "
                  "It is not recommended to perform a upgrade "
                  "over ssh currently because in case of failure "
                  "it is harder to recover.\n\n"
                  "If you continue, an additional ssh daemon will be "
                  "started at port '%s'.\n"
                  "Do you want to continue?") % port)
            # abort
            if res == False:
                sys.exit(1)
            res = subprocess.call(["/usr/sbin/sshd",
                                   "-o", "PidFile=%s" % pidfile,
                                   "-p",str(port)])
            if res == 0:
                summary = _("Starting additional sshd")
                descr =  _("To make recovery in case of failure easier, an "
                           "additional sshd will be started on port '%s'. "
                           "If anything goes wrong with the running ssh "
                           "you can still connect to the additional one.\n"
                           ) % port
                if iptables_active():
                    cmd = "iptables -I INPUT -p tcp --dport %s -j ACCEPT" % port
                    descr += _(
                        "If you run a firewall, you may need to "
                        "temporarily open this port. As this is "
                        "potentially dangerous it's not done automatically. "
                        "You can open the port with e.g.:\n'%s'") % cmd
                self._view.information(summary, descr)
        return True

    def _tryUpdateSelf(self):
        """ this is a helper that is run if we are started from a CD
            and we have network - we will then try to fetch a update
            of ourself
        """  
        from .MetaRelease import MetaReleaseCore
        from .DistUpgradeFetcherSelf import DistUpgradeFetcherSelf
        # check if we run from a LTS 
        forceLTS=False
        if (self.release == "dapper" or
            self.release == "hardy" or
            self.release == "lucid" or
            self.release == "precise"):
            forceLTS=True
        m = MetaReleaseCore(useDevelopmentRelease=False,
                            forceLTS=forceLTS)
        # this will timeout eventually
        self._view.processEvents()
        while not m.downloaded.wait(0.1):
            self._view.processEvents()
        if m.new_dist is None:
            logging.error("No new dist found")
            return False
        # we have a new dist
        progress = self._view.getAcquireProgress()
        fetcher = DistUpgradeFetcherSelf(new_dist=m.new_dist,
                                         progress=progress,
                                         options=self.options,
                                         view=self._view)
        fetcher.run()

    def _pythonSymlinkCheck(self):
        """ sanity check that /usr/bin/python points to the default
            python version. Users tend to modify this symlink, which
            breaks stuff in obscure ways (Ubuntu #75557).
        """
        logging.debug("_pythonSymlinkCheck run")
        binaries_and_dirnames = [("python", "python"), ("python2", "python"),
                                 ("python3", "python3")]
        for binary, dirname in binaries_and_dirnames:
            debian_defaults = '/usr/share/%s/debian_defaults' % dirname
            if os.path.exists(debian_defaults):
                config = SafeConfigParser()
                with open(debian_defaults) as f:
                    config.readfp(f)
                try:
                    expected_default = config.get('DEFAULT', 'default-version')
                except NoOptionError:
                    logging.debug("no default version for %s found in '%s'" %
                                  (binary, config))
                    return False
                try:
                    fs_default_version = os.readlink('/usr/bin/%s' % binary)
                except OSError as e:
                    logging.error("os.readlink failed (%s)" % e)
                    return False
                if not fs_default_version in (expected_default, os.path.join('/usr/bin', expected_default)) \
                        and not (binary == 'python' and fs_default_version in ('python2', '/usr/bin/python2')):
                    logging.debug("%s symlink points to: '%s', but expected is '%s' or '%s'" %
                                  (binary, fs_default_version, expected_default, os.path.join('/usr/bin', expected_default)))
                    return False
        return True


    def prepare(self):
        """ initial cache opening, sanity checking, network checking """
        # first check if that is a good upgrade
        self.release = release = subprocess.Popen(["lsb_release","-c","-s"],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True).communicate()[0].strip()
        logging.debug("lsb-release: '%s'" % release)
        if not (release == self.fromDist or release == self.toDist):
            logging.error("Bad upgrade: '%s' != '%s' " % (release, self.fromDist))
            self._view.error(_("Can not upgrade"),
                             _("An upgrade from '%s' to '%s' is not "
                               "supported with this tool." % (release, self.toDist)))
            sys.exit(1)

        # setup backports (if we have them)
        if self.options and self.options.havePrerequists:
            backportsdir = os.getcwd()+"/backports"
            logging.info("using backports in '%s' " % backportsdir)
            logging.debug("have: %s" % glob.glob(backportsdir+"/*.udeb"))
            if os.path.exists(backportsdir+"/usr/bin/dpkg"):
                apt_pkg.config.set("Dir::Bin::dpkg",backportsdir+"/usr/bin/dpkg");
            if os.path.exists(backportsdir+"/usr/lib/apt/methods"):
                apt_pkg.config.set("Dir::Bin::methods",backportsdir+"/usr/lib/apt/methods")
            conf = backportsdir+"/etc/apt/apt.conf.d/01ubuntu"
            if os.path.exists(conf):
                logging.debug("adding config '%s'" % conf)
                apt_pkg.read_config_file(apt_pkg.config, conf)

        # do the ssh check and warn if we run under ssh
        self._sshMagic()
        # check python version
        if not self._pythonSymlinkCheck():
            logging.error("pythonSymlinkCheck() failed, aborting")
            self._view.error(_("Can not upgrade"),
                             _("Your python3 install is corrupted. "
                               "Please fix the '/usr/bin/python3' symlink."))
            sys.exit(1)
        # open cache
        try:
            self.openCache()
        except SystemError as e:
            logging.error("openCache() failed: '%s'" % e)
            return False
        if not self.cache.sanity_check(self._view):
            return False

        # now figure out if we need to go into desktop or 
        # server mode - we use a heuristic for this
        self.serverMode = self.cache.need_server_mode()
        if self.serverMode:
            os.environ["RELEASE_UPGRADE_MODE"] = "server"
        else:
            os.environ["RELEASE_UPGRADE_MODE"] = "desktop"

        if not self.checkViewDepends():
            logging.error("checkViewDepends() failed")
            return False

        from .DistUpgradeMain import SYSTEM_DIRS
        for systemdir in SYSTEM_DIRS:
            if os.path.exists(systemdir) and not os.access(systemdir, os.W_OK):
                logging.error("%s not writable" % systemdir)
                self._view.error(
                    _("Can not write to '%s'") % systemdir,
                    _("Its not possible to write to the system directory "
                      "'%s' on your system. The upgrade can not "
                      "continue.\n"
                      "Please make sure that the system directory is "
                      "writable.") % systemdir)
                self.abort()
            

        # FIXME: we may try to find out a bit more about the network
        # connection here and ask more  intelligent questions
        if self.aptcdrom and self.options and self.options.withNetwork == None:
            res = self._view.askYesNoQuestion(_("Include latest updates from the Internet?"),
                                              _("The upgrade system can use the internet to "
                                                "automatically download "
                                                "the latest updates and install them during the "
                                                "upgrade.  If you have a network connection this is "
                                                "highly recommended.\n\n"
                                                "The upgrade will take longer, but when "
                                                "it is complete, your system will be fully up to "
                                                "date.  You can choose not to do this, but you "
                                                "should install the latest updates soon after "
                                                "upgrading.\n"
                                                "If you answer 'no' here, the network is not "
                                                "used at all."),
                                              'Yes')
            self.useNetwork = res
            self.config.set("Options","withNetwork", str(self.useNetwork))
            logging.debug("useNetwork: '%s' (selected by user)" % res)
            if res:
                self._tryUpdateSelf()
        return True

    def _sourcesListEntryDownloadable(self, entry):
        """
        helper that checks if a sources.list entry points to 
        something downloadable
        """
        logging.debug("verifySourcesListEntry: %s" % entry)
        # no way to verify without network
        if not self.useNetwork:
            logging.debug("skipping downloadable check (no network)")
            return True
        # check if the entry points to something we can download
        uri = "%s/dists/%s/Release" % (entry.uri, entry.dist)
        return url_downloadable(uri, logging.debug)

    def rewriteSourcesList(self, mirror_check=True):
        if mirror_check:
            logging.debug("rewriteSourcesList() with mirror_check")
        else:
            logging.debug("rewriteSourcesList()")

        sync_components = self.config.getlist("Sources","Components")

        # skip mirror check if special environment is set
        # (useful for server admins with internal repos)
        if (self.config.getWithDefault("Sources","AllowThirdParty",False) or
            "RELEASE_UPGRADER_ALLOW_THIRD_PARTY" in os.environ):
            logging.warning("mirror check skipped, *overriden* via config")
            mirror_check=False

        # check if we need to enable main
        main_was_missing = False
        if mirror_check == True and self.useNetwork:
            # now check if the base-meta pkgs are available in
            # the archive or only available as "now"
            # -> if not that means that "main" is missing and we
            #    need to enable it
            logging.debug(self.config.getlist("Distro", "BaseMetaPkgs"))
            for pkgname in self.config.getlist("Distro", "BaseMetaPkgs"):
                logging.debug("Checking pkg: %s" % pkgname)
                if ((not pkgname in self.cache or
                     not self.cache[pkgname].candidate or
                     len(self.cache[pkgname].candidate.origins) == 0)
                    or
                    (self.cache[pkgname].candidate and
                     len(self.cache[pkgname].candidate.origins) == 1 and
                     self.cache[pkgname].candidate.origins[0].archive == "now")
                   ):
                    logging.debug("BaseMetaPkg '%s' has no candidate.origins" % pkgname)
                    try:
                        distro = get_distro()
                        distro.get_sources(self.sources)
                        distro.enable_component("main")
                        main_was_missing = True
                        logging.debug('get_distro().enable_component("main") succeeded')
                    except NoDistroTemplateException as e:
                        logging.exception('NoDistroTemplateException raised: %s' % e)
                        # fallback if everything else does not work,
                        # we replace the sources.list with lines to
                        # main and restricted
                        logging.debug('get_distro().enable_component("main") failed, overwriting sources.list instead as last resort')
                        comment = " auto generated by ubuntu-release-upgrader"
                        comps = ["main", "restricted"]
                        uri = "http://archive.ubuntu.com/ubuntu"
                        self.sources.add("deb", uri, self.toDist, comps,
                                         comment)
                        self.sources.add("deb", uri, self.toDist+"-updates",
                                         comps, comment)
                        self.sources.add("deb",
                                         "http://security.ubuntu.com/ubuntu",
                                         self.toDist+"-security", comps,
                                         comment)
                    break

        # this must map, i.e. second in "from" must be the second in "to"
        # (but they can be different, so in theory we could exchange
        #  component names here)
        pockets = self.config.getlist("Sources","Pockets")
        fromDists = [self.fromDist] + ["%s-%s" % (self.fromDist, x)
                                       for x in pockets]
        toDists = [self.toDist] + ["%s-%s" % (self.toDist,x)
                                   for x in pockets]
        self.sources_disabled = False

        # Special quirk to remove extras.ubuntu.com
        new_list = []
        for entry in self.sources.list[:]:
            if "/extras.ubuntu.com" in entry.uri:
                continue
            if entry.line.startswith(
                    "## This software is not part of Ubuntu, but is offered by third-party"):
                continue
            if entry.line.startswith(
                    "## developers who want to ship their latest software."):
                continue
            new_list.append(entry)
        self.sources.list = new_list

        # look over the stuff we have
        foundToDist = False
        # collect information on what components (main,universe) are enabled for what distro (sub)version
        # e.g. found_components = { 'hardy':set("main","restricted"), 'hardy-updates':set("main") }
        self.found_components = {}
        entry_uri_test_results = {}
        for entry in self.sources.list[:]:
            if entry.uri not in entry_uri_test_results:
                entry_uri_test_results[entry.uri] = 'unknown'

            # ignore invalid records or disabled ones
            if entry.invalid or entry.disabled:
                continue

            # we disable breezy cdrom sources to make sure that demoted
            # packages are removed
            if entry.uri.startswith("cdrom:") and entry.dist == self.fromDist:
                logging.debug("disabled '%s' cdrom entry (dist == fromDist)" % entry)
                entry.disabled = True
                continue
            # check if there is actually a lists file for them available
            # and disable them if not
            elif entry.uri.startswith("cdrom:"):
                # 
                listdir = apt_pkg.config.find_dir("Dir::State::lists")
                if not os.path.exists("%s/%s%s_%s_%s" % 
                                      (listdir,
                                       apt_pkg.uri_to_filename(entry.uri),
                                       "dists",
                                       entry.dist,
                                       "Release")):
                    logging.warning("disabling cdrom source '%s' because it has no Release file" % entry)
                    entry.disabled = True
                continue

            # special case for archive.canonical.com that needs to
            # be rewritten (for pre-gutsy upgrades)
            cdist = "%s-commercial" % self.fromDist
            if (not entry.disabled and
                entry.uri.startswith("http://archive.canonical.com") and
                entry.dist == cdist):
                entry.dist = self.toDist
                entry.comps = ["partner"]
                logging.debug("transitioned commercial to '%s' " % entry)
                continue

            # special case for landscape.canonical.com because they
            # don't use a standard archive layout (gutsy->hardy)
            # XXX - Is this still relevant?
            if (not entry.disabled and
                entry.uri.startswith("http://landscape.canonical.com/packages/%s" % self.fromDist)):
                logging.debug("commenting landscape.canonical.com out")
                entry.disabled = True
                continue

            # Disable proposed on upgrade to a development release.
            if (not entry.disabled and self.options
                and self.options.devel_release == True and
                "%s-proposed" % self.fromDist in entry.dist):
                logging.debug("upgrade to development release, disabling proposed")
                entry.dist = "%s-proposed" % self.toDist
                entry.comment += _("Not for humans during development stage of release %s") % self.toDist
                entry.disabled = True
                continue

            # handle upgrades from a EOL release and check if there
            # is a supported release available
            if (not entry.disabled and
                "old-releases.ubuntu.com/" in entry.uri):
                logging.debug("upgrade from old-releases.ubuntu.com detected")
                # test country mirror first, then archive.u.c
                for uri in ["http://%sarchive.ubuntu.com/ubuntu" % country_mirror(),
                            "http://archive.ubuntu.com/ubuntu"]:
                    test_entry = copy.copy(entry)
                    test_entry.uri = uri
                    test_entry.dist = self.toDist
                    if self._sourcesListEntryDownloadable(test_entry):
                        logging.info("transition from old-release.u.c to %s" % uri)
                        entry.uri = uri
                        if entry.uri not in entry_uri_test_results:
                            entry_uri_test_results[entry.uri] = 'passed'
                        break

            logging.debug("examining: '%s'" %  get_string_with_no_auth_from_source_entry(entry))
            # check if it's a mirror (or official site)
            validMirror = self.isMirror(entry.uri)
            thirdPartyMirror = not mirror_check or self.isThirdPartyMirror(entry.uri)
            if validMirror or thirdPartyMirror:
                # disabled/security/commercial/extras are special cases
                # we use validTo/foundToDist to figure out if we have a 
                # main archive mirror in the sources.list or if we 
                # need to add one
                validTo = True
                if (entry.disabled or
                    entry.type == "deb-src" or
                    "/security.ubuntu.com" in entry.uri or
                    "%s-security" % self.fromDist in entry.dist or
                    "%s-backports" % self.fromDist in entry.dist or
                    "/archive.canonical.com" in entry.uri):
                    validTo = False
                if entry.dist in toDists:
                    # so the self.sources.list is already set to the new
                    # distro
                    logging.debug("entry '%s' is already set to new dist" % get_string_with_no_auth_from_source_entry(entry))
                    foundToDist |= validTo
                elif entry.dist in fromDists:
                    if entry_uri_test_results[entry.uri] == 'unknown':
                        foundToDist |= validTo
                        # check to see whether the archive provides the new dist
                        test_entry = copy.copy(entry)
                        test_entry.dist = self.toDist
                        if not self._sourcesListEntryDownloadable(test_entry):
                            entry_uri_test_results[entry.uri] = 'failed'
                        else:
                            entry_uri_test_results[entry.uri] = 'passed'
                    if entry_uri_test_results[entry.uri] == 'failed':
                        entry.disabled = True
                        self.sources_disabled = True
                        logging.debug("entry '%s' was disabled (no Release file)" % get_string_with_no_auth_from_source_entry(entry))
                    else:
                        foundToDist |= validTo
                        entry.dist = toDists[fromDists.index(entry.dist)]
                        logging.debug("entry '%s' updated to new dist" % get_string_with_no_auth_from_source_entry(entry))
                elif entry.type == 'deb-src':
                    continue
                elif validMirror:
                    # disable all entries that are official but don't
                    # point to either "to" or "from" dist
                    entry.disabled = True
                    self.sources_disabled = True
                    logging.debug("entry '%s' was disabled (unknown dist)" % get_string_with_no_auth_from_source_entry(entry))

                # if we make it to this point, we have an official or third-party mirror
                # XXX - is this still relevant?
                # check if the arch is powerpc or sparc and if so, transition
                # to ports.ubuntu.com (powerpc got demoted in gutsy, sparc
                # in hardy)
                if (entry.type == "deb" and
                    not "ports.ubuntu.com" in entry.uri and
                    (self.arch == "powerpc" or self.arch == "sparc")):
                    logging.debug("moving %s source entry to 'ports.ubuntu.com' " % self.arch)
                    entry.uri = "http://ports.ubuntu.com/ubuntu-ports/"

                # gather what components are enabled and are inconsistent
                for d in ["%s" % self.toDist,
                          "%s-updates" % self.toDist,
                          "%s-security" % self.toDist]:
                    # create entry if needed, ignore disabled
                    # entries and deb-src
                    self.found_components.setdefault(d, set())
                    if (not entry.disabled and entry.dist == d and
                        entry.type == "deb"):
                        for comp in entry.comps:
                            # only sync components we know about
                            if not comp in sync_components:
                                continue
                            self.found_components[d].add(comp)

            else:
                # disable anything that is not from a official mirror or a whitelisted third party
                if entry.dist == self.fromDist:
                    entry.dist = self.toDist
                disable_comment = " " + _("disabled on upgrade to %s") % self.toDist
                if isinstance(entry.comment, bytes):
                    entry.comment += disable_comment.encode('UTF-8')
                else:
                    entry.comment += disable_comment
                entry.disabled = True
                self.sources_disabled = True
                logging.debug("entry '%s' was disabled (unknown mirror)" % get_string_with_no_auth_from_source_entry(entry))
                # if its not a valid mirror and we manually added main, be
                # nice and add pockets and components corresponding to what we
                # disabled.
                if main_was_missing:
                    if entry.dist in fromDists:
                        entry.dist = toDists[fromDists.index(entry.dist)]
                    if entry.dist not in toDists:
                        continue    # Unknown target, do not add this
                    # gather what components are enabled and are inconsistent
                    for d in ["%s" % self.toDist,
                              "%s-updates" % self.toDist,
                              "%s-security" % self.toDist]:
                        # create entry if needed, ignore deb-src entries
                        self.found_components.setdefault(d, set())
                        if entry.dist == d and entry.type == "deb":
                            for comp in entry.comps:
                                # only sync components we know about
                                if not comp in sync_components:
                                    continue
                                self.found_components[d].add(comp)
                    logging.debug("Adding entry: %s %s %s" % (entry.type, entry.dist, entry.comps))
                    uri = "http://archive.ubuntu.com/ubuntu"
                    comment = " auto generated by ubuntu-release-upgrader"
                    self.sources.add(entry.type, uri, entry.dist, entry.comps, comment)

        # now go over the list again and check for missing components
        # in $dist-updates and $dist-security and add them
        for entry in self.sources.list[:]:
            # skip all comps that are not relevant (including e.g. "hardy")
            if (entry.invalid or entry.disabled or entry.type == "deb-src" or
                entry.uri.startswith("cdrom:") or entry.dist == self.toDist):
                continue
            # now check for "$dist-updates" and "$dist-security" and add any inconsistencies
            if entry.dist in self.found_components:
                component_diff = self.found_components[self.toDist]-self.found_components[entry.dist]
                if component_diff:
                    logging.info("fixing components inconsistency from '%s'" % get_string_with_no_auth_from_source_entry(entry))
                    # extend and make sure to keep order
                    entry.comps.extend(
                        sorted(component_diff, key=component_ordering_key))
                    logging.info("to new entry '%s'" % get_string_with_no_auth_from_source_entry(entry))
                    del self.found_components[entry.dist]
        return foundToDist

    def updateSourcesList(self):
        logging.debug("updateSourcesList()")
        self.sources = SourcesList(matcherPath=self.datadir)
        
        if not any(e.type == "deb" and e.dist == self.fromDist for e in self.sources):
            res = self._view.askYesNoQuestion(_("No valid sources.list entry found"),
                             _("While scanning your repository "
                               "information no entry about %s could be "
                               "found.\n\n"
                               "An upgrade might not succeed.\n\n"
                               "Do you want to continue anyway?") % self.fromDist)
            if not res:
                self.abort()

        # backup first!
        self.sources.backup(self.sources_backup_ext)
        if not self.rewriteSourcesList(mirror_check=True):
            logging.error("No valid mirror found")
            res = self._view.askYesNoQuestion(_("No valid mirror found"),
                             _("While scanning your repository "
                               "information no mirror entry for "
                               "the upgrade was found. "
                               "This can happen if you run an internal "
                               "mirror or if the mirror information is "
                               "out of date.\n\n"
                               "Do you want to rewrite your "
                               "'sources.list' file anyway? If you choose "
                               "'Yes' here it will update all '%s' to '%s' "
                               "entries.\n"
                               "If you select 'No' the upgrade will cancel."
                               ) % (self.fromDist, self.toDist))
            if res:
                # re-init the sources and try again
                self.sources = SourcesList(matcherPath=self.datadir)
                # its ok if rewriteSourcesList fails here if
                # we do not use a network, the sources.list may be empty
                if (not self.rewriteSourcesList(mirror_check=False)
                    and self.useNetwork):
                    #hm, still nothing useful ...
                    prim = _("Generate default sources?")
                    secon = _("After scanning your 'sources.list' no "
                              "valid entry for '%s' was found.\n\n"
                              "Should default entries for '%s' be "
                              "added? If you select 'No', the upgrade "
                              "will cancel.") % (self.fromDist, self.toDist)
                    if not self._view.askYesNoQuestion(prim, secon):
                        self.abort()

                    # add some defaults here
                    # FIXME: find mirror here
                    logging.info("Generated new default sources.list")
                    uri = "http://archive.ubuntu.com/ubuntu"
                    comps = ["main","restricted"]
                    self.sources.add("deb", uri, self.toDist, comps)
                    self.sources.add("deb", uri, self.toDist+"-updates", comps)
                    self.sources.add("deb",
                                     "http://security.ubuntu.com/ubuntu/",
                                     self.toDist+"-security", comps)
            else:
                self.abort()

        # now write
        self.sources.save()

        # re-check if the written self.sources are valid, if not revert and
        # bail out
        # TODO: check if some main packages are still available or if we
        #       accidentally shot them, if not, maybe offer to write a standard
        #       sources.list?
        try:
            sourceslist = apt_pkg.SourceList()
            sourceslist.read_main_list()
        except SystemError:
            logging.error("Repository information invalid after updating (we broke it!)")
            if os.path.exists("/usr/bin/apport-bug"):
                self._view.error(_("Repository information invalid"),
                                 _("Upgrading the repository information "
                                   "resulted in a invalid file so a bug "
                                   "reporting process is being started."))
                subprocess.Popen(["apport-bug", "ubuntu-release-upgrader-core"])
            else:
                self._view.error(_("Repository information invalid"),
                                 _("Upgrading the repository information "
                                   "resulted in a invalid file. To report "
                                   "a bug install apport and then execute "
                                   "'apport-bug ubuntu-release-upgrader'."))
                logging.error("Missing apport-bug, bug report not "
                              "autocreated")
            return False

        if self.sources_disabled:
            self._view.information(_("Third party sources disabled"),
                             _("Some third party entries in your sources.list "
                               "were disabled. You can re-enable them "
                               "after the upgrade with the "
                               "'software-properties' tool or "
                               "your package manager."
                               ))
        get_telemetry().set_using_third_party_sources(self.sources_disabled)
        return True

    def _logChanges(self):
        # debugging output
        logging.debug("About to apply the following changes")
        inst = []
        up = []
        rm = []
        held = []
        keep = []
        for pkg in self.cache:
            if pkg.marked_install: inst.append(pkg.name)
            elif pkg.marked_upgrade: up.append(pkg.name)
            elif pkg.marked_delete: rm.append(pkg.name)
            elif (pkg.is_installed and pkg.is_upgradable): held.append(pkg.name)
            elif pkg.is_installed and pkg.marked_keep: keep.append(pkg.name)
        logging.debug("Keep at same version: %s" % " ".join(keep))
        logging.debug("Upgradable, but held- back: %s" % " ".join(held))
        logging.debug("Remove: %s" % " ".join(rm))
        logging.debug("Install: %s" % " ".join(inst))
        logging.debug("Upgrade: %s" % " ".join(up))

    def doPostInitialUpdate(self):
        # check if we have packages in ReqReinst state that are not
        # downloadable
        logging.debug("doPostInitialUpdate")
        self.quirks.run("PostInitialUpdate")
        if not self.cache:
            return False
        if len(self.cache.req_reinstall_pkgs) > 0:
            logging.warning("packages in reqReinstall state, trying to fix")
            self.cache.fix_req_reinst(self._view)
            self.openCache()
        if len(self.cache.req_reinstall_pkgs) > 0:
            reqreinst = self.cache.req_reinstall_pkgs
            header = ngettext("Package in inconsistent state",
                              "Packages in inconsistent state",
                              len(reqreinst))
            summary = ngettext("The package '%s' is in an inconsistent "
                               "state and needs to be reinstalled, but "
                               "no archive can be found for it. "
                               "Please reinstall the package manually "
                               "or remove it from the system.",
                               "The packages '%s' are in an inconsistent "
                               "state and need to be reinstalled, but "
                               "no archive can be found for them. "
                               "Please reinstall the packages manually "
                               "or remove them from the system.",
                               len(reqreinst)) % ", ".join(reqreinst)
            self._view.error(header, summary)
            return False
        # Log MetaPkgs installed to see if there is more than one.
        meta_pkgs = []
        for pkg in self.config.getlist("Distro","MetaPkgs"):
            if pkg in self.cache and self.cache[pkg].is_installed:
                meta_pkgs.append(pkg)
        logging.debug("MetaPkgs: %s" % " ".join(sorted(meta_pkgs)))
        # FIXME: check out what packages are downloadable etc to
        # compare the list after the update again
        self.obsolete_pkgs = self.cache._getObsoletesPkgs()
        self.foreign_pkgs = self.cache._getForeignPkgs(self.origin, self.fromDist, self.toDist)
        # If a PPA has already been disabled the pkgs won't be considered
        # foreign
        if len(self.foreign_pkgs) > 0:
            self.config.set("Options","foreignPkgs", "True")
        else:
            self.config.set("Options","foreignPkgs", "False")
        if self.serverMode:
            self.tasks = self.cache.installedTasks
        logging.debug("Foreign: %s" % " ".join(sorted(self.foreign_pkgs)))
        logging.debug("Obsolete: %s" % " ".join(sorted(self.obsolete_pkgs)))
        return True

    def doUpdate(self, showErrors=True, forceRetries=None):
        logging.debug("running doUpdate() (showErrors=%s)" % showErrors)
        if not self.useNetwork:
            logging.debug("doUpdate() will not use the network because self.useNetwork==false")
            return True
        self.cache._list.read_main_list()
        progress = self._view.getAcquireProgress()
        # FIXME: also remove all files from the lists partial dir!
        currentRetry = 0
        if forceRetries is not None:
            maxRetries=forceRetries
        else:
            maxRetries = self.config.getint("Network","MaxRetries")
        # LP: #1321959
        error_msg = ""
        while currentRetry < maxRetries:
            try:
                self.cache.update(progress)
            except (SystemError, IOError) as e:
                error_msg = str(e)
                logging.error("IOError/SystemError in cache.update(): '%s'. Retrying (currentRetry: %s)" % (e,currentRetry))
                currentRetry += 1
                continue
            # no exception, so all was fine, we are done
            return True

        logging.error("doUpdate() failed completely")
        if showErrors:
            self._view.error(_("Error during update"),
                             _("A problem occurred during the update. "
                               "This is usually some sort of network "
                               "problem, please check your network "
                               "connection and retry."), "%s" % error_msg)
        return False


    def _checkBootEfi(self):
        " check that /boot/efi is a mounted partition on an EFI system"

        # Not an UEFI system
        if not os.path.exists("/sys/firmware/efi"):
            logging.debug("Not an UEFI system")
            return True

        # Stuff we know about that would write to the ESP
        bootloaders = ["shim-signed", "grub-efi-amd64", "grub-efi-ia32", "grub-efi-arm", "grub-efi-arm64", "sicherboot"]

        if not any(bl in self.cache and self.cache[bl].is_installed for bl in bootloaders):
            logging.debug("UEFI system, but no UEFI grub installed")
            return True

        mounted=False

        with open("/proc/mounts") as mounts:
            for line in mounts:
                line=line.strip()
                try:
                    (what, where, fs, options, a, b) = line.split()
                except ValueError as e:
                    logging.debug("line '%s' in /proc/mounts not understood (%s)" % (line, e))
                    continue

                if where != "/boot/efi":
                    continue

                mounted=True

                if "rw" in options.split(","):
                    logging.debug("Found writable ESP %s", line)
                    return True

        if not mounted:
            self._view.error(_("EFI System Partition (ESP) not usable"),
                             _("Your EFI System Partition (ESP) is not "
                               "mounted at /boot/efi. Please ensure that "
                               "it is properly configured and try again."))
        else:
            self._view.error(_("EFI System Partition (ESP) not usable"),
                             _("The EFI System Partition (ESP) mounted at "
                               "/boot/efi is not writable. Please mount "
                               "this partition read-write and try again."))
        return False

    def _checkFreeSpace(self):
        " this checks if we have enough free space on /var and /usr"
        err_sum = _("Not enough free disk space")
        # TRANSLATORS: you can change the order of the sentence,
        # make sure to keep all {str_*} string untranslated.
        err_msg = _("The upgrade has aborted. "
                    "The upgrade needs a total of {str_total} free space on disk '{str_dir}'. "
                    "Please free at least an additional {str_needed} of disk "
                    "space on '{str_dir}'. {str_remedy}")
        # specific ways to resolve lack of free space
        remedy_archivedir = _("Remove temporary packages of former "
                              "installations using 'sudo apt clean'.")
        remedy_boot = _("You can remove old kernels using "
                        "'sudo apt autoremove' and you could also "
                        "set COMPRESS=xz in "
                        "/etc/initramfs-tools/initramfs.conf to "
                        "reduce the size of your initramfs.")
        remedy_root = _("Empty your trash and remove temporary "
                        "packages of former installations using "
                        "'sudo apt-get clean'.")
        remedy_tmp = _("Reboot to clean up files in /tmp.")
        remedy_usr = _("")
        # allow override
        if self.config.getWithDefault("FreeSpace","SkipCheck",False):
            logging.warning("free space check skipped via config override")
            return True
        # do the check
        with_snapshots = self._is_apt_btrfs_snapshot_supported()
        try:
            self.cache.checkFreeSpace(with_snapshots)
        except NotEnoughFreeSpaceError as e:
            # ok, showing multiple error dialog sucks from the UI
            # perspective, but it means we do not need to break the
            # string freeze
            archivedir = apt_pkg.config.find_dir("Dir::Cache::archives")
            err_long = ""
            remedy = {archivedir: remedy_archivedir,
                      '/var': remedy_archivedir,
                      '/boot': remedy_boot,
                      '/': remedy_root,
                      '/tmp': remedy_tmp,
                      '/usr': remedy_usr}
            for req in e.free_space_required_list:
                if err_long != "":
                     err_long += " "
                if req.dir in remedy:
                    err_long += err_msg.format(str_total=req.size_total, str_dir=req.dir,
                                               str_needed=req.size_needed,
                                               str_remedy=remedy[req.dir])
                else:
                    err_long += err_msg.format(str_total=req.size_total, str_dir=req.dir,
                                               str_needed=req.size_needed,
                                               str_remedy='')
            self._view.error(err_sum, err_long)
            return False
        return True


    def calcDistUpgrade(self):
        self._view.updateStatus(_("Calculating the changes"))
        if not self.cache.distUpgrade(self._view, self.serverMode, self._partialUpgrade):
            return False

        if self.serverMode:
            if not self.cache.installTasks(self.tasks):
                return False

        # show changes and confirm
        changes = self.cache.get_changes()
        self._view.processEvents()

        # log the changes for debugging
        self._logChanges()
        self._view.processEvents()

        # check if we have enough free space 
        if not self._checkFreeSpace():
            return False

        # check that ESP is sane
        if not self._checkBootEfi():
            return False

        self._view.processEvents()

        # get the demotions
        self.installed_demotions = self.cache.get_installed_demoted_packages()
        if len(self.installed_demotions) > 0:
            self.installed_demotions.sort()
            logging.debug("demoted: '%s'" % " ".join([x.name for x in self.installed_demotions]))
            logging.debug("found components: %s" % self.found_components)

        # flush UI
        self._view.processEvents()
        return changes

    def askDistUpgrade(self):
        changes = self.calcDistUpgrade()

        if not changes:
            return False

        # ask the user
        res = self._view.confirmChanges(_("Do you want to start the upgrade?"),
                                        changes,
                                        self.installed_demotions,
                                        self.cache.required_download)
        return res

    def _disableAptCronJob(self):
        if os.path.exists("/etc/cron.daily/apt"):
            #self._aptCronJobPerms = os.stat("/etc/cron.daily/apt")[ST_MODE]
            logging.debug("disabling apt cron job (%s)" % oct(self._aptCronJobPerms))
            os.chmod("/etc/cron.daily/apt",0o644)
    def _enableAptCronJob(self):
        if os.path.exists("/etc/cron.daily/apt"):
            logging.debug("enabling apt cron job")
            os.chmod("/etc/cron.daily/apt", self._aptCronJobPerms)

    def doDistUpgradeFetching(self):
        # ensure that no apt cleanup is run during the download/install
        self._disableAptCronJob()
        # get the upgrade
        currentRetry = 0
        fprogress = self._view.getAcquireProgress()
        #iprogress = self._view.getInstallProgress(self.cache)
        # start slideshow
        url = self.config.getWithDefault("Distro","SlideshowUrl",None)
        if url:
            try:
                lang = locale.getdefaultlocale()[0].split('_')[0]
            except:
                logging.exception("getdefaultlocale")
                lang = "en"
            self._view.getHtmlView().open("%s#locale=%s" % (url, lang))
        # retry the fetching in case of errors
        maxRetries = self.config.getint("Network","MaxRetries")
        # FIXME: we get errors like 
        #   "I wasn't able to locate file for the %s package" 
        #  here sometimes. its unclear why and not reproducible, the 
        #  current theory is that for some reason the file is not
        #  considered trusted at the moment 
        #  pkgAcquireArchive::QueueNext() runs debReleaseIndex::IsTrused()
        #  (the later just checks for the existence of the .gpg file)
        #  OR 
        #  the fact that we get a pm and fetcher here confuses something
        #  in libapt?
        # POSSIBLE workaround: keep the list-dir locked so that 
        #          no apt-get update can run outside from the release
        #          upgrader 
        user_canceled = False
        # LP: #1102593 - In Python 3, the targets of except clauses get `del`d
        # from the current namespace after the exception is handled, so we
        # must assign it to a different variable in order to use it after
        # the while loop.
        exception = None
        while currentRetry < maxRetries:
            try:
                pm = apt_pkg.PackageManager(self.cache._depcache)
                self.fetcher = apt_pkg.Acquire(fprogress)
                self.cache._fetch_archives(self.fetcher, pm)
            except apt.cache.FetchCancelledException as e:
                logging.info("user canceled")
                user_canceled = True
                exception = e
                break
            except IOError as e:
                # fetch failed, will be retried
                logging.error("IOError in cache.commit(): '%s'. Retrying (currentTry: %s)" % (e,currentRetry))
                currentRetry += 1
                exception = e
                continue
            return True

        # maximum fetch-retries reached without a successful commit
        if user_canceled:
            self._view.information(_("Upgrade canceled"),
                                   _("The upgrade will cancel now and the "
                                     "original system state will be restored. "
                                     "You can resume the upgrade at a later "
                                     "time."))
        else:
            logging.error("giving up on fetching after maximum retries")
            self._view.error(_("Could not download the upgrades"),
                             _("The upgrade has aborted. Please check your "
                               "Internet connection or "
                               "installation media and try again. All files "
                               "downloaded so far have been kept."),
                             "%s" % exception)
        # abort here because we want our sources.list back
        self._enableAptCronJob()
        self.abort()

    def _is_apt_btrfs_snapshot_supported(self):
        """ check if apt-btrfs-snapshot is usable """
        try:
            import apt_btrfs_snapshot
        except ImportError:
            return
        try:
            apt_btrfs = apt_btrfs_snapshot.AptBtrfsSnapshot()
            res = apt_btrfs.snapshots_supported()
        except:
            logging.exception("failed to check btrfs support")
            return False
        logging.debug("apt btrfs snapshots supported: %s" % res)
        return res

    def _maybe_create_apt_btrfs_snapshot(self):
        """ create btrfs snapshot (if btrfs layout is there) """
        if not self._is_apt_btrfs_snapshot_supported():
            return
        import apt_btrfs_snapshot
        apt_btrfs = apt_btrfs_snapshot.AptBtrfsSnapshot()
        prefix = "release-upgrade-%s-" % self.toDist
        res = apt_btrfs.create_btrfs_root_snapshot(prefix)
        logging.info("creating snapshot '%s' (success=%s)" % (prefix, res))

    def doDistUpgradeSimulation(self):
        backups = {}
        backups["dir::bin::dpkg"] = [apt_pkg.config["dir::bin::dpkg"]]
        apt_pkg.config["dir::bin::dpkg"] = "/bin/true"

        for lst in "dpkg::pre-invoke", "dpkg::pre-install-pkgs", "dpkg::post-invoke", "dpkg::post-install-pkgs":
            backups[lst + "::"] = apt_pkg.config.value_list(lst)
            apt_pkg.config.clear(lst)

        try:
            return self.doDistUpgrade()
        finally:
            for lst in backups:
                for item in backups[lst]:
                    apt_pkg.config.set(lst, item)

    def doDistUpgrade(self):
        # add debug code only here
        #apt_pkg.config.set("Debug::pkgDpkgPM", "1")
        #apt_pkg.config.set("Debug::pkgOrderList", "1")
        #apt_pkg.config.set("Debug::pkgPackageManager", "1")

        # get the upgrade
        currentRetry = 0
        fprogress = self._view.getAcquireProgress()
        iprogress = self._view.getInstallProgress(self.cache)
        # retry the fetching in case of errors
        maxRetries = self.config.getint("Network","MaxRetries")
        if not self._partialUpgrade:
            self.quirks.run("StartUpgrade")
            # FIXME: take this into account for diskspace calculation
            self._maybe_create_apt_btrfs_snapshot()
        res = False
        exception = None
        while currentRetry < maxRetries:
            try:
                res = self.cache.commit(fprogress,iprogress)
                logging.debug("cache.commit() returned %s" % res)
            except SystemError as e:
                logging.error("SystemError from cache.commit(): %s" % e)
                exception = e
                # if its a ordering bug we can cleanly revert to
                # the previous release, no packages have been installed
                # yet (LP: #328655, #356781)
                if os.path.exists("/var/run/ubuntu-release-upgrader-apt-exception"):
                    with open("/var/run/ubuntu-release-upgrader-apt-exception") as f:
                        e = f.read()
                    logging.error("found exception: '%s'" % e)
                    # if its a ordering bug we can cleanly revert but we need to write
                    # a marker for the parent process to know its this kind of error
                    pre_configure_errors = [
                        "E:Internal Error, Could not perform immediate configuration",
                        "E:Couldn't configure pre-depend "]
                    for preconf_error in pre_configure_errors:
                        if str(e).startswith(preconf_error):
                            logging.debug("detected preconfigure error, restorting state")
                            self._enableAptCronJob()
                            # FIXME: strings are not good, but we are in string freeze
                            # currently
                            msg = _("Error during commit")
                            msg += "\n'%s'\n" % str(e)
                            msg += _("Restoring original system state")
                            self._view.error(_("Could not install the upgrades"), msg)
                            # abort() exits cleanly
                            self.abort()

                # invoke the frontend now and show a error message
                msg = _("The upgrade has aborted. Your system "
                        "could be in an unusable state. A recovery "
                        "will run now (dpkg --configure -a).")
                if not self._partialUpgrade:
                    if not run_apport():
                        msg += _("\n\nPlease report this bug in a browser at "
                                 "http://bugs.launchpad.net/ubuntu/+source/ubuntu-release-upgrader/+filebug "
                                 "and attach the files in /var/log/dist-upgrade/ "
                                 "to the bug report.\n"
                                 "%s" % e)
                self._view.error(_("Could not install the upgrades"), msg)
                # installing the packages failed, can't be retried
                cmd = ["/usr/bin/dpkg","--configure","-a"]
                if os.environ.get("DEBIAN_FRONTEND") == "noninteractive":
                    cmd.append("--force-confold")
                self._view.getTerminal().call(cmd)
                self._enableAptCronJob()
                return False
            except IOError as e:
                # fetch failed, will be retried
                logging.error("IOError in cache.commit(): '%s'. Retrying (currentTry: %s)" % (e,currentRetry))
                currentRetry += 1
                exception = e
                continue
            except OSError as e:
                logging.exception("cache.commit()")
                # deal gracefully with:
                #  OSError: [Errno 12] Cannot allocate memory
                exception = e
                if e.errno == 12:
                    self._enableAptCronJob()
                    msg = _("Error during commit")
                    msg += "\n'%s'\n" % str(e)
                    msg += _("Restoring original system state")
                    self._view.error(_("Could not install the upgrades"), msg)
                    # abort() exits cleanly
                    self.abort()
            # no exception, so all was fine, we are done
            self._enableAptCronJob()
            return True

        # maximum fetch-retries reached without a successful commit
        logging.error("giving up on fetching after maximum retries")
        self._view.error(_("Could not download the upgrades"),
                         _("The upgrade has aborted. Please check your "\
                           "Internet connection or "\
                           "installation media and try again. "),
                           "%s" % exception)
        # abort here because we want our sources.list back
        self.abort()

    def doPostUpgrade(self):
        get_telemetry().add_stage('POSTUPGRADE')
        # clean up downloaded packages
        archivedir = os.path.dirname(
            apt_pkg.config.find_dir("Dir::Cache::archives"))
        for item in self.fetcher.items:
            if os.path.dirname(os.path.abspath(item.destfile)) == archivedir:
                try:
                    os.unlink(item.destfile)
                except OSError:
                    pass

        # reopen cache
        self.openCache()
        # run the quirks handler that does does like things adding
        # missing groups or similar work arounds, only do it on real
        # upgrades
        self.quirks.run("PostUpgrade")
        # check out what packages are cruft now
        # use self.{foreign,obsolete}_pkgs here and see what changed
        self._view.setStep(Step.CLEANUP)
        self._view.updateStatus(_("Searching for obsolete software"))
        now_obsolete = self.cache._getObsoletesPkgs()
        now_foreign = self.cache._getForeignPkgs(self.origin, self.fromDist, self.toDist)
        logging.debug("Obsolete: %s" % " ".join(sorted(now_obsolete)))
        logging.debug("Foreign: %s" % " ".join(sorted(now_foreign)))
        # now sanity check - if a base meta package is in the obsolete list now, that means
        # that something went wrong (see #335154) badly with the network. this should never happen, but it did happen
        # at least once so we add extra paranoia here
        for pkg in self.config.getlist("Distro","BaseMetaPkgs"):
            if pkg in now_obsolete:
                logging.error("the BaseMetaPkg '%s' is in the obsolete list, something is wrong, ignoring the obsoletes" % pkg)
                now_obsolete = set()
                break
        # check if we actually want obsolete removal
        if not self.config.getWithDefault("Distro","RemoveObsoletes", True):
            logging.debug("Skipping obsolete Removal")
            return True

        # now get the meta-pkg specific obsoletes and purges
        for pkg in self.config.getlist("Distro","MetaPkgs"):
            if pkg in self.cache and self.cache[pkg].is_installed:
                self.forced_obsoletes.extend(self.config.getlist(pkg,"ForcedObsoletes"))
        # now add the obsolete kernels to the forced obsoletes
        self.forced_obsoletes.extend(self.cache.identifyObsoleteKernels())
        logging.debug("forced_obsoletes: %s" % self.forced_obsoletes)

        # mark packages that are now obsolete (and where not obsolete
        # before) to be deleted. make sure to not delete any foreign
        # (that is, not from ubuntu) packages
        if self.useNetwork:
            # we can only do the obsoletes calculation here if we use a
            # network. otherwise after rewriting the sources.list everything
            # that is not on the CD becomes obsolete (not-downloadable)
            remove_candidates = now_obsolete - self.obsolete_pkgs
        else:
            # initial remove candidates when no network is used should
            # be the demotions to make sure we don't leave potential
            # unsupported software
            remove_candidates = set([p.name for p in self.installed_demotions])
        remove_candidates |= set(self.forced_obsoletes)

        # now go for the unused dependencies
        unused_dependencies = self.cache._getUnusedDependencies()
        logging.debug("Unused dependencies: %s" %" ".join(unused_dependencies))
        remove_candidates |= set(unused_dependencies)

        # see if we actually have to do anything here
        if not self.config.getWithDefault("Distro","RemoveObsoletes", True):
            logging.debug("Skipping RemoveObsoletes as stated in the config")
            remove_candidates = set()
        logging.debug("remove_candidates: '%s'" % remove_candidates)
        logging.debug("Start checking for obsolete pkgs")
        progress = self._view.getOpCacheProgress()
        for (i, pkgname) in enumerate(remove_candidates):
            progress.update((i/float(len(remove_candidates)))*100.0)
            if pkgname not in self.foreign_pkgs:
                self._view.processEvents()
                if not self.cache.tryMarkObsoleteForRemoval(pkgname, remove_candidates, self.foreign_pkgs):
                    logging.debug("'%s' scheduled for remove but not safe to remove, skipping", pkgname)
        logging.debug("Finish checking for obsolete pkgs")
        progress.done()

        # get changes
        changes = self.cache.get_changes()
        logging.debug("The following packages are marked for removal: %s" % " ".join([pkg.name for pkg in changes]))
        summary = _("Remove obsolete packages?")
        actions = [_("_Keep"), _("_Remove")]
        # FIXME Add an explanation about what obsolete packages are
        #explanation = _("")
        if (len(changes) > 0 and 
            self._view.confirmChanges(summary, changes, [], 0, actions, False)):
            fprogress = self._view.getAcquireProgress()
            iprogress = self._view.getInstallProgress(self.cache)
            try:
                self.cache.commit(fprogress,iprogress)
            except (SystemError, IOError) as e:
                logging.error("cache.commit() in doPostUpgrade() failed: %s" % e)
                self._view.error(_("Error during commit"),
                                 _("A problem occurred during the clean-up. "
                                   "Please see the below message for more "
                                   "information. "),
                                   "%s" % e)
        # run stuff after cleanup
        self.quirks.run("PostCleanup")
        # run the post upgrade scripts that can do fixup like xorg.conf
        # fixes etc - only do on real upgrades
        if not self._partialUpgrade:
            self.runPostInstallScripts()
        return True

    def runPostInstallScripts(self):
        """ 
        scripts that are run in any case after the distupgrade finished 
        whether or not it was successful
        """
        # now run the post-upgrade fixup scripts (if any)
        for script in self.config.getlist("Distro","PostInstallScripts"):
            if not os.path.exists(script):
                logging.warning("PostInstallScript: '%s' not found" % script)
                continue
            logging.debug("Running PostInstallScript: '%s'" % script)
            try:
                # work around kde tmpfile problem where it eats permissions
                check_and_fix_xbit(script)
                self._view.getTerminal().call([script], hidden=True)
            except Exception as e:
                logging.error("got error from PostInstallScript %s (%s)" % (script, e))

    def abort(self):
        """ abort the upgrade, cleanup (as much as possible) """
        logging.debug("abort called")
        if hasattr(self, "sources"):
            self.sources.restore_backup(self.sources_backup_ext)
        if hasattr(self, "aptcdrom"):
            self.aptcdrom.restore_backup(self.sources_backup_ext)
        # generate a new cache
        self._view.updateStatus(_("Restoring original system state"))
        self._view.abort()
        self.openCache()
        sys.exit(1)

    def _checkDep(self, depstr):
        " check if a given depends can be satisfied "
        for or_group in apt_pkg.parse_depends(depstr):
            logging.debug("checking: '%s' " % or_group)
            for dep in or_group:
                depname = dep[0]
                ver = dep[1]
                oper = dep[2]
                if depname not in self.cache:
                    logging.error("_checkDep: '%s' not in cache" % depname)
                    return False
                inst = self.cache[depname]
                instver = getattr(inst.installed, "version", None)
                if (instver != None and
                    apt_pkg.check_dep(instver,oper,ver) == True):
                    return True
        logging.error("depends '%s' is not satisfied" % depstr)
        return False

    def checkViewDepends(self):
        " check if depends are satisfied "
        logging.debug("checkViewDepends()")
        res = True
        # now check if anything from $foo-updates is required
        depends = self.config.getlist("View","Depends")
        depends.extend(self.config.getlist(self._view.__class__.__name__,
                                           "Depends"))
        for dep in depends:
            logging.debug("depends: '%s'", dep)
            res &= self._checkDep(dep)
            if not res:
                # FIXME: instead of error out, fetch and install it
                #        here
                self._view.error(_("Required depends is not installed"),
                                 _("The required dependency '%s' is not "
                                   "installed. " % dep))
                sys.exit(1)
        return res

    def _verifyBackports(self):
        # run update (but ignore errors in case the countrymirror
        # substitution goes wrong, real errors will be caught later
        # when the cache is searched for the backport packages)
        backportslist = self.config.getlist("PreRequists","Packages")
        i=0
        noCache = apt_pkg.config.find("Acquire::http::No-Cache","false")
        maxRetries = self.config.getint("Network","MaxRetries")
        while i < maxRetries:
            self.doUpdate(showErrors=False)
            self.openCache()
            for pkgname in backportslist:
                if pkgname not in self.cache:
                    logging.error("Can not find backport '%s'" % pkgname)
                    raise NoBackportsFoundException(pkgname)
            if self._allBackportsAuthenticated(backportslist):
                break
            # FIXME: move this to some more generic place
            logging.debug("setting a cache control header to turn off caching temporarily")
            apt_pkg.config.set("Acquire::http::No-Cache","true")
            i += 1
        if i == maxRetries:
            logging.error("pre-requists item is NOT trusted, giving up")
            return False
        apt_pkg.config.set("Acquire::http::No-Cache",noCache)
        return True

    def _allBackportsAuthenticated(self, backportslist):
        # check if the user overwrote the check
        if apt_pkg.config.find_b("APT::Get::AllowUnauthenticated",False) == True:
            logging.warning("skip authentication check because of APT::Get::AllowUnauthenticated==true")
            return True
        try:
            b = self.config.getboolean("Distro","AllowUnauthenticated")
            if b:
                return True
        except NoOptionError:
            pass
        for pkgname in backportslist:
            pkg = self.cache[pkgname]
            if not pkg.candidate:
                return False
            for cand in pkg.candidate.origins:
                if cand.trusted:
                    break
            else:
                return False
        return True

    def isMirror(self, uri):
        """ check if uri is a known mirror """
        # deal with username:password in a netloc
        raw_uri = uri.rstrip("/")
        scheme, netloc, path, query, fragment = urlsplit(raw_uri)
        if "@" in netloc:
            netloc = netloc.split("@")[1]
        # construct new mirror url without the username/pw
        uri = "%s://%s%s" % (scheme, netloc, path)
        for mirror in self.valid_mirrors:
            mirror = mirror.rstrip("/")
            if is_mirror(mirror, uri):
                return True
            # deal with mirrors like
            #    deb http://localhost:9977/security.ubuntu.com/ubuntu intrepid-security main restricted
            # both apt-debtorrent and apt-cacher use this (LP: #365537)
            mirror_host_part = mirror.split("//")[1]
            if uri.endswith(mirror_host_part):
                logging.debug("found apt-cacher/apt-torrent style uri %s" % uri)
                return True
        return False

    def isThirdPartyMirror(self, uri):
        " check if uri is a whitelisted third-party mirror "
        uri = uri.rstrip("/")
        for mirror in self.valid_3p_mirrors:
            mirror = mirror.rstrip("/")
            if is_mirror(mirror, uri):
                return True
        return False

    def _getPreReqMirrorLines(self, dumb=False):
        " get sources.list snippet lines for the current mirror "
        lines = ""
        sources = SourcesList(matcherPath=".")
        for entry in sources.list:
            if entry.invalid or entry.disabled:
                continue
            if (entry.type == "deb" and 
                entry.disabled == False and
                self.isMirror(entry.uri) and
                "main" in entry.comps and
                "%s-updates" % self.fromDist in entry.dist and
                not entry.uri.startswith("http://security.ubuntu.com") and
                not entry.uri.startswith("http://archive.ubuntu.com") ):
                new_line = "deb %s %s-updates main\n" % (entry.uri, self.fromDist)
                if not new_line in lines:
                    lines += new_line
            # FIXME: do we really need "dumb" mode?
            #if (dumb and entry.type == "deb" and
            #    "main" in entry.comps):
            #    lines += "deb %s %s-proposed main\n" % (entry.uri, self.fromDist)
        return lines

    def _addPreRequistsSourcesList(self, template, out, dumb=False):
        " add prerequists based on template into the path outfile "
        # go over the sources.list and try to find a valid mirror
        # that we can use to add the backports dir
        logging.debug("writing prerequists sources.list at: '%s' " % out)
        mirrorlines = self._getPreReqMirrorLines(dumb)
        with open(out, "w") as outfile, open(template) as infile:
            for line in infile:
                template = Template(line)
                outline = template.safe_substitute(mirror=mirrorlines)
                outfile.write(outline)
                logging.debug("adding '%s' prerequists" % outline)
        return True

    def getRequiredBackports(self):
        " download the backports specified in DistUpgrade.cfg "
        logging.debug("getRequiredBackports()")
        res = True
        backportsdir = os.path.join(os.getcwd(),"backports")
        if not os.path.exists(backportsdir):
            os.mkdir(backportsdir)
        backportslist = self.config.getlist("PreRequists","Packages")

        # FIXME: this needs to be ported
        # if we have them on the CD we are fine
        if self.aptcdrom and not self.useNetwork:
            logging.debug("Searching for pre-requists on CDROM")
            p = os.path.join(self.aptcdrom.cdrompath,
                             "dists/stable/main/dist-upgrader/binary-%s/" % apt_pkg.config.find("APT::Architecture"))
            found_pkgs = set()
            for deb in glob.glob(p+"*_*.deb"):
                logging.debug("found pre-req '%s' to '%s'" % (deb, backportsdir))
                found_pkgs.add(os.path.basename(deb).split("_")[0])
            # now check if we got all backports on the CD
            if not set(backportslist).issubset(found_pkgs):
                logging.error("Expected backports: '%s' but got '%s'" % (set(backportslist), found_pkgs))
                return False
            # now install them
            self.cache.release_lock()
            p = subprocess.Popen(
                ["/usr/bin/dpkg", "-i", ] + glob.glob(p+"*_*.deb"),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True)
            res = None
            while res is None:
                res = p.poll()
                self._view.pulseProgress()
                time.sleep(0.02)
            self._view.pulseProgress(finished=True)
            self.cache.get_lock()
            logging.info("installing backport debs exit code '%s'" % res)
            logging.debug("dpkg output:\n%s" % p.communicate()[0])
            if res != 0:
                return False
            # and re-start itself when it done
            return self.setupRequiredBackports()

        # we support PreRequists/SourcesList-$arch sections here too
        # 
        # logic for mirror finding works list this:     
        # - use the mirror template from the config, then: [done]
        # 
        #  - try to find known mirror (isMirror) and prepend it [done]
        #  - archive.ubuntu.com is always a fallback at the end [done]
        # 
        # see if we find backports with that
        # - if not, try guessing based on URI, Trust and Dist   [done]
        #   in existing sources.list (internal mirror with no
        #   outside connection maybe)
        # 
        # make sure to remove file on cancel
        
        # FIXME: use the DistUpgradeFetcherCore logic
        #        in mirror_from_sources_list() here
        #        (and factor that code out into a helper)

        conf_option = "SourcesList"
        if self.config.has_option("PreRequists",conf_option+"-%s" % self.arch):
            conf_option = conf_option + "-%s" % self.arch
        prereq_template = self.config.get("PreRequists",conf_option)
        if not os.path.exists(prereq_template):
            logging.error("sourceslist not found '%s'" % prereq_template)
            return False
        outpath = os.path.join(apt_pkg.config.find_dir("Dir::Etc::sourceparts"), prereq_template)
        outfile = os.path.join(apt_pkg.config.find_dir("Dir::Etc::sourceparts"), prereq_template)
        self._addPreRequistsSourcesList(prereq_template, outfile) 
        try:
            self._verifyBackports()
        except NoBackportsFoundException as e:
            self._addPreRequistsSourcesList(prereq_template, outfile, dumb=True) 
            try:
                self._verifyBackports()
            except NoBackportsFoundException as e:
                logging.warning("no backport for '%s' found" % e)
            return False
        
        # FIXME: sanity check the origin (just for safety)
        for pkgname in backportslist:
            pkg = self.cache[pkgname]
            # look for the right version (backport)
            ver = self.cache._depcache.get_candidate_ver(pkg._pkg)
            if not ver:
                logging.error("No candidate for '%s'" % pkgname)
                os.unlink(outpath)
                return False
            if ver.file_list == None:
                logging.error("No ver.file_list for '%s'" % pkgname)
                os.unlink(outpath)
                return False
            logging.debug("marking '%s' for install" % pkgname)
            # mark install
            pkg.mark_install(auto_inst=False, auto_fix=False)

        # now get it
        res = False
        try:
            res = self.cache.commit(self._view.getAcquireProgress(),
                                    self._view.getInstallProgress(self.cache))
        except IOError as e:
            logging.error("fetch_archives returned '%s'" % e)
            res = False
        except SystemError as e:
            logging.error("install_archives returned '%s'" % e)
            res = False

        if res == False:
            logging.warning("_fetch_archives for backports returned False")

        # all backports done, remove the pre-requirests.list file again
        try:
            os.unlink(outfile)
        except Exception as e:
            logging.error("failed to unlink pre-requists file: '%s'" % e)
        return self.setupRequiredBackports()

    # used by both cdrom/http fetcher
    def setupRequiredBackports(self):
        # ensure that the new release upgrader uses the latest python-apt
        # from the backport path
        os.environ["PYTHONPATH"] = "/usr/lib/release-upgrader-python-apt"
        # copy log so that it gets not overwritten
        logging.shutdown()
        shutil.copy("/var/log/dist-upgrade/main.log",
                    "/var/log/dist-upgrade/main_pre_req.log")
        # now exec self again
        args = sys.argv + ["--have-prerequists"]
        if self.useNetwork:
            args.append("--with-network")
        else:
            args.append("--without-network")
        logging.info("restarting upgrader")
        #print("restarting upgrader to make use of the backports")
        # work around kde being clever and removing the x bit
        check_and_fix_xbit(sys.argv[0])
        os.execve(sys.argv[0],args, os.environ)

    # this is the core
    def fullUpgrade(self):
        # sanity check (check for ubuntu-desktop, brokenCache etc)
        self._view.updateStatus(_("Checking package manager"))
        self._view.setStep(Step.PREPARE)

        if not self.prepare():
            logging.error("self.prepare() failed")
            if os.path.exists("/usr/bin/apport-bug"):
                self._view.error(_("Preparing the upgrade failed"),
                                 _("Preparing the system for the upgrade "
                                   "failed so a bug reporting process is "
                                   "being started."))
                subprocess.Popen(["apport-bug", "ubuntu-release-upgrader-core"])
            else:
                self._view.error(_("Preparing the upgrade failed"),
                                 _("Preparing the system for the upgrade "
                                   "failed. To report a bug install apport "
                                   "and then execute 'apport-bug "
                                   "ubuntu-release-upgrader'."))
                logging.error("Missing apport-bug, bug report not "
                              "autocreated")
            self.abort()

        # mvo: commented out for now, see #54234, this needs to be
        #      refactored to use a arch=any tarball
        if (self.config.has_section("PreRequists") and
            self.options and
            self.options.havePrerequists == False):
            logging.debug("need backports")
            # get backported packages (if needed)
            if not self.getRequiredBackports():
                if os.path.exists("/usr/bin/apport-bug"):
                    self._view.error(_("Getting upgrade prerequisites failed"),
                                     _("The system was unable to get the "
                                       "prerequisites for the upgrade. "
                                       "The upgrade will abort now and restore "
                                       "the original system state.\n"
                                       "\n"
                                       "Additionally, a bug reporting process is "
                                       "being started."))
                    subprocess.Popen(["apport-bug", "ubuntu-release-upgrader-core"])
                else:
                    self._view.error(_("Getting upgrade prerequisites failed"),
                                     _("The system was unable to get the "
                                       "prerequisites for the upgrade. "
                                       "The upgrade will abort now and restore "
                                       "the original system state.\n"
                                       "\n"
                                       "To report a bug install apport and "
                                       "then execute 'apport-bug "
                                       "ubuntu-release-upgrader'."))
                    logging.error("Missing apport-bug, bug report not "
                                  "autocreated")
                self.abort()

        # run a "apt-get update" now, its ok to ignore errors, 
        # because 
        # a) we disable any third party sources later
        # b) we check if we have valid ubuntu sources later
        #    after we rewrite the sources.list and do a 
        #    apt-get update there too
        # because the (unmodified) sources.list of the user
        # may contain bad/unreachable entries we run only
        # with a single retry
        self.doUpdate(showErrors=False, forceRetries=1)
        self.openCache()

        # do pre-upgrade stuff (calc list of obsolete pkgs etc)
        if not self.doPostInitialUpdate():
            self.abort()

        # update sources.list
        self._view.setStep(Step.MODIFY_SOURCES)
        self._view.updateStatus(_("Updating repository information"))
        if not self.updateSourcesList():
            self.abort()

        # add cdrom (if we have one)
        if (self.aptcdrom and
            not self.aptcdrom.add(self.sources_backup_ext)):
            self._view.error(_("Failed to add the cdrom"),
                             _("Sorry, adding the cdrom was not successful."))
            self.abort()

        # then update the package index files
        if not self.doUpdate():
            self.abort()

        # then open the cache (again)
        self._view.updateStatus(_("Checking package manager"))
        # if something fails here (e.g. locking the cache) we need to
        # restore the system state (LP: #1052605)
        self.openCache(restore_sources_list_on_fail=True)

        # re-check server mode because we got new packages (it may happen
        # that the system had no sources.list entries and therefore no
        # desktop file information)
        self.serverMode = self.cache.need_server_mode()
        # do it here as we need to know if we are in server or client mode
        self.quirks.ensure_recommends_are_installed_on_desktops()
        # now check if we still have some key packages available/downloadable
        # after the update - if not something went seriously wrong
        # (this happend e.g. during the intrepid->jaunty upgrade for some
        #  users when de.archive.ubuntu.com was overloaded)
        for pkg in self.config.getlist("Distro","BaseMetaPkgs"):
            if (pkg not in self.cache or
                not self.cache.anyVersionDownloadable(self.cache[pkg])):
                # FIXME: we could offer to add default source entries here,
                #        but we need to be careful to not duplicate them
                #        (i.e. the error here could be something else than
                #        missing sources entries but network errors etc)
                logging.error("No '%s' available/downloadable after sources.list rewrite+update" % pkg)
                if pkg not in self.cache:
                    logging.error("'%s' was not in the cache" % pkg)
                if not self.cache.anyVersionDownloadable(self.cache[pkg]):
                    logging.error("'%s' was not downloadable" % pkg)
                self._view.error(_("Invalid package information"),
                                 _("After updating your package "
                                   "information, the essential package '%s' "
                                   "could not be located. This may be "
                                   "because you have no official mirrors "
                                   "listed in your software sources, or "
                                   "because of excessive load on the mirror "
                                   "you are using. See /etc/apt/sources.list "
                                   "for the current list of configured "
                                   "software sources."
                                   "\n"
                                   "In the case of an overloaded mirror, you "
                                   "may want to try the upgrade again later.")
                                   % pkg)
                if os.path.exists("/usr/bin/apport-bug"):
                    subprocess.Popen(["apport-bug", "ubuntu-release-upgrader-core"])
                else:
                    logging.error("Missing apport-bug, bug report not "
                                  "autocreated")
                self.abort()

        # calc the dist-upgrade and see if the removals are ok/expected
        # do the dist-upgrade
        self._view.updateStatus(_("Calculating the changes"))
        if not self.askDistUpgrade():
            self.abort()
        self._inhibitIdle()

        # fetch the stuff
        self._view.setStep(Step.FETCH)
        self._view.updateStatus(_("Fetching"))
        if not self.doDistUpgradeFetching():
            self._enableAptCronJob()
            self.abort()

        # simulate an upgrade
        self._view.setStep(Step.INSTALL)
        self._view.updateStatus(_("Upgrading"))
        if not self.doDistUpgradeSimulation():
            self._view.error(_("Upgrade infeasible"),
                             _("The upgrade could not be completed, there "
                               "were errors during the upgrade "
                               "process."))
            self.abort()

        # Just upgrade libc6 first
        self.cache.clear()
        libc6_possible = False
        try:
            self.cache["libc6"].mark_install()
            libc6_possible = True
        except SystemError as e:
            if "pkgProblemResolver" in str(e):
                logging.debug("Unable to mark libc6 alone for install.")
                pass

        if libc6_possible:
            self._view.setStep(Step.INSTALL)
            self._view.updateStatus(_("Upgrading"))
            if not self.doDistUpgrade():
                # don't abort here, because it would restore the sources.list
                self._view.information(_("Upgrade incomplete"),
                                       _("The upgrade has partially completed but there "
                                         "were errors during the upgrade "
                                         "process."))
                # do not abort because we are part of the way through the process
                sys.exit(1)

        # Reopen ask above
        self.openCache(restore_sources_list_on_fail=True)
        self.serverMode = self.cache.need_server_mode()
        self.quirks.ensure_recommends_are_installed_on_desktops()

        self._view.updateStatus(_("Calculating the changes"))
        if not self.calcDistUpgrade():
            self.abort()

        # now do the upgrade
        self._view.setStep(Step.INSTALL)
        self._view.updateStatus(_("Upgrading"))
        if not self.doDistUpgrade():
            # run the post install scripts (for stuff like UUID conversion)
            self.runPostInstallScripts()
            # don't abort here, because it would restore the sources.list
            self._view.information(_("Upgrade complete"),
                                   _("The upgrade has completed but there "
                                     "were errors during the upgrade "
                                     "process."))
            # do not abort because we are part of the way through the process
            sys.exit(1)

        # do post-upgrade stuff
        self.doPostUpgrade()

        # comment out cdrom source
        if self.aptcdrom:
            self.aptcdrom.comment_out_cdrom_entry()

        # remove upgrade-available notice
        if os.path.exists("/var/lib/ubuntu-release-upgrader/release-upgrade-available"):
            os.unlink("/var/lib/ubuntu-release-upgrader/release-upgrade-available")

        # done, ask for reboot
        self._view.setStep(Step.REBOOT)
        self._view.updateStatus(_("System upgrade is complete."))            
        get_telemetry().done()
        # FIXME should we look into /var/run/reboot-required here?
        if (not inside_chroot() and
            self._view.confirmRestart()):
            subprocess.Popen("/sbin/reboot")
            sys.exit(0)
        return True
        
    def run(self):
        self._view.processEvents()
        return self.fullUpgrade()
    
    def doPartialUpgrade(self):
        " partial upgrade mode, useful for repairing "
        self._view.setStep(Step.PREPARE)
        self._view.hideStep(Step.MODIFY_SOURCES)
        self._view.hideStep(Step.REBOOT)
        self._partialUpgrade = True
        self.prepare()
        if not self.doPostInitialUpdate():
            return False
        if not self.askDistUpgrade():
            return False
        self._view.setStep(Step.FETCH)
        self._view.updateStatus(_("Fetching"))
        if not self.doDistUpgradeFetching():
            return False
        self._view.setStep(Step.INSTALL)
        self._view.updateStatus(_("Upgrading"))
        if not self.doDistUpgrade():
            self._view.information(_("Upgrade complete"),
                                   _("The upgrade has completed but there "
                                     "were errors during the upgrade "
                                     "process."))
            return False
        if not self.doPostUpgrade():
            self._view.information(_("Upgrade complete"),
                                   _("The upgrade has completed but there "
                                     "were errors during the upgrade "
                                     "process."))
            return False

        if os.path.exists(REBOOT_REQUIRED_FILE):
            # we can not talk to session management here, we run as root
            if self._view.confirmRestart():
                subprocess.Popen("/sbin/reboot")
        else:
            self._view.information(_("Upgrade complete"),
                                   _("The partial upgrade was completed."))
        return True

    def _inhibitIdle(self):
        if os.path.exists("/usr/bin/gnome-session-inhibit"):
            self._uid = os.environ.get('SUDO_UID', '')
            if not self._uid:
                self._uid = os.environ.get('PKEXEC_UID', '')
            if not self._uid:
                logging.debug("failed to determine user upgrading")
                logging.error("failed to inhibit gnome-session idle")
                return
            self._getUserEnv()
            if not self._user_env:
                return
            #seteuid so dbus user session can be accessed
            os.seteuid(int(self._uid))

            logging.debug("inhibit gnome-session idle")
            try:
                xdg_desktop = self._user_env.get("XDG_CURRENT_DESKTOP", "")
                if not xdg_desktop:
                    logging.debug("failed to find XDG_CURRENT_DESKTOP")
                    logging.error("failed to inhibit gnome-session idle")
                    return
                subprocess.Popen(["gnome-session-inhibit", "--inhibit",
                                  "idle", "--inhibit-only"],
                                 env=self._user_env)
                self._view.information(_("Lock screen disabled"),
                                       _("Your lock screen has been "
                                         "disabled and will remain "
                                         "disabled until you reboot."))
            except (OSError, ValueError):
                logging.exception("failed to inhibit gnome-session idle")
            os.seteuid(os.getuid())

    def _getUserEnv(self):
        try:
            pid = subprocess.check_output(["pgrep", "-u", self._uid,
                                           "gnome-session"])
            pid = pid.decode().split('\n')[0]
            with open('/proc/' + pid + '/environ', 'r') as f:
                data = f.read().split('\x00')
            for line in data:
                if len(line):
                    env = line.split('=', 1)
                    self._user_env[env[0]] = env[1]
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                logging.debug("gnome-session not running for user")
            else:
                logging.exception("failed to read user env")



if __name__ == "__main__":
    from .DistUpgradeViewText import DistUpgradeViewText
    logging.basicConfig(level=logging.DEBUG)
    v = DistUpgradeViewText()
    dc = DistUpgradeController(v)
    #dc.openCache()
    dc._disableAptCronJob()
    dc._enableAptCronJob()
    #dc._addRelatimeToFstab()
    #dc.prepare()
    #dc.askDistUpgrade()
    #dc._checkFreeSpace()
    #dc._rewriteFstab()
    #dc._checkAdminGroup()
    #dc._rewriteAptPeriodic(2)
