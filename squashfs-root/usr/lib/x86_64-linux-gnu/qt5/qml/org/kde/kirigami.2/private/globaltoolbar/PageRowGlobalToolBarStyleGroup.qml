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

import QtQuick 2.1
import org.kde.kirigami 2.4 as Kirigami

QtObject {
    id: globalToolBar
    property int style: Kirigami.ApplicationHeaderStyle.None
    readonly property int actualStyle: {
        if (style == Kirigami.ApplicationHeaderStyle.Auto) {
            //Legacy: if ApplicationHeader or ToolbarApplicationHeader are in the header or footer, disable the toolbar here
            if (typeof applicationWindow !== "undefined" && applicationWindow().header && applicationWindow().header.toString().indexOf("ApplicationHeader") !== -1) {
                return Kirigami.ApplicationHeaderStyle.None
            }

            //non legacy logic
            return (Kirigami.Settings.isMobile
                    ? (root.wideMode ? Kirigami.ApplicationHeaderStyle.Titles : Kirigami.ApplicationHeaderStyle.Breadcrumb)
                    : Kirigami.ApplicationHeaderStyle.ToolBar)
        } else {
            //forbid ToolBar on mobile systems
            return Kirigami.Settings.isMobile && style == Kirigami.ApplicationHeaderStyle.ToolBar ? Kirigami.ApplicationHeaderStyle.Breadcrumb : style;
        }
    }

    property var showNavigationButtons: (style != Kirigami.ApplicationHeaderStyle.TabBar && (!Kirigami.Settings.isMobile || Qt.platform.os == "ios")) ? (Kirigami.ApplicationHeaderStyle.ShowBackButton | Kirigami.ApplicationHeaderStyle.ShowForwardButton) : Kirigami.ApplicationHeaderStyle.NoNavigationButtons
    property bool separatorVisible: true
    property int toolbarActionAlignment: Qt.AlignRight

    property int minimumHeight: 0
    property int preferredHeight: (actualStyle == Kirigami.ApplicationHeaderStyle.ToolBar
                    ? Kirigami.Units.iconSizes.medium
                    : Kirigami.Units.gridUnit * 1.8) + Kirigami.Units.smallSpacing * 2
    property int maximumHeight: preferredHeight
}
