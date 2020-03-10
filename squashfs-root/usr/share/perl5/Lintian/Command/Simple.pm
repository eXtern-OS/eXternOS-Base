# Copyright (C) 2010 Raphael Geissert <atomo64@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

package Lintian::Command::Simple;

use strict;
use warnings;

use Exporter qw(import);
use POSIX qw(:sys_wait_h);

our @EXPORT_OK = qw(wait_any kill_all);

=head1 NAME

Lintian::Command::Simple - Run commands without pipes

=head1 SYNOPSIS

    use Lintian::Command::Simple qw(wait_any);

    my %pid_info;
    my $pid = fork() // die("fork: $!");
    exec('do', 'something') if $pid == 0;
    $pid_info{$pid} = "A useful value associated with $pid";

    my ($termiated_pid, $value) = wait_any(\%pid_info);
    ...;

=head1 DESCRIPTION

Lintian::Command::Simple allows running commands with the capability of
running them "in the background" (asynchronously.)

Pipes are not handled at all, except for those handled internally by
the shell. See 'perldoc -f exec's note about shell metacharacters.
If you want to pipe to/from Perl, look at Lintian::Command instead.

=over 4

=item wait_any (hashref[, nohang])

When starting multiple processes asynchronously, it is common to wait
until the first is done. While the CORE::wait() function is usually
used for that very purpose, it does not provide the desired results
when the processes were started via the OO interface.

To help with this task, wait_any() can take a hash ref where the key
of each entry is the pid of that command.  There are no requirements
for the value (which can be used for any application specific
purpose).

Under this mode, wait_any() waits until any child process is done.
The key (and value) associated the pid of the reaped child will then
be removed from the hashref.  The exitcode of the child is available
via C<$?> as usual.

The results and return value are undefined when under this mode
wait_any() "accidentally" reaps a process not listed in the hashref.

The return value in scalar context is value associated with the pid of
the reaped processed.  In list context, the pid and value are returned
as a pair.

Whenever waitpid() would return -1, wait_any() returns undef or a null
value so that it is safe to:

    while($cmd = wait_any(\%hash)) { something; }

The same is true whenever the hash reference points to an empty hash.

If C<nohang> is also given, wait_any will attempt to reap any child
process non-blockingly.  If no child can be reaped, it will
immediately return (like there were no more processes left) instead of
waiting.

=cut

sub wait_any {
    my ($jobs, $nohang) = @_;
    my $reaped_pid;
    my $extra;

    $nohang = WNOHANG if $nohang;
    $nohang //= 0;

    return unless scalar keys %$jobs;

    $reaped_pid = waitpid(-1, $nohang);

    if ($reaped_pid == -1 or ($nohang and $reaped_pid == 0)) {
        return;
    }

    # Did we reap some other pid?
    return unless exists $jobs->{$reaped_pid};

    $extra = delete $jobs->{$reaped_pid};
    return ($reaped_pid, $extra) if wantarray;
    return $extra;
}

=item kill_all(hashref[, signal])

In a similar way to wait_any(), it is possible to pass a hash
reference to kill_all().  It will then kill all of the processes
(default signal being "TERM") followed by a reaping of the processes.
All reaped processes (and their values) will be removed from the set.

Any entries remaining in the hashref are processes that did not
terminate (or did not terminate yet).

=cut

sub kill_all {
    my ($jobs, $signal) = @_;
    my $count = 0;
    my @jobs;

    $signal //= 'TERM';

    foreach my $pid (keys %$jobs) {
        push @jobs, $pid if kill $signal, $pid;
    }

    foreach my $pid (@jobs) {
        if (waitpid($pid, 0) == $pid) {
            $count++;
            delete $jobs->{$pid};
        }
    }

    return scalar @jobs;
}

1;

__END__

=back

=head1 TODO

Provide the necessary methods to modify the environment variables of
the to-be-executed commands.  This would let us drop C<system_env> (from
Lintian::Util) and make C<run> more useful.

=head1 NOTES

Unless specified by prefixing the package name, every reference to a
function/method in this documentation refers to the functions/methods
provided by this package itself.

=head1 CAVEATS

Combining asynchronous jobs (e.g. via Lintian::Command) and calls to
wait_any() can lead to unexpected results.

=head1 AUTHOR

Originally written by Raphael Geissert <atomo64@gmail.com> for Lintian.

=cut

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
