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
 * @brief A card based delegate for showing a comment from a KNewStuffQuick::QuickCommentsModel
 */

import QtQuick 2.11
import QtQuick.Controls 2.11 as QtControls
import QtQuick.Layouts 1.11 as QtLayouts

import org.kde.kirigami 2.7 as Kirigami

import org.kde.newstuff 1.62 as NewStuff

QtLayouts.RowLayout {
    id: component

    /**
     * The KNSQuick Engine object which handles all our content
     */
    property QtObject engine

    /**
     * The username of the author of whatever the comment is attached to
     */
    property string entryAuthorId
    /**
     * The provider ID as supplied by the entry the comment is attached to
     */
    property string entryProviderId

    /**
     * The username of the comment's author
     */
    property string author
    /**
     * The OCS score, an integer from 1 to 100. It will be interpreted
     * as a 5 star rating, with half star support (0-10)
     */
    property int score
    /**
     * The title or subject line for the comment
     */
    property string title
    /**
     * The actual text of the comment
     */
    property alias reviewText: reviewLabel.text
    /**
     * The depth of the comment (in essence, how many parents the comment has)
     */
    property int depth

    spacing: 0

    property QtObject commentAuthor: NewStuff.Author {
        engine: component.engine
        providerId: component.entryProviderId
        username: component.author
    }

    anchors {
        left: parent.left
        right: parent.right
        leftMargin: Kirigami.Units.largeSpacing
        rightMargin: Kirigami.Units.largeSpacing
    }

    Repeater {
        model: component.depth
        delegate: Rectangle {
            QtLayouts.Layout.fillHeight: true
            QtLayouts.Layout.minimumWidth: Kirigami.Units.largeSpacing
            QtLayouts.Layout.maximumWidth: Kirigami.Units.largeSpacing
            color: Qt.tint(Kirigami.Theme.textColor, Qt.rgba(Kirigami.Theme.backgroundColor.r, Kirigami.Theme.backgroundColor.g, Kirigami.Theme.backgroundColor.b, 0.8))
            Rectangle {
                anchors {
                    top: parent.top
                    bottom: parent.bottom
                    left: parent.left
                }
                width: 1
                color: Kirigami.Theme.backgroundColor
            }
        }
    }

    QtLayouts.ColumnLayout {
        Item {
            visible: component.depth === 0
            QtLayouts.Layout.fillWidth: true
            QtLayouts.Layout.minimumHeight: Kirigami.Units.largeSpacing
            QtLayouts.Layout.maximumHeight: Kirigami.Units.largeSpacing
        }

        Kirigami.Separator {
            QtLayouts.Layout.fillWidth: true
        }

        QtLayouts.RowLayout {
            visible: (component.title !== "" || component.score !== 0)
            QtLayouts.Layout.fillWidth: true
            QtLayouts.Layout.leftMargin: Kirigami.Units.largeSpacing
            Kirigami.Heading {
                id: titleLabel
                text: ((component.title === "") ? i18nc("Placeholder title for when a comment has no subject, but does have a rating", "<i>(no title)</i>") : component.title)
                level: 4
                QtLayouts.Layout.fillWidth: true
            }
            Rating {
                id: ratingStars
                rating: Math.floor(component.score / 10)
            }
            Item {
                QtLayouts.Layout.minimumWidth: Kirigami.Units.largeSpacing
                QtLayouts.Layout.maximumWidth: Kirigami.Units.largeSpacing
            }
        }

        QtControls.Label {
            id: reviewLabel
            QtLayouts.Layout.fillWidth: true
            QtLayouts.Layout.leftMargin: Kirigami.Units.largeSpacing
            QtLayouts.Layout.rightMargin: Kirigami.Units.largeSpacing
            wrapMode: Text.Wrap
        }

        QtLayouts.RowLayout {
            QtLayouts.Layout.fillWidth: true
            Item {
                QtLayouts.Layout.fillWidth: true
            }
            Kirigami.UrlButton {
                id: authorLabel
                visible: (url !== "")
                url: (component.commentAuthor.homepage === "") ? component.commentAuthor.profilepage : component.commentAuthor.homepage
                text: (component.author === component.entryAuthorId) ? i18nc("The author label in case the comment was written by the author of the content entry the comment is attached to", "%1 <i>(author)</i>").arg(component.commentAuthor.name) : component.commentAuthor.name
            }
            QtControls.Label {
                visible: !authorLabel.visible
                text: authorLabel.text
            }
            Image {
                id: authorIcon
                QtLayouts.Layout.maximumWidth: height
                QtLayouts.Layout.minimumWidth: height
                QtLayouts.Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                fillMode: Image.PreserveAspectFit
                source: component.commentAuthor.avatarUrl
                Kirigami.Icon {
                    anchors.fill: parent;
                    source: "user"
                    visible: opacity > 0
                    opacity: authorIcon.status == Image.Ready ? 0 : 1
                    Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration; } }
                }
            }
            Item {
                QtLayouts.Layout.minimumWidth: Kirigami.Units.largeSpacing
                QtLayouts.Layout.maximumWidth: Kirigami.Units.largeSpacing
            }
        }
        Item {
            QtLayouts.Layout.fillWidth: true
            QtLayouts.Layout.minimumHeight: Kirigami.Units.largeSpacing
            QtLayouts.Layout.maximumHeight: Kirigami.Units.largeSpacing
        }

    }
}
