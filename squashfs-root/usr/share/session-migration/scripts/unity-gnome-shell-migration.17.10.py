#!/usr/bin/python3

from gi.repository import Gio
import os
import sys


UNITY_LAUNCHER_SETTINGS = "com.canonical.Unity.Launcher"
UNITY_LAUNCHER_FAVORITE_KEY = "favorites"
UNITY_APP_PREFIX = "application://"

GNOME_DASH_SETTINGS = "org.gnome.shell"
GNOME_DASH_FAVORITE_KEY = "favorite-apps"

UNITY_COMPIZ_LAUNCHER_SETTINGS = "org.compiz.unityshell"
UNITY_COMPIZ_LAUNCHER_SETTINGS_PATH = "/org/compiz/profiles/unity/plugins/unityshell/"

DOCK_SETTINGS = "org.gnome.shell.extensions.dash-to-dock"

def get_default_gnome_shell_favorites():
    settings = Gio.Settings.new(GNOME_DASH_SETTINGS)
    settings.delay()
    settings.reset(GNOME_DASH_FAVORITE_KEY)
    return settings.get_strv(GNOME_DASH_FAVORITE_KEY)


def get_default_launcher_property(property):
    settings = Gio.Settings.new_with_path(UNITY_COMPIZ_LAUNCHER_SETTINGS, UNITY_COMPIZ_LAUNCHER_SETTINGS_PATH)
    settings.delay()
    settings.reset(property)
    return settings.get_int(property)


def migrate_unity_launchers():

    gs_settings = Gio.Settings.new(GNOME_DASH_SETTINGS)
    if not gs_settings.is_writable(GNOME_DASH_FAVORITE_KEY):
        print("Can't migrate unity keys to GNOME Shell as they are not writable")
        return
    gs_favorites = gs_settings.get_strv(GNOME_DASH_FAVORITE_KEY)

    if gs_favorites != get_default_gnome_shell_favorites():
        print("Migration prevented as GNOME Shell launchers are modified from defaults")
        return

    unity_settings = Gio.Settings.new(UNITY_LAUNCHER_SETTINGS)
    unity_favorites = unity_settings.get_strv(UNITY_LAUNCHER_FAVORITE_KEY)

    new_favorites = []
    for fav in unity_favorites:
        if not fav.startswith(UNITY_APP_PREFIX):
            continue
        # change from u-c-c
        if fav == UNITY_APP_PREFIX + "unity-control-center.desktop":
            fav = UNITY_APP_PREFIX + "gnome-control-center.desktop"
        new_favorites.append(fav[len(UNITY_APP_PREFIX):])
    
    # we replace with unity existing keys
    gs_settings.set_strv(GNOME_DASH_FAVORITE_KEY, new_favorites)
    gs_settings.sync() # force sync to avoid race


def migrate_launcher_properties():
    source = Gio.SettingsSchemaSource.get_default()
    if source.lookup(DOCK_SETTINGS, True) is None:
        print("Don't migrate launcher properties as Ubuntu Docker not installed")
        return

    unity_settings = Gio.Settings.new_with_path(UNITY_COMPIZ_LAUNCHER_SETTINGS, UNITY_COMPIZ_LAUNCHER_SETTINGS_PATH)
    dock_settings = Gio.Settings.new(DOCK_SETTINGS)

    intellihide = unity_settings.get_int("launcher-hide-mode")
    if intellihide == 1 and intellihide != get_default_launcher_property("launcher-hide-mode"):
        dock_settings.set_boolean("dock-fixed", False)

    icon_size = unity_settings.get_int("icon-size")
    if icon_size != get_default_launcher_property("icon-size"):
        dock_settings.set_int("dash-max-icon-size", icon_size)
    
    launcher_placement = unity_settings.get_int("num-launchers")
    if launcher_placement != get_default_launcher_property("num-launchers"):
        if launcher_placement == 0:
            dock_settings.set_boolean("multi-monitor", "True")
        else:
            dock_settings.set_int("preferred-monitor", launcher_placement - 1)
    dock_settings.sync() # force sync to avoid race


def reset_rhythmbox_plugins():
    '''We had a glib bug for list plugins, people installing 17.10 beta or before
    were reset to default non override defaults, if this is the case, reset them
    again.
    '''
    source = Gio.SettingsSchemaSource.get_default()
    if (source.lookup("org.gnome.rhythmbox.plugins", True) is None):
        print("Don't reset Rhythmbox key as not installed")
        return
    rh_settings = Gio.Settings.new("org.gnome.rhythmbox.plugins")
    if not rh_settings.is_writable("active-plugins"):
        print("Can't reset Rhythmbox key as not writable")
        return
    # only migrate if default system values were set
    if rh_settings.get_strv("active-plugins") != ['power-manager', 'generic-player', 'android', 'audiocd', 'iradio', 'mmkeys']:
        return
    rh_settings.reset("active-plugins")
    rh_settings.sync()


if __name__ == "__main__":
    source = Gio.SettingsSchemaSource.get_default()
    # Unity or GS not installed
    if (source.lookup(UNITY_LAUNCHER_SETTINGS, True) is None or
        source.lookup(UNITY_COMPIZ_LAUNCHER_SETTINGS, True) is None or
        source.lookup(GNOME_DASH_SETTINGS, True) is None):
        print("Unity or GNOME Shell not installed: no migration needed")
        sys.exit(0)

    migrate_unity_launchers()
    migrate_launcher_properties()
    reset_rhythmbox_plugins()
