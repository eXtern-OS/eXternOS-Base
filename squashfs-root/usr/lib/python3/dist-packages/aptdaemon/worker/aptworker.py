#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Provides AptWorker which processes transactions."""
# Copyright (C) 2008-2009 Sebastian Heinlein <devel@glatzor.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

__all__ = ("AptWorker")

import contextlib
import errno
import glob
import logging
import netrc
import os
import re
import shutil
import stat
import sys
import tempfile
import time
import traceback
try:
    from urllib.parse import urlsplit, urlunsplit
except ImportError:
    from urlparse import urlsplit, urlunsplit

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

import apt
import apt.auth
import apt.cache
import apt.debfile
import apt_pkg
import aptsources
import aptsources.distro
from aptsources.sourceslist import SourcesList
from gi.repository import GObject, GLib

from . import BaseWorker
from ..enums import *
from ..errors import *
from .. import lock
from ..progress import (
    DaemonOpenProgress,
    DaemonInstallProgress,
    DaemonAcquireProgress,
    DaemonAcquireRepoProgress,
    DaemonDpkgInstallProgress,
    DaemonDpkgReconfigureProgress,
    DaemonDpkgRecoverProgress,
    DaemonLintianProgress,
    DaemonForkProgress)

log = logging.getLogger("AptDaemon.Worker")

# Just required to detect translatable strings. The translation is done by
# core.Transaction.gettext
_ = lambda s: s

_POPCON_PATH = "/etc/popularity-contest.conf"
_POPCON_DEFAULT = """# Config file for Debian's popularity-contest package.
#
# To change this file, use:
#        dpkg-reconfigure popularity-contest
#
# You can also edit it by hand, if you so choose.
#
# See /usr/share/popularity-contest/default.conf for more info
# on the options.
MY_HOSTID="%(host_id)s"
PARTICIPATE="%(participate)s"
USE_HTTP="yes"
"""


@contextlib.contextmanager
def set_euid_egid(uid, gid):
    # no need to drop privs
    if os.getuid() != 0 and os.getgid() != 0:
        yield
        return
    # temporary drop privs
    os.setegid(gid)
    old_groups = os.getgroups()
    os.setgroups([gid])
    os.seteuid(uid)
    try:
        yield
    finally:
        os.seteuid(os.getuid())
        os.setegid(os.getgid())
        os.setgroups(old_groups)


def trans_only_installs_pkgs_from_high_trust_repos(trans,
                                                   whitelist=set()):
    """Return True if this transaction only touches packages in the
    aptdaemon repoisotry high trust repository whitelist
    """
    # the transaction *must* be simulated before
    if not trans.simulated:
        return False
    # we never allow unauthenticated ones
    if trans.unauthenticated:
        return False
    # paranoia: wrong role
    if trans.role not in (ROLE_INSTALL_PACKAGES, ROLE_COMMIT_PACKAGES):
        return False
    # if there is anything touched that is not a install bail out
    for enum in (PKGS_REINSTALL, PKGS_REMOVE, PKGS_PURGE, PKGS_DOWNGRADE,
                 PKGS_UPGRADE):
        if trans.packages[enum]:
            return False
    # paranoia(2): we must want to install something
    if not trans.packages[PKGS_INSTALL]:
        return False
    # we only care about the name, not the version
    pkgs = [pkg.split("=")[0] for pkg in trans.packages[PKGS_INSTALL]]
    # if the install packages matches the whitelisted set we are good
    return set(pkgs) == set(trans.high_trust_packages)


def read_high_trust_repository_dir(whitelist_cfg_d):
    """Return a set of (origin, component, pkgname-regexp) from a
    high-trust-repository-whitelist.d directory
    """
    whitelist = set()
    for path in glob.glob(os.path.join(whitelist_cfg_d, "*.cfg")):
        whitelist |= _read_high_trust_repository_whitelist_file(path)
    return whitelist


def _read_high_trust_repository_whitelist_file(path):
    """Read a individual high-trust-repository whitelist file and return
       a set of tuples (origin, component, pkgname-regexp)
    """
    parser = ConfigParser()
    whitelist = set()
    try:
        parser.read(path)
    except Exception as e:
        log.error("Failed to read repository whitelist '%s' (%s)" % (path, e))
        return whitelist
    for section in parser.sections():
        origin = parser.get(section, "origin")
        component = parser.get(section, "component")
        pkgnames = parser.get(section, "pkgnames")
        whitelist.add((origin, component, pkgnames))
    return whitelist


