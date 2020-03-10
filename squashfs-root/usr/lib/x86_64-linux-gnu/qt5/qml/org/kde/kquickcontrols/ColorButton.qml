/*
 * Copyright (C) 2015 David Edmundson <davidedmundson@kde.org>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License or (at your option) version 3 or any later version
 * accepted by the membership of KDE e.V. (or its successor approved
 * by the membership of KDE e.V.), which shall act as a proxy
 * defined in Section 14 of version 3 of the license.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>
 */

import QtQuick 2.2
import QtQuick.Controls 1.2 as QtControls
import QtQuick.Dialogs 1.0 as QtDialogs

/**
 * @short A pushbutton to display or allow user selection of a color.
 *
 * This widget can be used to display or allow user selection of a color.
 *
 * @inherits QtQuick.Controls.Button
 */
QtControls.Button {
    id: colorPicker

    /**
     * The user selected color
     */
    property alias color: colorDialog.color

    /**
     * Title to show in the dialog
     */
    property alias dialogTitle: colorDialog.title

    /**
     * The color which the user has currently selected whilst the dialog is open
     * For the color that is set when the dialog is accepted, use the color property.
     */
    property alias currentColor: colorDialog.currentColor

    /**
     * Allow the user to configure an alpha value
     */
    property alias showAlphaChannel: colorDialog.showAlphaChannel

    /**
     * This signal is emitted when the color dialog has been accepted
     *
     * @since 5.61
     */
    signal accepted(color color)

    readonly property real _buttonMarigns: 4 // same as QStyles. Remove if we can get this provided by the QQC theme

    implicitWidth: 40 + _buttonMarigns*2 //to perfectly clone kcolorbutton from kwidgetaddons


    //create a checkerboard background for alpha to be adjusted
    Canvas {
        anchors.fill: colorBlock
        visible: colorDialog.color.a < 1

        onPaint: {
            var ctx = getContext('2d');

            ctx.fillStyle = "white";
            ctx.fillRect(0,0, ctx.width, ctx.height)

            ctx.fillStyle = "black";
            //in blocks of 16x16 draw two black squares of 8x8 in top left and bottom right
            for (var j=0;j<width;j+=16) {
                for (var i=0;i<height;i+=16) {
                    //top left, bottom right
                    ctx.fillRect(j,i,8,8);
                    ctx.fillRect(j+8,i+8,8,8);
                }
            }
        }

    }

    Rectangle {
        id: colorBlock

        anchors.centerIn: parent
        height: parent.height - _buttonMarigns*2
        width: parent.width - _buttonMarigns*2


        color: enabled ? colorDialog.color : disabledPalette.button

        SystemPalette {
            id: disabledPalette
            colorGroup: SystemPalette.Disabled
        }
    }

    QtDialogs.ColorDialog {
        id: colorDialog
        onAccepted: colorPicker.accepted(color)
    }

    onClicked: {
        colorDialog.open()
    }
}
