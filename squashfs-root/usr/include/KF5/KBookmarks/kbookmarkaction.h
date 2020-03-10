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

#ifndef KBOOKMARKACTION_H
#define KBOOKMARKACTION_H

#include "kbookmarkactioninterface.h"
#include <QAction>

class KBookmark;
class KBookmarkOwner;

/**
 * This class is a QAction for bookmarks.
 * It provides a nice constructor.
 * And on triggered uses the owner to open the bookmark.
 */
class KBOOKMARKS_EXPORT KBookmarkAction : public QAction, public KBookmarkActionInterface
{
    Q_OBJECT
public:
    KBookmarkAction(const KBookmark &bk, KBookmarkOwner *owner, QObject *parent);
    virtual ~KBookmarkAction();

public Q_SLOTS:
    void slotSelected(Qt::MouseButtons mb, Qt::KeyboardModifiers km);

private Q_SLOTS:
    void slotTriggered();

private:
    KBookmarkOwner *m_pOwner;
};

#endif
