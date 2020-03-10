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

import QtQuick 2.7
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.2 as QtControls
import org.kde.kirigami 2.2 as Kirigami
import org.kde.kcm 1.1 as KCM

/**
 * This component is intended to be used as the root item for most of the
 * KControl modules which are based upon a grid view of thumbnails, such as theme
 * or wallpaper selectors.
 * It has a big GridView as its main item, the implementation is free to add extra
 * content in the header or footer properties.
 * @code
 * import org.kde.kcm 1.1 as KCM
 * KCM.GridViewKCM {
 *     header: Item {...}
 *     view.model: kcm.model
 *     view.delegate: KCM.GridDelegate {...}
 *     footer: Item {...}
 * }
 * @endcode
 * @inherits org.kde.kirigami.Page
 */
Kirigami.Page {
    id: root

    /**
     * view: GridView
     * Exposes the internal GridView: in order to set a model or a delegate to it,
     * use the following code:
     * @code
     * import org.kde.kcm 1.1 as KCM
     * KCM.GridViewKCM {
     *     ...
     *     view.model: kcm.model
     *     view.delegate: KCM.GridDelegate {...}
     *     ...
     * }
     * @endcode
     */
    property alias view: scroll.view

    title: kcm.name
    implicitWidth: {
        var width = 0;

        // Show three columns at once, every colum occupies implicitCellWidth + Units.gridUnit
        width += 3 * (view.implicitCellWidth + Kirigami.Units.gridUnit);

        var scrollBar = scroll.QtControls.ScrollBar.vertical;
        width += scrollBar.width + scrollBar.leftPadding + scrollBar.rightPadding;

        width += scroll.leftPadding + scroll.rightPadding
        width += root.leftPadding + root.rightPadding;

        return width;
    }
    implicitHeight: view.implicitCellHeight * 3 + (header ? header.height : 0) + (footer ? footer.height : 0) + Kirigami.Units.gridUnit

    flickable: scroll.view

    //NOTE: this should be smallspacing buit we need a pixel size in order to align with systemsettings widgets
    leftPadding: Kirigami.Settings.isMobile ? 0 : headerParent.leftPadding
    topPadding: headerParent.contentItem ? 0 : leftPadding
    rightPadding: leftPadding
    bottomPadding: footerParent.contentItem ? 0 : leftPadding

    header: QtControls.Control {
        id: headerParent
    }

    footer: QtControls.Control {
        id: footerParent
    }
    Component.onCompleted: {
        if (footer && footer != footerParent) {
            var f = footer

            footerParent.contentItem = f
            footer = footerParent
            f.visible = true
            f.parent = footerParent
        }

        if (header && header != headerParent) {
            var f = header

            headerParent.contentItem = f
            header = headerParent
            f.visible = true
            f.parent = headerParent
        }
    }
    
    KCM.GridView {
        id: scroll
        anchors.fill: parent
    }
}