class AptWorker(BaseWorker):

    """Worker which processes transactions from the queue."""

    NATIVE_ARCH = apt_pkg.get_architectures()[0]

    # the basedir under which license keys can be stored
    LICENSE_KEY_ROOTDIR = "/opt/"

    def __init__(self, chroot=None, load_plugins=True):
        """Initialize a new AptWorker instance."""
        BaseWorker.__init__(self, chroot, load_plugins)
        self._cache = None

        # Change to a given chroot
        if self.chroot:
            apt_conf_file = os.path.join(chroot, "etc/apt/apt.conf")
            if os.path.exists(apt_conf_file):
                apt_pkg.read_config_file(apt_pkg.config, apt_conf_file)
            apt_conf_dir = os.path.join(chroot, "etc/apt/apt.conf.d")
            if os.path.isdir(apt_conf_dir):
                apt_pkg.read_config_dir(apt_pkg.config, apt_conf_dir)
            apt_pkg.config["Dir"] = chroot
            apt_pkg.config["Dir::State::Status"] = os.path.join(
                chroot, "var/lib/dpkg/status")
            apt_pkg.config.clear("DPkg::Post-Invoke")
            apt_pkg.config.clear("DPkg::Options")
            apt_pkg.config["DPkg::Options::"] = "--root=%s" % chroot
            apt_pkg.config["DPkg::Options::"] = ("--log=%s/var/log/dpkg.log" %
                                                 chroot)
            status_file = apt_pkg.config.find_file("Dir::State::status")
            lock.frontend_lock.path = os.path.join(os.path.dirname(status_file),
                                                 "lock-frontend")
            lock.status_lock.path = os.path.join(os.path.dirname(status_file),
                                                 "lock")
            archives_dir = apt_pkg.config.find_dir("Dir::Cache::Archives")
            lock.archive_lock.path = os.path.join(archives_dir, "lock")
            lists_dir = apt_pkg.config.find_dir("Dir::State::lists")
            lock.lists_lock.path = os.path.join(lists_dir, "lock")
            apt_pkg.init_system()

        # a set of tuples of the type (origin, component, pkgname-regexp)
        # that on install will trigger a different kind of polkit
        # authentication request (see LP: #1035207), useful for e.g.
        # webapps/company repos
        self._high_trust_repositories = read_high_trust_repository_dir(
            os.path.join(apt_pkg.config.find_dir("Dir"),
                         "etc/aptdaemon/high-trust-repository-whitelist.d"))
        log.debug(
            "using high-trust whitelist: '%s'" % self._high_trust_repositories)

        self._status_orig = apt_pkg.config.find_file("Dir::State::status")
        self._status_frozen = None
        if load_plugins:
            self._load_plugins(["modify_cache_after", "modify_cache_before",
                                "get_license_key"])

    def _call_plugins(self, name, resolver=None):
        """Call all plugins of a given type."""
        if not resolver:
            # If the resolver of the original task isn't available we create
            # a new one and protect the already marked changes
            resolver = apt.cache.ProblemResolver(self._cache)
            for pkg in self._cache.get_changes():
                resolver.clear(pkg)
                resolver.protect(pkg)
                if pkg.marked_delete:
                    resolver.remove(pkg)
        if name not in self.plugins:
            log.debug("There isn't any registered %s plugin" % name)
            return False
        for plugin in self.plugins[name]:
            log.debug("Calling %s plugin: %s", name, plugin)
            try:
                plugin(resolver, self._cache)
            except Exception as error:
                log.critical("Failed to call %s plugin:\n%s" % (plugin, error))
        return True

    def _run_transaction(self, trans):
        """Run the worker"""
        try:
            lock.wait_for_lock(trans)
            # Prepare the package cache
            if (trans.role == ROLE_FIX_INCOMPLETE_INSTALL or
                    not self.is_dpkg_journal_clean()):
                self.fix_incomplete_install(trans)
            # Process transaction which don't require a cache
            if trans.role == ROLE_ADD_VENDOR_KEY_FILE:
                self.add_vendor_key_from_file(trans, **trans.kwargs)
            elif trans.role == ROLE_ADD_VENDOR_KEY_FROM_KEYSERVER:
                self.add_vendor_key_from_keyserver(trans, **trans.kwargs)
            elif trans.role == ROLE_REMOVE_VENDOR_KEY:
                self.remove_vendor_key(trans, **trans.kwargs)
            elif trans.role == ROLE_ADD_REPOSITORY:
                self.add_repository(trans, **trans.kwargs)
            elif trans.role == ROLE_ENABLE_DISTRO_COMP:
                self.enable_distro_comp(trans, **trans.kwargs)
            elif trans.role == ROLE_RECONFIGURE:
                self.reconfigure(trans, trans.packages[PKGS_REINSTALL],
                                 **trans.kwargs)
            elif trans.role == ROLE_CLEAN:
                self.clean(trans)
            # Check if the transaction has been just simulated. So we could
            # skip marking the changes a second time.
            elif (trans.role in (ROLE_REMOVE_PACKAGES, ROLE_INSTALL_PACKAGES,
                                 ROLE_UPGRADE_PACKAGES, ROLE_COMMIT_PACKAGES,
                                 ROLE_UPGRADE_SYSTEM,
                                 ROLE_FIX_BROKEN_DEPENDS) and
                  self.marked_tid == trans.tid):
                self._apply_changes(trans)
                trans.exit = EXIT_SUCCESS
                return False
            else:
                self._open_cache(trans)
            # Process transaction which can handle a broken dep cache
            if trans.role == ROLE_FIX_BROKEN_DEPENDS:
                self.fix_broken_depends(trans)
            elif trans.role == ROLE_UPDATE_CACHE:
                self.update_cache(trans, **trans.kwargs)
            # Process the transactions which require a consistent cache
            elif trans.role == ROLE_ADD_LICENSE_KEY:
                self.add_license_key(trans, **trans.kwargs)
            elif self._cache and self._cache.broken_count:
                raise TransactionFailed(ERROR_CACHE_BROKEN,
                                        self._get_broken_details(trans))
            if trans.role == ROLE_PK_QUERY:
                self.query(trans)
            elif trans.role == ROLE_INSTALL_FILE:
                self.install_file(trans, **trans.kwargs)
            elif trans.role in [ROLE_REMOVE_PACKAGES, ROLE_INSTALL_PACKAGES,
                                ROLE_UPGRADE_PACKAGES, ROLE_COMMIT_PACKAGES]:
                self.commit_packages(trans, *trans.packages)
            elif trans.role == ROLE_UPGRADE_SYSTEM:
                self.upgrade_system(trans, **trans.kwargs)
        finally:
            lock.release()

    def commit_packages(self, trans, install, reinstall, remove, purge,
                        upgrade, downgrade, simulate=False):
        """Perform a complex package operation.

        Keyword arguments:
        trans - the transaction
        install - list of package names to install
        reinstall - list of package names to reinstall
        remove - list of package names to remove
        purge - list of package names to purge including configuration files
        upgrade - list of package names to upgrade
        downgrade - list of package names to upgrade
        simulate -- if True the changes won't be applied
        """
        log.info("Committing packages: %s, %s, %s, %s, %s, %s",
                 install, reinstall, remove, purge, upgrade, downgrade)
        with self._cache.actiongroup():
            resolver = apt.cache.ProblemResolver(self._cache)
            self._mark_packages_for_installation(install, resolver)
            self._mark_packages_for_installation(reinstall, resolver,
                                                 reinstall=True)
            self._mark_packages_for_removal(remove, resolver)
            self._mark_packages_for_removal(purge, resolver, purge=True)
            self._mark_packages_for_upgrade(upgrade, resolver)
            self._mark_packages_for_downgrade(downgrade, resolver)
            self._resolve_depends(trans, resolver)
        self._check_obsoleted_dependencies(trans, resolver)
        if not simulate:
            self._apply_changes(trans)

    def _resolve_depends(self, trans, resolver):
        """Resolve the dependencies using the given ProblemResolver."""
        self._call_plugins("modify_cache_before", resolver)
        resolver.install_protect()
        try:
            resolver.resolve()
        except SystemError:
            raise TransactionFailed(ERROR_DEP_RESOLUTION_FAILED,
                                    self._get_broken_details(trans, now=False))
        if self._call_plugins("modify_cache_after", resolver):
            try:
                resolver.resolve()
            except SystemError:
                details = self._get_broken_details(trans, now=False)
                raise TransactionFailed(ERROR_DEP_RESOLUTION_FAILED, details)

    def _get_high_trust_packages(self):
        """ Return a list of packages that come from a high-trust repo """
        def _in_high_trust_repository(pkgname, pkgorigin):
            for origin, component, regexp in self._high_trust_repositories:
                if (origin == pkgorigin.origin and
                        component == pkgorigin.component and
                        re.match(regexp, pkgname)):
                    return True
            return False
        # loop
        from_high_trust_repo = []
        for pkg in self._cache.get_changes():
            if pkg.marked_install:
                for origin in pkg.candidate.origins:
                    if _in_high_trust_repository(pkg.name, origin):
                        from_high_trust_repo.append(pkg.name)
                        break
        return from_high_trust_repo

    def _get_unauthenticated(self):
        """Return a list of unauthenticated package names """
        unauthenticated = []
        for pkg in self._cache.get_changes():
            if (pkg.marked_install or
                    pkg.marked_downgrade or
                    pkg.marked_upgrade or
                    pkg.marked_reinstall):
                trusted = False
                for origin in pkg.candidate.origins:
                    trusted |= origin.trusted
                if not trusted:
                    unauthenticated.append(pkg.name)
        return unauthenticated

    def _mark_packages_for_installation(self, packages, resolver,
                                        reinstall=False):
        """Mark packages for installation."""
        for pkg_name, pkg_ver, pkg_rel in [self._split_package_id(pkg)
                                           for pkg in packages]:
            pkg_name, sep, auto_marker = pkg_name.partition("#")
            from_user = (auto_marker != "auto")
            try:
                pkg = self._cache[pkg_name]
            except KeyError:
                raise TransactionFailed(ERROR_NO_PACKAGE,
                                        _("Package %s isn't available"),
                                        pkg_name)
            if reinstall:
                if not pkg.is_installed:
                    raise TransactionFailed(ERROR_PACKAGE_NOT_INSTALLED,
                                            _("Package %s isn't installed"),
                                            pkg.name)
                if pkg_ver and pkg.installed.version != pkg_ver:
                    raise TransactionFailed(ERROR_PACKAGE_NOT_INSTALLED,
                                            _("The version %s of %s isn't "
                                              "installed"),
                                            pkg_ver, pkg_name)
            else:
                # Fail if the user requests to install the same version
                # of an already installed package.
                if (pkg.is_installed and
                    # Compare version numbers
                    pkg_ver and pkg_ver == pkg.installed.version and
                    # Optionally compare the origin if specified
                    (not pkg_rel or
                     pkg_rel in [origin.archive for
                                 origin in pkg.installed.origins])):
                        raise TransactionFailed(
                            ERROR_PACKAGE_ALREADY_INSTALLED,
                            _("Package %s is already installed"), pkg_name)
            pkg.mark_install(False, True, from_user)
            resolver.clear(pkg)
            resolver.protect(pkg)
            if pkg_ver:
                try:
                    pkg.candidate = pkg.versions[pkg_ver]
                except KeyError:
                    raise TransactionFailed(ERROR_NO_PACKAGE,
                                            _("The version %s of %s isn't "
                                              "available."), pkg_ver, pkg_name)
            elif pkg_rel:
                self._set_candidate_release(pkg, pkg_rel)

    def enable_distro_comp(self, trans, component):
        """Enable given component in the sources list.

        Keyword arguments:
        trans -- the corresponding transaction
        component -- a component, e.g. main or universe
        """
        trans.progress = 101
        trans.status = STATUS_COMMITTING
        old_umask = os.umask(0o022)
        try:
            sourceslist = SourcesList()
            distro = aptsources.distro.get_distro()
            distro.get_sources(sourceslist)
            distro.enable_component(component)
            sourceslist.save()
        finally:
            os.umask(old_umask)

    def add_repository(self, trans, src_type, uri, dist, comps, comment,
                       sourcesfile):
        """Add given repository to the sources list.

        Keyword arguments:
        trans -- the corresponding transaction
        src_type -- the type of the entry (deb, deb-src)
        uri -- the main repository uri (e.g. http://archive.ubuntu.com/ubuntu)
        dist -- the distribution to use (e.g. karmic, "/")
        comps -- a (possible empty) list of components (main, restricted)
        comment -- an (optional) comment
        sourcesfile -- an (optinal) filename in sources.list.d
        """
        trans.progress = 101
        trans.status = STATUS_COMMITTING

        if sourcesfile:
            if not sourcesfile.endswith(".list"):
                sourcesfile += ".list"
            dir = apt_pkg.config.find_dir("Dir::Etc::sourceparts")
            sourcesfile = os.path.join(dir, os.path.basename(sourcesfile))
        else:
            sourcesfile = None
        # Store any private login information in a separate auth.conf file
        if re.match("(http|https|ftp)://\S+?:\S+?@\S+", uri):
            uri = self._store_and_strip_password_from_uri(uri)
            auth_conf_path = apt_pkg.config.find_file("Dir::etc::netrc")
            if not comment:
                comment = "credentials stored in %s" % auth_conf_path
            else:
                comment += "; credentials stored in %s" % auth_conf_path
        try:
            sources = SourcesList()
            entry = sources.add(src_type, uri, dist, comps, comment,
                                file=sourcesfile)
            if entry.invalid:
                # FIXME: Introduce new error codes
                raise RepositoryInvalidError()
        except:
            log.exception("adding repository")
            raise
        else:
            sources.save()

    def _store_and_strip_password_from_uri(self, uri, auth_conf_path=None):
        """Extract the credentials from an URI. Store the password in
        auth.conf and return the URI without any password information.
        """
        try:
            res = urlsplit(uri)
        except ValueError as error:
            log.warning("Failed to urlsplit '%s'", error)
            return uri
        netloc_public = res.netloc.replace("%s:%s@" % (res.username,
                                                       res.password),
                                           "")
        machine = netloc_public + res.path
        # find auth.conf
        if auth_conf_path is None:
            auth_conf_path = apt_pkg.config.find_file("Dir::etc::netrc")

        # read all "machine"s from the auth.conf "netrc" file
        netrc_hosts = {}
        netrc_hosts_as_text = ""
        if os.path.exists(auth_conf_path):
                netrc_hosts = netrc.netrc(auth_conf_path).hosts
                with open(auth_conf_path, "rb") as f:
                    netrc_hosts_as_text = f.read().decode("UTF-8")

        # the new entry
        new_netrc_entry = "\nmachine %s login %s password %s\n" % (
            machine, res.username, res.password)
        # if there is the same machine already defined, update it
        # using a regexp this will ensure order/comments remain
        if machine in netrc_hosts:
            sub_regexp = r'machine\s+%s\s+login\s+%s\s+password\s+%s' % (
                re.escape(machine),
                re.escape(netrc_hosts[machine][0]),
                re.escape(netrc_hosts[machine][2]))
            replacement = 'machine %s login %s password %s' % (
                machine, res.username, res.password)
            # this may happen if e.g. the order is unexpected
            if not re.search(sub_regexp, netrc_hosts_as_text):
                log.warning("can not replace existing netrc entry for '%s' "
                            "prepending it instead" % machine)
                netrc_hosts_as_text = new_netrc_entry + netrc_hosts_as_text
            else:
                netrc_hosts_as_text = re.sub(
                    sub_regexp, replacement, netrc_hosts_as_text)
        else:
            netrc_hosts_as_text += new_netrc_entry

        # keep permssion bits of the file
        mode = 0o640
        try:
            mode = os.stat(auth_conf_path)[stat.ST_MODE]
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
        # write out, tmp file first plus rename to be atomic
        try:
            auth_conf_tmp = tempfile.NamedTemporaryFile(
                dir=os.path.dirname(auth_conf_path),
                prefix=os.path.basename(auth_conf_path),
                delete=False)
            auth_conf_tmp.write(netrc_hosts_as_text.encode('UTF-8'))
            auth_conf_tmp.close()
            os.rename(auth_conf_tmp.name, auth_conf_path)
            # and restore permissions (or set default ones)
            os.chmod(auth_conf_path, mode)
        except OSError as error:
            log.warning("Failed to write auth.conf: '%s'" % error)

        # Return URI without user/pass
        return urlunsplit((res.scheme, netloc_public, res.path, res.query,
                           res.fragment))

    def add_vendor_key_from_keyserver(self, trans, keyid, keyserver):
        """Add the signing key from the given (keyid, keyserver) to the
        trusted vendors.

        Keyword argument:
        trans -- the corresponding transaction
        keyid - the keyid of the key (e.g. 0x0EB12F05)
        keyserver - the keyserver (e.g. keyserver.ubuntu.com)
        """
        log.info("Adding vendor key from keyserver: %s %s", keyid, keyserver)
        # Perform some sanity checks
        try:
            res = urlsplit(keyserver)
        except ValueError:
            raise TransactionFailed(ERROR_KEY_NOT_INSTALLED,
                                    # TRANSLATORS: %s is the URL of GnuPG
                                    #             keyserver
                                    _("The keyserver URL is invalid: %s"),
                                    keyserver)
        if res.scheme not in ["hkp", "ldap", "ldaps", "http", "https"]:
            raise TransactionFailed(ERROR_KEY_NOT_INSTALLED,
                                    # TRANSLATORS: %s is the URL of GnuPG
                                    #             keyserver
                                    _("Invalid protocol of the server: %s"),
                                    keyserver)
        try:
            int(keyid, 16)
        except ValueError:
            raise TransactionFailed(ERROR_KEY_NOT_INSTALLED,
                                    # TRANSLATORS: %s is the id of a GnuPG key
                                    #             e.g. E08ADE95
                                    _("Invalid key id: %s"), keyid)
        trans.status = STATUS_DOWNLOADING
        trans.progress = 101
        with DaemonForkProgress(trans) as progress:
            progress.run(apt.auth.add_key_from_keyserver, keyid, keyserver)
        if progress._child_exit != 0:
            # TRANSLATORS: The first %s is the key id and the second the server
            raise TransactionFailed(ERROR_KEY_NOT_INSTALLED,
                                    _("Failed to download and install the key "
                                      "%s from %s:\n%s"),
                                    keyid, keyserver, progress.output)

    def add_vendor_key_from_file(self, trans, path):
        """Add the signing key from the given file to the trusted vendors.

        Keyword argument:
        path -- absolute path to the key file
        """
        log.info("Adding vendor key from file: %s", path)
        trans.progress = 101
        trans.status = STATUS_COMMITTING
        with DaemonForkProgress(trans) as progress:
            progress.run(apt.auth.add_key_from_file, path)
        if progress._child_exit != 0:
            raise TransactionFailed(ERROR_KEY_NOT_INSTALLED,
                                    _("Key file %s couldn't be installed: %s"),
                                    path, progress.output)

    def remove_vendor_key(self, trans, fingerprint):
        """Remove repository key.

        Keyword argument:
        trans -- the corresponding transaction
        fingerprint -- fingerprint of the key to remove
        """
        log.info("Removing vendor key: %s", fingerprint)
        trans.progress = 101
        trans.status = STATUS_COMMITTING
        try:
            int(fingerprint, 16)
        except ValueError:
            raise TransactionFailed(ERROR_KEY_NOT_REMOVED,
                                    # TRANSLATORS: %s is the id of a GnuPG key
                                    #             e.g. E08ADE95
                                    _("Invalid key id: %s"), fingerprint)
        with DaemonForkProgress(trans) as progress:
            progress.run(apt.auth.remove_key, fingerprint)
        if progress._child_exit != 0:
            raise TransactionFailed(ERROR_KEY_NOT_REMOVED,
                                    _("Key with fingerprint %s couldn't be "
                                      "removed: %s"),
                                    fingerprint, progress.output)

    def install_file(self, trans, path, force, simulate=False):
        """Install local package file.

        Keyword argument:
        trans -- the corresponding transaction
        path -- absolute path to the package file
        force -- if installing an invalid package is allowed
        simulate -- if True the changes won't be committed but the debfile
                    instance will be returned
        """
        log.info("Installing local package file: %s", path)
        # Check if the dpkg can be installed at all
        trans.status = STATUS_RESOLVING_DEP
        deb = self._check_deb_file(trans, path, force)
        # Check for required changes and apply them before
        (install, remove, unauth) = deb.required_changes
        self._call_plugins("modify_cache_after")
        if simulate:
            return deb
        with self._frozen_status():
            if len(install) > 0 or len(remove) > 0:
                self._apply_changes(trans, fetch_range=(15, 33),
                                    install_range=(34, 63))
            # Install the dpkg file
            deb_progress = DaemonDpkgInstallProgress(trans, begin=64, end=95)
            res = deb.install(deb_progress)
            trans.output += deb_progress.output
            if res:
                raise TransactionFailed(ERROR_PACKAGE_MANAGER_FAILED,
                                        trans.output)

    def _mark_packages_for_removal(self, packages, resolver, purge=False):
        """Mark packages for installation."""
        for pkg_name, pkg_ver, pkg_rel in [self._split_package_id(pkg)
                                           for pkg in packages]:
            try:
                pkg = self._cache[pkg_name]
            except KeyError:
                raise TransactionFailed(ERROR_NO_PACKAGE,
                                        _("Package %s isn't available"),
                                        pkg_name)
            if not pkg.is_installed and not pkg.installed_files:
                raise TransactionFailed(ERROR_PACKAGE_NOT_INSTALLED,
                                        _("Package %s isn't installed"),
                                        pkg_name)
            if pkg.essential is True:
                raise TransactionFailed(ERROR_NOT_REMOVE_ESSENTIAL_PACKAGE,
                                        _("Package %s cannot be removed."),
                                        pkg_name)
            if pkg_ver and pkg.installed != pkg_ver:
                raise TransactionFailed(ERROR_PACKAGE_NOT_INSTALLED,
                                        _("The version %s of %s is not "
                                          "installed"), pkg_ver, pkg_name)
            pkg.mark_delete(False, purge)
            resolver.clear(pkg)
            resolver.protect(pkg)
            resolver.remove(pkg)

    def _check_obsoleted_dependencies(self, trans, resolver=None):
        """Mark obsoleted dependencies of to be removed packages
        for removal.
        """
        if not trans.remove_obsoleted_depends:
            return
        if not resolver:
            resolver = apt.cache.ProblemResolver(self._cache)
        installed_deps = set()
        with self._cache.actiongroup():
            for pkg in self._cache.get_changes():
                if pkg.marked_delete:
                    installed_deps = self._installed_dependencies(
                        pkg.name, installed_deps)
            for dep_name in installed_deps:
                if dep_name in self._cache:
                    pkg = self._cache[dep_name]
                    if pkg.is_installed and pkg.is_auto_removable:
                        pkg.mark_delete(False)
            # do an additional resolver run to ensure that the autoremove
            # never leaves the cache in an inconsistent state, see bug
            # LP: #659111 for the rational, essentially this may happen
            # if a package is marked install during problem resolving but
            # is later no longer required. the resolver deals with that
            self._resolve_depends(trans, resolver)

    def _installed_dependencies(self, pkg_name, all_deps=None):
        """Recursively return all installed dependencies of a given package."""
        # FIXME: Should be part of python-apt, since it makes use of non-public
        #       API. Perhaps by adding a recursive argument to
        #       apt.package.Version.get_dependencies()
        if not all_deps:
            all_deps = set()
        if pkg_name not in self._cache:
            return all_deps
        cur = self._cache[pkg_name]._pkg.current_ver
        if not cur:
            return all_deps
        for sec in ("PreDepends", "Depends", "Recommends"):
            try:
                for dep in cur.depends_list[sec]:
                    dep_name = dep[0].target_pkg.name
                    if dep_name not in all_deps:
                        all_deps.add(dep_name)
                        all_deps |= self._installed_dependencies(dep_name,
                                                                 all_deps)
            except KeyError:
                pass
        return all_deps

    def _mark_packages_for_downgrade(self, packages, resolver):
        """Mark packages for downgrade."""
        for pkg_name, pkg_ver, pkg_rel in [self._split_package_id(pkg)
                                           for pkg in packages]:
            try:
                pkg = self._cache[pkg_name]
            except KeyError:
                raise TransactionFailed(ERROR_NO_PACKAGE,
                                        _("Package %s isn't available"),
                                        pkg_name)
            if not pkg.is_installed:
                raise TransactionFailed(ERROR_PACKAGE_NOT_INSTALLED,
                                        _("Package %s isn't installed"),
                                        pkg_name)
            auto = pkg.is_auto_installed
            pkg.mark_install(False, True, True)
            pkg.mark_auto(auto)
            resolver.clear(pkg)
            resolver.protect(pkg)
            if pkg_ver:
                if pkg.installed and pkg.installed.version < pkg_ver:
                    # FIXME: We need a new error enum
                    raise TransactionFailed(ERROR_NO_PACKAGE,
                                            _("The former version %s of %s "
                                              "is already installed"),
                                            pkg.installed.version, pkg.name)
                elif pkg.installed and pkg.installed.version == pkg_ver:
                    raise TransactionFailed(ERROR_PACKAGE_ALREADY_INSTALLED,
                                            _("The version %s of %s "
                                              "is already installed"),
                                            pkg.installed.version, pkg.name)
                try:
                    pkg.candidate = pkg.versions[pkg_ver]
                except KeyError:
                    raise TransactionFailed(ERROR_NO_PACKAGE,
                                            _("The version %s of %s isn't "
                                              "available"), pkg_ver, pkg_name)
            else:
                raise TransactionFailed(ERROR_NO_PACKAGE,
                                        _("You need to specify a version to "
                                          "downgrade %s to"),
                                        pkg_name)

    def _mark_packages_for_upgrade(self, packages, resolver):
        """Mark packages for upgrade."""
        for pkg_name, pkg_ver, pkg_rel in [self._split_package_id(pkg)
                                           for pkg in packages]:
            try:
                pkg = self._cache[pkg_name]
            except KeyError:
                raise TransactionFailed(ERROR_NO_PACKAGE,
                                        _("Package %s isn't available"),
                                        pkg_name)
            if not pkg.is_installed:
                raise TransactionFailed(ERROR_PACKAGE_NOT_INSTALLED,
                                        _("Package %s isn't installed"),
                                        pkg_name)
            auto = pkg.is_auto_installed
            pkg.mark_install(False, True, True)
            pkg.mark_auto(auto)
            resolver.clear(pkg)
            resolver.protect(pkg)
            if pkg_ver:
                if (pkg.installed and
                    apt_pkg.version_compare(pkg.installed.version,
                                            pkg_ver) == 1):
                    raise TransactionFailed(ERROR_PACKAGE_UPTODATE,
                                            _("The later version %s of %s "
                                              "is already installed"),
                                            pkg.installed.version, pkg.name)
                elif (pkg.installed and
                      apt_pkg.version_compare(pkg.installed.version,
                                              pkg_ver) == 0):
                    raise TransactionFailed(ERROR_PACKAGE_UPTODATE,
                                            _("The version %s of %s "
                                              "is already installed"),
                                            pkg.installed.version, pkg.name)
                try:
                    pkg.candidate = pkg.versions[pkg_ver]
                except KeyError:
                    raise TransactionFailed(ERROR_NO_PACKAGE,
                                            _("The version %s of %s isn't "
                                              "available."), pkg_ver, pkg_name)

            elif pkg_rel:
                self._set_candidate_release(pkg, pkg_rel)

    @staticmethod
    def _set_candidate_release(pkg, release):
        """Set the candidate of a package to the one from the given release."""
        # FIXME: Should be moved to python-apt
        # Check if the package is provided in the release
        for version in pkg.versions:
            if [origin for origin in version.origins
                    if origin.archive == release]:
                break
        else:
            raise TransactionFailed(ERROR_NO_PACKAGE,
                                    _("The package %s isn't available in "
                                      "the %s release."), pkg.name, release)
        pkg._pcache.cache_pre_change()
        pkg._pcache._depcache.set_candidate_release(pkg._pkg, version._cand,
                                                    release)
        pkg._pcache.cache_post_change()

    def update_cache(self, trans, sources_list):
        """Update the cache.

        Keyword arguments:
        trans -- the corresponding transaction
        sources_list -- only update the repositories found in the sources.list
                        snippet by the given file name.
        """

        def compare_pathes(first, second):
            """Small helper to compare two pathes."""
            return os.path.normpath(first) == os.path.normpath(second)

        log.info("Updating cache")

        progress = DaemonAcquireRepoProgress(trans, begin=10, end=90)
        if sources_list and not sources_list.startswith("/"):
            dir = apt_pkg.config.find_dir("Dir::Etc::sourceparts")
            sources_list = os.path.join(dir, sources_list)
        if sources_list:
            # For security reasons (LP #722228) we only allow files inside
            # sources.list.d as basedir
            basedir = apt_pkg.config.find_dir("Dir::Etc::sourceparts")
            system_sources = apt_pkg.config.find_file("Dir::Etc::sourcelist")
            if "/" in sources_list:
                sources_list = os.path.abspath(sources_list)
                # Check if the sources_list snippet is in the sourceparts
                # directory
                common_prefix = os.path.commonprefix([sources_list, basedir])
                if not (compare_pathes(common_prefix, basedir) or
                        compare_pathes(sources_list, system_sources)):
                    raise AptDaemonError("Only alternative sources.list files "
                                         "inside '%s' are allowed (not '%s')" %
                                         (basedir, sources_list))
            else:
                sources_list = os.path.join(basedir, sources_list)
        try:
            self._cache.update(progress, sources_list=sources_list)
        except apt.cache.FetchFailedException as error:
            # ListUpdate() method of apt handles a cancelled operation
            # as a failed one, see LP #162441
            if trans.cancelled:
                raise TransactionCancelled()
            else:
                raise TransactionFailed(ERROR_REPO_DOWNLOAD_FAILED,
                                        str(error))
        except apt.cache.FetchCancelledException:
            raise TransactionCancelled()
        except apt.cache.LockFailedException:
            raise TransactionFailed(ERROR_NO_LOCK)
        self._open_cache(trans, begin=91, end=95)

    def upgrade_system(self, trans, safe_mode=True, simulate=False):
        """Upgrade the system.

        Keyword argument:
        trans -- the corresponding transaction
        safe_mode -- if additional software should be installed or removed to
                     satisfy the dependencies the an updates
        simulate -- if the changes should not be applied
        """
        log.info("Upgrade system with safe mode: %s" % safe_mode)
        trans.status = STATUS_RESOLVING_DEP
        # FIXME: What to do if already uptotdate? Add error code?
        self._call_plugins("modify_cache_before")
        try:
            self._cache.upgrade(dist_upgrade=not safe_mode)
        except SystemError as excep:
            raise TransactionFailed(ERROR_DEP_RESOLUTION_FAILED, str(excep))
        self._call_plugins("modify_cache_after")
        self._check_obsoleted_dependencies(trans)
        if not simulate:
            self._apply_changes(trans)

    def fix_incomplete_install(self, trans):
        """Run dpkg --configure -a to recover from a failed installation.

        Keyword arguments:
        trans -- the corresponding transaction
        """
        log.info("Fixing incomplete installs")
        trans.status = STATUS_CLEANING_UP
        with self._frozen_status():
            with DaemonDpkgRecoverProgress(trans) as progress:
                progress.run()
        trans.output += progress.output
        if progress._child_exit != 0:
            raise TransactionFailed(ERROR_PACKAGE_MANAGER_FAILED,
                                    trans.output)

    def reconfigure(self, trans, packages, priority):
        """Run dpkg-reconfigure to reconfigure installed packages.

        Keyword arguments:
        trans -- the corresponding transaction
        packages -- list of packages to reconfigure
        priority -- the lowest priority of question which should be asked
        """
        log.info("Reconfiguring packages")
        with self._frozen_status():
            with DaemonDpkgReconfigureProgress(trans) as progress:
                progress.run(packages, priority)
        trans.output += progress.output
        if progress._child_exit != 0:
            raise TransactionFailed(ERROR_PACKAGE_MANAGER_FAILED,
                                    trans.output)

    def fix_broken_depends(self, trans, simulate=False):
        """Try to fix broken dependencies.

        Keyword arguments:
        trans -- the corresponding transaction
        simualte -- if the changes should not be applied
        """
        log.info("Fixing broken depends")
        trans.status = STATUS_RESOLVING_DEP
        try:
            self._cache._depcache.fix_broken()
        except SystemError:
            raise TransactionFailed(ERROR_DEP_RESOLUTION_FAILED,
                                    self._get_broken_details(trans))
        if not simulate:
            self._apply_changes(trans)

    def _open_cache(self, trans, begin=1, end=5, quiet=False, status=None):
        """Open the APT cache.

        Keyword arguments:
        trans -- the corresponding transaction
        start -- the begin of the progress range
        end -- the end of the the progress range
        quiet -- if True do no report any progress
        status -- an alternative dpkg status file
        """
        self.marked_tid = None
        trans.status = STATUS_LOADING_CACHE
        if not status:
            status = self._status_orig
        apt_pkg.config.set("Dir::State::status", status)
        apt_pkg.init_system()
        progress = DaemonOpenProgress(trans, begin=begin, end=end,
                                      quiet=quiet)
        try:
            if not isinstance(self._cache, apt.cache.Cache):
                self._cache = apt.cache.Cache(progress)
            else:
                self._cache.open(progress)
        except SystemError as excep:
            raise TransactionFailed(ERROR_NO_CACHE, str(excep))

    def is_dpkg_journal_clean(self):
        """Return False if there are traces of incomplete dpkg status
        updates."""
        status_updates = os.path.join(os.path.dirname(self._status_orig),
                                      "updates/")
        for dentry in os.listdir(status_updates):
            if dentry.isdigit():
                return False
        return True

    def _apply_changes(self, trans, fetch_range=(15, 50),
                       install_range=(50, 90)):
        """Apply previously marked changes to the system.

        Keyword arguments:
        trans -- the corresponding transaction
        fetch_range -- tuple containing the start and end point of the
                       download progress
        install_range -- tuple containing the start and end point of the
                         install progress
        """
        changes = self._cache.get_changes()
        if not changes:
            return
        # Do not allow to remove essential packages
        for pkg in changes:
            if pkg.marked_delete and (pkg.essential is True or
                                      (pkg.installed and
                                       pkg.installed.priority == "required") or
                                      pkg.name == "aptdaemon"):
                raise TransactionFailed(ERROR_NOT_REMOVE_ESSENTIAL_PACKAGE,
                                        _("Package %s cannot be removed"),
                                        pkg.name)
        # Check if any of the cache changes get installed from an
        # unauthenticated repository""
        if not trans.allow_unauthenticated and trans.unauthenticated:
            raise TransactionFailed(ERROR_PACKAGE_UNAUTHENTICATED,
                                    " ".join(sorted(trans.unauthenticated)))
        if trans.cancelled:
            raise TransactionCancelled()
        trans.cancellable = False
        fetch_progress = DaemonAcquireProgress(trans, begin=fetch_range[0],
                                               end=fetch_range[1])
        inst_progress = DaemonInstallProgress(trans, begin=install_range[0],
                                              end=install_range[1])
        with self._frozen_status():
            try:
                # This was backported as 
                if "allow_unauthenticated" in apt.Cache.commit.__doc__:
                    self._cache.commit(fetch_progress, inst_progress,
                                       allow_unauthenticated=trans.allow_unauthenticated)
                else:
                    self._cache.commit(fetch_progress, inst_progress)
            except apt.cache.FetchFailedException as error:
                raise TransactionFailed(ERROR_PACKAGE_DOWNLOAD_FAILED,
                                        str(error))
            except apt.cache.FetchCancelledException:
                raise TransactionCancelled()
            except SystemError as excep:
                # Run dpkg --configure -a to recover from a failed transaction
                trans.status = STATUS_CLEANING_UP
                with DaemonDpkgRecoverProgress(trans, begin=90, end=95) as pro:
                    pro.run()
                output = inst_progress.output + pro.output
                trans.output += output
                raise TransactionFailed(ERROR_PACKAGE_MANAGER_FAILED,
                                        "%s: %s" % (excep, trans.output))
            else:
                trans.output += inst_progress.output

    @contextlib.contextmanager
    def _frozen_status(self):
        """Freeze the status file to allow simulate operations during
        a dpkg call."""
        frozen_dir = tempfile.mkdtemp(prefix="aptdaemon-frozen-status")
        shutil.copy(self._status_orig, frozen_dir)
        self._status_frozen = os.path.join(frozen_dir, "status")
        try:
            yield
        finally:
            shutil.rmtree(frozen_dir)
            self._status_frozen = None

    def query(self, trans):
        """Process a PackageKit query transaction."""
        raise NotImplementedError

    def _simulate_transaction(self, trans):
        depends = [[], [], [], [], [], [], []]
        unauthenticated = []
        high_trust_packages = []
        skip_pkgs = []
        size = 0
        installs = reinstalls = removals = purges = upgrades = upgradables = \
            downgrades = []

        # Only handle transaction which change packages
        # FIXME: Add support for ROLE_FIX_INCOMPLETE_INSTALL
        if trans.role not in [ROLE_INSTALL_PACKAGES, ROLE_UPGRADE_PACKAGES,
                              ROLE_UPGRADE_SYSTEM, ROLE_REMOVE_PACKAGES,
                              ROLE_COMMIT_PACKAGES, ROLE_INSTALL_FILE,
                              ROLE_FIX_BROKEN_DEPENDS]:
            return depends, 0, 0, [], []

        # If a transaction is currently running use the former status file
        if self._status_frozen:
            status_path = self._status_frozen
        else:
            status_path = self._status_orig
        self._open_cache(trans, quiet=True, status=status_path)
        if trans.role == ROLE_FIX_BROKEN_DEPENDS:
            self.fix_broken_depends(trans, simulate=True)
        elif self._cache.broken_count:
            raise TransactionFailed(ERROR_CACHE_BROKEN,
                                    self._get_broken_details(trans))
        elif trans.role == ROLE_UPGRADE_SYSTEM:
            for pkg in self._iterate_packages():
                if pkg.is_upgradable:
                    upgradables.append(pkg)
            self.upgrade_system(trans, simulate=True, **trans.kwargs)
        elif trans.role == ROLE_INSTALL_FILE:
            deb = self.install_file(trans, simulate=True, **trans.kwargs)
            skip_pkgs.append(deb.pkgname)
            try:
                # Sometimes a thousands comma is used in packages
                # See LP #656633
                size = int(deb["Installed-Size"].replace(",", "")) * 1024
                # Some packages ship really large install sizes e.g.
                # openvpn access server, see LP #758837
                if size > sys.maxsize:
                    raise OverflowError("Size is too large: %s Bytes" % size)
            except (KeyError, AttributeError, ValueError, OverflowError):
                if not trans.kwargs["force"]:
                    msg = trans.gettext("The package doesn't provide a "
                                        "valid Installed-Size control "
                                        "field. See Debian Policy 5.6.20.")
                    raise TransactionFailed(ERROR_INVALID_PACKAGE_FILE, msg)
            try:
                pkg = self._cache[deb.pkgname]
            except KeyError:
                trans.packages = [[deb.pkgname], [], [], [], [], []]
            else:
                if pkg.is_installed:
                    # if we failed to get the size from the deb file do nor
                    # try to get the delta
                    if size != 0:
                        size -= pkg.installed.installed_size
                    trans.packages = [[], [deb.pkgname], [], [], [], []]
                else:
                    trans.packages = [[deb.pkgname], [], [], [], [], []]
        else:
            # FIXME: ugly code to get the names of the packages
            (installs, reinstalls, removals, purges,
             upgrades, downgrades) = [[re.split("(=|/)", entry, 1)[0]
                                       for entry in lst]
                                      for lst in trans.packages]
            self.commit_packages(trans, *trans.packages, simulate=True)

        changes = self._cache.get_changes()
        changes_names = []
        # get the additional dependencies
        for pkg in changes:
            if (pkg.marked_upgrade and pkg.is_installed and
                    pkg.name not in upgrades):
                pkg_str = "%s=%s" % (pkg.name, pkg.candidate.version)
                depends[PKGS_UPGRADE].append(pkg_str)
            elif pkg.marked_reinstall and pkg.name not in reinstalls:
                pkg_str = "%s=%s" % (pkg.name, pkg.candidate.version)
                depends[PKGS_REINSTALL].append(pkg_str)
            elif pkg.marked_downgrade and pkg.name not in downgrades:
                pkg_str = "%s=%s" % (pkg.name, pkg.candidate.version)
                depends[PKGS_DOWNGRADE].append(pkg_str)
            elif pkg.marked_install and pkg.name not in installs:
                pkg_str = "%s=%s" % (pkg.name, pkg.candidate.version)
                depends[PKGS_INSTALL].append(pkg_str)
            elif pkg.marked_delete and pkg.name not in removals:
                pkg_str = "%s=%s" % (pkg.name, pkg.installed.version)
                depends[PKGS_REMOVE].append(pkg_str)
            # FIXME: add support for purges
            changes_names.append(pkg.name)
        # get the unauthenticated packages
        unauthenticated = self._get_unauthenticated()
        high_trust_packages = self._get_high_trust_packages()
        # Check for skipped upgrades
        for pkg in upgradables:
            if pkg.marked_keep:
                pkg_str = "%s=%s" % (pkg.name, pkg.candidate.version)
                depends[PKGS_KEEP].append(pkg_str)

        # apt.cache.Cache.required_download requires a clean cache. Under some
        # strange circumstances it can fail (most likely an interrupted
        # debconf question), see LP#659438
        # Running dpkg --configure -a fixes the situation
        try:
            required_download = self._cache.required_download
        except SystemError as error:
            raise TransactionFailed(ERROR_INCOMPLETE_INSTALL, str(error))

        required_space = size + self._cache.required_space

        return (depends, required_download, required_space, unauthenticated,
                high_trust_packages)

    def _check_deb_file(self, trans, path, force):
        """Perform some basic checks for the Debian package.

        :param trans: The transaction instance.

        :returns: An apt.debfile.Debfile instance.
        """
        # This code runs as root for simulate and simulate requires no
        # authentication - so we need to ensure we do not leak information
        # about files here (LP: #1449587, CVE-2015-1323)
        #
        # Note that the actual lintian run is also droping privs (real,
        # not just seteuid)
        with set_euid_egid(trans.uid, trans.gid):
            if not os.path.isfile(path):
                raise TransactionFailed(ERROR_UNREADABLE_PACKAGE_FILE, path)

        if not force and os.path.isfile("/usr/bin/lintian"):
            with DaemonLintianProgress(trans) as progress:
                progress.run(path)
            # FIXME: Add an error to catch return state 2 (failure)
            if progress._child_exit != 0:
                raise TransactionFailed(ERROR_INVALID_PACKAGE_FILE,
                                        "Lintian check results for %s:"
                                        "\n%s" % (path, progress.output))
        try:
            deb = apt.debfile.DebPackage(path, self._cache)
        except IOError:
            raise TransactionFailed(ERROR_UNREADABLE_PACKAGE_FILE, path)
        except Exception as error:
            raise TransactionFailed(ERROR_INVALID_PACKAGE_FILE, str(error))
        try:
            ret = deb.check()
        except Exception as error:
            raise TransactionFailed(ERROR_DEP_RESOLUTION_FAILED, str(error))
        if not ret:
            raise TransactionFailed(ERROR_DEP_RESOLUTION_FAILED,
                                    deb._failure_string)
        return deb

    def clean(self, trans):
        """Clean the download directories.

        Keyword arguments:
        trans -- the corresponding transaction
        """
        # FIXME: Use pkgAcquire.Clean(). Currently not part of python-apt.
        trans.status = STATUS_CLEANING_UP
        archive_path = apt_pkg.config.find_dir("Dir::Cache::archives")
        for dir in [archive_path, os.path.join(archive_path, "partial")]:
            for filename in os.listdir(dir):
                if filename == "lock":
                    continue
                path = os.path.join(dir, filename)
                if os.path.isfile(path):
                    log.debug("Removing file %s", path)
                    os.remove(path)

    def add_license_key(self, trans, pkg_name, json_token, server_name):
        """Add a license key data to the given package.

        Keyword arguemnts:
        trans -- the coresponding transaction
        pkg_name -- the name of the corresponding package
        json_token -- the oauth token as json
        server_name -- the server to use (ubuntu-production, ubuntu-staging)
        """
        # set transaction state to downloading
        trans.status = STATUS_DOWNLOADING
        try:
            license_key, license_key_path = (
                self.plugins["get_license_key"][0](trans.uid, pkg_name,
                                                   json_token, server_name))
        except Exception as error:
            logging.exception("get_license_key plugin failed")
            raise TransactionFailed(ERROR_LICENSE_KEY_DOWNLOAD_FAILED,
                                    str(error))
        # ensure stuff is good
        if not license_key_path or not license_key:
            raise TransactionFailed(ERROR_LICENSE_KEY_DOWNLOAD_FAILED,
                                    _("The license key is empty"))

        # add license key if we have one
        self._add_license_key_to_system(pkg_name, license_key,
                                        license_key_path)

    def _add_license_key_to_system(self, pkg_name, license_key,
                                   license_key_path):
        # fixup path
        license_key_path = os.path.join(apt_pkg.config.find_dir("Dir"),
                                        license_key_path.lstrip("/"))

        # Check content of the key
        if (license_key.strip().startswith("#!") or
                license_key.startswith("\x7fELF")):
            raise TransactionFailed(ERROR_LICENSE_KEY_INSTALL_FAILED,
                                    _("The license key is not allowed to "
                                      "contain executable code."))
        # Check the path of the license
        license_key_path = os.path.normpath(license_key_path)
        license_key_path_rootdir = os.path.join(
            apt_pkg.config["Dir"], self.LICENSE_KEY_ROOTDIR.lstrip("/"),
            pkg_name)
        if not license_key_path.startswith(license_key_path_rootdir):
            raise TransactionFailed(ERROR_LICENSE_KEY_INSTALL_FAILED,
                                    _("The license key path %s is invalid"),
                                    license_key_path)
        if os.path.lexists(license_key_path):
            raise TransactionFailed(ERROR_LICENSE_KEY_INSTALL_FAILED,
                                    _("The license key already exists: %s"),
                                    license_key_path)
        # Symlink attacks!
        if os.path.realpath(license_key_path) != license_key_path:
            raise TransactionFailed(ERROR_LICENSE_KEY_INSTALL_FAILED,
                                    _("The location of the license key is "
                                      "unsecure since it contains symbolic "
                                      "links. The path %s maps to %s"),
                                    license_key_path,
                                    os.path.realpath(license_key_path))
        # Check if the directory already exists
        if not os.path.isdir(os.path.dirname(license_key_path)):
            raise TransactionFailed(ERROR_LICENSE_KEY_INSTALL_FAILED,
                                    _("The directory where to install the key "
                                      "to doesn't exist yet: %s"),
                                    license_key_path)
        # write it
        log.info("Writing license key to '%s'" % license_key_path)
        old_umask = os.umask(18)
        try:
            with open(license_key_path, "w") as license_file:
                license_file.write(license_key)
        except IOError:
            raise TransactionFailed(ERROR_LICENSE_KEY_INSTALL_FAILED,
                                    _("Failed to write key file to: %s"),
                                    license_key_path)
        finally:
            os.umask(old_umask)

    def _iterate_mainloop(self):
        """Process pending actions on the main loop."""
        while GLib.main_context_default().pending():
            GLib.main_context_default().iteration()

    def _iterate_packages(self, interval=1000):
        """Itarte von the packages of the cache and iterate on the
        GObject main loop time for more responsiveness.

        Keyword arguments:
        interval - the number of packages after which we iterate on the
            mainloop
        """
        for enum, pkg in enumerate(self._cache):
            if not enum % interval:
                self._iterate_mainloop()
            yield pkg

    def _get_broken_details(self, trans, now=True):
        """Return a message which provides debugging information about
        broken packages.

        This method is basically a Python implementation of apt-get.cc's
        ShowBroken.

        Keyword arguments:
        trans -- the corresponding transaction
        now -- if we check currently broken dependecies or the installation
               candidate
        """
        msg = trans.gettext("The following packages have unmet dependencies:")
        msg += "\n\n"
        for pkg in self._cache:
            if not ((now and pkg.is_now_broken) or
                    (not now and pkg.is_inst_broken)):
                continue
            msg += "%s: " % pkg.name
            if now:
                version = pkg.installed
            else:
                version = pkg.candidate
            indent = " " * (len(pkg.name) + 2)
            dep_msg = ""
            for dep in version.dependencies:
                or_msg = ""
                for base_dep in dep.or_dependencies:
                    if or_msg:
                        or_msg += "or\n"
                        or_msg += indent
                    # Check if it's an important dependency
                    # See apt-pkg/depcache.cc IsImportantDep
                    # See apt-pkg/pkgcache.cc IsCritical()
                    if not (base_dep.rawtype in ["Depends", "PreDepends",
                                                 "Obsoletes", "DpkgBreaks",
                                                 "Conflicts"] or
                            (apt_pkg.config.find_b("APT::Install-Recommends",
                                                   False) and
                            base_dep.rawtype == "Recommends") or
                            (apt_pkg.config.find_b("APT::Install-Suggests",
                                                   False) and
                             base_dep.rawtype == "Suggests")):
                        continue
                    # Get the version of the target package
                    try:
                        pkg_dep = self._cache[base_dep.name]
                    except KeyError:
                        dep_version = None
                    else:
                        if now:
                            dep_version = pkg_dep.installed
                        else:
                            dep_version = pkg_dep.candidate
                    # We only want to display dependencies which cannot
                    # be satisfied
                    if dep_version and not apt_pkg.check_dep(base_dep.version,
                                                             base_dep.relation,
                                                             version.version):
                        break
                    or_msg = "%s: %s " % (base_dep.rawtype, base_dep.name)
                    if base_dep.version:
                        or_msg += "(%s %s) " % (base_dep.relation,
                                                base_dep.version)
                    if self._cache.is_virtual_package(base_dep.name):
                        or_msg += trans.gettext("but it is a virtual package")
                    elif not dep_version:
                        if now:
                            or_msg += trans.gettext("but it is not installed")
                        else:
                            or_msg += trans.gettext("but it is not going to "
                                                    "be installed")
                    elif now:
                        # TRANSLATORS: %s is a version number
                        or_msg += (trans.gettext("but %s is installed") %
                                   dep_version.version)
                    else:
                        # TRANSLATORS: %s is a version number
                        or_msg += (trans.gettext("but %s is to be installed") %
                                   dep_version.version)
                else:
                    # Only append an or-group if at least one of the
                    # dependencies cannot be satisfied
                    if dep_msg:
                        dep_msg += indent
                    dep_msg += or_msg
                    dep_msg += "\n"
            msg += dep_msg
        return msg

    def is_reboot_required(self):
        """If a reboot is required to get all changes into effect."""
        return os.path.exists(os.path.join(apt_pkg.config.find_dir("Dir"),
                                           "var/run/reboot-required"))

    def set_config(self, option, value, filename=None):
        """Write a configuration value to file."""
        if option in ["AutoUpdateInterval", "AutoDownload",
                      "AutoCleanInterval", "UnattendedUpgrade"]:
            self._set_apt_config(option, value, filename)
        elif option == "PopConParticipation":
            self._set_popcon_pariticipation(value)

    def _set_apt_config(self, option, value, filename):
        config_writer = ConfigWriter()
        cw.set_value(option, value, filename)
        apt_pkg.init_config()

    def _set_popcon_participation(self, participate):
        if participate in [True, 1, "yes"]:
            value = "yes"
        else:
            value = "no"
        if os.path.exists(_POPCON_PATH):
            # read the current config and replace the corresponding settings
            # FIXME: Check if the config file is a valid bash script and
            #        contains the host_id
            with open(_POPCON_PATH) as conf_file:
                old_config = conf_file.read()
            config = re.sub(r'(PARTICIPATE=*)(".+?")',
                            '\\1"%s"' % value,
                            old_config)
        else:
            # create a new popcon config file
            m = md5()
            m.update(open("/dev/urandom", "r").read(1024))
            config = _POPCON_DEFAULT % {"host_id": m.hexdigest(),
                                        "participate": value}

        with open(_POPCON_PATH, "w") as conf_file:
            conf_file.write(config)

    def get_config(self, option):
        """Return a configuration value."""
        if option == "AutoUpdateInterval":
            key = "APT::Periodic::Update-Package-Lists"
            return apt_pkg.config.find_i(key, 0)
        elif option == "AutoDownload":
            key = "APT::Periodic::Download-Upgradeable-Packages"
            return apt_pkg.config.find_b(key, False)
        elif option == "AutoCleanInterval":
            key = "APT::Periodic::AutocleanInterval"
            return apt_pkg.config.find_i(key, 0)
        elif option == "UnattendedUpgrade":
            key = "APT::Periodic::Unattended-Upgrade"
            return apt_pkg.config.find_b(key, False)
        elif option == "GetPopconParticipation":
            return self._get_popcon_pariticipation()

    def _get_popcon_participation(self):
        # FIXME: Use a script to evaluate the configuration:
        #       #!/bin/sh
        #       . /etc/popularitiy-contest.conf
        #       . /usr/share/popularitiy-contest/default.conf
        #       echo $PARTICIAPTE $HOST_ID
        if os.path.exists(_POPCON_PATH):
            with open(_POPCON_PATH) as conf_file:
                config = conf_file.read()
            match = re.match("\nPARTICIPATE=\"(yes|no)\"", config)
            if match and match[0] == "yes":
                return True
        return False

    def get_trusted_vendor_keys(self):
        """Return a list of trusted GPG keys."""
        return [key.keyid for key in apt.auth.list_keys()]


# vim:ts=4:sw=4:et
