#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""enums - Enumerates for apt daemon dbus messages"""
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

__all__ = ("PKGS_INSTALL", "PKGS_REINSTALL", "PKGS_REMOVE", "PKGS_PURGE",
           "PKGS_UPGRADE", "PKGS_DOWNGRADE", "PKGS_KEEP",
           "EXIT_SUCCESS", "EXIT_CANCELLED", "EXIT_FAILED", "EXIT_UNFINISHED",
           "ERROR_PACKAGE_DOWNLOAD_FAILED", "ERROR_REPO_DOWNLOAD_FAILED",
           "ERROR_DEP_RESOLUTION_FAILED",
           "ERROR_KEY_NOT_INSTALLED", "ERROR_KEY_NOT_REMOVED", "ERROR_NO_LOCK",
           "ERROR_NO_CACHE", "ERROR_NO_PACKAGE", "ERROR_PACKAGE_UPTODATE",
           "ERROR_PACKAGE_NOT_INSTALLED", "ERROR_PACKAGE_ALREADY_INSTALLED",
           "ERROR_NOT_REMOVE_ESSENTIAL_PACKAGE", "ERROR_DAEMON_DIED",
           "ERROR_PACKAGE_MANAGER_FAILED", "ERROR_CACHE_BROKEN",
           "ERROR_PACKAGE_UNAUTHENTICATED", "ERROR_INCOMPLETE_INSTALL",
           "ERROR_UNREADABLE_PACKAGE_FILE", "ERROR_INVALID_PACKAGE_FILE",
           "ERROR_SYSTEM_ALREADY_UPTODATE", "ERROR_NOT_SUPPORTED",
           "ERROR_LICENSE_KEY_INSTALL_FAILED",
           "ERROR_LICENSE_KEY_DOWNLOAD_FAILED",
           "ERROR_AUTH_FAILED", "ERROR_NOT_AUTHORIZED",
           "ERROR_UNKNOWN",
           "STATUS_SETTING_UP", "STATUS_WAITING", "STATUS_WAITING_MEDIUM",
           "STATUS_WAITING_CONFIG_FILE_PROMPT", "STATUS_WAITING_LOCK",
           "STATUS_RUNNING", "STATUS_LOADING_CACHE", "STATUS_DOWNLOADING",
           "STATUS_COMMITTING", "STATUS_CLEANING_UP", "STATUS_RESOLVING_DEP",
           "STATUS_FINISHED", "STATUS_CANCELLING", "STATUS_QUERY",
           "STATUS_DOWNLOADING_REPO", "STATUS_AUTHENTICATING",
           "ROLE_UNSET", "ROLE_INSTALL_PACKAGES", "ROLE_INSTALL_FILE",
           "ROLE_UPGRADE_PACKAGES", "ROLE_UPGRADE_SYSTEM", "ROLE_UPDATE_CACHE",
           "ROLE_REMOVE_PACKAGES", "ROLE_COMMIT_PACKAGES",
           "ROLE_ADD_VENDOR_KEY_FILE", "ROLE_ADD_VENDOR_KEY_FROM_KEYSERVER",
           "ROLE_REMOVE_VENDOR_KEY", "ROLE_FIX_INCOMPLETE_INSTALL",
           "ROLE_FIX_BROKEN_DEPENDS", "ROLE_ADD_REPOSITORY",
           "ROLE_ENABLE_DISTRO_COMP", "ROLE_CLEAN", "ROLE_RECONFIGURE",
           "ROLE_PK_QUERY", "ROLE_ADD_LICENSE_KEY",
           "DOWNLOAD_DONE", "DOWNLOAD_AUTH_ERROR", "DOWNLOAD_ERROR",
           "DOWNLOAD_FETCHING", "DOWNLOAD_IDLE", "DOWNLOAD_NETWORK_ERROR",
           "PKG_INSTALLING", "PKG_CONFIGURING", "PKG_REMOVING",
           "PKG_PURGING", "PKG_UPGRADING", "PKG_RUNNING_TRIGGER",
           "PKG_DISAPPEARING", "PKG_PREPARING_REMOVE", "PKG_PREPARING_INSTALL",
           "PKG_PREPARING_PURGE", "PKG_PREPARING_PURGE", "PKG_INSTALLED",
           "PKG_REMOVED", "PKG_PURGED", "PKG_UNPACKING", "PKG_UNKNOWN",
           "get_status_icon_name_from_enum", "get_role_icon_name_from_enum",
           "get_status_animation_name_from_enum",
           "get_package_status_from_enum",
           "get_role_localised_past_from_enum", "get_exit_string_from_enum",
           "get_role_localised_present_from_enum", "get_role_error_from_enum",
           "get_error_description_from_enum", "get_error_string_from_enum",
           "get_status_string_from_enum", "get_download_status_from_enum")

