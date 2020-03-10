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

## Represents something Lintian can process (e.g. a deb, dsc or a changes)
package Lintian::Processable;

use parent qw(Class::Accessor::Fast);

use strict;
use warnings;

use Carp qw(croak);

use Lintian::Util qw(strip);

=head1 NAME

Lintian::Processable -- An (abstract) object that Lintian can process

=head1 SYNOPSIS

 use Lintian::Processable::Package;
 
 # Instantiate via Lintian::Processable::Package
 my $proc = Lintian::Processable::Package->new ('lintian_2.5.0_all.deb');
 my $pkg_name = $proc->pkg_name;
 my $pkg_version = $proc->pkg_version;
 # etc.

=head1 DESCRIPTION

Instances of this perl class are objects that Lintian can process (e.g.
deb files).  Multiple objects can then be combined into
L<groups|Lintian::ProcessableGroup>, which Lintian will process
together.

=head1 CLASS METHODS

=over 4

=item new_from_metadata (TYPE, PARAGRAPH[, BASEPATH])

Returns a Lintian::Processable from a PARAGRAPH in a Sources or a
Packages file with the following exception.

If the PARAGRAPH has a field named "pkg_path", then that is used
instead of creating the path from BASEPATH path concatenated with the
TYPE specific field(s).  Hench BASEPATH is optional if and only if,
the paragraph has a field called "pkg_path".

The TYPE parameter determines the type of the processable and is
required.

NB: Optional fields (e.g. "Source" for binaries) may be omitted in
PARAGRAPH as usual.  In this case, the respective values are computed
from the required fields according to the Policy Manual.

=cut

my %KEEP = map { $_ => 1 } qw(
  pkg_name pkg_version pkg_src pkg_src_version pkg_type pkg_path pkg_arch
);
my %KEEP_EXTRA = map { $_ => 1} qw(
  section binary uploaders maintainer area
);

sub new_from_metadata {
    my ($clazz, $pkg_type, $paragraph, $basepath) = @_;
    my $self = {
        %$paragraph # Copy the input data for starters
    };
    my $rename_field = sub {
        my ($oldn, $newn, $default) = @_;
        $self->{$newn} = delete $self->{$oldn};
        if (not defined $self->{$newn} and defined $default) {
            $self->{$newn} = $default;
        }
        croak "Required field $oldn is missing or empty"
          unless defined $self->{$newn} and $self->{$newn} ne '';
    };
    $self->{'pkg_type'} = $pkg_type;
    $rename_field->('package', 'pkg_name');
    $rename_field->('version', 'pkg_version');
    bless $self, $clazz;
    if ($pkg_type eq 'binary' or $pkg_type eq 'udeb') {
        $rename_field->('source', 'pkg_src', $self->pkg_name);
        $rename_field->('architecture', 'pkg_arch');
        if ($self->{'pkg_src'} =~ /^([-+\.\w]+)\s+\((.+)\)$/) {
            $self->{'pkg_src'} = $1;
            $self->{'pkg_src_version'} = $2;
            croak 'Two source-versions given (source + source-version)'
              if exists $self->{'source-version'};
        } else {
            $rename_field->(
                'source-version', 'pkg_src_version', $self->pkg_version
            );
        }
        if (not exists $self->{'pkg_path'}) {
            my $fn = delete $self->{'filename'};
            croak 'Missing required "filename" field'
              unless defined $fn;
            $self->{'pkg_path'} = "$basepath/$fn";
        }
    } elsif ($pkg_type eq 'source') {
        $self->{'pkg_src'} = $self->pkg_name;
        $self->{'pkg_src_version'} = $self->pkg_version;
        $self->{'pkg_arch'} = 'source';
        if (not exists $self->{'pkg_path'}) {
            my $fn = delete $self->{'files'};
            my $dir = delete $self->{'directory'};
            $dir .= '/' if defined $dir;
            $dir //= '';
            foreach my $f (split m/\n/, $fn) {
                strip($f);
                next unless $f && $f =~ m/\.dsc$/;
                my (undef, undef, $file) = split m/\s++/, $f;
                # $dir should end with a slash if it is non-empty.
                $self->{'pkg_path'} = "$basepath/${dir}$file";
                last;
            }
            croak 'dsc file not listed in "Files"'
              unless defined $self->{'pkg_path'};
        }
    } elsif ($pkg_type eq 'changes') {
        # This case is basically for L::Lab::Manifest entries...
        $self->{'pkg_src'} = $self->pkg_name;
        $self->{'pkg_src_version'} = $self->pkg_version;
        $rename_field->('architecture', 'pkg_arch');
        croak '.changes file must have pkg_path set'
          unless defined $self->{'pkg_path'};
    } else {
        croak "Unsupported type $pkg_type";
    }
    # Prune the field list...
    foreach my $k (keys %$self) {
        my $val;
        $val = delete $self->{$k} unless exists $KEEP{$k};
        if (defined $val && exists $KEEP_EXTRA{$k}) {
            $self->{'extra-fields'}{$k} = $val;
        }
    }
    $self->_make_identifier;
    return $self;
}

