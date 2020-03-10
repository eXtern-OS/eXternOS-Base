
A sample script to build a chroot-ed/jail environment for internet
service.
Junjiro R. Okajima

o Introduction
Some internet services such as HTTP, DNS server, often run in a jail
environment which is a separated and chroot-ed directory hierarchy for
such service only.
The system administrators generally build the directory hierarchy and
copy some necessary files into it such like binaries, libraries,
devices and configuration files.
Thus, it is also often that he forgets updating those files after
upgrading the system packages or configurations.
This sample script addresses this problem.


o Using AUFS
This sample script can share all of system directory hierarchy with
using aufs. It builds a separated directory with a writable empty
directory and the system directory which is marked as readonly in this
environment.
For example, when you mount aufs with

	"writable empty temporary directory"
	over
	"root directory with marked as readonly"

then you will get a modifiable new root directory with no harm to the
original root directory. All of the modification goes to the new jail
environment only.
It must be effective and suitable for a chroot-ed environment for any
internet services.

If you have your /usr or /var in separated disk partitions, you need
to mount aufs for each partitions. See the sample script.

Note: Generally you don't need to stack over kernel virtual filesystems
such as /proc or /sys. To stack over those filesystems has no meaning
and aufs doesn't support it.

o the sample script
The 'auroot' is very easy and simple script, and you can customize
it for your purpose.
Currently, it mounts 4 aufs under the given directory, which are root,
/dev, /var and /usr, since they exist on the separated disk partitions
on my test system. And then, modifies etc/default/apache2, invokes
chroot and executes the given command.
For example, when you execute
	"sudo auroot /tmp/jail /etc/init.d/apache2 start"
the script will mount,
	/tmp/jail = <temp dir for root> + /
	/tmp/jail/dev = <temp dir for dev> + /dev
	/tmp/jail/var = <temp dir for var> + /var
	/tmp/jail/usr = <temp dir for usr> + /usr
and execute,
	"chroot /tmp/jail /etc/init.d/apache2 start"

Any modification under /tmp/jail will go to <temp dir for root>, and
the original system files will never be modified.


Enjoy!
