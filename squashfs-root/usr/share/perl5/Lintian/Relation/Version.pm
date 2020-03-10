# -*- perl -*-
# Lintian::Relation::Version -- comparison operators on Debian versions

# Copyright (C) 1998 Christian Schwarz and Richard Braakman
# Copyright (C) 2004-2009 Russ Allbery <rra@debian.org>
# Copyright (C) 2009 Adam D. Barratt <adam@adam-barratt.org.uk>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

package Lintian::Relation::Version;

use strict;
use warnings;

use Carp qw(croak);
use Exporter qw(import);

BEGIN {
    our @EXPORT_OK = qw(versions_equal versions_lte versions_gte versions_lt
      versions_gt versions_compare versions_comparator);
    our %EXPORT_TAGS = ('all' => \@EXPORT_OK);
}

use AptPkg::Config '$_config';
my $versioning = do {
    my $config = AptPkg::Config->new;
    $config->init;
    $config->system->versioning;
};

=head1 NAME

Lintian::Relation::Version - Comparison operators on Debian versions

=head1 SYNOPSIS

    print "yes\n" if versions_equal('1.0', '1.00');
    print "yes\n" if versions_gte('1.1', '1.0');
    print "no\n" if versions_lte('1.1', '1.0');
    print "yes\n" if versions_gt('1.1', '1.0');
    print "no\n" if versions_lt('1.1', '1.1');
    print "yes\n" if versions_compare('1.1', '<=', '1.1');

=head1 DESCRIPTION

This module provides five functions for comparing version numbers.  The
underlying implementation uses C<libapt-pkg-perl> to ensure that
the results match what dpkg will expect.

=head1 FUNCTIONS

=over 4

=item versions_equal(A, B)

Returns true if A is equal to B (C<=>) and false otherwise.

=cut

sub versions_equal {
    my ($p, $q) = @_;
    my $result;

    return 1 if $p eq $q;

    $result = $versioning->compare($p, $q);

    return ($result == 0);
}

=item versions_lte(A, B)

Returns true if A is less than or equal (C<< <= >>) to B and false
otherwise.

=cut

sub versions_lte {
    my ($p, $q) = @_;
    my $result;

    return 1 if $p eq $q;

    $result = $versioning->compare($p, $q);

    return ($result <= 0);
}

=item versions_gte(A, B)

Returns true if A is greater than or equal (C<< >= >>) to B and false
otherwise.

=cut

sub versions_gte {
    my ($p, $q) = @_;
    my $result;

    return 1 if $p eq $q;

    $result = $versioning->compare($p, $q);

    return ($result >= 0);
}

=item versions_lt(A, B)

Returns true if A is less than (C<<< << >>>) B and false otherwise.

=cut

sub versions_lt {
    my ($p, $q) = @_;
    my $result;

    return 0 if $p eq $q;

    $result = $versioning->compare($p, $q);

    return ($result < 0);
}

=item versions_gt(A, B)

Returns true if A is greater than (C<<< >> >>>) B and false otherwise.

=cut

sub versions_gt {
    my ($p, $q) = @_;
    my $result;

    return 0 if $p eq $q;

    $result = $versioning->compare($p, $q);

    return ($result > 0);
}

=item versions_compare(A, OP, B)

Returns true if A OP B, where OP is one of C<=>, C<< <= >>, C<< >= >>,
C<<< << >>>, or C<<< >> >>>, and false otherwise.

=cut

sub versions_compare {
    my ($p, $op, $q) = @_;
    if    ($op eq  '=') { return versions_equal($p, $q) }
    elsif ($op eq '<=') { return versions_lte($p, $q) }
    elsif ($op eq '>=') { return versions_gte($p, $q) }
    elsif ($op eq '<<') { return versions_lt($p, $q) }
    elsif ($op eq '>>') { return versions_gt($p, $q) }
    else { croak("unknown operator $op") }
}

=item versions_comparator (A, B)

Returns -1, 0 or 1 if the version A is (respectively) less than, equal
to or greater than B.  This is useful for (e.g.) sorting a list of
versions:

 foreach my $version (sort versions_comparator @versions) {
    ...
 }

=cut

# Use a prototype to avoid confusing Perl when used with sort.

sub versions_comparator ($$) {
    my ($p, $q) = @_;
    return $versioning->compare($p, $q);
}

=back

=head1 AUTHOR

Originally written by Russ Allbery <rra@debian.org> for Lintian and adapted
to use libapt-pkg-perl by Adam D. Barratt <adam@adam-barratt-org.uk>.

=head1 SEE ALSO

lintian(1)

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
