# triggers -- lintian check script -*- perl -*-

# Copyright (C) 2017 Niels Thykier
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

package Lintian::triggers;

use strict;
use warnings;

use Lintian::Data;
use Lintian::Tags qw(tag);
use Lintian::Util qw(internal_error strip);

sub _parse_trigger_types {
    my ($key, $val) = @_;
    my %values;
    for my $kvstr (split(m/\s*,\s*/, $val)) {
        my ($k, $v) = split(m/\s*=\s*/, $kvstr, 2);
        $values{$k} = $v;
    }
    if (exists($values{'implicit-await'})) {
        internal_error(
            join(q{ },
                'Invalid trigger-types data file:',
                "$key is defined as implicit-await trigger,",
                'but is not defined as an await trigger')
        ) if $values{'implicit-await'} and not $values{'await'};
    }
    return \%values;
}

my $TRIGGER_TYPES = Lintian::Data->new('triggers/trigger-types',
    qr/\s*\Q=>\E\s*/, \&_parse_trigger_types);

sub run {
    my (undef, undef, $info) = @_;
    my $triggers_file = $info->control_index('triggers');
    return if not $triggers_file or not $triggers_file->is_open_ok;
    my $fd = $triggers_file->open;
    my %seen_triggers;
    while (my $line = <$fd>) {
        strip($line);
        next if $line =~ m/^(?:\s*)(?:#.*)?$/;
        my ($trigger_type, $arg) = split(m/\s++/, $line, 2);
        my $trigger_info = $TRIGGER_TYPES->value($trigger_type);
        if (not $trigger_info) {
            tag 'unknown-trigger', $line, "(line $.)";
            next;
        }
        if ($trigger_info->{'implicit-await'}) {
            tag 'uses-implicit-await-trigger', $line, "(line $.)";
        }
        if (defined(my $prev_info = $seen_triggers{$arg})) {
            my ($prev_line, $prev_line_no) = @{$prev_info};
            tag 'repeated-trigger-name', $line, "(line $.)", 'vs', $prev_line,
              "(line $prev_line_no)";
            next;
        }
        $seen_triggers{$arg} = [$line, $.];
    }
    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
