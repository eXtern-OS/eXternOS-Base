// -*- c++ -*-

/*
 *   Copyright (C) 2001-2006 by Richard Moore <rich@kde.org>
 *   Copyright (C) 2004-2005 by Sascha Cunz <sascha.cunz@tiscali.de>
 *
 *   This library is free software; you can redistribute it and/or
 *   modify it under the terms of the GNU Lesser General Public
 *   License as published by the Free Software Foundation; either
 *   version 2 of the License, or (at your option) any later version.
 *
 *   This library is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *   Lesser General Public License for more details.
 *
 *   You should have received a copy of the GNU Lesser General Public
 *   License along with this library; if not, write to the Free Software
 *   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 */

#ifndef KPASSIVEPOPUP_H
#define KPASSIVEPOPUP_H

#include <knotifications_export.h>

#include <QFrame>

class QSystemTrayIcon;

/**
 * @class KPassivePopup kpassivepopup.h KPassivePopup
 *
 * @short A dialog-like popup that displays messages without interrupting the user.
 *
 * The simplest uses of KPassivePopup are by using the various message() static
 * methods. The position the popup appears at depends on the type of the parent window:
 *
 * @li Normal Windows: The popup is placed adjacent to the icon of the window.
 * @li System Tray Windows: The popup is placed adjacent to the system tray window itself.
 * @li Skip Taskbar Windows: The popup is placed adjacent to the window
 *     itself if it is visible, and at the edge of the desktop otherwise.
 *
 * You also have the option of calling show with a QPoint as a parameter that
 * removes the automatic placing of KPassivePopup and shows it in the point you want.
 *
 * The most basic use of KPassivePopup displays a popup containing a piece of text:
 * \code
 *    KPassivePopup::message( "This is the message", this );
 * \endcode
 * We can create popups with titles and icons too, as this example shows:
 * \code
 *    QPixmap px;
 *    px.load( "hi32-app-logtracker.png" );
 *    KPassivePopup::message( "Some title", "This is the main text", px, this );
 * \endcode
 * This screenshot shows a popup with both a caption and a main text which is
 * being displayed next to the toolbar icon of the window that triggered it:
 * \image html kpassivepopup.png "A passive popup"
 *
 * For more control over the popup, you can use the setView(QWidget *) method
 * to create a custom popup.
 * \code
 *    KPassivePopup *pop = new KPassivePopup( parent );
 *
 *    QWidget* content = new QWidget( pop );
 *    QVBoxLayout* vBox = new QVBoxLayout( content );
 *    QLabel* label = new QLabel( "<b>Isn't this great?</b>", content );
 *    vBox->addWidget( label );
 *
 *    QPushButton* btnYes = new QPushButton( "Yes", content );
 *    QPushButton* btnNo = new QPushButton( "No", content );
 *
 *    QHBoxLayout* hBox = new QHBoxLayout( content );
 *    hBox->addWidget( btnYes );
 *    hBox->addWidget( btnNo );
 *
 *    vBox->addLayout( vBox );
 *
 *    pop->setView( content );
 *    pop->show();
 * \endcode
 *
 * @author Richard Moore, rich@kde.org
 * @author Sascha Cunz, sascha.cunz@tiscali.de
 */
class KNOTIFICATIONS_EXPORT KPassivePopup : public QFrame
{
    Q_OBJECT
    Q_PROPERTY(bool autoDelete READ autoDelete WRITE setAutoDelete)
    Q_PROPERTY(int timeout READ timeout WRITE setTimeout)

public:
    /**
     * Styles that a KPassivePopup can have.
     */
    enum PopupStyle {
        Boxed,             ///< Information will appear in a framed box (default)
        Balloon,           ///< Information will appear in a comic-alike balloon
    };

    /**
     * Creates a popup for the specified widget.
     */
    explicit KPassivePopup(QWidget *parent = nullptr, Qt::WindowFlags f = Qt::WindowFlags());

