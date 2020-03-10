# DistUpgradeQuirks.py
#
#  Copyright (c) 2004-2010 Canonical
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
import atexit
import glob
import logging
import os
import re
import hashlib
import subprocess
from subprocess import PIPE, Popen
from shutil import copyfile

from .utils import get_arch

from .DistUpgradeGettext import gettext as _
try:
    from janitor.plugincore.manager import PluginManager
except ImportError:
    # janitor is not available, so create a no-op plugin manager.
    class PluginManager(object):
        def __init__(self, *args, **kws):
            pass

        def get_plugins(self, *args, **kws):
            return []


class DistUpgradeQuirks(object):
    """
    This class collects the various quirks handlers that can
    be hooked into to fix/work around issues that the individual
    releases have
    """

    def __init__(self, controller, config):
        self.controller = controller
        self._view = controller._view
        self.config = config
        self.uname = Popen(["uname", "-r"], stdout=PIPE,
                           universal_newlines=True).communicate()[0].strip()
        self.arch = get_arch()
        self.plugin_manager = PluginManager(self.controller, ["./plugins"])
        self._poke = None
        self._uid = ''
        self._user_env = {}
        self._snapstore_reachable = False

    # the quirk function have the name:
    #  $Name (e.g. PostUpgrade)
    #  $todist$Name (e.g. intrepidPostUpgrade)
    #  $from_$fromdist$Name (e.g. from_dapperPostUpgrade)
    def run(self, quirksName):
        """
        Run the specific quirks handler, the follow handlers are supported:
        - PreCacheOpen: run *before* the apt cache is opened the first time
                        to set options that affect the cache
        - PostInitialUpdate: run *before* the sources.list is rewritten but
                             after an initial apt-get update
        - PostDistUpgradeCache: run *after* the dist-upgrade was calculated
                                in the cache
        - StartUpgrade: before the first package gets installed (but the
                        download is finished)
        - PostUpgrade: run *after* the upgrade is finished successfully and
                       packages got installed
        - PostCleanup: run *after* the cleanup (orphaned etc) is finished
        """
        # we do not run any quirks in partialUpgrade mode
        if self.controller._partialUpgrade:
            logging.info("not running quirks in partialUpgrade mode")
            return
        to_release = self.config.get("Sources", "To")
        from_release = self.config.get("Sources", "From")
        # first check for matching plugins
        for condition in [
                quirksName,
                "%s%s" % (to_release, quirksName),
                "from_%s%s" % (from_release, quirksName)
        ]:
            for plugin in self.plugin_manager.get_plugins(condition):
                logging.debug("running quirks plugin %s" % plugin)
                plugin.do_cleanup_cruft()

        # run the handler that is common to all dists
        funcname = "%s" % quirksName
        func = getattr(self, funcname, None)
        if func is not None:
            logging.debug("quirks: running %s" % funcname)
            func()

        # run the quirksHandler to-dist
        funcname = "%s%s" % (to_release, quirksName)
        func = getattr(self, funcname, None)
        if func is not None:
            logging.debug("quirks: running %s" % funcname)
            func()

        # now run the quirksHandler from_${FROM-DIST}Quirks
        funcname = "from_%s%s" % (from_release, quirksName)
        func = getattr(self, funcname, None)
        if func is not None:
            logging.debug("quirks: running %s" % funcname)
            func()

    # individual quirks handler that run *before* the cache is opened
    def PreCacheOpen(self):
        """ run before the apt cache is opened the first time """
        logging.debug("running Quirks.PreCacheOpen")

    # individual quirks handler that run *after* the cache is opened
    def bionicPostInitialUpdate(self):
        # PreCacheOpen would be better but controller.abort fails terribly
        """ run after the apt cache is opened the first time """
        logging.debug("running Quirks.bionicPostInitialUpdate")
        cache = self.controller.cache
        if 'ubuntu-desktop' not in cache or \
                'snapd' not in cache:
            logging.debug("package required for Quirk not in cache")
            return
        if cache['ubuntu-desktop'].is_installed and \
                cache['snapd'].is_installed:
            self._checkStoreConnectivity()
        # neon packages with versions < in bionic
        copyfile('98-xenial-overrides', '/etc/apt/preferences.d/98-xenial-overrides')
        
    def bionicPostDistUpgradeCache(self):
        logging.debug("bionicPostDistUpgradeCache removing ecryptfs from mark_auto")
        cache = self.controller.cache
        # Make sure encrypted homes do not break.
        if 'ecryptfs-utils' in cache and cache['ecryptfs-utils'].is_installed:
            # Make sure this package isn't marked auto if it is installed.
            # If any user has an encrypted home losing this package would break
            # the decryption. If it is installed in error it still matters not,
            # better safe than sorry!
            cache['ecryptfs-utils'].mark_auto(False)

    def bionicPostUpgrade(self):
        logging.debug("running Quirks.bionicPostUpgrade")
        cache = self.controller.cache
        if 'ubuntu-desktop' not in cache or \
                'snapd' not in cache:
            logging.debug("package required for Quirk not in cache")
            return
        if cache['ubuntu-desktop'].is_installed and \
                cache['snapd'].is_installed and \
                self._snapstore_reachable:
            self._replaceDebsWithSnaps()
        # neon packages with versions < in bionic tidy
        os.remove('/etc/apt/preferences.d/98-xenial-overrides')

    # individual quirks handler when the dpkg run is finished ---------
    def PostCleanup(self):
        " run after cleanup "
        logging.debug("running Quirks.PostCleanup")

    # run right before the first packages get installed
    def StartUpgrade(self):
        logging.debug("running Quirks.StartUpgrade")
        self._applyPatches()
        self._removeOldApportCrashes()
        self._killUpdateNotifier()
        self._killKBluetooth()
        self._killScreensaver()
        self._pokeScreensaver()
        self._inhibitIdle()
        self._stopDocvertConverter()

    # individual quirks handler that run *after* the dist-upgrade was
    # calculated in the cache
    def PostDistUpgradeCache(self):
        """ run after calculating the dist-upgrade """
        logging.debug("running Quirks.PostDistUpgradeCache")
        self._install_linux_metapackage()

    # helpers
    def _get_pci_ids(self):
        """ return a set of pci ids of the system (using lspci -n) """
        lspci = set()
        try:
            p = subprocess.Popen(["lspci", "-n"], stdout=subprocess.PIPE,
                                 universal_newlines=True)
        except OSError:
            return lspci
        for line in p.communicate()[0].split("\n"):
            if line:
                lspci.add(line.split()[2])
        return lspci

    def _test_and_warn_for_unity_3d_support(self):
        UNITY_SUPPORT_TEST = "/usr/lib/nux/unity_support_test"
        if (not os.path.exists(UNITY_SUPPORT_TEST) or
                "DISPLAY" not in os.environ):
            return
        # see if there is a running unity, that service is used by both 2d,3d
        return_code = subprocess.call(
            ["ps", "-C", "unity-panel-service"], stdout=open(os.devnull, "w"))
        if return_code != 0:
            logging.debug(
                "_test_and_warn_for_unity_3d_support: no unity running")
            return
        # if we are here, we need to test and warn
        return_code = subprocess.call([UNITY_SUPPORT_TEST])
        logging.debug(
            "_test_and_warn_for_unity_3d_support '%s' returned '%s'" % (
                UNITY_SUPPORT_TEST, return_code))
        if return_code != 0:
            res = self._view.askYesNoQuestion(
                _("Your graphics hardware may not be fully supported in "
                  "Ubuntu 14.04."),
                _("Running the 'unity' desktop environment is not fully "
                  "supported by your graphics hardware. You will maybe end "
                  "up in a very slow environment after the upgrade. Our "
                  "advice is to keep the LTS version for now. For more "
                  "information see "
                  "https://wiki.ubuntu.com/X/Bugs/"
                  "UpdateManagerWarningForUnity3D "
                  "Do you still want to continue with the upgrade?")
            )
            if not res:
                self.controller.abort()

    def _test_and_warn_on_i8xx(self):
        I8XX_PCI_IDS = ["8086:7121",  # i810
                        "8086:7125",  # i810e
                        "8086:1132",  # i815
                        "8086:3577",  # i830
                        "8086:2562",  # i845
                        "8086:3582",  # i855
                        "8086:2572",  # i865
                        ]
        lspci = self._get_pci_ids()
        if set(I8XX_PCI_IDS).intersection(lspci):
            res = self._view.askYesNoQuestion(
                _("Your graphics hardware may not be fully supported in "
                  "Ubuntu 12.04 LTS."),
                _("The support in Ubuntu 12.04 LTS for your Intel "
                  "graphics hardware is limited "
                  "and you may encounter problems after the upgrade. "
                  "For more information see "
                  "https://wiki.ubuntu.com/X/Bugs/UpdateManagerWarningForI8xx "
                  "Do you want to continue with the upgrade?")
            )
            if not res:
                self.controller.abort()

    def _test_and_warn_on_dropped_fglrx_support(self):
        """
        Some cards are no longer supported by fglrx. Check if that
        is the case and warn
        """
        # this is to deal with the fact that support for some of the cards
        # that fglrx used to support got dropped
        if (self._checkVideoDriver("fglrx") and
                not self._supportInModaliases("fglrx")):
            res = self._view.askYesNoQuestion(
                _("Upgrading may reduce desktop "
                  "effects, and performance in games "
                  "and other graphically intensive "
                  "programs."),
                _("This computer is currently using "
                  "the AMD 'fglrx' graphics driver. "
                  "No version of this driver is "
                  "available that works with your "
                  "hardware in Ubuntu 10.04 LTS.\n\n"
                  "Do you want to continue?"))
            if not res:
                self.controller.abort()
            # if the user wants to continue we remove the fglrx driver
            # here because its no use (no support for this card)
            removals = [
                "xorg-driver-fglrx",
                "xorg-driver-fglrx-envy",
                "fglrx-kernel-source",
                "fglrx-amdcccle",
                "xorg-driver-fglrx-dev",
                "libamdxvba1"
            ]
            logging.debug("remove %s" % ", ".join(removals))
            postupgradepurge = self.controller.config.getlist(
                "Distro",
                "PostUpgradePurge")
            for remove in removals:
                postupgradepurge.append(remove)
            self.controller.config.set("Distro", "PostUpgradePurge",
                                       ",".join(postupgradepurge))

    def _test_and_fail_on_non_i686(self):
        """
        Test and fail if the cpu is not i686 or more or if its a newer
        CPU but does not have the cmov feature (LP: #587186)
        """
        # check on i386 only
        if self.arch == "i386":
            logging.debug("checking for i586 CPU")
            if not self._cpu_is_i686_and_has_cmov():
                logging.error("not a i686 or no cmov")
                summary = _("No i686 CPU")
                msg = _("Your system uses an i586 CPU or a CPU that does "
                        "not have the 'cmov' extension. "
                        "All packages were built with "
                        "optimizations requiring i686 as the "
                        "minimal architecture. It is not possible to "
                        "upgrade your system to a new Ubuntu release "
                        "with this hardware.")
                self._view.error(summary, msg)
                self.controller.abort()

    def _cpu_is_i686_and_has_cmov(self, cpuinfo_path="/proc/cpuinfo"):
        if not os.path.exists(cpuinfo_path):
            logging.error("cannot open %s ?!?" % cpuinfo_path)
            return True
        with open(cpuinfo_path) as f:
            cpuinfo = f.read()
        # check family
        if re.search("^cpu family\s*:\s*[345]\s*", cpuinfo, re.MULTILINE):
            logging.debug("found cpu family [345], no i686+")
            return False
        # check flags for cmov
        match = re.search("^flags\s*:\s*(.*)", cpuinfo, re.MULTILINE)
        if match:
            if "cmov" not in match.group(1).split():
                logging.debug("found flags '%s'" % match.group(1))
                logging.debug("can not find cmov in flags")
                return False
        return True

    def _test_and_fail_on_non_arm_v6(self):
        """
        Test and fail if the cpu is not a arm v6 or greater,
        from 9.10 on we do no longer support those CPUs
        """
        if self.arch == "armel":
            if not self._checkArmCPU():
                self._view.error(
                    _("No ARMv6 CPU"),
                    _("Your system uses an ARM CPU that is older "
                      "than the ARMv6 architecture. "
                      "All packages in karmic were built with "
                      "optimizations requiring ARMv6 as the "
                      "minimal architecture. It is not possible to "
                      "upgrade your system to a new Ubuntu release "
                      "with this hardware."))
                self.controller.abort()

    def _test_and_warn_if_vserver(self):
        """
        upstart and vserver environments are not a good match, warn
        if we find one
        """
        # verver test (LP: #454783), see if there is a init around
        try:
            os.kill(1, 0)
        except OSError:
            logging.warning("no init found")
            res = self._view.askYesNoQuestion(
                _("No init available"),
                _("Your system appears to be a virtualised environment "
                  "without an init daemon, e.g. Linux-VServer. "
                  "Ubuntu 10.04 LTS cannot function within this type of "
                  "environment, requiring an update to your virtual "
                  "machine configuration first.\n\n"
                  "Are you sure you want to continue?"))
            if not res:
                self.controller.abort()
            self._view.processEvents()

    def _checkArmCPU(self):
        """
        parse /proc/cpuinfo and search for ARMv6 or greater
        """
        logging.debug("checking for ARM CPU version")
        if not os.path.exists("/proc/cpuinfo"):
            logging.error("cannot open /proc/cpuinfo ?!?")
            return False
        with open("/proc/cpuinfo") as f:
            cpuinfo = f.read()
        if re.search("^Processor\s*:\s*ARMv[45]", cpuinfo,
                     re.MULTILINE):
            return False
        return True

    def _stopApparmor(self):
        """ /etc/init.d/apparmor stop (see bug #559433)"""
        if os.path.exists("/etc/init.d/apparmor"):
            logging.debug("/etc/init.d/apparmor stop")
            subprocess.call(["/etc/init.d/apparmor", "stop"])

    def _stopDocvertConverter(self):
        " /etc/init.d/docvert-converter stop (see bug #450569)"
        if os.path.exists("/etc/init.d/docvert-converter"):
            logging.debug("/etc/init.d/docvert-converter stop")
            subprocess.call(["/etc/init.d/docvert-converter", "stop"])

    def _killUpdateNotifier(self):
        "kill update-notifier"
        # kill update-notifier now to suppress reboot required
        if os.path.exists("/usr/bin/killall"):
            logging.debug("killing update-notifier")
            subprocess.call(["killall", "-q", "update-notifier"])

    def _killKBluetooth(self):
        """killall kblueplugd kbluetooth (riddel requested it)"""
        if os.path.exists("/usr/bin/killall"):
            logging.debug("killing kblueplugd kbluetooth4")
            subprocess.call(["killall", "-q", "kblueplugd", "kbluetooth4"])

    def _killScreensaver(self):
        """killall gnome-screensaver """
        if os.path.exists("/usr/bin/killall"):
            logging.debug("killing gnome-screensaver")
            subprocess.call(["killall", "-q", "gnome-screensaver"])

    def _pokeScreensaver(self):
        if (os.path.exists("/usr/bin/xdg-screensaver") and
                os.environ.get('DISPLAY')):
            logging.debug("setup poke timer for the scrensaver")
            cmd = "while true;"
            cmd += " do /usr/bin/xdg-screensaver reset >/dev/null 2>&1;"
            cmd += " sleep 30; done"
            try:
                self._poke = subprocess.Popen(cmd, shell=True)
                atexit.register(self._stopPokeScreensaver)
            except (OSError, ValueError):
                logging.exception("failed to setup screensaver poke")

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
                xdg_desktop = xdg_desktop.split(':')
                idle = subprocess.Popen(["gnome-session-inhibit", "--inhibit",
                                         "idle", "--inhibit-only"],
                                        env=self._user_env)
                # leave the inhibitor in place on Ubuntu GNOME, since the
                # lock screen will be broken after upgrade (LP: #1565178)
                for desktop in xdg_desktop:
                    if "GNOME" not in desktop:
                        atexit.register(idle.terminate)
            except (OSError, ValueError):
                logging.exception("failed to inhibit gnome-session idle")
            os.seteuid(os.getuid())

    def _stopPokeScreensaver(self):
        res = False
        if self._poke is not None:
            try:
                self._poke.terminate()
                res = self._poke.wait()
            except OSError:
                logging.exception("failed to stop screensaver poke")
            self._poke = None
        return res

    def _removeOldApportCrashes(self):
        " remove old apport crash files and whoopsie control files "
        try:
            for ext in ['.crash', '.upload', '.uploaded']:
                for f in glob.glob("/var/crash/*%s" % ext):
                    logging.debug("removing old %s file '%s'" % (ext, f))
                    os.unlink(f)
        except Exception as e:
            logging.warning("error during unlink of old crash files (%s)" % e)

    def _checkStoreConnectivity(self):
        """ check for connectivity to the snap store to install snaps"""
        res = False
        snap_env = os.environ.copy()
        snap_env["LANG"] = "C.UTF-8"
        connected = Popen(["snap", "debug", "connectivity"], stdout=PIPE,
                          stderr=PIPE, env=snap_env,
                          universal_newlines=True).communicate()
        if re.search("^ \* PASS", connected[0], re.MULTILINE):
            self._snapstore_reachable = True
            return
        # can't connect
        elif re.search("^ \*.*unreachable", connected[0], re.MULTILINE):
            logging.error("No snap store connectivity")
            res = self._view.askYesNoQuestion(
                _("Connection to Snap Store failed"),
                _("Your system does not have a connection to the Snap "
                  "Store. For the best upgrade experience make sure "
                  "that your system can connect to api.snapcraft.io.\n"
                  "Do you still want to continue with the upgrade?")
            )
        # debug command not available
        elif 'error: unknown command' in connected[1]:
            logging.error("snap debug command not available")
            res = self._view.askYesNoQuestion(
                _("Outdated snapd package"),
                _("Your system does not have the latest version of snapd. "
                  "Please update the version of snapd on your system to "
                  "improve the upgrade experience.\n"
                  "Do you still want to continue with the upgrade?")
            )
        # not running as root
        elif 'error: access denied' in connected[1]:
            res = False
            logging.error("Not running as root!")
        if not res:
            self.controller.abort()

    def _replaceDebsWithSnaps(self):
        """ install a snap and mark its corresponding package for removal """
        # gtk-common-themes isn't a package name but is this risky?
        snaps = ['gnome-3-26-1604', 'gtk-common-themes', 'gnome-calculator',
                 'gnome-characters', 'gnome-logs', 'gnome-system-monitor']
        self._view.updateStatus(_("Checking for installed snaps"))
        installed_snaps = subprocess.Popen(["snap", "list"],
                                           universal_newlines=True,
                                           stdout=PIPE).communicate()
        self._view.processEvents()
        for snap in snaps:
            installed = False
            # check to see if the snap is already installed
            if re.search("^%s " % snap, installed_snaps[0], re.MULTILINE):
                logging.debug("Snap %s is already installed" % snap)
                installed = True
            if not installed:
                try:
                    self._view.updateStatus(_("Installing snap %s" % snap))
                    self._view.processEvents()
                    proc = subprocess.run(["snap", "install", "--channel",
                                           "stable/ubuntu-18.04", snap],
                                          stdout=subprocess.PIPE,
                                          check=True)
                    self._view.processEvents()
                except subprocess.CalledProcessError:
                    logging.debug("Install of snap %s failed" % snap)
                    continue
                if proc.returncode == 0:
                    logging.debug("Install of snap %s succeeded" % snap)
                    installed = True
            if installed:
                self.controller.forced_obsoletes.append(snap)

    def _checkPae(self):
        " check PAE in /proc/cpuinfo "
        # upgrade from Precise will fail if PAE is not in cpu flags
        logging.debug("_checkPae")
        pae = 0
        with open('/proc/cpuinfo') as f:
            cpuinfo = f.read()
        if re.search("^flags\s+:.* pae ", cpuinfo, re.MULTILINE):
            pae = 1
        if not pae:
            logging.error("no pae in /proc/cpuinfo")
            summary = _("PAE not enabled")
            msg = _("Your system uses a CPU that does not have PAE enabled. "
                    "Ubuntu only supports non-PAE systems up to Ubuntu "
                    "12.04. To upgrade to a later version of Ubuntu, you "
                    "must enable PAE (if this is possible) see:\n"
                    "http://help.ubuntu.com/community/EnablingPAE")
            self._view.error(summary, msg)
            self.controller.abort()

    def _checkVideoDriver(self, name):
        " check if the given driver is in use in xorg.conf "
        XORG = "/etc/X11/xorg.conf"
        if not os.path.exists(XORG):
            return False
        with open(XORG) as f:
            lines = f.readlines()
        for line in lines:
            s = line.split("#")[0].strip()
            # check for fglrx driver entry
            if (s.lower().startswith("driver") and
                    s.endswith('"%s"' % name)):
                return True
        return False

    def _applyPatches(self, patchdir="./patches"):
        """
        helper that applies the patches in patchdir. the format is
        _path_to_file.md5sum and it will apply the diff to that file if the
        md5sum matches
        """
        if not os.path.exists(patchdir):
            logging.debug("no patchdir")
            return
        for f in os.listdir(patchdir):
            # skip, not a patch file, they all end with .$md5sum
            if "." not in f:
                logging.debug("skipping '%s' (no '.')" % f)
                continue
            logging.debug("check if patch '%s' needs to be applied" % f)
            (encoded_path, md5sum, result_md5sum) = f.rsplit(".", 2)
            # FIXME: this is not clever and needs quoting support for
            #        filenames with "_" in the name
            path = encoded_path.replace("_", "/")
            logging.debug("target for '%s' is '%s' -> '%s'" % (
                f, encoded_path, path))
            # target does not exist
            if not os.path.exists(path):
                logging.debug("target '%s' does not exist" % path)
                continue
            # check the input md5sum, this is not strictly needed as patch()
            # will verify the result md5sum and discard the result if that
            # does not match but this will remove a misleading error in the
            # logs
            md5 = hashlib.md5()
            with open(path, "rb") as fd:
                md5.update(fd.read())
            if md5.hexdigest() == result_md5sum:
                logging.debug("already at target hash, skipping '%s'" % path)
                continue
            elif md5.hexdigest() != md5sum:
                logging.warning("unexpected target md5sum, skipping: '%s'"
                                % path)
                continue
            # patchable, do it
            from .DistUpgradePatcher import patch
            try:
                patch(path, os.path.join(patchdir, f), result_md5sum)
                logging.info("applied '%s' successfully" % f)
            except Exception:
                logging.exception("ed failed for '%s'" % f)

    def _supportInModaliases(self, pkgname, lspci=None):
        """
        Check if pkgname will work on this hardware

        This helper will check with the modaliasesdir if the given
        pkg will work on this hardware (or the hardware given
        via the lspci argument)
        """
        # get lspci info (if needed)
        if not lspci:
            lspci = self._get_pci_ids()
        # get pkg
        if (pkgname not in self.controller.cache or
                not self.controller.cache[pkgname].candidate):
            logging.warning("can not find '%s' in cache")
            return False
        pkg = self.controller.cache[pkgname]
        for (module, pciid_list) in \
                self._parse_modaliases_from_pkg_header(pkg.candidate.record):
            for pciid in pciid_list:
                m = re.match("pci:v0000(.+)d0000(.+)sv.*", pciid)
                if m:
                    matchid = "%s:%s" % (m.group(1), m.group(2))
                    if matchid.lower() in lspci:
                        logging.debug("found system pciid '%s' in modaliases"
                                      % matchid)
                        return True
        logging.debug("checking for %s support in modaliases but none found"
                      % pkgname)
        return False

    def _parse_modaliases_from_pkg_header(self, pkgrecord):
        """ return a list of (module1, (pciid, ...), ...)"""
        if "Modaliases" not in pkgrecord:
            return []
        # split the string
        modules = []
        for m in pkgrecord["Modaliases"].split(")"):
            m = m.strip(", ")
            if not m:
                continue
            (module, pciids) = m.split("(")
            modules.append((module, [x.strip() for x in pciids.split(",")]))
        return modules

    def _add_extras_repository(self):
        logging.debug("_add_extras_repository")
        cache = self.controller.cache
        if "ubuntu-extras-keyring" not in cache:
            logging.debug("no ubuntu-extras-keyring, no need to add repo")
            return
        if not (cache["ubuntu-extras-keyring"].marked_install or
                cache["ubuntu-extras-keyring"].installed):
            logging.debug("ubuntu-extras-keyring not installed/marked_install")
            return
        try:
            import aptsources.sourceslist
            sources = aptsources.sourceslist.SourcesList()
            for entry in sources:
                if "extras.ubuntu.com" in entry.uri:
                    logging.debug("found extras.ubuntu.com, no need to add it")
                    break
            else:
                logging.info("no extras.ubuntu.com, adding it to sources.list")
                sources.add("deb", "http://extras.ubuntu.com/ubuntu",
                            self.controller.toDist, ["main"],
                            "Third party developers repository")
                sources.save()
        except Exception:
            logging.exception("error adding extras.ubuntu.com")

    def _gutenprint_fixup(self):
        """ foomatic-db-gutenprint get removed during the upgrade,
            replace it with the compressed ijsgutenprint-ppds
            (context is foomatic-db vs foomatic-db-compressed-ppds)
        """
        try:
            cache = self.controller.cache
            if ("foomatic-db-gutenprint" in cache and
                    cache["foomatic-db-gutenprint"].marked_delete and
                    "ijsgutenprint-ppds" in cache):
                logging.info("installing ijsgutenprint-ppds")
                cache.mark_install(
                    "ijsgutenprint-ppds",
                    "foomatic-db-gutenprint -> ijsgutenprint-ppds rule")
        except Exception:
            logging.exception("_gutenprint_fixup failed")

    def _enable_multiarch(self, foreign_arch="i386"):
        """ enable multiarch via /etc/dpkg/dpkg.cfg.d/multiarch """
        cfg = "/etc/dpkg/dpkg.cfg.d/multiarch"
        if not os.path.exists(cfg):
            try:
                os.makedirs("/etc/dpkg/dpkg.cfg.d/")
            except OSError:
                pass
            with open(cfg, "w") as f:
                f.write("foreign-architecture %s\n" % foreign_arch)

    def _is_greater_than(self, term1, term2):
        """ copied from ubuntu-drivers common """
        # We don't want to take into account
        # the flavour
        pattern = re.compile('(.+)-([0-9]+)-(.+)')
        match1 = pattern.match(term1)
        match2 = pattern.match(term2)
        if match1:
            term1 = '%s-%s' % (match1.group(1),
                               match1.group(2))
            term2 = '%s-%s' % (match2.group(1),
                               match2.group(2))

        logging.debug('Comparing %s with %s' % (term1, term2))
        return apt.apt_pkg.version_compare(term1, term2) > 0

    def _get_linux_metapackage(self, cache, headers):
        """ Get the linux headers or linux metapackage
            copied from ubuntu-drivers-common
        """
        suffix = headers and '-headers' or ''
        pattern = re.compile('linux-image-(.+)-([0-9]+)-(.+)')
        source_pattern = re.compile('linux-(.+)')

        metapackage = ''
        version = ''
        for pkg in cache:
            if ('linux-image' in pkg.name and 'extra' not in pkg.name and
                    (pkg.is_installed or pkg.marked_install)):
                match = pattern.match(pkg.name)
                # Here we filter out packages such as
                # linux-generic-lts-quantal
                if match:
                    source = pkg.candidate.record['Source']
                    current_version = '%s-%s' % (match.group(1),
                                                 match.group(2))
                    # See if the current version is greater than
                    # the greatest that we've found so far
                    if self._is_greater_than(current_version,
                                             version):
                        version = current_version
                        match_source = source_pattern.match(source)
                        # Set the linux-headers metapackage
                        if '-lts-' in source and match_source:
                            # This is the case of packages such as
                            # linux-image-3.5.0-18-generic which
                            # comes from linux-lts-quantal.
                            # Therefore the linux-headers-generic
                            # metapackage would be wrong here and
                            # we should use
                            # linux-headers-generic-lts-quantal
                            # instead
                            metapackage = 'linux%s-%s-%s' % (
                                           suffix,
                                           match.group(3),
                                           match_source.group(1))
                        else:
                            # The scheme linux-headers-$flavour works
                            # well here
                            metapackage = 'linux%s-%s' % (
                                           suffix,
                                           match.group(3))
        return metapackage

    def _install_linux_metapackage(self):
        """ Ensure the linux metapackage is installed for the newest_kernel
            installed. (LP: #1509305)
        """
        cache = self.controller.cache
        linux_metapackage = self._get_linux_metapackage(cache, False)
        # Seen on errors.u.c with linux-rpi2 metapackage
        # https://errors.ubuntu.com/problem/994bf05fae85fbcd44f721495db6518f2d5a126d
        if linux_metapackage not in cache:
            logging.info("linux metapackage (%s) not available" %
                         linux_metapackage)
            return
        # install the package if it isn't installed
        if not cache[linux_metapackage].is_installed:
            logging.info("installing linux metapackage: %s" %
                         linux_metapackage)
            reason = "linux metapackage may have been accidentally uninstalled"
            cache.mark_install(linux_metapackage, reason)

    def ensure_recommends_are_installed_on_desktops(self):
        """ ensure that on a desktop install recommends are installed
            (LP: #759262)
        """
        if not self.controller.serverMode:
            if not apt.apt_pkg.config.find_b("Apt::Install-Recommends"):
                msg = "Apt::Install-Recommends was disabled,"
                msg += " enabling it just for the upgrade"
                logging.warning(msg)
                apt.apt_pkg.config.set("Apt::Install-Recommends", "1")
