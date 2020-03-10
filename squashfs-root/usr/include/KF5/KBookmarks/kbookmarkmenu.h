/* This file is part of the KDE project
   Copyright (C) 1998, 1999 Torben Weis <weis@kde.org>
   Copyright (C) 2006 Daniel Teske <teske@squorn.de>

   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Library General Public
   License as published by the Free Software Foundation; either
   version 2 of the License, or (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Library General Public License for more details.

   You should have received a copy of the GNU Library General Public License
   along with this library; see the file COPYING.LIB.  If not, write to
   the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
   Boston, MA 02110-1301, USA.
*/

#ifndef __kbookmarkmenu_h__
#define __kbookmarkmenu_h__

#include <kbookmarks_export.h>

#include <QObject>

class QAction;
class QMenu;
class KBookmark;
class KActionCollection;
class KBookmarkManager;
class KBookmarkOwner;
class KBookmarkMenu;
class KBookmarkActionInterface;

class KBookmarkMenuPrivate; // Not implemented

/**
 * This class provides a bookmark menu.  It is typically used in
 * cooperation with KActionMenu but doesn't have to be.
 *
 * If you use this class by itself, then it will use KDE defaults for
 * everything -- the bookmark path, bookmark editor, bookmark launcher..
 * everything.  These defaults reside in the classes
 * KBookmarkOwner (editing bookmarks) and KBookmarkManager
 * (almost everything else).  If you wish to change the defaults in
 * any way, you must reimplement either this class or KBookmarkOwner.
 *
 * Using this class is very simple:
 *
 * 1) Create a popup menu (either KActionMenu or QMenu will do)
 * 2) Instantiate a new KBookmarkMenu object using the above popup
 *    menu as a parameter
 * 3) Insert your (now full) popup menu wherever you wish
 *
 * The functionality of this class can be disabled with the "action/bookmarks"
 * Kiosk action (see the KAuthorized namespace).
 */
class KBOOKMARKS_EXPORT KBookmarkMenu : public QObject
{
    Q_OBJECT
public:
    /**
     * Fills a bookmark menu
     * (one instance of KBookmarkMenu is created for the toplevel menu,
     *  but also one per submenu).
     *
     * @param mgr The bookmark manager to use (i.e. for reading and writing)
     * @param owner implementation of the KBookmarkOwner callback interface.
     * Note: If you pass a null KBookmarkOwner to the constructor, the
     * openBookmark signal is not emitted, instead QDesktopServices::openUrl is used to open the bookmark.
     * @param parentMenu menu to be filled
     * @param collec parent collection for the KActions.
     *
     * @todo KDE 5: give ownership of the bookmarkmenu to another qobject, e.g. parentMenu.
     * Currently this is a QObject without a parent, use setParent to benefit from automatic deletion.
     */
    KBookmarkMenu(KBookmarkManager *mgr, KBookmarkOwner *owner, QMenu *parentMenu, KActionCollection *collec);

    /**
     * Creates a bookmark submenu
     *
     * @todo KF6: give ownership of the bookmarkmenu to another qobject, e.g. parentMenu.
     * Currently this is a QObject without a parent, use setParent to benefit from automatic deletion.
     */
    KBookmarkMenu(KBookmarkManager *mgr, KBookmarkOwner *owner,
                  QMenu *parentMenu, const QString &parentAddress);

    ~KBookmarkMenu();

    /**
     * Call ensureUpToDate() if you need KBookmarkMenu to adjust to its
     * final size before it is executed.
     **/
    void ensureUpToDate();

    /**
     * @brief Sets the number of currently open tabs
     * @param numberOfOpenTabs The number of currently open tabs
     * @see numberOfOpenTabs()
     * @since 5.58
     */
    void setNumberOfOpenTabs(int numberOfOpenTabs);
    /**
     * This function returns how many (if any) tabs the application has open.
     * This is used to determine if the Add a folder for all open
     * tabs should be added to the menu, so if the application has more than
     * one tab open, then the menu will be added.
     * Default returns @c 2.
     * @since 5.58
     */
    int numberOfOpenTabs() const;

public Q_SLOTS:
    // public for KonqBookmarkBar
    void slotBookmarksChanged(const QString &);

protected Q_SLOTS:
    void slotAboutToShow();
    void slotAddBookmarksList();
    void slotAddBookmark();
    void slotNewFolder();
    void slotOpenFolderInTabs();

protected:
    virtual void clear();
    virtual void refill();
    virtual QAction *actionForBookmark(const KBookmark &bm);
    virtual QMenu *contextMenu(QAction *action);

    void addActions();
    void fillBookmarks();
    void addAddBookmark();
    void addAddBookmarksList();
    void addEditBookmarks();
    void addNewFolder();
    void addOpenInTabs();

    bool isRoot() const;
    bool isDirty() const;

    /**
     * Parent bookmark for this menu.
     */
    QString parentAddress() const;

    KBookmarkManager *manager() const;
    KBookmarkOwner *owner() const;
    /**
     * The menu in which we insert our actions
     * Supplied in the constructor.
     */
    QMenu *parentMenu() const;

    /**
     * List of our sub menus
     */
    QList<KBookmarkMenu *> m_lstSubMenus;

    // This is used to "export" our actions into an actionlist
    // we got in the constructor. So that the program can show our
    // actions in their shortcut dialog
    KActionCollection *m_actionCollection;
    /**
     * List of our actions.
     */
    QList<QAction *> m_actions;

private Q_SLOTS:
    void slotCustomContextMenu(const QPoint &);

private:
    KBookmarkMenuPrivate *d;

    bool m_bIsRoot;
    bool m_bDirty;
    KBookmarkManager *m_pManager;
    KBookmarkOwner *m_pOwner;

    QMenu *m_parentMenu;

private:
    QString m_parentAddress;
};

#endif
