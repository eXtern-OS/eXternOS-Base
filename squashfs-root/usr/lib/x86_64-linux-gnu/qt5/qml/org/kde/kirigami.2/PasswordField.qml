/*
 *   Copyright (C) 2019 Carl-Lucien Schwan <carl@carlschwan.eu>              *
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU Library/Lesser General Public License
 *   version 2, or (at your option) any later version, as published by the
 *   Free Software Foundation
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details
 *
 *   You should have received a copy of the GNU Library/Lesser General Public
 *   License along with this program; if not, write to the
 *   Free Software Foundation, Inc.,
 *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */

import QtQuick 2.6
import QtQuick.Controls 2.1 as Controls
import org.kde.kirigami 2.7 as Kirigami

/**
 * This is a standard password text field.
 *
 * Example usage for the password field component:
 * @code
 * import org.kde.kirigami 2.8 as Kirigami
 *
 * Kirigami.PasswordField {
 *     id: passwordField
 *     onAccepted: // check if passwordField.text is valid
 * }
 * @endcode
 *
 * @inherit org.kde.kirgami.ActionTextField
 */
Kirigami.ActionTextField
{
    id: root

    property bool showPassword: false
    echoMode: root.showPassword ? TextInput.Normal : TextInput.Password
    placeholderText: qsTr("Password")
    rightActions: [
        Kirigami.Action {
            iconName: root.showPassword ? "password-show-off" : "password-show-on"
            onTriggered: root.showPassword = !root.showPassword
        }
    ]
}
