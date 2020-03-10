/*
    Copyright 2015 David Rosca <nowrep@gmail.com>

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

import QtQuick 2.2
import QtQuick.Layouts 1.1
import org.kde.bluezqt 1.0 as BluezQt
import org.kde.plasma.components 2.0 as PlasmaComponents

ColumnLayout {
    id: mediaPlayer

    spacing: 0

    PlasmaComponents.Label {
        id: trackTitleLabel
        Layout.fillWidth: true
        elide: Text.ElideRight
        font.weight: MediaPlayer && MediaPlayer.track.title ? Font.DemiBold : Font.Normal
        font.italic: MediaPlayer && MediaPlayer.status == BluezQt.MediaPlayer.Playing
        font.pointSize: theme.smallestFont.pointSize
        opacity: 0.6
        text: trackTitleText()
        textFormat: Text.PlainText
        visible: text.length
    }

    PlasmaComponents.Label {
        id: trackArtistLabel
        Layout.fillWidth: true
        elide: Text.ElideRight
        font.pointSize: theme.smallestFont.pointSize
        opacity: 0.6
        text: MediaPlayer ? MediaPlayer.track.artist : ""
        textFormat: Text.PlainText
        visible: text.length
    }

    PlasmaComponents.Label {
        id: trackAlbumLabel
        Layout.fillWidth: true
        elide: Text.ElideRight
        font.pointSize: theme.smallestFont.pointSize
        opacity: 0.6
        text: MediaPlayer ? MediaPlayer.track.album : ""
        textFormat: Text.PlainText
        visible: text.length
    }

    RowLayout {
        spacing: 0

        PlasmaComponents.ToolButton {
            id: previousButton
            iconSource: "media-skip-backward"

            onClicked: MediaPlayer.previous()
        }

        PlasmaComponents.ToolButton {
            id: playPauseButton
            iconSource: playPauseButtonIcon()

            onClicked: playPauseButtonClicked()
        }

        PlasmaComponents.ToolButton {
            id: stopButton
            iconSource: "media-playback-stop"
            enabled: MediaPlayer && MediaPlayer.status != BluezQt.MediaPlayer.Stopped

            onClicked: MediaPlayer.stop()
        }

        PlasmaComponents.ToolButton {
            id: nextButton
            iconSource: "media-skip-forward"

            onClicked: MediaPlayer.next()
        }
    }

    function trackTitleText()
    {
        if (!MediaPlayer) {
            return "";
        }

        var play = "\u25B6";

        if (MediaPlayer.status == BluezQt.MediaPlayer.Playing) {
            return "%1 %2".arg(play).arg(MediaPlayer.track.title);
        }
        return MediaPlayer.track.title;
    }

    function playPauseButtonIcon()
    {
        if (!MediaPlayer) {
            return "";
        }

        if (MediaPlayer.status != BluezQt.MediaPlayer.Playing) {
            return "media-playback-start";
        } else {
            return "media-playback-pause";
        }
    }

    function playPauseButtonClicked()
    {
        if (MediaPlayer.status != BluezQt.MediaPlayer.Playing) {
            MediaPlayer.play()
        } else {
            MediaPlayer.pause()
        }
    }
}