# Shadow Class::Accessor::Fast - otherwise you get some very "funny" errors
# from Class::Accessor::Fast if you get the constructor wrong.
sub new { croak 'Not implemented'; }

=back

=head1 INSTANCE METHODS

=over 4

=cut

sub _make_identifier {
    my ($self) = @_;
    my $pkg_type = $self->pkg_type;
    my $pkg_name = $self->pkg_name;
    my $pkg_version = $self->pkg_version;
    my $pkg_arch = $self->pkg_arch;
    my $id = "$pkg_type:$pkg_name/$pkg_version";
    if ($pkg_type ne 'source') {
        $pkg_arch =~ s/\s++/_/g; # avoid spaces in ids
        $id .= "/$pkg_arch";
    }
    $self->{identifier} = $id;
    return;
}

=item $proc->pkg_name

Returns the package name.

=item $proc->pkg_version

Returns the version of the package.

=item $proc->pkg_path

Returns the path to the packaged version of actual package.  This path
is used in case the data needs to be extracted from the package.

Note: This may return the path to a symlink to the package.

=item $proc->pkg_type

Returns the type of package (e.g. binary, source, udeb ...)

=item $proc->pkg_arch

Returns the architecture(s) of the package. May return multiple values
from changes processables.  For source processables it is "source".

=item $proc->pkg_src

Returns the name of the source package.

=item $proc->pkg_src_version

Returns the version of the source package.

=item $proc->tainted

Returns a truth value if one or more fields in this Processable is
tainted.  On a best effort basis tainted fields will be sanitized
to less dangerous (but possibly invalid) values.

=item $proc->identifier

Produces an identifier for this processable.  The identifier is
based on the type, name, version and architecture of the package.

=cut

Lintian::Processable->mk_ro_accessors(
    qw(pkg_name pkg_version pkg_src pkg_arch pkg_path pkg_type pkg_src_version tainted identifier)
);

=item $proc->group([$group])

Returns the L<group|Lintian::ProcessableGroup> $proc is in,
if any.  If the processable is not in a group, this returns C<undef>.

Can also be used to set the group of this processable.

=cut

Lintian::Processable->mk_accessors(qw(group));

=item $proc->info

Returns L<$info|Lintian::Collect> element for this processable.

Note: This method must be implemented by sub-classes unless they
provide an "info" field.

=cut

sub info {
    my ($self) = @_;
    return $self->{info} if exists $self->{info};
    croak 'Not implemented.';
}

=item $proc->clear_cache

Discard the info element, so the memory used by it can be reclaimed.
Mostly useful when checking a lot of packages (e.g. on lintian.d.o).

Note: By default this does nothing, but it may (and should) be
overridden by sub-classes.

=cut

sub clear_cache {
    return;
}

=item $proc->get_field ($field[, $def])

Optional method to access a field in the underlying data set.

Returns $def if the field is not present or the implementation does
not have (or want to expose) it.  This method is I<not> guaranteed to
return the same value as "$proc->info->field ($field, $def)".

If C<$def> is omitted is defaults to C<undef>.

Default implementation accesses them via the hashref stored in
"extra-fields" if present.  If the field is present, but not defined
$def is returned instead.

NB: This is mostly an optimization used by L<Lintian::Lab> to avoid
(re-)reading the underlying package data.

=cut

sub get_field {
    my ($self, $field, $def) = @_;
    return $def
      unless exists $self->{'extra-fields'}
      and exists $self->{'extra-fields'}{$field};
    return $self->{'extra-fields'}{$field}//$def;
}

=back

=head1 AUTHOR

Originally written by Niels Thykier <niels@thykier.net> for Lintian.

=head1 SEE ALSO

lintian(1)

L<Lintian::ProcessableGroup>

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
