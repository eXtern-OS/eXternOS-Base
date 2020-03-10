# Copyright © 2008 Frank Lichtenheld <frank@lichtenheld.de>
#
# This program is free software; you can redistribute it and/or modify
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
# along with this program.  If not, you can find it on the World Wide
# Web at http://www.gnu.org/copyleft/gpl.html, or write to the Free
# Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston,
# MA 02110-1301, USA.

package Lintian::Command;
use strict;
use warnings;

use Carp qw(croak);

BEGIN {
    # Disabling IPC::Run::Debug saves tons of useless calls.
    $ENV{'IPCRUNDEBUG'} = 'none'
      unless exists $ENV{'IPCRUNDEBUG'};
}

use Exporter qw(import);
our @EXPORT_OK = qw(spawn reap kill safe_qx);

use IPC::Run qw(harness kill_kill);

=head1 NAME

Lintian::Command - Utilities to execute other commands from lintian code

=head1 SYNOPSIS

    use Lintian::Command qw(spawn);

    # simplest possible call
    my $success = spawn({}, ['command']);

    # catch output
    my $opts = {};
    $success = spawn($opts, ['command']);
    if ($success) {
        print "STDOUT: $opts->{out}\n";
        print "STDERR: $opts->{err}\n";
    }

    # from file to file
    $opts = { in => 'infile.txt', out => 'outfile.txt' };
    $success = spawn($opts, ['command']);

    # piping
    $success = spawn({}, ['command'], "|", ['othercommand']);

=head1 DESCRIPTION

Lintian::Command is a thin wrapper around IPC::Run, that catches exception
and implements a useful default behaviour for input and output redirection.

Lintian::Command provides a function spawn() which is a wrapper
around IPC::Run::run() resp. IPC::Run::start() (depending on whether a
pipe is requested).  To wait for finished child processes, it also
provides the reap() function as a wrapper around IPC::Run::finish().

=head2 C<spawn($opts, @cmds)>

The @cmds array is given to IPC::Run::run() (or ::start()) unaltered, but
should only be used for commands and piping symbols (i.e. all of the elements
should be either an array reference, a code reference, '|', or '&').  I/O
redirection is handled via the $opts hash reference. If you need more fine
grained control than that, you should just use IPC::Run directly.

$opts is a hash reference which can be used to set options and to retrieve
the status and output of the command executed.

The following hash keys can be set to alter the behaviour of spawn():

=over 4

=item in

STDIN for the first forked child.  Defaults to C<\undef>.

CAVEAT: Due to #301774, passing a SCALAR ref as STDIN for the child
leaks memory.  The leak is plugged for the C<\undef> case in spawn,
but other scalar refs may still be leaked.

=item pipe_in

Use a pipe for STDIN and start the process in the background.
You will need to close the pipe after use and call $opts->{harness}->finish
in order for the started process to end properly.

=item out

STDOUT of the last forked child.  Will be set to a newly created
scalar reference by default which can be used to retrieve the output
after the call.

Can be '&N' (e.g. &2) to redirect it to (numeric) file descriptor.

=item out_append

STDOUT of all forked children, cannot be used with out and should only be
used with files.  Unlike out, this appends the output to the file
instead of truncating the file.

=item pipe_out

Use a pipe for STDOUT and start the process in the background.
You will need to call $opts->{harness}->finish in order for the started
process to end properly.

=item err

STDERR of all forked children.  Defaults to STDERR of the parent.

Can be '&N' (e.g. &1) to redirect it to (numeric) file descriptor.

=item err_append

STDERR of all forked children, cannot be used with err and should only be
used with files.  Unlike err, this appends the output to the file
instead of truncating the file.

=item pipe_err

Use a pipe for STDERR and start the process in the background.
You will need to call $opts->{harness}->finish in order for the started
process to end properly.

=item fail

Configures the behaviour in case of errors. The default is 'exception',
which will cause spawn() to die in case of exceptions thrown by IPC::Run.
If set to 'error' instead, it will also die if the command exits
with a non-zero error code.  If exceptions should be handled by the caller,
setting it to 'never' will cause it to store the exception in the
C<exception> key instead.

=item child_before_exec

Run the given subroutine in each of the children before they run
"exec".

This is passed to L<IPC::Run/harness> as the I<init> keyword.

=back

