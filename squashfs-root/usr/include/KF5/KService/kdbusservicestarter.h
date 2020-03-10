/* This file is part of the KDE libraries
   Copyright (C) 2003 David Faure <faure@kde.org>

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

#ifndef KDBUSSERVICESTARTER_H
#define KDBUSSERVICESTARTER_H

#include <kservice_export.h>

#include <QString>

class KDBusServiceStarterPrivate;

#if KSERVICE_ENABLE_DEPRECATED_SINCE(5, 61)
/**
 * @class KDBusServiceStarter kdbusservicestarter.h <KDBusServiceStarter>
 *
 * A generic D-Bus service starter, using KServiceTypeTrader.
 * The default implementation starts new processes, but this interface can
 * also be reimplemented by specific applications to provide dlopened in-process D-Bus objects.
 * This interface is similar to the startService() function found in QDBusConnectionInterface, but
 * with the added benefit of using KServiceTypeTrader (and, therefore, additional constraints and the
 * ability to search the standard KDE dirs).
 * @author David Faure <faure@kde.org>
 *
 * @deprecated since 5.61, use D-Bus activation instead
 */
class KSERVICE_EXPORT KDBusServiceStarter   //krazy:exclude=dpointer (uses Q_GLOBAL_STATIC)
{
public:

    KSERVICE_DEPRECATED_VERSION(5, 61, "Use D-Bus activation")
    static KDBusServiceStarter *self();

    /**
     * Check if a given D-Bus service is available - from the serviceType it's supposed to implement.
     *
     * The trader is queried to find the preferred application for this serviceType,
     * with the constraint that its X-DBus-ServiceName property must be defined.
     * Then the D-Bus server is checked. If the service is not available,
     * this method will call startServiceFor to start it.
     *
     * @param serviceType the type of service we're looking for
     * @param constraint see KServiceTypeTrader
     * @param error On failure, @p error contains a description of the error
     *         that occurred. If the pointer is 0, the argument will be
     *         ignored
     * @param dbusService On success, @p dbusService contains the D-Bus service name
     *         under which this service is available. If the pointer is 0 the argument
     *         will be ignored
     * @param flags for future extensions (currently unused)
     *
     * @return an error code indicating success (== 0) or failure (> 0).
     */
    int findServiceFor(const QString &serviceType,
                       const QString &constraint = QString(),
                       QString *error = nullptr, QString *dbusService = nullptr,
                       int flags = 0);

    /**
     * Find an implementation of the given @p serviceType,
     * and start it, to use its D-Bus interface.
     * The default implementation uses KServiceTypeTrader to find the preferred Application,
     * and then starts it using KToolInvocation::startService...
     *
     * However applications (like kontact) can reimplement this method, to provide
     * an in-process way of loading the implementation for this service type.
     *
     * @param serviceType the type of service we're looking for
     * @param constraint see KServiceTypeTrader
     * @param error On failure, @p error contains a description of the error
     *         that occurred. If the pointer is 0, the argument will be
     *         ignored
     * @param dbusService On success, @p dbusService contains the D-Bus service name
     *         under which this service is available. If the pointer is 0 the argument
     *         will be ignored
     * @param flags for future extensions (currently unused)
     *
     * @return an error code indicating success (== 0) or failure (> 0).
     */
    virtual int startServiceFor(const QString &serviceType,
                                const QString &constraint = QString(),
                                QString *error = nullptr, QString *dbusService = nullptr,
                                int flags = 0);
protected:
    friend class KDBusServiceStarterPrivate;
    KDBusServiceStarter();
    virtual ~KDBusServiceStarter();
};
#endif

#endif