import gettext


def _(msg):
    return gettext.dgettext("aptdaemon", msg)

# PACKAGE GROUP INDEXES
#: Index of the list of to be installed packages in the :attr:`dependencies`
#: and :attr:`packages` property of :class:`~aptdaemon.client.AptTransaction`.
PKGS_INSTALL = 0
#: Index of the list of to be re-installed packages in the :attr:`dependencies`
#: and :attr:`packages` property of :class:`~aptdaemon.client.AptTransaction`.
PKGS_REINSTALL = 1
#: Index of the list of to be removed packages in the :attr:`dependencies`
#: and :attr:`packages` property of :class:`~aptdaemon.client.AptTransaction`.
PKGS_REMOVE = 2
#: Index of the list of to be purged packages in the :attr:`dependencies`
#: and :attr:`packages` property of :class:`~aptdaemon.client.AptTransaction`.
PKGS_PURGE = 3
#: Index of the list of to be upgraded packages in the :attr:`dependencies`
#: and :attr:`packages` property of :class:`~aptdaemon.client.AptTransaction`.
PKGS_UPGRADE = 4
#: Index of the list of to be downgraded packages in the :attr:`dependencies`
#: and :attr:`packages` property of :class:`~aptdaemon.client.AptTransaction`.
PKGS_DOWNGRADE = 5
#: Index of the list of to be keept packages in the :attr:`dependencies`
#: property of :class:`~aptdaemon.client.AptTransaction`.
PKGS_KEEP = 6

# FINISH STATES
#: The transaction was successful.
EXIT_SUCCESS = "exit-success"
#: The transaction has been cancelled by the user.
EXIT_CANCELLED = "exit-cancelled"
#: The transaction has failed.
EXIT_FAILED = "exit-failed"
#: The transaction failed since a previous one in a chain failed.
EXIT_PREVIOUS_FAILED = "exit-previous-failed"
#: The transaction is still being queued or processed.
EXIT_UNFINISHED = "exit-unfinished"

# ERROR CODES
#: Failed to download package files which should be installed.
ERROR_PACKAGE_DOWNLOAD_FAILED = "error-package-download-failed"
#: Failed to download package information (index files) from the repositories
ERROR_REPO_DOWNLOAD_FAILED = "error-repo-download-failed"
#: Failed to satisfy the dependencies or conflicts of packages.
ERROR_DEP_RESOLUTION_FAILED = "error-dep-resolution-failed"
#: The requested vendor key is not installed.
ERROR_KEY_NOT_INSTALLED = "error-key-not-installed"
#: The requested vendor could not be removed.
ERROR_KEY_NOT_REMOVED = "error-key-not-removed"
#: The package management system could not be locked. Eventually another
#: package manager is running.
ERROR_NO_LOCK = "error-no-lock"
#: The package cache could not be opened. This indicates a serious problem
#: on the system.
ERROR_NO_CACHE = "error-no-cache"
#: The requested package is not available.
ERROR_NO_PACKAGE = "error-no-package"
#: The package could not be upgraded since it is already up-to-date.
ERROR_PACKAGE_UPTODATE = "error-package-uptodate"
#: The package which was requested to install is already installed.
ERROR_PACKAGE_ALREADY_INSTALLED = "error-package-already-installed"
#: The package could not be removed since it is not installed.
ERROR_PACKAGE_NOT_INSTALLED = "error-package-not-installed"
#: It is not allowed to remove an essential system package.
ERROR_NOT_REMOVE_ESSENTIAL_PACKAGE = "error-not-remove-essential"
#: The aptdaemon crashed or could not be connected to on the D-Bus.
ERROR_DAEMON_DIED = "error-daemon-died"
#: On of the maintainer scripts during the dpkg call failed.
ERROR_PACKAGE_MANAGER_FAILED = "error-package-manager-failed"
#: There are packages with broken dependencies installed on the system.
#: This has to fixed before performing another transaction.
ERROR_CACHE_BROKEN = "error-cache-broken"
#: It is not allowed to install an unauthenticated packages. Packages are
#: authenticated by installing the vendor key.
ERROR_PACKAGE_UNAUTHENTICATED = "error-package-unauthenticated"
#: A previous installation has been aborted and is now incomplete.
#: Should be fixed by `dpkg --configure -a` or the :func:`FixIncomplete()`
#: transaction.
ERROR_INCOMPLETE_INSTALL = "error-incomplete-install"
#: Failed to open and read the package file
ERROR_UNREADABLE_PACKAGE_FILE = "error-unreadable-package-file"
#: The package file violates the Debian/Ubuntu policy
ERROR_INVALID_PACKAGE_FILE = "error-invalid-package-file"
#: The requested feature is not supported yet (mainly used by PackageKit
ERROR_NOT_SUPPORTED = "error-not-supported"
#: The license key download failed
ERROR_LICENSE_KEY_DOWNLOAD_FAILED = "error-license-key-download-failed"
#: The license key is invalid
ERROR_LICENSE_KEY_INSTALL_FAILED = "error-license-key-install-failed"
#: The system is already up-to-date and don't needs any upgrades
ERROR_SYSTEM_ALREADY_UPTODATE = "error-system-already-uptodate"
#: The user isn't allowed to perform the action at all
ERROR_NOT_AUTHORIZED = "error-not-authorized"
#: The user could not be authorized (e.g. wrong password)
ERROR_AUTH_FAILED = "error-auth-failed"
#: An unknown error occured. In most cases these are programming ones.
ERROR_UNKNOWN = "error-unknown"

