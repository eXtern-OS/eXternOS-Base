# UnitySupport.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2011 Canonical
#
#  Author: Michael Vogt <mvo@ubuntu.com>
#          Bilal Akhtar <bilalakhtar@ubuntu.com>
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

import logging
from gettext import gettext as _

HAVE_UNITY_SUPPORT = False
try:
    import gi
    gi.require_version('Dbusmenu', '0.4')
    gi.require_version('Unity', '7.0')
    from gi.repository import Dbusmenu, Unity
    HAVE_UNITY_SUPPORT = True
except (ValueError, ImportError) as e:
    logging.warning("can not import unity GI %s" % e)


class IUnitySupport(object):
    """ interface for unity support """
    def __init__(self, parent=None):
        pass

    def set_urgency(self, urgent):
        pass

    def set_install_menuitem_visible(self, visible):
        pass

    def set_progress(self, progress):
        pass


class UnitySupportImpl(IUnitySupport):
    """ implementation of unity support (if unity is available) """

    def __init__(self, parent=None):
        # create launcher and quicklist
        um_launcher_entry = Unity.LauncherEntry.get_for_desktop_id(
            "update-manager.desktop")
        self._unity = um_launcher_entry
        if parent:
            self._add_quicklist(parent)

    def _add_quicklist(self, parent):
            quicklist = Dbusmenu.Menuitem.new()
            # install
            self.install_dbusmenuitem = Dbusmenu.Menuitem.new()
            self.install_dbusmenuitem.property_set(
                Dbusmenu.MENUITEM_PROP_LABEL,
                _("Install All Available Updates"))
            self.install_dbusmenuitem.property_set_bool(
                Dbusmenu.MENUITEM_PROP_VISIBLE, True)
            self.install_dbusmenuitem.connect(
                "item-activated", parent.install_all_updates, None)
            quicklist.child_append(self.install_dbusmenuitem)
            # add it
            self._unity.set_property("quicklist", quicklist)

    def set_progress(self, progress):
        """ set the progress [0,100] """
        self._unity.set_property("progress", progress / 100.0)
        # hide progress when out of bounds
        if progress < 0 or progress > 100:
            self._unity.set_property("progress_visible", False)
        else:
            self._unity.set_property("progress_visible", True)

    def set_urgency(self, urgent):
        self._unity.set_property("urgent", urgent)

    def set_install_menuitem_visible(self, visible):
        self.install_dbusmenuitem.property_set_bool(
            Dbusmenu.MENUITEM_PROP_VISIBLE, visible)


# check what to export to the clients
if HAVE_UNITY_SUPPORT:
    UnitySupport = UnitySupportImpl
else:
    # we just provide the empty interface
    UnitySupport = IUnitySupport
