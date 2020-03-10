# Copyright © 2008 Jordà Polo <jorda@ettin.org>
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

package Lintian::Output::LetterQualifier;

use strict;
use warnings;

use Term::ANSIColor qw(colored);
use Lintian::Tag::Info ();

use Lintian::Output qw(:util);
use parent qw(Lintian::Output);

my %codes = (
    'classification' => {
        'wild-guess' => 'C?',
        'possible' => 'C ',
        'certain' => 'C!'
    },
    'pedantic' => {
        'wild-guess' => 'P?',
        'possible' => 'P ',
        'certain' => 'P!'
    },
    'wishlist' => {
        'wild-guess' => 'W?',
        'possible' => 'W ',
        'certain' => 'W!'
    },
    'minor' => {
        'wild-guess' => 'M?',
        'possible' => 'M ',
        'certain' => 'M!'
    },
    'normal' => {
        'wild-guess' => 'N?',
        'possible' => 'N ',
        'certain' => 'N!'
    },
    'important' => {
        'wild-guess' => 'I?',
        'possible' => 'I ',
        'certain' => 'I!'
    },
    'serious' => {
        'wild-guess' => 'S?',
        'possible' => 'S ',
        'certain' => 'S!'
    },
);

my %lq_default_colors = (
    'pedantic' => {
        'wild-guess' => 'green',
        'possible' => 'green',
        'certain' => 'green'
    },
    'wishlist' => {
        'wild-guess' => 'green',
        'possible' => 'green',
        'certain' => 'cyan'
    },
    'minor' => {
        'wild-guess' => 'green',
        'possible' => 'cyan',
        'certain' => 'yellow'
    },
    'normal' => {
        'wild-guess' => 'cyan',
        'possible' => 'yellow',
        'certain' => 'yellow'
    },
    'important' => {
        'wild-guess' => 'yellow',
        'possible' => 'red',
        'certain' => 'red'
    },
    'serious' => {
        'wild-guess' => 'yellow',
        'possible' => 'red',
        'certain' => 'magenta'
    },
);

sub new {
    my $self = Lintian::Output::new('Lintian::Output::LetterQualifier');

    $self->colors({%lq_default_colors});

    return $self;
}

sub print_tag {
    my ($self, $pkg_info, $tag_info, $information, $override) = @_;

    my $code = $tag_info->code;
    $code = 'X' if $tag_info->experimental;
    $code = 'O' if defined($override);

    my $sev = $tag_info->severity;
    my $cer = $tag_info->certainty;
    my $lq = $codes{$sev}{$cer};

    my $pkg = $pkg_info->{package};
    my $type = ($pkg_info->{type} ne 'binary') ? " $pkg_info->{type}" : '';

    my $tag = $tag_info->tag;

    $information = ' ' . $self->_quote_print($information)
      if $information ne '';

    if ($self->_do_color) {
        my $color = $self->colors->{$sev}{$cer};
        $lq = colored($lq, $color);
        $tag = colored($tag, $color);
    }

    $self->_print('', "$code\[$lq\]: $pkg$type", "$tag$information");
    if (not $self->issued_tag($tag_info->tag) and $self->showdescription) {
        my $description = $tag_info->description('text', '   ');
        $self->_print('', 'N', '');
        $self->_print('', 'N', split("\n", $description));
        $self->_print('', 'N', '');
    }
    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