# TRANSACTION STATES
#: The transaction was created, but hasn't been queued.
STATUS_SETTING_UP = "status-setting-up"
#: The transaction performs a query
STATUS_QUERY = "status-query"
#: The transaction is waiting in the queue.
STATUS_WAITING = "status-waiting"
#: The transaction is paused and waits until a required medium is inserted.
#: See :func:`ProvideMedium()`.
STATUS_WAITING_MEDIUM = "status-waiting-medium"
#: The transaction is paused and waits for the user to resolve a configuration
#: file conflict. See :func:`ResolveConfigFileConflict()`.
STATUS_WAITING_CONFIG_FILE_PROMPT = "status-waiting-config-file-prompt"
#: Wait until the package management system can be locked. Most likely
#: another package manager is running currently.
STATUS_WAITING_LOCK = "status-waiting-lock"
#: The processing of the transaction has started.
STATUS_RUNNING = "status-running"
#: The package cache is opened.
STATUS_LOADING_CACHE = "status-loading-cache"
#: The information about available packages is downloaded
STATUS_DOWNLOADING_REPO = "status-downloading-repo"
#: The required package files to install are getting downloaded.
STATUS_DOWNLOADING = "status-downloading"
#: The actual installation/removal takes place.
STATUS_COMMITTING = "status-committing"
#: The package management system is cleaned up.
STATUS_CLEANING_UP = "status-cleaning-up"
#: The dependecies and conflicts are now getting resolved.
STATUS_RESOLVING_DEP = "status-resolving-dep"
#: The transaction has been completed.
STATUS_FINISHED = "status-finished"
#: The transaction has been cancelled.
STATUS_CANCELLING = "status-cancelling"
#: The transaction waits for authentication
STATUS_AUTHENTICATING = "status-authenticating"

# PACKAGE STATES
#: The package gets unpacked
PKG_UNPACKING = "pkg-unpacking"
#: The installation of the package gets prepared
PKG_PREPARING_INSTALL = "pkg-preparing-install"
#: The package is installed
PKG_INSTALLED = "pkg-installed"
#: The package gets installed
PKG_INSTALLING = "pkg-installing"
#: The configuration of the package gets prepared
PKG_PREPARING_CONFIGURE = "pkg-preparing-configure"
#: The package gets configured
PKG_CONFIGURING = "pkg-configuring"
#: The removal of the package gets prepared
PKG_PREPARING_REMOVE = "pkg-preparing-removal"
#: The package gets removed
PKG_REMOVING = "pkg-removing"
#: The package is removed
PKG_REMOVED = "pkg-removed"
#: The purging of the package gets prepared
PKG_PREPARING_PURGE = "pkg-preparing-purge"
#: The package gets purged
PKG_PURGING = "pkg-purging"
#: The package was completely removed
PKG_PURGED = "pkg-purged"
#: The post installation trigger of the package is processed
PKG_RUNNING_TRIGGER = "pkg-running-trigger"
#: The package disappered - very rare
PKG_DISAPPEARING = "pkg-disappearing"
#: The package gets upgraded
PKG_UPGRADING = "pkg-upgrading"
#: Failed to get a current status of the package
PKG_UNKNOWN = "pkg-unknown"

