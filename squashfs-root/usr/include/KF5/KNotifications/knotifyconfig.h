/*
   Copyright (C) 2005-2009 by Olivier Goffart <ogoffart at kde.org>

   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 2.1 of the License, or (at your option) version 3, or any
   later version accepted by the membership of KDE e.V. (or its
   successor approved by the membership of KDE e.V.), which shall
   act as a proxy defined in Section 6 of version 3 of the license.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public
   License along with this library.  If not, see <http://www.gnu.org/licenses/>.

 */

#ifndef KNOTIFYCONFIG_H
#define KNOTIFYCONFIG_H

#include <ksharedconfig.h>

#include <QPair>
#include <QObject> //for Wid
#include <QImage>
#include "knotifications_export.h"

typedef QList< QPair<QString,QString> > ContextList;

/**
 * @class KNotifyImage knotifyconfig.h KNotifyConfig
 *
 * An image with lazy loading from the byte array
 */
class KNOTIFICATIONS_EXPORT KNotifyImage
{
    public:
        KNotifyImage() : dirty(false) {}
        KNotifyImage(const QByteArray &data) : source(data), dirty(true) {}
        QImage toImage();
        bool isNull() {
            return dirty ? source.isEmpty() : image.isNull();
        }
        QByteArray data() const {
            return source;
        }
    private:
        QByteArray source;
        QImage image;
        bool dirty;
};


/**
 * @class KNotifyConfig knotifyconfig.h KNotifyConfig
 *
 * Represent the configuration for an event
 * @author Olivier Goffart <ogoffart@kde.org>
*/
class KNOTIFICATIONS_EXPORT KNotifyConfig
{
public:
    KNotifyConfig(const QString &appname, const ContextList &_contexts , const QString &_eventid);
    ~KNotifyConfig();

    KNotifyConfig *copy() const;

    /**
        * @return entry from the knotifyrc file
        *
        * This will return the configuration from the user for the given key.
        * It first look into the user config file, and then in the global config file.
        *
        * return a null string if the entry doesn't exist
        */
    QString readEntry(const QString &entry , bool path = false);

    /**
        * the pixmap to put on the notification
        */
    KNotifyImage image;

    /**
        * the name of the application that triggered the notification
        */
    QString appname;

    /**
        * @internal
        */
    KSharedConfig::Ptr eventsfile,configfile;
    ContextList contexts;

    /**
        * the name of the notification
        */
    QString eventid;

    /**
        * reparse the cached configs.  to be used when the config may have changed
        */
    static void reparseConfiguration();

    static void reparseSingleConfiguration(const QString &app);
};

#endif
