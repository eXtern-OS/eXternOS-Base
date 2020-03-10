# -*- perl -*-
# Lintian::Collect::Binary -- interface to binary package data collection

# Copyright (C) 2008, 2009 Russ Allbery
# Copyright (C) 2008 Frank Lichtenheld
# Copyright (C) 2012 Kees Cook
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

package Lintian::Collect::Binary;

use strict;
use warnings;
use autodie;
use parent 'Lintian::Collect::Package';

use Lintian::Relation;
use Carp qw(croak);
use Parse::DebianChangelog;

use Lintian::Util
  qw(internal_error open_gz parse_dpkg_control get_file_checksum strip);

=head1 NAME

Lintian::Collect::Binary - Lintian interface to binary package data collection

=head1 SYNOPSIS

    my ($name, $type, $dir) = ('foobar', 'binary', '/path/to/lab-entry');
    my $collect = Lintian::Collect->new ($name, $type, $dir);
    if ($collect->native) {
        print "Package is native\n";
    }

=head1 DESCRIPTION

Lintian::Collect::Binary provides an interface to package data for binary
packages.  It implements data collection methods specific to binary
packages.

This module is in its infancy.  Most of Lintian still reads all data from
files in the laboratory whenever that data is needed and generates that
data via collect scripts.  The goal is to eventually access all data about
binary packages via this module so that the module can cache data where
appropriate and possibly retire collect scripts in favor of caching that
data in memory.

=head1 CLASS METHODS

=over 4

=item new (PACKAGE)

Creates a new Lintian::Collect::Binary object.  Currently, PACKAGE is
ignored.  Normally, this method should not be called directly, only via
the L<Lintian::Collect> constructor.

=cut

sub new {
    my ($class, $pkg) = @_;
    my $self = {};
    bless($self, $class);
    return $self;
}

=back

=head1 INSTANCE METHODS

In addition to the instance methods listed below, all instance methods
documented in the L<Lintian::Collect> and the
L<Lintian::Collect::Package> modules are also available.

=over 4

=item native

Returns true if the binary package is native and false otherwise.
Nativeness will be judged by the source version number.

If the version number is absent, this will return false (as
native packages are a lot rarer than non-native ones).

Needs-Info requirements for using I<native>: L<Same as field|Lintian::Collect/field ([FIELD[, DEFAULT]])>

=cut

sub native {
    my ($self) = @_;
    return $self->{native} if exists $self->{native};
    my $version;
    my $source = $self->field('source');
    if (defined $source && $source =~ m/\((.*)\)/) {
        $version = $1;
    } else {
        $version = $self->field('version');
    }
    if (defined $version) {
        $self->{native} = ($version !~ m/-/);
    } else {
        # We do not know, but assume it to non-native as it is
        # the most likely case.
        $self->{native} = 0;
    }
    return $self->{native};
}

=item changelog

Returns the changelog of the binary package as a Parse::DebianChangelog
object, or undef if the changelog doesn't exist.  The changelog-file
collection script must have been run to create the changelog file, which
this method expects to find in F<changelog>.

Needs-Info requirements for using I<changelog>: changelog-file

=cut

sub changelog {
    my ($self) = @_;
    return $self->{changelog} if exists $self->{changelog};
    my $dch = $self->lab_data_path('changelog');
    if (-l $dch || !-f $dch) {
        $self->{changelog} = undef;
    } else {
        my $shared = $self->{'_shared_storage'};
        my ($checksum, $changelog);
        if (defined($shared)) {
            $checksum = get_file_checksum('sha1', $dch);
            $changelog = $shared->{'changelog'}{$checksum};
        }
        if (not $changelog) {
            my %opts = (infile => $dch, quiet => 1);
            $changelog = Parse::DebianChangelog->init(\%opts);
            if (defined($shared)) {
                $shared->{'changelog'}{$checksum} = $changelog;
            }
        }
        $self->{changelog} = $changelog;
    }
    return $self->{changelog};
}

=item control ([FILE])

B<This method is deprecated>.  Consider using
L</control_index_resolved_path(PATH)> instead, which returns
L<Lintian::Path> objects.

Returns the path to FILE in the control.tar.gz.  FILE must be either a
L<Lintian::Path> object (>= 2.5.13~) or a string denoting the
requested path.  In the latter case, the path must be relative to the
root of the control.tar.gz member and should be normalized.

It is not permitted for FILE to be C<undef>.  If the "root" dir is
desired either invoke this method without any arguments at all, pass
it the correct L<Lintian::Path> or the empty string.

