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
import QtQuick.Layouts 1.1
import org.kde.bluezqt 1.0 as BluezQt
import org.kde.plasma.core 2.0 as PlasmaCore
import org.kde.plasma.components 2.0 as PlasmaComponents
import org.kde.kquickcontrolsaddons 2.0 as KQuickControlsAddons
import org.kde.plasma.private.bluetooth 1.0 as PlasmaBt

PlasmaComponents.ListItem {
    id: deviceItem

    property bool expanded : visibleDetails
    property bool visibleDetails : false
    property bool connecting : false
    property int baseHeight : deviceItemBase.height
    property var currentDeviceDetails : []

    height: expanded ? baseHeight + expandableComponentLoader.height + Math.round(units.gridUnit / 3) : baseHeight
    checked: containsMouse
    enabled: true

    Item {
        id: deviceItemBase

        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
            // Reset top margin from PlasmaComponents.ListItem
            topMargin: -Math.round(units.gridUnit / 3)
        }

        height: Math.max(units.iconSizes.medium, deviceNameLabel.height + deviceInfoLabel.height) + Math.round(units.gridUnit / 2)

        PlasmaCore.IconItem {
            id: deviceIcon

            anchors {
                left: parent.left
                verticalCenter: parent.verticalCenter
            }

            height: units.iconSizes.medium
            width: height
            source: Icon

            onSourceChanged: {
                var defaultIcon = "preferences-system-bluetooth";
                if (!valid && source != defaultIcon)
                    source = defaultIcon;
            }
        }

        PlasmaComponents.Label {
            id: deviceNameLabel

            anchors {
                bottom: deviceIcon.verticalCenter
                left: deviceIcon.right
                leftMargin: Math.round(units.gridUnit / 2)
                right: connectButton.visible ? connectButton.left : parent.right
            }

            height: paintedHeight
            elide: Text.ElideRight
            font.weight: Connected ? Font.DemiBold : Font.Normal
            font.italic: connecting
            text: DeviceFullName
            textFormat: Text.PlainText
        }

        PlasmaComponents.Label {
            id: deviceInfoLabel

            anchors {
                left: deviceIcon.right
                leftMargin: Math.round(units.gridUnit / 2)
                right: connectButton.visible ? connectButton.left : parent.right
                top: deviceNameLabel.bottom
            }

            height: paintedHeight
            elide: Text.ElideRight
            font.pointSize: theme.smallestFont.pointSize
            opacity: 0.6
            text: infoText()
            textFormat: Text.PlainText
        }

        PlasmaComponents.BusyIndicator {
            id: connectingIndicator

            anchors {
                right: parent.right
                rightMargin: Math.round(units.gridUnit / 2)
                verticalCenter: deviceIcon.verticalCenter
            }

            height: units.iconSizes.medium
            width: height
            running: connecting
            visible: running && !connectButton.visible
        }

        PlasmaComponents.Button {
            id: connectButton

            anchors {
                right: parent.right
                rightMargin: Math.round(units.gridUnit / 2)
                verticalCenter: deviceIcon.verticalCenter
            }

            text: Connected ? i18n("Disconnect") : i18n("Connect")
            opacity: !connecting && (deviceItem.containsMouse || deviceItem.visibleDetails) ? 1 : 0
            visible: opacity != 0

            Behavior on opacity {
                NumberAnimation {
                    duration: units.shortDuration
                }
            }

            onClicked: connectToDevice()
        }
    }

    Loader {
        id: expandableComponentLoader

        anchors {
            left: parent.left
            right: parent.right
            top: deviceItemBase.bottom
        }
    }

    Component {
        id: detailsComponent

        ColumnLayout {
            spacing: 0

            PlasmaCore.SvgItem {
                id: detailsSeparator
                Layout.fillWidth: true
                Layout.preferredHeight: lineSvg.elementSize("horizontal-line").height
                elementId: "horizontal-line"
                svg: PlasmaCore.Svg {
                    id: lineSvg
                    imagePath: "widgets/line"
                }
            }

            // Actions
            GridLayout {
                columns: 2
                rowSpacing: 0

                Item {
                    width: units.iconSizes.medium
                    Layout.rowSpan: 2
                }

                PlasmaComponents.ToolButton {
                    id: browseFilesButton
                    text: i18n("Browse Files")
                    iconSource: "folder"
                    visible: Uuids.indexOf(BluezQt.Services.ObexFileTransfer) != -1

                    onClicked: {
                        var url = "obexftp://%1/".arg(Address.replace(/:/g, "-"));
                        Qt.openUrlExternally(url);
                    }
                }

                PlasmaComponents.ToolButton {
                    id: sendFileButton
                    text: i18n("Send File")
                    iconSource: "folder-download"
                    visible: Uuids.indexOf(BluezQt.Services.ObexObjectPush) != -1

                    onClicked: {
                        PlasmaBt.LaunchApp.runCommand("bluedevil-sendfile", ["-u", Ubi]);
                    }
                }
            }

            PlasmaCore.SvgItem {
                id: actionsSeparator
                Layout.fillWidth: true
                Layout.preferredHeight: lineSvg.elementSize("horizontal-line").height
                visible: browseFilesButton.visible || sendFileButton.visible
                elementId: "horizontal-line"
                svg: lineSvg
            }

            Item {
                height: units.smallSpacing
            }

            // Media Player
            RowLayout {
                Item {
                    width: units.iconSizes.medium
                }

                MediaPlayerItem {
                    id: mediaPlayer
                    Layout.fillWidth: true
                    visible: MediaPlayer
                }
            }

            PlasmaCore.SvgItem {
                id: mediaPlayerSeparator
                Layout.fillWidth: true
                Layout.preferredHeight: lineSvg.elementSize("horizontal-line").height
                visible: mediaPlayer.visible
                elementId: "horizontal-line"
                svg: lineSvg
            }

            Item {
                height: units.smallSpacing
                visible: mediaPlayerSeparator.visible
            }

            KQuickControlsAddons.Clipboard {
                id: clipboard
            }

            PlasmaComponents.ContextMenu {
                id: contextMenu
                property string text

                function show(item, text, x, y) {
                    contextMenu.text = text
                    visualParent = item
                    open(x, y)
                }

                PlasmaComponents.MenuItem {
                    text: i18n("Copy")
                    icon: "edit-copy"
                    enabled: contextMenu.text !== ""
                    onClicked: clipboard.content = contextMenu.text
                }
            }

            // Details
            GridLayout {
                columns: 2
                rowSpacing: units.smallSpacing / 4

                Repeater {
                    id: repeater

                    model: currentDeviceDetails.length

                    PlasmaComponents.Label {
                        id: detailLabel
                        Layout.fillWidth: true
                        horizontalAlignment: index % 2 ? Text.AlignLeft : Text.AlignRight
                        elide: index % 2 ? Text.ElideRight : Text.ElideNone
                        font.pointSize: theme.smallestFont.pointSize
                        opacity: 0.6
                        text: index % 2 ? currentDeviceDetails[index] : "<b>%1</b>:".arg(currentDeviceDetails[index])
                        textFormat: index % 2 ? Text.PlainText : Text.StyledText

                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.RightButton
                            onPressed: contextMenu.show(this, detailLabel.text, mouse.x, mouse.y)
                            enabled: index % 2 === 1 // only let users copy the value on the right
                        }
                    }
                }
            }
        }
    }

    states: [
        State {
            name: "collapsed"
            when: !visibleDetails

            StateChangeScript {
                script: {
                    if (expandableComponentLoader.status == Loader.Ready) {
                        expandableComponentLoader.sourceComponent = undefined;
                    }
                }
            }
        },

        State {
            name: "expandedDetails"
            when: visibleDetails

            StateChangeScript {
                script: {
                    createContent();
                    expandableComponentLoader.sourceComponent = detailsComponent;
                }
            }
        }
    ]

    onStateChanged: {
        if (state == "expandedDetails") {
            ListView.view.currentIndex = index;
        }
    }

    onClicked: {
        visibleDetails = !visibleDetails;

        if (!visibleDetails) {
            ListView.view.currentIndex = -1;
        }
    }

    // Hide device details when the device for this delegate changes
    // This happens eg. when device connects/disconnects
    property QtObject __dev
    readonly property QtObject dev : Device
    onDevChanged: {
        if (__dev == dev) {
            return;
        }
        __dev = dev;

        if (visibleDetails) {
            visibleDetails = false;
            ListView.view.currentIndex = -1;
        }
    }

    function boolToString(v)
    {
        if (v) {
            return i18n("Yes");
        }
        return i18n("No");
    }

    function adapterName(a)
    {
        var hci = devicesModel.adapterHciString(a.ubi);
        if (hci != "") {
            return "%1 (%2)".arg(a.name).arg(hci);
        }
        return a.name;
    }

    function createContent() {
        var details = [];

        if (Name != RemoteName) {
            details.push(i18n("Remote Name"));
            details.push(RemoteName);
        }

        details.push(i18n("Address"));
        details.push(Address);

        details.push(i18n("Paired"));
        details.push(boolToString(Paired));

        details.push(i18n("Trusted"));
        details.push(boolToString(Trusted));

        details.push(i18n("Adapter"));
        details.push(adapterName(Adapter));

        currentDeviceDetails = details;
    }

    function infoText()
    {
        if (connecting) {
            return Connected ? i18n("Disconnecting") : i18n("Connecting");
        }

        switch (Type) {
        case BluezQt.Device.Headset:
        case BluezQt.Device.Headphones:
        case BluezQt.Device.OtherAudio:
            return i18n("Audio device");

        case BluezQt.Device.Keyboard:
        case BluezQt.Device.Mouse:
        case BluezQt.Device.Joypad:
        case BluezQt.Device.Tablet:
            return i18n("Input device");

        default:
            break;
        }

        var profiles = [];

        if (Uuids.indexOf(BluezQt.Services.ObexFileTransfer) != -1) {
            profiles.push(i18n("File transfer"));
        }
        if (Uuids.indexOf(BluezQt.Services.ObexObjectPush) != -1) {
            profiles.push(i18n("Send file"));
        }
        if (Uuids.indexOf(BluezQt.Services.HumanInterfaceDevice) != -1) {
            profiles.push(i18n("Input"));
        }
        if (Uuids.indexOf(BluezQt.Services.AdvancedAudioDistribution) != -1) {
            profiles.push(i18n("Audio"));
        }
        if (Uuids.indexOf(BluezQt.Services.Nap) != -1) {
            profiles.push(i18n("Network"));
        }

        if (!profiles.length) {
            return i18n("Other device");
        }

        return profiles.join(", ");
    }

    function connectToDevice()
    {
        if (connecting) {
            return;
        }

        connecting = true;
        runningActions++;

        // Disconnect device
        if (Connected) {
            Device.disconnectFromDevice().finished.connect(function(call) {
                connecting = false;
                runningActions--;
            });
            return;
        }

        // Connect device
        var call = Device.connectToDevice();
        call.userData = Device;

        call.finished.connect(function(call) {
            connecting = false;
            runningActions--;

            if (call.error) {
                var text = "";
                var device = call.userData;
                var title = "%1 (%2)".arg(device.name).arg(device.address);

                switch (call.error) {
                case BluezQt.PendingCall.Failed:
                    if (call.errorText == "Host is down") {
                        text = i18nc("Notification when the connection failed due to Failed:HostIsDown",
                                     "The device is unreachable");
                    } else {
                        text = i18nc("Notification when the connection failed due to Failed",
                                     "Connection to the device failed");
                    }
                    break;

                case BluezQt.PendingCall.NotReady:
                    text = i18nc("Notification when the connection failed due to NotReady",
                                 "The device is not ready");
                    break;

                default:
                    return;
                }

                PlasmaBt.Notify.connectionFailed(title, text);
            }
        });
    }
}
