/*
 *   Copyright 2019 Björn Feber <bfeber@protonmail.com>
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU Library General Public License as
 *   published by the Free Software Foundation; either version 2, or
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
 *   51 Franklin Street, Fifth Floor, Boston, MA  2.010-1301, USA.
 */

import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 2.4 as QQC2
import org.kde.kirigami 2.10

/**
 * A section delegate for the primitive ListView component.
 *
 * It's intended to make all listviews look coherent.
 *
 * Example usage:
 * @code
 * import QtQuick 2.5
 * import QtQuick.Controls 2.5 as QQC2
 *
 * import org.kde.kirigami 2.10 as Kirigami
 *
 * ListView {
 *  [...]
 *     section.delegate: Kirigami.ListSectionHeader {
 *         label: section
 *
 *         QQC2.Button {
 *             text: "Button 1"
 *         }
 *         QQC2.Button {
 *             text: "Button 2"
 *         }
 *     }
 *  [...]
 * }
 * @endcode
 *
 */
AbstractListItem {
    id: listSection

    /**
     * string: bool
     * A single text label the list section header will contain
     */
    property alias label: listSection.text

    default property alias _contents: rowLayout.data

    backgroundColor: Theme.backgroundColor
    Theme.inherit: false
    Theme.colorSet: Theme.Window

    separatorVisible: false
    sectionDelegate: true
    hoverEnabled: false
    supportsMouseEvents: false

    contentItem: RowLayout {
        id: rowLayout

        Heading {
            level: 3
            text: listSection.text
            Layout.fillWidth: true
        }
    }
}