# TRANSACTION ROLES
#: The role of the transaction has not been specified yet.
ROLE_UNSET = "role-unset"
#: The transaction performs a query compatible to the PackageKit interface
ROLE_PK_QUERY = "role-pk-query"
#: The transaction will install one or more packages.
ROLE_INSTALL_PACKAGES = "role-install-packages"
#: The transaction will install a local package file.
ROLE_INSTALL_FILE = "role-install-file"
#: The transaction will upgrade one or more packages.
ROLE_UPGRADE_PACKAGES = "role-upgrade-packages"
#: The transaction will perform a system upgrade.
ROLE_UPGRADE_SYSTEM = "role-upgrade-system"
#: The transaction will update the package cache.
ROLE_UPDATE_CACHE = "role-update-cache"
#: The transaction will remove one or more packages.
ROLE_REMOVE_PACKAGES = "role-remove-packages"
#: The transaction will perform a combined install, remove, upgrade or
#: downgrade action.
ROLE_COMMIT_PACKAGES = "role-commit-packages"
#: The transaction will add a local vendor key file to authenticate packages.
ROLE_ADD_VENDOR_KEY_FILE = "role-add-vendor-key-file"
#: The transaction will download vendor key to authenticate packages from
#: a keyserver.
ROLE_ADD_VENDOR_KEY_FROM_KEYSERVER = "role-add-vendor-key-from-keyserver"
#: The transaction will remove a vendor key which was used to authenticate
#: packages.
ROLE_REMOVE_VENDOR_KEY = "role-remove-vendor-key"
#: The transaction will try to finish a previous aborted installation.
ROLE_FIX_INCOMPLETE_INSTALL = "role-fix-incomplete-install"
#: The transaction will to resolve broken dependencies of already installed
#: packages.
ROLE_FIX_BROKEN_DEPENDS = "role-fix-broken-depends"
#: The transaction will enable a repository to download software from.
ROLE_ADD_REPOSITORY = "role-add-repository"
#: The transaction will enable a component in the distro repositories,
#: e.g main or universe
ROLE_ENABLE_DISTRO_COMP = "role-enable-distro-comp"
#: The transaction will reconfigure the given already installed packages
ROLE_RECONFIGURE = "role-reconfigure"
#: The transaction will remove all downloaded package files.
ROLE_CLEAN = "role-clean"
#: The transaction will add a license key to the system
ROLE_ADD_LICENSE_KEY = "role-add-license-key"

# DOWNLOAD STATES
#: The download has been completed.
DOWNLOAD_DONE = "download-done"
#: The file could not be downloaded since the authentication for the repository
#: failed.
DOWNLOAD_AUTH_ERROR = "download-auth-error"
#: There file could not be downloaded, e.g. because it is not available (404).
DOWNLOAD_ERROR = "download-error"
#: The file is currently being downloaded.
DOWNLOAD_FETCHING = "download-fetching"
#: The download is currently idling.
DOWNLOAD_IDLE = "download-idle"
#: The download failed since there seem to be a networking problem.
DOWNLOAD_NETWORK_ERROR = "download-network-error"

_ICONS_STATUS = {
    STATUS_CANCELLING: 'aptdaemon-cleanup',
    STATUS_CLEANING_UP: 'aptdaemon-cleanup',
    STATUS_RESOLVING_DEP: 'aptdaemon-resolve',
    STATUS_COMMITTING: 'aptdaemon-working',
    STATUS_DOWNLOADING: 'aptdaemon-download',
    STATUS_DOWNLOADING_REPO: 'aptdaemon-download',
    STATUS_FINISHED: 'aptdaemon-cleanup',
    STATUS_LOADING_CACHE: 'aptdaemon-update-cache',
    STATUS_RUNNING: 'aptdaemon-working',
    STATUS_SETTING_UP: 'aptdaemon-working',
    STATUS_WAITING: 'aptdaemon-wait',
    STATUS_WAITING_LOCK: 'aptdaemon-wait',
    STATUS_WAITING_MEDIUM: 'aptdaemon-wait',
    STATUS_WAITING_CONFIG_FILE_PROMPT:  'aptdaemon-wait'}

_ICONS_ROLE = {
    ROLE_INSTALL_FILE: 'aptdaemon-add',
    ROLE_INSTALL_PACKAGES: 'aptdaemon-add',
    ROLE_UPDATE_CACHE: 'aptdaemon-update-cache',
    ROLE_REMOVE_PACKAGES: 'aptdaemon-delete',
    ROLE_UPGRADE_PACKAGES: 'aptdaemon-upgrade',
    ROLE_UPGRADE_SYSTEM: 'system-software-update'}

