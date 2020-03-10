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

import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0

import org.kde.kcm 1.0
import org.kde.plasma.core 2.0 as PlasmaCore /* for units.gridUnit */
import org.kde.kirigami 2.5 as Kirigami
import org.kde.plasma.private.volume 0.1

Kirigami.Page {
    title: kcm.name
    property QtObject sinkModel: SinkModel { }
    property QtObject sourceModel: SourceModel { }
    ConfigModule.quickHelp: i18nd("kcm_pulseaudio", "This module allows configuring the Pulseaudio sound subsystem.")
    implicitHeight: Kirigami.Units.gridUnit * 28

    // TODO: replace this TabBar-plus-Frame-in-a-ColumnLayout with whatever shakes
    // out of https://bugs.kde.org/show_bug.cgi?id=394296
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TabBar {
            id: tabView

            // Tab styles generally assume that they're touching the inner layout,
            // not the frame, so we need to move the tab bar down a pixel and make
            // sure it's drawn on top of the frame
            Layout.bottomMargin: -1
            z: 1

            TabButton {
                text: i18ndc("kcm_pulseaudio", "@title:tab", "Devices")
            }
            TabButton {
                text: i18ndc("kcm_pulseaudio", "@title:tab", "Applications")
            }
            TabButton {
                text: i18ndc("kcm_pulseaudio", "@title:tab", "Advanced")
            }
        }
        Frame {
            Layout.fillWidth: true
            Layout.fillHeight: true

            StackLayout {
                anchors.fill: parent

                currentIndex: tabView.currentIndex

                Devices {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }
                Applications {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }
                Advanced {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }
            }
        }
    }
}
