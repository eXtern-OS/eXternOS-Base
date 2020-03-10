# UpdateList.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2004-2013 Canonical
#
#  Author: Michael Vogt <mvo@debian.org>
#          Dylan McCall <dylanmccall@ubuntu.com>
#          Michael Terry <michael.terry@canonical.com>
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

from __future__ import print_function

import warnings
warnings.filterwarnings("ignore", "Accessed deprecated property",
                        DeprecationWarning)

from gettext import gettext as _
import apt
import logging
import itertools
import platform
import os
import random
import glob

from gi.repository import Gio

from UpdateManager.Core import utils


class UpdateItem():
    def __init__(self, pkg, name, icon, to_remove):
        self.icon = icon
        self.name = name
        self.pkg = pkg
        self.to_remove = to_remove

    def is_selected(self):
        if not self.to_remove:
            return self.pkg.marked_install or self.pkg.marked_upgrade
        else:
            return self.pkg.marked_delete


class UpdateGroup(UpdateItem):
    _depcache = {}

    def __init__(self, pkg, name, icon, to_remove):
        UpdateItem.__init__(self, pkg, name, icon, to_remove)
        self._items = set()
        self._deps = set()
        self.core_item = None
        if pkg is not None:
            self.core_item = UpdateItem(pkg, name, icon, to_remove)
            self._items.add(self.core_item)

    @property
    def items(self):
        all_items = []
        all_items.extend(self._items)
        return sorted(all_items, key=lambda a: a.name.lower())

    def add(self, pkg, cache=None, eventloop_callback=None, to_remove=False):
        name = utils.get_package_label(pkg)
        icon = Gio.ThemedIcon.new("package")
        self._items.add(UpdateItem(pkg, name, icon, to_remove))
        # If the pkg is in self._deps, stop here. We have already calculated
        # the recursive dependencies for this package, no need to do it again.
        if cache and pkg.name in cache and pkg.name not in self._deps:
            if not self._deps:
                # Initial deps haven't been calculated. As we're checking
                # whether _deps is empty in is_dependency, we must init now or
                # it won't be done at all.
                self._init_deps(cache, eventloop_callback)
            self._add_deps(pkg, cache, eventloop_callback)

    def contains(self, item):
        return item in self._items

    def _init_deps(self, cache, eventloop_callback):
        for item in self._items:
            if item.pkg and item.pkg.name not in self._deps:
                self._add_deps(item.pkg, cache, eventloop_callback)

    def _add_deps(self, pkg, cache, eventloop_callback):
        """Adds pkg and dependencies of pkg to the dependency list."""
        if pkg is None or pkg.candidate is None or pkg.name in self._deps:
            # This shouldn't really happen. If we land here often, it's a sign
            # that something has gone wrong. Unless all pkgs are None it's not
            # a critical issue - a hit to the performance at most.
            reason = ((not pkg or not pkg.candidate) and
                      "Package was None or didn't have a candidate." or
                      "%s already in _deps." % pkg.name)
            logging.debug("Useless call to _add_deps. %s" % reason)
            return
        if len(self._deps) % 200 == 0 and callable(eventloop_callback):
            # Don't spin the loop every time _add_deps is called.
            eventloop_callback()

        self._deps.add(pkg.name)

        if pkg.name in self._depcache:
            for dep in self._depcache[pkg.name]:
                if dep not in self._deps and dep in cache:
                    self._add_deps(cache[dep], cache, eventloop_callback)
        else:
            candidate = pkg.candidate
            dependencies = candidate.get_dependencies('Depends', 'Recommends')
            for dependency_pkg in itertools.chain.from_iterable(dependencies):
                name = dependency_pkg.name
                if name not in self._deps and name in cache:
                    self._depcache.setdefault(pkg.name, []).append(name)
                    self._add_deps(cache[name], cache, eventloop_callback)

    def is_dependency(self, maybe_dep, cache=None, eventloop_callback=None):
        if not self._deps and cache:
            self._init_deps(cache, eventloop_callback)

        return maybe_dep.name in self._deps

    def packages_are_selected(self):
        for item in self.items:
            if item.is_selected():
                return True
        return False

    def selection_is_inconsistent(self):
        pkgs_installing = [item for item in self.items if item.is_selected()]
        return (len(pkgs_installing) > 0 and
                len(pkgs_installing) < len(self.items))

    def get_total_size(self):
        if self.to_remove:
            return 0
        size = 0
        for item in self.items:
            size += getattr(item.pkg.candidate, "size", 0)
        return size