    /**
     * Creates a popup for the specified window.
     */
    explicit KPassivePopup(WId parent);

    /**
     * Cleans up.
     */
    virtual ~KPassivePopup();

    /**
     * Sets the main view to be the specified widget (which must be a child of the popup).
     */
    void setView(QWidget *child);

    /**
     * Creates a standard view then calls setView(QWidget*) .
     */
    void setView(const QString &caption, const QString &text = QString());

    /**
     * Creates a standard view then calls setView(QWidget*) .
     */
    virtual void setView(const QString &caption, const QString &text, const QPixmap &icon);

    /**
     * Returns a widget that is used as standard view if one of the
     * setView() methods taking the QString arguments is used.
     * You can use the returned widget to customize the passivepopup while
     * keeping the look similar to the "standard" passivepopups.
     *
     * After customizing the widget, pass it to setView( QWidget* )
     *
     * @param caption The window caption (title) on the popup
     * @param text The text for the popup
     * @param icon The icon to use for the popup
     * @param parent The parent widget used for the returned widget. If left 0,
     * then "this", i.e. the passive popup object will be used.
     *
     * @return a QWidget containing the given arguments, looking like the
     * standard passivepopups. The returned widget contains a QVBoxLayout,
     * which is accessible through layout().
     * @see setView( QWidget * )
     * @see setView( const QString&, const QString& )
     * @see setView( const QString&, const QString&, const QPixmap& )
     */
    QWidget *standardView(const QString &caption, const QString &text,
                          const QPixmap &icon, QWidget *parent = nullptr);

    /**
     * Returns the main view.
     */
    QWidget *view() const;

    /**
     * Returns the delay before the popup is removed automatically.
     */
    int timeout() const;

    /**
     * Sets whether the popup will be deleted when it is hidden.
     *
     * The default is false (unless created by one of the static
     * message() overloads).
     */
    virtual void setAutoDelete(bool autoDelete);

    /**
     * Returns whether the popup will be deleted when it is hidden.
     *
     * @see setAutoDelete
     */
    bool autoDelete() const;

    /**
     * Returns the position to which this popup is anchored.
     */
    QPoint anchor() const;

    /**
     * Sets the anchor of this popup.
     *
     * The popup is placed near to the anchor.
     */
    void setAnchor(const QPoint &anchor);