To get a list of entries in the control.tar.gz or the file meta data
of the entries (as L<path objects|Lintian::Path>), see
L</sorted_control_index> and L</control_index (FILE)>.

The caveats of L<unpacked|Lintian::Collect::Package/unpacked ([FILE])>
also apply to this method.  However, as the control.tar.gz is not
known to contain symlinks, a simple file type check is usually enough.

Needs-Info requirements for using I<control>: bin-pkg-control

=cut

sub control {
    ## no critic (Subroutines::RequireArgUnpacking)
    # - see L::Collect::unpacked for why
    my $self = shift(@_);
    my $f = $_[0] // '';

    warnings::warnif(
        'deprecated',
        '[deprecated] The control method is deprecated.  '
          . "Consider using \$info->control_index_resolved_path('$f') instead."
          . '  Called' # warnif appends " at <...>"
    );
    return $self->_fetch_extracted_dir('control', 'control', @_);
}

=item control_index (FILE)

Returns a L<path object|Lintian::Path> to FILE in the control.tar.gz.
FILE must be relative to the root of the control.tar.gz and must be
without leading slash (or "./").  If FILE is not in the
control.tar.gz, it returns C<undef>.

To get a list of entries in the control.tar.gz, see
L</sorted_control_index>.  To actually access the underlying file
(e.g. the contents), use L</control ([FILE])>.

Note that the "root directory" (denoted by the empty string) will
always be present, even if the underlying tarball omits it.

Needs-Info requirements for using I<control_index>: bin-pkg-control

=cut

sub control_index {
    my ($self, $file) = @_;
    if (my $cache = $self->{'control_index'}) {
        return $cache->{$file}
          if exists($cache->{$file});
        return;
    }
    my $load_info = {
        'field' => 'control_index',
        'index_file' => 'control-index',
        'index_owner_file' => undef,
        'fs_root_sub' => 'control',
        # Control files are not installed relative to the system root.
        # Accordingly, we forbid absolute paths and symlinks..
        'has_anchored_root_dir' => 0,
    };
    return $self->_fetch_index_data($load_info, $file);
}

=item sorted_control_index

Returns a sorted array of file names listed in the control.tar.gz.
The names will not have a leading slash (or "./") and can be passed
to L</control ([FILE])> or L</control_index (FILE)> as is.

The array will not contain the entry for the "root" of the
control.tar.gz.

Needs-Info requirements for using I<sorted_control_index>: L<Same as control_index|/control_index (FILE)>

=cut

sub sorted_control_index {
    my ($self) = @_;
    # control_index does all our work for us, so call it if
    # sorted_control_index has not been created yet.
    $self->control_index('') unless exists($self->{'sorted_control_index'});
    return @{ $self->{'sorted_control_index'} };
}

=item control_index_resolved_path(PATH)

Resolve PATH (relative to the root of the package) and return the
L<entry|Lintian::Path> denoting the resolved path.

The resolution is done using
L<resolve_path|Lintian::Path/resolve_path([PATH])>.

Needs-Info requirements for using I<control_index_resolved_path>: L<Same as control_index|/control_index (FILE)>

=cut

sub control_index_resolved_path {
    my ($self, $path) = @_;
    return $self->control_index('')->resolve_path($path);
}

=item strings (FILE)

Returns an open handle, which will read the data from coll/strings for
FILE.  If coll/strings did not collect any strings about FILE, this
returns an open read handle with no content.

Caller is responsible for closing the handle either way.

Needs-Info requirements for using I<strings>: strings

=cut

sub strings {
    my ($self, $file) = @_;
    my $real = $self->_fetch_extracted_dir('strings', 'strings', "${file}.gz");
    if (not -f $real) {
        open(my $fd, '<', '/dev/null');
        return $fd;
    }
    my $fd = open_gz($real);
    return $fd;
}

=item scripts

Returns a hashref mapping a FILE to its script/interpreter information
(if FILE is a script).  If FILE is not a script, it is not in the hash
(and callers should use exists to test membership to ensure this
invariant holds).

The value for a given FILE consists of a table with the following keys
(and associated value):

=over 4

=item calls_env

Returns a truth value if the script uses env (/usr/bin/env or
/bin/env) in the "#!".  Otherwise it is C<undef>.

=item interpreter

This is the interpreter used.  If calls_env is true, this will be the
first argument to env.  Otherwise it will be the command listed after
the "#!".

