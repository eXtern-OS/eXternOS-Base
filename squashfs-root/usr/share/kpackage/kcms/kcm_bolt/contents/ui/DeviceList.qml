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

KCM.ScrollViewKCM {
    id: page

    property Bolt.DeviceModel deviceModel: null

    signal itemClicked(Bolt.Device device)

    header: RowLayout {
        CheckBox {
            id: enableBox
            text: i18n("Enable Thunderbolt devices")

            checked: deviceModel.manager.authMode == Bolt.Bolt.AuthMode.Enabled

            onToggled: {
                deviceModel.manager.authMode = enableBox.checked
                    ? Bolt.Bolt.AuthMode.Enabled
                    : Bolt.Bolt.AuthMode.Disabled
            }
        }
    }

    view: ListView {
        id: view
        model: deviceModel
        enabled: enableBox.checked

        property int _evalTrigger: 0

        Timer {
            interval: 2000
            running: view.visible
            repeat: true
            onTriggered: view._evalTrigger++;
        }

        delegate: Kirigami.AbstractListItem {
            id: item
            width: view.width

            RowLayout {
                id: layout
                spacing: Kirigami.Units.smallSpacing * 2
                property bool indicateActiveFocus: item.pressed || Kirigami.Settings.tabletMode || item.activeFocus || (item.ListView.view ? item.ListView.view.activeFocus : false)

                BusyIndicator {
                    id: busyIndicator
                    visible: model.device.status == Bolt.Bolt.Status.Authorizing
                    running: visible
                    Layout.minimumHeight: Kirigami.Units.iconSizes.smallMedium
                    Layout.maximumHeight: Layout.minimumHeight
                    Layout.minimumWidth: height
                }

                Label {
                    id: label
                    text: model.device.label
                    Layout.fillWidth: true
                    Layout.topMargin: Kirigami.Units.smallSpacing
                    Layout.bottomMargin: Kirigami.Units.smallSpacing
                    color: parent.indicateActiveFocus && (item.highlighted || item.checked || item.pressed) ? item.activeTextColor : item.textColor
                    elide: Text.ElideRight
                    font: item.font
                }

                Label {
                    id: statusLabel

                    Layout.alignment: Qt.AlignRight

                    property var _deviceStatus: Utils.deviceStatus(model.device, true)

                    text: view._evalTrigger, _deviceStatus.text
                    color: _deviceStatus.color
                }
            }

            onClicked: {
                page.itemClicked(model.device)
            }
        }
    }
}
