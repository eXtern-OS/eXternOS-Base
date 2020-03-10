/*
 * Copyright (c) 2018 - 2019  Daniel Vrátil <dvratil@kde.org>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License or (at your option) version 3 or any later version
 * accepted by the membership of KDE e.V. (or its successor approved
 * by the membership of KDE e.V.), which shall act as a proxy
 * defined in Section 14 of version 3 of the license.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import QtQuick 2.7
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.3

import org.kde.kirigami 2.4 as Kirigami
import org.kde.kquickcontrolsaddons 2.0 as KQCAddons
import org.kde.kcm 1.2 as KCM
import org.kde.bolt 0.1 as Bolt
import "utils.js" as Utils

Kirigami.Page {
    KCM.ConfigModule.quickHelp: i18n("This module allows you to manage Thunderbolt devices connected to your computer.")
    KCM.ConfigModule.buttons: KCM.ConfigModule.NoAdditionalButton
    id: root

    title: kcm.name
    implicitWidth: Kirigami.Units.gridUnit * 20
    implicitHeight: pageRow.contentHeight > 0 ? Math.min(pageRow.contentHeight, Kirigami.Units.gridUnit * 20)
                                              : Kirigami.Units.gridUnit * 20

    Bolt.Manager {
        id: boltManager
    }

    Kirigami.PageRow {
        id: pageRow
        clip: true
        anchors.fill: parent

        Component.onCompleted: {
            if (boltManager.isAvailable) {
                if (boltManager.securityLevel == Bolt.Bolt.Security.DPOnly
                        || boltManager.securityLevel == Bolt.Bolt.Security.USBOnly) {
                    pageRow.push(noBoltPage, { text: i18n("Thunderbolt support has been disabled in BIOS") })
                } else {
                    pageRow.push(deviceList, { manager: boltManager })
                }
            } else {
                pageRow.push(noBoltPage, { text: i18n("Thunderbolt subsystem is not available") })
            }
        }
    }

    Component {
        id: noBoltPage
        Kirigami.Page {
            property alias text: label.text
            Label {
                id: label

                anchors.fill: parent
                verticalAlignment: Qt.AlignVCenter
                horizontalAlignment: Qt.AlignHCenter
            }
        }
    }

    Component {
        id: deviceList
        DeviceList {
            property alias manager: model.manager
            deviceModel: Bolt.DeviceModel {
                id: model
                showHosts: false
            }

            onItemClicked: function(device) {
                pageRow.push(deviceView, { manager: manager, device: device })
            }
        }
    }

    Component {
        id: deviceView
        DeviceView {
        }
    }
}
