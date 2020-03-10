#!/bin/sh

test -f /usr/share/acpi-support/state-funcs || exit 0

# Find and toggle wireless of bluetooth devices on ThinkPads

. /usr/share/acpi-support/state-funcs

rfkill list | sed -n -e'/tpacpi_bluetooth_sw/,/^[0-9]/p' | grep -q 'Soft blocked: yes'
bluetooth_state=$?

# Note that this always alters the state of the wireless!
toggleAllWirelessStates;

# Sequence is Both on, Both off, Wireless only, Bluetooth only
if ! isAnyWirelessPoweredOn; then
    # Wireless was turned off
    if [ "$bluetooth_state" = 0 ]; then
        rfkill unblock bluetooth
    else
        rfkill block bluetooth
    fi
fi
