dpkg-divert --local --rename --add /sbin/initctl
rm -f /sbin/initctl
dpkg-divert --rename --remove /sbin/initctl
exit
