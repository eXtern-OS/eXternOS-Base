/**************************************************************************
**
** This file is part of the KDE Frameworks
**
** Copyright (c) 2011 Nokia Corporation and/or its subsidiary(-ies).
** Copyright (c) 2019 David Hallas <david@davidhallas.dk>
**
** GNU Lesser General Public License Usage
**
** This file may be used under the terms of the GNU Lesser General Public
** License version 2.1 as published by the Free Software Foundation and
** appearing in the file LICENSE.LGPL included in the packaging of this file.
** Please review the following information to ensure the GNU Lesser General
** Public License version 2.1 requirements will be met:
** http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
**
** In addition, as a special exception, Nokia gives you certain additional
** rights. These rights are described in the Nokia Qt LGPL Exception
** version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
**
** Other Usage
**
** Alternatively, this file may be used in accordance with the terms and
** conditions contained in a signed written agreement between you and Nokia.
**
** If you have questions regarding the use of this file, please contact
** Nokia at info@qt.nokia.com.
**
**************************************************************************/

#ifndef KPROCESSLIST_H
#define KPROCESSLIST_H

#include <kcoreaddons_export.h>
#include <QSharedDataPointer>
#include <QString>
#include <QList>

namespace KProcessList
{

class KProcessInfoPrivate;

/**
 * @brief Contains information about a process. This class is usually not used alone but rather returned by
 * processInfoList and processInfo. To check if the data contained in this class is valid use the isValid method.
 * @since 5.58
 */
class KCOREADDONS_EXPORT KProcessInfo {
public:
    KProcessInfo();
    KProcessInfo(qint64 pid, const QString &command, const QString &user);
    KProcessInfo(qint64 pid, const QString &command, const QString &name, const QString &user);

    KProcessInfo(const KProcessInfo &other);
    ~KProcessInfo();
    KProcessInfo &operator=(const KProcessInfo &other);
    /**
     * @brief If the KProcessInfo contains valid information. If it returns true the pid, name and user function
     * returns valid information, otherwise they return value is undefined.
     */
    bool isValid() const;
    /**
     * @brief The pid of the process
     */
    qint64 pid() const;
    /**
     * @brief The name of the process. The class will try to get the full path to the executable file for the process
     * but if it is not available the name of the process will be used instead.
     * e.g /bin/ls
     */
    QString name() const;
    /**
     * @brief The username the process is running under.
     */
    QString user() const;
    /**
     * @brief The command line running this process
     * e.g /bin/ls /some/path -R
     * @since 5.61
     */
    QString command() const;
private:
    QSharedDataPointer<KProcessInfoPrivate> d_ptr;
};

typedef QList<KProcessInfo> KProcessInfoList;

/**
 * @brief Retrieves the list of currently active processes.
 * @since 5.58
 */
KCOREADDONS_EXPORT KProcessInfoList processInfoList();

/**
 * @brief Retrieves process information for a specific process-id. If the process is not found a KProcessInfo with
 * isValid == false will be returned.
 * @param pid The process-id to retrieve information for.
 * @since 5.58
 */
KCOREADDONS_EXPORT KProcessInfo processInfo(qint64 pid);

} // KProcessList namespace

#endif // KPROCESSLIST_H
