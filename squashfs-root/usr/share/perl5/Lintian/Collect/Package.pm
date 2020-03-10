# -*- perl -*-
# Lintian::Collect::Package -- interface to data collection for packages

# Copyright (C) 2011 Niels Thykier
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

# This handles common things for things available in source and binary packages
package Lintian::Collect::Package;

use strict;
use warnings;
use autodie;

use parent 'Lintian::Collect';

use Carp qw(croak);
use Scalar::Util qw(blessed);

use Lintian::Path;
use Lintian::Path::FSInfo;
use Lintian::Util
  qw(internal_error open_gz perm2oct normalize_pkg_path dequote_name);

# A cache for (probably) the 5 most common permission strings seen in
# the wild.
# It may seem obscene, but it has an extreme "hit-ratio" and it is
# cheaper vastly than perm2oct.
my %PERM_CACHE = map { $_ => perm2oct($_) } (
    '-rw-r--r--', # standard (non-executable) file
    '-rwxr-xr-x', # standard executable file
    'drwxr-xr-x', # standard dir perm
    'drwxr-sr-x', # standard dir perm with suid (lintian-lab on lintian.d.o)
    'lrwxrwxrwx', # symlinks
);

my %FILE_CODE2LPATH_TYPE = (
    '-' => Lintian::Path::TYPE_FILE     | Lintian::Path::OPEN_IS_OK,
    'h' => Lintian::Path::TYPE_HARDLINK | Lintian::Path::OPEN_IS_OK,
    'd' => Lintian::Path::TYPE_DIR      | Lintian::Path::FS_PATH_IS_OK,
    'l' => Lintian::Path::TYPE_SYMLINK,
    'b' => Lintian::Path::TYPE_BLOCK_DEV,
    'c' => Lintian::Path::TYPE_CHAR_DEV,
    'p' => Lintian::Path::TYPE_PIPE,
);

my %INDEX_FAUX_DIR_TEMPLATE = (
    'name'       => '',
    '_path_info' => $FILE_CODE2LPATH_TYPE{'d'} | 0755,
    # Pick a "random" (but fixed) date
    # - hint, it's a good read.  :)
    'date_time'  => '1998-01-25 22:55:34',
    'faux'       => 1,
);

=head1 NAME

Lintian::Collect::Package - Lintian base interface to binary and source package data collection

=head1 SYNOPSIS

    use autodie;
    use Lintian::Collect;
    
    my ($name, $type, $dir) = ('foobar', 'source', '/path/to/lab-entry');
    my $info = Lintian::Collect->new ($name, $type, $dir);
    my $filename = "etc/conf.d/$name.conf";
    my $file = $info->index_resolved_path($filename);
    if ($file and $file->is_open_ok) {
        my $fd = $info->open;
        # Use $fd ...
        close($fd);
    } elsif ($file) {
        print "$file is available, but is not a file or unsafe to open\n";
    } else {
        print "$file is missing\n";
    }

=head1 DESCRIPTION

Lintian::Collect::Package provides part of an interface to package
data for source and binary packages.  It implements data collection
methods specific to all packages that can be unpacked (or can contain
files)

This module is in its infancy.  Most of Lintian still reads all data from
files in the laboratory whenever that data is needed and generates that
data via collect scripts.  The goal is to eventually access all data about
source packages via this module so that the module can cache data where
appropriate and possibly retire collect scripts in favor of caching that
data in memory.

=head1 INSTANCE METHODS

In addition to the instance methods listed below, all instance methods
documented in the L<Lintian::Collect> module are also available.

=over 4

=item unpacked ([FILE])

Returns the path to the directory in which the package has been
unpacked.  FILE must be either a L<Lintian::Path> object (>= 2.5.13~)
or a string denoting the requested path.  In the latter case, the path
must be relative to the root of the package and should be normalized.

It is not permitted for FILE to be C<undef>.  If the "root" dir is
desired either invoke this method without any arguments at all, pass
it the correct L<Lintian::Path> or the empty string.

If FILE is not in the package, it returns the path to a non-existent
file entry.

The path returned is not guaranteed to be inside the Lintian Lab as
the package may have been unpacked outside the Lab (e.g. as
optimization).

Caveat with symlinks: Package is extracted as is and the path returned
by this method points to the extracted file object.  If this is a
symlink, it may "escape the root" and point to a file outside the lab
(and a path traversal).

