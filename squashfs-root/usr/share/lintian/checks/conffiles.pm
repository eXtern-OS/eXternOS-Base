# conffiles -- lintian check script -*- perl -*-

# Copyright (C) 1998 Christian Schwarz
# Copyright (C) 2000 Sean 'Shaleh' Perry
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

package Lintian::conffiles;
use strict;
use warnings;
use autodie;

use Lintian::Tags qw(tag);
use Lintian::Util qw(rstrip);

sub run {
    my (undef, undef, $info) = @_;

    my $cf = $info->control_index('conffiles');
    my %conffiles;

    # Read conffiles if it exists and is a file; no real package uses
    # e.g. links in control.tar.gz.
    if ($cf and $cf->is_file and $cf->is_open_ok) {
        my $fd = $cf->open;
        while (my $filename = <$fd>) {
            # dpkg strips whitespace (using isspace) from the right hand
            # side of the file name.
            rstrip($filename);

            next if $filename eq q{};

            if ($filename !~ m{^ / }xsm) {
                tag 'relative-conffile', $filename;
            } else {
                # strip the leading slash from here.
                $filename =~ s{^ /++ }{}xsm;
            }
            $conffiles{$filename}++;

            if ($conffiles{$filename} > 1) {
                tag 'duplicate-conffile', $filename;
                next;
            }

            if (not defined($info->index($filename))) {
                tag 'conffile-is-not-in-package', $filename;
            }

            if ($filename =~ m{^ usr/ }xsm) {
                tag 'file-in-usr-marked-as-conffile', $filename;
            } else {
                if ($filename !~ m{^ etc/ }xsm) {
                    tag 'non-etc-file-marked-as-conffile', $filename;
                } elsif ($filename =~ m{^ etc/rc.\.d/ }xsm) {
                    tag 'file-in-etc-rc.d-marked-as-conffile', $filename;
                }
            }

        }
        close($fd);

    }

    # Read package contents...
    foreach my $file ($info->sorted_index) {
        if (not $file->is_file and exists $conffiles{$file}) {
            tag 'conffile-has-bad-file-type', $file;
        }
        next unless $file =~ m{\A etc/ }xsm and $file->is_file;

        # If there is an /etc/foo, it must be a conffile (with a few
        # exceptions).
        if (    not exists($conffiles{$file})
            and $file !~ m{ /README $}xsm
            and $file ne 'etc/init.d/skeleton'
            and $file ne 'etc/init.d/rc'
            and $file ne 'etc/init.d/rcS') {
            tag 'file-in-etc-not-marked-as-conffile', $file;
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
