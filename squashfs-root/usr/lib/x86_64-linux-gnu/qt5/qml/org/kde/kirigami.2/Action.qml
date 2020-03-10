/*
 *   Copyright 2016 Marco Martin <mart@kde.org>
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU Library General Public License as
 *   published by the Free Software Foundation; either version 2 or
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
 *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */

import QtQuick 2.7
import QtQuick.Controls 2.4 as Controls
import "private"

/**
 * An item that represents an abstract Action
 *
 * @inherit QtQuick.Controls.Action
 */
Controls.Action {
    id: root

    /**
     * visible: bool
     * True (default) when the graphic representation of the action
     * is supposed to be visible.
     * It's up to the action representation to honor this property.
     */
    property bool visible: true

    /**
     * iconName: string
     * Sets the icon name for the action. This will pick the icon with the given name from the current theme.
     */
    property alias iconName: root.icon.name

    /**
     * iconSource: string
     * Sets the icon file or resource url for the action. Defaults to the empty URL. Use this if you want a specific file rather than an icon from the theme
     */
    property alias iconSource: root.icon.source

     /**
     * A tooltip text to be shown when hovering the control bound to this action. Not all controls support tooltips on all platforms
     */
    property string tooltip

    /**
     * children: list<Action>
     * A list of children actions.
     * Useful for tree-like menus
     * @code
     * Action {
     *    text: "Tools"
     *    Action {
     *        text: "Action1"
     *    }
     *    Action {
     *        text: "Action2"
     *    }
     * }
     * @endcode
     */

    /**
     * separator: bool
     * Whether the action is is a separator action; defaults to false.
     */
    property bool separator: false

    /**
     * expandible: bool
     * When true, actions in globalDrawers and contextDrawers will become titles displaying te child actions as sub items
     * @since 2.6
     */
    property bool expandible: false

    property Controls.Action parent

    default property alias children: root.__children
    property list<QtObject> __children

    onChildrenChanged: {
        var child;
        for (var i in children) {
            child = children[i];
            if (child.hasOwnProperty("parent")) {
                child.parent = root
            }
        }
    }

    /**
     * visibleChildren: list<Action>
     * All child actions that are visible
     */
    readonly property var visibleChildren: {
        var visible = [];
        var child;
        for (var i in children) {
            child = children[i];
            if (!child.hasOwnProperty("visible") || child.visible) {
                visible.push(child)
            }
        }
        return visible;
    }
}
