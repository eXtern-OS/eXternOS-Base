//  -*- c-basic-offset:4; indent-tabs-mode:nil -*-
/* This file is part of the KDE libraries
   Copyright (C) 1996-1998 Martin R. Jones <mjones@kde.org>
   Copyright (C) 2000 David Faure <faure@kde.org>
   Copyright (C) 2003 Alexander Kellett <lypanov@kde.org>

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

#ifndef __kbookmarkexporter_h
#define __kbookmarkexporter_h

#include <kbookmark.h>

class KBOOKMARKS_EXPORT KBookmarkExporterBase
{
public:
    KBookmarkExporterBase(KBookmarkManager *mgr, const QString &fileName)
        : m_fileName(fileName), m_pManager(mgr)
    {}
    virtual ~KBookmarkExporterBase() {}
    virtual void write(const KBookmarkGroup &) = 0;
protected:
    QString m_fileName;
    KBookmarkManager *m_pManager;
private:
    class KBookmarkExporterBasePrivate *d;
};

#endif
