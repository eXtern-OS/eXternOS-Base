/*
 *   Copyright 2015 Marco Martin <mart@kde.org>
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
 *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */

import QtQuick 2.1
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.2
import org.kde.kirigami 2.4
import "private"

/**
 * ScrollablePage is a container for all the app pages: everything pushed to the
 * ApplicationWindow stackView should be a Page or ScrollablePage instance.
 * This Page subclass is for content that has to be scrolled around, such as
 * bigger content than the screen that would normally go in a Flickable
 * or a ListView.
 * Scrolling and scrolling indicators will be automatically managed
 *
 *
 * @code
 * ScrollablePage {
 *     id: root
 *     //The rectangle will automatically bescrollable
 *     Rectangle {
 *         width: root.width
 *         height: 99999
 *     }
 * }
 * @endcode
 *
 * Another behavior added by this class is a "scroll down to refresh" behavior
 * It also can give the contents of the flickable to have more top margins in order
 * to make possible to scroll down the list to reach it with the thumb while using the
 * phone with a single hand.
 *
 * Implementations should handle the refresh themselves as follows
 *
 * @code
 * Kirigami.ScrollablePage {
 *     id: view
 *     supportsRefreshing: true
 *     onRefreshingChanged: {
 *         if (refreshing) {
 *             myModel.refresh();
 *         }
 *     }
 *     ListView {
 *         //NOTE: MyModel doesn't come from the components,
 *         //it's purely an example on how it can be used together
 *         //some application logic that can update the list model
 *         //and signals when it's done.
 *         model: MyModel {
 *             onRefreshDone: view.refreshing = false;
 *         }
 *         delegate: BasicListItem {}
 *     }
 * }
 * [...]
 * @endcode
 *
 */
Page {
    id: root

    /**
     * refreshing: bool
     * If true the list is asking for refresh and will show a loading spinner.
     * it will automatically be set to true when the user pulls down enough the list.
     * This signals the application logic to start its refresh procedure.
     * The application itself will have to set back this property to false when done.
     */
    property alias refreshing: scrollView.refreshing

    /**
     * supportsRefreshing: bool
     * If true the list supports the "pull down to refresh" behavior.
     * default is false.
     */
    property alias supportsRefreshing: scrollView.supportsRefreshing

    /**
     * flickable: Flickable
     * The main Flickable item of this page
     */
    property alias flickable: scrollView.flickableItem

    /**
     * verticalScrollBarPolicy: Qt.ScrollBarPolicy
     * The vertical scrollbar policy
     */
    property alias verticalScrollBarPolicy: scrollView.verticalScrollBarPolicy

    /**
     * horizontalScrollBarPolicy: Qt.ScrollBarPolicy
     * The horizontal scrollbar policy
     */
    property alias horizontalScrollBarPolicy: scrollView.horizontalScrollBarPolicy

    /**
     * The main content Item of this page.
     * In the case of a ListView or GridView, both contentItem and flickable
     * will be a pointer to the ListView (or GridView)
     * NOTE: can't be contentItem as Page's contentItem is final
     */
    default property QtObject mainItem

    /**
     * keyboardNavigationEnabled: bool
     * If true, and if flickable is an item view, like a ListView or
     * a GridView, it will be possible to navigate the list current item
     * to next and previous items with keyboard up/down arrow buttons.
     * Also, any key event will be forwarded to the current list item.
     * default is true.
     */
    property bool keyboardNavigationEnabled: true

    contentHeight: root.flickable.contentHeight
    implicitHeight: (header ? header.implicitHeight : 0) + (footer ? footer.implicitHeight : 0) + contentHeight + topPadding + bottomPadding
    implicitWidth: root.flickable.contentItem ? root.flickable.contentItem.implicitWidth : contentItem.implicitWidth + leftPadding + rightPadding

    Theme.colorSet: flickable && flickable.hasOwnProperty("model") ? Theme.View : Theme.Window

    clip: true
    contentItem: RefreshableScrollView {
        id: scrollView
        //NOTE: here to not expose it to public api
        property QtObject oldMainItem
        page: root
        clip: true
        topPadding: contentItem == flickableItem ? 0 : root.topPadding
        leftPadding: root.leftPadding
        rightPadding: root.rightPadding + (root.flickable.ScrollBar.vertical && root.flickable.ScrollBar.vertical.visible ? root.flickable.ScrollBar.vertical.width : 0)
        bottomPadding: contentItem == flickableItem ? 0 : root.bottomPadding
        anchors {
            top: root.header
                    ? root.header.bottom
                    //FIXME: for nowassuming globalToolBarItem is in a Loader, which needs to be got rid of
                    : (globalToolBarItem && globalToolBarItem.parent && globalToolBarItem.visible ?
                    globalToolBarItem.parent.bottom : parent.top)
            bottom: root.footer ? root.footer.top : parent.bottom
            left: parent.left
            right: parent.right
        }
    }

    anchors.topMargin: 0

    Keys.forwardTo: root.keyboardNavigationEnabled && root.flickable
                        ? (("currentItem" in root.flickable) && root.flickable.currentItem ?  
                           [ root.flickable.currentItem, root.flickable ] : [ root.flickable ])
                        : []

    //HACK to get the mainItem as the last one, all the other eventual items as an overlay
    //no idea if is the way the user expects
    onMainItemChanged: {
        //Duck type for Item
         if (mainItem.hasOwnProperty("anchors") && mainItem.hasOwnProperty("antialiasing")) {
             scrollView.contentItem = mainItem
             mainItem.focus = true
         //don't try to reparent drawers
         } else if (mainItem.hasOwnProperty("dragMargin")) {
             return;
        //reparent sheets
        } else if (mainItem.hasOwnProperty("sheetOpen")) {
            if (mainItem.parent === root || mainItem.parent === null) {
                mainItem.parent = root;
            }
             root.data.push(mainItem);
             return;
        }

        if (scrollView.oldMainItem && scrollView.oldMainItem.hasOwnProperty("parent") && (typeof applicationWindow == 'undefined' || scrollView.oldMainItem.parent !== applicationWindow().overlay)) {
             scrollView.oldMainItem.parent = overlay
         }
         scrollView.oldMainItem = mainItem
    }
}
