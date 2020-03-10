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
import org.kde.plasma.core 2.0 as PlasmaCore
import org.kde.plasma.extras 2.0 as PlasmaExtras
import org.kde.qtextracomponents 2.0 as QtExtra

import "../globals.js" as Globals

Item {
    property string title
    property variant keys
    property variant values
    property int length
    property string iconName

    width: childrenRect.width
    height: childrenRect.height

    Row {

        QtExtra.QIconItem {
            id: iconItem
            width: height
            height: rightSide.height

            icon: iconName
            smooth: true
        }

        Column {
            id: rightSide
            PlasmaComponents.Label {
                text: title
                height: Globals.TitleSize
                color: theme.textColor
                font.pointSize: theme.defaultFont.pointSize * 1.5
            }

            Repeater {
                model: length

                Row {
                    PlasmaComponents.Label {
                        text: keys[index] + " "
                        height: Globals.IconSize
                        color: theme.textColor
                        opacity: 0.5
                    }

                    PlasmaComponents.Label {
                        text: values[index]
                        height: Globals.IconSize
                        color: theme.textColor
                        elide: Text.ElideRight
                    }
                }
            }
        }
    }
}
