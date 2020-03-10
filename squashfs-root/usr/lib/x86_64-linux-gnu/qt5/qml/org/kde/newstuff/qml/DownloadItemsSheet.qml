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

import QtQuick 2.11
import QtQuick.Controls 2.11 as QtControls
import QtQuick.Layouts 1.11 as QtLayouts

import org.kde.kirigami 2.7 as Kirigami

import org.kde.newstuff 1.62 as NewStuff

/**
 * @brief An overlay sheet for showing a list of download options for one entry
 *
 * This is used by the NewStuff.Page componet
 * @since 5.63
 */

Kirigami.OverlaySheet {
    id: component

    property string entryId
    property alias downloadLinks: itemsView.model
    signal itemPicked(string entryId, int downloadItemId, string downloadName)

    showCloseButton: true
    header: QtLayouts.ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        Kirigami.Heading {
            QtLayouts.Layout.fillWidth: true
            text: i18n("Pick Your Installation Option")
            elide: Text.ElideRight
        }
        QtControls.Label {
            QtLayouts.Layout.fillWidth: true
            QtLayouts.Layout.margins: Kirigami.Units.largeSpacing
            text: i18n("Please select the option you wish to install from the list of downloadable items below. If it is unclear which you should chose out of the available options, please contact the author of this item and ask that they clarify this through the naming of the items.")
            wrapMode: Text.Wrap
        }
    }
    contentItem: ListView {
        id: itemsView
        QtLayouts.Layout.preferredWidth: parent.width - Kirigami.Units.largeSpacing * 2
        delegate: Kirigami.BasicListItem {
            anchors {
                left: parent.left
                right: parent.right
                leftMargin: Kirigami.Units.largeSpacing * 2
                rightMargin: Kirigami.Units.largeSpacing * 2
            }
            text: modelData.name
            icon: "download"
            QtControls.ToolButton {
                text: i18n("Install")
                icon.name: "install"
                QtLayouts.Layout.alignment: Qt.AlignRight
                onClicked: {
                    component.close();
                    component.itemPicked(component.entryId, modelData.id, modelData.name);
                }
            }
        }
    }
}
