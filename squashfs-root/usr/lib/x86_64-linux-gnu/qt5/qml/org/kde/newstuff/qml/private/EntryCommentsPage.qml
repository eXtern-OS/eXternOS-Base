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
 * @brief A Kirigami.Page component used for displaying a NewStuff entry's comments
 */

import QtQuick 2.11
import QtQuick.Controls 2.11 as QtControls
import QtQuick.Layouts 1.11 as QtLayouts

import org.kde.kirigami 2.7 as Kirigami

import org.kde.newstuff 1.62 as NewStuff

Kirigami.ScrollablePage {
    id: component
    property string entryName
    property string entryAuthorId
    property string entryProviderId
    property alias entryIndex: commentsModel.entryIndex
    property alias itemsModel: commentsModel.itemsModel
    title: i18nc("Title for the page containing a view of the comments for the entry", "Comments and Reviews for %1").arg(component.entryName)
    ListView {
        id: commentsView
        model: NewStuff.CommentsModel {
            id: commentsModel
        }
        QtLayouts.Layout.fillWidth: true
        header: Item {
            anchors {
                left: parent.left
                right: parent.right
            }
            height: Kirigami.Units.largeSpacing
        }
        delegate: EntryCommentDelegate {
            engine: component.itemsModel.engine
            entryAuthorId: component.entryAuthorId
            entryProviderId: component.entryProviderId
            author: model.username
            score: model.score
            title: model.subject
            reviewText: model.text
            depth: model.depth
        }
    }
}
