/*
   Copyright (c) 2017 Marco Martin <mart@kde.org>

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

import QtQuick 2.5
import QtQuick.Controls 2.5 as QQC2
import QtQuick.Layouts 1.1
import org.kde.kirigami 2.10 as Kirigami

Kirigami.ScrollablePage {
    id: mainColumn
    Component.onCompleted: searchField.forceActiveFocus()

    header: Rectangle {
        Kirigami.Theme.colorSet: Kirigami.Theme.Window
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor
        width: mainColumn.width
        height: Math.round(Kirigami.Units.gridUnit * 2.5)
        RowLayout {
            id: searchLayout
            spacing: Kirigami.Units.smallSpacing
            anchors {
                fill: parent
                margins: Kirigami.Units.smallSpacing
            }

            QQC2.ToolButton {
                id: menuButton
                icon.name: "application-menu"
                checkable: true
                checked: systemsettings.actionMenuVisible
                Layout.maximumWidth: Kirigami.Units.iconSizes.smallMedium + Kirigami.Units.smallSpacing * 2
                Layout.maximumHeight: width
                Keys.onBacktabPressed: {
                    root.focusPreviousRequest()
                }
                onClicked: systemsettings.showActionMenu(mapToGlobal(0, height))

                QQC2.ToolTip {
                    text: i18n("Show menu")
                }
            }

            Kirigami.SearchField {
                id: searchField
                focus: true
                Layout.minimumHeight: Layout.maximumHeight
                Layout.maximumHeight: Kirigami.Units.iconSizes.smallMedium + Kirigami.Units.smallSpacing * 2
                Layout.fillWidth: true
                onTextChanged: {
                    systemsettings.categoryModel.filterRegExp = text;
                }
                KeyNavigation.tab: categoryView
            }
        }
        Kirigami.Separator {
            anchors {
                left: parent.left
                right: parent.right
                top: parent.bottom
            }
        }
    }
    background: Rectangle {
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        color: Kirigami.Theme.backgroundColor
    }
    Kirigami.Heading {
        anchors.centerIn: parent
        width: parent.width * 0.7
        wrapMode: Text.WordWrap
        horizontalAlignment: Text.AlignHCenter
        text: i18nc("A search yielded no results", "No items matching your search")
        opacity: categoryView.count == 0 ? 0.3 : 0
        Behavior on opacity {
            OpacityAnimator {
                duration: Kirigami.Units.longDuration
                easing.type: Easing.InOutQuad
            }
        }
    }
    ListView {
        id: categoryView
        anchors.fill: parent
        model: systemsettings.categoryModel
        currentIndex: systemsettings.activeCategory
        onContentYChanged: systemsettings.hideToolTip();
        activeFocusOnTab: true
        keyNavigationWraps: true
        Accessible.role: Accessible.List
        Keys.onTabPressed: {
            if (applicationWindow().wideScreen) {
                subCategoryColumn.focus = true;
            } else {
                root.focusNextRequest();
            }
        }
        section {
            property: "categoryDisplayRole"
            delegate: Kirigami.ListSectionHeader {
                width: categoryView.width
                label: section
            }
        }

        delegate: Kirigami.BasicListItem {
            id: delegate
            icon: model.decoration
            label: model.display
            separatorVisible: false
            Accessible.role: Accessible.ListItem
            Accessible.name: model.display
            onClicked: {
                if (systemsettings.activeCategory == index) {
                    root.pageStack.currentIndex = 1;
                } else {
                    systemsettings.activeCategory = index;
                    subCategoryColumn.title = model.display;
                }
            }
            onHoveredChanged: {
                if (hovered) {
                    systemsettings.requestToolTip(index, delegate.mapToItem(root, 0, 0, width, height));
                } else {
                    systemsettings.hideToolTip();
                }
            }
            onFocusChanged: {
                if (focus) {
                    onCurrentIndexChanged: categoryView.positionViewAtIndex(index, ListView.Contain);
                }
            }
            highlighted: systemsettings.activeCategory == index
            Keys.onEnterPressed: clicked();
            Keys.onReturnPressed: clicked();
        }
    }
}
