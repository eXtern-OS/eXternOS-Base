/*
 *   Copyright 2018 David Edmundson <davidedmundson@kde.org>
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU Library General Public License as
 *   published by the Free Software Foundation; either version 2, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details
 *
 *   You should have received a copy of the GNU Library General Public
 *   License along with this program; if not, write to the
 *   Free Software Foundation, Inc.,
 *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */

#ifndef KCONFIGWATCHER_H
#define KCONFIGWATCHER_H

#include <QObject>
#include <QSharedPointer>

#include <KSharedConfig>
#include <KConfigGroup>

#include <kconfigcore_export.h>

class KConfigWatcherPrivate;

/**
 * \class KConfigWatcher kconfigwatcher.h <KConfigWatcher>
 *
 * Notifies when another client has updated this config file with the Notify flag set.
 * @since 5.51
 */
class KCONFIGCORE_EXPORT KConfigWatcher: public QObject
{
    Q_OBJECT
public:
    typedef QSharedPointer<KConfigWatcher> Ptr;

    /**
     * Instantiate a ConfigWatcher for a given config
     *
     * @note any additional config sources should be set before this point.
     */
    static Ptr create(const KSharedConfig::Ptr &config);

    ~KConfigWatcher() override;

Q_SIGNALS:
    /**
     * Emitted when a config group has changed
     * The config will be reloaded before this signal is emitted
     *
     * @arg group the config group that has changed
     * @arg names a list of entries that have changed within that group
     */
    void configChanged(const KConfigGroup &group, const QByteArrayList &names);

private Q_SLOTS:
    void onConfigChangeNotification(const QHash<QString, QByteArrayList> &changes);

private:
    KConfigWatcher(const KSharedConfig::Ptr &config);
    Q_DISABLE_COPY(KConfigWatcher)
    const QScopedPointer<KConfigWatcherPrivate> d;
};

#endif
