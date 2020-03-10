/* This file is part of the KDE libraries
 *  Copyright (c) 2013 David Faure <faure@kde.org>
 *
 *  This library is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU Lesser General Public License as published by
 *  the Free Software Foundation; either version 2 of the License or ( at
 *  your option ) version 3 or, at the discretion of KDE e.V. ( which shall
 *  act as a proxy as in section 14 of the GPLv3 ), any later version.
 *
 *  This library is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *  Library General Public License for more details.
 *
 *  You should have received a copy of the GNU Lesser General Public License
 *  along with this library; see the file COPYING.LIB.  If not, write to
 *  the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
 *  Boston, MA 02110-1301, USA.
 */

#ifndef KJOBWIDGETS_H
#define KJOBWIDGETS_H

#include <kjobwidgets_export.h>
class QWidget;
class QWindow;
class KJob;

/**
 * KJobWidgets namespace
 */
namespace KJobWidgets
{
/**
 * Associate this job with a window given by @p window.
 * This is used:
 * @li by KDialogJobUiDelegate as parent widget for error messages
 * @li by KWidgetJobTracker as parent widget for progress dialogs
 * @li by KIO::AbstractJobInteractionInterface as parent widget for rename/skip dialogs
 * and possibly more.
 * @li by KIO::DropJob as parent widget of popup menus.
 * This is required on Wayland to properly position the menu.
 * @since 5.0
 */
KJOBWIDGETS_EXPORT void setWindow(KJob *job, QWidget *widget);

/**
 * Return the window associated with this job.
 * @since 5.0
 */
KJOBWIDGETS_EXPORT QWidget *window(KJob *job);

/**
 * Updates the last user action timestamp to the given time.
 * @since 5.0
 */
KJOBWIDGETS_EXPORT void updateUserTimestamp(KJob *job, unsigned long time);
/**
 * Returns the last user action timestamp
 * @since 5.0
 */
KJOBWIDGETS_EXPORT unsigned long userTimestamp(KJob *job);
}

namespace KJobWindows
{
/**
 * Associate this job with a window given by @p window.
 * This is used:
 * @li by KDialogJobUiDelegate as parent widget for error messages
 * @li by KWidgetJobTracker as parent widget for progress dialogs
 * @li by KIO::AbstractJobInteractionInterface as parent widget for rename/skip dialogs
 * and possibly more.
 * @li by KIO::DropJob as parent widget of popup menus.
 * This is required on Wayland to properly position the menu.
 * @since 5.42
 */
KJOBWIDGETS_EXPORT void setWindow(KJob *job, QWindow *window);

/**
 * Return the window associated with this job.
 * @since 5.42
 */
KJOBWIDGETS_EXPORT QWindow *window(KJob *job);
}

#endif
