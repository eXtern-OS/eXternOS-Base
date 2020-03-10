/*
 * Copyright (c) 1999-2003 Hans Petter Bieker <bieker@kde.org>
 *           (c) 2001      Martijn Klingens <klingens@kde.org>
 *           (c) 2007      David Jarvie <software@astrojar.org.uk>
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Library General Public
 *  License as published by the Free Software Foundation; either
 *  version 2 of the License, or (at your option) any later version.
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

#ifndef KLANGUAGENAME_H
#define KLANGUAGENAME_H

#include "kconfigwidgets_export.h"

class QString;

/**
 * @class KLanguageName klanguagename.h KLanguageName
 *
 * KLanguageName is a helper namespace that returns the name of a given language code.
 *
 * @since 5.55
 *
 */
namespace KLanguageName
{
    /**
     * Returns the name of the given language code in the current locale.
     *
     * If it can't be found in the current locale it returns the name in English.
     *
     * It it can't be found in English either it returns an empty QString.
     *
     * @param code code (ISO 639-1) of the language whose name is wanted.
     */
    KCONFIGWIDGETS_EXPORT QString nameForCode(const QString &code);

    /**
     * Returns the name of the given language code in the other given locale code.
     *
     * If it can't be found in the given locale it returns the name in English.
     *
     * It it can't be found in English either it returns an empty QString.
     *
     * @param code code (ISO 639-1) of the language whose name is wanted.
     * @param outputLocale code (ISO 639-1) of the language in which we want the name in.
     */
    KCONFIGWIDGETS_EXPORT QString nameForCodeInLocale(const QString &code, const QString &outputLocale);
}

#endif
