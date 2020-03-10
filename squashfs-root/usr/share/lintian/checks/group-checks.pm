# group-checks -- lintian check script -*- perl -*-

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

package Lintian::group_checks;
use strict;
use warnings;
use autodie;

use Lintian::Data;
use Lintian::Relation;
use Lintian::Tags qw(tag);

sub run {

    my (undef, undef, undef, undef, $group) = @_;

    ## To find circular dependencies, we will first generate Strongly
    ## Connected Components using Tarjan's algorithm
    ##
    ## We are not using DepMap, because it cannot tell how the circles
    ## are made - only that there exists at least 1 circle.

    # The packages a.k.a. nodes
    my (@nodes, %edges, $sccs);
    my $ginfo = $group->info;
    my @procs = $group->get_processables('binary');

    _check_file_overlap(@procs);

    foreach my $proc (@procs) {
        my $deps = $ginfo->direct_dependencies($proc);
        if (scalar @$deps > 0) {
            # it depends on another package - it can cause
            # a circular dependency
            my $pname = $proc->pkg_name;
            push @nodes, $pname;
            $edges{$pname} = [map { $_->pkg_name } @$deps];
            _check_multiarch($proc, $deps);
        }
    }

    # Bail now if we do not have at least two packages depending
    # on some other package from this source.
    return if scalar @nodes < 2;

    $sccs = Lintian::group_checks::Graph->new(\@nodes, \%edges)->tarjans;

    foreach my $comp (@$sccs) {
        # It takes two to tango... erh. make a circular dependency.
        next if scalar @$comp < 2;
        tag 'intra-source-package-circular-dependency', sort @$comp;
    }

    return;
}

sub _check_file_overlap {
    my (@procs) = @_;
    # Sort them for stable output
    my @sorted = sort { $a->pkg_name cmp $b->pkg_name } @procs;
    for (my $i = 0 ; $i < scalar @sorted ; $i++) {
        my $proc = $sorted[$i];
        my $pinfo = $proc->info;
        my @p = grep { $_ } split(m/,/o, $pinfo->field('provides', ''));
        my $prov = Lintian::Relation->new(join(' |̈́ ', $proc->pkg_name, @p));
        for (my $j = $i ; $j < scalar @sorted ; $j++) {
            my $other = $sorted[$j];
            my $oinfo = $other->info;
            my @op = grep { $_ } split(m/,/o, $oinfo->field('provides', ''));
            my $oprov
              = Lintian::Relation->new(join(' | ', $other->pkg_name, @op));
            # poor man's "Multi-arch: same" work-around.
            next if $proc->pkg_name eq $other->pkg_name;

            # $other conflicts/replaces with $proc
            next if $oinfo->relation('conflicts')->implies($prov);
            next if $oinfo->relation('replaces')->implies($proc->pkg_name);

            # $proc conflicts/replaces with $other
            next if $pinfo->relation('conflicts')->implies($oprov);
            next if $pinfo->relation('replaces')->implies($other->pkg_name);

            _overlap_check($proc, $pinfo, $other, $oinfo);
        }
    }
    return;
}

sub _overlap_check {
    my ($a_proc, $a_info, $b_proc, $b_info) = @_;
    foreach my $a_file ($a_info->sorted_index) {
        my $name = $a_file->name;
        my $b_file;
        $name =~ s,/$,,o;
        $b_file = $b_info->index($name) // $b_info->index("$name/");
        if ($b_file) {
            next if $a_file->is_dir and $b_file->is_dir;
            tag 'binaries-have-file-conflict', $a_proc->pkg_name,
              $b_proc->pkg_name, $name;
        }
    }
    return;
}

sub _check_multiarch {
    my ($proc, $deps) = @_;
    my $ma = $proc->info->field('multi-arch', 'no');
    if ($ma eq 'same') {
        foreach my $dep (@$deps) {
            my $dma = $dep->info->field('multi-arch', 'no');
            if ($dma eq 'same' or $dma eq 'foreign') {
                1; # OK
            } else {
                tag 'dependency-is-not-multi-archified',
                  join(q{ },
                    $proc->pkg_name, 'depends on',
                    $dep->pkg_name, "(multi-arch: $dma)");
            }
        }
    } elsif ($ma ne 'same'
        and $proc->info->field('section', 'none') =~ m,(?:^|/)debug$,o) {
        # Debug package that isn't M-A: same, exploit that (non-debug)
        # dependencies is (almost certainly) a package for which the
        # debug carries debug symbols.
        foreach my $dep (@$deps) {
            my $dma = $dep->info->field('multi-arch', 'no');
            if (    $dma eq 'same'
                and $dep->info->field('section', 'none') !~ m,(?:^|/)debug$,o){

                # Debug package isn't M-A: same, but depends on a
                # package that is from same source that isn't a debug
                # package and that is M-A same.  Thus it is not
                # possible to install debug symbols for all
                # (architecture) variants of the binaries.
                tag 'debug-package-for-multi-arch-same-pkg-not-coinstallable',
                  $proc->pkg_name . ' => ' . $dep->pkg_name;
            }
        }
    }
    return;
}

## Encapsulate Tarjan's algorithm in a class/object to keep
## the run sub somewhat sane.  Allow this "extra" package as
## it is not a proper subclass.
#<<< no Perl tidy (it breaks the no critic comment)
package Lintian::group_checks::Graph;  ## no critic (Modules::ProhibitMultiplePackages)
#>>>

sub new {
    my ($type, $nodes, $edges) = @_;
    my $self = { nodes => $nodes, edges => $edges};
    bless $self, $type;
    return $self;
}

sub tarjans {
    my ($self) = @_;
    my $nodes = $self->{nodes};
    $self->{index} = 0;
    $self->{scc} = [];
    $self->{stack} = [];
    $self->{on_stack} = {};
    # The information for each node:
    #  $self->{node_info}{$node}[X], where X is:
    #    0 => index
    #    1 => low_index
    $self->{node_info} = {};
    foreach my $node (@$nodes) {
        $self->_tarjans_sc($node)
          unless defined $self->{node_info}{$node};
    }
    return $self->{scc};
}

sub _tarjans_sc {
    my ($self, $node) = @_;
    my $index = $self->{index};
    my $stack = $self->{stack};
    my $ninfo = [$index, $index];
    my $on_stack = $self->{on_stack};
    $self->{node_info}{$node} = $ninfo;
    $index++;
    $self->{index} = $index;
    push @$stack, $node;
    $on_stack->{$node} = 1;

    foreach my $neighbour (@{ $self->{edges}{$node} }){
        my $nb_info;
        $nb_info = $self->{node_info}{$neighbour};
        if (!defined $nb_info){
            # First time visit
            $self->_tarjans_sc($neighbour);
            # refresh $nb_info
            $nb_info = $self->{node_info}{$neighbour};
            # min($node.low_index, $neigh.low_index)
            $ninfo->[1] = $nb_info->[1] if $nb_info->[1] < $ninfo->[1];
        } elsif (exists $on_stack->{$neighbour})  {
            # Node is in this component
            # min($node.low_index, $neigh.index)
            $ninfo->[1] = $nb_info->[0] if $nb_info->[0] < $ninfo->[1];
        }
    }
    if ($ninfo->[0] == $ninfo->[1]){
        # the "root" node - create the SSC.
        my $component = [];
        my $scc = $self->{scc};
        my $elem = '';
        do {
            $elem = pop @$stack;
            delete $on_stack->{$elem};
            push @$component, $elem;
        } until $node eq $elem;
        push @$scc, $component;
    }
    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
