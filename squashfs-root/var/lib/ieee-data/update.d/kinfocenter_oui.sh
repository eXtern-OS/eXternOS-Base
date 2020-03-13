#!/bin/sh

dirname="$1"
filename="$2"

if [ "oui.txt" != $(basename "$filename") ]; then
    # Not for us
    exit 0
fi

awk '
/base 16/ {
    if (NF>3) {
        s=$1;
        for (i=4; i<=NF; i++) s=s " " $i;
        print s;
    }
}' $filename > $dirname/kinfocenter_oui.db
