#! /bin/sh
set -e

# A fake /lib/brltty/brltty.sh for the initramfs. Rather than actually
# starting brltty (which is problematic because brltty would have to be shut
# down and restarted when switching out of early userspace), we just write
# out a brltty.conf which will be copied over to the real root filesystem
# later.

brailleDriver=auto
brailleDevice=usb:

while [ "$1" ]; do
	case $1 in
		-b)
			brailleDriver="$2"
			shift 2
			;;
		-d)
			brailleDevice="$2"
			shift 2
			;;
		-*)
			shift 2
			;;
		*)
			shift
			;;
	esac
done

cat >/dev/.initramfs/brltty.conf <<EOF
# Created by $0
braille-driver $brailleDriver
braille-device $brailleDevice
EOF

exit 0
