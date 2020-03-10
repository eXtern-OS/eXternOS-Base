#!/bin/sh

test -f /usr/share/acpi-support/key-constants || exit 0

. /usr/share/acpi-support/state-funcs

if isAnyWirelessPoweredOn; then
    if [ -x /usr/bin/toshset ]; then
        if `toshset -bluetooth | grep -q attached`; then
                toshset -bluetooth off
                toggleAllWirelessStates
        else
                toshset -bluetooth on
        fi
    else
	toggleAllWirelessStates
    fi
else
        toggleAllWirelessStates
fi