_ANIMATIONS_STATUS = {
    STATUS_CANCELLING: 'aptdaemon-action-cleaning-up',
    STATUS_CLEANING_UP: 'aptdaemon-action-cleaning-up',
    STATUS_RESOLVING_DEP: 'aptdaemon-action-resolving',
    STATUS_DOWNLOADING: 'aptdaemon-action-downloading',
    STATUS_DOWNLOADING_REPO: 'aptdaemon-action-downloading',
    STATUS_LOADING_CACHE: 'aptdaemon-action-updating-cache',
    STATUS_WAITING: 'aptdaemon-action-waiting',
    STATUS_WAITING_LOCK: 'aptdaemon-action-waiting',
    STATUS_WAITING_MEDIUM: 'aptdaemon-action-waiting',
    STATUS_WAITING_CONFIG_FILE_PROMPT: 'aptdaemon-action-waiting'}

_PAST_ROLE = {
    ROLE_INSTALL_FILE: _("Installed file"),
    ROLE_INSTALL_PACKAGES: _("Installed packages"),
    ROLE_ADD_VENDOR_KEY_FILE: _("Added key from file"),
    ROLE_UPDATE_CACHE: _("Updated cache"),
    ROLE_PK_QUERY: _("Search done"),
    ROLE_REMOVE_VENDOR_KEY: _("Removed trusted key"),
    ROLE_REMOVE_PACKAGES: _("Removed packages"),
    ROLE_UPGRADE_PACKAGES: _("Updated packages"),
    ROLE_UPGRADE_SYSTEM: _("Upgraded system"),
    ROLE_COMMIT_PACKAGES: _("Applied changes"),
    ROLE_FIX_INCOMPLETE_INSTALL: _("Repaired incomplete installation"),
    ROLE_FIX_BROKEN_DEPENDS: _("Repaired broken dependencies"),
    ROLE_ADD_REPOSITORY: _("Added software source"),
    ROLE_ENABLE_DISTRO_COMP: _("Enabled component of the distribution"),
    ROLE_CLEAN: _("Removed downloaded package files"),
    ROLE_RECONFIGURE: _("Reconfigured installed packages"),
    ROLE_UNSET: ""}

_STRING_EXIT = {
    EXIT_SUCCESS: _("Successful"),
    EXIT_CANCELLED: _("Canceled"),
    EXIT_FAILED: _("Failed")}

_PRESENT_ROLE = {
    ROLE_INSTALL_FILE: _("Installing file"),
    ROLE_INSTALL_PACKAGES: _("Installing packages"),
    ROLE_ADD_VENDOR_KEY_FILE: _("Adding key from file"),
    ROLE_UPDATE_CACHE: _("Updating cache"),
    ROLE_REMOVE_VENDOR_KEY: _("Removing trusted key"),
    ROLE_REMOVE_PACKAGES: _("Removing packages"),
    ROLE_UPGRADE_PACKAGES: _("Updating packages"),
    ROLE_UPGRADE_SYSTEM: _("Upgrading system"),
    ROLE_COMMIT_PACKAGES: _("Applying changes"),
    ROLE_FIX_INCOMPLETE_INSTALL: _("Repairing incomplete installation"),
    ROLE_FIX_BROKEN_DEPENDS: _("Repairing installed software"),
    ROLE_ADD_REPOSITORY: _("Adding software source"),
    ROLE_ENABLE_DISTRO_COMP: _("Enabling component of the distribution"),
    ROLE_CLEAN: _("Removing downloaded package files"),
    ROLE_RECONFIGURE: _("Reconfiguring installed packages"),
    ROLE_PK_QUERY: _("Searching"),
    ROLE_UNSET: ""}

