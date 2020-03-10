# DistUpgradeCache.py
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
import glob
import locale
import os
import re
import logging
import time
import datetime
import threading
import configparser
from subprocess import Popen, PIPE

from .DistUpgradeGettext import gettext as _
from .DistUpgradeGettext import ngettext

from .utils import inside_chroot

class CacheException(Exception):
    pass


class CacheExceptionLockingFailed(CacheException):
    pass


class CacheExceptionDpkgInterrupted(CacheException):
    pass


def estimate_kernel_initrd_size_in_boot():
    """estimate the amount of space used by the kernel and initramfs in /boot,
    including a safety margin
    """
    kernel = 0
    initrd = 0
    kver = os.uname()[2]
    for f in glob.glob("/boot/*%s*" % kver):
        if f == '/boot/initrd.img-%s' % kver:
            initrd += os.path.getsize(f)
        # don't include in the estimate any files that are left behind by
        # an interrupted package manager run
        elif (f.find('initrd.img') >= 0 or f.find('.bak') >= 0
              or f.find('.dpkg-') >= 0):
            continue
        else:
            kernel += os.path.getsize(f)
    if kernel == 0:
        logging.warning(
            "estimate_kernel_initrd_size_in_boot() returned '0' for kernel?")
        kernel = 28*1024*1024
    if initrd == 0:
        logging.warning(
            "estimate_kernel_initrd_size_in_boot() returned '0' for initrd?")
        initrd = 45*1024*1024
    # add small safety buffer
    kernel += 1*1024*1024
    # safety buffer as a percentage of the existing initrd's size
    initrd_buffer = 1*1024*1024
    if initrd * 0.05 > initrd_buffer:
        initrd_buffer = initrd * 0.05
    initrd += initrd_buffer
    return kernel,initrd
KERNEL_SIZE, INITRD_SIZE = estimate_kernel_initrd_size_in_boot()


class FreeSpaceRequired(object):
    """ FreeSpaceRequired object:

    This exposes:
    - the total size required (size_total)
    - the dir that requires the space (dir)
    - the additional space that is needed (size_needed)
    """
    def __init__(self, size_total, dir, size_needed):
        self.size_total = size_total
        self.dir = dir
        self.size_needed = size_needed
    def __str__(self):
        return "FreeSpaceRequired Object: Dir: %s size_total: %s size_needed: %s" % (self.dir, self.size_total, self.size_needed)


class NotEnoughFreeSpaceError(CacheException):
    """
    Exception if there is not enough free space for this operation

    """
    def __init__(self, free_space_required_list):
        self.free_space_required_list = free_space_required_list


