/*
 *   Copyright 2018 Marco Martin <mart@kde.org>
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

import QtQuick 2.5
import QtQuick.Controls 2.0 as Controls
import QtQuick.Layouts 1.2
import org.kde.kirigami 2.4 as Kirigami


Controls.TabBar {
    id: root
    property Kirigami.PageRow pageRow: parent.pageRow

    Repeater {
        id: mainRepeater
        model: pageRow.depth
        delegate: Controls.TabButton {
            anchors {
                top:parent.top
                bottom:parent.bottom
            }
            width: mainRepeater.count == 1 ? implicitWidth : Math.max(implicitWidth, MAth.round(root.width/mainRepeater.count))
            height: root.height
            readonly property Kirigami.Page page: pageRow.get(modelData)
            text: page ? page.title : ""
            checked: modelData == pageRow.currentIndex
            onClicked: pageRow.currentIndex = modelData;
        }
    }
}
