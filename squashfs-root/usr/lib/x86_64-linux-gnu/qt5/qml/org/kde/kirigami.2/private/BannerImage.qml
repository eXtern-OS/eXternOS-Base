/*
 *   Copyright 2018 Marco Martin <mart@kde.org>
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
import QtQuick.Layouts 1.2
import QtGraphicalEffects 1.0
import org.kde.kirigami 2.4 as Kirigami

/**
 * This Component is used as the header of GlobalDrawer and as the header
 * of Card, It can be accessed there as a grouped property but can never
 * be instantiated directly
 */
Image {
    id: root

    /*
     * FIXME: compatibility
     */
    property alias imageSource: root.source
    property alias iconSource: root.titleIcon
    
    /**
     * title: string
     * A title to be displayed on top of the image
     */
    property alias title: heading.text

    /**
     * icon: var
     * An icon to be displayed alongside the title.
     * It can be a QIcon, a fdo-compatible icon name, or any url understood by Image
     */
    property alias titleIcon: headingIcon.source

    /**
     * titleAlignment: Qt.Alignment
     */
    property int titleAlignment: Qt.AlignTop | Qt.AlignLeft

    /**
     * titleLevel: a Kirigami Heading level, default 1
     */
    property alias titleLevel: heading.level

    /**
     * wrapMode: if the header should be able to do wrapping
     */
    property alias titleWrapMode: heading.wrapMode

    property int leftPadding: headingIcon.valid ? Kirigami.Units.smallSpacing * 2 : Kirigami.Units.largeSpacing
    property int topPadding: headingIcon.valid ? Kirigami.Units.smallSpacing * 2 : Kirigami.Units.largeSpacing
    property int rightPadding: headingIcon.valid ? Kirigami.Units.smallSpacing * 2 : Kirigami.Units.largeSpacing
    property int bottomPadding: headingIcon.valid ? Kirigami.Units.smallSpacing * 2 : Kirigami.Units.largeSpacing

    Layout.fillWidth: true

    Layout.preferredWidth: titleLayout.implicitWidth || sourceSize.width
    Layout.preferredHeight: titleLayout.completed && source != "" ? width/(sourceSize.width / sourceSize.height) : Layout.minimumHeight
    Layout.minimumHeight: titleLayout.implicitHeight > 0 ? titleLayout.implicitHeight + Kirigami.Units.smallSpacing * 2 : 0
    property int implicitWidth: Layout.preferredWidth

    readonly property bool empty: bannerImage.title !== undefined && bannerImage.title.length === 0 &&
                                  bannerImage.source !== undefined && bannerImage.source.length === 0 &&
                                  bannerImage.titleIcon !== undefined &&bannerImage.titleIcon.length === 0

    fillMode: Image.PreserveAspectCrop
    asynchronous: true

    Component.onCompleted: {
        titleLayout.completed = true;
    }

    LinearGradient {
        anchors {
            left: parent.left
            right: parent.right
            top: root.status != 
Image.Ready || (root.titleAlignment & Qt.AlignTop) ? parent.top : undefined
            bottom: root.status != 
Image.Ready || (root.titleAlignment & Qt.AlignBottom) ? parent.bottom : undefined
        }
        visible: root.source != "" && root.title != "" && ((root.titleAlignment & Qt.AlignTop) || (root.titleAlignment & Qt.AlignBottom))
        height: Math.min(parent.height, titleLayout.height * 2)
        start: Qt.point(0, 0)
        end: Qt.point(0, height)
        gradient: Gradient {
            GradientStop {
                position: (root.titleAlignment & Qt.AlignTop) ? 0.0 : 1.0
                color: Qt.rgba(0, 0, 0, 0.8)
            }
            GradientStop {
                position: (root.titleAlignment & Qt.AlignTop) ? 1.0 : 0.0
                color: Qt.rgba(0, 0, 0, root.status == 
Image.Ready ? 0 : 0.3)
            }
        }
    }

    RowLayout {
        id: titleLayout
        property bool completed: false
        anchors {
            left: root.titleAlignment & Qt.AlignLeft ? parent.left : undefined
            top: root.titleAlignment & Qt.AlignTop ? parent.top : undefined
            right: root.titleAlignment & Qt.AlignRight ? parent.right : undefined
            bottom: root.titleAlignment & Qt.AlignBottom ? parent.bottom : undefined
            horizontalCenter: root.titleAlignment & Qt.AlignHCenter ? parent.horizontalCenter : undefined
            verticalCenter: root.titleAlignment & Qt.AlignVCenter ? parent.verticalCenter : undefined

            leftMargin: root.leftPadding
            topMargin: root.topPadding
            rightMargin: root.rightPadding
            bottomMargin: root.bottomPadding
        }
        width: Math.min(implicitWidth, parent.width -root.leftPadding - root.rightPadding)
        height: Math.min(implicitHeight, parent.height - root.topPadding - root.bottomPadding)
        Kirigami.Icon {
            id: headingIcon
            Layout.minimumWidth: Kirigami.Units.iconSizes.large
            Layout.minimumHeight: width
            visible: valid
            isMask: false
        }
        Kirigami.Heading {
            id: heading
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: text.length > 0
            level: 1
            color: source != "" ? "white" : Kirigami.Theme.textColor
            wrapMode: Text.NoWrap
            elide: Text.ElideRight
        }
    }
}
