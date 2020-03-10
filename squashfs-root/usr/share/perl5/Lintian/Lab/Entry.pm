# Lintian::Lab::Entry -- Perl laboratory entry for lintian

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

package Lintian::Lab::Entry;

=head1 NAME

Lintian::Lab::Entry - A package inside the Lab

=head1 SYNOPSIS

 use Lintian::Lab;
 
 my $lab = Lintian::Lab->new ("dir");
 my $lpkg = $lab->get_package ("name", "type", "version", "arch");
 
 # create the entry
 $lpkg->create;
 
 # obtain a Lintian::Collect object.
 my $info = $lpkg->info;
 
 $lpkg->clear_cache;
 
 # Remove package from lab.
 $lpkg->remove;

=head1 DESCRIPTION

This module provides basic access and manipulation about an entry
(i.e. processable) stored in the Lab.  Instances of this class
are not created directly, instead they are returned by various
methods from L<Lintian::Lab>.

=head1 CLASS METHODS

=over 4

=cut

use strict;
use warnings;

use parent qw(Lintian::Processable Class::Accessor::Fast);

use Carp qw(croak);
use Cwd();
use File::Spec;
use Scalar::Util qw(refaddr);
use POSIX qw();

use Lintian::Lab;
use Lintian::Util qw(delete_dir parse_dpkg_control get_dsc_info strip);

# This is the entry format version - this changes whenever the layout of
# entries changes.  This differs from LAB_FORMAT in that LAB_FORMAT
# presents the things "outside" the entry.
use constant LAB_ENTRY_FORMAT => 1;

=item new_from_metadata (PKG_TYPE, METADATA, LAB, BASEDIR)

Overrides same constructor in Lintian::Processable.

Used by L<Lintian::Lab> to load an existing entry from the lab.

=cut

sub new_from_metadata {
    my ($type, $pkg_type, $metadata, $lab, $base_dir) = @_;
    my $self;
    my $pkg_path;
    $pkg_path = $metadata->{'pkg_path'}
      if exists $metadata->{'pkg_path'};
    {
        # Create a phony pkg_path if missing
        local $metadata->{'pkg_path'} = '<PLACEHOLDER>'
          unless exists $metadata->{'pkg_path'};
        $self = $type->SUPER::new_from_metadata($pkg_type, $metadata);
    }
    $self->{lab}      = $lab;
    $self->{info}     = undef; # load on demand.
    $self->{coll}     = {};
    $self->{base_dir} = $base_dir;
    $self->{pkg_path} = $pkg_path; # Could be undef, _init will fix that
    $self->_init;

    return $self;
}

# private constructor (called by Lintian::Lab)
sub _new_from_proc {
    my ($type, $proc, $lab, $base_dir) = @_;
    my $self = {};
    bless $self, $type;
    $self->{pkg_name}        = $proc->pkg_name;
    $self->{pkg_version}     = $proc->pkg_version;
    $self->{pkg_type}        = $proc->pkg_type;
    $self->{pkg_src}         = $proc->pkg_src;
    $self->{pkg_src_version} = $proc->pkg_src_version;
    $self->{pkg_path}        = $proc->pkg_path;
    $self->{lab}             = $lab;
    $self->{info}            = undef; # load on demand.
    $self->{coll}            = {};

    if ($self->pkg_type ne 'source') {
        $self->{pkg_arch} = $proc->pkg_arch;
    } else {
        $self->{pkg_arch} = 'source';
    }

    $self->{base_dir} = $base_dir;

    $self->_init(1);
    $self->_make_identifier;

    if ($proc->isa('Lintian::Processable::Package')) {
        my $ctrl = $proc->_ctrl_fields;
        if ($ctrl) {
            # The processable has already loaded the fields, cache them to save
            # info from doing it later...
            $self->{info}
              = Lintian::Collect->new($self->pkg_name, $self->pkg_type,
                $self->base_dir, $ctrl);
        }
    }
    return $self;
}

=back

=head1 INSTANCE METHODS

=over 4

=item base_dir

Returns the base directory of this package inside the lab.

=item lab

Returns a reference to the laboratory related to this entry.

=cut

Lintian::Lab::Entry->mk_ro_accessors(qw(lab base_dir));

=item from_lab (LAB)

Returns a truth value if this entry is from LAB.

=cut

sub from_lab {
    my ($self, $lab) = @_;
    return refaddr $lab eq refaddr $self->{'lab'} ? 1 : 0;
}

=item info

Returns the L<info|Lintian::Collect> object associated with this entry.

Overrides info from L<Lintian::Processable>.

=cut

