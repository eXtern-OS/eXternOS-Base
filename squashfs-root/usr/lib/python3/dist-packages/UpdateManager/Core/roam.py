# utils.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2011 Canonical
#
#  Author:  Alex Chiang <achiang@canonical.com>
#           Michael Vogt <michael.vogt@ubuntu.com>
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

import dbus
import sys


class ModemManagerHelper(object):

    # data taken from
    #  http://projects.gnome.org/NetworkManager/developers/mm-spec-04.html
    MM_DBUS_IFACE = "org.freedesktop.ModemManager"
    MM_DBUS_IFACE_MODEM = MM_DBUS_IFACE + ".Modem"

    # MM_MODEM_TYPE
    MM_MODEM_TYPE_GSM = 1
    MM_MODEM_TYPE_CDMA = 2

    # GSM
    # Not registered, not searching for new operator to register.
    MM_MODEM_GSM_NETWORK_REG_STATUS_IDLE = 0
    # Registered on home network.
    MM_MODEM_GSM_NETWORK_REG_STATUS_HOME = 1
    # Not registered, searching for new operator to register with.
    MM_MODEM_GSM_NETWORK_REG_STATUS_SEARCHING = 2
    # Registration denied.
    MM_MODEM_GSM_NETWORK_REG_STATUS_DENIED = 3
    # Unknown registration status.
    MM_MODEM_GSM_NETWORK_REG_STATUS_UNKNOWN = 4
    # Registered on a roaming network.
    MM_MODEM_GSM_NETWORK_REG_STATUS_ROAMING = 5

    # CDMA
    # Registration status is unknown or the device is not registered.
    MM_MODEM_CDMA_REGISTRATION_STATE_UNKNOWN = 0
    # Registered, but roaming status is unknown or cannot be provided
    # by the device. The device may or may not be roaming.
    MM_MODEM_CDMA_REGISTRATION_STATE_REGISTERED = 1
    #     Currently registered on the home network.
    MM_MODEM_CDMA_REGISTRATION_STATE_HOME = 2
    #     Currently registered on a roaming network.
    MM_MODEM_CDMA_REGISTRATION_STATE_ROAMING = 3

    def __init__(self):
        self.bus = dbus.SystemBus()
        self.proxy = self.bus.get_object("org.freedesktop.ModemManager",
                                         "/org/freedesktop/ModemManager")
        modem_manager = dbus.Interface(self.proxy, self.MM_DBUS_IFACE)
        self.modems = modem_manager.EnumerateDevices()

    @staticmethod
    def get_dbus_property(proxy, interface, property):
        props = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        property = props.Get(interface, property)
        return property

    def is_gsm_roaming(self):
        for m in self.modems:
            dev = self.bus.get_object(self.MM_DBUS_IFACE, m)
            type = self.get_dbus_property(dev, self.MM_DBUS_IFACE_MODEM,
                                          "Type")
            if type != self.MM_MODEM_TYPE_GSM:
                continue
            net = dbus.Interface(dev,
                                 self.MM_DBUS_IFACE_MODEM + ".Gsm.Network")
            reg = net.GetRegistrationInfo()
            # Be conservative about roaming. If registration unknown,
            # assume yes.
            # MM_MODEM_GSM_NETWORK_REG_STATUS
            if reg[0] in (self.MM_MODEM_GSM_NETWORK_REG_STATUS_UNKNOWN,
                          self.MM_MODEM_GSM_NETWORK_REG_STATUS_ROAMING):
                return True
        return False

    def is_cdma_roaming(self):
        for m in self.modems:
            dev = self.bus.get_object(self.MM_DBUS_IFACE, m)
            type = self.get_dbus_property(dev, self.MM_DBUS_IFACE_MODEM,
                                          "Type")
            if type != self.MM_MODEM_TYPE_CDMA:
                continue
            cdma = dbus.Interface(dev, self.MM_DBUS_IFACE_MODEM + ".Cdma")
            (cmda_1x, evdo) = cdma.GetRegistrationState()
            # Be conservative about roaming. If registration unknown,
            # assume yes.
            # MM_MODEM_CDMA_REGISTRATION_STATE
            roaming_states = (self.MM_MODEM_CDMA_REGISTRATION_STATE_REGISTERED,
                              self.MM_MODEM_CDMA_REGISTRATION_STATE_ROAMING)
            # evdo trumps cmda_1x (thanks to Mathieu Trudel-Lapierre)
            if evdo in roaming_states:
                return True
            elif cmda_1x in roaming_states:
                return True
        return False


