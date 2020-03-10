# my-vendor/another-check -- lintian example check script -*- perl -*-
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

package Lintian::my_vendor::another_check;

use strict;
use warnings;

use Lintian::Tags qw(tag);

sub run {
    my ($pkg, undef, $info) = @_;
    if (not $info->index("usr/share/doc/$pkg/important-file")) {
        tag 'missing-some-important-file', "usr/share/doc/$pkg/important-file";
    }
    return;
}

1;
