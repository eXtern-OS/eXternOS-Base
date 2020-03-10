/*
 *   Copyright 2017 Marco Martin <mart@kde.org>
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU Library General Public License as
 *   published by the Free Software Foundation; either version 2 or
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

import QtQuick 2.6
import QtQuick.Layouts 1.2
import QtQuick.Controls 2.2
import org.kde.kirigami 2.4 as Kirigami

/**
 * This is the base class for Form layouts conforming to the
 * Kirigami Human interface guidelines. The layout will
 * be divided in two columns: on the right there will be a column
 * of fields, on the left their labels specified in the FormData attached
 * property.
 *
 * Example:
 * @code
 * import org.kde.kirigami 2.3 as Kirigami
 * Kirigami.FormLayout {
 *    TextField {
 *       Kirigami.FormData.label: "Label:"
 *    }
 *    Kirigami.Separator {
 *        Kirigami.FormData.label: "Section Title"
 *        Kirigami.FormData.isSection: true
 *    }
 *    TextField {
 *       Kirigami.FormData.label: "Label:"
 *    }
 *    TextField {
 *    }
 * }
 * @endcode
 * @inherits QtQuick.Item
 * @since 2.3
 */
Item {
    id: root

    /**
     * wideMode: bool
     * If true the layout will be optimized for a wide screen, such as
     * a desktop machine (the labels will be on a left column,
     * the fields on a right column beside it), if false (such as on a phone)
     * everything is laid out in a single column.
     * by default this will be based on whether the application is
     * wide enough for the layout of being in such mode.
     * It can be overridden by reassigning the property
     */
    property bool wideMode: width >= lay.wideImplicitWidth

    implicitWidth: lay.implicitWidth
    implicitHeight: lay.implicitHeight
    Layout.preferredHeight: lay.implicitHeight

    Component.onCompleted: {
        relayoutTimer.triggered()
    }

    /**
     * twinFormLayouts: list<FormLayout>
     * If for some implementation reason multiple FormLayouts has to appear
     * on the same page, they can have each other in twinFormLayouts,
     * so they will vertically align each other perfectly
     * @since 5.53
     */
    //should be list<FormLayout> but we can't have a recursive declaration
    property list<Item> twinFormLayouts

    Layout.fillWidth: true

    GridLayout {
        id: lay
        property int wideImplicitWidth
        columns: root.wideMode ? 2 : 1
        rowSpacing: Kirigami.Units.smallSpacing
        columnSpacing: Kirigami.Units.smallSpacing
        property var knownItems: []
        property var buddies: []
        property int knownItemsImplicitWidth: {
            var hint = 0;
            for (var i in knownItems) {
                hint = Math.max(hint, knownItems[i].Layout.preferredWidth > 0 ? knownItems[i].Layout.preferredWidth : knownItems[i].implicitWidth);
            }
            return hint;
        }
        property int buddiesImplicitWidth: {
            var hint = 0;
            for (var i in buddies) {
                if (buddies[i].visible) {
                    hint = Math.max(hint, buddies[i].implicitWidth);
                }
            }
            return hint;
        }
        anchors {
            left: root.wideMode ? undefined : parent.left
            top: parent.top
            //to make room for the invisible spacer elements
            topMargin: -lay.columnSpacing
           // right: parent.right
           horizontalCenter: root.wideMode ? parent.horizontalCenter : undefined
        }
        width: Math.min(implicitWidth, parent.width)
        Timer {
            id: hintCompression
            onTriggered: {
                if (root.wideMode) {
                    lay.wideImplicitWidth = lay.implicitWidth;
                }
            }
        }
        onImplicitWidthChanged: hintCompression.restart();
        //This invisible row is used to sync alignment between multiple layouts
        Item {
            Layout.preferredWidth: {
                var hint = 1;
                for (var i in root.twinFormLayouts) {
                    hint = Math.max(hint, root.twinFormLayouts[i].children[0].buddiesImplicitWidth);
                }
                return hint;
            }
        }
        Item {
            Layout.preferredWidth: {
                var hint = 1;
                for (var i in root.twinFormLayouts) {
                    hint = Math.max(hint, root.twinFormLayouts[i].children[0].knownItemsImplicitWidth);
                }
                return hint;
            }
        }
    }

    Item {
        id: temp
    }

    Timer {
        id: relayoutTimer
        interval: 0
        onTriggered: {
            var __items = children;
            //exclude the layout and temp
            for (var i = 2; i < __items.length; ++i) {
                var item = __items[i];

                //skip items that are already there
                if (lay.knownItems.indexOf(item) != -1 ||
                    //exclude Repeaters
                    //NOTE: this is an heuristic but there are't better ways
                    (item.hasOwnProperty("model") && item.model !== undefined && item.children.length === 0)) {
                    continue;
                }
                lay.knownItems.push(item);

                var itemContainer = itemComponent.createObject(temp, {"item": item})

                //if section, label goes after the separator
                if (item.Kirigami.FormData.isSection) {
                    //put an extra spacer
                    var placeHolder = placeHolderComponent.createObject(lay, {"item": item});
                    itemContainer.parent = lay;
                }

                var buddy;
                if (item.Kirigami.FormData.checkable) {
                    buddy = checkableBuddyComponent.createObject(lay, {"item": item})
                } else {
                    buddy = buddyComponent.createObject(lay, {"item": item})
                }

                itemContainer.parent = lay;
                lay.buddies.push(buddy);
            }
            lay.knownItemsChanged();
            lay.buddiesChanged();
            hintCompression.triggered();
        }
    }

    onChildrenChanged: relayoutTimer.restart();

    Component {
        id: itemComponent
        Item {
            id: container
            property var item
            enabled: item.enabled
            visible: item.visible

            //NOTE: work around a  GridLayout quirk which doesn't lay out items with null size hints causing things to be laid out incorrectly in some cases
            implicitWidth: Math.max(item.implicitWidth, 1)
            implicitHeight: Math.max(item.implicitHeight, 1)
            Layout.preferredWidth: Math.max(1, item.Layout.preferredWidth > 0 ? item.Layout.preferredWidth : item.implicitWidth)
            Layout.preferredHeight: Math.max(1, item.Layout.preferredHeight > 0 ? item.Layout.preferredHeight : item.implicitHeight)

            Layout.minimumWidth: item.Layout.minimumWidth
            Layout.minimumHeight: item.Layout.minimumHeight

            Layout.maximumWidth: item.Layout.maximumWidth
            Layout.maximumHeight: item.Layout.maximumHeight

            Layout.leftMargin: root.wideMode ? 0 : Kirigami.Units.largeSpacing
            Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter
            Layout.fillWidth: item.Layout.fillWidth || item.Kirigami.FormData.isSection
            Layout.columnSpan: item.Kirigami.FormData.isSection ? lay.columns : 1
            onItemChanged: {
                if (!item) {
                    container.destroy();
                }
            }
            onXChanged: item.x = x + lay.x;
            //Assume lay.y is always 0
            onYChanged: item.y = y + lay.y;
            onWidthChanged: item.width = width;
            Component.onCompleted: item.x = x + lay.x;
            Connections {
                target: lay
                onXChanged: item.x = x + lay.x;
            }
        }
    }
    Component {
        id: placeHolderComponent
        Item {
            property var item
            enabled: item.enabled
            visible: item.visible
            width: Kirigami.Units.smallSpacing
            height: Kirigami.Units.smallSpacing
            Layout.topMargin: item.height > 0 ? Kirigami.Units.smallSpacing : 0 
            onItemChanged: {
                if (!item) {
                    labelItem.destroy();
                }
            }
        }
    }
    Component {
        id: buddyComponent
        Kirigami.Heading {
            id: labelItem

            property var item
            enabled: item.enabled
            visible: item.visible
            Kirigami.MnemonicData.enabled: item.Kirigami.FormData.buddyFor && item.Kirigami.FormData.buddyFor.activeFocusOnTab
            Kirigami.MnemonicData.controlType: Kirigami.MnemonicData.FormLabel
            Kirigami.MnemonicData.label: item.Kirigami.FormData.label
            text: Kirigami.MnemonicData.richTextLabel

            level: item.Kirigami.FormData.isSection ? 3 : 5

            Layout.columnSpan: item.Kirigami.FormData.isSection ? lay.columns : 1
            Layout.preferredHeight: item.Kirigami.FormData.label.length > 0 ? Math.max(implicitHeight, item.Kirigami.FormData.buddyFor.height) : Kirigami.Units.smallSpacing

            Layout.alignment: item.Kirigami.FormData.isSection
                             ? Qt.AlignLeft
                             : (root.wideMode
                                ? (Qt.AlignRight | Qt.AlignTop)
                                : (Qt.AlignLeft | Qt.AlignBottom))
            verticalAlignment: root.wideMode ? Text.AlignVCenter : Text.AlignBottom

            //Layout.topMargin: item.Kirigami.FormData.buddyFor.y
            onItemChanged: {
                if (!item) {
                    labelItem.destroy();
                }
            }
            Shortcut {
                sequence: labelItem.Kirigami.MnemonicData.sequence
                onActivated: item.Kirigami.FormData.buddyFor.forceActiveFocus()
            }
        }
    }
    Component {
        id: checkableBuddyComponent
        CheckBox {
            id: labelItem
            property var item
            visible: item.visible
            Kirigami.MnemonicData.enabled: item.Kirigami.FormData.buddyFor && item.Kirigami.FormData.buddyFor.activeFocusOnTab
            Kirigami.MnemonicData.controlType: Kirigami.MnemonicData.FormLabel
            Kirigami.MnemonicData.label: item.Kirigami.FormData.label

            Layout.columnSpan: item.Kirigami.FormData.isSection ? lay.columns : 1
            Layout.preferredHeight: item.Kirigami.FormData.label.length > 0 ? implicitHeight : Kirigami.Units.smallSpacing

            Layout.alignment: item.Kirigami.FormData.isSection
                             ? Qt.AlignLeft
                             : (root.wideMode
                                ? (Qt.AlignRight | (item.Kirigami.FormData.buddyFor.height > height * 2 ? Qt.AlignTop : Qt.AlignVCenter))
                                : (Qt.AlignLeft | Qt.AlignBottom))
            Layout.topMargin: item.Kirigami.FormData.buddyFor.height > implicitHeight * 2 ? Kirigami.Units.smallSpacing/2 : 0

            activeFocusOnTab: indicator.visible && indicator.enabled
            text: labelItem.Kirigami.MnemonicData.richTextLabel
            enabled: labelItem.item.Kirigami.FormData.enabled
            checked: labelItem.item.Kirigami.FormData.checked

            onItemChanged: {
                if (!item) {
                    labelItem.destroy();
                }
            }
            Shortcut {
                sequence: labelItem.Kirigami.MnemonicData.sequence
                onActivated: {
                    checked = !checked
                    item.Kirigami.FormData.buddyFor.forceActiveFocus()
                }
            }
            onCheckedChanged: {
                item.Kirigami.FormData.checked = checked
            }
            contentItem: Kirigami.Heading {
                id: labelItemHeading
                level: labelItem.item.Kirigami.FormData.isSection ? 3 : 5
                text: labelItem.text
                verticalAlignment: root.wideMode ? Text.AlignVCenter : Text.AlignBottom
                enabled: labelItem.item.Kirigami.FormData.enabled
                leftPadding: parent.indicator.width
            }
            Rectangle {
                enabled: labelItem.indicator.enabled
                anchors.left: labelItemHeading.left
                anchors.right: labelItemHeading.right
                anchors.top: labelItemHeading.bottom
                anchors.leftMargin: labelItemHeading.leftPadding
                height: 1 * Kirigami.Units.devicePixelRatio
                color: Kirigami.Theme.highlightColor
                visible: labelItem.activeFocus && labelItem.indicator.visible
            }
        }
    }
}
