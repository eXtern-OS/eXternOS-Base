# networking - Monitor the network status
#
# Copyright (c) 2010 Mohamed Amine IL Idrissi
# Copyright (c) 2011 Canonical
# Copyright (c) 2011 Sebastian Heinlein
#
# Author:  Alex Chiang <achiang@canonical.com>
#          Michael Vogt <michael.vogt@ubuntu.com>
#          Mohamed Amine IL Idrissi <ilidrissiamine@gmail.com>
#          Sebastian Heinlein <devel@glatzor.de>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

from defer import Deferred, inline_callbacks, return_value
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import PackageKitGlib as pk
import dbus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
import logging
import os


log = logging.getLogger("AptDaemon.NetMonitor")


class NetworkMonitorBase(GObject.GObject):

    """Check the network state."""

    __gsignals__ = {"network-state-changed": (GObject.SignalFlags.RUN_FIRST,
                                              None,
                                              (GObject.TYPE_PYOBJECT,))}

    def __init__(self):
        log.debug("Initializing network monitor")
        GObject.GObject.__init__(self)
        self._state = pk.NetworkEnum.ONLINE

    def _set_state(self, enum):
        if self._state != enum:
            log.debug("Network state changed: %s", enum)
            self._state = enum
            self.emit("network-state-changed", enum)

    def _get_state(self):
        return self._state

    state = property(_get_state, _set_state)

    @inline_callbacks
    def get_network_state(self):
        """Update the network state."""
        return_value(self._state)


class ProcNetworkMonitor(NetworkMonitorBase):

    """Use the route information of the proc filesystem to detect
    the network state.
    """

    def __init__(self):
        log.debug("Initializing proc based network monitor")
        NetworkMonitorBase.__init__(self)
        self._state = pk.NetworkEnum.OFFLINE
        self._file = Gio.File.new_for_path("/proc/net/route")
        self._monitor = Gio.File.monitor(self._file,
                                         Gio.FileMonitorFlags.NONE,
                                         None)
        self._monitor.connect("changed",
                              self._on_route_file_changed)

    def _on_route_file_changed(self, *args):
        self.get_network_state()

    def _parse_route_file(self):
        """Parse the route file - taken from PackageKit"""
        with open("/proc/net/route") as route_file:
            for line in route_file.readlines():
                rows = line.split("\t")
                # The header line?
                if rows[0] == "Iface":
                    continue
                # A loopback device?
                elif rows[0] == "lo":
                    continue
                # Correct number of rows?
                elif len(rows) != 11:
                    continue
                # The route is a default gateway
                elif rows[1] == "00000000":
                    break
                # A gateway is set
                elif rows[2] != "00000000":
                    break
            else:
                return pk.NetworkEnum.OFFLINE
        return pk.NetworkEnum.ONLINE

    @inline_callbacks
    def get_network_state(self):
        """Update the network state."""
        self.state = self._parse_route_file()
        return_value(self.state)


