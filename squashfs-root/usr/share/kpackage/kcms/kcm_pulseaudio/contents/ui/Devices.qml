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
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.3

ScrollView {
    id: scrollView

    contentWidth: contentLayout.width
    contentHeight: contentLayout.height
    clip: true

    ColumnLayout {
        id: contentLayout

        Component.onCompleted: {
            // Normal binding causes binding loops
            width = Qt.binding(function() {
                return scrollView.width;
            });
        }

        Header {
            Layout.fillWidth: true
            enabled: sinks.count > 0
            text: i18nd("kcm_pulseaudio", "Outputs")
            disabledText: i18ndc("kcm_pulseaudio", "@label", "No Output Devices Available")
        }

        ListView {
            id: sinks
            Layout.fillWidth: true
            Layout.preferredHeight: contentHeight
            Layout.margins: units.gridUnit / 2
            interactive: false
            spacing: units.smallSpacing * 2
            model: sinkModel
            delegate: DeviceListItem {}
        }

        Header {
            Layout.fillWidth: true
            enabled: sources.count > 0
            text: i18nd("kcm_pulseaudio", "Inputs")
            disabledText: i18ndc("kcm_pulseaudio", "@label", "No Input Devices Available")
        }

        ListView {
            id: sources
            Layout.fillWidth: true
            Layout.preferredHeight: contentHeight
            Layout.margins: units.gridUnit / 2
            interactive: false
            model: sourceModel
            delegate: DeviceListItem {}
        }
    }
}
