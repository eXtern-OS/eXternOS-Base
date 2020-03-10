/* This file is part of the KDE libraries
   Copyright (C) 2002 Alexander Kellett <lypanov@kde.org>

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

#ifndef __kbookmarkimporter_opera_h
#define __kbookmarkimporter_opera_h


#include <kbookmarkimporter.h>
#include <kbookmarkexporter.h>

/**
 * A class for importing Opera bookmarks
 */
class KBOOKMARKS_EXPORT KOperaBookmarkImporterImpl : public KBookmarkImporterBase
{
    Q_OBJECT // For QObject::tr
public:
    KOperaBookmarkImporterImpl() { }
    void parse() override;
    QString findDefaultLocation(bool forSaving = false) const override;
private:
    class KOperaBookmarkImporterImplPrivate *d;
};

class KBOOKMARKS_EXPORT KOperaBookmarkExporterImpl : public KBookmarkExporterBase
{
public:
    KOperaBookmarkExporterImpl(KBookmarkManager *mgr, const QString &filename)
        : KBookmarkExporterBase(mgr, filename)
    {
        ;
    }
    ~KOperaBookmarkExporterImpl() override {}
    void write(const KBookmarkGroup &parent) override;
private:
    class KOperaBookmarkExporterImplPrivate *d;
};

#endif
