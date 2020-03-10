/*
 * Copyright (c) 2018 - 2019  Daniel Vrátil <dvratil@kde.org>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License or (at your option) version 3 or any later version
 * accepted by the membership of KDE e.V. (or its successor approved
 * by the membership of KDE e.V.), which shall act as a proxy
 * defined in Section 14 of version 3 of the license.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

.import org.kde.kirigami 2.0 as Kirigami
.import org.kde.bolt 0.1 as Bolt

function deviceStatus(device, withStored)
{
    var status = device.status;
    var str = "";
    var color = Kirigami.Theme.textColor;
    if (status == Bolt.Bolt.Status.Disconnected) {
        str = i18n("Disconnected");
    } else if (status == Bolt.Bolt.Status.Connecting) {
        str = i18n("Connecting");
    } else if (status == Bolt.Bolt.Status.Connected) {
        str = i18n("Connected");
        color = Kirigami.Theme.neutralTextColor;
    } else if (status == Bolt.Bolt.Status.AuthError) {
        str = i18n("Authorization Error");
    } else if (status == Bolt.Bolt.Status.Authorizing) {
        str = i18n("Authorizing");
    } else if (status == Bolt.Bolt.Status.Authorized) {
        color = Kirigami.Theme.positiveTextColor;
        if (device.authFlags & Bolt.Bolt.Auth.NoPCIE) {
            str = i18n("Reduced Functionality");
        } else {
            str = i18n("Connected & Authorized");
        }
    }
    if (withStored && device.stored) {
        if (str != "") {
            str += ", ";
        }
        str += i18n("Trusted");
    }

    return { text: str, color: color };
}
