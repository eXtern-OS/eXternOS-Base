/*
    Copyright 2014-2015 Harald Sitter <sitter@kde.org>
    Copyright 2016 David Rosca <nowrep@gmail.com>

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
import QtQuick.Controls 2.2

import org.kde.plasma.private.volume 0.1

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
            enabled: eventStreamView.count || sinkInputView.count
            text: i18nd("kcm_pulseaudio", "Playback")
            disabledText: i18ndc("kcm_pulseaudio", "@label", "No Applications Playing Audio")
        }

        ListView {
            id: eventStreamView
            Layout.fillWidth: true
            Layout.preferredHeight: contentHeight
            Layout.margins: units.gridUnit / 2
            interactive: false
            spacing: units.largeSpacing
            model: PulseObjectFilterModel {
                filters: [ { role: "Name", value: "sink-input-by-media-role:event" } ]
                sourceModel: StreamRestoreModel {}
            }
            delegate: StreamListItem {
                deviceModel: sinkModel
            }
        }

        ListView {
            id: sinkInputView
            Layout.fillWidth: true
            Layout.preferredHeight: contentHeight
            Layout.margins: units.gridUnit / 2
            interactive: false
            spacing: units.largeSpacing
            model: PulseObjectFilterModel {
                filters: [ { role: "VirtualStream", value: false } ]
                sourceModel: SinkInputModel {}
            }
            delegate: StreamListItem {
                deviceModel: sinkModel
            }
        }

        Header {
            Layout.fillWidth: true
            enabled: sourceOutputView.count > 0
            text: i18nd("kcm_pulseaudio", "Recording")
            disabledText: i18ndc("kcm_pulseaudio", "@label", "No Applications Recording Audio")
        }

        ListView {
            id: sourceOutputView
            Layout.fillWidth: true
            Layout.preferredHeight: contentHeight
            Layout.margins: units.gridUnit / 2
            interactive: false
            spacing: units.largeSpacing
            model: PulseObjectFilterModel {
                filters: [ { role: "VirtualStream", value: false } ]
                sourceModel: SourceOutputModel {}
            }

            delegate: StreamListItem {
                deviceModel: sourceModel
            }
        }
    }
}
