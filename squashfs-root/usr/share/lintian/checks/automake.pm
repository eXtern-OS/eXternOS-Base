# automake -- lintian check script -*- perl -*-
#
# Copyright (C) 2013 Gautier Minster
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

package Lintian::automake;
use strict;
use warnings;
use autodie;

use Lintian::Tags qw(tag);

sub run {
    my (undef, undef, $info) = @_;

    my $makefile = $info->index('Makefile.am');

    # If there's no Makefile.am, automake probably isn't used, we're fine
    return unless defined $makefile;

    my $deprecated_configure = $info->index('configure.in');

    if (defined $deprecated_configure) {
        tag 'deprecated-configure-filename';
    }

    return;
}

1;

