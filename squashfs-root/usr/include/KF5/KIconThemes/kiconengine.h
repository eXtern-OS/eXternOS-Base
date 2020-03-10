/* This file is part of the KDE libraries
    Copyright (C) 2006 Hamish Rodda <rodda@kde.org>

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

#ifndef KICONENGINE_H
#define KICONENGINE_H

#include "kiconthemes_export.h"
#include <QIconEngine>
#include <QPointer>

class KIconLoader;

/**
 * @class KIconEngine kiconengine.h KIconEngine
 *
 * \short A class to provide rendering of KDE icons.
 *
 * Currently, this class is not much more than a wrapper around QIconEngine.
 * However, it should not be difficult to extend with features such as SVG
 * rendered icons.
 *
 * Icon themes specifying a KDE-Extensions string list setting, will limit
 * themselves to checking these extensions exclusively, in the order specified
 * in the setting.
 *
 * @author Hamish Rodda <rodda@kde.org>
 */
class KICONTHEMES_EXPORT KIconEngine : public QIconEngine // exported for kdelibs4support's KIcon and plasma integration
{
public:
    /**
     * Constructs an icon engine for a KDE named icon.
     *
     * @param iconName the name of the icon to load
     * @param iconLoader The KDE icon loader that this engine is to use.
     * @param overlays Add one or more overlays to the icon. See KIconLoader::Overlays.
     *
     * @sa KIconLoader
     */
    KIconEngine(const QString &iconName, KIconLoader *iconLoader, const QStringList &overlays);

    /**
     * \overload
     */
    KIconEngine(const QString &iconName, KIconLoader *iconLoader);

    /**
     * Destructor.
     */
    ~KIconEngine() override;

    /// Reimplementation
    QSize actualSize(const QSize &size, QIcon::Mode mode, QIcon::State state) override;
    /// Reimplementation
    void paint(QPainter *painter, const QRect &rect, QIcon::Mode mode, QIcon::State state) override;
    /// Reimplementation
    QPixmap pixmap(const QSize &size, QIcon::Mode mode, QIcon::State state) override;
    /// Reimplementation
    QString iconName() const override;
    /// Reimplementation
    QList<QSize> availableSizes(QIcon::Mode mode, QIcon::State state) const override;

    QString key() const override;
    QIconEngine *clone() const override;
    bool read(QDataStream &in) override;
    bool write(QDataStream &out) const override;

    void virtual_hook(int id, void *data) override;

private:
    //TODO KF6: move those into the d-pointer
    QPixmap createPixmap(const QSize &size, qreal scale, QIcon::Mode mode, QIcon::State state);
    QString mIconName;
    QStringList mOverlays;
    QPointer<KIconLoader> mIconLoader;
};

inline KIconEngine::~KIconEngine()
{
}

#endif
