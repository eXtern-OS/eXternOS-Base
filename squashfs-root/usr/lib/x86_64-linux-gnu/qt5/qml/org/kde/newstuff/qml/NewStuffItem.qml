/*
 * Copyright (C) 2015 Dan Leinir Turthra Jensen <admin@leinir.dk>
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

import org.kde.kirigami 2.1 as Kirigami

import org.kde.newstuff 1.62 as NewStuff

Kirigami.SwipeListItem {
    id: listItem;
    height: Math.max(Kirigami.Units.iconSizes.huge + Kirigami.Units.smallSpacing * 2, nameText.height + descriptionText.height + Kirigami.Units.smallSpacing * 5);
    property QtObject listModel;
    enabled: true;
    actions: [
        Kirigami.Action {
            text: i18nc("Request installation of this item", "Install");
            iconName: "list-add"
            onTriggered: { listModel.installItem(model.index, 1); }
            enabled: model.status == NewStuff.ItemsModel.DownloadableStatus || model.status == NewStuff.ItemsModel.DeletedStatus;
            visible: enabled;
        },
        Kirigami.Action {
            text: i18nc("Request updating of this item", "Update");
            iconName: "refresh"
            onTriggered: { listModel.installItem(model.index, 1); }
            enabled: model.status == NewStuff.ItemsModel.UpdateableStatus;
            visible: enabled;
        },
        Kirigami.Action {
            text: i18nc("Request uninstallation of this item", "Uninstall");
            iconName: "list-remove"
            onTriggered: { listModel.uninstallItem(model.index); }
            enabled: model.status == NewStuff.ItemsModel.InstalledStatus
            visible: enabled;
        }
    ]
    QtLayouts.RowLayout {
        Item {
            id: previewContainer;
            QtLayouts.Layout.preferredHeight: listItem.height - Kirigami.Units.smallSpacing * 2;
            QtLayouts.Layout.minimumWidth: Kirigami.Units.iconSizes.huge;
            QtLayouts.Layout.maximumWidth: Kirigami.Units.iconSizes.huge;
            Image {
                id: previewImage;
                anchors {
                    fill: parent;
                    margins: Kirigami.Units.smallSpacing;
                    leftMargin: -Kirigami.Units.smallSpacing;
                }
                asynchronous: true;
                fillMode: Image.PreserveAspectFit;
                source: model.previewsSmall.length > 0 ? model.previewsSmall[0] : "";
                Kirigami.Icon {
                    id: updateAvailableBadge;
                    opacity: (model.status == NewStuff.ItemsModel.UpdateableStatus) ? 1 : 0;
                    Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration; } }
                    anchors {
                        bottom: parent.bottom;
                        right: parent.right;
                        margins: -Kirigami.Units.smallSpacing;
                    }
                    height: Kirigami.Units.iconSizes.smallMedium;
                    width: height;
                    source: "vcs-update-required";
                }
                Kirigami.Icon {
                    id: installedBadge;
                    opacity: (model.status == NewStuff.ItemsModel.InstalledStatus) ? 1 : 0;
                    Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration; } }
                    anchors {
                        bottom: parent.bottom;
                        right: parent.right;
                        margins: -Kirigami.Units.smallSpacing;
                    }
                    height: Kirigami.Units.iconSizes.smallMedium;
                    width: height;
                    source: "vcs-normal";
                }
            }
            Rectangle {
                anchors.fill: parent
                opacity: installIndicator.opacity > 0 ? 0.7 : 0
                Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration; } }
                visible: opacity > 0
            }
            QtControls.BusyIndicator {
                id: installIndicator
                anchors.centerIn: parent;
                opacity: (model.status == NewStuff.ItemsModel.InstallingStatus || model.status == NewStuff.ItemsModel.UpdatingStatus) ? 1 : 0;
                Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration; } }
                running: opacity > 0;
                QtControls.Label {
                    anchors {
                        horizontalCenter: parent.horizontalCenter;
                        bottom: parent.bottom;
                        margins: Kirigami.Units.smallSpacing;
                    }
                    text: (model.status == NewStuff.ItemsModel.InstallingStatus) ? "Installing" : ((model.status == NewStuff.ItemsModel.UpdatingStatus) ? "Updating" : "");
                    width: paintedWidth;
                }
            }
        }
        QtLayouts.ColumnLayout {
            QtLayouts.Layout.fillWidth: true
            QtLayouts.Layout.fillHeight: true
            Kirigami.Heading {
                id: nameText
                QtLayouts.Layout.fillWidth: true
                level: 3
                text: model.name
                opacity: 1 - installIndicator.opacity
            }
            QtControls.Label {
                id: descriptionText
                QtLayouts.Layout.fillWidth: true
                text: model.summary.split("\n")[0];
                elide: Text.ElideRight
                maximumLineCount: 2
                wrapMode: Text.Wrap
                opacity: 1 - installIndicator.opacity
            }
            Item {
                QtLayouts.Layout.fillWidth: true
                QtLayouts.Layout.fillHeight: true
            }
        }
    }
}
