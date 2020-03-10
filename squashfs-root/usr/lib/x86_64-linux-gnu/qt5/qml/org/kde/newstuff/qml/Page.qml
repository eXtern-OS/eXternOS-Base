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
 * @brief A Kirigami.Page component used for managing KNS entries
 *
 * This component is functionally equivalent to the old DownloadDialog
 * @see KNewStuff::DownloadDialog
 * @since 5.63
 */

import QtQuick 2.11
import QtQuick.Controls 2.11 as QtControls
import QtQuick.Layouts 1.11 as QtLayouts
import QtGraphicalEffects 1.11 as QtEffects

import org.kde.kcm 1.2 as KCM
import org.kde.kirigami 2.7 as Kirigami

import org.kde.newstuff 1.62 as NewStuff

import "private" as Private
import "private/entrygriddelegates" as EntryGridDelegates

KCM.GridViewKCM {
    id: root;
    /**
     * @brief The configuration file which describes the application (knsrc)
     *
     * The format and location of this file is found in the documentation for
     * KNS3::DownloadDialog
     */
    property alias configFile: newStuffEngine.configFile;
    readonly property alias engine: newStuffEngine;

    /**
     * Any generic message from the NewStuff.Engine
     * @param message The message to be shown to the user
     */
    signal message(string message);
    /**
     * A message posted usually describing that whatever action a recent busy
     * message said was happening has been completed
     * @param message The message to be shown to the user
     */
    signal idleMessage(string message);
    /**
     * A message posted when the engine is busy doing something long duration
     * (usually this will be when fetching installation data)
     * @param message The message to be shown to the user
     */
    signal busyMessage(string message);
    /**
     * A message posted when something has gone wrong
     * @param message The message to be shown to the user
     */
    signal errorMessage(string message);

    property string uninstallLabel: i18nc("Request uninstallation of this item", "Uninstall");
    property string useLabel: i18nc("If a knsrc file defines an adoption command, the option to run this command and 'use' an item becomes available. This is the text for an action to do so.", "Use");

    property int viewMode: Page.ViewMode.Tiles
    enum ViewMode {
        Tiles,
        Icons,
        Preview
    }

    title: newStuffEngine.name
    NewStuff.Engine {
        id: newStuffEngine;
        onMessage: root.message(message);
        onIdleMessage: root.idleMessage(message);
        onBusyMessage: root.busyMessage(message);
        onErrorMessage: root.errorMessage(message);
    }
    NewStuff.QuestionAsker {}

    titleDelegate: QtLayouts.RowLayout {
        Kirigami.Heading {
            id: title
            level: 1

            QtLayouts.Layout.fillWidth: true;
            QtLayouts.Layout.preferredWidth: titleTextMetrics.width
            QtLayouts.Layout.minimumWidth: titleTextMetrics.width
            opacity: root.isCurrentPage ? 1 : 0.4
            maximumLineCount: 1
            elide: Text.ElideRight
            text: root.title
            TextMetrics {
                id: titleTextMetrics
                text: root.title
                font: title.font
            }
        }
        QtControls.ButtonGroup {
            id: displayModeGroup
            buttons: [displayModeTiles, displayModeIcons]
        }
        QtControls.ToolButton {
            id: displayModeTiles
            icon.name: "view-list-details"
            onClicked: { root.viewMode = Page.ViewMode.Tiles; }
            checked: root.viewMode == Page.ViewMode.Tiles
        }
        QtControls.ToolButton {
            id: displayModeIcons
            icon.name: "view-list-icons"
            onClicked: { root.viewMode = Page.ViewMode.Icons; }
            checked: root.viewMode == Page.ViewMode.Icons
        }
        QtControls.ToolButton {
            id: displayPreview
            icon.name: "view-preview"
            onClicked: { root.viewMode = Page.ViewMode.Preview; }
            checked: root.viewMode == Page.ViewMode.Preview
        }
        Kirigami.ActionTextField {
            id: searchField
            placeholderText: i18n("Search...")
            focusSequence: "Ctrl+F"
            rightActions: [
                Kirigami.Action {
                    iconName: "edit-clear"
                    visible: searchField.text !== ""
                    onTriggered: {
                        searchField.text = "";
                        searchField.accepted();
                    }
                }
            ]
            onAccepted: {
                newStuffEngine.searchTerm = searchField.text;
            }
        }
    }

    footer: QtLayouts.RowLayout {
        QtControls.ComboBox {
            id: categoriesCombo
            QtLayouts.Layout.fillWidth: true
            model: newStuffEngine.categories
            textRole: "displayName"
            onCurrentIndexChanged: {
                newStuffEngine.categoriesFilter = model.data(model.index(currentIndex, 0), NewStuff.CategoriesModel.NameRole);
            }
        }
        QtControls.ComboBox {
            id: filterCombo
            QtLayouts.Layout.fillWidth: true
            model: ListModel {}
            Component.onCompleted: {
                filterCombo.model.append({ text: i18nc("List option which will set the filter to show everything", "Show Everything") });
                filterCombo.model.append({ text: i18nc("List option which will set the filter so only installed items are shown", "Installed Only") });
                filterCombo.model.append({ text: i18nc("List option which will set the filter so only installed items with updates available are shown", "Updateable Only") });
                filterCombo.currentIndex = newStuffEngine.filter;
            }
            onCurrentIndexChanged: {
                newStuffEngine.filter = currentIndex;
            }
        }
        QtControls.ComboBox {
            id: sortCombo
            QtLayouts.Layout.fillWidth: true
            model: ListModel { }
            Component.onCompleted: {
                sortCombo.model.append({ text: i18nc("List option which will set the sort order to based on when items were most recently updated", "Show most recent first") });
                sortCombo.model.append({ text: i18nc("List option which will set the sort order to be alphabetical based on the name", "Sort alphabetically") });
                sortCombo.model.append({ text: i18nc("List option which will set the sort order to based on user ratings", "Show highest rated first") });
                sortCombo.model.append({ text: i18nc("List option which will set the sort order to based on number of downloads", "Show most downloaded first") });
                sortCombo.currentIndex = newStuffEngine.sortOrder;
            }
            onCurrentIndexChanged: {
                newStuffEngine.sortOrder = currentIndex;
            }
        }
    }

    view.model: NewStuff.ItemsModel {
        id: newStuffModel;
        engine: newStuffEngine;
    }
    NewStuff.DownloadItemsSheet {
        id: downloadItemsSheet
        onItemPicked: {
            var entryName = newStuffModel.data(newStuffModel.index(entryId, 0), NewStuff.ItemsModel.NameRole);
            applicationWindow().showPassiveNotification(i18nc("A passive notification shown when installation of an item is initiated", "Installing %1 from %2").arg(downloadName).arg(entryName), 1500);
            newStuffModel.installItem(entryId, downloadItemId);
        }
    }

    view.implicitCellWidth: root.viewMode == Page.ViewMode.Tiles ? Kirigami.Units.gridUnit * 30 : (root.viewMode == Page.ViewMode.Preview ? Kirigami.Units.gridUnit * 25 : Kirigami.Units.gridUnit * 10)
    view.implicitCellHeight: root.viewMode == Page.ViewMode.Tiles ? Math.round(view.implicitCellWidth / 3) : (root.viewMode == Page.ViewMode.Preview ? Kirigami.Units.gridUnit * 25 : Math.round(view.implicitCellWidth / 1.6) + Kirigami.Units.gridUnit*2)
    view.delegate: root.viewMode == Page.ViewMode.Tiles ? tileDelegate : (root.viewMode == Page.ViewMode.Preview ? bigPreviewDelegate : thumbDelegate)

    Component {
        id: bigPreviewDelegate
        EntryGridDelegates.BigPreviewDelegate { }
    }
    Component {
        id: tileDelegate
        EntryGridDelegates.TileDelegate  {
            useLabel: root.useLabel
            uninstallLabel: root.uninstallLabel
        }
    }
    Component {
        id: thumbDelegate
        EntryGridDelegates.ThumbDelegate {
            useLabel: root.useLabel
            uninstallLabel: root.uninstallLabel
        }
    }

    Component {
        id: detailsPage;
        NewStuff.EntryDetails { }
    }
}