sub info {
    my ($self) = @_;
    my $info;
    $info = $self->{info};
    if (!defined $info) {
        croak('Cannot load info, entry does not exist') unless $self->exists;

        $info = Lintian::Collect->new($self->pkg_name, $self->pkg_type,
            $self->base_dir);
        $self->{info} = $info;
    }
    return $info;
}

=item clear_cache

Clears any caches held; this includes discarding the L<info|Lintian::Collect> object.

Overrides clear_cache from L<Lintian::Processable>.

=cut

sub clear_cache {
    my ($self) = @_;
    delete $self->{info};
    return;
}

=item remove

Removes all unpacked parts of the package in the lab.  Returns a truth
value if successful.

=cut

sub remove {
    my ($self) = @_;
    my $basedir = $self->{base_dir};
    return 1 if(!-e $basedir);
    $self->clear_cache;
    unless(delete_dir($basedir)) {
        return 0;
    }
    $self->{lab}->_entry_removed($self);
    return 1;
}

=item exists

Returns a truth value if the entry exists.

=cut

sub exists {
    my ($self) = @_;
    my $pkg_type = $self->{pkg_type};
    my $base_dir = $self->{base_dir};

    # Check if the relevant symlink exists.
    if ($pkg_type eq 'changes'){
        return 1 if -l "$base_dir/changes";
    } elsif ($pkg_type eq 'binary' or $pkg_type eq 'udeb') {
        return 1 if -l "$base_dir/deb";
    } elsif ($pkg_type eq 'source'){
        return 1 if -l "$base_dir/dsc";
    }

    # No unpack level and no symlink => the entry does not
    # exist or it is too broken in its current state.
    return 0;
}

=item create

Creates a minimum entry, in which collections and checks
can be run.  Note if it already exists, then this will do
nothing.

=cut

sub create {
    my ($self) = @_;
    my $pkg_type = $self->{pkg_type};
    my $base_dir = $self->{base_dir};
    my $pkg_path = $self->{pkg_path};
    my $lab      = $self->{lab};
    my $link;
    my $madedir = 0;

    if (not -d $base_dir) {
        # In the pool we may have to create multiple directories. On
        # error we only remove the "top dir" and that is enough.
        system('mkdir', '-p', $base_dir) == 0
          or croak "mkdir -p $base_dir failed";
        $madedir = 1;
    } else {
        # If $base_dir exists, then check if the entry exists
        # - this is optimising for "non-existence" which is
        #   often the common case.
        return 0 if $self->exists;
    }
    if ($pkg_type eq 'changes'){
        $link = "$base_dir/changes";
    } elsif ($pkg_type eq 'binary' or $pkg_type eq 'udeb') {
        $link = "$base_dir/deb";
    } elsif ($pkg_type eq 'source'){
        $link = "$base_dir/dsc";
    } else {
        croak "create cannot handle $pkg_type";
    }
    unless (symlink($pkg_path, $link)){
        my $err = $!;
        # "undo" the mkdir if the symlink fails.
        rmdir $base_dir  if $madedir;
        $! = $err;
        croak "symlinking $pkg_path failed: $!";
    }
    if ($pkg_type eq 'source'){
        # If it is a source package, pull in all the related files
        #  - else unpacked will fail or we would need a separate
        #    collection for the symlinking.
        my (undef, $dir, undef) = File::Spec->splitpath($pkg_path);
        for my $fs (split(m/\n/o, $self->info->field('files'))) {
            strip($fs);
            next if $fs eq '';
            my @t = split(/\s+/o,$fs);
            next if ($t[2] =~ m,/,o);
            symlink("$dir/$t[2]", "$base_dir/$t[2]")
              or croak("cannot symlink file $t[2]: $!");
        }
    }
    $lab->_entry_created($self);
    return 1;
}

=item coll_version (COLL)

Returns the version of the collection named COLL, if that
COLL has been marked as finished.

Returns the empty string if COLL has not been marked as finished.

Note: The version can be 0.

=cut

sub coll_version {
    my ($self, $coll) = @_;
    return $self->{coll}{$coll}//'';
}

=item is_coll_finished (COLL, VERSION)

Returns a truth value if the collection COLL has been completed and
its version is at least VERSION.  The versions are assumed to be
integers (the comparison is performed with ">=").

This returns 0 if the collection COLL has not been marked as
finished.

=cut

sub is_coll_finished {
    my ($self, $coll, $version) = @_;
    my $c = $self->coll_version($coll);
    return 0 if $c eq '';
    return $c >= $version;
}

# $lpkg->_mark_coll_finished ($coll, $version)
#
# non-public method to mark a collection as complete
sub _mark_coll_finished {
    my ($self, $coll, $version) = @_;
    $self->{coll}{$coll} = $version;
    return 1;
}

