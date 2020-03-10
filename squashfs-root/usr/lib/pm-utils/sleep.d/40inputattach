#!/bin/bash
#								-*-shell-script-*-
# /usr/lib/pm-utils/sleep.d/40inputattach
# Action script to restart Wacom serial tablet inputs

. "${PM_FUNCTIONS}"

# Unique key name for saving/restoring state
STATE=inputattach

get_devs() {
    # Scrape command line(s) of any running `inputattach` daemons
    ps -C inputattach -o args=
}

run_inputattach() {
    # Run commands as they come in from the saved state
    while read CMD; do
	$CMD
    done
}

case "$1" in
    suspend|hibernate)
	# Save any Wacom W8001 devices
	get_devs | savestate $STATE
	;;
    resume|thaw)
	if state_exists $STATE; then
	    restorestate $STATE | run_inputattach
	fi
	;;
esac

exit 0
