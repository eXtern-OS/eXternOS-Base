/*
    This file is part of KDE.

    Copyright (c) 2018 Ralf Habacker <ralf.habacker@freenet.de>

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
#ifndef ATTICA_CONFIG_H
#define ATTICA_CONFIG_H

#include <QString>
#include <QSharedDataPointer>

#include "attica_export.h"

namespace Attica {

/**
 * Represents a server config
 */
class ATTICA_EXPORT Config
{
  public:
    typedef QList<Config> List;
    class Parser;

    /**
     * Creates an empty Config
     */
    Config();

    /**
     * Copy constructor.
     * @param other the Config to copy from
     */
    Config(const Config& other);

    /**
     * Assignment operator.
     * @param other the Config to assign from
     * @return pointer to this Config
     */
    Config& operator=(const Config& other);

    /**
     * Destructor.
     */
    ~Config();

    QString contact() const;
    QString host() const;
    QString version() const;
    bool ssl() const;
    QString website() const;

    void setContact(const QString &contact);
    void setHost(const QString &host);
    void setSsl(bool ssl);
    void setVersion(const QString &version);
    void setWebsite(const QString &website);

    /**
     * Checks whether this config is valid
     * @return @c true if config is valid, @c false otherwise
     */
    bool isValid() const;

  private:
    class Private;
    QSharedDataPointer<Private> d;
};

}

#endif