# $lpkg->_clear_coll_status ($coll)
#
# Removes the notion that $coll has been finished.
sub _clear_coll_status {
    my ($self, $coll) = @_;
    delete $self->{coll}{$coll};
    return 1;
}

=item update_status_file

Flushes the cached changes of which collections have been completed.

This should also be called for new entries to create the status file.

=cut

sub update_status_file {
    my ($self) = @_;
    my $file;
    my @sc;

    unless ($self->exists) {
        $! = POSIX::ENOENT;
        return 0;
    }

    $file = $self->base_dir . '/.lintian-status';
    open my $sfd, '>', $file or return 0;
    print $sfd 'Lab-Entry-Format: ' . LAB_ENTRY_FORMAT . "\n";
    # Basic package meta-data - this is redundant, but having it may
    # greatly simplify a migration or detecting a broken lab later.
    print $sfd 'Package: ' . $self->pkg_name, "\n";
    print $sfd 'Version: ' . $self->pkg_version, "\n";
    # Add Source{,-Version} if it is different from Package/Version
    print $sfd 'Source: ' . $self->pkg_src, "\n"
      unless $self->pkg_src eq $self->pkg_name;
    print $sfd 'Source-Version: ' . $self->pkg_src_version, "\n"
      unless $self->pkg_src_version eq $self->pkg_version;
    print $sfd 'Architecture: ' . $self->pkg_arch, "\n"
      if $self->pkg_type ne 'source';
    print $sfd 'Package-Type: ' . $self->pkg_type, "\n";

    @sc = sort keys %{ $self->{coll} };
    print $sfd "Collections: \n";
    print $sfd ' ' . join(",\n ", map { "$_=$self->{coll}{$_}" } @sc);
    print $sfd "\n\n";
    close $sfd or return 0;
    return 1;
}

sub _init {
    my ($self, $newentry) = @_;
    my $base_dir = $self->base_dir;
    my (@data, $head, $coll, $fd, $exists);

    eval {
        use autodie qw(open);
        open($fd, '<', "$base_dir/.lintian-status");
        # If the status file exists, then so does the
        # entry.
        $exists = 1;
    };
    if (my $err = $@) {
        die($err) if $err->errno != POSIX::ENOENT;
        # If it is a new entry, we assume it does not exist if
        # .lintian-status absent.  In practise, it does not
        # change the outcome for new entries and it saves
        # a stat from calling exists().
        $exists = $self->exists if not $newentry;
    } else {
        @data = parse_dpkg_control($fd);
        close($fd);
    }

    if ($newentry) {
        my $pkg_path = $self->pkg_path;
        croak "$pkg_path does not exist." unless -e $pkg_path;
    } else {
        # This error should not happen unless someone (read: me) breaks
        # Lintian::Lab::get_package
        my $pkg_type = $self->pkg_type;
        my $link;
        if (not $exists) {
            # This happens with the metadata gets out of sync with reality.
            # (e.g. unclean close).  Solve it by purging the entry.
            $self->remove;
            # Ensure the lab knows the entry us gone.  Depending on how
            # "missing" the entry is, remove might fail to do it for us.
            $self->{'lab'}->_entry_removed($self);
            # Use die as croak insists on adding " at <...>"
            die("entry-disappeared\n");
        }
        $link = 'deb' if $pkg_type eq 'binary' or $pkg_type eq 'udeb';
        $link = 'dsc' if $pkg_type eq 'source';
        $link = 'changes' if $pkg_type eq 'changes';

        croak "Unknown package type $pkg_type" unless $link;
        if (not $self->pkg_path) {
            # This case shouldn't happen unless the entry is missing
            # from the metadata.
            my $linkp = "$base_dir/$link";
            # Resolve the link if possible, but else just fall back to the link
            # - this is not safe in case of a "delete and create", but if
            #   abs_path fails odds are the package cannot be read anyway.
            $self->{pkg_path} = Cwd::abs_path("$base_dir/$link")
              // "$base_dir/$link";
        }
    }

    return unless $exists;
    $head = $data[0];

    # Check that we know the format.
    return unless (LAB_ENTRY_FORMAT eq ($head->{'lab-entry-format'}//''));

    $coll = $head->{'collections'}//'';
    $coll =~ s/\n/ /go;
    foreach my $c (split m/\s*,\s*+/o, strip($coll)) {
        my ($cname, $cver) = split m/\s*=\s*/, $c;
        $self->_mark_coll_finished($cname, $cver);
    }
    return;
}

=back

=head1 AUTHOR

Niels Thykier <niels@thykier.net>

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
