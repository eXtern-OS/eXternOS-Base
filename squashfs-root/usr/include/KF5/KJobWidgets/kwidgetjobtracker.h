/*  This file is part of the KDE project
    Copyright (C) 2000 Matej Koss <koss@miesto.sk>
    Copyright (C) 2007 Kevin Ottens <ervin@kde.org>
    Copyright (C) 2009 Shaun Reich <shaun.reich@kdemail.net>

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

#ifndef KWIDGETJOBTRACKER_H
#define KWIDGETJOBTRACKER_H

#include <kjobwidgets_export.h>
#include <kabstractwidgetjobtracker.h>

/**
 * @class KWidgetJobTracker kwidgetjobtracker.h KWidgetJobTracker
 *
 * This class implements a job tracker with a widget suited for use as a
 * progress dialog.
 */
class KJOBWIDGETS_EXPORT KWidgetJobTracker : public KAbstractWidgetJobTracker
{
    Q_OBJECT

public:
    /**
     * Creates a new KWidgetJobTracker
     *
     * @param parent the parent of this object and of the widget displaying the job progresses
     */
    explicit KWidgetJobTracker(QWidget *parent = nullptr);

    /**
     * Destroys a KWidgetJobTracker
     */
    ~KWidgetJobTracker() override;

    /**
     * The widget associated to this tracker.
     *
     * @param job the job that is assigned the widget we want to get
     * @return the widget displaying the job progresses
     */
    QWidget *widget(KJob *job) override;

// KDE5: move this two virtual methods to be placed correctly (ereslibre)
public Q_SLOTS:
    /**
     * Register a new job in this tracker.
     *
     * @param job the job to register
     */
    void registerJob(KJob *job) override;

    /**
     * Unregister a job from this tracker.
     *
     * @param job the job to unregister
     */
    void unregisterJob(KJob *job) override;

public:
    bool keepOpen(KJob *job) const;

protected Q_SLOTS:
    /**
     * The following slots are inherited from KJobTrackerInterface.
     */
    void infoMessage(KJob *job, const QString &plain, const QString &rich) override;
    virtual void description(KJob *job, const QString &title,
                             const QPair<QString, QString> &field1,
                             const QPair<QString, QString> &field2) override;
    void totalAmount(KJob *job, KJob::Unit unit, qulonglong amount) override;
    void processedAmount(KJob *job, KJob::Unit unit, qulonglong amount) override;
    void percent(KJob *job, unsigned long percent) override;
    void speed(KJob *job, unsigned long value) override;
    void slotClean(KJob *job) override;
    void suspended(KJob *job) override;
    void resumed(KJob *job) override;

    //TODO: Misses canResume()

private:
    class Private;
    Private *const d;

    Q_PRIVATE_SLOT(d, void _k_showProgressWidget())
};

#endif
