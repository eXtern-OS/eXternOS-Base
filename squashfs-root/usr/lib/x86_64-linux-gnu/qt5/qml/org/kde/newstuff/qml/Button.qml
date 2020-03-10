/*
 * Copyright (C) 2019 Dan Leinir Turthra Jensen <admin@leinir.dk>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) version 3, or any
 * later version accepted by the membership of KDE e.V. (or its
 * successor approved by the membership of KDE e.V.), which shall
 * act as a proxy defined in Section 6 of version 3 of the license.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

/**
 * @brief A button which when clicked will open a dialog with a NewStuff.Page at the base
 *
 * This component is equivalent to the old Button
 * @see KNewStuff::Button
 * @since 5.63
 */

import QtQuick 2.11
import QtQuick.Controls 2.11 as QtControls

import org.kde.newstuff 1.62 as NewStuff

QtControls.Button {
    id: component

    /*
     * The configuration file is not aliased, because then we end up initialising the
     * KNSCore::Engine immediately the Button is shown, which we want to avoid (as that
     * is effectively a phone-home scenario, and causes internet traffic in situations
     * where it would not seem likely that there should be any).
     * If we want, in the future, to add some status display to Button (such as "there
     * are updates to be had" or somesuch, then we can do this, but until that choice is
     * made, let's not)
     */
    /**
     * The configuration file to use for this button
     */
    property string configFile: ghnsDialog.configFile

    /**
     * Set the text that should appear on the button. Will be set as
     * i18n("Download New %1").
     *
     * @note For the sake of consistency, you should NOT override the text propety, just set this one
     */
    property string downloadNewWhat: i18nc("Used to contruct the button's label (which will become Download New 'this value')", "Stuff")
    text: i18n("Download New %1").arg(downloadNewWhat)

    /**
     * The default view mode of the dialog spawned by this button. This should be
     * set using the NewStuff.Page.ViewMode enum
     * @see NewStuff.Page.ViewMode
     */
    property alias viewMode: ghnsDialog.viewMode

    /**
     * emitted when the Hot New Stuff dialog is about to be shown, usually
     * as a result of the user having click on the button
     */
    signal aboutToShowDialog();

    /**
     * The engine which handles the content in this Button
     */
    property alias engine: ghnsDialog.engine

    /**
     * Contains the entries which have been changed.
     * @note This is cleared when the dialog is shown, so the changed entries are those
     * changed since the dialog was opened most recently (rather than the lifetime
     * of the instance of the Button component)
     */
    property alias changedEntries: ghnsDialog.changedEntries

    /**
     * If this is true (default is false), the button will be shown when the Kiosk settings are such
     * that Get Hot New Stuff is disallowed (and any other time enabled is set to false).
     * Usually you would want to leave this alone, but occasionally you may have a reason to
     * leave a button in place that the user is unable to enable.
     */
    property bool visibleWhenDisabled: false

    /**
     * Show the dialog (same as clicking the button), if allowed by the Kiosk settings
     */
    function showDialog() {
        if (ghnsDialog.engine.allowedByKiosk) {
            ghnsDialog.engine.configFile = component.configFile
            component.aboutToShowDialog();
            ghnsDialog.open();
        } else {
            // make some noise, because silently doing nothing is a bit annoying
        }
    }

    onClicked: { showDialog(); }

    icon.name: "get-hot-new-stuff"
    visible: enabled || visibleWhenDisabled
    enabled: ghnsDialog.engine.allowedByKiosk
    onEnabledChanged: {
        // If the user resets this when kiosk has disallowed ghns, force enabled back to false
        if (enabled === true && ghnsDialog.engine.allowedByKiosk === false) {
            enabled = false;
        }
    }

    NewStuff.Dialog {
        id: ghnsDialog
    }
}