NB: Some template files have "#!" lines like "#!@PERL@" or "#!perl".
In this case, this value will be @PERL@ or perl (respectively).

=item name

Return the file name of the script.  This will be identical to key to
look up this table.

=back

Needs-Info requirements for using I<scripts>: scripts

=cut

sub scripts {
    my ($self) = @_;
    return $self->{scripts} if exists $self->{scripts};
    my $scrf = $self->lab_data_path('scripts');
    my %scripts;
    if (-f $scrf) {
        open(my $fd, '<', $scrf);
        while (my $line = <$fd>) {
            my (%file, $name);
            chomp($line);

            $line =~ m/^(env )?(\S*) (.*)$/o
              or internal_error("bad line in scripts file: $line");
            ($file{calls_env}, $file{interpreter}, $name) = ($1, $2, $3);

            $name =~ s,^\./,,o;
            $name =~ s,/+$,,o;
            $file{name} = $name;
            $scripts{$name} = \%file;
        }
        close($fd);
    }
    $self->{scripts} = \%scripts;

    return $self->{scripts};
}

=item objdump_info

Returns a hashref mapping a FILE to the data collected by objdump-info
or C<undef> if no data is available for that FILE.  Data is generally
only collected for ELF files.

Needs-Info requirements for using I<objdump_info>: objdump-info

=cut

