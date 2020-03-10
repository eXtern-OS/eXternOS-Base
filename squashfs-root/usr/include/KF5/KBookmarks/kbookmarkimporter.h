//  -*- c-basic-offset:4; indent-tabs-mode:nil -*-
/* This file is part of the KDE libraries
   Copyright (C) 2000 David Faure <faure@kde.org>

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

#ifndef __kbookmarkimporter_h
#define __kbookmarkimporter_h

#include <QObject>

#include "kbookmark.h"

/**
 * A class for importing NS bookmarks
 * KEditBookmarks uses it to insert bookmarks into its DOM tree,
 * and KActionMenu uses it to create actions directly.
 */
class KBOOKMARKS_EXPORT KBookmarkImporterBase : public QObject
{
    Q_OBJECT
public:
    KBookmarkImporterBase() {}
    virtual ~KBookmarkImporterBase() {}

    void setFilename(const QString &filename)
    {
        m_fileName = filename;
    }

    virtual void parse() = 0;
    virtual QString findDefaultLocation(bool forSaving = false) const = 0;

    // TODO - make this static?
    void setupSignalForwards(QObject *src, QObject *dst);
    static KBookmarkImporterBase *factory(const QString &type);

Q_SIGNALS:
    /**
     * Notify about a new bookmark
     * Use "html" for the icon
     */
    void newBookmark(const QString &text, const QString &url, const QString &additionalInfo);

    /**
     * Notify about a new folder
     * Use "bookmark_folder" for the icon
     */
    void newFolder(const QString &text, bool open, const QString &additionalInfo);

    /**
     * Notify about a new separator
     */
    void newSeparator();

    /**
     * Tell the outside world that we're going down
     * one menu
     */
    void endFolder();

protected:
    QString m_fileName;

private:
    class KBookmarkImporterBasePrivate *d;
};

/**
 * A class for importing XBEL files
 */
class KBOOKMARKS_EXPORT KXBELBookmarkImporterImpl : public KBookmarkImporterBase, protected KBookmarkGroupTraverser
{
    Q_OBJECT
public:
    KXBELBookmarkImporterImpl() {}
    void parse() override;
    QString findDefaultLocation(bool = false) const override
    {
        return QString();
    }
protected:
    void visit(const KBookmark &) override;
    void visitEnter(const KBookmarkGroup &) override;
    void visitLeave(const KBookmarkGroup &) override;
private:
    class KXBELBookmarkImporterImplPrivate *d;
};

#endif
