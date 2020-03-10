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

import org.kde.newstuff 1.62 as NewStuff

/**
 * To use NewStuffList, simply instantiate it and pass the
 * local file location of a knsrc file to the configFile property.
 * The components will, in this case, take care of the rest for you.
 * If you want more, you can look at what NewStuffItem does with the
 * various bits, and be inspired by that.
 *
 * An (overly simple) example which might be used for managing
 * wallpapers and just outputting any messages onto the console can
 * be seen below. Note that you should obviously not be using
 * hardcoded paths, it is done here to get the idea across.
 *
 * \code
    NewStuff.NewStuffList {
        configFile: "/some/filesystem/location/wallpaper.knsrc";
        onMessage: console.log("KNS Message: " + message);
        onIdleMessage: console.log("KNS Idle: " + message);
        onBusyMessage: console.log("KNS Busy: " + message);
        onErrorMessage: console.log("KNS Error: " + message);
    }
    \endcode
 */
ListView {
    id: root;
    /**
     * @brief The configuration file which describes the application (knsrc)
     *
     * The format and location of this file is found in the documentation for
     * KNS3::DownloadDialog
     */
    property alias configFile: newStuffEngine.configFile;
    signal message(string message);
    signal idleMessage(string message);
    signal busyMessage(string message);
    signal errorMessage(string message);
    signal downloadedItemClicked(variant installedFiles);
    header: QtLayouts.RowLayout {
        anchors {
            left: parent.left
            right: parent.right
        }
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
    delegate: NewStuffItem {
        listModel: newStuffModel;
        onClicked: {
            if(model.status == NewStuff.ItemsModel.InstalledStatus) {
                root.downloadedItemClicked(model.installedFiles);
            }
        }
    }
    model: NewStuff.ItemsModel {
        id: newStuffModel;
        engine: newStuffEngine;
    }
    NewStuff.Engine {
        id: newStuffEngine;
        onMessage: root.message(message);
        onIdleMessage: root.idleMessage(message);
        onBusyMessage: root.busyMessage(message);
        onErrorMessage: root.errorMessage(message);
    }
    NewStuff.QuestionAsker {}
}
