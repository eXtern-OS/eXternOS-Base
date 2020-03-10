#!/usr/bin/perl

# Lintian Lab Tool -- Various Laboratory related utilities
#
# Copyright (C) 2016 Niels Thykier
#
# Based on "frontend/lintian", which was:
# Copyright (C) 1998 Christian Schwarz and Richard Braakman
#
# This program is free software.  It is distributed under the terms of
# the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any
# later version.
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

use strict;
use warnings;

use List::Util qw(max);

use Lintian::Lab;

# turn file buffering off:
STDOUT->autoflush;

my %OPERATIONS = (
    'help'        => \&help,
    'create-lab'  => \&create_lab,
    'remove-lab'  => \&remove_lab,
    'remove-pkgs' => \&remove_pkgs_from_lab,
    'scrub-lab'   => \&scrub_lab,
);

my %CMD_LINE_SYNOPSIS = (
    'help'        => '[operation]',
    'create-lab'  => '<lab-directory>',
    'remove-lab'  => '<lab-directory>',
    'remove-pkgs' => '<lab-directory> <lab-query> [... <lab-query>]',
    'scrub-lab'   => '<lab-directory>',
);

my %HUMAN_SYNOPSIS = (
    'help'        => 'Display help about this command or a given operation.',
    'create-lab'  => 'Create a laboratory',
    'remove-lab'  => 'Remove a laboratory',
    'remove-pkgs' =>
      'Remove packages matching a given query from the laboratory',
    'scrub-lab'   =>
      'Attempt to fix simple metadata corruptions in the laboratory',
);

sub error {
    my ($msg) = @_;
    print "$msg\n";
    exit(2);
}

sub main {
    my ($cmd_name, @args) = @ARGV;
    my $cmd;
    $cmd_name //= 'help';
    if ($cmd_name eq '-h' or $cmd_name eq '--help') {
        print "(Please use \"help\" instead of \"${cmd_name}\"\n";
        $cmd_name = 'help';
    }
    $cmd = $OPERATIONS{$cmd_name};
    if (not $cmd) {
        error("Unknown command \"${cmd_name}\" - try using \"help\" instead");
    }
    exit($cmd->($cmd_name, @args));
}

sub with_lab($&) {
    my ($lab_dir, $closure) = @_;
    my $lab = Lintian::Lab->new($lab_dir);
    my ($act_err, $lab_close_err, $ret);
    $lab->open;
    eval {
        $ret = $closure->($lab);
        $ret //= 0;
    };
    $act_err = $@;
    eval {$lab->close;};
    $lab_close_err = $@;
    die($act_err) if $act_err;
    die($lab_close_err) if $lab_close_err;
    return $ret;
}

sub validate_lab_dir_arg {
    my ($dir) = @_;
    if (not defined($dir)) {
        error('Missing laboratory path');
    }
    return $dir;
}

sub help {
    my (undef, $given_cmd) = @_;
    my $me = $ENV{'LINTIAN_DPLINT_CALLED_AS'} // $0;

    if (defined($given_cmd)) {
        my $cmd_synopsis = $CMD_LINE_SYNOPSIS{$given_cmd} // '';
        my $synopsis = $HUMAN_SYNOPSIS{$given_cmd} // 'No synopsis available';
        if (not exists($OPERATIONS{$given_cmd})) {
            print "Unknown command $given_cmd\n";
            return 1;
        }
        print <<EOF;
Usage: ${me} ${given_cmd} ${cmd_synopsis}

${synopsis}
EOF

    } else {
        my @cmds = sort(keys(%OPERATIONS));
        my $cmd_length = max(map { length } @cmds);

        print <<EOF;
Usage: ${me} <cmd> [args ...]

Perform some common operations on (or related to) permanent Lintian laboratories.

Available operations:
EOF

        for my $cmd (@cmds) {
            my $synopsis = $HUMAN_SYNOPSIS{$cmd} // 'No synopsis available';
            printf "  %-*s   %s\n", $cmd_length, $cmd, $synopsis;
        }
    }
    return 0;
}

sub create_lab {
    my (undef, $lab_dir) = @_;
    my $lab;
    validate_lab_dir_arg($lab_dir);
    $lab = Lintian::Lab->new($lab_dir);
    $lab->create;
    return 0;
}

sub remove_lab {
    my (undef, $lab_dir) = @_;
    my $lab;
    validate_lab_dir_arg($lab_dir);
    $lab = Lintian::Lab->new($lab_dir);
    $lab->remove;
    return 0;
}

sub scrub_lab {
    my (undef, $lab_dir) = @_;
    validate_lab_dir_arg($lab_dir);
    return with_lab $lab_dir, sub {
        my ($lab) = @_;
        $lab->repair;
        return 0;
    };
}

sub remove_pkgs_from_lab {
    my (undef, $lab_dir, @queries) = @_;
    validate_lab_dir_arg($lab_dir);
    if (not @queries) {
        error('Please specify a "lab query" to delete items from the lab');
    }
    return with_lab $lab_dir, sub {
        my ($lab) = @_;
        my $had_match = 0;
        for my $query (@queries) {
            my @res = $lab->lab_query($query);
            if (not @res) {
                print "No matches for $query\n";
            }
            $had_match = 1;
            for my $entry (@res) {
                my $identifier = $entry->identifier;
                print "Removing $identifier (matched by $query)\n";
                $entry->remove;
            }
        }
        if (not $had_match) {
            print "Nothing matched any of the queries given\n";
            return 1;
        }
        return 0;
    };
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