_ERROR_ROLE = {
    ROLE_INSTALL_FILE: _("Installation of the package file failed"),
    ROLE_INSTALL_PACKAGES: _("Installation of software failed"),
    ROLE_ADD_VENDOR_KEY_FILE: _("Adding the key to the list of trusted "
                                "software vendors failed"),
    ROLE_UPDATE_CACHE: _("Refreshing the software list failed"),
    ROLE_REMOVE_VENDOR_KEY: _("Removing the vendor from the list of trusted "
                              "ones failed"),
    ROLE_REMOVE_PACKAGES: _("Removing software failed"),
    ROLE_UPGRADE_PACKAGES: _("Updating software failed"),
    ROLE_UPGRADE_SYSTEM: _("Upgrading the system failed"),
    ROLE_COMMIT_PACKAGES: _("Applying software changes failed"),
    ROLE_FIX_INCOMPLETE_INSTALL: _("Repairing incomplete installation "
                                   "failed"),
    ROLE_FIX_BROKEN_DEPENDS: _("Repairing broken dependencies failed"),
    ROLE_ADD_REPOSITORY: _("Adding software source failed"),
    ROLE_ENABLE_DISTRO_COMP: _("Enabling component of the distribution "
                               "failed"),
    ROLE_CLEAN: _("Removing downloaded package files failed"),
    ROLE_RECONFIGURE: _("Removing downloaded package files failed"),
    ROLE_PK_QUERY: _("Search failed"),
    ROLE_ADD_LICENSE_KEY: _("Adding license key"),
    ROLE_UNSET: ""}

_DESCS_ERROR = {
    ERROR_PACKAGE_DOWNLOAD_FAILED: _("Check your Internet connection."),
    ERROR_REPO_DOWNLOAD_FAILED: _("Check your Internet connection."),
    ERROR_CACHE_BROKEN: _("Check if you are using third party "
                          "repositories. If so disable them, since "
                          "they are a common source of problems.\n"
                          "Furthermore run the following command in a "
                          "Terminal: apt-get install -f"),
    ERROR_KEY_NOT_INSTALLED: _("The selected file may not be a GPG key file "
                               "or it might be corrupt."),
    ERROR_KEY_NOT_REMOVED: _("The selected key couldn't be removed. "
                             "Check that you provided a valid fingerprint."),
    ERROR_NO_LOCK: _("Check if you are currently running another "
                     "software management tool, e.g. Synaptic or aptitude. "
                     "Only one tool is allowed to make changes at a time."),
    ERROR_NO_CACHE: _("This is a serious problem. Try again later. If this "
                      "problem appears again, please report an error to the "
                      "developers."),
    ERROR_NO_PACKAGE: _("Check the spelling of the package name, and "
                        "that the appropriate repository is enabled."),
    ERROR_PACKAGE_UPTODATE: _("There isn't any need for an update."),
    ERROR_PACKAGE_ALREADY_INSTALLED: _("There isn't any need for an "
                                       "installation"),
    ERROR_PACKAGE_NOT_INSTALLED: _("There isn't any need for a removal."),
    ERROR_NOT_REMOVE_ESSENTIAL_PACKAGE: _("You requested to remove a "
                                          "package which is an essential "
                                          "part of your system."),
    ERROR_DAEMON_DIED: _("The connection to the daemon was lost. Most likely "
                         "the background daemon crashed."),
    ERROR_PACKAGE_MANAGER_FAILED: _("The installation or removal of a "
                                    "software package failed."),
    ERROR_NOT_SUPPORTED: _("The requested feature is not supported."),
    ERROR_UNKNOWN: _("There seems to be a programming error in aptdaemon, "
                     "the software that allows you to install/remove "
                     "software and to perform other package management "
                     "related tasks."),
    ERROR_DEP_RESOLUTION_FAILED: _("This error could be caused by required "
                                   "additional software packages which are "
                                   "missing or not installable. Furthermore "
                                   "there could be a conflict between "
                                   "software packages which are not allowed "
                                   "to be installed at the same time."),
    ERROR_PACKAGE_UNAUTHENTICATED: _("This requires installing packages "
                                     "from unauthenticated sources."),
    ERROR_INCOMPLETE_INSTALL: _("The installation could have failed because "
                                "of an error in the corresponding software "
                                "package or it was cancelled in an unfriendly "
                                "way. "
                                "You have to repair this before you can "
                                "install or remove any further software."),
    ERROR_UNREADABLE_PACKAGE_FILE: _("Please copy the file to your local "
                                     "computer and check the file "
                                     "permissions."),
    ERROR_INVALID_PACKAGE_FILE: _("The installation of a package which "
                                  "violates the quality standards isn't "
                                  "allowed. This could cause serious "
                                  "problems on your computer. Please contact "
                                  "the person or organisation who provided "
                                  "this package file and include the details "
                                  "beneath."),
    ERROR_LICENSE_KEY_INSTALL_FAILED: _("The downloaded license key which is "
                                        "required to run this piece of "
                                        "software is not valid or could not "
                                        "be installed correctly.\n"
                                        "See the details for more "
                                        "information."),
    ERROR_SYSTEM_ALREADY_UPTODATE: _("All available upgrades have already "
                                     "been installed."),
    ERROR_LICENSE_KEY_DOWNLOAD_FAILED: _("The license key which allows you to "
                                         "use this piece of software could "
                                         "not be downloaded. Please check "
                                         "your network connection."),
    ERROR_NOT_AUTHORIZED: _("You don't have the required privileges to "
                            "perform this action."),
    ERROR_AUTH_FAILED: _("You either provided a wrong password or "
                         "cancelled the authorization.\n"
                         "Furthermore there could also be a technical reason "
                         "for this error if you haven't seen a password "
                         "dialog: your desktop environment doesn't provide a "
                         "PolicyKit session agent.")}

