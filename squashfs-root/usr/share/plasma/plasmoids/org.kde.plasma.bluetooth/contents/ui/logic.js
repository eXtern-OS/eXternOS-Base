/*
    Copyright 2014-2015 David Rosca <nowrep@gmail.com>

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) version 3, or any
    later version accepted by the membership of KDE e.V. (or its
    successor approved by the membership of KDE e.V.), which shall
    act as a proxy defined in Section 6 of version 3 of the license.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library.  If not, see <http://www.gnu.org/licenses/>.
*/

function init()
{
    btManager.deviceAdded.connect(updateStatus);
    btManager.deviceRemoved.connect(updateStatus);
    btManager.deviceChanged.connect(updateStatus);
    btManager.bluetoothBlockedChanged.connect(updateStatus);
    btManager.bluetoothOperationalChanged.connect(updateStatus);

    updateStatus();
}

function updateStatus()
{
    var connectedDevices = [];

    for (var i = 0; i < btManager.devices.length; ++i) {
        var device = btManager.devices[i];
        if (device.connected) {
            connectedDevices.push(device);
        }
    }

    var text = "";
    var bullet = "\u2022";

    if (btManager.bluetoothBlocked) {
        text = i18n("Bluetooth is disabled");
    } else if (!btManager.bluetoothOperational) {
        if (!btManager.adapters.length) {
            text = i18n("No adapters available");
        } else {
            text = i18n("Bluetooth is offline");
        }
    } else if (connectedDevices.length) {
        text = i18ncp("Number of connected devices", "%1 connected device", "%1 connected devices", connectedDevices.length);
        for (var i = 0; i < connectedDevices.length; ++i) {
            var device = connectedDevices[i];
            text += "\n %1 %2".arg(bullet).arg(device.name);
        }
    } else {
        text = i18n("No connected devices");
    }

    plasmoid.toolTipSubText = text;
    deviceConnected = connectedDevices.length;

    if (btManager.bluetoothOperational) {
        plasmoid.status = PlasmaCore.Types.ActiveStatus;
    } else {
        plasmoid.status = PlasmaCore.Types.PassiveStatus;
    }
}

function icon()
{
    if (deviceConnected) {
        return "preferences-system-bluetooth-activated";
    } else if (!btManager.bluetoothOperational) {
        return "preferences-system-bluetooth-inactive";
    }
    return "preferences-system-bluetooth";
}
