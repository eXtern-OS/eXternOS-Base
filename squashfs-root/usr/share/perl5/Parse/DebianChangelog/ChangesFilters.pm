#
# Parse::DebianChangelog::ChangesFilters
#
# Copyright 2005,2011 Frank Lichtenheld <frank@lichtenheld.de>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#

=head1 NAME

Parse::DebianChangelog::ChangesFilters - filters to be applied to Debian changelog entries

=head1 SYNOPSIS

=head1 DESCRIPTION

This is currently only used internally by Parse::DebianChangelog and
is not yet documented. There may be still API changes until this module
is finalized.

=cut

package Parse::DebianChangelog::ChangesFilters;

use 5.010;
use strict;
use warnings;

our @ISA = qw(Exporter);

our %EXPORT_TAGS = ( 'all' => [ qw(
				   encode_entities
				   http_ftp_urls
				   email_to_ddpo
				   bugs_to_bts
				   cve_to_mitre
				   pseudo_markup
				   common_licenses
) ] );

our @EXPORT_OK = ( @{ $EXPORT_TAGS{'all'} } );

our @all_filters = (
		    \&encode_entities,
		    \&http_ftp_urls,
		    \&email_to_ddpo,
		    \&bugs_to_bts,
		    \&cve_to_mitre,
		    \&pseudo_markup,
		    \&common_licenses,
		    );

sub encode_entities {
    require HTML::Entities;

    return HTML::Entities::encode_entities( "$_[0]", '<>&"' ) || '';
}

sub http_ftp_urls {
    my ($text, $cgi) = @_;

    $text=~ s|&lt;URL:([-\w\.\/:~_\@]+):([a-zA-Z0-9\'() ]+)&gt;
        |$cgi->a({ -href=>$1 }, $2)
	|xego;
    $text=~ s|(&lt;)?\K(https?:[\w/\.:\@+\-~\%\#?=&;,]+[\w/])(?(1)(?=&gt;))
	|$cgi->a({ -href=>$2 }, $2)
	|xego;
    $text=~ s|(ftp:[\w/\.:\@+\-~\%\#?=&;,]+[\w/])
	|$cgi->a({ -href=>$1 }, $1)
	|xego;

    return $text;
}

sub email_to_ddpo {
    my ($text, $cgi) = @_;

    $text =~ s|([a-zA-Z0-9_\+\-\.]+\@(?:[a-zA-Z0-9][\w\.+\-]+\.[a-zA-Z]{2,}))
	|$cgi->a({ -href=>"http://qa.debian.org/developer.php?login=$1" }, $1)
	|xego;
    return $text;
}

sub bugs_to_bts {
    (my $text = $_[0]) =~ s|(Closes:\s*(?:Bug)?\#?\d+(?:\s*,\s*(?:Bug)?\#?\d+)*)
	|my $tmp = $1; { no warnings;
			 $tmp =~ s@(Bug)?\#?(\d+)@<a class="buglink" href="http://bugs.debian.org/$2">$1\#$2</a>@ig; }
    "$tmp"
	|xiego;
    return $text;
}

sub cve_to_mitre {
    my ($text, $cgi) = @_;

    $text =~ s!\b((?:CVE|CAN)-\d{4}-\d{4,})\b
        !$cgi->a({ -href=>"http://cve.mitre.org/cgi-bin/cvename.cgi?name=$1" }, $1)
	!xego;
    return $text;
}

sub pseudo_markup {
    my ($text, $cgi) = @_;

    $text =~ s|\B\*([a-z][a-z -]*[a-z])\*\B
	|$cgi->em($1)
	|xiego;
    $text=~ s|\B\*([a-z])\*\B
	|$cgi->em($1)
	|xiego;
    $text=~ s|\B\#([a-z][a-z -]*[a-z])\#\B
	|$cgi->strong($1)
	|xego;
    $text=~ s|\B\#([a-z])\#\B
	|$cgi->strong($1)
	|xego;

    return $text;
}

my $fsf_lics = 'http://www.gnu.org/licenses';
my $fsf_old_lics = $fsf_lics."/old-licenses";
sub common_licenses {
    my ($text, $cgi) = @_;

    $text=~ s;(/usr/share/common-licenses/GPL(?:-([1-3]))?)
	;($2 && $2 < 3) ? $cgi->a({ -href=>"$fsf_old_lics/gpl-$2.0.html" }, $1)
                        : $cgi->a({ -href=>"$fsf_lics/gpl.html" }, $1)
	;xego;
    $text=~ s;(/usr/share/common-licenses/LGPL(?:-(2\.[01]|3))?)
	;($2 && $2 < 3) ? $cgi->a({ -href=>"$fsf_old_lics/lgpl-$2.html" }, $1)
                        : $cgi->a({ -href=>"$fsf_lics/lgpl.html" }, $1)
	;xego;
    $text=~ s;(/usr/share/common-licenses/GFDL(?:-1\.([1-3]))?)
	;($2 && $2 < 3) ? $cgi->a({ -href=>"$fsf_old_lics/fdl-1.$2.html" }, $1)
                        : $cgi->a({ -href=>"$fsf_lics/fdl.html" }, $1)
	;xego;
    $text=~ s|(/usr/share/common-licenses/Artistic)
	|$cgi->a({ -href=>"http://www.opensource.org/licenses/artistic-license.php" }, $1)
	|xego;
    $text=~ s|(/usr/share/common-licenses/BSD)
	|$cgi->a({ -href=>"http://www.debian.org/misc/bsd.license" }, $1)
	|xego;

    return $text;
}

sub all_filters {
    my ($text, $cgi) = @_;

    $text = encode_entities( $text, $cgi );
    $text = http_ftp_urls( $text, $cgi );
    $text = email_to_ddpo( $text, $cgi );
    $text = bugs_to_bts( $text, $cgi );
    $text = cve_to_mitre( $text, $cgi );
    $text = pseudo_markup( $text, $cgi );
    $text = common_licenses( $text, $cgi );

    return $text;
}

1;
__END__

=head1 SEE ALSO

Parse::DebianChangelog

=head1 AUTHOR

Frank Lichtenheld, E<lt>frank@lichtenheld.deE<gt>

=head1 COPYRIGHT AND LICENSE

Copyright (C) 2005 by Frank Lichtenheld

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

=cut
