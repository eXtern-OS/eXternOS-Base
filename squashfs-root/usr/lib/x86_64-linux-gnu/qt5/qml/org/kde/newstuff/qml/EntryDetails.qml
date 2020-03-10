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
 * @brief A Kirigami.Page component used for displaying the details for a single entry
 *
 * This component is equivalent to the details view in the old DownloadDialog
 * @see KNewStuff::DownloadDialog
 * @since 5.63
 */

import QtQuick 2.11
import QtQuick.Controls 2.11 as QtControls
import QtQuick.Layouts 1.11 as QtLayouts

import org.kde.kirigami 2.7 as Kirigami
import org.kde.kcm 1.2 as KCM

import org.kde.newstuff 1.62 as NewStuff

import "private" as Private

KCM.SimpleKCM {
    id: component
    property QtObject newStuffModel
    property int index
    property string name
    property var author
    property alias shortSummary: shortSummaryItem.text
    property alias summary: summaryItem.text;
    property alias previews: screenshotsItem.screenshotsModel
    property string homepage
    property string donationLink
    property int status
    property int commentsCount
    property int rating
    property int downloadCount
    property var downloadLinks
    property string providerId

    NewStuff.DownloadItemsSheet {
        id: downloadItemsSheet
        onItemPicked: {
            var entryName = newStuffModel.data(newStuffModel.index(entryId, 0), NewStuff.ItemsModel.NameRole);
            applicationWindow().showPassiveNotification(i18nc("A passive notification shown when installation of an item is initiated", "Installing %1 from %2").arg(downloadName).arg(entryName), 1500);
            newStuffModel.installItem(entryId, downloadItemId);
        }
    }

    Connections {
        target: newStuffModel
        onEntryChanged: {
            var status = newStuffModel.data(newStuffModel.index(index, 0), NewStuff.ItemsModel.StatusRole);
            if (status == NewStuff.ItemsModel.DownloadableStatus
             || status == NewStuff.ItemsModel.InstalledStatus
             || status == NewStuff.ItemsModel.UpdateableStatus
             || status == NewStuff.ItemsModel.DeletedStatus) {
                statusCard.message = "";
            } else if (status == NewStuff.ItemsModel.InstallingStatus) {
                statusCard.message = i18nc("Status message to be shown when the entry is in the process of being installed", "Currently installing the item %1 by %2. Please wait...").arg(component.name).arg(entryAuthor.name);
            } else if (status == NewStuff.ItemsModel.UpdatingStatus) {
                statusCard.message = i18nc("Status message to be shown when the entry is in the process of being updated", "Currently updating the item %1 by %2. Please wait...").arg(component.name).arg(entryAuthor.name);
            } else {
                statusCard.message = i18nc("Status message which should only be shown when the entry has been given some unknown or invalid status.", "This item is currently in an invalid or unknown state. Please report this to the KDE Community in a bug report.");
            }
        }
    }

    NewStuff.Author {
        id: entryAuthor
        engine: component.newStuffModel.engine
        providerId: component.providerId
        username: author.name
    }
    title: i18nc("Combined title for the entry details page made of the name of the entry, and the author's name", "%1 by %2").arg(component.name).arg(entryAuthor.name)
    titleDelegate: QtLayouts.RowLayout {
        implicitHeight: title.height
        Kirigami.Heading {
            id: title
            level: 1

            QtLayouts.Layout.fillWidth: true;
            QtLayouts.Layout.preferredWidth: titleTextMetrics.width
            QtLayouts.Layout.minimumWidth: titleTextMetrics.width
            opacity: component.isCurrentPage ? 1 : 0.4
            maximumLineCount: 1
            elide: Text.ElideRight
            text: component.title
            TextMetrics {
                id: titleTextMetrics
                text: component.title
                font: title.font
            }
        }
        QtControls.ToolButton {
            text: component.downloadCount == 1 ? i18nc("Request installation of this item, available when there is exactly one downloadable item", "Install") : i18nc("Show installation options, where there is more than one downloadable item", "Install...");
            icon.name: "install"
            onClicked: {
                if (component.downloadCount == 1) {
                    newStuffModel.installItem(component.index);
                } else {
                    downloadItemsSheet.downloadLinks = component.downloadLinks;
                    downloadItemsSheet.entryId = component.index;
                    downloadItemsSheet.open();
                }
            }
            enabled: component.status == NewStuff.ItemsModel.DownloadableStatus || component.status == NewStuff.ItemsModel.DeletedStatus;
            visible: enabled;
        }
        QtControls.ToolButton {
            text: i18nc("Request updating of this item", "Update");
            icon.name: "update"
            onClicked: { newStuffModel.installItem(component.index); }
            enabled: component.status == NewStuff.ItemsModel.UpdateableStatus;
            visible: enabled;
        }
        QtControls.ToolButton {
            text: i18nc("Request uninstallation of this item", "Uninstall");
            icon.name: "uninstall"
            onClicked: { newStuffModel.uninstallItem(component.index); }
            enabled: component.status == NewStuff.ItemsModel.InstalledStatus
            visible: enabled;
        }
    }
    QtLayouts.ColumnLayout {
        spacing: Kirigami.Units.smallSpacing
        Item { width: parent.width; height: Kirigami.Units.gridUnit * 3; }
        Kirigami.AbstractCard {
            id: statusCard
            property string message;
            visible: opacity > 0
            opacity: message.length > 0 ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.longDuration; } }
            QtLayouts.Layout.fillWidth: true
            QtLayouts.Layout.margins: Kirigami.Units.largeSpacing
            Item {
                id: statusContent
                implicitHeight: statusCard.message.length > 0 ? Math.max(statusBusy.height, statusLabel.height) + Kirigami.Units.largeSpacing * 4 : 0
                implicitWidth: statusCard.width
                QtControls.BusyIndicator {
                    id: statusBusy
                    anchors {
                        top: parent.top
                        left: parent.left
                    }
                    running: statusCard.opacity > 0
                    Rectangle { anchors.fill: parent; color: "red"; opacity: 0.3; }
                }
                QtControls.Label {
                    id: statusLabel
                    anchors {
                        top: parent.top
                        left: statusBusy.right
                        leftMargin: Kirigami.Units.largeSpacing
                        right: parent.right
                    }
                    text: statusCard.message
                    wrapMode: Text.Wrap
                    Rectangle { anchors.fill: parent; color: "blue"; opacity: 0.3; }
                }
            }
        }
        Private.EntryScreenshots {
            id: screenshotsItem
            QtLayouts.Layout.fillWidth: true
        }
        Kirigami.Heading {
            id: shortSummaryItem
            QtLayouts.Layout.fillWidth: true
        }
        Kirigami.FormLayout {
            QtLayouts.Layout.fillWidth: true
            Kirigami.LinkButton {
                Kirigami.FormData.label: i18n("Comments and Reviews:")
                enabled: component.commentsCount > 0
                text: i18nc("A link which, when clicked, opens a new sub page with reviews (comments) for this entry", "%1 Reviews").arg(component.commentsCount)
                onClicked: pageStack.push(commentsPage)
            }
            Private.Rating {
                id: ratingsItem
                Kirigami.FormData.label: i18n("Rating:")
                rating: Math.floor(component.rating / 10)
            }
            Kirigami.LinkButton {
                Kirigami.FormData.label: i18n("Homepage:")
                text: i18nc("A link which, when clicked, opens the website associated with the entry (this could be either one specific to the project, the author's homepage, or any other website they have chosen for the purpose)", "Open the homepage for %2").arg(component.name)
                onClicked: Qt.openUrlExternally(component.homepage)
            }
            Kirigami.LinkButton {
                Kirigami.FormData.label: i18n("How To Donate:")
                text: i18nc("A link which, when clicked, opens a website with information on donation in support of the entry", "Find out how to donate to this project")
                onClicked: Qt.openUrlExternally(component.donationLink)
            }
        }
        QtControls.Label {
            id: summaryItem
            QtLayouts.Layout.fillWidth: true
            QtLayouts.Layout.margins: Kirigami.Units.largeSpacing
            wrapMode: Text.Wrap
        }
    }

    Component {
        id: commentsPage
        Private.EntryCommentsPage {
            itemsModel: component.newStuffModel
            entryIndex: component.index
            entryName: component.name
            entryAuthorId: component.author.name
            entryProviderId: component.providerId
        }
    }
}
