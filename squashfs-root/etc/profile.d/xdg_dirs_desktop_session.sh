# /etc/profile.d/desktop_session_xdg_dirs.sh - Prepend a $DESKTOP_SESSION-named directory to $XDG_CONFIG_DIRS and $XDG_DATA_DIRS

DEFAULT_XDG_CONFIG_DIRS='/etc/xdg'
DEFAULT_XDG_DATA_DIRS='/usr/local/share/:/usr/share/'

if [ -n "$DESKTOP_SESSION" ]; then
  # readd default if was empty
  if [ -z "$XDG_CONFIG_DIRS" ]; then
    XDG_CONFIG_DIRS="$DEFAULT_XDG_CONFIG_DIRS"
  fi
  if [ -n "${XDG_CONFIG_DIRS##*$DEFAULT_XDG_CONFIG_DIRS/xdg-$DESKTOP_SESSION*}" ]; then
    XDG_CONFIG_DIRS="$DEFAULT_XDG_CONFIG_DIRS"/xdg-"$DESKTOP_SESSION":"$XDG_CONFIG_DIRS"
  fi
  export XDG_CONFIG_DIRS
  # gnome is already added if gnome-session installed
  if [ "$DESKTOP_SESSION" != "gnome" ]; then
     if [ -z "$XDG_DATA_DIRS" ]; then
       XDG_DATA_DIRS="$DEFAULT_XDG_DATA_DIRS"
     fi
     if [ -n "${XDG_DATA_DIRS##*/usr/share/$DESKTOP_SESSION*}" ]; then
       XDG_DATA_DIRS=/usr/share/"$DESKTOP_SESSION":"$XDG_DATA_DIRS"
     fi
     export XDG_DATA_DIRS
  fi
fi
