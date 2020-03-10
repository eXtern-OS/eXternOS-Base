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

## Represents something Lintian can process (e.g. a deb, dsc, buildinfo or a changes)
package Lintian::Processable::Package;

use parent qw(Lintian::Processable Class::Accessor::Fast);

use strict;
use warnings;

use Cwd qw(realpath);
use Carp qw(croak);

use Lintian::Util qw(get_deb_info get_dsc_info);

# Black listed characters - any match will be replaced with a _.
use constant EVIL_CHARACTERS => qr,[/&|;\$"'<>],o;

=head1 NAME

Lintian::Processable::Package -- An object that Lintian can process

=head1 SYNOPSIS

 use Lintian::Processable::Package;
 
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

=item new (FILE[, TYPE])

Creates a processable from FILE.  If TYPE is given, the FILE is
assumed to be that TYPE otherwise the type is determined by the file
extension.

TYPE is one of "binary" (.deb), "udeb" (.udeb), "source" (.dsc) or
"changes" (.changes).

=cut

# internal initialization method.
#  reads values from fields etc.
sub new {
    my ($class, $file, $pkg_type) = @_;
    my $pkg_path;
    my $self;

    if (not defined $pkg_type) {
        if ($file =~ m/\.dsc$/o) {
            $pkg_type = 'source';
        } elsif ($file =~ m/\.deb$/o) {
            $pkg_type = 'binary';
        } elsif ($file =~ m/\.udeb$/o) {
            $pkg_type = 'udeb';
        } elsif ($file =~ m/\.changes$/o) {
            $pkg_type = 'changes';
        } else {
            croak "$file is not a known type of package";
        }
    }

    croak "$file does not exists"
      unless -f $file;

    $pkg_path = realpath($file);
    croak "Cannot resolve $file: $!"
      unless $pkg_path;

    $self = {
        pkg_type => $pkg_type,
        pkg_path => $pkg_path,
        tainted => 0,
    };

    if ($pkg_type eq 'binary' or $pkg_type eq 'udeb'){
        my $dinfo = get_deb_info($pkg_path)
          or croak "could not read control data in $pkg_path: $!";
        my $pkg_name = $dinfo->{package};
        my $pkg_src = $dinfo->{source};
        my $pkg_version = $dinfo->{version};
        my $pkg_src_version = $pkg_version;

        unless ($pkg_name) {
            my $type = $pkg_type;
            $type = 'deb' if $type eq 'binary';
            $pkg_name = _derive_name($pkg_path, $type)
              or croak "Cannot determine the name of $pkg_path";
        }

        # Source may be left out if it is the same as $pkg_name
        $pkg_src = $pkg_name unless (defined $pkg_src && length $pkg_src);

        # Source may contain the version (in parentheses)
        if ($pkg_src =~ m/(\S++)\s*\(([^\)]+)\)/o){
            $pkg_src = $1;
            $pkg_src_version = $2;
        }
        $self->{pkg_name} = $pkg_name;
        $self->{pkg_version} = $pkg_version;
        $self->{pkg_arch} = $dinfo->{architecture};
        $self->{pkg_src} = $pkg_src;
        $self->{pkg_src_version} = $pkg_src_version;
        $self->{'extra-fields'} = $dinfo;
    } elsif ($pkg_type eq 'source'){
        my $dinfo = get_dsc_info($pkg_path)
          or croak "$pkg_path is not valid dsc file";
        my $pkg_name = $dinfo->{source} // '';
        my $pkg_version = $dinfo->{version};
        if ($pkg_name eq '') {
            croak "$pkg_path is missing Source field";
        }
        $self->{pkg_name} = $pkg_name;
        $self->{pkg_version} = $pkg_version;
        $self->{pkg_arch} = 'source';
        $self->{pkg_src} = $pkg_name; # it is own source pkg
        $self->{pkg_src_version} = $pkg_version;
        $self->{'extra-fields'} = $dinfo;
    } elsif ($pkg_type eq 'buildinfo' or $pkg_type eq 'changes'){
        my $cinfo = get_dsc_info($pkg_path)
          or croak "$pkg_path is not a valid $pkg_type file";
        my $pkg_version = $cinfo->{version};
        my $pkg_name = $cinfo->{source}//'';
        unless ($pkg_name) {
            $pkg_name = _derive_name($pkg_path, $pkg_type)
              or croak "Cannot determine the name of $pkg_path";
        }
        $self->{pkg_name} = $pkg_name;
        $self->{pkg_version} = $pkg_version;
        $self->{pkg_src} = $pkg_name;
        $self->{pkg_src_version} = $pkg_version;
        $self->{pkg_arch} = $cinfo->{architecture};
        $self->{'extra-fields'} = $cinfo;
    } else {
        croak "Unknown package type $pkg_type";
    }
    # make sure these are not undefined
    $self->{pkg_version}     = '' unless (defined $self->{pkg_version});
    $self->{pkg_src_version} = '' unless (defined $self->{pkg_src_version});
    $self->{pkg_arch}        = '' unless (defined $self->{pkg_arch});
    # make sure none of the fields can cause traversal.
    for my $field (qw(pkg_name pkg_version pkg_src pkg_src_version pkg_arch)) {
        if ($self->{$field} =~ m,${\EVIL_CHARACTERS},o){
            # None of these fields are allowed to contain a these
            # characters.  This package is most likely crafted to
            # cause Path traversals or other "fun" things.
            $self->{tainted} = 1;
            $self->{$field} =~ s,${\EVIL_CHARACTERS},_,go;
        }
    }
    bless $self, $class;
    $self->_make_identifier;
    return $self;
}

# _derive_name ($file, $ext)
#
# Derive the name from the file name
#  - the name is the part of the basename up to (and excl.) the first "_".
#
# _derive_name ('somewhere/lintian_2.5.2_amd64.changes', 'changes') eq 'lintian'
sub _derive_name {
    my ($file, $ext) = @_;
    my ($name) = ($file =~ m,(?:.*/)?([^_/]+)[^/]*\.$ext$,);
    return $name;
}

# $proc->_ctrl_fields
#
# Return a hashref of the control fields if available.  Used by
# L::Lab::Entry to avoid (re-)loading the fields from the control
# file.
sub _ctrl_fields {
    my ($self) = @_;
    return $self->{'extra-fields'} if exists $self->{'extra-fields'};
    return;
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
