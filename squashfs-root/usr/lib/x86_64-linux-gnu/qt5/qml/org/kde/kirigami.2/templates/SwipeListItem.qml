/*
 *   Copyright 2010 Marco Martin <notmart@gmail.com>
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
 *   51 Franklin Street, Fifth Floor, Boston, MA  2.010-1301, USA.
 */

import QtQuick 2.7
import QtQuick.Layouts 1.2
import QtQuick.Controls 2.7 as Controls
import org.kde.kirigami 2.7
import "../private"
import QtQuick.Templates 2.0 as T2

/**
 * An item delegate Intended to support extra actions obtainable
 * by uncovering them by dragging away the item with the handle
 * This acts as a container for normal list items.
 * Any subclass of AbstractListItem can be assigned as the contentItem property.
 * @code
 * ListView {
 *     model: myModel
 *     delegate: SwipeListItem {
 *         QQC2.Label {
 *             text: model.text
 *         }
 *         actions: [
 *              Action {
 *                  iconName: "document-decrypt"
 *                  onTriggered: print("Action 1 clicked")
 *              },
 *              Action {
 *                  iconName: model.action2Icon
 *                  onTriggered: //do something
 *              }
 *         ]
 *     }
 * 
 * }
 * @endcode
 *
 * @inherit QtQuick.Templates.ItemDelegate
 */
