# -*- perl -*-
# Lintian::Path::FSInfo -- File System information for Lintian::Path

# Copyright (C) 2014 Niels Thykier
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

package Lintian::Path::FSInfo;

use strict;
use warnings;
use parent qw(Class::Accessor::Fast);

use Carp qw(confess);

use Scalar::Util qw(weaken);

=head1 NAME

Lintian::Path::FSInfo - File System information for L<Lintian::Path>

=head1 SYNOPSIS

  my $l_path;  # A L::Path object
  my $fs_info; # A L::Path::FSInfo object
  if ($fs_info->has_anchored_root_dir) {
    # The "root" dir is anchored and paths starting with "/" can
    # trivially be resolved (as relative to the "root" dir).
  } else {
    # The "root" dir is undefined and paths starting with "/" *cannot*
    # be resolved.
  }

=head1 CLASS METHODS

=over 4

=item new(OPTS)

Internal constructor (used by Lintian::Collect::Package)

=cut

sub new {
    my ($class, %opts) = @_;
    weaken($opts{'_collect'});
    return bless(\%opts, $class);
}

=back

=head1 INSTANCE METHODS

=over 4

=item _underlying_fs_path(PATH)

Given PATH, a L<Lintian::Path>, obtain the underlying file system path
that it represents.

=cut

sub _underlying_fs_path {
    my ($self, $path) = @_;
    my $fs_root;
    my $fname = $path->name;
    if ($fs_root = $self->{'_root_fs_path'}) {
        return join('/', $fs_root, $fname) if $fname ne q{};
        return $fs_root;
    }
    my $collect = $self->{'_collect'};
    my $collect_sub = $self->{'_collect_path_sub'};
    if (not defined($collect_sub)) {
        confess($self->name . ' does not have an underlying FS object');
    }
    {
        # Disable the deprecation warning from (e.g.) control.  It is
        # not meant for this call.
        no warnings qw(deprecated);
        $fs_root = $collect->$collect_sub();
    };
    $self->{'_root_fs_path'} = $fs_root;
    return join('/', $fs_root, $fname) if $fname ne q{};
    return $fs_root;
}

=item _file_info(PATH)

Given PATH, a L<Lintian::Path>, obtain the output from file(1) about
the file, if it has been collected.  Throws an error if it not
available.

=cut

sub _file_info {
    my ($self, $path) = @_;
    my $collect = $self->{'_collect'};
    my $collect_sub = $self->{'_collect_file_info_sub'};
    if (not defined($collect_sub)) {
        confess($path->name . ' has not had collected file(1) info');
    }
    return $collect->$collect_sub($path->name);
}

=item has_anchored_root_dir

Returns a truth value if the "root" directory is anchored and is
defined by the path string "/".  In such cases, paths starting with
"/" are well-defined semantically and are relative to the root
directory rather than the "current" directory.

On the other hand, if this returns a non-truth value, the "root"
directory is I<not> well-defined and no path starting with "/" can be
resolved logically.

=cut

Lintian::Path::FSInfo->mk_ro_accessors(qw(has_anchored_root_dir));

=back

=head1 AUTHOR

Originally written by Niels Thykier <niels@thykier.net> for Lintian.

=head1 SEE ALSO

lintian(1), Lintian::Path(3), Lintian::Collect(3),
Lintian::Collect::Binary(3), Lintian::Collect::Source(3)

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et

