# duplicate-files -- lintian check script -*- perl -*-

# Copyright (C) 2011 Niels Thykier
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

package Lintian::duplicate_files;
use strict;
use warnings;
use autodie;

use List::MoreUtils qw(any);

use Lintian::Tags qw(tag);

sub run {
    my (undef, undef, $info) = @_;
    my %hashmap;

    foreach my $file ($info->sorted_index){
        my $md5 = $info->md5sums->{$file};
        my $fs;
        next unless defined $md5;
        next unless $file->is_regular_file;
        # Ignore empty files; in some cases (e.g. python) a file is
        # required even if it is empty and we are never looking at a
        # substantial gain in such a case.  Also see #632789
        next unless $file->size;
        next unless $file =~ m{\A usr/share/doc/}xsmo;
        $fs = $hashmap{$md5};
        unless (defined $fs){
            $fs = [$file];
            $hashmap{$md5} = $fs;
        } else {
            push @$fs, $file;
        }
    }

    foreach my $hash (keys %hashmap){
        my @files = @{ $hashmap{$hash} };
        next if scalar(@files) < 2;
        if (any { m,changelog,io} @files) {
            tag 'duplicate-changelog-files', sort @files;
        } else {
            tag 'duplicate-files', sort @files;
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
