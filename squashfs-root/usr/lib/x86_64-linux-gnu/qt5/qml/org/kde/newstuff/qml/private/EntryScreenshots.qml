/*
 *   Copyright (C) 2012 Aleix Pol Gonzalez <aleixpol@blue-systems.com>
 *   Copyright (C) 2019 Dan Leinir Turthra Jensen <admin@leinir.dk>
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU Library/Lesser General Public License
 *   version 2, or (at your option) any later version, as published by the
 *   Free Software Foundation
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details
 *
 *   You should have received a copy of the GNU Library/Lesser General Public
 *   License along with this program; if not, write to the
 *   Free Software Foundation, Inc.,
 *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */

import QtQuick 2.11
import QtQuick.Controls 2.11
import QtQuick.Layouts 1.11
import QtGraphicalEffects 1.11

import org.kde.kirigami 2.5 as Kirigami

Flickable {
    id: root
    property alias screenshotsModel: screenshotsRep.model
    readonly property alias count: screenshotsRep.count
    property int currentIndex: -1
    property Item currentItem: screenshotsRep.itemAt(currentIndex)
    Layout.preferredHeight: Kirigami.Units.gridUnit * 13
    contentHeight: height
    contentWidth: screenshotsLayout.width

    Popup {
        id: overlay
        parent: applicationWindow().overlay
        modal: true
        clip: false

        x: (parent.width - width)/2
        y: (parent.height - height)/2
        readonly property real proportion: overlayImage.sourceSize.width>1 ? overlayImage.sourceSize.height/overlayImage.sourceSize.width : 1
        height: overlayImage.status == Image.Loading ? Kirigami.Units.gridUnit * 5 : Math.min(parent.height * 0.9, (parent.width * 0.9) * proportion, overlayImage.sourceSize.height)
        width: height/proportion

        BusyIndicator {
            id: indicator
            visible: running
            running: overlayImage.status == Image.Loading
            anchors.fill: parent
        }

        Image {
            id: overlayImage
            anchors.fill: parent
            source: root.currentItem ? root.currentItem.imageSource : ""
            fillMode: Image.PreserveAspectFit
            smooth: true
        }

        Button {
            anchors {
                right: parent.left
                verticalCenter: parent.verticalCenter
            }
            visible: leftAction.visible
            icon.name: leftAction.iconName
            onClicked: leftAction.triggered(null)
        }

        Button {
            anchors {
                left: parent.right
                verticalCenter: parent.verticalCenter
            }
            visible: rightAction.visible
            icon.name: rightAction.iconName
            onClicked: rightAction.triggered(null)
        }

        Kirigami.Action {
            id: leftAction
            icon.name: "arrow-left"
            enabled: overlay.visible && visible
            visible: root.currentIndex >= 1 && !indicator.running
            onTriggered: root.currentIndex = (root.currentIndex - 1) % root.count
        }

        Kirigami.Action {
            id: rightAction
            icon.name: "arrow-right"
            enabled: overlay.visible && visible
            visible: root.currentIndex < (root.count - 1) && !indicator.running
            onTriggered: root.currentIndex = (root.currentIndex + 1) % root.count
        }
    }

    Row {
        id: screenshotsLayout
        height: root.contentHeight
        spacing: Kirigami.Units.largeSpacing
        focus: overlay.visible

        Keys.onLeftPressed:  if (leftAction.visible)  leftAction.trigger()
        Keys.onRightPressed: if (rightAction.visible) rightAction.trigger()

        Repeater {
            id: screenshotsRep

            delegate: MouseArea {
                readonly property url imageSource: modelData
                readonly property real proportion: thumbnail.sourceSize.width>1 ? thumbnail.sourceSize.height/thumbnail.sourceSize.width : 1
                width: Math.max(50, height/proportion)
                height: screenshotsLayout.height

                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor

                onClicked: {
                    root.currentIndex = index
                    overlay.open()
                }

                DropShadow {
                    source: thumbnail
                    anchors.fill: thumbnail
                    verticalOffset: Kirigami.Units.largeSpacing
                    horizontalOffset: 0
                    radius: 12.0
                    samples: 25
                    color: Kirigami.Theme.disabledTextColor
                    cached: true
                }

                BusyIndicator {
                    visible: running
                    running: thumbnail.status == Image.Loading
                    anchors.centerIn: parent
                }

                Image {
                    id: thumbnail
                    source: modelData
                    height: parent.height
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                }
            }
        }
    }
    clip: true
    readonly property var leftShadow: Shadow {
        parent: root
        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
        }
        edge: Qt.LeftEdge
        width: Math.max(0, Math.min(root.width/5, root.contentX))
    }

    readonly property var rightShadow: Shadow {
        parent: root
        anchors {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
        }
        edge: Qt.RightEdge
        width: Math.max(0, Math.min(root.contentWidth - root.contentX - root.width)/5)
    }
}
