/*
    Copyright 2013-2014 Jan Grulich <jgrulich@redhat.com>
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

import QtQuick 2.2
import org.kde.plasma.plasmoid 2.0
import org.kde.bluezqt 1.0 as BluezQt
import org.kde.plasma.core 2.0 as PlasmaCore
import org.kde.kquickcontrolsaddons 2.0

import "logic.js" as Logic

Item {
    id: bluetoothApplet

    property bool deviceConnected : false
    property int runningActions : 0
    property QtObject btManager : BluezQt.Manager

    Plasmoid.toolTipMainText: i18n("Bluetooth")
    Plasmoid.icon: Logic.icon()

    Plasmoid.switchWidth: units.gridUnit * 15
    Plasmoid.switchHeight: units.gridUnit * 10

    Plasmoid.compactRepresentation: CompactRepresentation { }
    Plasmoid.fullRepresentation: FullRepresentation { }

    function action_bluedevilkcm() {
        KCMShell.open(["bluedevildevices", "bluedeviladapters", "bluedevilglobal"]);
    }

    Component.onCompleted: {
        plasmoid.removeAction("configure");
        plasmoid.setAction("bluedevilkcm", i18n("Configure &Bluetooth..."), "preferences-system-bluetooth");

        Logic.init();
    }
}