sub objdump_info {
    my ($self) = @_;
    return $self->{objdump_info} if exists $self->{objdump_info};
    my $objf = $self->lab_data_path('objdump-info.gz');
    my %objdump_info;
    local $_;
    my $fd = open_gz($objf);
    foreach my $pg (parse_dpkg_control($fd)) {
        my %info;
        if (lc($pg->{'broken'}//'no') eq 'yes') {
            $info{'ERRORS'} = 1;
        }
        if (lc($pg->{'bad-dynamic-table'}//'no') eq 'yes') {
            $info{'BAD-DYNAMIC-TABLE'} = 1;
        }
        $info{'ELF-TYPE'} = $pg->{'elf-type'} if $pg->{'elf-type'};
        foreach my $symd (split m/\s*\n\s*/, $pg->{'dynamic-symbols'}//'') {
            next unless $symd;
            if ($symd =~ m/^\s*(\S+)\s+(?:(\S+)\s+)?(\S+)$/){
                # $ver is not always there
                my ($sec, $ver, $sym) = ($1, $2, $3);
                $ver //= '';
                push @{ $info{'SYMBOLS'} }, [$sec, $ver, $sym];
            }
        }
        foreach my $section (split m/\s*\n\s*/, $pg->{'section-headers'}//'') {
            next unless $section;
            # NB: helpers/coll/objdump-info-helper discards most
            # sections.  If you are missing a section name for a
            # check, please update helpers/coll/objdump-info-helper to
            # retrain the section name you need.
            strip($section);
            $info{'SH'}{$section} = 1;
        }
        foreach my $data (split m/\s*\n\s*/, $pg->{'program-headers'}//'') {
            next unless $data;
            my ($header, @vals) = split m/\s++/, $data;
            foreach my $extra (@vals) {
                my ($opt, $val) = split m/=/, $extra;
                if ($opt eq 'interp' and $header eq 'INTERP') {
                    $info{'INTERP'} = $val;
                } else {
                    $info{'PH'}{$header}{$opt} = $val;
                }
            }
        }
        foreach my $data (split m/\s*\n\s*/, $pg->{'dynamic-section'}//'') {
            next unless $data;
            # Here we just need RPATH and NEEDS, so ignore the rest for now
            my ($header, $val) = split(m/\s++/, $data, 2);
            if ($header eq 'RPATH' or $header eq 'RUNPATH') {
                # RPATH is like PATH
                foreach my $rpathcomponent (split(m/:/,$val)) {
                    $info{$header}{$rpathcomponent} = 1;
                }
            } elsif ($header eq 'NEEDED' or $header eq 'SONAME') {
                push @{ $info{$header} }, $val;
            } elsif ($header eq 'TEXTREL' or $header eq 'DEBUG') {
                $info{$header} = 1;
            } elsif ($header eq 'FLAGS_1') {
                for my $flag (split(m/\s++/, $val)) {
                    $info{$header}{$flag} = 1;
                }
            }
        }

        if ($pg->{'filename'} =~ m,^(.+)\(([^/\)]+)\)$,o) {
            # object file in a static lib.
            my ($lib, $obj) = ($1, $2);
            my $libentry = $objdump_info{$lib};
            if (not defined $libentry) {
                $libentry = {
                    'filename' => $lib,
                    'objects'  => [$obj],
                };
                $objdump_info{$lib} = $libentry;
            } else {
                push @{ $libentry->{'objects'} }, $obj;
            }
        }
        $objdump_info{$pg->{'filename'}} = \%info;
    }
    $self->{objdump_info} = \%objdump_info;

    close($fd);

    return $self->{objdump_info};
}

=item hardening_info

Returns a hashref mapping a FILE to its hardening issues.

NB: This is generally only useful for checks/binaries to emit the
hardening-no-* tags.

Needs-Info requirements for using I<hardening_info>: hardening-info

=cut

sub hardening_info {
    my ($self) = @_;
    return $self->{hardening_info} if exists $self->{hardening_info};
    my $hardf = $self->lab_data_path('hardening-info');
    my %hardening_info;
    if (-e $hardf) {
        open(my $idx, '<', $hardf);
        while (my $line = <$idx>) {
            chomp($line);

            if ($line =~ m,^([^:]+):(?:\./)?(.*)$,) {
                my ($tag, $file) = ($1, $2);
                push(@{$hardening_info{$file}}, $tag);
            }
        }
        close($idx);
    }

    $self->{hardening_info} = \%hardening_info;
    return $self->{hardening_info};
}

=item java_info

Returns a hashref containing information about JAR files found in
binary packages, in the form I<file name> -> I<info>, where I<info> is
a hash containing the following keys:

=over 4

=item manifest

A hash containing the contents of the JAR file manifest. For instance,
to find the classpath of I<$file>, you could use:

 if (exists $info->java_info->{$file}{'manifest'}) {
     my $cp = $info->java_info->{$file}{'manifest'}{'Class-Path'};
     # ...
 }

NB: Not all jar files have a manifest.  For those without, this will
value will not be available.  Use exists (rather than defined) to
check for it.

=item files

A table of the files in the JAR.  Each key is a file name and its value
is its "Major class version" for Java or "-" if it is not a class file.

=item error

If it exists, this is an error that occurred during reading of the zip
file.  If it exists, it is unlikely that the other fields will be
present.

=back

Needs-Info requirements for using I<java_info>: java-info

=cut

sub java_info {
    my ($self) = @_;
    return $self->{java_info} if exists $self->{java_info};
    my $javaf = $self->lab_data_path('java-info.gz');
    my %java_info;
    if (!-f $javaf) {
        # no java-info.gz => no jar files to collect data.  Just
        # return an empty hash ref.
        $self->{java_info} = \%java_info;
        return $self->{java_info};
    }
    my $idx = open_gz($javaf);
    my $file;
    my $file_list;
    my $manifest = 0;
    local $_;
    while (<$idx>) {
        chomp;
        next if m/^\s*$/o;

        if (m#^-- ERROR:\s*(\S.++)$#o) {
            $java_info{$file}{error} = $1;
        } elsif (m#^-- MANIFEST: (?:\./)?(?:.+)$#o) {
            # TODO: check $file == $1 ?
            $java_info{$file}{manifest} = {};
            $manifest = $java_info{$file}{manifest};
            $file_list = 0;
        } elsif (m#^-- (?:\./)?(.+)$#o) {
            $file = $1;
            $java_info{$file}{files} = {};
            $file_list = $java_info{$file}{files};
            $manifest = 0;
        } else {
            if ($manifest && m#^  (\S+):\s(.*)$#o) {
                $manifest->{$1} = $2;
            } elsif ($file_list) {
                my ($fname, $clmajor) = (m#^([^-].*):\s*([-\d]+)$#);
                $file_list->{$fname} = $clmajor;
            }

        }
    }
    $self->{java_info} = \%java_info;
    close($idx);
    return $self->{java_info};
}

=item relation (FIELD)

Returns a L<Lintian::Relation> object for the specified FIELD, which should
be one of the possible relationship fields of a Debian package or one of
the following special values:

=over 4

=item all

The concatenation of Pre-Depends, Depends, Recommends, and Suggests.

=item strong

The concatenation of Pre-Depends and Depends.

=item weak

The concatenation of Recommends and Suggests.

=back

If FIELD isn't present in the package, the returned Lintian::Relation
object will be empty (always satisfied and implies nothing).

Needs-Info requirements for using I<relation>: L<Same as field|Lintian::Collect/field ([FIELD[, DEFAULT]])>

=cut

sub relation {
    my ($self, $field) = @_;
    $field = lc $field;
    return $self->{relation}{$field} if exists $self->{relation}{$field};

    my %special = (
        all    => [qw(pre-depends depends recommends suggests)],
        strong => [qw(pre-depends depends)],
        weak   => [qw(recommends suggests)]);
    my $result;
    if ($special{$field}) {
        $result = Lintian::Relation->and(map { $self->relation($_) }
              @{ $special{$field} });
    } else {
        my %known = map { $_ => 1 }
          qw(pre-depends depends recommends suggests enhances breaks
          conflicts provides replaces);
        croak("unknown relation field $field") unless $known{$field};
        my $value = $self->field($field);
        $result = Lintian::Relation->new($value);
    }
    $self->{relation}{$field} = $result;
    return $self->{relation}{$field};
}

=item is_pkg_class ([TYPE])

Returns a truth value if the package is the given TYPE of special
package.  TYPE can be one of "transitional", "debug" or "any-meta".
If omitted it defaults to "any-meta".  The semantics for these values
are:

=over 4

=item transitional

The package is (probably) a transitional package (e.g. it is probably
empty, just depend on stuff will eventually disappear.)

Guessed from package description.

=item any-meta

This package is (probably) some kind of meta or task package.  A meta
package is usually empty and just depend on stuff.  It will also
return a truth value for "tasks" (i.e. tasksel "tasks").

A transitional package will also match this.

Guessed from package description, section or package name.

=item debug

The package is (probably) a package containing debug symbols.

Guessed from the package name.

=item auto-generated

The package is (probably) a package generated automatically (e.g. a
dbgsym package)

Guessed from the "Auto-Built-Package" field.

=back

Needs-Info requirements for using I<is_pkg_class>: L<Same as field|Lintian::Collect/field ([FIELD[, DEFAULT]])>

=cut

{
    # Regexes to try against the package description to find metapackages or
    # transitional packages.
    my $METAPKG_REGEX= qr/meta[ -]?package|dummy|(?:dependency|empty) package/;

    sub is_pkg_class {
        my ($self, $pkg_class) = @_;
        my $desc = $self->field('description', '');
        $pkg_class //= 'any-meta';
        if ($pkg_class eq 'debug') {
            return 1 if $self->name =~ m/-dbg(?:sym)?/;
            return;
        }
        if ($pkg_class eq 'auto-generated') {
            return 1 if $self->field('auto-built-package');
            return;
        }
        return 1 if $desc =~ m/transitional package/;
        $desc = lc($desc);
        if ($pkg_class eq 'any-meta') {
            my ($section) = $self->field('section', '');
            return 1 if $desc =~ m/$METAPKG_REGEX/o;
            # Section "tasks" or "metapackages" qualifies as well
            return 1 if $section =~ m,(?:^|/)(?:tasks|metapackages)$,;
            return 1 if $self->name =~ m/^task-/;
        }
        return;
    }
}

=item is_conffile (FILE)

Returns a truth value if FILE is listed in the conffiles control file.
If the control file is not present or FILE is not listed in it, it
returns C<undef>.

Note that FILE should be the filename relative to the package root
(even though the control file uses absolute paths).  If the control
file does relative paths, they are assumed to be relative to the
package root as well (and used without warning).

Needs-Info requirements for using I<is_conffile>: L<Same as control_index_resolved_path|/control_index_resolved_path(PATH)>

=cut

sub is_conffile {
    my ($self, $file) = @_;
    if (exists $self->{'conffiles'}) {
        return 1 if exists $self->{'conffiles'}{$file};
        return;
    }
    my $cf = $self->control_index_resolved_path('conffiles');
    my %conffiles;
    $self->{'conffiles'} = \%conffiles;
    return if not $cf or not $cf->is_open_ok;
    my $fd = $cf->open;
    while (my $line = <$fd>) {
        chomp $line;
        next if $line =~ m/^\s*$/;
        # Look up happens with a relative path (e.g. etc/file.conf).
        # Side-effect is that we silently "fix" relative conffiles,
        # but checks/conffiles catches those for us.
        $line =~ s,^/++,,o;
        $conffiles{$line} = 1;
    }
    close($fd);
    return 1 if exists $conffiles{$file};
    return;
}

=back

=head1 AUTHOR

Originally written by Frank Lichtenheld <djpig@debian.org> for Lintian.

=head1 SEE ALSO

lintian(1), L<Lintian::Collect>, L<Lintian::Relation>

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
