//  -*- c-basic-offset:4; indent-tabs-mode:nil -*-
/* This file is part of the KDE libraries
   Copyright (C) 2000, 2006 David Faure <faure@kde.org>

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
#ifndef __kbookmarkmanager_h
#define __kbookmarkmanager_h

#include <QString>
#include <QObject>
#include <QDomDocument>
class KBookmarkManagerPrivate;

#include "kbookmark.h"
#include "kbookmarkowner.h" // for SC reasons

class KBookmarkGroup;
class QDBusMessage;

class KBookmarkDialog;

/**
 * This class implements the reading/writing of bookmarks in XML.
 * The bookmarks file is read and written using the XBEL standard
 * (http://pyxml.sourceforge.net/topics/xbel/)
 *
 * A sample file looks like this :
 * \code
 * <xbel>
 *   <bookmark href="http://techbase.kde.org"><title>Developer Web Site</title></bookmark>
 *   <folder folded="no">
 *     <title>Title of this folder</title>
 *     <bookmark icon="kde" href="http://www.kde.org"><title>KDE Web Site</title></bookmark>
 *     <folder toolbar="yes">
 *       <title>My own bookmarks</title>
 *       <bookmark href="http://www.koffice.org"><title>KOffice Web Site</title></bookmark>
 *       <separator/>
 *       <bookmark href="http://www.kdevelop.org"><title>KDevelop Web Site</title></bookmark>
 *     </folder>
 *   </folder>
 * </xbel>
 * \endcode
 */
class KBOOKMARKS_EXPORT KBookmarkManager : public QObject
{
    Q_OBJECT
private:
    /**
     * Creates a bookmark manager with a path to the bookmarks.  By
     * default, it will use the KDE standard dirs to find and create the
     * correct location.  If you are using your own app-specific
     * bookmarks directory, you must instantiate this class with your
     * own path <em>before</em> KBookmarkManager::managerForFile() is ever
     * called.
     *
     * @param bookmarksFile full path to the bookmarks file,
     * Use ~/.kde/share/apps/konqueror/bookmarks.xml for the konqueror bookmarks
     *
     * @param dbusObjectName a unique name that represents this bookmark collection,
     * usually your component (e.g. application) name. This is "konqueror" for the
     * konqueror bookmarks, "kfile" for KFileDialog bookmarks, etc.
     * The final D-Bus object path is /KBookmarkManager/dbusObjectName
     * An empty @p dbusObjectName disables the registration to D-Bus (used for temporary managers)
     */
    KBookmarkManager(const QString &bookmarksFile, const QString &dbusObjectName);

    /**
     * Creates a bookmark manager for an external file
     * (Using QFileSystemWatcher for change monitoring)
     * @since 4.1
     */
    KBookmarkManager(const QString &bookmarksFile);

    /**
     * Creates a temp bookmark manager
     */
    KBookmarkManager();

public:
    /**
     * Destructor
     */
    ~KBookmarkManager();

    /**
     * Check whether auto error handling is enabled.
     * If enabled, it will show an error dialog to the user when an
     * error occurs. It is turned on by default.
     * @return true if auto error handling is enabled, false otherwise
     * @note dialogs will only be displayed if the current thread is the gui thread
     * @since 4.6
     * @see setAutoErrorHandlingEnabled()
     */
    bool autoErrorHandlingEnabled() const;

    /**
    * Enable or disable auto error handling is enabled.
    * If enabled, it will show an error dialog to the user when an
    * error occurs. It is turned on by default.
    * If disabled, the application should react on the error() signal.
    * @param enable true to enable auto error handling, false to disable
    * @param parent the parent widget for the error dialogs, can be @c nullptr for
    *               top-level
    * @since 4.6
    * @see autoErrorHandlingEnabled()
    */
    void setAutoErrorHandlingEnabled(bool enable, QWidget *parent);

    /**
     * Set the update flag. Defaults to true.
     * @param update if true then KBookmarkManager will listen to D-Bus update requests.
     */
    void setUpdate(bool update);

    /**
     * Save the bookmarks to the given XML file on disk.
     * @param filename full path to the desired bookmarks file location
     * @param toolbarCache iff true save a cache of the toolbar folder, too
     * @return true if saving was successful
     */
    // KF6 TODO: Use an enum and not a bool
    bool saveAs(const QString &filename, bool toolbarCache = true) const;

    /**
     * Update access time stamps for a given url.
     * @param url the viewed url
     * @return true if any metadata was modified (bookmarks file is not saved automatically)
     */
    bool updateAccessMetadata(const QString &url);

    /*
     * NB. currently *unimplemented*
     *
     * Update favicon url for a given url.
     * @param url the viewed url
     * @param faviconurl the favicion url
     */
    void updateFavicon(const QString &url, const QString &faviconurl);

    /**
     * This will return the path that this manager is using to read
     * the bookmarks.
     * @internal
     * @return the path containing the bookmarks
     */
    QString path() const;

    /**
     * This will return the root bookmark.  It is used to iterate
     * through the bookmarks manually.  It is mostly used internally.
     *
     * @return the root (top-level) bookmark
     */
    KBookmarkGroup root() const;