class NetworkManagerHelper(object):
    NM_DBUS_IFACE = "org.freedesktop.NetworkManager"

    # connection states
    # Old enum values are for NM 0.7

    # The NetworkManager daemon is in an unknown state.
    NM_STATE_UNKNOWN = 0
    # The NetworkManager daemon is connecting a device.
    NM_STATE_CONNECTING_OLD = 2
    NM_STATE_CONNECTING = 40
    NM_STATE_CONNECTING_LIST = [NM_STATE_CONNECTING_OLD,
                                NM_STATE_CONNECTING]
    # The NetworkManager daemon is connected.
    NM_STATE_CONNECTED_OLD = 3
    NM_STATE_CONNECTED_LOCAL = 50
    NM_STATE_CONNECTED_SITE = 60
    NM_STATE_CONNECTED_GLOBAL = 70
    NM_STATE_CONNECTED_LIST = [NM_STATE_CONNECTED_OLD,
                               NM_STATE_CONNECTED_LOCAL,
                               NM_STATE_CONNECTED_SITE,
                               NM_STATE_CONNECTED_GLOBAL]

    # The device type is unknown.
    NM_DEVICE_TYPE_UNKNOWN = 0
    # The device is wired Ethernet device.
    NM_DEVICE_TYPE_ETHERNET = 1
    # The device is an 802.11 WiFi device.
    NM_DEVICE_TYPE_WIFI = 2
    # The device is a GSM-based cellular WAN device.
    NM_DEVICE_TYPE_GSM = 3
    # The device is a CDMA/IS-95-based cellular WAN device.
    NM_DEVICE_TYPE_CDMA = 4

    def __init__(self):
        self.bus = dbus.SystemBus()
        self.proxy = self.bus.get_object("org.freedesktop.NetworkManager",
                                         "/org/freedesktop/NetworkManager")

    @staticmethod
    def get_dbus_property(proxy, interface, property):
        props = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        property = props.Get(interface, property)
        return property

    def is_active_connection_gsm_or_cdma(self):
        res = False
        actives = self.get_dbus_property(
            self.proxy, self.NM_DBUS_IFACE, 'ActiveConnections')
        for a in actives:
            active = self.bus.get_object(self.NM_DBUS_IFACE, a)
            default_route = self.get_dbus_property(
                active, self.NM_DBUS_IFACE + ".Connection.Active", 'Default')
            if not default_route:
                continue
            devs = self.get_dbus_property(
                active, self.NM_DBUS_IFACE + ".Connection.Active", 'Devices')
            for d in devs:
                dev = self.bus.get_object(self.NM_DBUS_IFACE, d)
                type = self.get_dbus_property(
                    dev, self.NM_DBUS_IFACE + ".Device", 'DeviceType')
                if type == self.NM_DEVICE_TYPE_GSM:
                    return True
                elif type == self.NM_DEVICE_TYPE_CDMA:
                    return True
                else:
                    continue
        return res

    def is_active_connection_gsm_or_cdma_roaming(self):
        res = False
        if self.is_active_connection_gsm_or_cdma():
            mmhelper = ModemManagerHelper()
            res |= mmhelper.is_gsm_roaming()
            res |= mmhelper.is_cdma_roaming()
        return res


if __name__ == "__main__":

    # test code
    if sys.argv[1:] and sys.argv[1] == "--test":
        mmhelper = ModemManagerHelper()
        print("is_gsm_roaming", mmhelper.is_gsm_roaming())
        print("is_cdma_romaing", mmhelper.is_cdma_roaming())

    # roaming?
    nmhelper = NetworkManagerHelper()
    is_roaming = nmhelper.is_active_connection_gsm_or_cdma_roaming()
    print("roam: ", is_roaming)
    if is_roaming:
        sys.exit(1)
    sys.exit(0)
