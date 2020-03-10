# /etc/profile.d/input-method-config.sh
#
# This is a temporary measure which works around
# https://launchpad.net/bugs/1720250

if [ -z "$XDG_CURRENT_DESKTOP" -o -n "$GTK_IM_MODULE" ]; then
    return
fi

. /etc/X11/Xsession.d/70im-config_launch
if [ "$IM_CONFIG_PHASE" = 1 ]; then
    export IM_CONFIG_PHASE=2
    . /usr/share/im-config/xinputrc.common
    if [ -r "$IM_CONFIG_XINPUTRC_USR" ]; then
        . $IM_CONFIG_XINPUTRC_USR
    elif [ -r "$IM_CONFIG_XINPUTRC_SYS" ]; then
        . $IM_CONFIG_XINPUTRC_SYS
    fi
    export XMODIFIERS
    export GTK_IM_MODULE
    export QT_IM_MODULE
    export QT4_IM_MODULE
    export CLUTTER_IM_MODULE
fi
