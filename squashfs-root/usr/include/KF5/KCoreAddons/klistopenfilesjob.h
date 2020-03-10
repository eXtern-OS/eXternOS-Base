/*
 *  This file is part of the KDE project
 *  Copyright (C) 2010 by Jacopo De Simoi <wilderkde@gmail.com>
 *  Copyright (C) 2014 by Lukáš Tinkl <ltinkl@redhat.com>
 *  Copyright (C) 2016 by Kai Uwe Broulik <kde@privat.broulik.de>
 *  Copyright (C) 2019 David Hallas <david@davidhallas.dk>
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Library General Public
 *  License version 2 as published by the Free Software Foundation.
 *
 *  This library is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *  Library General Public License for more details.
 *
 *  You should have received a copy of the GNU Library General Public License
 *  along with this library; see the file COPYING.LIB.  If not, write to
 *  the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
 *  Boston, MA 02110-1301, USA.
*/

#ifndef KLISTOPENFILESJOB_H
#define KLISTOPENFILESJOB_H

#include <kcoreaddons_export.h>
#include <kprocesslist.h>
#include <kjob.h>
#include <QObject>
#include <QScopedPointer>
#include <QString>

class KListOpenFilesJobPrivate;


/**
 * @brief Provides information about processes that have open files in a given path or subdirectory of path.
 *
 * When start() is invoked it starts to collect information about processes that have any files open in path or a
 * subdirectory of path. When it is done the KJob::result signal is emitted and the result can be retrieved with the
 * processInfoList function.
 *
 * On Unix like systems the lsof utility is used to get the list of processes.
 * On Windows the listing always fails with error code NotSupported.
 *
 * @since 5.63
 */
class KCOREADDONS_EXPORT KListOpenFilesJob : public KJob
{
    Q_OBJECT
public:
    explicit KListOpenFilesJob(const QString &path);
    ~KListOpenFilesJob() override;
    void start() override;
    /**
     * @brief Returns the list of processes with open files for the requested path
     * @return The list of processes with open files for the requested path
     */
    KProcessList::KProcessInfoList processInfoList() const;

public:
    /**
     * @brief Special error codes emitted by KListOpenFilesJob
     *
     * The KListOpenFilesJob uses the error codes defined here besides the standard error codes defined by KJob
     */
    enum class Error {
        /*** Indicates that the platform doesn't support listing open files by processes */
        NotSupported = KJob::UserDefinedError + 1,
        /*** Internal error has ocurred */
        InternalError = KJob::UserDefinedError + 2,
        /*** The specified path does not exist */
        DoesNotExist = KJob::UserDefinedError + 11,
    };
private:
    friend class KListOpenFilesJobPrivate;
    QScopedPointer<KListOpenFilesJobPrivate> d;
};

#endif // KLISTOPENFILESJOB_H