The following additional keys will be set during the execution of spawn():

=over 4

=item harness

Will contain the IPC::Run object used for the call which can be used to
query the exit values of the forked programs (E.g. with results() and
full_results()) and to wait for processes started in the background.

=item exception

If an exception is raised during the execution of the commands,
and if C<fail> is set to 'never', the exception will be caught and
stored under this key.

=item success

Will contain the return value of spawn().

=back

=cut

sub spawn {
    my ($opts, @cmds) = @_;

    if (ref($opts) ne 'HASH') {
        $opts = {};
    }
    $opts->{fail} ||= 'exception';

    my ($out, $background);
    my (@out, @in, @err, @kwargs);
    if ($opts->{pipe_in}) {
        @in = ('<pipe', $opts->{pipe_in});
        $background = 1;
    } else {
        # ("<", \$ref) leaks memory, but ("<&-") doesn't (see #301774)
        #
        # We plug the \undef case here because it has a trivial work
        # around and it is the default value.
        my $in = $opts->{in};
        if (not defined $in or (ref $in eq 'SCALAR' and not defined $$in)) {
            @in = ('<&-');
        } else {
            @in = ('<', $opts->{in});
        }
    }
    if ($opts->{pipe_out}) {
        @out = ('>pipe', $opts->{pipe_out});
        $background = 1;
    } else {
        if (!exists $opts->{out} && defined $opts->{out_append}){
            @out = ('>>', $opts->{out_append});
        } elsif ($opts->{out} && substr($opts->{out}, 0, 1) eq '&') {
            # >&2 redirects must be a single string
            @err = ('>' . $opts->{out});
        } else {
            # Generic redirect to files, scalar refs or open fds
            $opts->{out} ||= \$out;
            @out = ('>', $opts->{out});
        }
    }
    if ($opts->{pipe_err}) {
        @err = ('2>pipe', $opts->{pipe_err});
        $background = 1;
    } else {
        if (!exists $opts->{err} && defined $opts->{err_append}){
            @err = ('2>>', $opts->{err_append});
        } elsif ($opts->{err} && substr($opts->{err}, 0, 1) eq '&') {
            # 2>&1 redirects must be a single string
            @err = ('2>' . $opts->{err});
        } else {
            # Generic redirect to files, scalar refs or open fds
            $opts->{err} ||= \*STDERR;
            @err = ('2>', $opts->{err});
        }
    }

    if ($opts->{'child_before_exec'}) {
        push(@kwargs, 'init', $opts->{'child_before_exec'});
        @cmds = map {
            # The init handler has to be injected after each
            # command but (presumably) before the '|' or '&'.
            if (ref($_) eq 'ARRAY') {
                ($_, @kwargs);
            } else {
                $_;
            }
        } @cmds;
    }

    eval {
        if (@cmds == 1) {
            my $cmd = pop @cmds;
            my $last = pop @$cmd;
            # Support shell-style "command &"
            if ($last eq '&') {
                $background = 1;
            } else {
                push @$cmd, $last;
            }
            $opts->{harness} = harness($cmd, @in, @out, @err);
        } else {
            my ($first, $last) = (shift @cmds, pop @cmds);
            # Support shell-style "command &"
            if ($last eq '&') {
                $background = 1;
            } else {
                push @cmds, $last;
            }
            $opts->{harness} = harness($first, @in, @cmds, @out, @err);
        }
        if ($background) {
            $opts->{success} = $opts->{harness}->start;
        } else {
            $opts->{success} = $opts->{harness}->run;
        }
    };
    if ($@) {
        croak($@) if $opts->{fail} ne 'never';
        $opts->{success} = 0;
        $opts->{exception} = $@;
    } elsif ($opts->{fail} eq 'error'
        and not $opts->{success}) {
        if ($opts->{description}) {
            croak("$opts->{description} failed with error code "
                  . $opts->{harness}->result);
        } elsif (@cmds == 1) {
            croak("$cmds[0][0] failed with error code "
                  . $opts->{harness}->result);
        } else {
            croak(
                'command failed with error code ' . $opts->{harness}->result);
        }
    }
    return $opts->{success};
}

=head2 C<reap($opts[, $opts[,...]])>