class NetworkManagerMonitor(NetworkMonitorBase):

    """Use NetworkManager to monitor network state."""

    NM_DBUS_IFACE = "org.freedesktop.NetworkManager"
    NM_ACTIVE_CONN_DBUS_IFACE = NM_DBUS_IFACE + ".Connection.Active"
    NM_DEVICE_DBUS_IFACE = NM_DBUS_IFACE + ".Device"

    # The device type is unknown
    NM_DEVICE_TYPE_UNKNOWN = 0
    # The device is wired Ethernet device
    NM_DEVICE_TYPE_ETHERNET = 1
    # The device is an 802.11 WiFi device
    NM_DEVICE_TYPE_WIFI = 2
    # The device is a GSM-based cellular WAN device
    NM_DEVICE_TYPE_GSM = 3
    # The device is a CDMA/IS-95-based cellular WAN device
    NM_DEVICE_TYPE_CDMA = 4

    def __init__(self):
        log.debug("Initializing NetworkManager monitor")
        NetworkMonitorBase.__init__(self)
        self.bus = dbus.SystemBus()
        self.proxy = self.bus.get_object("org.freedesktop.NetworkManager",
                                         "/org/freedesktop/NetworkManager")
        self.proxy.connect_to_signal("PropertiesChanged",
                                     self._on_nm_properties_changed,
                                     dbus_interface=self.NM_DBUS_IFACE)
        self.bus.add_signal_receiver(
            self._on_nm_active_conn_props_changed,
            signal_name="PropertiesChanged",
            dbus_interface=self.NM_ACTIVE_CONN_DBUS_IFACE)

    @staticmethod
    def get_dbus_property(proxy, interface, property):
        """Small helper to get the property value of a dbus object."""
        props = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        deferred = Deferred()
        props.Get(interface, property,
                  reply_handler=deferred.callback,
                  error_handler=deferred.errback)
        return deferred

    @inline_callbacks
    def _on_nm_properties_changed(self, props):
        """Callback if NetworkManager properties changed."""
        if "ActiveConnections" in props:
            if not props["ActiveConnections"]:
                log.debug("There aren't any active connections")
                self.state = pk.NetworkEnum.OFFLINE
            else:
                yield self.get_network_state()

    @inline_callbacks
    def _on_nm_active_conn_props_changed(self, props):
        """Callback if properties of the active connection changed."""
        if "Default" not in props:
            raise StopIteration
        yield self.get_network_state()

    @inline_callbacks
    def _query_network_manager(self):
        """Query NetworkManager about the network state."""
        state = pk.NetworkEnum.OFFLINE
        try:
            active_conns = yield self.get_dbus_property(self.proxy,
                                                        self.NM_DBUS_IFACE,
                                                        "ActiveConnections")
        except dbus.DBusException:
            log.warning("Failed to determinate network state")
            return_value(state)

        for conn in active_conns:
            conn_obj = self.bus.get_object(self.NM_DBUS_IFACE, conn)
            try:
                is_default = yield self.get_dbus_property(
                    conn_obj, self.NM_ACTIVE_CONN_DBUS_IFACE, "Default")
                if not is_default:
                    continue
                devs = yield self.get_dbus_property(
                    conn_obj, self.NM_ACTIVE_CONN_DBUS_IFACE, "Devices")
            except dbus.DBusException:
                log.warning("Failed to determinate network state")
                break
            priority_device_type = -1
            for dev in devs:
                try:
                    dev_obj = self.bus.get_object(self.NM_DBUS_IFACE, dev)
                    dev_type = yield self.get_dbus_property(
                        dev_obj, self.NM_DEVICE_DBUS_IFACE, "DeviceType")
                except dbus.DBusException:
                    log.warning("Failed to determinate network state")
                    return_value(pk.NetworkEnum.UNKNOWN)
                # prioterizse device types, since a bridged GSM/CDMA connection
                # should be returned as a GSM/CDMA one
                # The NM_DEVICE_TYPE_* enums are luckly ordered in this sense.
                if dev_type <= priority_device_type:
                    continue
                priority_device_type = dev_type

                if dev_type in (self.NM_DEVICE_TYPE_GSM,
                                self.NM_DEVICE_TYPE_CDMA):
                    state = pk.NetworkEnum.MOBILE
                elif dev_type == self.NM_DEVICE_TYPE_ETHERNET:
                    state = pk.NetworkEnum.WIRED
                elif dev_type == self.NM_DEVICE_TYPE_WIFI:
                    state = pk.NetworkEnum.WIFI
                elif dev_type == self.NM_DEVICE_TYPE_UNKNOWN:
                    state = pk.NetworkEnum.OFFLINE
                else:
                    state = pk.NetworkEnum.ONLINE
        return_value(state)

    @inline_callbacks
    def get_network_state(self):
        """Update the network state."""
        self.state = yield self._query_network_manager()
        return_value(self.state)


def get_network_monitor(fallback=False):
    """Return a network monitor."""
    if fallback:
        return ProcNetworkMonitor()
    try:
        return NetworkManagerMonitor()
    except dbus.DBusException:
        pass
    if os.path.exists("/proc/net/route"):
        return ProcNetworkMonitor()
    return NetworkMonitorBase()


if __name__ == "__main__":
    @inline_callbacks
    def _call_monitor():
        state = yield monitor.get_network_state()
        print(("Initial network state: %s" % state))
    log_handler = logging.StreamHandler()
    log.addHandler(log_handler)
    log.setLevel(logging.DEBUG)
    monitor = get_network_monitor(True)
    _call_monitor()
    loop = GLib.MainLoop()
    loop.run()
