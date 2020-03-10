# -*- perl -*-
# Lintian::Collect -- interface to package data collection

# Copyright (C) 2008 Russ Allbery
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

package Lintian::Collect;
use strict;
use warnings;
use warnings::register;

use Carp qw(croak);

use Lintian::Util qw(get_dsc_info get_deb_info);

=encoding utf-8

=head1 NAME

Lintian::Collect - Lintian interface to package data collection

=head1 SYNOPSIS

    my ($name, $type, $dir) = ('foobar', 'udeb', '/some/abs/path');
    my $collect = Lintian::Collect->new ($name, $type, $dir);
    $name = $collect->name;
    $type = $collect->type;

=head1 DESCRIPTION

Lintian::Collect provides the shared interface to package data used by
source, binary and udeb packages and .changes files.  It creates an
object of the appropriate type and provides common functions used by the
collection interface to all types of package.

Usually instances should not be created directly (exceptions include
collections), but instead be requested via the
L<info|Lintian::Lab::Entry/info> method in Lintian::Lab::Entry.

This module is in its infancy.  Most of Lintian still reads all data from
files in the laboratory whenever that data is needed and generates that
data via collect scripts.  The goal is to eventually access all data via
this module and its subclasses so that the module can cache data where
appropriate and possibly retire collect scripts in favor of caching that
data in memory.

=head1 CLASS METHODS

=over 4

=item new (PACKAGE, TYPE, BASEDIR[, FIELDS]))

Creates a new object appropriate to the package type.  TYPE can be
retrieved later with the L</type> method.  Croaks if given an unknown
TYPE.

PACKAGE is the name of the package and is stored in the collect object.
It can be retrieved with the L</name> method.

BASEDIR is the base directory for the data and should be absolute.

If FIELDS is given it is assumed to be the fields from the underlying
control file.  This is only used to avoid an unnecessary read
operation (possibly incl. an ar | gzip pipeline) when the fields are
already known.

=cut

sub new {
    my ($class, $pkg, $type, $base_dir, $fields) = @_;
    my $object;
    if ($type eq 'source') {
        require Lintian::Collect::Source;
        $object = Lintian::Collect::Source->new($pkg);
    } elsif ($type eq 'binary' or $type eq 'udeb') {
        require Lintian::Collect::Binary;
        $object = Lintian::Collect::Binary->new($pkg);
    } elsif ($type eq 'buildinfo') {
        require Lintian::Collect::Buildinfo;
        $object = Lintian::Collect::Buildinfo->new($pkg);
    } elsif ($type eq 'changes') {
        require Lintian::Collect::Changes;
        $object = Lintian::Collect::Changes->new($pkg);
    } else {
        croak("Undefined type: $type");
    }
    $object->{name} = $pkg;
    $object->{type} = $type;
    $object->{base_dir} = $base_dir;
    $object->{field} = $fields if defined $fields;
    return $object;
}

=back

=head1 INSTANCE METHODS

In addition to the instance methods documented here, see the documentation
of L<Lintian::Collect::Source>, L<Lintian::Collect::Binary> and
L<Lintian::Collect::Changes> for instance methods specific to source and
binary / udeb packages and .changes files.

=over 4

=item name

Returns the name of the package.

Needs-Info requirements for using I<name>: none

=cut

sub name {
    my ($self) = @_;
    return $self->{name};
}

=item type

Returns the type of the package.

Needs-Info requirements for using I<type>: none

=cut

sub type {
    my ($self) = @_;
    return $self->{type};
}

=item base_dir

Returns the base_dir where all the package information is stored.

Needs-Info requirements for using I<base_dir>: none

=cut

sub base_dir {
    my ($self) = @_;
    return $self->{base_dir};
}

=item lab_data_path ([ENTRY])

Return the path to the ENTRY in the lab.  This is a convenience method
around base_dir.  If ENTRY is not given, this method behaves like
base_dir.

