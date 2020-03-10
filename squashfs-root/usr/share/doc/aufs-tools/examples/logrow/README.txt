
Logrow -- expand the size of the mounted loopback block device
J. R. Okajima

Some of the linux filesystems can grow its size with being mounted by a
special tool. For example, the patched EXT2 and the native XFS.
While the filesystem supports growing its size, the loopback block
device doesn't. The logrow patch which was merged into linux-2.6.30, and
a utility logrow.c, expands the size of the loopback device.
If you specify its backend file, then the utility expands it too.
You don't have to unmount it.

It may be useful for aufs users who wants to use the loopback as a
writable branch.

- use linux-2.6.30 and later
- make the logrow executable
  you should make sure that the header file include path points to your
  kernel tree.
- read test.sh
- and you will know how to use it


Enjoy!
