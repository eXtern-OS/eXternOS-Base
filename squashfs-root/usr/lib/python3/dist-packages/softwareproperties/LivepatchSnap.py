#
#  Copyright (c) 2019 Canonical
#
#  Authors:
#       Andrea Azzarone <andrea.azzarone@canonical.com>
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

from gettext import gettext as _
import logging

import gi
from gi.repository import Gio, GLib

try:
    gi.require_version('Snapd', '1')
    from gi.repository import Snapd
except(ImportError, ValueError):
    pass


class LivepatchSnap(object):

    # Constants
    SNAP_NAME = 'canonical-livepatch'

    # Public API
    def __init__(self):
        self._snapd_client = Snapd.Client()
        self._cancellable = Gio.Cancellable()

    def get_status(self):
        """ Get the status of canonical-livepatch snap.

        Returns:
            Snapd.SnapStatus.Enun: An enum indicating the status of the snap.
        """
        snap = self._get_raw_snap()
        return snap.get_status() if snap else Snapd.SnapStatus.UNKNOWN

    def enable_or_install(self):
        """Enable or install canonical-livepatch snap.

        Returns:
            (True, '') if successful, (False, error_message) otherwise.
        """
        status = self.get_status()

        if status == Snapd.SnapStatus.ACTIVE:
            logging.warning('{} snap is already active'.format(self.SNAP_NAME))
            return True, ''
        elif status == Snapd.SnapStatus.AVAILABLE:
            return self._install()
        elif status == Snapd.SnapStatus.INSTALLED:
            return self._enable()
        else:
            logging.warning('{} snap is in an unknown state'.format(self.SNAP_NAME))
            return False, _('Canonical Livepatch snap cannot be installed.')

    # Private methods
    def _get_raw_snap(self):
        """Get the Sanpd.Snap raw object of the canonical-livepatch snapd.

        Returns:
            Sanpd.Snap if successful, None otherwise.
        """
        try:
            snap = self._snapd_client.get_snap_sync(
                name=self.SNAP_NAME,
                cancellable=self._cancellable)
        except GLib.Error as e:
            logging.debug('Snapd.Client.get_snap_sync failed: {}'.format(e.message))
            snap = None

        if snap:
            return snap

        try:
            (snaps, ignored) = self._snapd_client.find_sync(
                flags=Snapd.FindFlags.MATCH_NAME,
                query=self.SNAP_NAME,
                cancellable=self._cancellable)
            snap = snaps[0]
        except GLib.Error as e:
            logging.debug('Snapd.Client.find_sync failed: {}'.format(e.message))

        return snap

    def _install(self):
        """Install canonical-livepatch snap.

        Returns:
            (True, '') if successful, (False, error_message) otherwise.
        """
        assert self.get_status() == Snapd.SnapStatus.AVAILABLE

        try:
            self._snapd_client.install2_sync(
                flags=Snapd.InstallFlags.NONE,
                name=self.SNAP_NAME,
                cancellable=self._cancellable)
        except GLib.Error as e:
            return False, _('Canonical Livepatch snap cannot be installed: {}'.format(e.message))
        else:
            return True, ''

    def _enable(self):
        """Enable the canonical-livepatch snap.

        Returns:
            (True, '') if successful, (False, error_message) otherwise.
        """
        assert self.get_status() == Snapd.SnapStatus.INSTALLED

        try:
            self._snapd_client.enable_sync(
                name=self.SNAP_NAME,
                cancellable=self._cancellable)
        except GLib.Error as e:
            return False, _('Canonical Livepatch snap cannot be enabled: {}'.format(e.message))
        else:
            return True, ''
