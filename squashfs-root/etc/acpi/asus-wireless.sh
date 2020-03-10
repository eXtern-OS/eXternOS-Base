#!/bin/sh
# Find and toggle wireless devices on Asus laptops

test -f /usr/share/acpi-support/state-funcs || exit 0

. /usr/share/acpi-support/state-funcs

toggleAllWirelessStates
