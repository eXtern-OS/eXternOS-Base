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

import org.kde.kirigami 2.5 as Kirigami

Kirigami.ApplicationItem {
    id: root
    implicitWidth: wideScreen ? Kirigami.Units.gridUnit * 30 :  Kirigami.Units.gridUnit * 15
    pageStack.initialPage: mainColumn
    pageStack.defaultColumnWidth: wideScreen ? root.width / 2 : root.width
    
    LayoutMirroring.enabled: Qt.application.layoutDirection === Qt.RightToLeft
    LayoutMirroring.childrenInherit: true

    signal focusNextRequest()
    signal focusPreviousRequest()

    function focusFirstChild() {
        mainColumn.focus = true;
    }

    function focusLastChild() {
        subCategoryColumn.focus = true;
    }

    wideScreen: pageStack.depth > 1 && systemsettings.width > Kirigami.Units.gridUnit * 70
    CategoriesPage {
        id: mainColumn
        focus: true
    }

    SubCategoryPage {
        id: subCategoryColumn
        KeyNavigation.left: mainColumn
    }
    Kirigami.Separator {
        z: 999
        anchors {
            top: parent.top
            right: parent.right
            bottom: parent.bottom
        }
    }
}