class UpdateApplicationGroup(UpdateGroup):
    def __init__(self, pkg, application, to_remove):
        name = application.get_display_name()
        icon = application.get_icon()
        super(UpdateApplicationGroup, self).__init__(pkg, name, icon,
                                                     to_remove)


class UpdatePackageGroup(UpdateGroup):
    def __init__(self, pkg, to_remove):
        name = utils.get_package_label(pkg)
        icon = Gio.ThemedIcon.new("package")
        super(UpdatePackageGroup, self).__init__(pkg, name, icon, to_remove)


class UpdateSystemGroup(UpdateGroup):
    def __init__(self, cache, to_remove):
        # Translators: the %s is a distro name, like 'Ubuntu' and 'base' as in
        # the core components and packages.
        name = _("%s base") % utils.get_ubuntu_flavor_name(cache=cache)
        icon = Gio.ThemedIcon.new("distributor-logo")
        super(UpdateSystemGroup, self).__init__(None, name, icon, to_remove)


class UpdateOrigin():
    def __init__(self, desc, importance):
        self.packages = []
        self.importance = importance
        self.description = desc


class UpdateList():
    """
    class that contains the list of available updates in
    self.pkgs[origin] where origin is the user readable string
    """

    # the key in the debian/control file used to add the phased
    # updates percentage
    PHASED_UPDATES_KEY = "Phased-Update-Percentage"

    # the file that contains the uniq machine id
    UNIQ_MACHINE_ID_FILE = "/etc/machine-id"
    # use the dbus one as a fallback
    UNIQ_MACHINE_ID_FILE_FALLBACK = "/var/lib/dbus/machine-id"

    APP_INSTALL_PATTERN = "/usr/share/app-install/desktop/%s:*.desktop"

    # the configuration key to turn phased-updates always on
    ALWAYS_INCLUDE_PHASED_UPDATES = (
        "Update-Manager::Always-Include-Phased-Updates")
    # ... or always off
    NEVER_INCLUDE_PHASED_UPDATES = (
        "Update-Manager::Never-Include-Phased-Updates")

    def __init__(self, parent, dist=None):
        self.dist = dist if dist else platform.dist()[2]
        self.distUpgradeWouldDelete = 0
        self.update_groups = []
        self.security_groups = []
        self.kernel_autoremove_groups = []
        self.num_updates = 0
        self.random = random.Random()
        self.ignored_phased_updates = []
        # a stable machine uniq id
        try:
            with open(self.UNIQ_MACHINE_ID_FILE) as f:
                self.machine_uniq_id = f.read()
        except FileNotFoundError:
            with open(self.UNIQ_MACHINE_ID_FILE_FALLBACK) as f:
                self.machine_uniq_id = f.read()

        if 'XDG_DATA_DIRS' in os.environ and os.environ['XDG_DATA_DIRS']:
            data_dirs = os.environ['XDG_DATA_DIRS']
        else:
            data_dirs = '/usr/local/share/:/usr/share/'
        self.application_dirs = [os.path.join(base, 'applications')
                                 for base in data_dirs.split(':')]

        if 'XDG_CURRENT_DESKTOP' in os.environ:
            self.current_desktop = os.environ.get('XDG_CURRENT_DESKTOP')
        else:
            self.current_desktop = ''
        self.desktop_cache = {}

    def _file_is_application(self, file_path):
        # WARNING: This is called often if there's a lot of updates. A poor
        # performing call here has a huge impact on the overall performance!
        if not file_path.endswith(".desktop"):
            # First the obvious case: If the path doesn't end in a .desktop
            # extension, this isn't a desktop file.
            return False

        file_path = os.path.abspath(file_path)
        for app_dir in self.application_dirs:
            if file_path.startswith(app_dir):
                return True
        return False

    def _rate_application_for_package(self, application, pkg):
        score = 0
        desktop_file = os.path.basename(application.get_filename())
        application_id = os.path.splitext(desktop_file)[0]

        if application.should_show():
            score += 1

            if application_id == pkg.name:
                score += 5

        return score

    def _get_application_for_package(self, pkg):
        desktop_files = []
        rated_applications = []

        for installed_file in pkg.installed_files:
            if self._file_is_application(installed_file):
                desktop_files.append(installed_file)

        if pkg.name in self.desktop_cache:
            desktop_files += self.desktop_cache[pkg.name]

        for desktop_file in desktop_files:
            try:
                application = Gio.DesktopAppInfo.new_from_filename(
                    desktop_file)
                application.set_desktop_env(self.current_desktop)
            except Exception as e:
                logging.warning("Error loading .desktop file %s: %s" %
                                (desktop_file, e))
                continue
            score = self._rate_application_for_package(application, pkg)
            if score > 0:
                rated_applications.append((score, application))

        rated_applications.sort(key=lambda app: app[0], reverse=True)
        if len(rated_applications) > 0:
            return rated_applications[0][1]
        else:
            return None

    def _populate_desktop_cache(self, pkg_names):
        if not pkg_names:
            # No updates; This shouldn't have happened.
            logging.warning("_populate_desktop_cache called with empty list "
                            "of packages.")
            return
        elif len(pkg_names) == 1:
            # One update; Let glob do the matching.
            pattern = self.APP_INSTALL_PATTERN % pkg_names[0]
        else:
            # More than one update available. Glob all desktop files and store
            # those that match an upgradeable package.
            pattern = self.APP_INSTALL_PATTERN % "*"

        for desktop_file in glob.iglob(pattern):
            try:
                pkg = desktop_file.split('/')[-1].split(":")[0]
            except IndexError:
                # app-install-data desktop file had an unexpected naming
                # convention. As we can't extract the package name from
                # the path, just ignore it.
                logging.error("Could not extract package name from '%s'. "
                              "File ignored." % desktop_file)
                continue

            if pkg in pkg_names:
                self.desktop_cache.setdefault(pkg, []).append(desktop_file)
                logging.debug("App candidate for %s: %s" %
                              (pkg, desktop_file))

    def _is_security_update(self, pkg):
        """ This will test if the pkg is a security update.
            This includes if there is a newer version in -updates, but also
            an older update available in -security.  For example, if
            installed pkg A v1.0 is available in both -updates (as v1.2) and
            -security (v1.1). we want to display it as a security update.

            :return: True if the update comes from the security pocket
        """
        if not self.dist:
            return False
        inst_ver = pkg._pkg.current_ver
        for ver in pkg._pkg.version_list:
            # discard is < than installed ver
            if (inst_ver and
                    apt.apt_pkg.version_compare(ver.ver_str,
                                                inst_ver.ver_str) <= 0):
                continue
            # check if we have a match
            for (verFileIter, index) in ver.file_list:
                if verFileIter.archive == "%s-security" % self.dist and \
                        verFileIter.origin == "Ubuntu":
                    indexfile = pkg._pcache._list.find_index(verFileIter)
                    if indexfile:  # and indexfile.IsTrusted:
                        return True
        return False

    def _is_ignored_phased_update(self, pkg):
        """ This will test if the pkg is a phased update and if
            it needs to get installed or ignored.

            :return: True if the updates should be ignored
        """
        # allow the admin to override this
        if apt.apt_pkg.config.find_b(
                self.ALWAYS_INCLUDE_PHASED_UPDATES, False):
            return False

        if self.PHASED_UPDATES_KEY in pkg.candidate.record:
            if apt.apt_pkg.config.find_b(
                    self.NEVER_INCLUDE_PHASED_UPDATES, False):
                logging.info("holding back phased update per configuration")
                return True

            # its important that we always get the same result on
            # multiple runs of the update-manager, so we need to
            # feed a seed that is a combination of the pkg/ver/machine
            self.random.seed("%s-%s-%s" % (
                pkg.candidate.source_name, pkg.candidate.version,
                self.machine_uniq_id))
            threshold = pkg.candidate.record[self.PHASED_UPDATES_KEY]
            percentage = self.random.randint(0, 100)
            if percentage > int(threshold):
                logging.info("holding back phased update %s (%s < %s)" % (
                    pkg.name, threshold, percentage))
                return True
        return False

    def _get_linux_packages(self):
        "Return all binary packages made by the linux-meta source package"
        # Hard code this rather than generate from source info in cache because
        # that might only be available if we have deb-src lines.  I think we
        # could also generate it by iterating over all the binary package info
        # we have, but that is costly.  These don't change often.
        return ['linux',
                'linux-cloud-tools-generic',
                'linux-cloud-tools-lowlatency',
                'linux-cloud-tools-virtual',
                'linux-crashdump',
                'linux-generic',
                'linux-generic-lpae',
                'linux-headers-generic',
                'linux-headers-generic-lpae',
                'linux-headers-lowlatency',
                'linux-headers-lowlatency-lpae',
                'linux-headers-server',
                'linux-headers-virtual',
                'linux-image',
                'linux-image-extra-virtual',
                'linux-image-generic',
                'linux-image-generic-lpae',
                'linux-image-lowlatency',
                'linux-image-virtual',
                'linux-lowlatency',
                'linux-signed-generic',
                'linux-signed-image-generic',
                'linux-signed-image-lowlatency',
                'linux-signed-lowlatency',
                'linux-source',
                'linux-tools-generic',
                'linux-tools-generic-lpae',
                'linux-tools-lowlatency',
                'linux-tools-virtual',
                'linux-virtual']

    def _make_groups(self, cache, pkgs, eventloop_callback, to_remove=False):
        if not pkgs:
            return []
        ungrouped_pkgs = []
        app_groups = []
        pkg_groups = []

        for pkg in pkgs:
            app = self._get_application_for_package(pkg)
            if app is not None:
                app_group = UpdateApplicationGroup(pkg, app, to_remove)
                app_groups.append(app_group)
            else:
                ungrouped_pkgs.append(pkg)

        # Stick together applications and their immediate dependencies
        for pkg in list(ungrouped_pkgs):
            dep_groups = []
            for group in app_groups:
                if group.is_dependency(pkg, cache, eventloop_callback):
                    dep_groups.append(group)
                    if len(dep_groups) > 1:
                        break
            if len(dep_groups) == 1:
                dep_groups[0].add(pkg, cache, eventloop_callback, to_remove)
                ungrouped_pkgs.remove(pkg)

        system_group = None
        if ungrouped_pkgs:
            # Separate out system base packages. If we have already found an
            # application for all updates, don't bother.
            meta_group = UpdateGroup(None, None, None, to_remove)
            flavor_package = utils.get_ubuntu_flavor_package(cache=cache)
            meta_pkgs = [flavor_package, "ubuntu-standard", "ubuntu-minimal"]
            meta_pkgs.extend(self._get_linux_packages())
            for pkg in meta_pkgs:
                if pkg in cache:
                    meta_group.add(cache[pkg])
            for pkg in ungrouped_pkgs:
                if meta_group.is_dependency(pkg, cache, eventloop_callback):
                    if system_group is None:
                        system_group = UpdateSystemGroup(cache, to_remove)
                    system_group.add(pkg)
                else:
                    pkg_groups.append(UpdatePackageGroup(pkg, to_remove))

        app_groups.sort(key=lambda a: a.name.lower())
        pkg_groups.sort(key=lambda a: a.name.lower())
        if system_group:
            pkg_groups.append(system_group)

        return app_groups + pkg_groups

    def update(self, cache, eventloop_callback=None):
        self.held_back = []

        # do the upgrade
        self.distUpgradeWouldDelete = cache.saveDistUpgrade()

        security_pkgs = []
        upgrade_pkgs = []
        kernel_autoremove_pkgs = []

        # Find all upgradable packages
        for pkg in cache:
            if pkg.is_upgradable or pkg.marked_install:
                if getattr(pkg.candidate, "origins", None) is None:
                    # can happen for e.g. locked packages
                    # FIXME: do something more sensible here (but what?)
                    print("WARNING: upgradable but no candidate.origins?!?: ",
                          pkg.name)
                    continue

                # see if its a phased update and *not* a security update
                # keep track of packages for which the update percentage was
                # not met for testing
                is_security_update = self._is_security_update(pkg)
                if not is_security_update:
                    if self._is_ignored_phased_update(pkg):
                        self.ignored_phased_updates.append(pkg)
                        continue

                if is_security_update:
                    security_pkgs.append(pkg)
                else:
                    upgrade_pkgs.append(pkg)
                self.num_updates = self.num_updates + 1

            if pkg.is_upgradable and not (pkg.marked_upgrade or
                                          pkg.marked_install):
                self.held_back.append(pkg.name)
                continue
            if (pkg.is_auto_removable and
                (cache.versioned_kernel_pkgs_regexp and
                 cache.versioned_kernel_pkgs_regexp.match(pkg.name) and
                 not cache.running_kernel_pkgs_regexp.match(pkg.name))):
                kernel_autoremove_pkgs.append(pkg)

        # perform operations after the loop to not skip packages which
        # changed state due to the resolver
        for pkg in kernel_autoremove_pkgs:
            pkg.mark_delete()
        for pkg in self.ignored_phased_updates:
            pkg.mark_keep()

        if security_pkgs or upgrade_pkgs:
            # There's updates available. Initiate the desktop file cache.
            pkg_names = [p.name for p in
                         security_pkgs + upgrade_pkgs + kernel_autoremove_pkgs]
            self._populate_desktop_cache(pkg_names)
        self.update_groups = self._make_groups(cache, upgrade_pkgs,
                                               eventloop_callback)
        self.security_groups = self._make_groups(cache, security_pkgs,
                                                 eventloop_callback)
        self.kernel_autoremove_groups = self._make_groups(
            cache, kernel_autoremove_pkgs, eventloop_callback, True)
