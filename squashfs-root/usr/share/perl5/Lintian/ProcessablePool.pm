# Copyright (C) 2011 Niels Thykier <niels@thykier.net>
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

## Represents a pool of processables (Lintian::Processable)
package Lintian::ProcessablePool;

use strict;
use warnings;

use Carp qw(croak);

use Cwd();
use Lintian::Util;

use Lintian::Processable::Package;
use Lintian::ProcessableGroup;

=head1 NAME

Lintian::ProcessablePool -- Pool of processables

=head1 SYNOPSIS

 use Lintian::ProcessablePool;
 
 my $pool = Lintian::ProcessablePool->new;
 $pool->add_file('foo.changes');
 $pool->add_file('bar.dsc');
 $pool->add_file('baz.deb');
 $pool->add_file('qux.buildinfo');
 foreach my $gname ($pool->get_group_names){
    my $group = $pool->get_group($gname);
    process($gname, $group);
 }

=head1 METHODS

=over 4

=item Lintian::ProcessablePool->new ([LAB])

Creates a new empty pool.

If LAB is given, it is assumed to be a Lintian::Lab.  In this case,
any processable added to this pool will be stored as a
L<lab entry|Lintian::Lab::Entry> from LAB.

=cut

sub new {
    my ($class, $lab) = @_;
    my $self = {
        'lab' => $lab,
        'groups' => {},
    };
    bless $self, $class;
    return $self;
}

=item $pool->add_file($file)

Adds a file to the pool.  The $file will be turned into a
L<processable|Lintian::Processable> and grouped together with other
processables from the same source package (if any).

=cut

sub add_file {
    my ($self, $file) = @_;
    if ($file =~ m/\.(buildinfo|changes)$/o){
        my $type = $1;
        croak "$file does not exist" unless -f $file;
        my $pkg_path = Cwd::abs_path($file);
        croak "Cannot resolve $file: $!" unless $pkg_path;
        return $self->_add_file($type, $pkg_path);
    }

    my $proc = Lintian::Processable::Package->new($file);
    return $self->add_proc($proc);
}

=item $pool->add_proc ($proc)

Adds a L<processable|Lintian::Processable> to the pool.

=cut

sub add_proc {
    my ($self, $proc) = @_;
    my ($group, $groupid);
    my $pkg_type = $proc->pkg_type;

    if ($proc->tainted) {
        warn(
            sprintf(
                "warning: tainted %1\$s package '%2\$s', skipping\n",
                $pkg_type, $proc->pkg_name
            ));
        return 0;
    }
    $groupid = $self->_get_group_id($proc);
    $group = $self->{groups}{$groupid};
    if (defined $group){
        if ($pkg_type eq 'source'){
            # if this is a source pkg, then this is a duplicate
            # assuming the group already has a source package.
            return 0 if defined $group->get_source_processable;
        }
        # else add the binary/udeb proc to the group
        return $group->add_processable($proc);
    } else {
        # Create a new group
        $group = Lintian::ProcessableGroup->new($self->{'lab'});
        $group->add_processable($proc);
        $self->{groups}{$groupid} = $group;
    }
    # add it to the "unprocessed"/"seen" map.
    return 1;
}

=item $pool->get_group_names

Returns the name of all the groups in this pool.

Do not modify the list nor its contents.

=cut

sub get_group_names{
    my ($self) = @_;
    return keys %{ $self->{groups} };
}

=item $pool->get_group($name)

Returns the group called $name or C<undef>
if there is no group called $name.

=cut

sub get_group{
    my ($self, $group) = @_;
    return $self->{groups}{$group};
}

=item $pool->get_groups

Returns all the groups in the pool.

Do not modify the list nor its contents.

=cut

sub get_groups{
    my ($self) = @_;
    my $groups = $self->{groups};
    if (scalar keys %$groups) {
        return values %$groups;
    }
    return ();
}

=item $pool->empty

Returns true if the pool is empty.

=cut

sub empty{
    my ($self) = @_;
    return scalar keys %{ $self->{groups} } < 1;
}

#### Internal subs ####

sub _add_file{
    my ($self, $type, $pkg_path) = @_;
    my $group = Lintian::ProcessableGroup->new($self->{'lab'}, $pkg_path);
    my $proc;
    if ($type eq 'buildinfo') {
        $proc = $group->get_buildinfo_processable;
    } elsif ($type eq 'changes') {
        $proc = $group->get_changes_processable;
    }
    my $gid = $self->_get_group_id($proc);
    my $ogroup = $self->{groups}{$gid};
    if (defined($ogroup)){
        # Group already exists...
        my $added = 0;
        # Merge architectures/packages ...
        # Accept all new

        if ($type eq 'buildinfo'
            && !defined($ogroup->get_buildinfo_processable)) {
            $ogroup->add_processable($proc);
            $added = 1;
        }elsif ($type eq 'changes'
            && !defined($ogroup->get_changes_processable)) {
            $ogroup->add_processable($proc);
            $added = 1;
        }

        if (  !defined $ogroup->get_source_processable
            && defined $group->get_source_processable){
            $ogroup->add_processable($group->get_source_processable);
            $added = 1;
        }
        foreach my $bin ($group->get_binary_processables){
            # New binary package ?
            my $was_new = $ogroup->add_processable($bin);
            $added ||= $was_new;
        }
        return $added;
    } else {
        $self->{groups}{$gid} = $group;
    }
    return 1;
}

# Fetches the group id for a package
#  - this id is based on the name and the version of the
#    src-pkg.
sub _get_group_id{
    my ($self, $pkg) = @_;
    my $id = $pkg->pkg_src;
    $id .= '/' . $pkg->pkg_src_version;
    return $id;
}

=back

=head1 AUTHOR

Originally written by Niels Thykier <niels@thykier.net> for Lintian.

=head1 SEE ALSO

lintian(1)

L<Lintian::Processable>

L<Lintian::ProcessableGroup>

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