If you used one of the C<pipe_*> options to spawn() or used the shell-style "&"
operator to send the process to the background, you will need to wait for your
child processes to finish.  For this you can use the reap() function,
which you can call with the $opts hash reference you gave to spawn() and which
will do the right thing. Multiple $opts can be passed.

Note however that this function will not close any of the pipes for you, so
you probably want to do that first before calling this function.

The following keys of the $opts hash have roughly the same function as
for spawn():

=over 4

=item harness

=item fail

=item success

=item exception

=back

All other keys are probably just ignored.

=cut

sub reap {
    my $status = 1;
    while (my $opts = shift @_) {
        next unless defined($opts->{harness});

        eval {$opts->{success} = $opts->{harness}->finish;};
        if ($@) {
            croak($@) if $opts->{fail} ne 'never';
            $opts->{success} = 0;
            $opts->{exception} = $@;
        } elsif ($opts->{fail} eq 'error'
            and not $opts->{success}) {
            if ($opts->{description}) {
                croak("$opts->{description} failed with error code "
                      . $opts->{harness}->result);
            } else {
                croak('command failed with error code '
                      . $opts->{harness}->result);
            }
        }
        $status &&= $opts->{success};
    }
    return $status;
}

=head2 C<kill($opts[, $opts[, ...]])>

This is a simple wrapper around the kill_kill function. It doesn't allow
any customisation, but takes an $opts hash ref and SIGKILLs the process
two seconds after SIGTERM is sent. If multiple hash refs are passed it
executes kill_kill on each of them. The return status is the ORed value of
all the executions of kill_kill.

=cut

sub kill {
    my $status = 1;
    while (my $opts = shift @_) {
        $status &&= kill_kill($opts->{'harness'}, grace => 2);
    }
    return $status;
}

=head2 C<done($opts)>

Check if a process and its children are done. This is useful when one wants to
know whether reap() can be called without blocking waiting for the process.
It takes a single hash reference as returned by spawn.

=cut

sub done {
    my $opts = shift;

    eval { $opts->{'harness'}->pump_nb; };

    return 0 unless($@);

    if ($@ =~ m/process ended prematurely/) {
        return 1;
    } else {
        croak("Unknown failure when trying to pump_nb: $@");
    }
}

=head2 C<safe_qx([$opts,] @cmds)>

Variant of spawn that emulates the C<qx()> operator by returning the
captured output.

It takes the same arguments as C<spawn> and they have the same
basic semantics with the following exceptions:

=over 4

=item The initial $opts is optional.

=item If only a single command is to be run, the surrounding list
reference can be omitted (see the examples below).

=back

If $opts is given, caller must ensure that the output is captured as a
scalar reference in C<$opts->{out}> (possibly by omitting the "out"
and "out_append" keys).

Furthermore, the commands should not be backgrounded, so they cannot
use '&' nor (e.g. C<$opts->{pipe_in}>).

If needed C<$?> will be set after the call like for C<qx()>.

Examples:

  # Capture the output of a simple command
  # - Both are eqv.
  safe_qx('grep', 'some-pattern', 'path/to/file');
  safe_qx(['grep', 'some-pattern', 'path/to/file']);

  # Capture the output of some pipeline
  safe_qx(['grep', 'some-pattern', 'path/to/file'], '|',
          ['head', '-n1'])

  # Call nproc and capture stdout and stderr interleaved
  safe_qx({ 'err' => '&1'}, 'nproc')

  #  WRONG: Runs grep with 5 arguments including a literal "|" and
  # "-n1", which will generally fail with bad arguments.
  safe_qx('grep', 'some-pattern', 'path/to/file', '|',
          'head', '-n1')

Possible known issue: It might not possible to discard stdout and
capture stderr instead.


=cut

sub safe_qx {
    my ($opts, @args);
    if (ref($_[0]) eq 'HASH') {
        $opts = shift;
    } else {
        $opts = {};
    }
    if (ref($_[0]) eq 'ARRAY') {
        @args = @_;
    } else {
        @args = [@_];
    }
    spawn($opts, @args);
    return ${$opts->{out}};
}

1;

__END__

=head1 EXPORTS

Lintian::Command exports nothing by default, but you can export the
spawn() and reap() functions.

=head1 AUTHOR

Originally written by Frank Lichtenheld <djpig@debian.org> for Lintian.

=head1 SEE ALSO

lintian(1), IPC::Run

=cut

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