_STRINGS_ERROR = {
    ERROR_PACKAGE_DOWNLOAD_FAILED: _("Failed to download package files"),
    ERROR_REPO_DOWNLOAD_FAILED: _("Failed to download repository "
                                  "information"),
    ERROR_DEP_RESOLUTION_FAILED: _("Package dependencies cannot be resolved"),
    ERROR_CACHE_BROKEN: _("The package system is broken"),
    ERROR_KEY_NOT_INSTALLED: _("Key was not installed"),
    ERROR_KEY_NOT_REMOVED: _("Key was not removed"),
    ERROR_NO_LOCK: _("Failed to lock the package manager"),
    ERROR_NO_CACHE: _("Failed to load the package list"),
    ERROR_NO_PACKAGE: _("Package does not exist"),
    ERROR_PACKAGE_UPTODATE: _("Package is already up to date"),
    ERROR_PACKAGE_ALREADY_INSTALLED: _("Package is already installed"),
    ERROR_PACKAGE_NOT_INSTALLED: _("Package isn't installed"),
    ERROR_NOT_REMOVE_ESSENTIAL_PACKAGE: _("Failed to remove essential "
                                          "system package"),
    ERROR_DAEMON_DIED: _("Task cannot be monitored or controlled"),
    ERROR_PACKAGE_MANAGER_FAILED: _("Package operation failed"),
    ERROR_PACKAGE_UNAUTHENTICATED: _("Requires installation of untrusted "
                                     "packages"),
    ERROR_INCOMPLETE_INSTALL: _("Previous installation hasn't been completed"),
    ERROR_INVALID_PACKAGE_FILE: _("The package is of bad quality"),
    ERROR_UNREADABLE_PACKAGE_FILE: _("Package file could not be opened"),
    ERROR_NOT_SUPPORTED: _("Not supported feature"),
    ERROR_LICENSE_KEY_DOWNLOAD_FAILED: _("Failed to download the license key"),
    ERROR_LICENSE_KEY_INSTALL_FAILED: _("Failed to install the license key"),
    ERROR_SYSTEM_ALREADY_UPTODATE: _("The system is already up to date"),
    ERROR_AUTH_FAILED: _("You could not be authorized"),
    ERROR_NOT_AUTHORIZED: _("You are not allowed to perform this action"),
    ERROR_UNKNOWN: _("An unhandlable error occured")}

_STRINGS_STATUS = {
    STATUS_SETTING_UP: _("Waiting for service to start"),
    STATUS_QUERY: _("Searching"),
    STATUS_WAITING: _("Waiting"),
    STATUS_WAITING_MEDIUM: _("Waiting for required medium"),
    STATUS_WAITING_LOCK: _("Waiting for other software managers to quit"),
    STATUS_WAITING_CONFIG_FILE_PROMPT: _("Waiting for configuration file "
                                         "prompt"),
    STATUS_RUNNING: _("Running task"),
    STATUS_DOWNLOADING: _("Downloading"),
    STATUS_DOWNLOADING_REPO: _("Querying software sources"),
    STATUS_CLEANING_UP: _("Cleaning up"),
    STATUS_RESOLVING_DEP: _("Resolving dependencies"),
    STATUS_COMMITTING: _("Applying changes"),
    STATUS_FINISHED: _("Finished"),
    STATUS_CANCELLING: _("Cancelling"),
    STATUS_LOADING_CACHE: _("Loading software list"),
    STATUS_AUTHENTICATING: _("Waiting for authentication")}

