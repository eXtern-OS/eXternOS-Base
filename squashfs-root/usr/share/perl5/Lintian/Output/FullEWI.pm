# Copyright © 2011 Niels Thykier <niels@thykier.net>
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

package Lintian::Output::FullEWI;

# The FullEWI always emit *full* package metadata even if it is
# redundant (that is, optional values are always included) when
# emitting tags.
#   Other than that, it is identical to the normal output.
#
# When parsing a lintian.log written in format, it is no longer
# ambiguous which package is referred to (even if --verbose is
# not used).
#   This makes machine-parsing of the log easier, especially
# when using the parsed data with the Lintian::Lab API.
#
# The full format of the emitted tag is:
#
#  C: name type (version) [arch]: tag [...]
#
# Note the "[...]" is the extra which may or may not be present
# depending on the tag.
#
# Notable cases:
# * binary packages include type classification
# * source packages include an architecture, which is always
#   "source".
# * "[arch]" may contain spaces (and generally do for .changes)
#   files.
# * "(version)" may contain colon (i.e. epoch versions)

use strict;
use warnings;

use parent qw(Lintian::Output);

# Overridden from Lintian::Output
sub _format_pkg_info {
    my ($self, $pkg_info, $tag_info, $override) = @_;
    my $code = $tag_info->code;
    $code = 'X' if $tag_info->experimental;
    $code = 'O' if defined $override;
    my $version = $pkg_info->{version};
    my $arch = '';
    my $type = $pkg_info->{type};
    $arch = "$pkg_info->{arch}" if $pkg_info->{type} ne 'source';
    $arch = 'source' unless $arch;
    return "$code: $pkg_info->{package} $type ($version) [$arch]";
}

1;

