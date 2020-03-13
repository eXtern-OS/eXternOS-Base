#!/bin/sh

# bridge-network-interface - configure a network bridge
#
# This service checks whether a physical network device that has been added
# is one of the ports in a bridge config, and if so, brings up the related
# bridge

set -e

if [ -z "$INTERFACE" ]; then
	echo "missing \$INTERFACE" >&2
	exit 1
fi

#default configuration
BRIDGE_HOTPLUG=no
[ -f /etc/default/bridge-utils ] && . /etc/default/bridge-utils

[ "$BRIDGE_HOTPLUG" = "no" ] && exit 0

. /lib/bridge-utils/bridge-utils.sh

if [ -d /run/network ]; then
   for i in $(ifquery --list --allow auto); do
	ports=$(ifquery $i | sed -n -e's/^bridge[_-]ports: //p')
	for port in $(bridge_parse_ports $ports); do
		case $port in
			$INTERFACE|$INTERFACE.*)
				if [ ! -d /sys/class/net/$port ] &&
				   [ -x /etc/network/if-pre-up.d/vlan ]; then
					IFACE=$port /etc/network/if-pre-up.d/vlan
				fi

				if [ -d /sys/class/net/$port ]; then
					if [ ! -d /sys/class/net/$i ]; then
						brctl addbr $i
					fi
					brctl addif $i $port && ip link set dev $port up
				fi
				break
				;;
		esac
	done
   done
fi
