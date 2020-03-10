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

import org.kde.kirigami 2.5 as Kirigami

Kirigami.ScrollablePage {
    id: subCategoryColumn
    header: Rectangle {
        id: headerRect
        Kirigami.Theme.colorSet: Kirigami.Theme.Window
        Kirigami.Theme.inherit: false
        color: {
            if (headerControls.pressed) {
                return Kirigami.Theme.highlightColor;
            } else if (headerControls.containsMouse) {
                return Kirigami.Theme.hoverColor;
            } else {
                return Kirigami.Theme.backgroundColor;
            }
        }
        width: subCategoryColumn.width
        height: Math.round(Kirigami.Units.gridUnit * 2.5)

        MouseArea {
            id: headerControls
            Kirigami.Theme.colorSet: Kirigami.Theme.Button
            Kirigami.Theme.inherit: false
            anchors.fill: parent
            enabled: !applicationWindow().wideScreen
            hoverEnabled: true
            onClicked: root.pageStack.currentIndex = 0
            Accessible.role: Accessible.Button
            Accessible.name: i18n("Back")

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Kirigami.Units.largeSpacing

                Kirigami.Icon {
                    id: toolButtonIcon
                    visible: !applicationWindow().wideScreen
                    Layout.alignment: Qt.AlignVCenter
                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                    Layout.preferredWidth: Layout.preferredHeight

                    source: LayoutMirroring.enabled ? "go-next" : "go-previous"
                    color: {
                        if (headerControls.pressed) {
                            return Kirigami.Theme.highlightedTextColor;
                        } else {
                            return Kirigami.Theme.textColor;
                        }
                    }
                }

                Kirigami.Heading {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    level: 3
                    height: toolButtonIcon.height
                    text: subCategoryColumn.title
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                    color: {
                        if (headerControls.pressed) {
                            return Kirigami.Theme.highlightedTextColor;
                        } else {
                            return Kirigami.Theme.textColor;
                        }
                    }
                }
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
    ListView {
        id: subCategoryView
        anchors.fill: parent
        model: systemsettings.subCategoryModel
        currentIndex: systemsettings.activeSubCategory
        onContentYChanged: systemsettings.hideSubCategoryToolTip();
        activeFocusOnTab: true
        keyNavigationWraps: true
        Accessible.role: Accessible.List
        Keys.onTabPressed: root.focusNextRequest();
        Keys.onBacktabPressed: {
            mainColumn.focus = true;
        }
        onCountChanged: {
            if (count > 1) {
                if (root.pageStack.depth < 2) {
                    root.pageStack.push(subCategoryColumn);
                }
            } else {
                root.pageStack.pop(mainColumn)
            }
        }
        Connections {
            target: systemsettings
            onActiveSubCategoryChanged: {
                root.pageStack.currentIndex = 1;
                subCategoryView.forceActiveFocus();
            }
        }

        delegate: Kirigami.BasicListItem {
            id: delegate
            icon: model.decoration
            label: model.display
            separatorVisible: false
            onClicked: systemsettings.activeSubCategory = index
            onHoveredChanged: {
                if (hovered) {
                    systemsettings.requestSubCategoryToolTip(index, delegate.mapToItem(root, 0, 0, width, height));
                } else {
                    systemsettings.hideSubCategoryToolTip();
                }
            }
            onFocusChanged: {
                if (focus) {
                    onCurrentIndexChanged: subCategoryView.positionViewAtIndex(index, ListView.Contain);
                }
            }
            highlighted: systemsettings.activeSubCategory == index
            Keys.onEnterPressed: clicked();
            Keys.onReturnPressed: clicked();
        }
    }
}
