# huge-usr-share -- lintian check script -*- perl -*-

# Copyright (C) 2004 Jeroen van Wolffelaar <jeroen@wolffelaar.nl>
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

package Lintian::huge_usr_share;
use strict;
use warnings;
use autodie;

use Lintian::Tags qw(tag);

# Threshold in kB of /usr/share to trigger this warning.  Consider that the
# changelog alone can be quite big, and cannot be moved away.
my $THRESHOLD_SIZE_SOFT = 4096;
my $THRESHOLD_SIZE_HARD = 8192;
my $THRESHOLD_PERC = 50;

sub run {
    my (undef, undef, $info) = @_;
    # Skip architecture-dependent packages.
    my $arch = $info->field('architecture', '');
    return if $arch eq 'all';

    # Add up the space taken by the package and the space taken by
    # just the files in /usr/share.  Convert the totals to kilobytes.
    my ($size, $size_usrshare) = (0, 0);
    for my $file (grep { $_->is_regular_file } $info->sorted_index) {
        $size += $file->size;
        if ($file =~ m,usr/share/,) {
            $size_usrshare += $file->size;
        }
    }
    $size = int($size / 1024);
    $size_usrshare = int($size_usrshare / 1024);

    if ($size_usrshare > $THRESHOLD_SIZE_SOFT) {
        my $perc = int(100 * $size_usrshare / $size);
        if ($size_usrshare > $THRESHOLD_SIZE_HARD || $perc > $THRESHOLD_PERC) {
            tag 'arch-dep-package-has-big-usr-share',
              "${size_usrshare}kB $perc%";
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
