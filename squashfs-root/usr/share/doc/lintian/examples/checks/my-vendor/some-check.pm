# my-vendor/some-check -- lintian example check script -*- perl -*-
#
# Copyright © 2013 Niels Thykier <niels@thykier.net>
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

package Lintian::my_vendor::some_check;

use strict;
use warnings;

use Lintian::Tags qw(tag);

sub run {
    my ($pkg, undef, $info) = @_;

    # This check only applies to source packages that are named
    # my-vendor-<something>
    return unless $pkg =~ m{\A my-vendor-}xsm;
    # Does not apply to the source "my-vendor-tools"
    return if $pkg eq 'my-vendor-tools';

    if (not $info->relation('build-depends')->implies('my-vendor-tools')) {
        tag 'missing-build-depends-on-my-vendor-tools';
    }
    return;
}

1;
