# -*- perl -*-
# Lintian::Collect::Group -- interface to group data collections

# Copyright (C) 2011 Niels Thykier
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

# This is a "Lintian::Collect"-like interface (as in "not quite a
# Lintian::Collect").
package Lintian::Collect::Group;

use strict;
use warnings;

=head1 NAME

Lintian::Collect::Group - Lintian interface to group data collection

=head1 SYNOPSIS

 my $group = Lintian::ProcessableGroup->new ('lintian_2.5.0_i386.changes');
 my $ginfo = Lintian::Collect::Group->new ($group);
 
 foreach my $bin ($group->get_binary_processables) {
    my $pkg_name = $bin->pkg_name;
    foreach my $dirdep ($ginfo->direct_dependencies ($bin)) {
        print "$pkg_name (pre-)depends on $dirdep (which is also in this group)\n";
    }
 }

=head1 DESCRIPTION

Lintian::Collect::Group is a "group" variant of the Lintian::Collect
modules.  It attempts to expose a similar interface as these and
provide useful information about the processable group (or members of
it).

=head1 CLASS METHODS

=over 4

=item Lintian::Collect::Group->new ($group)

Creates a new object to provide information about
L<$group|Lintian::ProcessableGroup>.

=cut

sub new {
    my ($class, $group) = @_;
    my $shared_storage = {};
    my $self = {
        'group' => $group,
        '_shared_storage' => $shared_storage,
    };
    for my $member ($group->get_processables) {
        $member->info->_set_shared_storage($shared_storage);
    }
    return bless($self, $class);
}

=item direct_dependencies (PROC)

If PROC is a part of the underlying processable group, this method
returns a listref containing all the direct dependencies of PROC.  If
PROC is not a part of the group, this returns undef.

Note: Only strong dependencies (Pre-Depends and Depends) are
considered.

Note: Self-dependencies (if any) are I<not> included in the result.

=cut

# sub direct_dependencies Needs-Info <>
sub direct_dependencies {
    my ($self, $p) = @_;
    my $deps = $self->{'direct-dependencies'};
    unless ($deps) {
        my $group = $self->{'group'};
        my @procs = $group->get_processables('binary');
        push @procs, $group->get_processables('udeb');
        $deps = {};
        foreach my $proc (@procs) {
            my $pname = $proc->pkg_name;
            my $relation = $proc->info->relation('strong');
            my $d = [];
            foreach my $oproc (@procs) {
                my $opname = $oproc->pkg_name;
                # Ignore self deps - we have checks for that and it
                # will just end up complicating "correctness" of
                # otherwise simple checks.
                next if $opname eq $pname;
                push @$d, $oproc if $relation->implies($opname);
            }
            $deps->{$pname} = $d;
        }
        $self->{'direct-dependencies'} = $deps;
    }
    return $deps->{$p->pkg_name} if $p;
    return $deps;
}

=item $ginfo->type

Return the type of this collect object (which is the string 'group').

=cut

# Return the package type.
# sub type Needs-Info <>
sub type {
    my ($self) = @_;
    return 'group';
}

=item spelling_exceptions

Returns a hashref of words, which the spell checker should ignore.
These words are generally based on the package names in the group to
avoid false-positive "spelling error" when packages have "fun" names.

Example: Package alot-doc (#687464)

=cut

# sub spelling_exceptions Needs-Info <>
sub spelling_exceptions {
    my ($self) = @_;
    return $self->{'spelling_exceptions'}
      if exists $self->{'spelling_exceptions'};
    my %except;
    my $group = $self->{'group'};
    foreach my $proc ($group->get_processables('binary')) {
        foreach my $name ($proc->pkg_name, $proc->pkg_src) {
            $except{$name} = 1;
            $except{$_} = 1 for split m/-/, $name;
        }
    }
    $self->{'spelling_exceptions'} = \%except;
    return \%except;
}

=back

=head1 AUTHOR

Originally written by Niels Thykier <niels@thykier.net> for Lintian.

=head1 SEE ALSO

lintian(1), Lintian::Collect::Binary(3), Lintian::Collect::Changes(3),
Lintian::Collect::Source(3)

=cut

1;
__END__;

