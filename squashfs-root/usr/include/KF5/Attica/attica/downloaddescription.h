/*
This file is part of KDE.

Copyright (c) 2009 Frederik Gladhorn <gladhorn@kde.org>

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

#ifndef DOWNLOADDESCRIPTION_H
#define DOWNLOADDESCRIPTION_H

#include <QSharedData>
#include <QString>

#include "attica_export.h"

namespace Attica
{

class ATTICA_EXPORT DownloadDescription
{
public:

    enum Type {
        FileDownload = 0,
        LinkDownload,
        PackageDownload
    };

    DownloadDescription();
    DownloadDescription(const DownloadDescription &other);

    DownloadDescription &operator=(const DownloadDescription &other);
    ~DownloadDescription();

    /**
      The id of the description - as one Content can have multiple download descriptions associated.
      This will simply be 1, 2, ...
      */
    int id() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    int id();
#endif

#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(0, 2, "Use DownloadDescription::type()")
    Attica::DownloadDescription::Type type();
#endif
    Attica::DownloadDescription::Type type() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(0, 2)
    ATTICA_DEPRECATED_VERSION(0, 2, "Use DownloadDescription::type()")
    bool isDownloadtypLink();
#endif
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    bool hasPrice();
#endif
    bool hasPrice() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    QString category();
#endif
    QString category() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    QString name();
#endif
    QString name() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    QString link();
#endif
    QString link() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    QString distributionType();
#endif
    QString distributionType() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    QString priceReason();
#endif
    QString priceReason() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    QString priceAmount();
#endif
    QString priceAmount() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    uint size();
#endif
    uint size() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    QString gpgFingerprint();
#endif
    QString gpgFingerprint() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    QString gpgSignature();
#endif
    QString gpgSignature() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    QString packageName();
#endif
    QString packageName() const;
#if ATTICA_ENABLE_DEPRECATED_SINCE(5, 4)
    ATTICA_DEPRECATED_VERSION(5, 4, "Use const overload")
    QString repository();
#endif
    QString repository() const;
    /**
     * Get the list of tags for this download description
     * @since 5.50
     */
    QStringList tags() const;

    void setId(int id);
    void setType(Attica::DownloadDescription::Type type);
#if ATTICA_ENABLE_DEPRECATED_SINCE(0, 2)
    ATTICA_DEPRECATED_VERSION(0, 2, "Use DownloadDescription::setType(Attica::DownloadDescription::Type)")
    void setDownloadtypLink(bool isLink);
#endif
    void setHasPrice(bool hasPrice);
    void setCategory(const QString &category);
    void setName(const QString &name);
    void setLink(const QString &link);
    void setDistributionType(const QString &distributionType);
    void setPriceReason(const QString &priceReason);
    void setPriceAmount(const QString &priceAmount);
    void setSize(uint size);
    void setGpgFingerprint(const QString &fingerprint);
    void setGpgSignature(const QString &signature);
    void setPackageName(const QString &packageName);
    void setRepository(const QString &repository);
    /**
     * Set the list of tags for this download description
     * @since 5.50
     */
    void setTags(const QStringList &tags);

private:
    class Private;
    QSharedDataPointer<Private> d;
};

}

#endif // DOWNLOADDESCRIPTION_H
