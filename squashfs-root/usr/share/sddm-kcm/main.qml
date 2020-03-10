/*
    Copyright 2013 by Reza Fatahilah Shah <rshah0385@kireihana.com>
    Copyright 2019 by Filip Fila <filipfila.kde@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
import QtQuick 2.4
import QtQuick.Window 2.2
import QtQuick.Layouts 1.12
import QtQuick.Controls 2.4
import org.kde.kirigami 2.4 as Kirigami
import QtGraphicalEffects 1.0

Rectangle {
    id: root
    //WORKAROUND: makes the rectangle's color match the background color
    color: Qt.tint(palette.window, Qt.rgba(palette.base.r, palette.base.g, palette.base.b, 0.3))
    height: Kirigami.Units.gridUnit * 24

    property string themeName: ""
    property string previewPath: ""
    property string authorName: ""
    property string description: ""
    property string license: ""
    property string email: ""
    property string website: ""
    property string copyright: ""
    property string version: ""

    DropShadow {
        source: previewImage.available ? previewImage : noPreviewFrame
        anchors.fill: previewImage.available ? previewImage : noPreviewFrame
        verticalOffset: 2
        radius: 10
        samples: 32
        color: Qt.rgba(0, 0, 0, 0.3)
    }

    Image {
        id: previewImage
        readonly property bool available: status === Image.Ready || status === Image.Loading
        visible: available
        source: previewPath
        sourceSize.width: width  * Screen.devicePixelRatio
        sourceSize.height: height * Screen.devicePixelRatio
        anchors {
            top: root.top
            left: root.left
            right: root.right
            margins: Math.round(units.smallSpacing * 1.5)
        }
        fillMode: Image.PreserveAspectFit
    }

    Rectangle {
        id: noPreviewFrame
        visible: !previewImage.available
        radius: units.smallSpacing
        anchors {
            top: root.top
            left: root.left
            right: root.right
            margins: Math.round(units.smallSpacing * 1.5)
        }
        height: Math.round(width * 0.5625) // 16:9 aspect ratio
        color: Kirigami.Theme.backgroundColor

        ColumnLayout{
            anchors.centerIn: parent

            Kirigami.Icon {
                Layout.alignment : Qt.AlignHCenter
                width: units.iconSizes.huge
                height: width
                source: "view-preview"
            }

            Kirigami.Heading {
                id: noPreviewText
                text: i18n("No preview available")
            }
        }
    }

    ColumnLayout {
        id: column
        width: previewImage.paintedWidth
        anchors {
            top: previewImage.available ? previewImage.bottom : noPreviewFrame.bottom
            left: previewImage.available ? previewImage.left : noPreviewFrame.left
            right: previewImage.available ? previewImage.right : noPreviewFrame.right
            topMargin: Math.round(units.smallSpacing * 1.5)
        }

        Kirigami.Heading {
            text: themeName + " (" + version + ")"
            level: 2
            font.bold: true
            font.weight: Font.Bold
            Layout.fillWidth: true
            wrapMode: Text.Wrap
        }

        Label {
            text: description + i18n(", by ") + authorName + " (" + license + ")"
            Layout.fillWidth: true
            wrapMode: Text.Wrap
        }

        Label {
            id: url
            visible: website !== ""
            text:("<a href='"+website+"'>"+website+"</a>")
            onLinkActivated: Qt.openUrlExternally(link)
            font.pointSize: theme.smallestFont.pointSize
            Layout.fillWidth: true
            wrapMode: Text.Wrap
        }

        Label {
            id: mail
            visible: email !== ""
            text: ("<a href='"+email+"'>"+email+"</a>")
            onLinkActivated: Qt.openUrlExternally("mailto:"+email+"")
            font.pointSize: theme.smallestFont.pointSize
            Layout.fillWidth: true
            Layout.bottomMargin: Math.round(units.smallSpacing * 1.5)
            wrapMode: Text.Wrap
        }
    }

    SystemPalette {
        id: palette
        colorGroup: SystemPalette.Active
    }
}
