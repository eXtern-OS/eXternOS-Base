#!/bin/bash
TARGET="intel_backlight"
cd /sys/class/backlight
MAX="$(cat "${TARGET}/max_brightness")"
# The `/1` at the end forced bc to cast the result 
# to an integer, even if $1 is a float (which it 
# should be)
LOGIC="$(echo "($1 * ${MAX})/1" | bc)"
for i in */; do
    if [[ "${TARGET}/" != "$i" && -e "${i}brightness" ]]; then
        cat "${i}max_brightness" > "${i}brightness"
    fi
done
echo "$LOGIC" > "${TARGET}/brightness"
