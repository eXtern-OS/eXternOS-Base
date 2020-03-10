# Copyright (C) 2009 Raphael Geissert <atomo64@gmail.com>
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

package Lintian::DepMap;

use strict;
use warnings;

use parent 'Clone';
use Carp qw(croak);
use List::MoreUtils qw(any);

use Lintian::Util qw(internal_error);

=head1 NAME

Lintian::DepMap - Dependencies map/tree creator

=head1 SYNOPSIS

    use Lintian::DepMap;

    my $map = Lintian::DepMap->new;

    # know about A:
    $map->add('A');
    # B depends on A:
    $map->add('B', 'A');

    # prints 'A':
    print $map->selectable;

    # indicate we are working on 'A' (optional):
    $map->select('A');
    # do 'A' ... work work work

    # we are done with A:
    $map->satisfy('A');
    # prints 'B':
    print $map->selectable;


=head1 DESCRIPTION

Lintian::DepMap is a simple dependencies map/tree creator and "resolver".
It works by creating a tree based on the indicated dependencies and destroying
it to resolve it.


Note: in the below documentation a C<node> means a node name; no internal
reference is ever returned and therefore never accepted as a parameter.

=over 4

=item new()

Creates a new Lintian::DepMap object and returns a reference to it.

=cut

sub new {
    my ($class) = @_;
    my $self = {};
    bless($self, $class);
    return $self;
}

=item initialise()

Ensure, by reconstructing if necessary, the map's status is the initial.
That is, partially or fully resolved maps can be restored to its original
state by calling this method.

This can be useful when the same map will be used multiple times.

E.g.

    $map->add('A');
    $map->satisfy('A');
    # prints nothing
    print $map->selectable;
    $map->initialise;
    print $map->selectable;

=cut

#'
sub initialise {
    my $self = shift;

    delete $self->{'selected'};

    while (my ($parent, $childs) = each %{$self->{'satisfied_nodes'}}) {
        if (@{$childs}) {
            for my $child (@{$childs}) {
                $self->add($child, $parent);
            }
        }
        $self->add($parent);
    }
    delete $self->{'satisfied_nodes'};

    return 1;
}

=item add(node[, dependency[, dependency[, ...]]])

Adds the given C<node> to the map marking any second or more parameter as its
dependencies. E.g.

    # A has no dependency:
    $map->add('A');
    # B depends on A:
    $map->add('B', 'A');

=cut

sub add {
    my $self = shift;
    my ($node, @parents) = @_;
    my $parents = 0;

    if (exists($self->{'unknown'}{$node})
        && defined($self->{'unknown'}{$node})) {
        $self->{'known'}{$node} = $self->{'unknown'}{$node};
        delete $self->{'unknown'}{$node};
    }
    $self->{'known'}{$node}++;

    $self->{'nodes'}{$node}{'branches'} = {}
      unless(exists($self->{'nodes'}{$node}{'branches'}));
    $self->{'nodes'}{$node}{'parents'} = {}
      unless(exists($self->{'nodes'}{$node}{'parents'}));

    while (my $parent = pop @parents) {
        $parents = 1;

        if (exists($self->{'known'}{$parent})) {
            $self->{'known'}{$parent}++;
        } else {
            $self->{'unknown'}{$parent}++;
        }

        $self->{'nodes'}{$parent}{'branches'}{$node}
          = $self->{'nodes'}{$node};
        $self->{'nodes'}{$node}{'parents'}{$parent}
          = $self->{'nodes'}{$parent};
    }
    unless ($parents || scalar %{$self->{'nodes'}{$node}{'parents'}}) {
        $self->{'pending'}{$node} = 1;
    } elsif (exists $self->{'pending'}{$node}) {
        delete $self->{'pending'}{$node};
    }
    return 1;
}

=item addp(node[, prefix, dependency[, dependency[, ...]]])

Adds the given C<node> to the map marking any third or more parameters,
after prefixing them with C<prefix>, as its dependencies. E.g.

    # pA and pB have no dependency:
    $map->add('pA');
    $map->add('pA');
    # C depends on pA and pB:
    $map->addp('C', 'p', 'A', 'B');

=cut

sub addp {
    my ($self,$node,$prefix) = (shift,shift,shift);
    my @deps;

    while (my $dep = shift) {
        push @deps, $prefix . $dep;
    }

    return $self->add($node, @deps);
}

=item satisfy(node)

Indicates that the given C<node> has been satisfied/done.

The given C<node> is no longer marked as being selected, if it was;
all of its branches that have no other parent are now selectable()
and all the references to C<node> are deleted except the one from
the known() list.

