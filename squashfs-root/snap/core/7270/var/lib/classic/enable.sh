#! /bin/sh

set -e

rm -f /usr/local/bin/* /etc/apt/sources.list.d/*

tar xf /var/lib/classic/classic-diff.tgz -C /

dpkg -i /var/cache/apt/archives/*.deb
dpkg -i --force-confask --force-confnew /var/cache/apt/archives/base-files*.deb

apt-get clean
apt-get update
