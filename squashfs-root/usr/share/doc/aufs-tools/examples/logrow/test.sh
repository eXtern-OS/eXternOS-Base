#!/bin/sh

# Copyright (C) 2005-2010 Junjiro R. Okajima
#
# This program, aufs is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# $Id: test.sh,v 1.3 2009/01/26 06:24:45 sfjro Exp $

tmp=/tmp/$$
img=$tmp.img
dir=$tmp.xfs

set -eux
dd if=/dev/null of=$img bs=1k seek=16k
mkfs -t xfs -q -b size=1024 -f $img
mkdir -p $dir
#sudo mount -vo loop $img $dir
dev=$(sudo mount -vo loop $img $dir |
	tail -n 1 |
	sed -e 's:^.*loop=\(/dev/loop[/0-9]*\).*$:\1:')
test $(sudo ./logrow $dev) -eq $((16*1024*1024))
df $dir
sudo chmod a+w $dir

echo abc > $dir/a
mkdir $dir/b
ln $dir/a $dir/b/c

sz=$((32*1024*1024))
sudo strace ./logrow -s $sz $dev $img
test $(sudo ./logrow $dev) -eq $sz
sudo xfs_growfs $dir
df $dir

for i in a b/c
do echo abc | diff -u - $dir/$i
done
dd if=/dev/zero bs=1M of=$dir/full && false
ls -l $dir/full

sudo umount $dir
rm -fr $tmp $tmp.*