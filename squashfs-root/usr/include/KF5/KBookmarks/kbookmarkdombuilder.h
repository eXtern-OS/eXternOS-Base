/* This file is part of the KDE project
   Copyright (C) 2003 Alexander Kellett <lypanov@kde.org>

   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Library General Public
   License as published by the Free Software Foundation; either
   version 2 of the License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Library General Public License for more details.

   You should have received a copy of the GNU Library General Public License
   along with this program; see the file COPYING.  If not, write to
   the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
   Boston, MA 02110-1301, USA.
*/

#ifndef __kbookmarkdombuilder_h
#define __kbookmarkdombuilder_h

#include <QtCore/QStack>
#include <QtCore/QObject>
#include <kbookmark.h>

class KBOOKMARKS_EXPORT KBookmarkDomBuilder : public QObject
{
    Q_OBJECT
public:
    KBookmarkDomBuilder(const KBookmarkGroup &group, KBookmarkManager *);
    virtual ~KBookmarkDomBuilder();
    void connectImporter(const QObject *);
protected Q_SLOTS:
    void newBookmark(const QString &text, const QString &url, const QString &additionalInfo);
    void newFolder(const QString &text, bool open, const QString &additionalInfo);
    void newSeparator();
    void endFolder();
private:
    QStack<KBookmarkGroup> m_stack;
    QList<KBookmarkGroup> m_list;
    KBookmarkManager *m_manager;
    class KBookmarkDomBuilderPrivate *p;
};

#endif