class MyCache(apt.Cache):
    ReInstReq = 1
    HoldReInstReq = 3

    # init
    def __init__(self, config, view, quirks, progress=None, lock=True):
        self.to_install = []
        self.to_remove = []
        self.view = view
        self.quirks = quirks
        self.lock = False
        self.partialUpgrade = False
        self.config = config
        self.metapkgs = self.config.getlist("Distro", "MetaPkgs")
        # acquire lock
        self._listsLock = -1
        if lock:
            try:
                apt_pkg.pkgsystem_lock()
                self.lock_lists_dir()
                self.lock = True
            except SystemError as e:
                # checking for this is ok, its not translatable
                if "dpkg --configure -a" in str(e):
                    raise CacheExceptionDpkgInterrupted(e)
                raise CacheExceptionLockingFailed(e)
        # Do not create the cache until we know it is not locked
        apt.Cache.__init__(self, progress)
        # a list of regexp that are not allowed to be removed
        self.removal_blacklist = config.getListFromFile("Distro", "RemovalBlacklistFile")
        self.uname = Popen(["uname", "-r"], stdout=PIPE,
                           universal_newlines=True).communicate()[0].strip()
        self._initAptLog()
        # from hardy on we use recommends by default, so for the
        # transition to the new dist we need to enable them now
        if (config.get("Sources", "From") == "hardy" and
            not "RELEASE_UPGRADE_NO_RECOMMENDS" in os.environ):
            apt_pkg.config.set("APT::Install-Recommends", "true")


        apt_pkg.config.set("APT::AutoRemove::SuggestsImportant", "false")

    def _apply_dselect_upgrade(self):
        """ honor the dselect install state """
        for pkg in self:
            if pkg.is_installed:
                continue
            if pkg._pkg.selected_state == apt_pkg.SELSTATE_INSTALL:
                # upgrade() will take care of this
                pkg.mark_install(auto_inst=False, auto_fix=False)

    @property
    def req_reinstall_pkgs(self):
        " return the packages not downloadable packages in reqreinst state "
        reqreinst = set()
        for pkg in self:
            if ((not pkg.candidate or not pkg.candidate.downloadable)
                and
                (pkg._pkg.inst_state == self.ReInstReq or
                 pkg._pkg.inst_state == self.HoldReInstReq)):
                reqreinst.add(pkg.name)
        return reqreinst

    def fix_req_reinst(self, view):
        " check for reqreinst state and offer to fix it "
        reqreinst = self.req_reinstall_pkgs
        if len(reqreinst) > 0:
            header = ngettext("Remove package in bad state",
                              "Remove packages in bad state",
                              len(reqreinst))
            summary = ngettext("The package '%s' is in an inconsistent "
                               "state and needs to be reinstalled, but "
                               "no archive can be found for it. "
                               "Do you want to remove this package "
                               "now to continue?",
                               "The packages '%s' are in an inconsistent "
                               "state and need to be reinstalled, but "
                               "no archives can be found for them. Do you "
                               "want to remove these packages now to "
                               "continue?",
                               len(reqreinst)) % ", ".join(reqreinst)
            if view.askYesNoQuestion(header, summary):
                self.release_lock()
                cmd = ["/usr/bin/dpkg", "--remove", "--force-remove-reinstreq"] + list(reqreinst)
                view.getTerminal().call(cmd)
                self.get_lock()
                return True
        return False

    # logging stuff
    def _initAptLog(self):
        " init logging, create log file"
        logdir = self.config.getWithDefault("Files", "LogDir",
                                            "/var/log/dist-upgrade")
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        apt_pkg.config.set("Dir::Log", logdir)
        apt_pkg.config.set("Dir::Log::Terminal", "apt-term.log")
        self.logfd = os.open(os.path.join(logdir, "apt.log"),
                             os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o644)
        now = datetime.datetime.now()
        header = "Log time: %s\n" % now
        os.write(self.logfd, header.encode("utf-8"))

        # turn on debugging in the cache
        apt_pkg.config.set("Debug::pkgProblemResolver", "true")
        apt_pkg.config.set("Debug::pkgDepCache::Marker", "true")
        apt_pkg.config.set("Debug::pkgDepCache::AutoInstall", "true")
    def _startAptResolverLog(self):
        if hasattr(self, "old_stdout"):
            os.close(self.old_stdout)
            os.close(self.old_stderr)
        self.old_stdout = os.dup(1)
        self.old_stderr = os.dup(2)
        os.dup2(self.logfd, 1)
        os.dup2(self.logfd, 2)
    def _stopAptResolverLog(self):
        os.fsync(1)
        os.fsync(2)
        os.dup2(self.old_stdout, 1)
        os.dup2(self.old_stderr, 2)
    # use this decorator instead of the _start/_stop stuff directly
    # FIXME: this should probably be a decorator class where all
    #        logging is moved into?
    def withResolverLog(f):
        " decorator to ensure that the apt output is logged "
        def wrapper(*args, **kwargs):
            args[0]._startAptResolverLog()
            res = f(*args, **kwargs)
            args[0]._stopAptResolverLog()
            return res
        return wrapper

    # properties
    @property
    def required_download(self):
        """ get the size of the packages that are required to download """
        pm = apt_pkg.PackageManager(self._depcache)
        fetcher = apt_pkg.Acquire()
        pm.get_archives(fetcher, self._list, self._records)
        return fetcher.fetch_needed
    @property
    def additional_required_space(self):
        """ get the size of the additional required space on the fs """
        return self._depcache.usr_size
    @property
    def is_broken(self):
        """ is the cache broken """
        return self._depcache.broken_count > 0

    # methods
    def lock_lists_dir(self):
        name = apt_pkg.config.find_dir("Dir::State::Lists") + "lock"
        self._listsLock = apt_pkg.get_lock(name)
        if self._listsLock < 0:
            e = "Can not lock '%s' " % name
            raise CacheExceptionLockingFailed(e)
    def unlock_lists_dir(self):
        if self._listsLock > 0:
            os.close(self._listsLock)
            self._listsLock = -1
    def update(self, fprogress=None):
        """
        our own update implementation is required because we keep the lists
        dir lock
        """
        self.unlock_lists_dir()
        res = apt.Cache.update(self, fprogress)
        self.lock_lists_dir()
        if fprogress and fprogress.release_file_download_error:
            # FIXME: not ideal error message, but we just reuse a
            #        existing one here to avoid a new string
            raise IOError(_("The server may be overloaded"))
        if res == False:
            raise IOError("apt.cache.update() returned False, but did not raise exception?!?")

    def commit(self, fprogress, iprogress):
        logging.info("cache.commit()")
        if self.lock:
            self.release_lock()
        apt.Cache.commit(self, fprogress, iprogress)

    def release_lock(self, pkgSystemOnly=True):
        if self.lock:
            try:
                apt_pkg.pkgsystem_unlock()
                self.lock = False
            except SystemError as e:
                logging.debug("failed to SystemUnLock() (%s) " % e)

    def get_lock(self, pkgSystemOnly=True):
        if not self.lock:
            try:
                apt_pkg.pkgsystem_lock()
                self.lock = True
            except SystemError as e:
                logging.debug("failed to SystemLock() (%s) " % e)

    def downloadable(self, pkg, useCandidate=True):
        " check if the given pkg can be downloaded "
        if useCandidate:
            ver = self._depcache.get_candidate_ver(pkg._pkg)
        else:
            ver = pkg._pkg.current_ver
        if ver == None:
            logging.warning("no version information for '%s' (useCandidate=%s)" % (pkg.name, useCandidate))
            return False
        return ver.downloadable

    def pkg_auto_removable(self, pkg):
        """ check if the pkg is auto-removable """
        return (pkg.is_installed and
                self._depcache.is_garbage(pkg._pkg))

    def fix_broken(self):
        """ try to fix broken dependencies on the system, may throw
            SystemError when it can't"""
        return self._depcache.fix_broken()

    def create_snapshot(self):
        """ create a snapshot of the current changes """
        self.to_install = []
        self.to_remove = []
        for pkg in self.get_changes():
            if pkg.marked_install or pkg.marked_upgrade:
                self.to_install.append(pkg.name)
            if pkg.marked_delete:
                self.to_remove.append(pkg.name)

    def clear(self):
        self._depcache.init()

    def restore_snapshot(self):
        """ restore a snapshot """
        actiongroup = apt_pkg.ActionGroup(self._depcache)
        # just make pyflakes shut up, later we need to use
        # with self.actiongroup():
        actiongroup
        self.clear()
        for name in self.to_remove:
            pkg = self[name]
            pkg.mark_delete()
        for name in self.to_install:
            pkg = self[name]
            pkg.mark_install(auto_fix=False, auto_inst=False)

    def need_server_mode(self):
        """
        This checks if we run on a desktop or a server install.

        A server install has more freedoms, for a desktop install
        we force a desktop meta package to be install on the upgrade.

        We look for a installed desktop meta pkg and for key
        dependencies, if none of those are installed we assume
        server mode
        """
        #logging.debug("need_server_mode() run")
        # check for the MetaPkgs (e.g. ubuntu-desktop)
        metapkgs = self.config.getlist("Distro", "MetaPkgs")
        for key in metapkgs:
            # if it is installed we are done
            if key in self and self[key].is_installed:
                logging.debug("need_server_mode(): run in 'desktop' mode, (because of pkg '%s')" % key)
                return False
            # if it is not installed, but its key depends are installed
            # we are done too (we auto-select the package later)
            deps_found = True
            for pkg in self.config.getlist(key, "KeyDependencies"):
                deps_found &= pkg in self and self[pkg].is_installed
            if deps_found:
                logging.debug("need_server_mode(): run in 'desktop' mode, (because of key deps for '%s')" % key)
                return False
        logging.debug("need_server_mode(): can not find a desktop meta package or key deps, running in server mode")
        return True

    def sanity_check(self, view):
        """ check if the cache is ok and if the required metapkgs
            are installed
        """
        if self.is_broken:
            try:
                logging.debug("Have broken pkgs, trying to fix them")
                self.fix_broken()
            except SystemError:
                view.error(_("Broken packages"),
                                 _("Your system contains broken packages "
                                   "that couldn't be fixed with this "
                                   "software. "
                                   "Please fix them first using synaptic or "
                                   "apt-get before proceeding."))
                return False
        return True

    def mark_install(self, pkg, reason=""):
        logging.debug("Installing '%s' (%s)" % (pkg, reason))
        if pkg in self:
            self[pkg].mark_install()
            if not (self[pkg].marked_install or self[pkg].marked_upgrade):
                logging.error("Installing/upgrading '%s' failed" % pkg)
                #raise SystemError("Installing '%s' failed" % pkg)
                return False
        return True

    def mark_upgrade(self, pkg, reason=""):
        logging.debug("Upgrading '%s' (%s)" % (pkg, reason))
        if pkg in self and self[pkg].is_installed:
            self[pkg].mark_upgrade()
            if not self[pkg].marked_upgrade:
                logging.error("Upgrading '%s' failed" % pkg)
                return False
        return True

    def mark_remove(self, pkg, reason=""):
        logging.debug("Removing '%s' (%s)" % (pkg, reason))
        if pkg in self:
            self[pkg].mark_delete()

    def mark_purge(self, pkg, reason=""):
        logging.debug("Purging '%s' (%s)" % (pkg, reason))
        if pkg in self:
            self._depcache.mark_delete(self[pkg]._pkg, True)

    def _keep_installed(self, pkgname, reason):
        if (pkgname in self
            and self[pkgname].is_installed
            and self[pkgname].marked_delete):
            self.mark_install(pkgname, reason)

    def keep_installed_rule(self):
        """ run after the dist-upgrade to ensure that certain
            packages are kept installed """
        # first the global list
        for pkgname in self.config.getlist("Distro", "KeepInstalledPkgs"):
            self._keep_installed(pkgname, "Distro KeepInstalledPkgs rule")
        # the the per-metapkg rules
        for key in self.metapkgs:
            if key in self and (self[key].is_installed or
                                self[key].marked_install):
                for pkgname in self.config.getlist(key, "KeepInstalledPkgs"):
                    self._keep_installed(pkgname, "%s KeepInstalledPkgs rule" % key)

        # only enforce section if we have a network. Otherwise we run
        # into CD upgrade issues for installed language packs etc
        if self.config.get("Options", "withNetwork") == "True":
            logging.debug("Running KeepInstalledSection rules")
            # now the KeepInstalledSection code
            for section in self.config.getlist("Distro", "KeepInstalledSection"):
                for pkg in self:
                    if (pkg.candidate and pkg.candidate.downloadable
                        and pkg.marked_delete and pkg.section == section):
                        self._keep_installed(pkg.name, "Distro KeepInstalledSection rule: %s" % section)
            for key in self.metapkgs:
                if key in self and (self[key].is_installed or
                                    self[key].marked_install):
                    for section in self.config.getlist(key, "KeepInstalledSection"):
                        for pkg in self:
                            if (pkg.candidate and pkg.candidate.downloadable
                                and pkg.marked_delete and
                                pkg.section == section):
                                self._keep_installed(pkg.name, "%s KeepInstalledSection rule: %s" % (key, section))


    def post_upgrade_rule(self):
        " run after the upgrade was done in the cache "
        for (rule, action) in [("Install", self.mark_install),
                               ("Upgrade", self.mark_upgrade),
                               ("Remove", self.mark_remove),
                               ("Purge", self.mark_purge)]:
            # first the global list
            for pkg in self.config.getlist("Distro", "PostUpgrade%s" % rule):
                action(pkg, "Distro PostUpgrade%s rule" % rule)
            for key in self.metapkgs:
                if key in self and (self[key].is_installed or
                                    self[key].marked_install):
                    for pkg in self.config.getlist(key, "PostUpgrade%s" % rule):
                        action(pkg, "%s PostUpgrade%s rule" % (key, rule))
        # run the quirks handlers
        if not self.partialUpgrade:
            self.quirks.run("PostDistUpgradeCache")

    def identifyObsoleteKernels(self):
        # we have a funny policy that we remove security updates
        # for the kernel from the archive again when a new ABI
        # version hits the archive. this means that we have
        # e.g.
        # linux-image-2.6.24-15-generic
        # is obsolete when
        # linux-image-2.6.24-19-generic
        # is available
        # ...
        # This code tries to identify the kernels that can be removed
        logging.debug("identifyObsoleteKernels()")
        obsolete_kernels = set()
        version = self.config.get("KernelRemoval", "Version")
        basenames = self.config.getlist("KernelRemoval", "BaseNames")
        types = self.config.getlist("KernelRemoval", "Types")
        for pkg in self:
            for base in basenames:
                basename = "%s-%s-" % (base, version)
                for type in types:
                    if (pkg.name.startswith(basename) and
                        pkg.name.endswith(type) and
                        pkg.is_installed):
                        if (pkg.name == "%s-%s" % (base, self.uname)):
                            logging.debug("skipping running kernel %s" % pkg.name)
                            continue
                        logging.debug("removing obsolete kernel '%s'" % pkg.name)
                        obsolete_kernels.add(pkg.name)
        logging.debug("identifyObsoleteKernels found '%s'" % obsolete_kernels)
        return obsolete_kernels

    def checkForNvidia(self):
        """
        this checks for nvidia hardware and checks what driver is needed
        """
        logging.debug("nvidiaUpdate()")
        # if the free drivers would give us a equally hard time, we would
        # never be able to release
        try:
            from NvidiaDetector.nvidiadetector import NvidiaDetection
        except (ImportError, SyntaxError) as e:
            # SyntaxError is temporary until the port of NvidiaDetector to
            # Python 3 is in the archive.
            logging.error("NvidiaDetector can not be imported %s" % e)
            return False
        try:
            # get new detection module and use the modalises files
            # from within the release-upgrader
            nv = NvidiaDetection(obsolete="./ubuntu-drivers-obsolete.pkgs")
            #nv = NvidiaDetection()
            # check if a binary driver is installed now
            for oldDriver in nv.oldPackages:
                if oldDriver in self and self[oldDriver].is_installed:
                    self.mark_remove(oldDriver, "old nvidia driver")
                    break
            else:
                logging.info("no old nvidia driver installed, installing no new")
                return False
            # check which one to use
            driver = nv.selectDriver()
            logging.debug("nv.selectDriver() returned '%s'" % driver)
            if not driver in self:
                logging.warning("no '%s' found" % driver)
                return False
            if not (self[driver].marked_install or self[driver].marked_upgrade):
                self[driver].mark_install()
                logging.info("installing %s as suggested by NvidiaDetector" % driver)
                return True
        except Exception as e:
            logging.error("NvidiaDetection returned a error: %s" % e)
        return False


    def _has_kernel_headers_installed(self):
        for pkg in self:
            if (pkg.name.startswith("linux-headers-") and
                pkg.is_installed):
                return True
        return False

    def checkForKernel(self):
        """ check for the running kernel and try to ensure that we have
            an updated version
        """
        logging.debug("Kernel uname: '%s' " % self.uname)
        try:
            (version, build, flavour) = self.uname.split("-")
        except Exception as e:
            logging.warning("Can't parse kernel uname: '%s' (self compiled?)" % e)
            return False
        # now check if we have a SMP system
        dmesg = Popen(["dmesg"], stdout=PIPE).communicate()[0]
        if b"WARNING: NR_CPUS limit" in dmesg:
            logging.debug("UP kernel on SMP system!?!")
        return True

    def checkPriority(self):
        # tuple of priorities we require to be installed
        need = ('required', )
        # stuff that its ok not to have
        removeEssentialOk = self.config.getlist("Distro", "RemoveEssentialOk")
        # check now
        for pkg in self:
            # WORKAROUND bug on the CD/python-apt #253255
            ver = pkg._pcache._depcache.get_candidate_ver(pkg._pkg)
            if ver and ver.priority == 0:
                logging.error("Package %s has no priority set" % pkg.name)
                continue
            if (pkg.candidate and pkg.candidate.downloadable and
                not (pkg.is_installed or pkg.marked_install) and
                not pkg.name in removeEssentialOk and
                # ignore multiarch priority required packages
                not ":" in pkg.name and
                pkg.candidate.priority in need):
                self.mark_install(pkg.name, "priority in required set '%s' but not scheduled for install" % need)

    # FIXME: make this a decorator (just like the withResolverLog())
    def updateGUI(self, view, lock):
        i = 0
        while lock.locked():
            if i % 15 == 0:
                view.pulseProgress()
            view.processEvents()
            time.sleep(0.02)
            i += 1
        view.pulseProgress(finished=True)
        view.processEvents()

    @withResolverLog
    def distUpgrade(self, view, serverMode, partialUpgrade):
        # keep the GUI alive
        lock = threading.Lock()
        lock.acquire()
        t = threading.Thread(target=self.updateGUI, args=(self.view, lock,))
        t.start()
        try:
            # mvo: disabled as it casues to many errornous installs
            #self._apply_dselect_upgrade()

            # upgrade (and make sure this way that the cache is ok)
            self.upgrade(True)

            # check that everything in priority required is installed
            self.checkPriority()

            # see if our KeepInstalled rules are honored
            self.keep_installed_rule()

            # check if we got a new kernel (if we are not inside a
            # chroot)
            if inside_chroot():
                logging.warning("skipping kernel checks because we run inside a chroot")
            else:
                self.checkForKernel()

            # check for nvidia stuff
            self.checkForNvidia()

            # and if we have some special rules
            self.post_upgrade_rule()

            # install missing meta-packages (if not in server upgrade mode)
            self._keepBaseMetaPkgsInstalled(view)
            if not serverMode:
                # if this fails, a system error is raised
                self._installMetaPkgs(view)

            # see if it all makes sense, if not this function raises
            self._verifyChanges()

        except SystemError as e:
            # this should go into a finally: line, see below for the
            # rationale why it doesn't
            lock.release()
            t.join()
            # the most likely problem is the 3rd party pkgs so don't address
            # foreignPkgs and devRelease being True
            details =  _("An unresolvable problem occurred while "
                         "calculating the upgrade.\n\n ")
            if self.config.get("Options", "foreignPkgs") == "True":
                details += _("This was likely caused by:\n"
                             " * Unofficial software packages not provided by Ubuntu\n"
                             "Please use the tool 'ppa-purge' from the ppa-purge \n"
                             "package to remove software from a Launchpad PPA and \n"
                             "try the upgrade again.\n"
                             "\n")
            elif self.config.get("Options", "foreignPkgs") == "False" and \
                self.config.get("Options", "devRelease") == "True":
                details +=  _("This was caused by:\n"
                              " * Upgrading to a pre-release version of Ubuntu\n"
                              "This is most likely a transient problem, \n"
                              "please try again later.\n")
            # we never have partialUpgrades (including removes) on a stable system
            # with only ubuntu sources so we do not recommend reporting a bug
            if partialUpgrade:
                details += _("This is most likely a transient problem, "
                             "please try again later.")
            else:
                details += _("If none of this applies, then please report this bug using "
                             "the command 'ubuntu-bug ubuntu-release-upgrader-core' in a terminal.")
                details += _("If you want to investigate this yourself the log files in "
                             "'/var/log/dist-upgrade' will contain details about the upgrade. "
                             "Specifically, look at 'main.log' and 'apt.log'.")
            # make the error text available again on stdout for the
            # text frontend
            self._stopAptResolverLog()
            view.error(_("Could not calculate the upgrade"), details)
            # may contain utf-8 (LP: #1310053)
            error_msg = str(e)
            logging.error("Dist-upgrade failed: '%s'", error_msg)
            # start the resolver log again because this is run with
            # the withResolverLog decorator
            self._startAptResolverLog()
            return False
        # would be nice to be able to use finally: here, but we need
        # to run on python2.4 too
        #finally:
        # wait for the gui-update thread to exit
        lock.release()
        t.join()

        # check the trust of the packages that are going to change
        untrusted = []
        downgrade = []
        for pkg in self.get_changes():
            if pkg.marked_delete:
                continue
            # special case because of a bug in pkg.candidate.origins
            if pkg.marked_downgrade:
                downgrade.append(pkg.name)
                for ver in pkg._pkg.version_list:
                    # version is lower than installed one
                    if apt_pkg.version_compare(
                        ver.ver_str, pkg.installed.version) < 0:
                        for (verFileIter, index) in ver.file_list:
                            indexfile = pkg._pcache._list.find_index(verFileIter)
                            if indexfile and not indexfile.is_trusted:
                                untrusted.append(pkg.name)
                                break
                continue
            origins = pkg.candidate.origins
            trusted = False
            for origin in origins:
                #print(origin)
                trusted |= origin.trusted
            if not trusted:
                untrusted.append(pkg.name)
        # check if the user overwrote the unauthenticated warning
        try:
            b = self.config.getboolean("Distro", "AllowUnauthenticated")
            if b:
                logging.warning("AllowUnauthenticated set!")
                return True
        except configparser.NoOptionError as e:
            pass
        if len(downgrade) > 0:
            downgrade.sort()
            logging.error("Packages to downgrade found: '%s'" %
                          " ".join(downgrade))
        if len(untrusted) > 0:
            untrusted.sort()
            logging.error("Unauthenticated packages found: '%s'" %
                          " ".join(untrusted))
            # FIXME: maybe ask a question here? instead of failing?
            self._stopAptResolverLog()
            view.error(_("Error authenticating some packages"),
                       _("It was not possible to authenticate some "
                         "packages. This may be a transient network problem. "
                         "You may want to try again later. See below for a "
                         "list of unauthenticated packages."),
                       "\n".join(untrusted))
            # start the resolver log again because this is run with
            # the withResolverLog decorator
            self._startAptResolverLog()
            return False
        return True

    def _verifyChanges(self):
        """ this function tests if the current changes don't violate
            our constrains (blacklisted removals etc)
        """
        main_arch = apt_pkg.config.find("APT::Architecture")
        removeEssentialOk = self.config.getlist("Distro", "RemoveEssentialOk")
        # check changes
        for pkg in self.get_changes():
            if pkg.marked_delete and self._inRemovalBlacklist(pkg.name):
                logging.debug("The package '%s' is marked for removal but it's in the removal blacklist", pkg.name)
                raise SystemError(_("The package '%s' is marked for removal but it is in the removal blacklist.") % pkg.name)
            if pkg.marked_delete and (
                    pkg._pkg.essential == True and
                    pkg.installed.architecture in (main_arch, "all") and
                    not pkg.name in removeEssentialOk):
                logging.debug("The package '%s' is marked for removal but it's an ESSENTIAL package", pkg.name)
                raise SystemError(_("The essential package '%s' is marked for removal.") % pkg.name)
        # check bad-versions blacklist
        badVersions = self.config.getlist("Distro", "BadVersions")
        for bv in badVersions:
            (pkgname, ver) = bv.split("_")
            if (pkgname in self and self[pkgname].candidate and
                self[pkgname].candidate.version == ver and
                (self[pkgname].marked_install or
                 self[pkgname].marked_upgrade)):
                raise SystemError(_("Trying to install blacklisted version '%s'") % bv)
        return True

    def _lookupPkgRecord(self, pkg):
        """
        helper to make sure that the pkg._records is pointing to the right
        location - needed because python-apt 0.7.9 dropped the python-apt
        version but we can not yet use the new version because on upgrade
        the old version is still installed
        """
        ver = pkg._pcache._depcache.get_candidate_ver(pkg._pkg)
        if ver is None:
            print("No candidate ver: ", pkg.name)
            return False
        if ver.file_list is None:
            print("No file_list for: %s " % self._pkg.name())
            return False
        f, index = ver.file_list.pop(0)
        pkg._pcache._records.lookup((f, index))
        return True

    @property
    def installedTasks(self):
        tasks = {}
        installed_tasks = set()
        for pkg in self:
            if not self._lookupPkgRecord(pkg):
                logging.debug("no PkgRecord found for '%s', skipping " % pkg.name)
                continue
            for line in pkg._pcache._records.record.split("\n"):
                if line.startswith("Task:"):
                    for task in (line[len("Task:"):]).split(","):
                        task = task.strip()
                        if task not in tasks:
                            tasks[task] = set()
                        tasks[task].add(pkg.name)
        for task in tasks:
            installed = True
            for pkgname in tasks[task]:
                if not self[pkgname].is_installed:
                    installed = False
                    break
            if installed:
                installed_tasks.add(task)
        return installed_tasks

    def installTasks(self, tasks):
        logging.debug("running installTasks")
        for pkg in self:
            if pkg.marked_install or pkg.is_installed:
                continue
            self._lookupPkgRecord(pkg)
            if not (hasattr(pkg._pcache._records, "record") and pkg._pcache._records.record):
                logging.warning("can not find Record for '%s'" % pkg.name)
                continue
            for line in pkg._pcache._records.record.split("\n"):
                if line.startswith("Task:"):
                    for task in (line[len("Task:"):]).split(","):
                        task = task.strip()
                        if task in tasks:
                            pkg.mark_install()
        return True

    def _keepBaseMetaPkgsInstalled(self, view):
        for pkg in self.config.getlist("Distro", "BaseMetaPkgs"):
            self._keep_installed(pkg, "base meta package keep installed rule")

    def _installMetaPkgs(self, view):

        def metaPkgInstalled():
            """
            internal helper that checks if at least one meta-pkg is
            installed or marked install
            """
            for key in metapkgs:
                if key in self:
                    pkg = self[key]
                    if pkg.is_installed and pkg.marked_delete:
                        logging.debug("metapkg '%s' installed but marked_delete" % pkg.name)
                    if ((pkg.is_installed and not pkg.marked_delete)
                        or self[key].marked_install):
                        return True
            return False

        # now check for ubuntu-desktop, kubuntu-desktop, edubuntu-desktop
        metapkgs = self.config.getlist("Distro", "MetaPkgs")

        # we never go without ubuntu-base
        for pkg in self.config.getlist("Distro", "BaseMetaPkgs"):
            self[pkg].mark_install()

        # every meta-pkg that is installed currently, will be marked
        # install (that result in a upgrade and removes a mark_delete)
        for key in metapkgs:
            try:
                if (key in self and
                    self[key].is_installed and
                    self[key].is_upgradable):
                    logging.debug("Marking '%s' for upgrade" % key)
                    self[key].mark_upgrade()
            except SystemError as e:
                # warn here, but don't fail, its possible that meta-packages
                # conflict (like ubuntu-desktop vs xubuntu-desktop) LP: #775411
                logging.warning("Can't mark '%s' for upgrade (%s)" % (key, e))

        # check if we have a meta-pkg, if not, try to guess which one to pick
        if not metaPkgInstalled():
            logging.debug("none of the '%s' meta-pkgs installed" % metapkgs)
            for key in metapkgs:
                deps_found = True
                for pkg in self.config.getlist(key, "KeyDependencies"):
                    deps_found &= pkg in self and self[pkg].is_installed
                if deps_found:
                    logging.debug("guessing '%s' as missing meta-pkg" % key)
                    try:
                        self[key].mark_install()
                    except (SystemError, KeyError) as e:
                        logging.error("failed to mark '%s' for install (%s)" %
                                      (key, e))
                        view.error(_("Can't install '%s'") % key,
                                   _("It was impossible to install a "
                                     "required package. Please report "
                                     "this as a bug using "
                                     "'ubuntu-bug ubuntu-release-upgrader-core' in "
                                     "a terminal."))
                        return False
                    logging.debug("marked_install: '%s' -> '%s'" % (key, self[key].marked_install))
                    break
        # check if we actually found one
        if not metaPkgInstalled():
            meta_pkgs = ', '.join(metapkgs[0:-1])
            view.error(_("Can't guess meta-package"),
                       _("Your system does not contain a "
                         "%s or %s package and it was not "
                         "possible to detect which version of "
                         "Ubuntu you are running.\n "
                         "Please install one of the packages "
                         "above first using synaptic or "
                         "apt-get before proceeding.") %
                        (meta_pkgs, metapkgs[-1]))
            return False
        return True

    def _inRemovalBlacklist(self, pkgname):
        for expr in self.removal_blacklist:
            if re.compile(expr).match(pkgname):
                logging.debug("blacklist expr '%s' matches '%s'" % (expr, pkgname))
                return True
        return False

    @withResolverLog
    def tryMarkObsoleteForRemoval(self, pkgname, remove_candidates, foreign_pkgs):
        #logging.debug("tryMarkObsoleteForRemoval(): %s" % pkgname)
        # sanity check, first see if it looks like a running kernel pkg
        if pkgname.endswith(self.uname):
            logging.debug("skipping running kernel pkg '%s'" % pkgname)
            return False
        if self._inRemovalBlacklist(pkgname):
            logging.debug("skipping '%s' (in removalBlacklist)" % pkgname)
            return False
        # ensure we honor KeepInstalledSection here as well
        for section in self.config.getlist("Distro", "KeepInstalledSection"):
            if pkgname in self and self[pkgname].section == section:
                logging.debug("skipping '%s' (in KeepInstalledSection)" % pkgname)
                return False
        # if we don't have the package anyway, we are fine (this can
        # happen when forced_obsoletes are specified in the config file)
        if pkgname not in self:
            #logging.debug("package '%s' not in cache" % pkgname)
            return True
        # check if we want to purge
        try:
            purge = self.config.getboolean("Distro", "PurgeObsoletes")
        except configparser.NoOptionError as e:
            purge = False

        # this is a delete candidate, only actually delete,
        # if it dosn't remove other packages depending on it
        # that are not obsolete as well
        actiongroup = apt_pkg.ActionGroup(self._depcache)
        # just make pyflakes shut up, later we should use
        # with self.actiongroup():
        actiongroup
        self.create_snapshot()
        try:
            self[pkgname].mark_delete(purge=purge)
            self.view.processEvents()
            #logging.debug("marking '%s' for removal" % pkgname)
            for pkg in self.get_changes():
                if (pkg.name not in remove_candidates or
                      pkg.name in foreign_pkgs or
                      self._inRemovalBlacklist(pkg.name)):
                    logging.debug("package '%s' has unwanted removals, skipping" % pkgname)
                    self.restore_snapshot()
                    return False
        except (SystemError, KeyError) as e:
            logging.warning("_tryMarkObsoleteForRemoval failed for '%s' (%s: %s)" % (pkgname, repr(e), e))
            self.restore_snapshot()
            return False
        return True

    def _getObsoletesPkgs(self):
        " get all package names that are not downloadable "
        obsolete_pkgs = set()
        for pkg in self:
            if pkg.is_installed:
                # check if any version is downloadable. we need to check
                # for older ones too, because there might be
                # cases where e.g. firefox in gutsy-updates is newer
                # than hardy
                if not self.anyVersionDownloadable(pkg):
                    obsolete_pkgs.add(pkg.name)
        return obsolete_pkgs

    def anyVersionDownloadable(self, pkg):
        " helper that checks if any of the version of pkg is downloadable "
        for ver in pkg._pkg.version_list:
            if ver.downloadable:
                return True
        return False

    def _getUnusedDependencies(self):
        " get all package names that are not downloadable "
        unused_dependencies = set()
        for pkg in self:
            if pkg.is_installed and self._depcache.is_garbage(pkg._pkg):
                unused_dependencies.add(pkg.name)
        return unused_dependencies

    def get_installed_demoted_packages(self):
        """ return list of installed and demoted packages

            If a demoted package is a automatic install it will be skipped
        """
        demotions = set()
        demotions_file = self.config.get("Distro", "Demotions")
        if os.path.exists(demotions_file):
            with open(demotions_file) as demotions_f:
                for line in demotions_f:
                    if not line.startswith("#"):
                        demotions.add(line.strip())
        installed_demotions = set()
        for demoted_pkgname in demotions:
            if demoted_pkgname not in self:
                continue
            pkg = self[demoted_pkgname]
            if (not pkg.is_installed or
                self._depcache.is_auto_installed(pkg._pkg) or
                pkg.marked_delete):
                continue
            installed_demotions.add(pkg)
        return list(installed_demotions)

    def _getForeignPkgs(self, allowed_origin, fromDist, toDist):
        """ get all packages that are installed from a foreign repo
            (and are actually downloadable)
        """
        foreign_pkgs = set()
        for pkg in self:
            if pkg.is_installed and self.downloadable(pkg):
                if not pkg.candidate:
                    continue
                # assume it is foreign and see if it is from the
                # official archive
                foreign = True
                for origin in pkg.candidate.origins:
                    # FIXME: use some better metric here
                    if fromDist in origin.archive and \
                           origin.origin == allowed_origin:
                        foreign = False
                    if toDist in origin.archive and \
                           origin.origin == allowed_origin:
                        foreign = False
                if foreign:
                    foreign_pkgs.add(pkg.name)
        return foreign_pkgs

    def checkFreeSpace(self, snapshots_in_use=False):
        """
        this checks if we have enough free space on /var, /boot and /usr
        with the given cache

        Note: this can not be fully accurate if there are multiple
              mountpoints for /usr, /var, /boot
        """

        class FreeSpace(object):
            " helper class that represents the free space on each mounted fs "
            def __init__(self, initialFree):
                self.free = initialFree
                self.need = 0

        def make_fs_id(d):
            """ return 'id' of a directory so that directories on the
                same filesystem get the same id (simply the mount_point)
            """
            for mount_point in mounted:
                if d.startswith(mount_point):
                    return mount_point
            return "/"

        # this is all a bit complicated
        # 1) check what is mounted (in mounted)
        # 2) create FreeSpace objects for the dirs we are interested in
        #    (mnt_map)
        # 3) use the  mnt_map to check if we have enough free space and
        #    if not tell the user how much is missing
        mounted = []
        mnt_map = {}
        fs_free = {}
        with open("/proc/mounts") as mounts:
            for line in mounts:
                try:
                    (what, where, fs, options, a, b) = line.split()
                except ValueError as e:
                    logging.debug("line '%s' in /proc/mounts not understood (%s)" % (line, e))
                    continue
                if not where in mounted:
                    mounted.append(where)
        # make sure mounted is sorted by longest path
        mounted.sort(key=len, reverse=True)
        archivedir = apt_pkg.config.find_dir("Dir::Cache::archives")
        aufs_rw_dir = "/tmp/"
        if (hasattr(self, "config") and
            self.config.getWithDefault("Aufs", "Enabled", False)):
            aufs_rw_dir = self.config.get("Aufs", "RWDir")
            if not os.path.exists(aufs_rw_dir):
                os.makedirs(aufs_rw_dir)
        logging.debug("cache aufs_rw_dir: %s" % aufs_rw_dir)
        for d in ["/", "/usr", "/var", "/boot", archivedir, aufs_rw_dir, "/home", "/tmp/"]:
            d = os.path.realpath(d)
            fs_id = make_fs_id(d)
            if os.path.exists(d):
                st = os.statvfs(d)
                free = st.f_bavail * st.f_frsize
            else:
                logging.warning("directory '%s' does not exists" % d)
                free = 0
            if fs_id in mnt_map:
                logging.debug("Dir %s mounted on %s" %
                              (d, mnt_map[fs_id]))
                fs_free[d] = fs_free[mnt_map[fs_id]]
            else:
                logging.debug("Free space on %s: %s" %
                              (d, free))
                mnt_map[fs_id] = d
                fs_free[d] = FreeSpace(free)
        del mnt_map
        logging.debug("fs_free contains: '%s'" % fs_free)

        # now calculate the space that is required on /boot
        # we do this by checking how many linux-image-$ver packages
        # are installed or going to be installed
        kernel_count = 0
        for pkg in self:
            # we match against everything that looks like a kernel
            # and add space check to filter out metapackages
            if re.match("^linux-(image|image-debug)-[0-9.]*-.*", pkg.name):
                # upgrade because early in the release cycle the major version
                # may be the same or they might be -lts- kernels
                if pkg.marked_install or pkg.marked_upgrade:
                    logging.debug("%s (new-install) added with %s to boot space" % (pkg.name, KERNEL_SIZE))
                    kernel_count += 1
        # space calculated per LP: #1646222
        space_in_boot = (kernel_count * KERNEL_SIZE
                         + (kernel_count + 1) * INITRD_SIZE)

        # we check for various sizes:
        # archivedir is where we download the debs
        # /usr is assumed to get *all* of the install space (incorrect,
        #      but as good as we can do currently + safety buffer
        # /     has a small safety buffer as well
        required_for_aufs = 0.0
        if (hasattr(self, "config") and
            self.config.getWithDefault("Aufs", "Enabled", False)):
            logging.debug("taking aufs overlay into space calculation")
            aufs_rw_dir = self.config.get("Aufs", "RWDir")
            # if we use the aufs rw overlay all the space is consumed
            # the overlay dir
            for pkg in self:
                if pkg.marked_upgrade or pkg.marked_install:
                    required_for_aufs += pkg.candidate.installed_size

        # add old size of the package if we use snapshots
        required_for_snapshots = 0.0
        if snapshots_in_use:
            for pkg in self:
                if (pkg.is_installed and
                    (pkg.marked_upgrade or pkg.marked_delete)):
                    required_for_snapshots += pkg.installed.installed_size
            logging.debug("additional space for the snapshots: %s" % required_for_snapshots)

        # sum up space requirements
        for (dir, size) in [(archivedir, self.required_download),
                            ("/usr", self.additional_required_space),
                            # plus 50M safety buffer in /usr
                            ("/usr", 50*1024*1024),
                            ("/boot", space_in_boot),
                            ("/tmp", 5*1024*1024),   # /tmp for dkms LP: #427035
                            ("/", 10*1024*1024),     # small safety buffer /
                            (aufs_rw_dir, required_for_aufs),
                            # if snapshots are in use
                            ("/usr", required_for_snapshots),
                           ]:
            # we are ensuring we have more than enough free space not less
            if size < 0:
                continue
            dir = os.path.realpath(dir)
            logging.debug("dir '%s' needs '%s' of '%s' (%f)" % (dir, size, fs_free[dir], fs_free[dir].free))
            fs_free[dir].free -= size
            fs_free[dir].need += size

        # check for space required violations
        required_list = {}
        for dir in fs_free:
            if fs_free[dir].free < 0:
                # ensure unicode here (LP: #1172740)
                free_at_least = apt_pkg.size_to_str(float(abs(fs_free[dir].free)+1))
                if isinstance(free_at_least, bytes):
                    free_at_least = free_at_least.decode(
                        locale.getpreferredencoding())
                free_needed = apt_pkg.size_to_str(fs_free[dir].need)
                if isinstance(free_needed, bytes):
                    free_needed = free_needed.decode(
                        locale.getpreferredencoding())
                # make_fs_id ensures we only get stuff on the same
                # mountpoint, so we report the requirements only once
                # per mountpoint
                required_list[make_fs_id(dir)] = FreeSpaceRequired(free_needed, make_fs_id(dir), free_at_least)
        # raise exception if free space check fails
        if len(required_list) > 0:
            logging.error("Not enough free space: %s" % [str(i) for i in required_list])
            raise NotEnoughFreeSpaceError(list(required_list.values()))
        return True


if __name__ == "__main__":
    import sys
    from .DistUpgradeConfigParser import DistUpgradeConfig
    from .DistUpgradeView import DistUpgradeView
    print("foo")
    c = MyCache(DistUpgradeConfig("."), DistUpgradeView(), None)
    #c.checkForNvidia()
    #print(c._identifyObsoleteKernels())
    print(c.checkFreeSpace())
    sys.exit()

    c.clear()
    c.create_snapshot()
    c.installedTasks
    c.installTasks(["ubuntu-desktop"])
    print(c.get_changes())
    c.restore_snapshot()
