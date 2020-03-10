/*
 * This file is part of the KDE Baloo Project
 * Copyright (C) 2015  Pinak Ahuja <pinak.ahuja@gmail.com>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) version 3, or any
 * later version accepted by the membership of KDE e.V. (or its
 * successor approved by the membership of KDE e.V.), which shall
 * act as a proxy defined in Section 6 of version 3 of the license.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

import QtQuick 2.4
import QtQuick.Controls 2.0 as QQC2
import QtQuick.Layouts 1.1

import org.kde.baloo.experimental 0.1 as Baloo
import "constants.js" as Constants
import org.kde.kcm 1.1 as KCM

KCM.SimpleKCM {
    id: mainWindow

    KCM.ConfigModule.quickHelp: i18n("This module lets you monitor the file indexing")

    implicitWidth: units.gridUnit * 25
    implicitHeight: units.gridUnit * 10

    Baloo.Monitor {
        id: monitor
    }

    ColumnLayout {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 20
        spacing: 20
        visible: monitor.balooRunning

        QQC2.Label {
            id: indexerState
            text: i18n("Indexer State: %1", monitor.stateString)
        }

        QQC2.Label {
            id: filePath

            // Required so that text elides instead of expanding the entire layout
            Layout.maximumWidth: parent.width

            width: parent.width
            elide: Text.ElideMiddle

            text: {
                if (monitor.state == Constants.State.ContentIndexing) {
                    return i18n("Indexing: %1 ", monitor.filePath)
                } else if (monitor.state == Constants.State.Idle && monitor.filesIndexed == monitor.totalFiles) {
                    return i18n("Done")
                } else {
                    return ""
                }

            }
        }

        RowLayout {
            id: progressLayout
            spacing: 20

            QQC2.ProgressBar {
                id: progress
                Layout.fillWidth: true
                to: monitor.totalFiles
                value: monitor.filesIndexed
            }

            QQC2.Button {
                id: toggleButton
                text: monitor.state == Constants.State.Suspended ? i18n("Resume") : i18n("Suspend")
                onClicked: monitor.toggleSuspendState()
            }
        }

        QQC2.Label {
            visible: monitor.state == Constants.State.ContentIndexing
            id: remainingTime
            text: i18n("Remaining Time: %1", monitor.remainingTime)
        }
    }

    ColumnLayout {
        visible: !monitor.balooRunning
        anchors.centerIn: parent
        anchors.margins: 20

        spacing: 20

        QQC2.Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: i18n("File Indexer not running")
        }

        QQC2.Button {
            Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            id: startBaloo
            text: i18n("Start File Indexer")
            onClicked: monitor.startBaloo()
        }
    }
}
