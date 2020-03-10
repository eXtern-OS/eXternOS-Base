/*
   Copyright (C) 2005-2006 by Olivier Goffart <ogoffart at kde.org>

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

#ifndef KNOTIFICATIONPLUGIN_H
#define KNOTIFICATIONPLUGIN_H

#include <QObject>
#include <KPluginFactory>

#include "knotifications_export.h"

class KNotification;
class KNotificationPluginPrivate;
class KNotifyConfig;

/**
 * @class KNotificationPlugin knotificationplugin.h KNotificationPlugin
 *
 * @brief abstract class for KNotification actions
 *
 * A KNotificationPlugin is responsible of notification presentation.
 * You can subclass it to have your own presentation of a notification.
 *
 * You should reimplement the KNotificationPlugin::notify method to display the notification.
 *
 * @author Olivier Goffart <ogoffart at kde.org>
*/
class KNOTIFICATIONS_EXPORT KNotificationPlugin : public QObject
{
    Q_OBJECT

public:
    KNotificationPlugin(QObject *parent = nullptr, const QVariantList &args = QVariantList());
    virtual ~KNotificationPlugin();

    /**
        * @brief return the name of this plugin.
        *
        * this is the name that should appear in the .notifyrc file,
        * in the field Action=... if a notification is set to use this plugin
        */
    virtual QString optionName() = 0;

    // TODO KF6 make notifyConfig const reference
    /**
        * This function is called when the notification is sent.
        * (or re-sent)
        * You should implement this function to display a notification
        *
        * for each call to this function (even for re-notification), you MUST call finish(KNotification*)
        *
        * @param notification is the KNotification object
        * @param notifyConfig is the configuration of the notification
        */
    virtual void notify(KNotification *notification, KNotifyConfig *notifyConfig) = 0;

    // TODO KF6 make config const reference
    /**
        * This function is called when the notification has changed (such as the text or the icon)
        */
    virtual void update(KNotification *notification, KNotifyConfig *config);

    /**
        * This function is called when the notification has been closed
        */
    virtual void close(KNotification *notification);

protected:
    /**
        * emit the finished signal
        * you MUST call this function for each call to notify(), even if you do nothing there
        *
        * call it when the presentation is finished (because the user closed the popup or the sound is finished)
        *
        * If your presentation is synchronous, you can even call this function from the notify() call itself
        */
    void finish(KNotification *notification);

Q_SIGNALS:
    /**
        * the presentation is finished.
        */
    void finished(KNotification *notification);
    /**
        * emit this signal if one action was invoked
        * @param id is the id of the notification
        * @param action is the action number.  zero for the default action
        */
    void actionInvoked(int id , int action);

private:
    KNotificationPluginPrivate *const d;

};

#endif