E.g.

    # A has no dependencies:
    $map->add('A');
    # B depends on A:
    $map->add('B', 'A');
    # we work on A, and we are done:
    $map->satisfy('A');
    # B is now available:
    $map->selectable('B');

B<Note>: shall the requested node not exist this method die()s.

=cut

sub satisfy {
    my $self = shift;
    my $node = shift;

    if (any {$_ eq $node} $self->missing) {
        internal_error(
               "Attempted to mark node '$node' as satisfied but it is not "
              .'reachable, perhaps you forgot to add() it first?');
    }
    if (not exists($self->{'nodes'}{$node})) {
        internal_error(
               "Attempted to mark node '$node' as satisfied but it is not "
              .'reachable, perhaps you forgot to satisfy() its dependencies first?'
        );
    }
    return 0 unless (exists($self->{'pending'}{$node}));

    delete $self->{'selected'}{$node}
      if exists($self->{'selected'}{$node});

    $self->{'satisfied_nodes'}{$node}
      = [keys %{$self->{'nodes'}{$node}{'branches'}}];

    for my $branch (keys %{$self->{'nodes'}{$node}{'branches'}}) {
        delete $self->{'nodes'}{$branch}{'parents'}{$node};
        delete $self->{'nodes'}{$node}{'branches'}{$branch};
        unless (scalar keys %{$self->{'nodes'}{$branch}{'parents'}}) {
            $self->{'pending'}{$branch} = 1;
        }
    }

    delete $self->{'pending'}{$node};
    delete $self->{'nodes'}{$node};
    return 1;
}

=item done(node)

Returns whether the given C<node> has been satisfied/done.

E.g.

    # A has no dependencies:
    $map->add('A');
    # we work on A, and we are done:
    $map->satisfy('A');

    print "A is done!"
        if ($map->done('A'));

=cut

sub done {
    my $self = shift;
    my $node = shift;
    return exists $self->{'satisfied_nodes'}{$node};
}

=item unlink(node)

Removes all references to the given C<node> except for the entry in the
known() table.

B<IMPORTANT>: since all references are deleted it is possible that a node
that depended on C<node> may become available even when it was not expected
to.

B<IMPORTANT>: this operation can B<not> be reversed by the means of
initialise().

E.g.

    $map->add('A');
    # Prints A
    print $map->selectable;
    # we later notice we don't want A
    $map->unlink('A');
    # Prints nothing
    print $map->selectable;

B<Note>: shall the requested node not exist this method die()s.

=cut

sub unlink {
    my $self = shift;
    my $node = shift;

    if (not exists($self->{'nodes'}{$node})) {
        internal_error(
               "Attempted to unlink node '$node' but it cannot be found"
              .', perhaps it has already been satisfied?');
    }

    delete $self->{'pending'}{$node}
      if (exists($self->{'pending'}{$node}));

    delete $self->{'selected'}{$node}
      if (exists($self->{'selected'}{$node}));

    for my $parent (keys %{$self->{'nodes'}{$node}{'parents'}}) {
        delete $self->{'nodes'}{$parent}{'branches'}{$node}
          if exists $self->{'nodes'}{$parent}{'branches'}{$node};
        delete $self->{'nodes'}{$node}{'parents'}{$parent};
    }

    for my $branch (keys %{$self->{'nodes'}{$node}{'branches'}}) {
        delete $self->{'nodes'}{$branch}{'parents'}{$node};
        delete $self->{'nodes'}{$node}{'branches'}{$branch};
    }

    delete $self->{'nodes'}{$node};

    return 1;
}

=item select(node)

Marks the given C<node> as selected to indicate that whatever it represents
is being worked on. Note: this operation is not atomic.

E.g.

    $map->add('A');
    $map->add('B', 'A');
    while($map->pending) {
        for my $node ($map->selectable) {
            $map->select($node);
            # work work work
            $map->satisfy($node);
        }
    }

=cut

sub select {
    my $self = shift;
    my $node = shift;

    if (not exists($self->{'pending'}{$node})) {
        internal_error(
               "Attempted to mark node '$node' as selected but it is not "
              .'known, perhaps its parents are not yet satisfied?');
    }
    return 0 if (exists($self->{'selected'}{$node}));

    $self->{'selected'}{$node} = 1;

    return 1;
}

=item selectable([node])

If a C<node> is specified returns TRUE if it can be select()ed.

B<Note>: already select()ed nodes cannot be re-selected,
i.e. if the given C<node> has already been selected this function will
return FALSE; or any selected item will be omitted from the returned array,
in case no C<node> is specified. 

=cut