STRINGS_PKG_STATUS = {
    # TRANSLATORS: %s is the name of a package
    PKG_INSTALLING: _("Installing %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_CONFIGURING: _("Configuring %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_REMOVING: _("Removing %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_PURGING: _("Completely removing %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_PURGING: _("Noting disappearance of %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_RUNNING_TRIGGER: _("Running post-installation trigger %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_UPGRADING: _("Upgrading %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_UNPACKING: _("Unpacking %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_PREPARING_INSTALL: _("Preparing installation of %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_PREPARING_CONFIGURE: _("Preparing configuration of %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_PREPARING_REMOVE: _("Preparing removal of %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_PREPARING_PURGE: _("Preparing complete removal of %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_INSTALLED: _("Installed %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_PURGED: _("Completely removed %s"),
    # TRANSLATORS: %s is the name of a package
    PKG_REMOVED: _("Removed %s")}

STRINGS_DOWNLOAD = {
    DOWNLOAD_DONE: _("Done"),
    DOWNLOAD_AUTH_ERROR: _("Authentication failed"),
    DOWNLOAD_ERROR: _("Failed"),
    DOWNLOAD_FETCHING: _("Fetching"),
    DOWNLOAD_IDLE: _("Idle"),
    DOWNLOAD_NETWORK_ERROR: _("Network isn't available")}


def get_status_icon_name_from_enum(enum):
    """Get the icon name for a transaction status.

    :param enum: The transaction status enum, e.g. :data:`STATUS_WAITING`.
    :returns: The icon name string.
    """
    try:
        return _ICONS_STATUS[enum]
    except KeyError:
        return "aptdaemon-working"


def get_role_icon_name_from_enum(enum):
    """Get an icon to represent the role of a transaction.

    :param enum: The transaction role enum, e.g. :data:`ROLE_UPDATE_CACHE`.
    :returns: The icon name string.
    """
    try:
        return _ICONS_ROLE[enum]
    except KeyError:
        return "aptdaemon-working"


def get_status_animation_name_from_enum(enum):
    """Get an animation to represent a transaction status.

    :param enum: The transaction status enum, e.g. :data:`STATUS_WAITING`.
    :returns: The animation name string.
    """
    try:
        return _ANIMATIONS_STATUS[enum]
    except KeyError:
        return None


def get_role_localised_past_from_enum(enum):
    """Get the description of a completed transaction action.

    :param enum: The transaction role enum, e.g. :data:`ROLE_UPDATE_CACHE`.
    :returns: The description string.
    """
    try:
        return _PAST_ROLE[enum]
    except KeyError:
        return None


def get_exit_string_from_enum(enum):
    """Get the description of a transaction exit status.

    :param enum: The transaction exit status enum, e.g. :data:`EXIT_FAILED`.
    :returns: The description string.
    """
    try:
        return _STRING_EXIT[enum]
    except:
        return None


def get_role_localised_present_from_enum(enum):
    """Get the description of a present transaction action.

    :param enum: The transaction role enum, e.g. :data:`ROLE_UPDATE_CACHE`.
    :returns: The description string.
    """
    try:
        return _PRESENT_ROLE[enum]
    except KeyError:
        return None


def get_role_error_from_enum(enum):
    """Get the description of a failed transaction action.

    :param enum: The transaction role enum, e.g. :data:`ROLE_UPDATE_CACHE`.
    :returns: The description string.
    """
    try:
        return _ERROR_ROLE[enum]
    except KeyError:
        return None


def get_error_description_from_enum(enum):
    """Get a long description of an error.

    :param enum: The transaction error enum, e.g. :data:`ERROR_NO_LOCK`.
    :returns: The description string.
    """
    try:
        return _DESCS_ERROR[enum]
    except KeyError:
        return None


def get_error_string_from_enum(enum):
    """Get a short description of an error.

    :param enum: The transaction error enum, e.g. :data:`ERROR_NO_LOCK`.
    :returns: The description string.
    """
    try:
        return _STRINGS_ERROR[enum]
    except KeyError:
        return None


def get_status_string_from_enum(enum):
    """Get the description of a transaction status.

    :param enum: The transaction status enum, e.g. :data:`STATUS_WAITING`.
    :returns: The description string.
    """
    try:
        return _STRINGS_STATUS[enum]
    except KeyError:
        return None


def get_package_status_from_enum(enum):
    """Get the description of a package status.

    :param enum: The download status enum, e.g. :data:`PKG_INSTALLING`.
    :returns: The description string.
    """
    try:
        return STRINGS_PKG_STATUS[enum]
    except KeyError:
        return _("Processing %s")


def get_download_status_from_enum(enum):
    """Get the description of a download status.

    :param enum: The download status enum, e.g. :data:`DOWNLOAD_DONE`.
    :returns: The description string.
    """
    try:
        return STRINGS_DOWNLOAD[enum]
    except KeyError:
        return None

# vim:ts=4:sw=4:et
