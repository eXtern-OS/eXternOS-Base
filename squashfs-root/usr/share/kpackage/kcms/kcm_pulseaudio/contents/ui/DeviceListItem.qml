/*
    Copyright 2014-2015 Harald Sitter <sitter@kde.org>

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of
    the License or (at your option) version 3 or any later version
    accepted by the membership of KDE e.V. (or its successor approved
    by the membership of KDE e.V.), which shall act as a proxy
    defined in Section 14 of version 3 of the license.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

import QtQuick 2.0
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.0

import org.kde.kirigami 2.5 as Kirigami
import org.kde.plasma.private.volume 0.1

ColumnLayout {
    id: delegate
    width: parent.width

    RowLayout {
        Kirigami.Icon {
            Layout.alignment: Qt.AlignHCenter
            width: height
            height: inputText.height
            source: IconName || "audio-card"
        }

        Label {
            id: inputText
            Layout.fillWidth: true
            elide: Text.ElideRight
            text: Description
        }

        Button {
            text: i18n("Default device")
            icon.name: "favorite"
            visible: delegate.ListView.view.count > 1
            checkable: true
            checked: Default
            onClicked: Default = true;
        }

        MuteButton {
            muted: Muted
            onCheckedChanged: Muted = checked
        }
    }

    ColumnLayout {
        width: parent.width

        RowLayout {
            visible: portbox.count > 1

            Label {
                text: i18nd("kcm_pulseaudio", "Port")
            }

            ComboBox {
                id: portbox
                readonly property var ports: Ports
                Layout.fillWidth: true
                onModelChanged: currentIndex = ActivePortIndex
                currentIndex: ActivePortIndex
                onActivated: ActivePortIndex = index

                onPortsChanged: {
                    var items = [];
                    for (var i = 0; i < ports.length; ++i) {
                        var port = ports[i];
                        var text = port.description;
                        if (port.availability == Port.Unavailable) {
                            if (port.name == "analog-output-speaker" || port.name == "analog-input-microphone-internal") {
                                text += i18ndc("kcm_pulseaudio", "Port is unavailable", " (unavailable)");
                            } else {
                                text += i18ndc("kcm_pulseaudio", "Port is unplugged", " (unplugged)");
                            }
                        }
                        items.push(text);
                    }
                    model = items;
                }
            }
        }

        VolumeSlider {}
    }

    ListItemSeperator { view: delegate.ListView.view }
}
