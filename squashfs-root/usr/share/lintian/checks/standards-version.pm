# standards-version -- lintian check script -*- perl -*-

# Copyright (C) 1998 Christian Schwarz and Richard Braakman
# Copyright (C) 2008-2009 Russ Allbery
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

package Lintian::standards_version;

use strict;
use warnings;
use autodie;

use POSIX qw(strftime);
use List::Util qw(first);
use Date::Parse qw(str2time);

use Lintian::Data;
use Lintian::Tags qw(tag);
use Lintian::Util qw(internal_error);

# Any Standards Version released before this day is "ancient"
my $ANCIENT_DATE_DATA = Lintian::Data->new(
    'standards-version/ancient-date',
    qr{\s*<\s*},
    sub {
        my $date = str2time($_[1])
          or internal_error("Cannot parse ANCIENT_DATE: $!");
        return $date;
    });

my $ANCIENT_DATE = $ANCIENT_DATE_DATA->value('ANCIENT')
  or internal_error('Cannot get ANCIENT_DATE');

my $STANDARDS= Lintian::Data->new('standards-version/release-dates', qr/\s+/o);

# In addition to the normal Lintian::Data structure, we also want a list of
# all standards and their release dates so that we can check things like the
# release date of the standard released after the one a package declared.  Do
# that by pulling all data out of the Lintian::Data structure and sorting it
# by release date.  We can also use this to get the current standards version.
my @STANDARDS = reverse sort { $a->[1] <=> $b->[1] }
  map { [$_, $STANDARDS->value($_)] } $STANDARDS->all;
my $CURRENT_DATE = $STANDARDS[0][1];

# In scalar context you get the string (e.g. "3.9.2")
# and in list context you get it split into pieces (3, 9, 2)
my $CURRENT      = $STANDARDS[0][0];
my @CURRENT      = split(m/\./, $CURRENT);

sub run {
    my (undef, undef, $info) = @_;

    # udebs aren't required to conform to policy, so they don't need
    # Standards-Version. (If they have it, though, it should be valid.)
    my $version = $info->field('standards-version');
    my $all_udeb = 1;
    $all_udeb = 0
      if first { $info->binary_package_type($_) ne 'udeb' } $info->binaries;

    if (not defined $version) {
        tag 'no-standards-version-field' unless $all_udeb;
        return;
    }

    # Check basic syntax and strip off the fourth digit.  People are allowed to
    # include the fourth digit if they want, but it indicates a non-normative
    # change in Policy and is therefore meaningless in the Standards-Version
    # field.
    unless ($version =~ m/^\s*(\d+\.\d+\.\d+)(?:\.\d+)?\s*$/) {
        tag 'invalid-standards-version', $version;
        return;
    }
    my $stdver = $1;
    my ($major, $minor, $patch) = $stdver =~ m/^(\d+)\.(\d+)\.(\d+)/;

    # To do some date checking, we have to get the package date from
    # the changelog file.  If we can't find the changelog file, assume
    # that the package was released today, since that activates the
    # most tags.
    my $changes = $info->changelog;
    my ($pkgdate, $dist);
    if (defined $changes) {
        my ($entry) = $changes->data;
        $pkgdate
          = ($entry && $entry->Timestamp) ? $entry->Timestamp : $CURRENT_DATE;
        $dist = ($entry && $entry->Distribution)? $entry->Distribution : '';
    } else {
        $pkgdate = $CURRENT_DATE;
    }

    # Check for packages dated prior to the date of release of the standards
    # version with which they claim to comply.
    if (   defined $dist
        && $dist ne 'UNRELEASED'
        && $STANDARDS->known($stdver)
        && $STANDARDS->value($stdver) > $pkgdate) {

        my $package = strftime('%Y-%m-%d', gmtime $pkgdate);
        my $release = strftime('%Y-%m-%d', gmtime $STANDARDS->value($stdver));
        if ($package eq $release) {
            # Increase the precision if required
            my $fmt = '%Y-%m-%d %H:%M:%S UTC';
            $package = strftime($fmt, gmtime $pkgdate);
            $release = strftime($fmt, gmtime $STANDARDS->value($stdver));
        }
        tag 'timewarp-standards-version', "($package < $release)";
    }

    my $tag = "$version (current is $CURRENT)";
    if (not $STANDARDS->known($stdver)) {
        # Unknown standards version.  Perhaps newer?
        if (
               ($major > $CURRENT[0])
            or ($major == $CURRENT[0] and $minor > $CURRENT[1])
            or (    $major == $CURRENT[0]
                and $minor == $CURRENT[1]
                and $patch > $CURRENT[2])
          ) {
            tag 'newer-standards-version', $tag;
        } else {
            tag 'invalid-standards-version', $version;
        }
    } elsif ($stdver eq $CURRENT) {
        # Current standard.  Nothing more to check.
        return;
    } else {
        # Otherwise, we need to see if the standard that this package
        # declares is both new enough to not be ancient and was the
        # current standard at the time the package was uploaded.
        #
        # A given standards version is considered obsolete if the
        # version following it has been out for at least two years (so
        # the current version is never obsolete).
        my $rdate = $STANDARDS->value($stdver);
        my $released = strftime('%Y-%m-%d', gmtime $rdate);
        $tag = "$version (released $released) (current is $CURRENT)";
        if ($rdate < $ANCIENT_DATE) {
            tag 'ancient-standards-version', $tag;
        } else {
            # We have to get the package date from the changelog file.  If we
            # can't find the changelog file, always issue the tag.
            if (not defined $changes) {
                tag 'out-of-date-standards-version', $tag;
                return;
            }
            my ($entry) = $changes->data;
            my $timestamp
              = ($entry && $entry->Timestamp) ? $entry->Timestamp : 0;
            for my $standard (@STANDARDS) {
                last if $standard->[0] eq $stdver;
                if ($standard->[1] < $timestamp) {
                    tag 'out-of-date-standards-version', $tag;
                    last;
                }
            }
        }
    }

    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
