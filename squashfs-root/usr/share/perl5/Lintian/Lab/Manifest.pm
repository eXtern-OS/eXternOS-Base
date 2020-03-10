# Lintian::Lab::Manifest -- Lintian Lab manifest

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

package Lintian::Lab::Manifest;

use strict;
use warnings;
use autodie;

use parent qw(Class::Accessor::Fast Clone);

use Carp qw(croak);

=head1 NAME

Lintian::Lab::Manifest -- Lintian Lab manifest

=head1 SYNOPSIS

 use Lintian::Lab::Manifest;
 
 my $plist = Lintian::Lab::Manifest->new ('binary');
 # Read the file
 $plist->read_list('info/binary-packages');
 # fetch the entry for lintian (if any)
 my $entry = $plist->get('lintian', '2.5.2', 'all');
 if ( $entry && exits $entry->{'version'} ) {
    print "Lintian has version $entry->{'version'}\n";
 }
 # delete all lintian entries
 $plist->delete('lintian');
 # Write to file if changed
 if ($plist->dirty) {
    $plist->write_list('info/binary-packages');
 }

=head1 DESCRIPTION

Instances of this class provide access to the packages list used by
the lab as caches.

The data structure is basically a tree (using hashes).  For binaries
is looks (something) like:

 $self->{'state'}{$name}{$version}{$architecture}

The (order of the) fields used in the tree are listed in the
@{BIN,SRC,CHG}_QUERY lists below.  The fields may (and generally do)
differ between package types.

=head1 CLASS METHODS

=over 4

=cut

