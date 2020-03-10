# AlertWatcher.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2010 Mohamed Amine IL Idrissi
#
#  Author: Mohamed Amine IL Idrissi <ilidrissiamine@gmail.com>
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

from __future__ import absolute_import

from gi.repository import GObject
import dbus
from dbus.mainloop.glib import DBusGMainLoop


class AlertWatcher(GObject.GObject):
    """ a class that checks for alerts and reports them, like a battery
    or network warning """

    __gsignals__ = {"network-alert": (GObject.SignalFlags.RUN_FIRST,
                                      None,
                                      (GObject.TYPE_INT,)),
                    "battery-alert": (GObject.SignalFlags.RUN_FIRST,
                                      None,
                                      (GObject.TYPE_BOOLEAN,)),
                    "network-3g-alert": (GObject.SignalFlags.RUN_FIRST,
                                         None,
                                         (GObject.TYPE_BOOLEAN,
                                          GObject.TYPE_BOOLEAN,)),
                    }

    def __init__(self):
        GObject.GObject.__init__(self)
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.Bus(dbus.Bus.TYPE_SYSTEM)
        # make it always connected if NM isn't available
        self.network_state = 3

    def check_alert_state(self):
        try:
            obj = self.bus.get_object("org.freedesktop.NetworkManager",
                                      "/org/freedesktop/NetworkManager")
            obj.connect_to_signal(
                "StateChanged",
                self._on_network_state_changed,
                dbus_interface="org.freedesktop.NetworkManager")
            interface = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
            self.network_state = interface.Get(
                "org.freedesktop.NetworkManager", "State")
            self._network_alert(self.network_state)
            # power
            obj = self.bus.get_object('org.freedesktop.UPower',
                                      '/org/freedesktop/UPower')
            obj.connect_to_signal("Changed", self._power_changed,
                                  dbus_interface="org.freedesktop.UPower")
            self._power_changed()
            # 3g
            self._update_3g_state()
        except dbus.exceptions.DBusException:
            pass

    def _on_network_state_changed(self, state):
        self._network_alert(state)
        self._update_3g_state()

    def _update_3g_state(self):
        from .roam import NetworkManagerHelper
        nm = NetworkManagerHelper()
        on_3g = nm.is_active_connection_gsm_or_cdma()
        is_roaming = nm.is_active_connection_gsm_or_cdma_roaming()
        self._network_3g_alert(on_3g, is_roaming)

    def _network_3g_alert(self, on_3g, is_roaming):
        self.emit("network-3g-alert", on_3g, is_roaming)

    def _network_alert(self, state):
        self.network_state = state
        self.emit("network-alert", state)

    def _power_changed(self):
        obj = self.bus.get_object("org.freedesktop.UPower",
                                  "/org/freedesktop/UPower")
        interface = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
        on_battery = interface.Get("org.freedesktop.UPower", "OnBattery")
        self.emit("battery-alert", on_battery)
