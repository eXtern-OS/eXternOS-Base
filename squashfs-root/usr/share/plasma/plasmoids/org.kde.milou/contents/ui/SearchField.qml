/*
 * This file is part of the KDE Milou Project
 * Copyright (C) 2013-2014 Vishesh Handa <me@vhanda.in>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) version 3, or any
 * later version accepted by the membership of KDE e.V. (or its
 * successor approved by the membership of KDE e.V.), which shall
 * act as a proxy defined in Section 6 of version 3 of the license.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

import QtQuick 2.1

import org.kde.plasma.components 2.0 as PlasmaComponents
import "globals.js" as Globals

/*
 * The SearchField is a simple text field widget. The only complex part
 * is the internal timer to reduce the number of textChanged signals
 * using searchTextChanged.
 */
Item {
    signal searchTextChanged()
    property alias text: textField.text

    height: childrenRect.height
    width: Globals.PlasmoidWidth

    PlasmaComponents.TextField {
        id: textField
        clearButtonShown: true
        placeholderText: i18n("Search...")
        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
        }

        focus: true
        Keys.forwardTo: listView

        // We do not want to send the text instantly as that would result
        // in too many queries. Therefore we add a small 200msec delay
        Timer {
            id: timer
            interval: 200
            onTriggered: searchTextChanged()
        }

        onTextChanged: timer.restart()
    }

    function selectAll() {
        textField.selectAll()
    }

    function setFocus() {
        textField.focus = true
    }

    Keys.onEscapePressed: {
        textField.text = ""
    }
}