# these banner lines have to be changed with every incompatible change of the
# binary and source list file formats
use constant BINLIST_FORMAT =>
  q{Lintian's list of binary packages in the archive--V5};
use constant SRCLIST_FORMAT =>
  q{Lintian's list of source packages in the archive--V5};
use constant BLDLIST_FORMAT =>
  q{Lintian's list of buildinfo packages in the archive--V1};
use constant CHGLIST_FORMAT =>
  q{Lintian's list of changes packages in the archive--V1};

# List of fields in the formats and the order they appear in
#  - for internal usage to read and write the files

# source package lists
my @SRC_FILE_FIELDS = (
    'source','version','maintainer','uploaders',
    'area','binary','file','timestamp',
);

# binary/udeb package lists
my @BIN_FILE_FIELDS = (
    'package','version','source','source-version',
    'architecture','file','timestamp','area',
);

# buildinfo packages lists
my @BLD_FILE_FIELDS = ('source','version','architecture','file','timestamp',);

# changes packages lists
my @CHG_FILE_FIELDS = ('source','version','architecture','file','timestamp',);

# List of fields (in order) of fields used to look up the package in the
# manifest.  The field names matches those used in the list above.

my @SRC_QUERY = ('source','version',);

my @GROUP_QUERY = ('source','version','identifier',);

my @BIN_QUERY = ('package','version','architecture',);

my @BLD_QUERY = ('source','version','architecture',);

my @CHG_QUERY = ('source','version','architecture',);

my %TYPE2INFO = (
    'source' => {
        'file-fields'  => \@SRC_FILE_FIELDS,
        'file-header'  => SRCLIST_FORMAT,
        'query-fields' => \@SRC_QUERY
    },
    'binary' => {
        'file-fields'  => \@BIN_FILE_FIELDS,
        'file-header'  => BINLIST_FORMAT,
        'query-fields' => \@BIN_QUERY
    },
    'buildinfo' => {
        'file-fields'  => \@BLD_FILE_FIELDS,
        'file-header'  => BLDLIST_FORMAT,
        'query-fields' => \@BLD_QUERY
    },
    'changes' => {
        'file-fields'  => \@CHG_FILE_FIELDS,
        'file-header'  => CHGLIST_FORMAT,
        'query-fields' => \@CHG_QUERY
    },
    'GROUP' => {
        'file-fields'  => undef, # Never written to disk
        'file-header'  => undef, # Never written to disk
        'query-fields' => \@GROUP_QUERY
    },
);

# udeb behave exactly like binary, so share the underlying table
#  \o/  ~50 bytes saved!
$TYPE2INFO{'udeb'} = $TYPE2INFO{'binary'};

=item new (TYPE[, GROUPING])

Creates a new packages list for a certain type of packages.  This type
defines the format of the files.

The known types are:
 * binary
 * changes
 * source
 * udeb
 * GROUP

If TYPE is GROUP, then GROUPING should be omitted.

=cut

sub new {
    my ($class, $pkg_type, $grouping) = @_;
    my $self = {
        'type'  => $pkg_type,
        'dirty' => 0,
        'state' => {},
        'grouping' => $grouping,
    };
    bless $self, $class;
    return $self;
}

=back

=head1 INSTANCE METHODS

=over 4

=item dirty

Returns a truth value if the manifest has changed since it was last
written.

=item type

Returns the type of packages that this manifest has information about.
(one of binary, udeb, source or changes)

=cut

Lintian::Lab::Manifest->mk_ro_accessors(qw(dirty type));

=item read_list (FILE)

Reads a manifest from FILE.  Any records already in the manifest will
be discarded before reading the contents.

On success, this will clear the L</dirty> flag and on error it will
croak.

=cut

sub read_list {
    my ($self, $file) = @_;
    my $type = $self->type;
    croak 'Cannot read a GROUP manifest' if $type eq 'GROUP';

    # Accept a scalar (as an "in-memory file") - write_list does the same
    if (my $r = ref $file) {
        croak 'Attempt to pass non-scalar ref to read_list'
          unless $r eq 'SCALAR';
    } else {
        # FIXME: clear the manifest if -s $file
        return unless -s $file;
    }

    my ($header, $fields, $qf)
      = @{$TYPE2INFO{$type}}{'file-header', 'file-fields', 'query-fields'};

    $self->{'state'} = $self->_do_read_file($file, $header, $fields, $qf);
    $self->_mark_dirty(0);
    return 1;
}

=item write_list (FILE)

Writes the manifest to FILE.

On success, this will clear the L</dirty> flag and on error it will
croak.

On error, the contents of FILE are undefined.

=cut

sub write_list {
    my ($self, $file) = @_;
    my $type = $self->type;
    croak 'Cannot write a GROUP manifest' if $type eq 'GROUP';
    my ($header, $fields) = @{$TYPE2INFO{$type}}{'file-header', 'file-fields'};
    my $visitor;

    open(my $fd, '>', $file);
    print $fd "$header\n";

    $visitor = sub {
        my ($entry) = @_;
        return if exists $entry->{'_transient'};
        my %values = %$entry;
        print $fd join(';', @values{@$fields}) . "\n";
    };

    $self->visit_all($visitor);

    close($fd);
    $self->_mark_dirty(0);
    return 1;
}

=item visit_all (VISITOR[, KEY1, ..., KEYN])

Visits entries and passes them to VISITOR.  If any keys are passed they
are used to reduce the search.  See get for a list of (common) keys.

The VISITOR is called as:

 VISITOR->(ENTRY, KEYS)

where ENTRY is the entry and KEYS are the keys to be used to look up
this entry via get method.  So for the lintian 2.5.2 binary the keys
would be something like:
 ('lintian', '2.5.2', 'all')

=cut

sub visit_all {
    my ($self, $visitor, @keys) = @_;
    my $root;
    my $type = $self->type;
    my $qf = $TYPE2INFO{$type}{'query-fields'};

    if (@keys) {
        $root = $self->get(@keys);
        return unless $root;
        if (scalar @$qf == scalar @keys) {
            # If we are given an exact match, just visit that and
            # stop.
            $visitor->($root, @keys);
            return;
        }
    } else {
        $root = $self->{'state'};
    }

    $self->_recurse_visit($root, $visitor, scalar @$qf - 1, @keys);
    return;
}

=item get (KEYS...)

Fetches the entry for KEYS (if any).  Returns C<undef> if the entry is
not known.  If KEYS is exactly one item, it is assumed to be a
L<Lintian::Processable> and the correct keys are extracted from it.

Otherwise, the keys are (in general and in order):

=over 4

=item package/source

=item version

=item architecture

except for source packages

=back

=cut

sub get {
    my ($self, @keys) = @_;
    my $cur = $self->{'state'};
    my $type = $self->type;
    my $qf = $TYPE2INFO{$type}{'query-fields'};
    my $max = scalar @$qf;
    @keys = $self->_make_keys($keys[0])
      if scalar(@keys) == 1 && ref($keys[0]);
    $max = scalar @keys if scalar @keys < $max;
    for (my $i = 0 ; $i < $max ; $i++) {
        my $key = $keys[$i];
        $cur = $cur->{$key};
        return unless defined $cur;
    }
    return $cur;
}

sub _make_keys {
    my ($self, $entry) = @_;
    my @keys = ($entry->pkg_name, $entry->pkg_version);
    push @keys, $entry->pkg_arch if $entry->pkg_type ne 'source';
    return @keys;
}

=item set (ENTRY)

Inserts ENTRY into the manifest.  This may replace an existing entry.

Note: The interesting fields from ENTRY are copied, so later changes
to ENTRY will not affect the data in the manifest.

=cut

sub set {
    my ($self, $entry) = @_;
    my $type = $self->type;
    croak 'Cannot alter a GROUP manifest directly'
      if $type eq 'GROUP';
    my %pdata;
    my ($fields, $qf) = @{$TYPE2INFO{$type}}{'file-fields', 'query-fields'};

    # Copy the relevant fields - ensuring all fields are defined.
    foreach my $field (@$fields) {
        my $val = $entry->{$field} // '';
        # Avoid some problematic characters that would break the file
        # format.
        $val =~ tr/;\n/_ /;
        $pdata{$field} = $val;
    }
    $self->_make_alias_fields(\%pdata);

    $self->_do_set($qf, \%pdata);
    $self->_mark_dirty(1);
    return 1;
}

=item set_transient_marker (TRANSIENT, KEYS...)

Set or clear transient flag.  Transient entries are not written to the
disk (i.e. They will not appear in the file created/written by
L</write_list (FILE)>).  KEYS is passed as is passed to
L</get (KEYS...)>.

By default all entries are persistent.

=cut

sub set_transient_marker {
    my ($self, $marker, @keys) = @_;
    my $entry = $self->get(@keys);
    return unless $entry;
    $self->{'_transient'} = 1 if $marker;
    delete $self->{'_transient'} unless $marker;
    return;
}

=item delete (KEYS...)

Removes the entry/entries found by KEYS (if any).  KEYS must contain
at least one item - if the list of keys cannot uniquely identify a single
element, all "matching" elements will be removed.  Examples:

 # Delete the gcc-4.6 entry at version 4.6.1-4 that is also architecture i386
 $manifest->delete ('gcc-4.6', '4.6.1-4', 'i386');
 
 # Delete all gcc-4.6 entries at version 4.6.1-4 regardless of their
 # architecture
 $manifest->delete ('gcc-4.6', '4.6.1-4');
 
 # Delete all gcc-4.6 entries regardless of version and architecture
 $manifest->delete ('gcc-4.6')

If KEYS is exactly one item, it is assumed to be a
L<Lintian::Processable>.  If so, the proper keys will be extracted
from that processable and (if present) that one element will be
removed.

This will mark the list as dirty if an element was removed.  If it returns
a truth value, an element was removed - otherwise it will return 0.

See L</get (KEYS...)> for the key names.

=cut

sub delete {
    my ($self, @keys) = @_;
    croak 'Cannot alter a GROUP manifest directly'
      if $self->type eq 'GROUP';
    return $self->_do_delete(@keys);
}

sub _do_delete {
    my ($self, @keys) = @_;
    @keys = $self->_make_keys($keys[0]) if scalar @keys == 1;
    # last key, that is what we will remove :)
    my $lk = pop @keys;
    my $hash;

    return 0 unless defined $lk;

    if (@keys) {
        $hash = $self->get(@keys);
    } else {
        $hash = $self->{'state'};
    }

    if (defined $hash && exists $hash->{$lk}) {
        my $entry = delete $hash->{$lk};
        $self->_mark_dirty(1);
        if (my $grouping = $self->{'grouping'}) {
            my @keys = (
                $entry->{'source'},
                $entry->{'source-version'},
                $entry->{'identifier'});
            $grouping->_do_delete(@keys);
        }
        return 1;
    }
    return 0;
}

=item diff (MANIFEST)

Returns a L<diff|Lintian::Lab::ManifestDiff> between this manifest and
MANIFEST.

This instance is considered the "original" and MANIFEST is "new"
version of the manifest.  (See the olist and nlist methods of
L<Lintian::Lab::ManifestDiff> for more information.

=cut

sub diff {
    my ($self, $other) = @_;
    croak 'Cannot diff a GROUP manifest' if $self->type eq 'GROUP';
    my ($copy, @changed, @added, @removed, $visitor);
    unless ($self->{'type'} eq $other->{'type'}) {
        my $st = $self->{'type'};
        my $ot = $other->{'type'};
        croak "Diffing incompatible types ($st != $ot)";
    }
    $copy = $self->clone;

    $visitor = sub {
        my ($ov, @keys) = @_;
        my $sv = $copy->get(@keys);
        unless (defined $sv) {
            push @added, \@keys;
            return;
        }
        if (  $sv->{'version'} ne $ov->{'version'}
            ||$sv->{'timestamp'} ne $ov->{'timestamp'}) {
            push @changed, \@keys;
        }
        # Remove the entry from $copy
        $copy->delete(@keys);
    }; # End of visitor sub

    # Find all the added and changed entries - since $visitor removes
    # all entries it finds from $copy, $copy will contain the elements
    # that are only in $self after this call.
    $other->visit_all($visitor);
    # Thus we can just add all of these entries to @removed.  :)
    $copy->visit_all(sub { my (undef, @keys) = @_; push @removed, \@keys; });

    require Lintian::Lab::ManifestDiff;

    return Lintian::Lab::ManifestDiff->_new($self->{'type'}, $other, $self,
        \@added, \@removed, \@changed);
}

### Internal methods ###

# $plist->_mark_dirty($val)
#
# Internal sub to alter the dirty flag. 1 for dirty, 0 for "not dirty"
sub _mark_dirty {
    my ($self, $dirty) = @_;
    $self->{'dirty'} = $dirty;
    return;
}

# $plist->_do_read_file($file, $header, $fields)
#
# internal sub to actually load the pkg list from $file.
# $header is the expected header (first line excl. newline)
# $fields is a ref to the relevant field list (see @*_FILE_FIELDS)
#  - croaks on error
sub _do_read_file {
    my ($self, $file, $header, $fields, $qf) = @_;
    my $count = scalar @$fields;
    my $root = {};
    open(my $fd, '<', $file);
    my $hd = <$fd>;
    chop $hd;
    unless ($hd eq $header) {
        # The interesting part here is the format is invalid, so
        # "ignore" errors from close
        no autodie qw(close);
        close($fd);
        croak "Unknown/unsupported file format ($hd)";
    }

    while (my $line = <$fd>) {
        chop($line);
        next if $line =~ m/^\s*+$/o;
        my (@values) = split m/\;/o, $line, $count;
        my $entry = {};
        unless ($count == scalar @values) {
            # The interesting part here is the format is invalid, so
            # "ignore" errors from close
            no autodie qw(close);
            close($fd);
            croak "Invalid line in $file at line $. ($_)";
        }
        for (my $i = 0 ; $i < $count ; $i++) {
            $entry->{$fields->[$i]} = $values[$i]//'';
        }
        $self->_make_alias_fields($entry);
        $self->_do_set($qf, $entry, $root);
    }
    close($fd);
    return $root;
}

sub _make_alias_fields {
    my ($self, $entry) = @_;

    # define source-version as alias of version for
    # source packages.
    $entry->{'source-version'} = $entry->{'version'}
      unless defined $entry->{'source-version'};
    # For compat with Lintian::Processable->new_from_metadata
    $entry->{'pkg_path'} = $entry->{'file'};
    $entry->{'package'} = $entry->{'source'}
      unless defined $entry->{'package'};

    $entry->{'pkg_type'} = $self->type;

    unless (defined $entry->{'identifier'}) {
        my $pkg = $entry->{'package'};
        my $version = $entry->{'version'};
        my $id = $self->type . ":$pkg/$version";
        $id .= '/' . $entry->{'architecture'} if $self->type ne 'source';
        $entry->{'identifier'} = $id;
    }
    return;
}

sub _do_set {
    my ($self, $qf, $entry, $root) = @_;
    my $qfl = scalar @$qf - 1; # exclude the last element (see below)
    my $cur = $root // $self->{'state'};
    my $k;

    # Find the hash where the entry should be stored
    # - The basic structure is "$root->{key1}->...->{keyN-1}{keyN} = $entry"
    # - This loop is supposed to find the "n-1"th hash and save that in $cur.
    # - After the loop, a simple "$cur->{$keyN} = $entry" inserts the element.
    for (my $i = 0 ; $i < $qfl ; $i++) {
        # Current key
        my $curk = $entry->{$qf->[$i]};
        my $element = $cur->{$curk};
        unless (defined $element) {
            $element = {};
            $cur->{$curk} = $element;
        }
        $cur = $element;
    }
    $k = $entry->{$qf->[$qfl]};
    $cur->{$k} = $entry;
    if (my $grouping = $self->{'grouping'}) {
        $grouping->_do_set(\@GROUP_QUERY, $entry);
    }
    return 1;
}

# Self-recursing method powering visit_all
sub _recurse_visit {
    my ($self, $hash, $visitor, $vdep, @keys) = @_;
    # if false, we recurse, if true we pass it to $visitor
    my $visit = $vdep == scalar @keys;
    foreach my $k (sort keys %$hash) {
        my $v = $hash->{$k};
        # Should we recurse into $v?
        $self->_recurse_visit($v, $visitor, $vdep, @keys, $k) unless $visit;
        # ... or is it the value to be visited?
        $visitor->($v, @keys, $k) if $visit;
    }
    return;
}

=back

=head1 AUTHOR

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
