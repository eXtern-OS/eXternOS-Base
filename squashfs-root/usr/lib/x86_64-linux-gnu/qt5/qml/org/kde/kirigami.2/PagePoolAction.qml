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
import QtQuick.Controls 2.5 as Controls
import org.kde.kirigami 2.11 as Kirigami

/**
 * An action used to load Pages coming from a common PagePool
 * in a PageRow or QtQuickControls2 StackView
 *
 * @inherit Action
 */
Kirigami.Action {
    id: root

    /**
     * page: string
     * Url or filename of the page this action will load
     */
    property string page

    /**
     * pagePool: Kirigami.PagePool
     * The PagePool used by this PagePoolAction.
     * PagePool will make sure only one instance of the page identified by the page url will be created and reused.
     *PagePool's lastLoaderUrl property will be used to control the mutual 
     * exclusivity of the checked state of the PagePoolAction instances
     * sharing the same PagePool
     */
    property Kirigami.PagePool pagePool

    /**
     * pageStack: Kirigami.PageRow or QtQuickControls2 StackView
     * The component that will instantiate the pages, which has to work with a stack logic.
     * Kirigami.PageRow is recommended, but will work with QtQuicControls2 StackView as well.
     * By default this property is binded to ApplicationWindow's global
     * pageStack, which is a PageRow by default.
     */
    property Item pageStack: typeof applicationWindow != undefined ? applicationWindow().pageStack : null

    /**
     * basePage: Kirigami.Page
     * The page of pageStack new pages will be pushed after.
     * All pages present after the given basePage will be removed from the pageStack
     */
    property Controls.Page basePage

    checked: pagePool && pagePool.resolvedUrl(page) == pagePool.lastLoadedUrl
    onTriggered: {
        if (page.length == 0 || !pagePool || !pageStack) {
            return;
        }

        if (pagePool.resolvedUrl(page) == pagePool.lastLoadedUrl) {
            return;
        }

        if (!pageStack.hasOwnProperty("pop") || typeof pageStack.pop !== "function" || !pageStack.hasOwnProperty("push") || typeof pageStack.push !== "function") {
            return;
        }

        if (pagePool.isLocalUrl(page)) {
            if (basePage) {
                pageStack.pop(basePage);
            } else {
                pageStack.clear();
            }
            pageStack.push(pagePool.loadPage(page));
        } else {
            pagePool.loadPage(page, function(item) {
                if (basePage) {
                    pageStack.pop(basePage);
                } else {
                    pageStack.clear();
                }
                pageStack.push(item);
            });
        }
    }
}
