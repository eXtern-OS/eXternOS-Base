# Tags::ColonSeparated -- Perl tags functions for lintian
# $Id: Tags.pm 489 2005-09-17 00:06:30Z djpig $

# Copyright (C) 2005,2008 Frank Lichtenheld <frank@lichtenheld.de>
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

package Lintian::Output::ColonSeparated;
use strict;
use warnings;

use Lintian::Output qw(:util);
use parent qw(Lintian::Output);

sub print_tag {
    my ($self, $pkg_info, $tag_info, $information, $override) = @_;
    my $odata = '';
    if ($override) {
        $odata = $override->tag;
        $odata .= ' ' . $self->_quote_print($override->extra)
          if $override->extra;
    }

    $self->issued_tag($tag_info->tag);
    $self->_print(
        'tag',
        $tag_info->code,
        $tag_info->severity,
        $tag_info->certainty,
        ($tag_info->experimental ? 'X' : '') . (defined($override) ? 'O' : ''),
        @{$pkg_info}{'package','version','arch','type'},
        $tag_info->tag,
        $self->_quote_print($information),
        $odata,
    );
    return;
}

sub _delimiter {
    return;
}

sub _message {
    my ($self, @args) = @_;

    foreach (@args) {
        $self->_print('message', $_);
    }
    return;
}

sub _warning {
    my ($self, @args) = @_;

    foreach (@args) {
        $self->_print('warning', $_);
    }
    return;
}

sub _print {
    my ($self, @args) = @_;

    my $output = $self->string(@args);
    print {$self->stdout} $output;
    return;
}

sub string {
    my ($self, @args) = _global_or_object(@_);

    return join(':', _quote_char(':', @args))."\n";
}

sub _quote_char {
    my ($char, @items) = @_;

    foreach (@items) {
        s/\\/\\\\/go;
        s/\Q$char\E/\\$char/go;
    }

    return @items;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
