/*
 *   Copyright 2019 Marco Martin <mart@kde.org>
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

import QtQuick 2.6
import QtQuick.Controls 2.0 as QQC2
import QtQuick.Layouts 1.2
import org.kde.kirigami 2.5

BasicListItem {
    id: listItem

    readonly property bool isSeparator: modelData.hasOwnProperty("separator") && modelData.separator

    readonly property bool isExpandible: modelData && modelData.hasOwnProperty("expandible") && modelData.expandible

    checked: modelData.checked
    icon: modelData.icon
    separatorVisible: false
    reserveSpaceForIcon: !isSeparator
    reserveSpaceForLabel: !isSeparator

    label: model ? (model.tooltip ? model.tooltip : model.text) : (modelData.tooltip ? modelData.tooltip : modelData.text)
    hoverEnabled: (!isExpandible || root.collapsed) && !Settings.tabletMode
    sectionDelegate: isExpandible
    font.pointSize: isExpandible ? Theme.defaultFont.pointSize * 1.30 : Theme.defaultFont.pointSize

    enabled: !isExpandible && !isSeparator && (model ? model.enabled : modelData.enabled)
    visible: model ? model.visible : modelData.visible
    opacity: enabled || isExpandible ? 1.0 : 0.6

    Separator {
        id: separatorAction

        visible: listItem.isSeparator
        Layout.fillWidth: true
    
        ActionsMenu {
            id: actionsMenu
            y: Settings.isMobile ? -height : listItem.height
            z: 9999
            actions: modelData.children
            submenuComponent: Component {
                ActionsMenu {}
            }
        }
    }

    Icon {
        isMask: true
        Layout.alignment: Qt.AlignVCenter
        Layout.rightMargin: !Settings.isMobile && mainFlickable && mainFlickable.contentHeight > mainFlickable.height ? Units.gridUnit : 0
        Layout.preferredHeight: Units.iconSizes.small/2
        selected: listItem.checked || listItem.pressed
        Layout.preferredWidth: Layout.preferredHeight
        source: "go-up-symbolic"
        visible: !isExpandible  && !listItem.isSeparator && modelData.children!== undefined && modelData.children.length > 0
    }

    onPressed: {
        if (modelData.children.length > 0) {
            actionsMenu.open();
        }
    }
    onClicked: {
        if (modelData.children.length === 0) {
            root.drawerOpen = false;
        }

        if (modelData && modelData.trigger !== undefined) {
            modelData.trigger();
        // assume the model is a list of QAction or Action
        } else if (menu.model.length > index) {
            menu.model[index].trigger();
        } else {
            console.warning("Don't know how to trigger the action")
        }
    }
}
