/*
 *   Copyright 2016 Marco Martin <mart@kde.org>
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU Library General Public License as
 *   published by the Free Software Foundation; either version 2, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Library General Public License for more details
 *
 *   You should have received a copy of the GNU Library General Public
 *   License along with this program; if not, write to the
 *   Free Software Foundation, Inc.,
 *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */
import QtQuick 2.7
import QtQuick.Controls 2.0
import org.kde.kirigami 2.9 as Kirigami

MouseArea {
    id: root
    default property Item contentItem
    property Flickable flickableItem
    clip: true

    //TODO: horizontalScrollBarPolicy is completely noop just for compatibility right now
    property int horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
    property int verticalScrollBarPolicy: Qt.ScrollBarAsNeeded

    readonly property Item verticalScrollBar: flickableItem.ScrollBar.vertical ? flickableItem.ScrollBar.vertical : null

    onVerticalScrollBarPolicyChanged: {
        if (flickableItem.ScrollBar.vertical) {
            flickableItem.ScrollBar.vertical.visible = verticalScrollBarPolicy != Qt.ScrollBarAlwaysOff;
        }
        scrollBarCreationTimer.restart();
    }
    onHorizontalScrollBarPolicyChanged: {
        if (flickableItem.ScrollBar.horizontal) {
            flickableItem.ScrollBar.horizontal.visible = horizontalScrollBarPolicy != Qt.ScrollBarAlwaysOff;
        }
        scrollBarCreationTimer.restart();
    }


    onContentItemChanged: {
        if (contentItem.hasOwnProperty("contentY")) {
            flickableItem = contentItem;
            if (typeof(flickableItem.keyNavigationEnabled) != "undefined") {
                flickableItem.keyNavigationEnabled = true;
                flickableItem.keyNavigationWraps = true;
            }
            contentItem.parent = flickableParent;
        } else {
            flickableItem = flickableComponent.createObject(flickableParent);
            contentItem.parent = flickableItem.contentItem;
        }

        flickableItem.interactive = true;
        flickableItem.anchors.fill = flickableParent;

        scrollBarCreationTimer.restart();
    }

    Timer {
        id: scrollBarCreationTimer
        interval: 0
        onTriggered: {
            //create or destroy the vertical scrollbar
            if ((!flickableItem.ScrollBar.vertical) && 
                verticalScrollBarPolicy != Qt.ScrollBarAlwaysOff) {
                flickableItem.ScrollBar.vertical = verticalScrollComponent.createObject(root);
            } else if (flickableItem.ScrollBar.vertical &&
                verticalScrollBarPolicy == Qt.ScrollBarAlwaysOff) {
                flickableItem.ScrollBar.vertical.destroy();
            }

            //create or destroy the horizontal scrollbar
            if ((!flickableItem.ScrollBar.horizontal) && 
                horizontalScrollBarPolicy != Qt.ScrollBarAlwaysOff) {
                flickableItem.ScrollBar.horizontal = horizontalScrollComponent.createObject(root);
            } else if (flickableItem.ScrollBar.horizontal &&
                horizontalScrollBarPolicy == Qt.ScrollBarAlwaysOff) {
                flickableItem.ScrollBar.horizontal.destroy();
            }
        }
    }
    Kirigami.WheelHandler {
        id: wheelHandler
        target: root.flickableItem
    }
    Item {
        id: flickableParent
        anchors {
            fill: parent
        }
    }
    Component {
        id: flickableComponent
        Flickable {
            anchors {
                fill: parent
            }
            contentWidth: root.contentItem ? root.contentItem.width : 0
            contentHeight: root.contentItem ? root.contentItem.height : 0
        }
    }
    Component {
        id: verticalScrollComponent
        ScrollBar {
            z: flickableParent.z + 1
            visible: root.contentItem.visible && size < 1
            interactive: !Kirigami.Settings.tabletMode

            //NOTE: use this instead of anchors as crashes on some Qt 5.8 checkouts
            height: parent.height - anchors.topMargin
            anchors {
                topMargin: parent.flickableItem.headerItem ? parent.flickableItem.headerItem.height : 0
                right: parent.right
                top: parent.top
            }
        }
    }
    Component {
        id: horizontalScrollComponent
        ScrollBar {
            z: flickableParent.z + 1
            visible: root.contentItem.visible && size < 1
            interactive: !Kirigami.Settings.tabletMode

            //NOTE: use this instead of anchors as crashes on some Qt 5.8 checkouts
            height: parent.height - anchors.topMargin
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
        }
    }
}