Needs-Info requirements for using I<lab_data_path>: L</base_dir>

=cut

sub lab_data_path {
    my ($self, $entry) = @_;
    my $base = $self->base_dir;
    return "$base/$entry" if $entry;
    return $base;
}

=item field ([FIELD[, DEFAULT]])

If FIELD is given, this method returns the value of the control field
FIELD in the control file for the package.  For a source package, this
is the *.dsc file; for a binary package, this is the control file in
the control section of the package.

If FIELD is passed but not present, then this method will return
DEFAULT (if given) or undef.

Otherwise this will return a hash of fields, where the key is the field
name (in all lowercase).

Needs-Info requirements for using I<field>: none

=cut

sub field {
    my ($self, $field, $def) = @_;
    return $self->_get_field($field, $def);
}

# $self->_get_field([$name[, $def]])
#
# Method getting the fields; this is the backing method of $self->field
#
# It must return either a field (if $name is given) or a hash, where the keys are
# the name of the fields.  If $name is given and it is not present, then it will
# return $def (or undef if $def was not given).
#
# It must cache the result if possible, since field and fields are called often.
# sub _get_field Needs-Info none
sub _get_field {
    my ($self, $field, $def) = @_;
    my $fields;
    unless (exists $self->{field}) {
        my $base_dir = $self->base_dir;
        my $type = $self->{type};
        if ($type eq 'changes' or $type eq 'source'){
            my $file = 'changes';
            $file = 'dsc' if $type eq 'source';
            $fields = get_dsc_info("$base_dir/$file");
        } elsif ($type eq 'binary' or $type eq 'udeb'){
            # (ab)use the unpacked control dir if it is present
            if (   -f "$base_dir/control/control"
                && -s "$base_dir/control/control") {
                $fields = get_dsc_info("$base_dir/control/control");
            } else {
                $fields = (get_deb_info("$base_dir/deb"));
            }
        }
        $self->{field} = $fields;
    } else {
        $fields = $self->{field};
    }
    return $fields->{$field}//$def if $field;
    return $fields;
}

=item is_non_free

Returns a truth value if the package appears to be non-free (based on
the section field; "non-free/*" and "restricted/*")

Needs-Info requirements for using I<is_non_free>: L</field ([FIELD[, DEFAULT]])>

=cut

sub is_non_free {
    my ($self) = @_;
    return $self->{is_non_free} if exists $self->{is_non_free};
    $self->{is_non_free} = 0;
    $self->{is_non_free} = 1
      if $self->field('section', 'main')
      =~ m,^(?:non-free|restricted|multiverse)/,;
    return $self->{is_non_free};
}

# Internal sub for providing a shared storage between multiple
# L::Collect objects from same group.
#
# sub _set_shared_storage Needs-Info none
sub _set_shared_storage {
    my ($self, $storage) = @_;
    $self->{'_shared_storage'} = $storage;
    return;
}

# Internal sub for dumping the memory usage of this instance
#
# Used by the frontend (under debug level >= 4)
#
# sub _memory_usage Needs-Info none
sub _memory_usage {
    my ($self, $calc_usage) = @_;
    my %usage;
    for my $field (keys(%{$self})) {
        next if ($field =~ m{ \A sorted_ }xsm);
        if (exists($self->{"sorted_$field"})) {
            # merge "index" and "sorted_index".  At the price of an extra
            # list, we avoid overcounting all the L::Path objects so the
            # produced result is a lot more accurate.
            $usage{$field}
              = $calc_usage->([$self->{$field},$self->{"sorted_$field"}]);
        } else {
            $usage{$field} = $calc_usage->($self->{$field});
        }
    }
    return \%usage;
}

=back

=head1 AUTHOR

Originally written by Russ Allbery <rra@debian.org> for Lintian.

=head1 SEE ALSO

lintian(1), L<Lintian::Collect::Binary>, L<Lintian::Collect::Changes>,
L<Lintian::Collect::Source>

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