T2.ItemDelegate {
    id: listItem

//BEGIN properties
    /**
     * supportsMouseEvents: bool
     * Holds if the item emits signals related to mouse interaction.
     *TODO: remove
     * The default value is false.
     */
    property alias supportsMouseEvents: listItem.hoverEnabled

    /**
     * containsMouse: bool
     * True when the user hover the mouse over the list item
     * NOTE: on mobile touch devices this will be true only when pressed is also true
     */
    property alias containsMouse: listItem.hovered

    /**
     * alternatingBackground: bool
     * If true the background of the list items will be alternating between two
     * colors, helping readability with multiple column views.
     * Use it only when implementing a view which shows data visually in multiple columns
     * @ since 2.7 
     */
    property bool alternatingBackground: false

    /**
     * sectionDelegate: bool
     * If true the item will be a delegate for a section, so will look like a
     * "title" for the items under it.
     */
    property bool sectionDelegate: false

    /**
     * separatorVisible: bool
     * True if the separator between items is visible
     * default: true
     */
    property bool separatorVisible: true

    /**
     * actionsVisible: bool
     * True if it's possible to see and access the item actions.
     * Actions should go completely out of the way for instance during
     * the editing of an item.
     * @since 2.5
     */
    property alias actionsVisible: behindItem.visible

    /**
     * actions: list<Action>
     * Defines the actions for the list item: at most 4 buttons will
     * contain the actions for the item, that can be revealed by
     * sliding away the list item.
     */
    property list<Action> actions

    /**
     * textColor: color
     * Color for the text in the item
     *
     * Note: if custom text elements are inserted in an AbstractListItem,
     * their color property will have to be manually bound with this property
     */
    property color textColor: Theme.textColor

    /**
     * backgroundColor: color
     * Color for the background of the item
     */
    property color backgroundColor: Theme.backgroundColor

    /**
     * alternateBackgroundColor: color
     * The background color to use if alternatingBackground is true.
     * It is advised to leave the default.
     * @since 2.7
     */
    property color alternateBackgroundColor: Theme.alternateBackgroundColor

    /**
     * activeTextColor: color
     * Color for the text in the item when pressed or selected
     * It is advised to leave the default value (Theme.highlightedTextColor)
     *
     * Note: if custom text elements are inserted in an AbstractListItem,
     * their color property will have to be manually bound with this property
     */
    property color activeTextColor: Theme.highlightedTextColor

    /**
     * activeBackgroundColor: color
     * Color for the background of the item when pressed or selected
     * It is advised to leave the default value (Theme.highlightColor)
     */
    property color activeBackgroundColor: Theme.highlightColor

    default property alias _default: listItem.contentItem

    hoverEnabled: true
    implicitWidth: contentItem ? contentItem.implicitWidth : Units.gridUnit * 12
    width: parent ? parent.width : implicitWidth
    implicitHeight: Math.max(Units.gridUnit * 2, contentItem.implicitHeight, actionsLayout.implicitHeight) + topPadding + bottomPadding

    padding: Settings.tabletMode ? Units.largeSpacing : Units.smallSpacing

    leftPadding: padding * 2

    rightPadding: padding * 2 + (handleMouse.visible ? handleMouse.width : (hovered || !supportsMouseEvents) * actionsLayout.width) + handleMouse.anchors.rightMargin
    
    topPadding: padding
    bottomPadding: padding

//END properties

    Item {
        id: behindItem
        parent: listItem
        z: -1
        //TODO: a global "open" state
        enabled: background.x !== 0
        property bool indicateActiveFocus: listItem.pressed || Settings.tabletMode || listItem.activeFocus || (view ? view.activeFocus : false)
        property Flickable view: listItem.ListView.view || (listItem.parent ? (listItem.parent.ListView.view || listItem.parent) : null)
        property T2.ScrollBar flickableVerticalScrollbar: view ? (view.T2.ScrollBar.vertical ? view.T2.ScrollBar.vertical : null) : null
        property T2.ScrollBar scrollviewVerticalScrollbar: view ? (view.parent.T2.ScrollBar.vertical ? view.parent.T2.ScrollBar.vertical : null) : null
        onViewChanged: {
            if (view && Settings.tabletMode && !behindItem.view.parent.parent._swipeFilter) {
                var component = Qt.createComponent(Qt.resolvedUrl("../private/SwipeItemEventFilter.qml"));
                behindItem.view.parent.parent._swipeFilter = component.createObject(behindItem.view.parent.parent);
            }
        }

        // Some of the views use flickables, and some use scrollviews, so we
        // need to handle both when we determine whether or not to move items
        // over to the right so the scrollbar doesn't overlap them
        function calculateMargin() {
            if (scrollviewVerticalScrollbar && scrollviewVerticalScrollbar.visible) {
                return scrollviewVerticalScrollbar.width
            } else if (flickableVerticalScrollbar && flickableVerticalScrollbar.visible) {
                return flickableVerticalScrollbar.width
            }
            return Units.smallSpacing
        }

        anchors {
            fill: parent
        }
        Rectangle {
            id: shadowHolder
            color: Qt.darker(Theme.backgroundColor, 1.05);
            anchors.fill: parent
        }
        EdgeShadow {
            edge: Qt.TopEdge
            visible: background.x != 0
            anchors {
                right: parent.right
                left: parent.left
                top: parent.top
            }
        }
        EdgeShadow {
            edge: LayoutMirroring.enabled ? Qt.RightEdge : Qt.LeftEdge
            x: LayoutMirroring.enabled ? listItem.background.x - width : (listItem.background.x + listItem.background.width)
            visible: background.x != 0
            anchors {
                top: parent.top
                bottom: parent.bottom
            }
        }
        MouseArea {
            anchors.fill: parent
            preventStealing: true
            enabled: background.x != 0
            onClicked: {
                positionAnimation.from = background.x;
                positionAnimation.to = 0;
                positionAnimation.running = true;
            }
        }
        Row {
            id: actionsLayout
            z: 1
            visible: listItem.actionsVisible
            parent: Settings.tabletMode ? behindItem : listItem
            opacity: Settings.tabletMode || listItem.hovered || !listItem.supportsMouseEvents ? 1 : 0
            Behavior on opacity {
                OpacityAnimator {
                    duration: Units.longDuration
                    easing.type: Easing.InOutQuad
                }
            }
            anchors {
                right: parent.right
                verticalCenter: parent.verticalCenter
                rightMargin: LayoutMirroring.enabled ? 0 : behindItem.calculateMargin()
                leftMargin:  LayoutMirroring.enabled ? 0 : behindItem.calculateMargin()
            }
            height: Math.min( parent.height / 1.5, Units.iconSizes.smallMedium)
            width: childrenRect.width
            property bool exclusive: false
            property Item checkedButton
            spacing: Settings.tabletMode ? Units.largeSpacing : 0
            property bool hasVisibleActions: false
            function updateVisibleActions(definitelyVisible = false) {
                if (definitelyVisible) {
                    hasVisibleActions = true;
                } else {
                    var actionCount = listItem.actions.length;
                    for (var i = 0; i < actionCount; i++) {
                        // Assuming that visible is only false if it is explicitly false, and not just falsy
                        if (listItem.actions[i].visible === false) {
                            continue;
                        }
                        hasVisibleActions = true;
                        break;
                    }
                }
            }
            Repeater {
                model: {
                    if (listItem.actions.length === 0) {
                        return null;
                    } else {
                        return listItem.actions[0].text !== undefined &&
                            listItem.actions[0].trigger !== undefined ?
                                listItem.actions :
                                listItem.actions[0];
                    }
                }
                delegate: Controls.ToolButton {
                    anchors.verticalCenter: parent.verticalCenter
                    icon.name: modelData.iconName !== "" ? modelData.iconName : ""
                    icon.source: modelData.iconSource !== "" ? modelData.iconSource : ""
                    enabled: (modelData && modelData.enabled !== undefined) ? modelData.enabled : true;
                    visible: (modelData && modelData.visible !== undefined) ? modelData.visible : true;
                    onVisibleChanged: actionsLayout.updateVisibleActions(visible);
                    Component.onCompleted: actionsLayout.updateVisibleActions(visible);
                    Component.onDestruction: actionsLayout.updateVisibleActions(visible);
                    Controls.ToolTip.delay: Units.toolTipDelay
                    Controls.ToolTip.timeout: 5000
                    Controls.ToolTip.visible: listItem.visible && (Settings.tabletMode ? pressed : hovered) && Controls.ToolTip.text.length > 0
                    Controls.ToolTip.text: modelData.tooltip || modelData.text

                    onClicked: {
                        if (modelData && modelData.trigger !== undefined) {
                            modelData.trigger();
                        }
                        positionAnimation.from = background.x;
                        positionAnimation.to = 0;
                        positionAnimation.running = true;
                    }
                }
            }
        }
    }

    MouseArea {
        id: handleMouse
        parent: listItem.background
        visible: Settings.tabletMode && listItem.actionsVisible && actionsLayout.hasVisibleActions
        z: 99
        anchors {
            right: parent.right
            verticalCenter: parent.verticalCenter
            rightMargin: LayoutMirroring.enabled ? 0 : behindItem.calculateMargin()
            leftMargin:  LayoutMirroring.enabled ? 0 : behindItem.calculateMargin()
        }

        preventStealing: true
        width: Units.iconSizes.smallMedium
        height: width
        property var downTimestamp;
        property int startX
        property int startMouseX

        onClicked: {
            positionAnimation.from = background.x;
            if (listItem.background.x > -listItem.background.width/2) {
                positionAnimation.to = (LayoutMirroring.enabled ? -1 : +1) * (-listItem.width + height + handleMouse.anchors.rightMargin);
            } else {
                positionAnimation.to = 0;
            }
            positionAnimation.restart();
        }
        onPressed: {
            downTimestamp = (new Date()).getTime();
            startX = listItem.background.x;
            startMouseX = mouse.x;
        }
        onPositionChanged: {
            if (LayoutMirroring.enabled) {
                listItem.background.x = Math.max(0, Math.min(listItem.width - height, listItem.background.x - (startMouseX - mouse.x)));
            } else {
                listItem.background.x = Math.min(0, Math.max(-listItem.width + height, listItem.background.x - (startMouseX - mouse.x)));
            }
        }
        onReleased: {
            var speed = ((startX - listItem.background.x) / ((new Date()).getTime() - downTimestamp) * 1000);
            var absoluteDelta = startX - listItem.background.x;
            if (LayoutMirroring.enabled) {
                speed = -speed;
                absoluteDelta = -absoluteDelta;
            }

            if (Math.abs(speed) < Units.gridUnit) {
                return;
            }
            if (speed > listItem.width/2 || absoluteDelta > listItem.width/2) {
                positionAnimation.to = (LayoutMirroring.enabled ? -1 : +1) * (-listItem.width + height + handleMouse.anchors.rightMargin);
            } else {
                positionAnimation.to = 0;
            }
            positionAnimation.from = background.x;
            positionAnimation.running = true;
        }
        Icon {
            id: handleIcon
            anchors.fill: parent
            selected: listItem.checked || (listItem.pressed && !listItem.checked && !listItem.sectionDelegate)
            source: (LayoutMirroring.enabled ? (listItem.background.x < listItem.background.width/2 ? "overflow-menu-right" : "overflow-menu-left") : (listItem.background.x < -listItem.background.width/2 ? "overflow-menu-right" : "overflow-menu-left"))
        }
    }

    NumberAnimation {
        id: positionAnimation
        property: "x"
        target: background
        duration: Units.longDuration
        easing.type: Easing.InOutQuad
    }

//BEGIN signal handlers
    onContentItemChanged: {
        if (!contentItem) {
            return;
        }
        contentItem.parent = background;
        contentItem.anchors.top = background.top;
        contentItem.anchors.left = background.left;
        contentItem.anchors.right = background.right;
        contentItem.anchors.leftMargin = Qt.binding(function() {return listItem.leftPadding});
        contentItem.anchors.rightMargin = Qt.binding(function() {return listItem.rightPadding});
        contentItem.anchors.topMargin = Qt.binding(function() {return listItem.topPadding});
        contentItem.z = 0;
    }
    Component.onCompleted: {
        //this will happen only once
        listItem.contentItemChanged();
    }
    Connections {
        target: Settings
        onTabletModeChanged: {
            if (Settings.tabletMode) {
                if (!internal.swipeFilterItem) {
                    var component = Qt.createComponent(Qt.resolvedUrl("../private/SwipeItemEventFilter.qml"));
                    listItem.ListView.view.parent.parent._swipeFilter = component.createObject(listItem.ListView.view.parent.parent);
                }
            } else {
                if (listItem.ListView.view.parent.parent._swipeFilter) {
                    listItem.ListView.view.parent.parent._swipeFilter.destroy();
                    positionAnimation.to = 0;
                    positionAnimation.from = background.x;
                    positionAnimation.running = true;
                }
            }
        }
    }
    QtObject {
        id: internal
        readonly property QtObject swipeFilterItem: (behindItem.view && behindItem.view.parent && behindItem.view.parent.parent && behindItem.view.parent.parent._swipeFilter) ? behindItem.view.parent.parent._swipeFilter : null

        readonly property bool edgeEnabled: swipeFilterItem ? swipeFilterItem.currentItem === listItem || swipeFilterItem.currentItem === listItem.parent : false
    }

    Connections {
        id: swipeFilterConnection

        target: internal.edgeEnabled ? internal.swipeFilterItem : null
        onPeekChanged: {
            if (!listItem.actionsVisible) {
                return;
            }
            if (listItem.LayoutMirroring.enabled) {
                listItem.background.x = (listItem.background.width - listItem.background.height) * (1 - internal.swipeFilterItem.peek);
            } else {
                listItem.background.x = -(listItem.background.width - listItem.background.height) * internal.swipeFilterItem.peek;
            }
        }
        onPressed: {
            if (internal.edgeEnabled) {
                handleMouse.onPressed(mouse);
            }
        }
        onClicked: {
            if (Math.abs(listItem.background.x) < Units.gridUnit && internal.edgeEnabled) {
                handleMouse.clicked(mouse);
            }
        }
        onReleased: {
            if (internal.edgeEnabled) {
                handleMouse.released(mouse);
            }
        }
        onCurrentItemChanged: {
            if (!internal.edgeEnabled) {
                positionAnimation.to = 0;
                positionAnimation.from = background.x;
                positionAnimation.running = true;
            }
        }
    }

//END signal handlers

    Accessible.role: Accessible.ListItem
}
