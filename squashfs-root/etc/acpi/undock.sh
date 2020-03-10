#!/bin/sh

test -f /usr/share/acpi-support/key-constants || exit 0

for device in /sys/devices/platform/dock.*; do
	[ -e "$device/type" ] || continue
	[ x$(cat "$device/type") = xdock_station ] || continue
	echo 1 > "$device/undock"
done