    /**
     * Convenience method that displays popup with the specified  message  beside the
     * icon of the specified widget.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(const QString &text, QWidget *parent,
                                  const QPoint &p = QPoint());

    /**
     * Convenience method that displays popup with the specified  message  beside the
     * icon of the specified QSystemTrayIcon.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(const QString &text, QSystemTrayIcon *parent);

    /**
     * Convenience method that displays popup with the specified caption and message
     * beside the icon of the specified widget.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(const QString &caption, const QString &text,
                                  QWidget *parent, const QPoint &p = QPoint());

    /**
     * Convenience method that displays popup with the specified caption and message
     * beside the icon of the specified QSystemTrayIcon.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(const QString &caption, const QString &text,
                                  QSystemTrayIcon *parent);

    /**
     * Convenience method that displays popup with the specified icon, caption and
     * message beside the icon of the specified widget.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(const QString &caption, const QString &text,
                                  const QPixmap &icon, QWidget *parent, int timeout = -1,
                                  const QPoint &p = QPoint());

    /**
     * Convenience method that displays popup with the specified icon, caption and
     * message beside the icon of the specified QSystemTrayIcon.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(const QString &caption, const QString &text,
                                  const QPixmap &icon, QSystemTrayIcon *parent, int timeout = -1);

    /**
     * Convenience method that displays popup with the specified icon, caption and
     * message beside the icon of the specified window.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(const QString &caption, const QString &text,
                                  const QPixmap &icon, WId parent,
                                  int timeout = -1, const QPoint &p = QPoint());

    /**
     * Convenience method that displays popup with the specified popup-style and message beside the
     * icon of the specified widget.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(int popupStyle, const QString &text, QWidget *parent, const QPoint &p = QPoint());

    /**
     * Convenience method that displays popup with the specified popup-style and message beside the
     * icon of the specified QSystemTrayIcon.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(int popupStyle, const QString &text, QSystemTrayIcon *parent);

    /**
     * Convenience method that displays popup with the specified popup-style, caption and message
     * beside the icon of the specified QSystemTrayIcon.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(int popupStyle, const QString &caption, const QString &text,
                                  QSystemTrayIcon *parent);

    /**
     * Convenience method that displays popup with the specified popup-style, caption and message
     * beside the icon of the specified widget.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(int popupStyle, const QString &caption, const QString &text,
                                  QWidget *parent, const QPoint &p = QPoint());

    /**
     * Convenience method that displays popup with the specified popup-style, icon, caption and
     * message beside the icon of the specified widget.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(int popupStyle, const QString &caption, const QString &text,
                                  const QPixmap &icon, QWidget *parent, int timeout = -1,
                                  const QPoint &p = QPoint());

    /**
     * Convenience method that displays popup with the specified popup-style, icon, caption and
     * message beside the icon of the specified QSystemTrayIcon.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(int popupStyle, const QString &caption, const QString &text,
                                  const QPixmap &icon, QSystemTrayIcon *parent, int timeout = -1);

    /**
     * Convenience method that displays popup with the specified popup-style, icon, caption and
     * message beside the icon of the specified window.
     * Note that the returned object is destroyed when it is hidden.
     * @see setAutoDelete
     */
    static KPassivePopup *message(int popupStyle, const QString &caption, const QString &text,
                                  const QPixmap &icon, WId parent, int timeout = -1,
                                  const QPoint &p = QPoint());

    // we create an overloaded version of show()
    using QFrame::show;

public Q_SLOTS:
    /**
     * Sets the delay for the popup is removed automatically. Setting the delay to 0
     * disables the timeout, if you're doing this, you may want to connect the
     * clicked() signal to the hide() slot.
     * Setting the delay to -1 makes it use the default value.
     *
     * @see timeout
     */
    void setTimeout(int delay);

    /**
     * Sets the visual appearance of the popup.
     * @see PopupStyle
     */
    void setPopupStyle(int popupstyle);

    /**
     * Shows the popup in the given point
     */
    void show(const QPoint &p);

    /** @reimp */
    void setVisible(bool visible) override;

Q_SIGNALS:
    /**
     * Emitted when the popup is clicked.
     */
    void clicked();

    /**
     * Emitted when the popup is clicked.
     */
    void clicked(const QPoint &pos);

protected:
    /**
     * Positions the popup.
     *
     * The default implementation attempts to place it by the taskbar
     * entry; failing that it places it by the window of the associated
     * widget; failing that it places it at the location given by
     * defaultLocation().
     *
     * @see moveNear()
     */
    virtual void positionSelf();

    /**
     * Returns a default location for popups when a better placement
     * cannot be found.
     *
     * The default implementation returns the top-left corner of the
     * available work area of the desktop (ie: minus panels, etc).
     */
    virtual QPoint defaultLocation() const;

    /**
     * Moves the popup to be adjacent to @p target.
     *
     * The popup will be placed adjacent to, but outside of, @p target,
     * without going off the current desktop.
     *
     * Reimplementations of positionSelf() can use this to actually
     * position the popup.
     */
    void moveNear(const QRect &target);

    /** @reimp */
    void hideEvent(QHideEvent *) override;

    /** @reimp */
    void mouseReleaseEvent(QMouseEvent *e) override;

    /** @reimp */
    void paintEvent(QPaintEvent *pe) override;

private:
    /* @internal */
    class Private;
    Private *const d;
};

#endif // KPASSIVEPOPUP_H

// Local Variables:
// End:

