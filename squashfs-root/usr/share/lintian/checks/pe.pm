# pe -- lintian check script -*- perl -*-

# Copyright (C) 2017 Chris Lamb <lamby@debian.org>
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

package Lintian::pe;
use strict;
use warnings;
use autodie;

use List::MoreUtils qw(any);

use Lintian::Tags qw(tag);
use Lintian::Util qw(internal_error);

sub run {
    my (undef, undef, $info) = @_;

    foreach my $file ($info->sorted_index) {
        next unless $file->is_file;
        next unless $file->file_info =~ /^PE32\+? executable/;
        next unless $file->is_open_ok;

        my $buf;
        my $fd = $file->open;

        eval {
            # Offset to main header
            seek($fd, 0x3c, 0) or internal_error("seek: $!");
            read($fd, $buf, 4) or internal_error("read: $!");
            my $pe_offset = unpack('V', $buf);
            # Read magic to determine whether we are are PE32 or PE32+
            seek($fd, $pe_offset + 26 + 64, 0) or internal_error("seek: $!");
            # Read and parse DLLCharacteristics value
            read($fd, $buf, 2) or internal_error("read: $!");
        };

        my $characteristics = unpack('v', $buf);
        my %features = (
            'ASLR' => $characteristics & 0x40,
            'DEP/NX' => $characteristics & 0x100,
            'SEH' => ~$characteristics & 0x400,
        );

        tag 'portable-executable-missing-security-features', $file
          unless any { $_ == 0 } values %features;

        close($fd);
    }

    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