The following code may be helpful in checking for path traversal:

 use Lintian::Util qw(is_ancestor_of);

 my $collect = ... ;
 my $file = '../../../etc/passwd';
 my $uroot = $collect->unpacked;
 my $ufile = $collect->unpacked($file);
 # $uroot will exist, but $ufile might not.
 if ( -e $ufile && is_ancestor_of($uroot, $ufile)) {
    # has not escaped $uroot
    do_stuff($ufile);
 } elsif ( -e $ufile) {
    # escaped $uroot
    die "Possibly path traversal ($file)";
 } else {
    # Does not exists
 }

Alternatively one can use normalize_pkg_path in L<Lintian::Util> or
L<link_normalized|Lintian::Path/link_normalized>.

To get a list of entries in the package or the file meta data of the
entries (as L<path objects|Lintian::Path>), see L</sorted_index> and
L</index (FILE)>.

Needs-Info requirements for using I<unpacked>: unpacked

=cut

sub unpacked {
    ## no critic (Subroutines::RequireArgUnpacking)
    #  - _fetch_extracted_dir checks if the FILE argument was explicitly
    #    undef, but it relies on the size of @_ to do this.  With
    #    unpacking we would have to use shift or check it directly here
    #    (and duplicate said check in ::Binary::control and
    #    ::Source::debfiles).
    my $self = shift(@_);
    my $f = $_[0] // '';

    warnings::warnif(
        'deprecated',
        '[deprecated] The unpacked method is deprecated.  '
          . "Consider using \$info->index_resolved_path('$f') instead."
          . '  Called' # warnif appends " at <...>"
    );

    return $self->_fetch_extracted_dir('unpacked', 'unpacked', @_);
}

=item file_info (FILE)

Returns the output of file(1) -e ascii for FILE (if it exists) or
C<undef>.

B<CAVEAT>: As file(1) is passed "-e ascii", all text files will be
considered "data" rather than "text", "Java code" etc.

