/*
  Copyright (c) 2014 Montel Laurent <montel@kde.org>
  based on code:
  Copyright 2009 Aurélien Gâteau <agateau@kde.org>

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
  License along with this program.  If not, see <http://www.gnu.org/licenses/>.

*/
#ifndef KSPLITTERCOLLAPSERBUTTON_H
#define KSPLITTERCOLLAPSERBUTTON_H

// Qt
#include <QToolButton>
#include <kwidgetsaddons_export.h>

class QSplitter;

/**
 * @class KSplitterCollapserButton ksplittercollapserbutton.h KSplitterCollapserButton
 *
 * A button which appears on the side of a splitter handle and allows easy
 * collapsing of the widget on the opposite side
 * @since 5.5
 */
class KWIDGETSADDONS_EXPORT KSplitterCollapserButton : public QToolButton
{
    Q_OBJECT
public:
    /**
     * @brief KSplitterCollapserButton create a splitter collapser
     * @param childWidget the widget, child of the splitter, whose size is controlled by this collapser
     * @param splitter the splitter which this collapser should be associated with.
     */
    explicit KSplitterCollapserButton(QWidget *childWidget, QSplitter *splitter);

    /**
      * Destructor
      */
    ~KSplitterCollapserButton() override;

    /**
     * @brief isWidgetCollapsed
     * @return true if splitter is collapsed.
     */
    bool isWidgetCollapsed() const;

    QSize sizeHint() const override;

public Q_SLOTS:
    /**
     * @brief collapse, this function collapses the splitter if splitter is not collapsed.
     */
    void collapse();
    /**
     * @brief restore, call this function to restore previous splitter position.
     */
    void restore();
    /**
     * @brief setCollapsed, this function allows to collapse or not the splitter.
     * @param collapsed if the splitter should be collapsed
     */
    void setCollapsed(bool collapsed);

private Q_SLOTS:
    void slotClicked();

protected:
    bool eventFilter(QObject *, QEvent *) override;
    void paintEvent(QPaintEvent *) override;

    void enterEvent(QEvent *event) override;
    void leaveEvent(QEvent *event) override;
    void showEvent(QShowEvent *event) override;
private:
    class Private;
    Private *const d;
};

#endif /* KSPLITTERCOLLAPSERBUTTON_H */
