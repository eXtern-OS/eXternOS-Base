# -*- perl -*-
# Lintian::Internal::FrontendUtil -- internal helpers for lintian frontends

# Copyright (C) 2011 Niels Thykier
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

package Lintian::Internal::FrontendUtil;
use strict;
use warnings;
use autodie;

use Exporter qw(import);

use Carp qw(croak);
use Dpkg::Vendor;

use Lintian::CollScript;
use Lintian::Command qw(safe_qx);
use Lintian::Util qw(check_path);

our @EXPORT_OK
  = qw(check_test_feature default_parallel load_collections split_tag
  sanitize_environment open_file_or_fd);

# Check if we are testing a specific feature
#  - e.g. vendor-libdpkg-perl
sub check_test_feature{
    my $env = $ENV{LINTIAN_TEST_FEATURE};
    return 0 unless $env;
    foreach my $feat (@_){
        return 1 if($env =~ m/$feat/);
    }
    return 0;
}

{
    # sanitize_environment
    #
    # Reset the environment to a known and well-defined state.
    #
    # We trust nothing but "LINTIAN_*" variables and a select few
    # variables.  This is mostly to ensure we know what state tools
    # (e.g. tar) start in.  In particular, we do not want to inherit
    # some random "TAR_OPTIONS" or "GZIP" values.
    my %PRESERVE_ENV = map { $_ => 1 } qw(
      DEBRELEASE_DEBS_DIR
      HOME
      LANG
      LC_ALL
      LC_MESSAGES
      PATH
      TMPDIR
      XDG_CACHE_HOME
      XDG_CONFIG_DIRS
      XDG_CONFIG_HOME
      XDG_DATA_DIRS
      XDG_DATA_HOME
    );

    sub sanitize_environment {
        for my $key (keys(%ENV)) {
            delete $ENV{$key}
              if not exists($PRESERVE_ENV{$key})
              and $key !~ m/^LINTIAN_/;
        }
        # reset locale definition (necessary for tar)
        $ENV{'LC_ALL'} = 'C';

        # reset timezone definition (also for tar)
        $ENV{'TZ'} = '';

        # When run in some automated ways, Lintian may not have a
        # PATH, but we assume we can call standard utilities without
        # their full path.  If PATH is completely unset, add something
        # basic.
        $ENV{'PATH'} = '/bin:/usr/bin' unless exists($ENV{'PATH'});
        return;
    }
}

# load_collections ($visitor, $dirname)
#
# Load collections from $dirname and pass them to $visitor.  $visitor
# will be called once per collection as it has been loaded.  The first
# (and only) argument to $visitor is the collection as an instance of
# Lintian::CollScript instance.
sub load_collections {
    my ($visitor, $dirname) = @_;

    opendir(my $dir, $dirname);

    foreach my $file (readdir $dir) {
        next if $file =~ m/^\./;
        next unless $file =~ m/\.desc$/;
        my $cs = Lintian::CollScript->new("$dirname/$file");
        $visitor->($cs);
    }

    closedir($dir);
    return;
}

# Return the default number of parallelization to be used
sub default_parallel {
    # check cpuinfo for the number of cores...
    my %opts = ('err' => '&1');
    my $cpus = safe_qx(\%opts, 'nproc');
    if ($? == 0 and $cpus =~ m/^\d+$/) {
        # Running up to twice the number of cores usually gets the most out
        # of the CPUs and disks but it might be too aggressive to be the
        # default for -j. Only use <cores>+1 then.
        return $cpus + 1;
    }

    # No decent number of jobs? Just use 2 as a default
    return 2;
}

{
    # Matches something like:  (1:2.0-3) [arch1 arch2]
    # - captures the version and the architectures
    my $verarchre = qr,(?: \s* \(( [^)]++ )\) \s* \[ ( [^]]++ ) \]),xo;
    #                             ^^^^^^^^          ^^^^^^^^^^^^
    #                           ( version   )      [architecture ]

    # matches the full deal:
    #    1  222 3333  4444444   5555   666  777
    # -  T: pkg type (version) [arch]: tag [...]
    #           ^^^^^^^^^^^^^^^^^^^^^
    # Where the marked part(s) are optional values.  The numbers above
    # the example are the capture groups.
    my $TAG_REGEX
      = qr/([EWIXOPC]): (\S+)(?: (\S+)(?:$verarchre)?)?: (\S+)(?:\s+(.*))?/o;

    sub split_tag {
        my ($tag_input) = @_;
        my $pkg_type;
        return unless $tag_input =~ m/^${TAG_REGEX}$/o;
        # default value...
        $pkg_type = $3//'binary';
        return ($1, $2, $pkg_type, $4, $5, $6, $7);
    }
}

# open_file_or_fd(TO_OPEN, MODE)
#
# Open a given file or FD based on TO_OPEN and MODE and returns the
# open handle.  Will croak / throw a trappable error on failure.
#
# MODE can be one of "<" (read) or ">" (write).
#
# TO_OPEN is one of:
#  * "-", alias of "&0" or "&1" depending on MODE
#  * "&N", reads/writes to the file descriptor numbered N
#          based on MODE.
#  * "+FILE" (MODE eq '>' only), open FILE in append mode
#  * "FILE", open FILE in read or write depending on MODE.
#            Note that this will truncate the file if MODE
#            is ">".
sub open_file_or_fd {
    my ($to_open, $mode) = @_;
    my $fd;
    # autodie trips this for some reasons (possibly fixed
    # in v2.26)
    no autodie qw(open);
    if ($mode eq '<') {
        if ($to_open eq '-' or $to_open eq '&0') {
            $fd = \*STDIN;
        } elsif ($to_open =~ m/^\&\d+$/) {
            open($fd, '<&=', substr($to_open, 1))
              or die("fdopen $to_open for reading: $!\n");
        } else {
            open($fd, '<', $to_open)
              or die("open $to_open for reading: $!\n");
        }
    } elsif ($mode eq '>') {
        if ($to_open eq '-' or $to_open eq '&1') {
            $fd = \*STDOUT;
        } elsif ($to_open =~ m/^\&\d+$/) {
            open($fd, '>&=', substr($to_open, 1))
              or die("fdopen $to_open for writing: $!\n");
        } else {
            $mode = ">$mode" if $to_open =~ s/^\+//;
            open($fd, $mode, $to_open)
              or die("open $to_open for write/append ($mode): $!\n");
        }
    } else {
        croak("Invalid mode \"$mode\" for open_file_or_fd");
    }
    return $fd;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
