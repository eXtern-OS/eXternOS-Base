/*
   Copyright (c) 2015 Marco Martin <mart@kde.org>
   Copyright (c) 2019 Dan Leinir Turthra Jensen <admin@leinir.dk>

   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Library General Public
   License version 2 as published by the Free Software Foundation.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Library General Public License for more details.

   You should have received a copy of the GNU Library General Public License
   along with this library; see the file COPYING.LIB.  If not, write to
   the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
   Boston, MA 02110-1301, USA.
*/

import QtQuick 2.11
import QtQuick.Controls 2.11 as Controls
import QtQuick.Templates 2.11 as T2
import QtQuick.Layouts 1.11
import QtGraphicalEffects 1.11

import org.kde.kirigami 2.2 as Kirigami

/**
 * Base delegate for KControlmodules based on Grid views of thumbnails
 * Use the onClicked signal handler for managing the main action when
 * the user clicks on the tile, modified from the original GridDelegate
 * from the KCM module
 * @inherits QtQuick.Templates.ItemDelegate
 */
T2.ItemDelegate {
    id: delegate

    /**
     * toolTip: string
     * string for a tooltip for the whole delegate
     */
    property string toolTip

    /**
     * tile: Item
     * the item actually implementing the tile: the visualization is up to the implementation
     */
    property alias tile: thumbnailArea.data

    /**
     * thumbnailAvailable: bool
     * Set it to true when a tile is actually available: when false,
     * a default icon will be shown instead of the actual tile.
     */
    property bool thumbnailAvailable: false

    /**
     * actions: list<Action>
     * A list of extra actions for the thumbnails. They will be shown as
     * icons on the bottom-right corner of the tile on mouse over
     */
    property list<QtObject> actions

    /**
     * actionsAnchors: anchors
     * The anchors of the actions listing
     */
    property alias actionsAnchors: actionsScope.anchors

    width: GridView.view.cellWidth
    height: GridView.view.cellHeight
    hoverEnabled: true

    Rectangle {
        id: tile
        anchors.centerIn: parent
        width: Kirigami.Settings.isMobile ? delegate.width - Kirigami.Units.gridUnit : Math.min(delegate.GridView.view.implicitCellWidth, delegate.width - Kirigami.Units.gridUnit)
        height: Math.min(delegate.GridView.view.implicitCellHeight, delegate.height - Kirigami.Units.gridUnit)
        radius: Kirigami.Units.smallSpacing
        Kirigami.Theme.inherit: false
        Kirigami.Theme.colorSet: Kirigami.Theme.View

        color: {
            if (delegate.GridView.isCurrentItem) {
                return Kirigami.Theme.highlightColor;
            } else if (parent.hovered) {
                return Kirigami.Theme.highlightColor;
            } else {
                return Kirigami.Theme.backgroundColor;
            }
        }
        Behavior on color {
            ColorAnimation {
                duration: Kirigami.Units.longDuration
                easing.type: Easing.OutQuad
            }
        }

        Rectangle {
            id: thumbnailArea
            radius: Kirigami.Units.smallSpacing/2
            anchors {
                fill: parent
                margins: Kirigami.Units.smallSpacing
            }

            color: Kirigami.Theme.backgroundColor
            Kirigami.Icon {
                visible: !delegate.thumbnailAvailable
                anchors.centerIn: parent
                width: Kirigami.Units.iconSizes.large
                height: width
                source: delegate.text === i18n("None") ? "edit-none" : "view-preview"
            }
        }

        Rectangle {
            anchors.fill: thumbnailArea
            visible: actionsColumn.children.length > 0
            opacity: Kirigami.Settings.isMobile || delegate.hovered || (actionsScope.focus) ? 1 : 0
            radius: Kirigami.Units.smallSpacing
            color: Kirigami.Settings.isMobile ? "transparent" : Qt.rgba(1, 1, 1, 0.2)

            Behavior on opacity {
                NumberAnimation {
                    duration: Kirigami.Units.longDuration
                    easing.type: Easing.OutQuad
                }
            }

            FocusScope {
                id: actionsScope

                anchors {
                    right: parent.right
                    rightMargin: Kirigami.Units.smallSpacing
                    top: parent.top
                    topMargin: Kirigami.Units.smallSpacing
                }
                width: actionsColumn.width
                height: actionsColumn.height

                ColumnLayout {
                    id: actionsColumn

                    Repeater {
                        model: delegate.actions
                        delegate: Controls.Button {
                            icon.name: modelData.iconName
                            text: modelData.text
                            activeFocusOnTab: focus || delegate.focus
                            onClicked: {
                                delegate.clicked()
                                modelData.trigger()
                            }
                            enabled: modelData.enabled
                            visible: modelData.visible
                            //NOTE: there aren't any global settings where to take "official" tooltip timeouts
                            Controls.ToolTip.delay: 1000
                            Controls.ToolTip.timeout: 5000
                            Controls.ToolTip.visible: (Kirigami.Settings.isMobile ? pressed : hovered) && modelData.tooltip.length > 0
                            Controls.ToolTip.text: modelData.tooltip
                        }
                    }
                }
            }
        }
        // Bug 397367: explicitly using "delegate" as otherwise it crashes when switching between KCMs
        layer.enabled: delegate.GraphicsInfo.api === GraphicsInfo.OpenGL
        layer.effect: DropShadow {
            horizontalOffset: 0
            verticalOffset: 2
            radius: 10
            samples: 32
            color: Qt.rgba(0, 0, 0, 0.3)
        }
    }

    Controls.ToolTip.delay: 1000
    Controls.ToolTip.timeout: 5000
    Controls.ToolTip.visible: hovered && delegate.toolTip.length > 0
    Controls.ToolTip.text: toolTip
}
