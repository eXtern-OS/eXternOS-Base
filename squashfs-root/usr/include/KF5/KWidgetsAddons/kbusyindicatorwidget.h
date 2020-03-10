/*
    Copyright 2019 Harald Sitter <sitter@kde.org>

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
    License along with this library.  If not, see <https://www.gnu.org/licenses/>.
*/

#ifndef KBUSYINDICATORWIDGET_H
#define KBUSYINDICATORWIDGET_H

#include <kwidgetsaddons_export.h>

#include <QWidget>

/**
 * @brief Rotating spinning icon to indicate busyness
 *
 * When you need to communicate to the user that your application is busy with
 * something you'll want to use a KBusyIndicatorWidget to display an infinately
 * spinnning indicator icon.
 *
 * A way of using this widget is to combine it with a QLabel to construct a
 * status line:
 *
 * ```
 * auto layout = new QHBoxLayout;
 * layout->addWidget(new KBusyIndicatorWidget);
 * layout->addWidget(new QLabel(QStringLiteral("Waterig the flowers...")));
 * ```
 *
 * @image html kbusyindicatorwidget.png "KBusyIndicatorWidget with label"
 *
 * KBusyIndicatorWidget is set apart from KPixmapSequenceWidget in that it
 * does not render a pixmap sequence but rather animates a scaled Icon.
 * It can support multiple semi-abitrary sizes and quality is only limited
 * by the resolution of available icons. It is also easier to use as its use
 * is more specific.
 *
 * @since 5.61.0
 */
class KWIDGETSADDONS_EXPORT KBusyIndicatorWidget : public QWidget
{
    Q_OBJECT
public:
    explicit KBusyIndicatorWidget(QWidget *parent = nullptr);
    ~KBusyIndicatorWidget() override;

    QSize minimumSizeHint() const override;

protected:
    void showEvent(QShowEvent *event) override;
    void hideEvent(QHideEvent *event) override;
    void resizeEvent(QResizeEvent *event) override;
    void paintEvent(QPaintEvent *) override;
    bool event(QEvent *event) override;

private:
    class KBusyIndicatorWidgetPrivate *const d;
};

#endif // KBUSYINDICATORWIDGET_H