NB: The value may have been calibrated by Lintian.  A notorious example
is gzip files, where file(1) can be unreliable at times (see #620289)

Needs-Info requirements for using I<file_info>: file-info

=cut

sub file_info {
    my ($self, $file) = @_;
    if (my $cache = $self->{file_info}) {
        return ${$cache->{$file}}
          if exists $cache->{$file};
        return;
    }
    my %interned;
    my %file_info;
    my $path = $self->lab_data_path('file-info.gz');
    my $idx = open_gz($path);
    while (my $line = <$idx>) {
        chomp($line);

        $line =~ m/^(.+?)\x00\s+(.*)$/o
          or croak(
            join(q{ },
                'an error in the file pkg is preventing',
                "lintian from checking this package: $_"));
        my ($file, $info) = ($1,$2);
        my $ref = $interned{$info};

        $file =~ s,^\./,,o;

        if (!defined($ref)) {
            # Store a ref to the info to avoid creating a new copy
            # each time.  We just have to deref the reference on
            # return.  TODO: Test if this will be obsolete by
            # COW variables in Perl 5.20.
            $interned{$info} = $ref = \$info;
        }

        $file_info{$file} = $ref;
    }
    close($idx);
    $self->{file_info} = \%file_info;

    return ${$self->{file_info}{$file}}
      if exists $self->{file_info}{$file};
    return;
}

=item md5sums

Returns a hashref mapping a FILE to its md5sum.  The md5sum is
computed by Lintian during extraction and is not guaranteed to match
the md5sum in the "md5sums" control file.

Needs-Info requirements for using I<md5sums>: md5sums

=cut

sub md5sums {
    my ($self) = @_;
    return $self->{md5sums} if exists $self->{md5sums};
    my $md5f = $self->lab_data_path('md5sums');
    my $result = {};

    # read in md5sums info file
    open(my $fd, '<', $md5f);
    while (my $line = <$fd>) {
        chop($line);
        next if $line =~ m/^\s*$/o;
        $line =~ m/^(\\)?(\S+)\s*(\S.*)$/o
          or internal_error("syntax error in $md5f info file: $line");
        my ($zzescaped, $zzsum, $zzfile) = ($1, $2, $3);
        if($zzescaped) {
            $zzfile = dequote_name($zzfile);
        }
        $zzfile =~ s,^(?:\./)?,,o;
        $result->{$zzfile} = $zzsum;
    }
    close($fd);
    $self->{md5sums} = $result;
    return $result;
}

=item index (FILE)

Returns a L<path object|Lintian::Path> to FILE in the package.  FILE
must be relative to the root of the unpacked package and must be
without leading slash (or "./").  If FILE is not in the package, it
returns C<undef>.  If FILE is supposed to be a directory, it must be
given with a trailing slash.  Example:

  my $file = $info->index ("usr/bin/lintian");
  my $dir = $info->index ("usr/bin/");

To get a list of entries in the package, see L</sorted_index>.  To
actually access the underlying file (e.g. the contents), use
L</unpacked ([FILE])>.

Note that the "root directory" (denoted by the empty string) will
always be present, even if the underlying tarball omits it.

Needs-Info requirements for using I<index>: unpacked

=cut

sub index {
    my ($self, $file) = @_;
    if (my $cache = $self->{'index'}) {
        return $cache->{$file}
          if exists($cache->{$file});
        return;
    }
    my $load_info = {
        'field' => 'index',
        'index_file' => 'index',
        'index_owner_file' => 'index-owner-id',
        'fs_root_sub' => 'unpacked',
        'has_anchored_root_dir' => 1,
        'file_info_sub' => 'file_info',
    };
    return $self->_fetch_index_data($load_info, $file);
}

=item sorted_index

Returns a sorted array of file names listed in the package.  The names
will not have a leading slash (or "./") and can be passed to
L</unpacked ([FILE])> or L</index (FILE)> as is.

The array will not contain the entry for the "root" of the package.

NB: For source packages, please see the
L<"index"-caveat|Lintian::Collect::Source/index (FILE)>.

Needs-Info requirements for using I<sorted_index>: L<Same as index|/index (FILE)>

=cut

sub sorted_index {
    my ($self) = @_;
    # index does all our work for us, so call it if sorted_index has
    # not been created yet.
    $self->index('') unless exists $self->{sorted_index};
    return @{ $self->{sorted_index} };
}

=item index_resolved_path(PATH)

Resolve PATH (relative to the root of the package) and return the
L<entry|Lintian::Path> denoting the resolved path.

The resolution is done using
L<resolve_path|Lintian::Path/resolve_path([PATH])>.

NB: For source packages, please see the
L<"index"-caveat|Lintian::Collect::Source/index (FILE)>.

Needs-Info requirements for using I<index_resolved_path>: L<Same as index|/index (FILE)>

=cut

sub index_resolved_path {
    my ($self, $path) = @_;
    return $self->index('')->resolve_path($path);
}

# Backing method for unpacked, debfiles and others; this is not a part of the
# API.
# sub _fetch_extracted_dir Needs-Info none
sub _fetch_extracted_dir {
    my ($self, $field, $dirname, $file) = @_;
    my $dir = $self->{$field};
    my $filename = '';
    my $normalized = 0;
    if (not defined $dir) {
        $dir = $self->lab_data_path($dirname);
        croak "$field ($dirname) is not available" unless -d "$dir/";
        $self->{$field} = $dir;
    }

    if (!defined($file)) {
        if (scalar(@_) >= 4) {
            # Was this undef explicit?
            croak('Input file was undef');
        }
        $normalized = 1;
    } else {
        if (ref($file)) {
            if (!blessed($file) || !$file->isa('Lintian::Path')) {
                croak('Input file must be a string or a Lintian::Path object');
            }
            $filename = $file->name;
            $normalized = 1;
        } else {
            $normalized = 0;
            $filename = $file;
        }
    }

    if ($filename ne '') {
        if (!$normalized) {
            # strip leading ./ - if that leaves something, return the
            # path there
            if ($filename =~ s,^(?:\.?/)++,,go) {
                warnings::warnif('Lintian::Collect',
                    qq{Argument to $field had leading "/" or "./"});
            }
            if ($filename =~ m{(?: ^|/ ) \.\. (?: /|$ )}xsm) {
                # possible traversal - double check it and (if needed)
                # stop it before it gets out of hand.
                if (!defined(normalize_pkg_path('/', $filename))) {
                    croak qq{The path "$file" is not within the package root};
                }
            }
        }
        return "$dir/$filename" if $filename ne '';
    }
    return $dir;
}

# Backing method for index and others; this is not a part of the API.
# sub _fetch_index_data Needs-Info none
sub _fetch_index_data {
    my ($self, $load_info, $file) = @_;

    my (%idxh, %children, $num_idx, %rhlinks, @sorted, @check_dirs);
    my $base_dir = $self->base_dir;
    my $field = $load_info->{'field'};
    my $index = $load_info->{'index_file'};
    my $indexown = $load_info->{'index_owner_file'};
    my $allow_empty = $load_info->{'allow_empty'} // 0;
    my $idx = open_gz("$base_dir/${index}.gz");
    my $fs_info = Lintian::Path::FSInfo->new(
        '_collect' => $self,
        '_collect_path_sub' => $load_info->{'fs_root_sub'},
        '_collect_file_info_sub' => $load_info->{'file_info_sub'},
        'has_anchored_root_dir' => $load_info->{'as_anchored_root_dir'},
    );

    if ($indexown) {
        $num_idx = open_gz("$base_dir/${indexown}.gz");
    }
    while (my $line = <$idx>) {
        chomp($line);

        my (%file, $perm, $operm, $ownership, $name, $raw_type, $size);
        my ($date, $time);
        ($perm,$ownership,$size,$date,$time,$name)=split(' ', $line, 6);

        $file{'date_time'} = "${date} ${time}";
        $raw_type = substr($perm, 0, 1);

        # Only set size if it is non-zero and even then, only for
        # regular files.  When we set it, insist on it being an int.
        # This makes perl store it slightly more efficient.
        $file{'size'} = int($size) if $size and $raw_type eq '-';

        # This may appear to be obscene, but the call overhead of
        # perm2oct is measurable on (e.g.) chromium-browser.  With
        # the cache we go from ~1.5s to ~0.1s.
        #   Of the 115363 paths here, only 306 had an "uncached"
        # permission string (chromium-browser/32.0.1700.123-2).
        if (exists($PERM_CACHE{$perm})) {
            $operm = $PERM_CACHE{$perm};
        } else {
            $operm = perm2oct($perm);
        }
        $file{'_path_info'} = $operm
          | ($FILE_CODE2LPATH_TYPE{$raw_type} // Lintian::Path::TYPE_OTHER);

        if ($num_idx) {
            # If we have a "numeric owner" index file, read that as well
            my $numeric = <$num_idx>;
            chomp $numeric;
            croak 'cannot read index file $indexown' unless defined $numeric;
            my ($owner_id, $name_chk) = (split(' ', $numeric, 6))[1, 5];
            croak "mismatching contents of index files: $name $name_chk"
              if $name ne $name_chk;
            my ($uid, $gid) = split('/', $owner_id, 2);
            # Memory-optimise for 0/0.  Perl has an insane overhead
            # for each field, so this is sadly worth it!
            if ($uid) {
                $file{'uid'} = int($uid);
            }
            if ($gid) {
                $file{'gid'} = int($gid);
            }
        }

        my ($owner, $group) = split('/', $ownership, 2);

        # Memory-optimise for root/root.  Perl has an insane overhead
        # for each field, so this is sadly worth it!
        if ($owner ne 'root' and $owner ne '0') {
            $file{'owner'} = $owner;
        }
        if ($group ne 'root' and $group ne '0') {
            $file{'group'} = $group;
        }

        if ($name =~ s/ link to (.*)//) {
            my $target = dequote_name($1);
            $file{'_path_info'} = $FILE_CODE2LPATH_TYPE{'h'} | $operm;
            $file{link} = $target;

            push @{$rhlinks{$target}}, dequote_name($name);
        } elsif ($raw_type eq 'l') {
            ($name, $file{link}) = split ' -> ', $name, 2;
            $file{link} = dequote_name($file{link}, 0);
        }
        # We store the name here, but will replace it later.  The
        # reason for storing it now is that we may need it during the
        # "hard-link fixup"-phase.
        $file{'name'} = $name = dequote_name($name);

        $idxh{$name} = \%file;

        # Record children
        $children{$name} ||= [] if $raw_type eq 'd';
        my ($parent) = ($name =~ m,^(.+/)?(?:[^/]+/?)$,);
        $parent = '' unless defined $parent;

        $children{$parent} = [] unless exists $children{$parent};

        # coll/unpacked sorts its output, so the parent dir ought to
        # have been created before this entry.  However, it might not
        # be if an intermediate directory is missing.  NB: This
        # often triggers for the root directory, which is normal.
        push(@check_dirs, $parent) if not exists($idxh{$parent});

        # Ensure the "root" is not its own child.  It is not really helpful
        # from an analysis PoV and it creates ref cycles  (and by extension
        # leaks like #695866).
        push @{ $children{$parent} }, $name unless $parent eq $name;
    }
    while (defined(my $name = pop(@check_dirs))) {
        # check_dirs /can/ contain the same item multiple times.
        if (!exists($idxh{$name})) {
            my %cpy = %INDEX_FAUX_DIR_TEMPLATE;
            my ($parent) = ($name =~ m,^(.+/)?(?:[^/]+/?)$,);
            $parent //= '';
            $cpy{'name'} = $name;
            $idxh{$name} = \%cpy;
            $children{$parent} = [] unless exists $children{$parent};
            push @{ $children{$parent} }, $name unless $parent eq $name;
            push(@check_dirs, $parent) if not exists($idxh{$parent});
        }
    }
    if (!$allow_empty && !exists($idxh{''})) {
        internal_error('The root dir should be present or have been faked');
    }
    if (%rhlinks) {
        foreach my $file (sort keys %rhlinks) {
            # We remove entries we have fixed up, so check the entry
            # is still there.
            next unless exists $rhlinks{$file};
            my $e = $idxh{$file};
            my @check = ($e->{name});
            my (%candidates, @sorted, $target);
            while (my $current = pop @check) {
                $candidates{$current} = 1;
                foreach my $rdep (@{$rhlinks{$current}}) {
                    # There should not be any cycles, but just in case
                    push @check, $rdep unless $candidates{$rdep};
                }
                # Remove links we are fixing
                delete $rhlinks{$current};
            }
            # keys %candidates will be a complete list of hardlinks
            # that points (in)directly to $file.  Time to normalize
            # the links.
            #
            # Sort in reverse order (allows pop instead of unshift)
            @sorted = reverse sort keys %candidates;
            # Our preferred target
            $target = pop @sorted;

            foreach my $link (@sorted) {
                next unless exists $idxh{$target};
                my $le = $idxh{$link};
                # We may be "demoting" a "real file" to a "hardlink"
                $le->{'_path_info'}
                  = ($le->{'_path_info'} & ~Lintian::Path::TYPE_FILE)
                  | Lintian::Path::TYPE_HARDLINK;
                $le->{link} = $target;
            }
            if (defined($target) and $target ne $e->{name}) {
                $idxh{$target}{'_path_info'}
                  = ($idxh{$target}{'_path_info'}
                      & ~Lintian::Path::TYPE_HARDLINK)
                  | Lintian::Path::TYPE_FILE;
                # hardlinks does not have size, so copy that from the original
                # entry.
                $idxh{$target}{'size'} = $e->{'size'} if exists($e->{'size'});
                delete($e->{'size'});
                delete $idxh{$target}{link};
            }
        }
    }
    @sorted = sort keys %idxh;
    foreach my $file (reverse @sorted) {
        # Add them in reverse order - entries in a dir are made
        # objects before the dir itself.
        my $entry = $idxh{$file};
        if ($entry->{'_path_info'} & Lintian::Path::TYPE_DIR) {
            my (%child_table, @sorted_children);
            for my $cname (sort(@{ $children{$file} })) {
                my $child = $idxh{$cname};
                my $basename = $child->basename;
                if (substr($basename, -1, 1) eq '/') {
                    $basename = substr($basename, 0, -1);
                }
                $child_table{$basename} = $child;
                push(@sorted_children, $child);
            }
            $entry->{'_sorted_children'} = \@sorted_children;
            $entry->{'children'} = \%child_table;
            $entry->{'_fs_info'} = $fs_info;
        }
        # Insert name here to share the same storage with the hash key
        $entry->{'name'} = $file;
        $idxh{$file} = Lintian::Path->new($entry);
    }
    $self->{$field} = \%idxh;
    # Remove the "top" dir in the sorted_index as it is hardly ever
    # used.
    # - Note this will always be present as we create it if it is
    #   missing.  It will always be the first entry since we sorted
    #   the list.
    shift @sorted;
    @sorted = map { $idxh{$_} } @sorted;
    $self->{"sorted_$field"} = \@sorted;
    close($idx);
    close($num_idx) if $num_idx;
    return $self->{$field}{$file} if exists $self->{$field}{$file};
    return;
}

1;

=back

=head1 AUTHOR

Originally written by Niels Thykier <niels@thykier.net> for Lintian.

=head1 SEE ALSO

lintian(1), L<Lintian::Collect>, L<Lintian::Collect::Binary>,
L<Lintian::Collect::Source>

=cut

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
