# Lintian::Lab::ManifestDiff -- Representation of a diff between two manifests

# Copyright (C) 2011 Niels Thykier
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

package Lintian::Lab::ManifestDiff;

use strict;
use warnings;

use parent qw(Class::Accessor::Fast);

=head1 NAME

Lintian::Lab::ManifestDiff -- Difference representation between two Manifests

=head1 SYNOPSIS

 use Lintian::Lab::Manifest;
 
 my $olist = Lintian::Lab::Manifest->new ('binary');
 my $nlist = Lintian::Lab::Manifest->new ('binary');
 $olist->read_list ('old/binary-packages');
 $nlist->read_list ('new/binary-packages');
 my $diff = $olist->diff($nlist);
 foreach my $added (@{ $diff->added }) {
    my $entry = $nlist->get (@$added);
    # do something
 }
 foreach my $removed (@{ $diff->removed }) {
    my $entry = $olist->get (@$removed);
    # do something
 }
 foreach my $changed (@{ $diff->changed }) {
    my $oentry = $olist->get (@$changed);
    my $nentry = $nlist->get (@$changed);
    # use/diff $oentry and $nentry as needed
 }

=head1 DESCRIPTION

Instances of this class provides access to the packages list used by
the Lab as caches.

=head1 METHODS

=over 4

=cut

# Private constructor (used by Lintian::Lab::Manifest::diff)
sub _new {
    my ($class, $type, $nlist, $olist, $added, $removed, $changed) = @_;
    my $self = {
        'added'   => $added,
        'removed' => $removed,
        'changed' => $changed,
        'type'    => $type,
        'olist'   => $olist,
        'nlist'   => $nlist,
    };
    bless $self, $class;
    return $self;
}

=item $diff->added

Returns a listref containing the keys of the elements that has been added.

Each element is a listref of keys; this list (when dereferenced) can be
used with the manifest's get method to look up the item.

=item $diff->removed

Returns a listref containing the keys of the elements that has been removed.

Each element is a listref of keys; this list (when dereferenced) can
be used with the manifest's get method to look up the item.

=item $diff->changed

Returns a listref containing the keys of the elements that has been changed.

Each element is a listref of keys; this list (when dereferenced) can
be used with the manifest's get method to look up the item.

=item $diff->nlist

Returns the "new" manifest used to create this diff.  Note the manifest is not
copied and may have been changed since the diff has been created.

=item $diff->olist

Returns the "orig" manifest used to create this diff.  Note the manifest is not
copied and may have been changed since the diff has been created.

=cut

Lintian::Lab::ManifestDiff->mk_ro_accessors(
    qw(added removed changed type nlist olist));

=back

Originally written by Niels Thykier <niels@thykier.net> for Lintian.

=head1 SEE ALSO

lintian(1)

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