sub selectable {
    my $self = shift;
    my $node = shift;

    return (exists $self->{'pending'}{$node}
          and not exists $self->{'selected'}{$node})
      if (defined($node));
    return
      grep {not exists $self->{'selected'}{$_}} keys %{$self->{'pending'}};
}

=item selected([node])

If a C<node> is specified returns TRUE if it is has been selected,
FALSE otherwise.

If no C<node> is specified it returns an array with the name of all the
nodes that have been select()ed but not yet satisfied.

E.g.

    # We are going to work on A
    $map->select('A');
    # Returns true
    $map->selected('A');
    # Prints A
    print $map->selected;

=cut

sub selected {
    my $self = shift;
    my $node = shift;

    return exists $self->{'selected'}{$node}
      if (defined($node));
    return keys %{$self->{'selected'}};
}

=item selectAll()

select()s all the selectable() nodes.

=cut

sub selectAll {
    my $self = shift;

    for my $node ($self->selectable) {
        $self->select($node);
    }
    return;
}

=item parents(node)

Return an array with the name of the parent nodes for the given C<node>.

E.g.

    $map->add('A');
    $map->add('B', 'A');
    # Prints 'A'
    print $map->parents('B');

B<Note>: shall the requested node not exist this method die()s.

=cut

sub parents {
    my $self = shift;
    my $node = shift;

    if (not exists($self->{'nodes'}{$node})) {
        internal_error(
               "Attempted to get the parents of node '$node' but it is not"
              .'known, perhaps you forgot to add() it first?');
    }

    return keys %{$self->{'nodes'}{$node}{'parents'}};
}

=item pending()

Return the number of nodes that can or have already been selected. E.g.

    $map->add('B', 'A');
    # prints 1:
    print $map->pending;
    $map->select('A');
    # prints 1:
    print $map->pending;
    $map->satisfy('A');
    # prints 1 ('B' is now available):
    print $map->pending;

=cut

sub pending {
    my $self = shift;

    return (scalar keys %{$self->{'pending'}});
}

=item known()

Return an array containing the names of nodes that were added. E.g.

    $map->add('B', 'A');
    # prints 'B':
    print $map->known;
    $map->add('A');
    # prints 'A' and 'B':
    print $map->known;

=item known(NODE)

Returns a truth value if NODE is known or C<undef> otherwise.

=cut

sub known {
    my ($self, $node) = @_;

    if (@_ > 1) {
        croak('known(NODE) requires a defined argument')
          if not defined($node);
        return 1 if exists($self->{'known'}{$node});
        return;
    }

    return keys %{$self->{'known'}};
}

=item missing()

Return an array containing the names of nodes that were not added but that
another node depended on it. E.g.

    $map->add('B', 'A');
    # prints 'A':
    print $map->missing;
    $map->add('A');
    # prints nothing:
    print $map->missing;
    # this also works; A depends on 'Z':
    $map->add('A', 'Z');
    # but now this prints 'Z':
    print $map->missing;

=cut

sub missing {
    my $self = shift;

    return keys %{$self->{'unknown'}};
}

=item circular(['deep'])

Returns an array of nodes that have a circular dependency.

E.g.

    $map->add('A', 'B');
    $map->add('B', 'A');
    # Prints A and B
    print $map->circular;

B<Note>: since recursive/deep circular dependencies detection is a bit
more resource expensive it is not the default.

    $map->add('A', 'B');
    $map->add('B', 'C');
    $map->add('C', 'A');
    # No deep/recursive scanning is performed, prints nothing
    print $map->circular;
    # deep scan, prints 'A, B, C'
    print $map->circular('deep');

=cut

sub circular {
    my $self = shift;
    my $deep = shift;
    my @circ;

    $deep = (defined($deep) && $deep eq 'deep');

    if ($deep) {
        my @nodes;
        my ($prev_satisfied, $prev_selected)
          = ($self->{'satisfied_nodes'}, $self->{'selected'});
        while(@nodes = $self->selectable) {
            for my $node (@nodes) {
                $self->satisfy($node);
            }
        }
        # there should be no nodes left:
        @circ = keys %{$self->{'nodes'}};

        $self->{'satisfied_nodes'} = $prev_satisfied;
        $self->{'selected'} = $prev_selected;
        $self->initialise;
    } else {
        for my $node (keys %{$self->{'nodes'}}) {
            my $node_p = $self->{'nodes'}{$node}{'parents'};
            push @circ, grep { exists $node_p->{$_} } keys %{$node_p};
        }
    }

    return @circ;
}

1;

__END__

=back

=head1 AUTHOR

Originally written by Raphael Geissert <atomo64@gmail.com> for Lintian.

=cut

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