    /**
     * This returns the root of the toolbar menu.
     * In the XML, this is the group with the attribute toolbar=yes
     *
     * @return the toolbar group
     */
    KBookmarkGroup toolbar();

    /**
     * @return the bookmark designated by @p address
     * @param address the address belonging to the bookmark you're looking for
     * @param tolerate when true tries to find the most tolerable bookmark position
     * @see KBookmark::address
     */
    KBookmark findByAddress(const QString &address);

    /**
     * Saves the bookmark file and notifies everyone.
     *
     **/
    void emitChanged();

    /**
     * Saves the bookmark file and notifies everyone.
     * @param group the parent of all changed bookmarks
     */
    void emitChanged(const KBookmarkGroup &group);

    /**
     * Save the bookmarks to an XML file on disk.
     * You should use emitChanged() instead of this function, it saves
     * and notifies everyone that the file has changed.
     * Only use this if you don't want the emitChanged signal.
     * @param toolbarCache iff true save a cache of the toolbar folder, too
     * @return true if saving was successful
     */
    // KF6 TODO: Use an enum and not a bool
    bool save(bool toolbarCache = true) const;

    void emitConfigChanged();

    /**
     * Set options with which slotEditBookmarks called keditbookmarks
     * this can be used to change the appearance of the keditbookmarks
     * in order to provide a slightly differing outer shell depending
     * on the bookmarks file / app which calls it.
     * @param caption the --caption string, for instance "Konsole"
     * @param browser iff false display no browser specific
     *            menu items in keditbookmarks :: --nobrowser
     */
    // KF6 TODO: Use an enum and not a bool
    void setEditorOptions(const QString &caption, bool browser);

    /**
     * This static function will return an instance of the
     * KBookmarkManager, responsible for the given @p bookmarksFile.
     * If you do not instantiate this class either
     * natively or in a derived class, then it will return an object
     * with the default behaviors.  If you wish to use different
     * behaviors, you <em>must</em> derive your own class and
     * instantiate it before this method is ever called.
     *
     * @param bookmarksFile full path to the bookmarks file,
     * Use ~/.kde/share/apps/konqueror/bookmarks.xml for the konqueror bookmarks
     *
     * @param dbusObjectName a unique name that represents this bookmark collection,
     * usually your component (e.g. application) name. This is "konqueror" for the
     * konqueror bookmarks, "kfile" for KFileDialog bookmarks, etc.
     * The final D-Bus object path is /KBookmarkManager/dbusObjectName
     * An empty @p dbusObjectName disables the registration to D-Bus (used for temporary managers)
     *
     */
    static KBookmarkManager *managerForFile(const QString &bookmarksFile,
                                            const QString &dbusObjectName);

    /**
     * Returns a KBookmarkManager, which will use QFileSystemWatcher for change detection
     * This is important when sharing bookmarks with other Desktops.
     * @param bookmarksFile full path to the bookmarks file
     * @since 4.1
     */
    static KBookmarkManager *managerForExternalFile(const QString &bookmarksFile);

    /**
     * only used for KBookmarkBar
     */
    static KBookmarkManager *createTempManager();

    /**
     * Returns a pointer to the user's main (konqueror) bookmark collection.
     */
    static KBookmarkManager *userBookmarksManager();

    /**
     * @internal
     */
    QDomDocument internalDocument() const;

public Q_SLOTS:
    void slotEditBookmarks();
    void slotEditBookmarksAtAddress(const QString &address);

    /**
     * Reparse the whole bookmarks file and notify about the change
     * Doesn't send signal over D-Bus to the other Bookmark Managers
     * You probably want to use emitChanged()
     *
     */
    void notifyCompleteChange(const QString &caller);

#ifndef KBOOKMARKS_NO_DBUS
    /**
     * Emit the changed signal for the group whose address is given
     * @see KBookmark::address()
     * Called by the process that saved the file after
     * a small change (new bookmark or new folder).
     * Does not send signal over D-Bus to the other Bookmark Managers
     * You probably want to call emitChanged()
     */
    void notifyChanged(const QString &groupAddress, const QDBusMessage &msg);
#endif

    void notifyConfigChanged();

Q_SIGNALS:
    /**
     * Signal send over D-Bus
     */
    void bookmarkCompleteChange(QString caller);

    /**
     * Signal send over D-Bus
     */
    void bookmarksChanged(QString groupAddress);

    /**
     * Signal send over D-Bus
     */
    void bookmarkConfigChanged();

    /**
     * Signals that the group (or any of its children) with the address
     * @p groupAddress (e.g. "/4/5")
     * has been modified by the caller @p caller.
     * connect to this
     */
    void changed(const QString &groupAddress, const QString &caller);

    /**
     * Signals that the config changed
     */
    void configChanged();

    /**
     * Emitted when an error occurs.
     * Contains the translated error message.
     * @since 4.6
     */
    void error(const QString &errorMessage);

private Q_SLOTS:
    void slotFileChanged(const QString &path); // external bookmarks

private:
    // consts added to avoid a copy-and-paste of internalDocument
    void parse() const;
    void init(const QString &dbusPath);

    void startKEditBookmarks(const QStringList &args);

    KBookmarkManagerPrivate *const d;

    friend class KBookmarkGroup;
};

#endif

