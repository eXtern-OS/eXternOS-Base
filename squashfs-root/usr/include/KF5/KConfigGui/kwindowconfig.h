/*
   This file is part of the KDE libraries
   Copyright (c) 2012 Benjamin Port <benjamin.port@ben2367.fr>

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

#ifndef KWINDOWCONFIG_H
#define KWINDOWCONFIG_H

#include <kconfiggroup.h>
#include <kconfiggui_export.h>

class QWindow;

/**
 * Save and load window sizes into a config
 */
namespace KWindowConfig
{
/**
 * Saves the window's size dependent on the screen dimension either to the
 * global or application config file.
 *
 * @note the group must be set before calling
 *
 * @param window The window to save size.
 * @param config The config group to read from.
 * @param options passed to KConfigGroup::writeEntry()
 * @since 5.0
 */
KCONFIGGUI_EXPORT void saveWindowSize(const QWindow *window, KConfigGroup &config, KConfigGroup::WriteConfigFlags options = KConfigGroup::Normal);

/**
 * Restores the dialog's size from the configuration according to
 * the screen size.
 *
 * If you're calling this from a constructor (for a mainwindow or dialog, for instance)
 * you should first call winId() so that a QWindow is created, then you can call windowHandle()
 * to pass to this method.
 *
 * Example code:
 * @code
 *   create(); // ensure there's a window created
 *   const QSize availableSize = windowHandle()->screen()->availableSize();
 *   windowHandle()->resize(availableSize.width() * 0.7, availableSize.height() * 0.5); // default size
 *   KWindowConfig::restoreWindowSize(windowHandle(), KSharedConfig::openConfig()->group("MyDialog"));
 *   resize(windowHandle()->size()); // workaround for QTBUG-40584
 * @endcode
 *
 * @note the group must be set before calling
 *
 * @param window The window to restore size.
 * @param config The config group to read from.
 * @since 5.0.
 */
KCONFIGGUI_EXPORT void restoreWindowSize(QWindow *window,  const KConfigGroup &config);
}

#endif // KWINDOWCONFIG_H
