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
import QtGraphicalEffects 1.11 as QtEffects

import org.kde.kcm 1.2 as KCM
import org.kde.kirigami 2.7 as Kirigami

import org.kde.newstuff 1.62 as NewStuff

import ".." as Private

KCM.GridDelegate {
    id: component
    property string useLabel
    property string uninstallLabel
    text: model.name
//         onClicked: pageStack.push(detailsPage, {
//             name: model.name,
//             author: model.author,
//             previews: model.previews,
//             shortSummary: model.shortSummary,
//             summary: model.summary,
//             homepage: model.homepage,
//             donationLink: model.donationLink
//         });
    actions: [
        Kirigami.Action {
            text: component.useLabel
            iconName: "dialog-ok-apply"
            onTriggered: { model.adopt(model.index); }
            enabled: (model.status == NewStuff.ItemsModel.InstalledStatus || model.status == NewStuff.ItemsModel.UpdateableStatus) && newStuffEngine.hasAdoptionCommand
            visible: enabled
        },
        Kirigami.Action {
            text: model.downloadCount == 1 ? i18nc("Request installation of this item, available when there is exactly one downloadable item", "Install") : i18nc("Show installation options, where there is more than one downloadable item", "Install...");
            iconName: "install"
            onTriggered: {
                if (model.downloadCount == 1) {
                    newStuffModel.installItem(model.index);
                } else {
                    downloadItemsSheet.downloadLinks = model.downloadLinks;
                    downloadItemsSheet.entryId = model.index;
                    downloadItemsSheet.open();
                }
            }
            enabled: model.status == NewStuff.ItemsModel.DownloadableStatus || model.status == NewStuff.ItemsModel.DeletedStatus;
            visible: enabled;
        },
        Kirigami.Action {
            text: i18nc("Request updating of this item", "Update");
            iconName: "update"
            onTriggered: { newStuffModel.installItem(model.index); }
            enabled: model.status == NewStuff.ItemsModel.UpdateableStatus;
            visible: enabled;
        },
        Kirigami.Action {
            text: component.uninstallLabel
            iconName: "uninstall"
            onTriggered: { newStuffModel.uninstallItem(model.index); }
            enabled: model.status == NewStuff.ItemsModel.InstalledStatus
            visible: enabled;
        }
    ]
    thumbnailAvailable: model.previewsSmall.length > 0
    thumbnail: Image {
        anchors {
            fill: parent;
            margins: Kirigami.Units.smallSpacing;
        }
        asynchronous: true;
        fillMode: Image.PreserveAspectFit;
        source: thumbnailAvailable ? model.previewsSmall[0] : "";
        Kirigami.Icon {
            id: updateAvailableBadge;
            opacity: (model.status == NewStuff.ItemsModel.UpdateableStatus) ? 1 : 0;
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration; } }
            anchors {
                top: parent.top;
                right: parent.right;
                margins: -Kirigami.Units.smallSpacing;
            }
            height: Kirigami.Units.iconSizes.smallMedium;
            width: height;
            source: "package-installed-outdated";
        }
        Kirigami.Icon {
            id: installedBadge;
            opacity: (model.status == NewStuff.ItemsModel.InstalledStatus) ? 1 : 0;
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration; } }
            anchors {
                top: parent.top;
                right: parent.right;
                margins: -Kirigami.Units.smallSpacing;
            }
            height: Kirigami.Units.iconSizes.smallMedium;
            width: height;
            source: "package-installed-updated";
        }
        Item {
            anchors.fill: parent
            opacity: (model.status == NewStuff.ItemsModel.InstallingStatus || model.status == NewStuff.ItemsModel.UpdatingStatus) ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.longDuration; } }
            Rectangle {
                anchors.fill: parent
                color: Kirigami.Theme.backgroundColor
                opacity: 0.5;
            }
            QtControls.BusyIndicator {
                anchors.centerIn: parent
                running: parent.opacity > 0
            }
        }
        MouseArea {
            anchors.fill: parent;
            onClicked: pageStack.push(detailsPage, {
                newStuffModel: GridView.view.model,
                index: model.index,
                name: model.name,
                author: model.author,
                previews: model.previews,
                shortSummary: model.shortSummary,
                summary: model.summary,
                homepage: model.homepage,
                donationLink: model.donationLink,
                status: model.status,
                commentsCount: model.numberOfComments,
                rating: model.rating,
                downloadCount: model.downloadCount,
                downloadLinks: model.downloadLinks,
                providerId: model.providerId
            });
        }
    }
}
