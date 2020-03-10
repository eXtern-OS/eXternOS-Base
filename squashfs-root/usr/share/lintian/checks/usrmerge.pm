# usrmerge -- lintian check script -*- perl -*-

# Copyright (C) 2016 Marco d'Itri
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

package Lintian::usrmerge;
use strict;
use warnings;
use autodie;

use Lintian::Tags qw(tag);

sub run {
    my (undef, undef, $info) = @_;

    foreach my $file1 ($info->sorted_index) {
        next unless $file1 =~ m,^(?:s?bin|lib(?:|[ox]?32|64))/,;
        my $file2 = $info->index("usr/$file1") or next;
        next if $file1->is_dir and $file2->is_dir;

        if ($file1 =~ m,^lib.+\.(?:so[\.0-9]*|a)$,) {
            tag 'library-in-root-and-usr', $file1, $file2;
        } else {
            tag 'file-in-root-and-usr', $file1, $file2;
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
