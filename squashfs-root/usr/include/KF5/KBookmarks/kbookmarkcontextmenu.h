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

#ifndef KBOOKMARKCONTEXTMENU_H
#define KBOOKMARKCONTEXTMENU_H

#include <QMenu>

#include "kbookmark.h"

class KBookmarkManager;
class KBookmarkOwner;

class KBOOKMARKS_EXPORT KBookmarkContextMenu : public QMenu
{
    Q_OBJECT

public:
    KBookmarkContextMenu(const KBookmark &bm, KBookmarkManager *manager, KBookmarkOwner *owner, QWidget *parent = nullptr);
    virtual ~KBookmarkContextMenu();
    virtual void addActions();

public Q_SLOTS:
    void slotEditAt();
    void slotProperties();
    void slotInsert();
    void slotRemove();
    void slotCopyLocation();
    void slotOpenFolderInTabs();

protected:
    void addBookmark();
    void addFolderActions();
    void addProperties();
    void addBookmarkActions();
    void addOpenFolderInTabs();

    KBookmarkManager *manager() const;
    KBookmarkOwner *owner() const;
    KBookmark bookmark() const;

private Q_SLOTS:
    void slotAboutToShow();

private:
    KBookmark bm;
    KBookmarkManager *m_pManager;
    KBookmarkOwner *m_pOwner;
};

#endif
