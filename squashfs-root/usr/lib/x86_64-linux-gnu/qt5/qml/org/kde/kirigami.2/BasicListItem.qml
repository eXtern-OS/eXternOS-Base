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

import QtQuick 2.1
import QtQuick.Layouts 1.2
import QtQuick.Controls 2.0 as QQC2
import org.kde.kirigami 2.4

/**
 * An item delegate for the primitive ListView component.
 *
 * It's intended to make all listviews look coherent.
 * It has a default icon and a label
 *
 */
AbstractListItem {
    id: listItem

    /**
     * string: bool
     * A single text label the list item will contain
     */
    property alias label: listItem.text

    /**
     * icon: var
     * A single icon that will be displayed in the list item.
     * The icon can be a grouped property with name,size,color etc, as QtQuickControls2 icons are defined.
     * The icon can also be either a QIcon, a string name of a fdo compatible name,
     * or any url accepted by the Image element.
     */
    property var icon

    /**
     * iconSize: int
     * The preferred size for the icon
     * @since 2.5
     */
    property alias iconSize: iconItem.size

    /**
     * iconColor: color
     * The color the icon should be colorized to.
     * By default it will be the text color.
     * If the icon shouldn't be colorized in any way, set it to "transparent"
     * @since 2.7
     */
    property alias iconColor: iconItem.color

    /**
     * reserveSpaceForIcon: bool
     * If true, even when there is no icon the space will be reserved for it
     * It's useful in layouts where only some entries have an icon,
     * having the text all horizontally aligned
     */
    property alias reserveSpaceForIcon: iconItem.visible

    /**
     * reserveSpaceForLabel: bool
     * If false, the label will not try to be as wide as possible
     * It's useful in layouts containing entries without text
     */
    property alias reserveSpaceForLabel: labelItem.visible

    default property alias _basicDefault: layout.data

    icon: action ? action.icon.name || action.icon.source : undefined
    contentItem: RowLayout {
        id: layout
        spacing: LayoutMirroring.enabled ? listItem.rightPadding : listItem.leftPadding
        Icon {
            id: iconItem
            source: {
                if (listItem.icon && listItem.icon.hasOwnProperty) {
                    if (listItem.icon.hasOwnProperty("name") && listItem.icon.name !== "")
                        return listItem.icon.name;
                    if (listItem.icon.hasOwnProperty("source"))
                        return listItem.icon.source;
                }
                return listItem.icon;
            }
            property int size: Units.iconSizes.smallMedium
            Layout.minimumHeight: size
            Layout.maximumHeight: size
            Layout.minimumWidth: size
            selected: (listItem.highlighted || listItem.checked || (listItem.pressed && listItem.supportsMouseEvents))
            opacity: 1
        }
        QQC2.Label {
            id: labelItem
            text: listItem.text
            Layout.fillWidth: true
            color: (listItem.highlighted || listItem.checked || (listItem.pressed && listItem.supportsMouseEvents)) ? listItem.activeTextColor : listItem.textColor
            elide: Text.ElideRight
            font: listItem.font
            opacity: 1
        }
    }
}
