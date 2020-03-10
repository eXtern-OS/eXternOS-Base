#!/bin/sh

# this directory is a symlink on my machine:
KEYS_DIR=/sys/class/leds/asus\:\:kbd_backlight

test -d $KEYS_DIR || exit 0

MIN=0
MAX=$(cat $KEYS_DIR/max_brightness)
VAL=$(cat $KEYS_DIR/brightness)

if [ "$1" = down ]; then
	VAL=$((VAL-1))
else
	VAL=$((VAL+1))
fi

if [ "$VAL" -lt $MIN ]; then
	VAL=$MIN
elif [ "$VAL" -gt $MAX ]; then
	VAL=$MAX
fi

echo $VAL > $KEYS_DIR/brightness
