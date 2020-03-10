/* This file is part of the KDE libraries
   Copyright 2007 Daniel Teske <teske@squorn.de>

   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Library General Public
   License version 2 as published by the Free Software Foundation.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Library General Public License for more details.

   You should have received a copy of the GNU Library General Public License
   along with this library; see the file COPYING.LIB.  If not, write to
   the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
   Boston, MA 02110-1301, USA.
*/
#ifndef __kbookmarkdialog_h
#define __kbookmarkdialog_h

#include "kbookmark.h"
#include "kbookmarkowner.h"
#include <QDialog>

class KBookmarkManager;
class KBookmarkDialogPrivate;

/**
 * This class provides a Dialog for editing properties, adding Bookmarks and creating new folders.
 * It can be used to show dialogs for common tasks with bookmarks.
 *
 * It is used by KBookmarkMenu to show a dialog for "Properties", "Add Bookmark" and "Create New Folder".
 * If you want to customize those dialogs, derive from KBookmarkOwner and reimplement bookmarkDialog(),
 * return a KBookmarkDialog subclass and reimplement initLayout(), aboutToShow() and save().
**/

class KBOOKMARKS_EXPORT KBookmarkDialog : public QDialog
{
    Q_OBJECT

public:
    /**
     * Creates a KBookmarkDialog instance
     */
    KBookmarkDialog(KBookmarkManager *manager, QWidget *parent = nullptr);
    /**
     * Shows a properties dialog
     * Note: this updates the bookmark and calls KBookmarkManager::emitChanged
     */
    KBookmark editBookmark(const KBookmark &bm);
    /**
     * Shows a "Add Bookmark" dialog
     * Note: this updates the bookmark and calls KBookmarkManager::emitChanged
     */
    KBookmark addBookmark(const QString &title, const QUrl &url, const QString &icon, KBookmark parent = KBookmark());
    /**
     * Creates a folder from a list of bookmarks
     * Note: this updates the bookmark and calls KBookmarkManager::emitChanged
     */
    KBookmarkGroup addBookmarks(const QList<KBookmarkOwner::FutureBookmark> &list, const QString &name = QString(), KBookmarkGroup parent = KBookmarkGroup());
    /**
     * Shows a dialog to create a new folder.
     */
    KBookmarkGroup createNewFolder(const QString &name, KBookmark parent = KBookmark());
    /**
     * Shows a dialog to select a folder.
     */
    KBookmarkGroup selectFolder(KBookmark start = KBookmark());

    ~KBookmarkDialog() override;
protected:
    void accept() override;

protected Q_SLOTS:
    void newFolderButton();

private:
    KBookmarkDialogPrivate *const d;
    friend class KBookmarkDialogPrivate;
};

#endif

