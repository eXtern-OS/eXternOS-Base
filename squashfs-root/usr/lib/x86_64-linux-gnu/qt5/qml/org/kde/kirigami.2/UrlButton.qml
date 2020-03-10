/*
 *   Copyright (C) 2018 Aleix Pol Gonzalez <aleixpol@blue-systems.com>
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU Library/Lesser General Public License
 *   version 2, or (at your option) any later version, as published by the
 *   Free Software Foundation
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details
 *
 *   You should have received a copy of the GNU Library/Lesser General Public
 *   License along with this program; if not, write to the
 *   Free Software Foundation, Inc.,
 *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */

import QtQuick 2.2
import org.kde.kirigami.private 2.6 as KirigamiPrivate
import QtQuick.Controls 2.1 as QQC2

/**
 * A link button that contains a URL
 *
 * It will open the url by default, allow to copy it if triggered with the
 * secondary mouse button.
 *
 * @since 5.63
 * @since org.kde.kirigami 2.6
 */
LinkButton
{
    id: button
    property string url
    text: url
    visible: text.length > 0
    acceptedButtons: Qt.LeftButton | Qt.RightButton

    onPressed: if (mouse.button === Qt.RightButton) {
        menu.popup()
    }
    onClicked: if (mouse.button !== Qt.RightButton) {
        Qt.openUrlExternally(url)
    }

    QQC2.Menu {
        id: menu
        QQC2.MenuItem {
            text: qsTr("Copy link address")
            onClicked: KirigamiPrivate.CopyHelperPrivate.copyTextToClipboard(button.url)
        }
    }
}
