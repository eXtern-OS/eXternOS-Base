#!/usr/bin/perl -w

# The following example code uses IPC::System::Simple to mount
# a /mnt/backup directory, run an rsync command, and then unmount
# the directory again.

use strict;
use IPC::System::Simple qw(run capture);
use POSIX qw(nice strftime);
use Fatal qw(open close nice);
use constant NICE_VALUE => 10;

die "Must be root" if $> != 0;

nice(NICE_VALUE);

my $mounted = 0;
my $today   = strftime('%Y-%m-%d',localtime);

# The capture() from IPC::System::Simple either works, or dies.
my $machine_name = capture("hostname");

open(my $mtab_fh, '<', '/etc/mtab');

while (<$mtab_fh>) {
	if (m{/mnt/backup}) {
		$mounted = 1;
		last;
	}
}

close($mtab_fh);

if (not $mounted) { 
	# Our run() from IPC::System::Simple either works, or dies.
	run(qw(/bin/mount /mnt/backup));
}

my $last_backup = '';

foreach my $dir ( glob("/mnt/backup/$machine_name/*") ) {

	next if not -d $dir;

	# 'gt' is correct here, since we're delaing with YYYY-MM-DD
	if ($dir gt $last_backup) {
		$last_backup = $dir;
	}
}

die "Cannot find last backup" unless $last_backup;

#  0 - Successful backup
# 24 - Files disappeared during backup.  This is expected on
#      an active filesystem, and not considered an error.

run([0,24],
	qw(/usr/bin/rsync -aH --exclude-from=/etc/rsync-ignore), 
	"--link-dest=$last_backup","/",
	"/mnt/backup/teddybear/$today",
);

# Unmount our filesystem if we found it unmounted to begin with.
# Again, run() either succeeds, or dies.

if (not $mounted) {
	run(qw(/bin/umount /mnt/backup));
}
