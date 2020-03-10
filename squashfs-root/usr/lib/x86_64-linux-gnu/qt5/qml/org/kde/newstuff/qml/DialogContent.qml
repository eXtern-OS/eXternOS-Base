/*
 * Copyright (C) 2019 Dan Leinir Turthra Jensen <admin@leinir.dk>
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

/**
 * @brief The contents of the NewStuff.Dialog component
 *
 * This component is equivalent to the old DownloadWidget, but you should consider
 * using NewStuff.Page instead for a more modern style of integration into your
 * application's flow.
 * @see KNewStuff::DownloadWidget
 * @since 5.63
 */

import QtQuick 2.11
import QtQuick.Layouts 1.11 as QtLayouts

import org.kde.kirigami 2.7 as Kirigami

import org.kde.newstuff 1.62 as NewStuff

Kirigami.ApplicationItem {
    id: component

    property alias downloadNewWhat: newStuffPage.title
    /**
     * The configuration file to use for this button
     */
    property alias configFile: newStuffPage.configFile

    /**
     * The engine which handles the content in this dialog
     */
    property alias engine: newStuffPage.engine

    /**
     * The default view mode of the dialog spawned by this button. This should be
     * set using the NewStuff.Page.ViewMode enum
     * @see NewStuff.Page.ViewMode
     */
    property alias viewMode: newStuffPage.viewMode

    QtLayouts.Layout.preferredWidth: Kirigami.Units.gridUnit * 50
    QtLayouts.Layout.preferredHeight: Kirigami.Units.gridUnit * 40
    pageStack.defaultColumnWidth: pageStack.width
    pageStack.globalToolBar.style: Kirigami.ApplicationHeaderStyle.Auto
    pageStack.initialPage: NewStuff.Page {
        id: newStuffPage
        onMessage: component.showPassiveNotification(message);
        onIdleMessage: component.showPassiveNotification(message);
        onBusyMessage: component.showPassiveNotification(message);
        onErrorMessage: component.showPassiveNotification(message);
    }
}
