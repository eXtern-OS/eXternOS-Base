# cruft -- lintian check script -*- perl -*-
#
# based on debhelper check,
# Copyright (C) 1999 Joey Hess
# Copyright (C) 2000 Sean 'Shaleh' Perry
# Copyright (C) 2002 Josip Rodin
# Copyright (C) 2007 Russ Allbery
# Copyright (C) 2013-2014 Bastien ROUCARIÈS
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

package Lintian::cruft;
use strict;
use warnings;
use autodie;
use v5.10;

# Half of the size used in the "sliding window" for detecting bad
# licenses like GFDL with invariant sections.
# NB: Keep in sync cruft-gfdl-fp-sliding-win/pre_build.
# not less than 8192 for source missing
use constant BLOCKSIZE => 16_384;

# constant for insane line length
use constant INSANE_LINE_LENGTH => 512;
use constant SAFE_LINE_LENGTH => 256;

use File::Basename qw(basename);
use List::MoreUtils qw(any);

use Lintian::Data;
use Lintian::Relation ();
use Lintian::Tags qw(tag);
use Lintian::Util qw(internal_error normalize_pkg_path strip);
use Lintian::SlidingWindow;

our $LIBTOOL = Lintian::Relation->new('libtool | dh-autoreconf');

# load data for md5sums based check
sub _md5sum_based_lintian_data {
    my ($filename) = @_;
    return Lintian::Data->new(
        $filename,
        qr/\s*\~\~\s*/,
        sub {
            my @sliptline = split(/\s*\~\~\s*/, $_[1], 5);
            if (scalar(@sliptline) != 5) {
                internal_error("Syntax error in $filename", $.);
            }
            my ($sha1, $sha256, $name, $reason, $link) = @sliptline;
            return {
                'sha1'   => $sha1,
                'sha256' => $sha256,
                'name'   => $name,
                'reason' => $reason,
                'link'   => $link,
            };
        });
}

# forbidden files
my $NON_DISTRIBUTABLE_FILES
  = _md5sum_based_lintian_data('cruft/non-distributable-files');

# non free files
my $NON_FREE_FILES = _md5sum_based_lintian_data('cruft/non-free-files');

# prebuilt-file or forbidden file type
my $WARN_FILE_TYPE =  Lintian::Data->new(
    'cruft/warn-file-type',
    qr/\s*\~\~\s*/,
    sub {
        my @sliptline = split(/\s*\~\~\s*/, $_[1], 4);
        if (scalar(@sliptline) < 1 or scalar(@sliptline) > 4) {
            internal_error('Syntax error in cruft/warn-file-type', $.);
        }
        my ($regtype, $regname, $transformlist) = @sliptline;

        # allow empty regname
        $regname = defined($regname) ? strip($regname) : '';
        if (length($regname) == 0) {
            $regname = '.*';
        }

        # build transform pair
        $transformlist //= '';
        $transformlist = strip($transformlist);

        my $syntaxerror = 'Syntax error in cruft/warn-file-type';
        my @transformpairs;
        unless($transformlist eq '') {
            my @transforms = split(/\s*\&\&\s*/, $transformlist);
            if(scalar(@transforms) > 0) {
                foreach my $transform (@transforms) {
                    # regex transform
                    if($transform =~ m'^s/') {
                        $transform =~ m'^s/([^/]*?)/([^/]*?)/$';
                        unless(defined($1) and defined($2)) {
                            internal_error($syntaxerror, 'in transform regex',
                                $.);
                        }
                        push(@transformpairs,[$1,$2]);
                    } elsif ($transform =~ m'^map\s*{') {
                        $transform
                          =~ m#^map \s* { \s* 's/([^/]*?)/\'.\$_.'/' \s* } \s* qw\(([^\)]*)\)#x;
                        unless(defined($1) and defined($2)) {
                            internal_error($syntaxerror,
                                'in map transform regex', $.);
                        }
                        my $words = $2;
                        my $match = $1;
                        my @wordarray = split(/\s+/,$words);
                        if(scalar(@wordarray) == 0) {
                            internal_error($syntaxerror,
                                'in map transform regex : no qw arg', $.);
                        }
                        foreach my $word (@wordarray) {
                            push(@transformpairs,[$match, $word]);
                        }
                    } else {
                        internal_error($syntaxerror, 'in last field', $.);
                    }
                }
            }
        }

        return {
            'regtype'   => qr/$regtype/x,
            'regname' => qr/$regname/x,
            'checkmissing' => (not not scalar(@transformpairs)),
            'transform' => \@transformpairs,
        };
    });

# prebuilt-file or forbidden file type
my $RFC_WHITELIST =  Lintian::Data->new(
    'cruft/rfc-whitelist',
    qr/\s*\~\~\s*/,
    sub {
        return qr/$_[0]/xms;
    });

# "Known good" files that match eg. lena.jpg.
my $LENNA_WHITELIST = Lintian::Data->new('cruft/lenna-whitelist');

# prebuilt-file or forbidden copyright
my $BAD_LINK_COPYRIGHT =  Lintian::Data->new(
    'cruft/bad-link-copyright',
    qr/\s*\~\~\s*/,
    sub {
        return qr/$_[1]/xms;
    });

my $MISSING_DIR_SEARCH_PATH
  =  Lintian::Data->new('cruft/missing-dir-search-path');

# get javascript name
sub _minified_javascript_name_regexp {
    my $jsv
      = $WARN_FILE_TYPE->value('source-contains-prebuilt-javascript-object');
    return defined($jsv)
      ? $jsv->{'regname'}
      : qr/(?i)[-._](?:min|pack(?:ed)?)\.js$/;
}

sub _get_license_check_file {
    my ($filename) = @_;
    my $data = Lintian::Data->new(
        $filename,
        qr/\s*\~\~\s*/,
        sub {
            my %LICENSE_CHECK_DISPATCH_TABLE= (
                'license-problem-gfdl-invariants' =>
                  \&_check_gfdl_license_problem,
                'rfc-whitelist-filename' =>\&_rfc_whitelist_filename,
                'php-source-whitelist' => \&_php_source_whitelist,
                #'print-group'          => sub { print($1)},
            );
            my @splitline = split(/\s*\~\~\s*/, $_[1], 5);
            my $syntaxerror = 'Syntax error in '.$filename;
            if(scalar(@splitline) > 5 or scalar(@splitline) <2) {
                internal_error($syntaxerror, $.);
            }
            my ($keywords, $sentence, $regex, $firstregex, $callsub)
              = @splitline;
            $keywords = defined($keywords) ? strip($keywords) : '';
            $sentence = defined($sentence) ? strip($sentence) : '';
            $regex = defined($regex) ? strip($regex) : '';
            $firstregex = defined($firstregex) ? strip($firstregex) : '';
            $callsub = defined($callsub) ? strip($callsub) : '';

            my @keywordlist = split(/\s*\&\&\s*/, $keywords);
            if(scalar(@keywordlist) < 1) {
                internal_error($syntaxerror, 'No keywords on line', $.);
            }
            my @sentencelist = split(/\s*\|\|\s*/, $sentence);
            if(scalar(@sentencelist) < 1) {
                internal_error($syntaxerror, 'No sentence on line', $.);
            }

            if($regex eq '') {
                $regex = '.*';
            }
            if($firstregex eq '') {
                $firstregex = $regex;
            }
            my %ret = (
                'keywords' =>  \@keywordlist,
                'sentence' => \@sentencelist,
                'regex' => qr/$regex/xsm,
                'firstregex' => qr/$firstregex/xsm,
            );
            unless($callsub eq '') {
                if(defined($LICENSE_CHECK_DISPATCH_TABLE{$callsub})) {
                    $ret{'callsub'} = $LICENSE_CHECK_DISPATCH_TABLE{$callsub};
                } else {
                    internal_error($syntaxerror, 'Unknown sub', $.);
                }
            }
            return \%ret;
        });
    return $data;
}

# get usual non distributable license
my $NON_DISTRIBUTABLE_LICENSES
  = _get_license_check_file('cruft/non-distributable-license');

# get non free license
# get usual non distributable license
my $NON_FREE_LICENSES = _get_license_check_file('cruft/non-free-license');

# get usual data about admissible/not admissible GFDL invariant part of license
my $GFDL_FRAGMENTS = Lintian::Data->new(
    'cruft/gfdl-license-fragments-checks',
    qr/\s*\~\~\s*/,
    sub {
        my ($gfdlsectionsregex,$secondpart) = @_;

        # allow empty parameters
        $gfdlsectionsregex
          = defined($gfdlsectionsregex) ? strip($gfdlsectionsregex) : '';

        $secondpart //= '';
        my ($acceptonlyinfile,$applytag)= split(/\s*\~\~\s*/, $secondpart, 2);

        $acceptonlyinfile
          = defined($acceptonlyinfile) ? strip($acceptonlyinfile) : '';
        $applytag =defined($applytag) ? strip($applytag) : '';

        # empty first field is everything
        if (length($gfdlsectionsregex) == 0) {
            $gfdlsectionsregex = '.*';
        }
        # empty regname is none
        if (length($acceptonlyinfile) == 0) {
            $acceptonlyinfile = '.*';
        }

        my %ret = (
            'gfdlsectionsregex'   => qr/$gfdlsectionsregex/xis,
            'acceptonlyinfile' => qr/$acceptonlyinfile/xs,
        );
        unless ($applytag eq '') {
            $ret{'tag'} = $applytag;
        }

        return \%ret;
    });

# The files that contain error messages from tar, which we'll check and issue
# tags for if they contain something unexpected, and their corresponding tags.
our %ERRORS = (
    'index-errors'    => 'tar-errors-from-source',
    'unpacked-errors' => 'tar-errors-from-source'
);

# Directory checks.  These regexes match a directory that shouldn't be in the
# source package and associate it with a tag (minus the leading
# source-contains or diff-contains).  Note that only one of these regexes
# should trigger for any single directory.
my @directory_checks = (
    [qr,^(.+/)?CVS/?$,        => 'cvs-control-dir'],
    [qr,^(.+/)?\.svn/?$,      => 'svn-control-dir'],
    [qr,^(.+/)?\.bzr/?$,      => 'bzr-control-dir'],
    [qr,^(.+/)?\{arch\}/?$,   => 'arch-control-dir'],
    [qr,^(.+/)?\.arch-ids/?$, => 'arch-control-dir'],
    [qr!^(.+/)?,,.+/?$!       => 'arch-control-dir'],
    [qr,^(.+/)?\.git/?$,      => 'git-control-dir'],
    [qr,^(.+/)?\.hg/?$,       => 'hg-control-dir'],
    [qr,^(.+/)?\.be/?$,       => 'bts-control-dir'],
    [qr,^(.+/)?\.ditrack/?$,  => 'bts-control-dir'],

    # Special case (can only be triggered for diffs)
    [qr,^(.+/)?\.pc/?$, => 'quilt-control-dir'],
);

# File checks.  These regexes match files that shouldn't be in the source
# package and associate them with a tag (minus the leading source-contains or
# diff-contains).  Note that only one of these regexes should trigger for any
# given file.  If the third column is a true value, don't issue this tag
# unless the file is included in the diff; it's too common in source packages
# and not important enough to worry about.
my @file_checks = (
    [qr,^(.+/)?svn-commit\.(.+\.)?tmp$, => 'svn-commit-file'],
    [qr,^(.+/)?svk-commit.+\.tmp$,      => 'svk-commit-file'],
    [qr,^(.+/)?\.arch-inventory$,       => 'arch-inventory-file'],
    [qr,^(.+/)?\.hgtags$,               => 'hg-tags-file'],
    [qr,^(.+/)?\.\#(.+?)\.\d+(\.\d+)*$, => 'cvs-conflict-copy'],
    [qr,^(.+/)?(.+?)\.(r[1-9]\d*)$,     => 'svn-conflict-file'],
    [qr,\.(orig|rej)$,                  => 'patch-failure-file', 1],
    [qr,((^|/)\.[^/]+\.swp|~)$,         => 'editor-backup-file', 1],
);

# List of files to check for a LF-only end of line terminator, relative
# to the debian/ source directory
our @EOL_TERMINATORS_FILES = qw(control changelog);

# List of files to check for a trailing whitespace characters relative
# to the debian/ source directory
our @TRAILING_WHITESPACE_FILES = (
    ['debian/changelog'        => qr,\s+\n$,],
    ['debian/control'          => qr,\s+\n$,],
    ['debian/rules'            => qr,[ ]+\n$,], # Allow trailing tabs in Make
);

sub run {
    my (undef, undef, $info, $proc, $group) = @_;
    my $source_pkg = $proc->pkg_src;
    my $d_files = $info->index_resolved_path('debian/files');

    if ($d_files and $d_files->is_file and $d_files->size != 0) {
        tag 'debian-files-list-in-source';
    }

    tag 'package-uses-deprecated-source-override-location'
      if $info->index_resolved_path('debian/source.lintian-overrides');

    # This doesn't really belong here, but there isn't a better place at the
    # moment to put this check.
    my $version = $info->field('version', '0-1');

    if ($info->native) {
        if ($version =~ /-/) {
            tag 'native-package-with-dash-version';
        }
    }else {
        if ($version !~ /-/) {
            tag 'non-native-package-with-native-version';
        }
    }

    # Check if the package build-depends on autotools-dev, automake,
    # or libtool.
    my $ltinbd  = $info->relation('build-depends-all')->implies($LIBTOOL);
    my %warned;
    # Assume the package to be non-native if the field is not present.
    # - while 1.0 is more likely in this case, Lintian will probably get
    #   better results by checking debfiles/ rather than looking for a diffstat
    #   that may not be present.
    my $format = $info->field('format', '3.0 (quilt)');

    if ($format =~ /^\s*2\.0\s*\z/ or $format =~ /^\s*3\.0\s*\(quilt|git\)/) {
        check_debian_dir($info, \%warned);
    }elsif (not $info->native) {
        check_diffstat($info->diffstat, \%warned);
    }
    find_cruft($source_pkg, $info, \%warned, $ltinbd, $group);

    for my $file (@EOL_TERMINATORS_FILES) {
        my $path = $info->index_resolved_path("debian/$file");
        next if not $path or not $path->is_open_ok;
        my $fd = $path->open;
        while (my $line = <$fd>) {
            if ($line =~ m{ \r \n \Z}xsm) {
                tag 'control-file-with-CRLF-EOLs', $path;
                last;
            }
        }
        close($fd);
    }

    for my $file (@TRAILING_WHITESPACE_FILES) {
        my $path = $info->index_resolved_path($file->[0]);
        next if not $path or not $path->is_open_ok;
        my $fd = $path->open;
        while (my $line = <$fd>) {
            tag 'file-contains-trailing-whitespace', "$path (line $.)"
              if ($line =~ $file->[1]);
        }
        close($fd);
    }

    if (my $pycompat = $info->index_resolved_path('debian/pycompat')) {
        tag 'debian-pycompat-is-obsolete' if $pycompat->is_file;
    }

    # Report any error messages from tar while unpacking the source
    # package if it isn't just tar cruft.
    for my $file (keys %ERRORS) {
        my $tag  = $ERRORS{$file};
        my $path = $info->lab_data_path($file);
        if (-s $path) {
            open(my $fd, '<', $path);
            local $_;
            while (<$fd>) {
                chomp;
                s,^(?:[/\w]+/)?tar: ,,;

                # Record size errors are harmless.  Skipping to next
                # header apparently comes from star files.  Ignore all
                # GnuPG noise from not having a valid GnuPG
                # configuration directory.  Also ignore the tar
                # "exiting with failure status" message, since it
                # comes after some other error.
                next if /^Record size =/;
                next if /^Skipping to next header/;
                next if /^gpgv?: /;
                next if /^secmem usage: /;
                next
                  if /^Exiting with failure status due to previous errors/;
                tag $tag, $_;
            }
            close($fd);
        }
    }

    foreach my $file ($info->sorted_orig_index) {
        tag 'source-contains-empty-directory', $file
          if $file->is_dir
          and scalar($file->children) == 0;
    }

    return;
}    # </run>

# -----------------------------------

# Check the diff for problems.  Record any files we warn about in $warned so
# that we don't warn again when checking the full unpacked source.  Takes the
# name of a file containing diffstat output.
sub check_diffstat {
    my ($diffstat, $warned) = @_;
    my $saw_file;
    open(my $fd, '<', $diffstat);
    local $_;
    while (<$fd>) {
        my ($file) = (m,^\s+(.*?)\s+\|,)
          or internal_error("syntax error in diffstat file: $_");
        $saw_file = 1;

        # Check for CMake cache files.  These embed the source path and hence
        # will cause FTBFS on buildds, so they should never be touched in the
        # diff.
        if (    $file =~ m,(?:^|/)CMakeCache.txt\z,
            and $file !~ m,(?:^|/)debian/,){
            tag 'diff-contains-cmake-cache-file', $file;
        }

        # For everything else, we only care about diffs that add files.  If
        # the file is being modified, that's not a problem with the diff and
        # we'll catch it later when we check the source.  This regex doesn't
        # catch only file adds, just any diff that doesn't remove lines from a
        # file, but it's a good guess.
        next unless m,\|\s+\d+\s+\++$,;

        # diffstat output contains only files, but we consider the directory
        # checks to trigger if the diff adds any files in those directories.
        my ($directory) = ($file =~ m,^(.*)/[^/]+$,);
        if ($directory and not $warned->{$directory}) {
            for my $rule (@directory_checks) {
                if ($directory =~ /$rule->[0]/) {
                    tag "diff-contains-$rule->[1]", $directory;
                    $warned->{$directory} = 1;
                }
            }
        }

        # Now the simpler file checks.
        for my $rule (@file_checks) {
            if ($file =~ /$rule->[0]/) {
                tag "diff-contains-$rule->[1]", $file;
                $warned->{$file} = 1;
            }
        }

        # Additional special checks only for the diff, not the full source.
        if ($file =~ m@^debian/(?:.+\.)?substvars$@) {
            tag 'diff-contains-substvars', $file;
        }
    }
    close($fd);

    # If there was nothing in the diffstat output, there was nothing in the
    # diff, which is probably a mistake.
    tag 'empty-debian-diff' unless $saw_file;
    return;
}

# Check the debian directory for problems.  This is used for Format: 2.0 and
# 3.0 (quilt) packages where there is no Debian diff and hence no diffstat
# output.  Record any files we warn about in $warned so that we don't warn
# again when checking the full unpacked source.
sub check_debian_dir {
    my ($info, $warned) = @_;
    my $droot = $info->index_resolved_path('debian/');
    return if not $droot;

    my @worklist = $droot->children;

    # Check for unwanted directories and files.  This really
    # duplicates the find_cruft function and we should find a way to
    # combine them.

  ENTRY:
    while (my $entry = shift(@worklist)) {
        my $name     = $entry->name;

        if ($entry->is_dir) {
            # Remove the trailing slash (historically we never
            # included the slash for these tags and there is no
            # particular reason to change that now).
            $name     = substr($name,     0, -1);

            for my $rule (@directory_checks) {
                if ($name =~ /$rule->[0]/) {
                    tag "diff-contains-$rule->[1]", $name;
                    $warned->{$name} = 1;
                }
            }
            push(@worklist, $entry->children);
        } else {

            for my $rule (@file_checks) {
                if ($name =~ /$rule->[0]/) {
                    tag "diff-contains-$rule->[1]", $entry;
                    $warned->{$name} = 1;
                }
            }

            # Additional special checks only for the diff, not the
            # full source.
            if ($name =~ m@^debian/(?:.+\.)?substvars$@o) {
                tag 'diff-contains-substvars', $entry;
            }
        }
    }
    return;
}

# testset exception
sub istestset {
    my ($dirname) = @_;
    return $dirname
      =~ m{ (:?\A|/) t (?: est (?: s (?: et)?+ )?+ )?+ (?: \Z | /)}xsm;
}

# Check each file in the source package for problems.  By the time we get to
# this point, we've already checked the diff and warned about anything added
# there, so we only warn about things that weren't in the diff here.
#
# Report problems with native packages using the "diff-contains" rather than
# "source-contains" tag.  The tag isn't entirely accurate, but it's better
# than creating yet a third set of tags, and this gets the severity right.
sub find_cruft {
    my ($source_pkg, $info, $warned, $ltinbd, $group) = @_;
    my $prefix = ($info->native ? 'diff-contains' : 'source-contains');
    my @worklist;
    my $ships_examples = _ships_examples($group);

    # start with the top-level dirs
    push(@worklist, $info->index('')->children);

  ENTRY:
    while (my $entry = shift(@worklist)) {
        my $name     = $entry->name;
        my $basename = $entry->basename;
        my $dirname = $entry->dirname;
        my $file_info;
        my $istestsetdir = istestset($dirname);

        if ($entry->is_dir) {

            # Remove the trailing slash (historically we never
            # included the slash for these tags and there is no
            # particular reason to change that now).
            $name     = substr($name,     0, -1);
            $basename = substr($basename, 0, -1);

            # Ignore the .pc directory and its contents, created as
            # part of the unpacking of a 3.0 (quilt) source package.

            # NB: this catches all .pc dirs (regardless of depth).  If you
            # change that, please check we have a
            # "source-contains-quilt-control-dir" tag.
            next if $basename eq '.pc';

            if (not $istestsetdir and not $warned->{$name}) {
                for my $rule (@directory_checks) {
                    if ($basename =~ /$rule->[0]/) {
                        tag "${prefix}-$rule->[1]", $name;

                        # At most one rule will match
                        last;
                    }
                }
                tag 'package-does-not-install-examples', $entry
                  if $basename eq 'examples' and not $ships_examples;
            }

            push(@worklist, $entry->children);
            next ENTRY;
        }
        if ($entry->is_symlink) {
            next ENTRY if $istestsetdir;

            # An absolute link always escapes the root (of a source
            # package).  For relative links, it escapes the root if we
            # cannot normalize it.
            if ($entry->link =~ m{\A / }xsm
                or not defined($entry->link_normalized)){
                tag 'source-contains-unsafe-symlink', $name;
            }
            next ENTRY;
        }

        # we just need normal files for the rest
        next ENTRY unless $entry->is_file;
        # avoid lintian testset
        next ENTRY if $source_pkg eq 'lintian' && $istestsetdir;

        # check non free file
        my $md5sum = $info->md5sums->{$name};
        if(
            _md5sum_based_check(
                $name, $md5sum, $NON_DISTRIBUTABLE_FILES,
                'license-problem-md5sum-non-distributable-file'
            )
          ) {
            next ENTRY;
        }
        unless ($info->is_non_free) {
            _md5sum_based_check($name, $md5sum, $NON_FREE_FILES,
                'license-problem-md5sum-non-free-file');
        }

        $file_info = $entry->file_info;

        # check full text problem
        full_text_check($source_pkg, $entry, $info, $name, $basename,$dirname);

        # waf is not allowed
        if ($basename =~ /\bwaf$/) {
            my $marker = 0;
            my $fd = $entry->open;
            while (my $line = <$fd>) {
                next unless $line =~ m/^#/o;
                if ($marker && $line =~ m/^#BZ[h0][0-9]/o) {
                    tag 'source-contains-waf-binary', $name;
                    last;
                }
                $marker = 1 if $line =~ m/^#==>/o;

                # We could probably stop here, but just in case
                $marker = 0 if $line =~ m/^#<==/o;
            }
            close($fd);
        }

        # .chm files are usually generated by non-free software
        if (   $basename =~ /\.chm$/i
            && $file_info eq 'MS Windows HtmlHelp Data'
            && $entry->is_open_ok
            && index($entry->file_contents, 'Halibut,') == -1) {
            tag 'source-contains-prebuilt-ms-help-file', $name;
        }

        # Ensure we have a README.source for R data files
        if (   $basename =~ m,\.(?:rda|Rda|rdata|Rdata|RData)$,
            && $entry->is_file
            && !$info->index_resolved_path('debian/README.source')) {
            tag 'r-data-without-readme-source', $name;
        }

        if (   $name =~ m,configure.(in|ac)$,
            && $entry->is_file
            && $entry->is_open_ok) {
            my $fd = $entry->open;
            while (my $line = <$fd>) {
                next if $line =~ m{^\s*dnl};
                tag 'autotools-pkg-config-macro-not-cross-compilation-safe',
                  $name, "(line $.)"
                  if $line=~ m{AC_PATH_PROG\s*\([^,]+,\s*\[?pkg-config\]?\s*,};
            }
            close($fd);
        }

        # Lena Söderberg image
        if ($basename =~ /\blenn?a\b/i) {
            if(    $file_info =~ /\bimage\b/i
                or $file_info =~ /^Matlab v\d+ mat/i
                or $file_info =~ /\bbitmap\b/i
                or $file_info =~ /^PDF Document\b/i
                or $file_info =~ /^Postscript Document\b/i) {
                tag 'license-problem-non-free-img-lenna', $name
                  unless $LENNA_WHITELIST->known($md5sum);
            }

        }

        next ENTRY if $istestsetdir;

        # warn by file type
        foreach my $tag_filetype ($WARN_FILE_TYPE->all) {
            my $warn_data = $WARN_FILE_TYPE->value($tag_filetype);
            my $regtype = $warn_data->{'regtype'};
            if($file_info =~ m{$regtype}) {
                my $regname = $warn_data->{'regname'};
                if($name =~ m{$regname}) {
                    tag $tag_filetype, $name;
                    if($warn_data->{'checkmissing'}) {
                        check_missing_source($entry,$info,$name, $basename,
                            $dirname,$warn_data->{'transform'});
                    }
                }
            }
        }

        # here we check old upstream specification
        # debian/upstream should be a directory
        if (   $name eq 'debian/upstream'
            || $name eq 'debian/upstream-metadata.yaml') {
            tag 'debian-upstream-obsolete-path', $name;
        }

        if (   $name eq 'debian/README.source'
            && $entry->is_file
            && $entry->is_open_ok) {
            my $contents = $entry->file_contents;
            if (
                index($contents,
                    'You WILL either need to modify or delete this file') >= 0
              ) {
                tag 'readme-source-is-dh_make-template';
            }
        }

        if (   $name =~ m{^debian/(README.source|copyright|rules|control)$}
            && $entry->is_file
            && $entry->is_open_ok) {
            my $fd = $entry->open;
            while (my $line = <$fd>) {
                next unless $line =~ m/(?<!")(FIX_?ME)(?!")/;
                tag 'file-contains-fixme-placeholder', "$name:$. $1";
            }
        }

        # Find mentioning of usr/lib/perl5 inside the packaging
        if ($name =~ m{^debian/}) {
            my $short = $entry->basename;

            # Skip symlinks and other nasty stuff as well as
            # debian/changelog
            if (   $short ne 'changelog'
                && $name !~ m{^debian/patches/.*$}
                && $entry->is_file
                && $entry->is_open_ok) {
                my $contents = $entry->file_contents;

                # ignore comments
                $contents =~ s/#.*$//m;
                if (index($contents, 'usr/lib/perl5') >= 0) {
                    tag 'mentions-deprecated-usr-lib-perl5-directory', $short;
                }
            }
        }

        if (   $basename eq 'doxygen.png'
            or $basename eq 'doxygen.sty') {
            unless ($source_pkg eq 'doxygen') {
                tag 'source-contains-prebuilt-doxygen-documentation', $dirname;
            }
        }

        unless ($warned->{$name}) {
            for my $rule (@file_checks) {
                next if ($rule->[2] and not $info->native);
                if ($basename =~ /$rule->[0]/) {
                    tag "${prefix}-$rule->[1]", $name;
                }
            }
        }

        # Tests of autotools files are a special case.  Ignore
        # debian/config.cache as anyone doing that probably knows what
        # they're doing and is using it as part of the build.
        if ($basename =~ m{\A config.(?:cache|log|status) \Z}xsm) {
            if ($dirname ne 'debian') {
                tag 'configure-generated-file-in-source', $name;
            }
        }elsif ($basename eq 'ltconfig' and not $ltinbd) {
            tag 'ancient-libtool', $name;
        }elsif ($basename eq 'ltmain.sh', and not $ltinbd) {
            my $fd = $entry->open;
            while (<$fd>) {
                if (/^VERSION=[\"\']?(1\.(\d)\.(\d+)(?:-(\d))?)/) {
                    my ($version, $major, $minor, $debian)=($1, $2, $3, $4);
                    if ($major < 5 or ($major == 5 and $minor < 2)) {
                        tag 'ancient-libtool', $name, $version;
                    }elsif ($minor == 2 and (!$debian || $debian < 2)) {
                        tag 'ancient-libtool', $name, $version;
                    }
                    last;
                }
            }
            close($fd);
        }
    }
    return;
}

# try to check if source is missing
sub check_missing_source {
    my ($file, $info, $name, $basename, $dirname,$replacementspairref,
        $extratext)
      = @_;
    my $basename_of_dirname = basename($dirname);
    $extratext //= '';

    # do not check missing source for non free
    if($info->is_non_free) {
        return;
    }

    my @replacementspair;
    if(defined($replacementspairref)) {
        @replacementspair = @{$replacementspairref};
    }

    unless ($file->is_regular_file) {
        return;
    }

    # try to find for each replacement
  REPLACEMENT:
    foreach my $pair (@replacementspair) {
        my $newbasename = $basename;

        my ($match, $replace) = @{$pair};

        if($match eq '') {
            $newbasename = $basename;
        } else {
            $newbasename =~ s/$match/$replace/;
        }
        # next but we may be return an error
        if($newbasename eq '') {
            next REPLACEMENT;
        }
        # now try for each path
      PATH:
        foreach my $path ($MISSING_DIR_SEARCH_PATH->all) {
            my $newpath;
            # first replace dir name
            $path =~ s/\$dirname/$dirname/g;
            $path =~ s/\$basename_of_dirname/$basename_of_dirname/g;
            # absolute path
            if(substr($path,0,1) eq '/') {
                $path =~ s,^/+,,g;
                $newpath = normalize_pkg_path($path.'/'.$newbasename);
            }
            # relative path
            else {
                $newpath
                  = normalize_pkg_path($dirname.'/'.$path.'/'.$newbasename);
            }
            # path outside package
            if(!defined($newpath)) {
                next PATH;
            }
            # ok we get same name => next
            if($newpath eq $name) {
                next PATH;
            }
            # do not check empty
            if($newpath eq '') {
                next PATH;
            }
            # found source file or directory
            if($info->index_resolved_path($newpath)) {
                return;
            }
        }
    }
    tag 'source-is-missing', $name, $extratext;
    return;
}

# do basic license check against well known offender
# note that it does not replace licensecheck(1)
# and is only used for autoreject by ftp-master
sub full_text_check {
    my ($source_pkg, $entry, $info, $name, $basename, $dirname) = @_;

    # license string in debian/changelog are probably just change
    # Ignore these strings in d/README.{Debian,source}.  If they
    # appear there it is probably just "file XXX got removed
    # because of license Y".
    if (   $name eq 'debian/changelog'
        or $name eq 'debian/README.Debian'
        or $name eq 'debian/README.source') {
        return;
    }

    my $fd = $entry->open(':raw');
    # check only text files
    unless (-T $fd) {
        close($fd);
        return;
    }

    # some js file comments are really really long
    my $sfd= Lintian::SlidingWindow->new($fd, \&lc_block, BLOCKSIZE);
    my %licenseproblemhash;

    # we try to read this file in block and use a sliding window
    # for efficiency.  We store two blocks in @queue and the whole
    # string to match in $block. Please emit license tags only once
    # per file
  BLOCK:
    while (my $block = $sfd->readwindow) {
        my ($cleanedblock, %matchedkeyword);
        my $blocknumber = $sfd->blocknumber;

        # Check for non-distributable files - this
        # applies even to non-free, as we still need
        # permission to distribute those.
        if(
            _license_check(
                $info, $source_pkg,
                $name,$basename,
                $NON_DISTRIBUTABLE_LICENSES,$block,
                $blocknumber,\$cleanedblock,
                \%matchedkeyword,\%licenseproblemhash
            )
          ){
            return;
        }

        # Skip the rest of the license checks for non-free
        # sections.
        if ($info->is_non_free) {
            next BLOCK;
        }

        _license_check(
            $info, $source_pkg, $name,
            $basename,$NON_FREE_LICENSES,$block,
            $blocknumber,\$cleanedblock, \%matchedkeyword,
            \%licenseproblemhash
        );

        # check only in block 0
        if($blocknumber == 0) {
            _search_in_block0($entry, $info, $name, $basename, $dirname,
                $block);
        }
    }
    close($fd);
    return;
}

# check if file is javascript but not minified
sub _is_javascript_but_not_minified {
    my ($name) = @_;
    my $isjsfile = ($name =~ m/\.js$/) ? 1 : 0;
    if($isjsfile) {
        my $minjsregexp =  _minified_javascript_name_regexp();
        $isjsfile = ($name =~ m{$minjsregexp}) ? 0 : 1;
    }
    return $isjsfile;
}

# search something in block $0
sub _search_in_block0 {
    my ($entry, $info, $name, $basename, $dirname, $block) = @_;

    if(_is_javascript_but_not_minified($name)) {
        # exception sphinx documentation
        if($basename eq 'searchindex.js') {
            if($block =~ m/\A\s*search\.setindex\s* \s* \(\s*\{/xms) {
                tag 'source-contains-prebuilt-sphinx-documentation', $dirname;
                return;
            }
        }
        if($basename eq 'search_index.js') {
            if($block =~ m/\A\s*var\s*search_index\s*=/xms) {
                tag 'source-contains-prebuilt-pandoc-documentation', $dirname;
                return;
            }
        }
        # false positive in dx package at least
        elsif($basename eq 'srchidx.js') {
            if($block =~ m/\A\s*profiles \s* = \s* new \s* Array\s*\(/xms) {
                return;
            }
        }
        # see #745152
        # Be robust check also .js
        elsif($basename eq 'deployJava.js') {
            if($block =~ m/(?:\A|\v)\s*var\s+deployJava\s*=\s*function/xmsi) {
                check_missing_source($entry,$info,$name,$basename,$dirname,
                    [['(?i)\.js$','.txt'],['','']]);
                return;
            }
        }
        # https://github.com/rafaelp/css_browser_selector is actually the
        # original source. (#874381)
        elsif ($block =~ m/css_browser_selector\(/) {
            return;
        }
        # Avoid false-positives in Jush's syntax highlighting definition files.
        elsif ($block =~ m/jush\.tr\./) {
            return;
        }

        # now search hidden minified
        _linelength_test($entry, $info, $name, $basename, $dirname,$block);
    }
    # search link rel header
    if(index($block,' rel="copyright" ') > -1) {
        my $href = $block;
        $href =~ m,<link \s+
                  rel="copyright" \s+
                  href="([^"]+)" \s*/? \s*>,xmsi;
        if(defined($1)) {
            my $copyrighttarget = $1;
            foreach my $badcopyrighttag ($BAD_LINK_COPYRIGHT->all) {
                my $regex =  $BAD_LINK_COPYRIGHT->value($badcopyrighttag);
                if($copyrighttarget =~ m{$regex}) {
                    tag $badcopyrighttag, $name;
                    last;
                }
            }
        }
    }
    return;
}

# warn about prebuilt javascript and check missing source
sub _warn_prebuilt_javascript{
    my ($entry, $info, $name, $basename, $dirname,$linelength,$cutoff) = @_;
    my $extratext
      =  'line length is '.int($linelength)." characters (>$cutoff)";
    tag 'source-contains-prebuilt-javascript-object',$name,$extratext;
    # Check for missing source.  It will check
    # for the source file in well known directories
    check_missing_source($entry,$info,$name,$basename,$dirname,
        [['(?i)\.js$','.debug.js'],['(?i)\.js$','-debug.js'],['','']],
        $extratext);
    return;
}

# detect if max line of block is > cutoff
# return false if file is minified
sub _linelength_test_maxlength {
    my ($block, $cutoff) = @_;
    while($block =~ /([^\n]+)\n?/g){
        my $linelength = length($1);
        if($linelength > $cutoff) {
            return ($linelength,$1,substr($block,pos($block)));
        }
    }
    return (0,'',$block);
}

# strip C comment
# warning block is at more 8192 char in order to be too slow
# and in order to avoid regex recursion
sub _strip_c_comments {
    my ($block) = @_;
    # from perl faq strip comments
    $block =~ s{
                # Strip /* */ comments
                /\* [^*]*+ \*++ (?: [^/*][^*]*+\*++ ) */
                # Strip // comments (C++ style)
                |  // (?: [^\\] | [^\n][\n]? )*? (?=\n)
                |  (
                    # Keep "/* */" (etc) as is
                    "(?: \\. | [^"\\]++)*"
                    # Keep '/**/' (etc) as is
                    | '(?: \\. | [^'\\]++)*'
                    # Keep anything else
                    | .[^/"'\\]*+
                   )
               }{defined $1 ? $1 : ""}xgse;
    return $block;
}

# try to detect non human source based on line length
sub _linelength_test {
    my ($entry, $info, $name, $basename, $dirname, $block) = @_;
    my $linelength = 0;
    my $line;
    my $nextblock;

    ($linelength)= _linelength_test_maxlength($block,INSANE_LINE_LENGTH);
    # first check if line >  INSANE_LINE_LENGTH that is likely minification
    # avoid problem by recursive regex with longline
    if($linelength) {
        tag 'insane-line-length-in-source-file', $name,
          'line length is', int($linelength),
          'characters (>'.INSANE_LINE_LENGTH.')';
        # clean up jslint craps line
        $block =~ s,^\s*/[*][^\n]*[*]/\s*$,,gm;
        $block =~ s,^\s*//[^\n]*$,,gm;
        $block =~ s/^\s+//gm;

        # try to remove comments in first 8192 block (license...)
        my $block8192 = substr($block,0,8192);
        $block8192 = _strip_c_comments($block8192);
        $block
          = length($block) > 8192
          ? $block8192.substr($block,8192)
          : $block8192;

        # strip empty line
        $block =~ s/^\s*\n//mg;
        # remove last \n
        $block =~ s/\n\Z//m;

        # retry insane line length test now: if insane length likely minified
        ($linelength)= _linelength_test_maxlength($block,INSANE_LINE_LENGTH);

        if($linelength) {
            _warn_prebuilt_javascript($entry, $info, $name, $basename,
                $dirname,$linelength,INSANE_LINE_LENGTH);
            return;
        }
    }
    # Now try to be more clever and work only on the 8192 character
    # in order to avoid regexp recursion problems
    my $strip = substr($block,0,8192);
    # strip indention
    $strip =~ s/^\s+//mg;
    $strip = _strip_c_comments($block);
    # strip empty line
    $strip =~ s/^\s*\n//mg;
    # remove last \n
    $strip =~ s/\n\Z//m;
    $nextblock = $strip;
    while(length($nextblock)) {
        # check line above > SAFE_LINE_LENGTH
        ($linelength,$line,$nextblock)
          = _linelength_test_maxlength($nextblock,SAFE_LINE_LENGTH);
        # no long line
        unless($linelength) {
            return;
        }
        # compute number of ;
        if(($line =~ tr/;/;/) > 1) {
            _warn_prebuilt_javascript($entry, $info, $name, $basename,
                $dirname,$linelength,SAFE_LINE_LENGTH);
            return;
        }
    }
    return;
}

sub _tag_gfdl {
    my ($applytag, $name, $gfdlsections) = @_;
    tag $applytag, $name, 'invariant part is:', $gfdlsections;
    return;
}

# return True in case of license problem
sub _check_gfdl_license_problem {
    my (
        $info, $source_pkg, $name,
        $basename,$block,$blocknumber,
        $cleanedblock,$matchedkeyword,$licenseproblemhash,
        $licenseproblem,%matchedhash
    )= @_;
    my $rawgfdlsections  = $matchedhash{rawgfdlsections}  || '';
    my $rawcontextbefore = $matchedhash{rawcontextbefore} || '';

    # strip punctuation
    my $gfdlsections  = _strip_punct($rawgfdlsections);
    my $contextbefore = _strip_punct($rawcontextbefore);

    # remove line number at beginning of line
    # see krusader/1:2.4.0~beta3-2/doc/en_US/advanced-functions.docbook/
    $gfdlsections =~ s{[ ]\d+[ ]}{ }gxsmo;
    $gfdlsections =~ s{^\d+[ ]}{ }xsmo;
    $gfdlsections =~ s{[ ]\d+$}{ }xsmo;
    $gfdlsections =~ s{[ ]+}{ }xsmo;

    # remove classical and without meaning part of
    # matched string
    my $oldgfdlsections;
    do {
        $oldgfdlsections = $gfdlsections;
        $gfdlsections =~ s{ \A \(?[ ]? g?fdl [ ]?\)?[ ]? [,\.;]?[ ]?}{}xsmo;
        $gfdlsections =~ s{ \A (?:either[ ])?
                           version [ ] \d+(?:\.\d+)? [ ]?}{}xsmo;
        $gfdlsections =~ s{ \A of [ ] the [ ] license [ ]?[,\.;][ ]?}{}xsmo;
        $gfdlsections=~ s{ \A or (?:[ ]\(?[ ]? at [ ] your [ ] option [ ]?\)?)?
                           [ ] any [ ] later [ ] version[ ]?}{}xsmo;
        $gfdlsections =~ s{ \A (as[ ])? published [ ] by [ ]
                           the [ ] free [ ] software [ ] foundation[ ]?}{}xsmo;
        $gfdlsections =~ s{\(?[ ]? fsf [ ]?\)?[ ]?}{}xsmo;
        $gfdlsections =~ s{\A [ ]? [,\.;]? [ ]?}{}xsmo;
        $gfdlsections =~ s{[ ]? [,\.]? [ ]?\Z}{}xsmo;
    } while ($oldgfdlsections ne $gfdlsections);

    $contextbefore =~ s{
                       [ ]? (:?[,\.;]? [ ]?)?
                       permission [ ] is [ ] granted [ ] to [ ] copy [ ]?[,\.;]?[ ]?
                       distribute [ ]?[,\.;]?[ ]? and[ ]?/?[ ]?or [ ] modify [ ]
                       this [ ] document [ ] under [ ] the [ ] terms [ ] of [ ] the\Z}{}xsmo;

    # Treat ambiguous empty text
    unless(
        defined(
            $licenseproblemhash->{'license-problem-gfdl-invariants-empty'})
      ) {
        if ($gfdlsections eq '') {
            # lie in order to check more part
            tag 'license-problem-gfdl-invariants-empty', $name;
            $licenseproblemhash->{'license-problem-gfdl-invariants-empty'}= 1;
            return 0;
        }
    }

    # official wording
    if(
        $gfdlsections =~ m/\A
                          with [ ] no [ ] invariant [ ] sections[ ]?,
                          [ ]? no [ ] front(?:[ ]?-[ ]?|[ ])cover [ ] texts[ ]?,?
                          [ ]? and [ ] no [ ] back(?:[ ]?-?[ ]?|[ ])cover [ ] texts
                          \Z/xso
      ) {
        return 0;
    }

    # example are ok
    if (
        $contextbefore =~ m/following [ ] is [ ] an [ ] example
                           (:?[ ] of [ ] the [ ] license [ ] notice [ ] to [ ] use
                            (?:[ ] after [ ] the [ ] copyright [ ] (?:line(?:\(s\)|s)?)?
                             (?:[ ] using [ ] all [ ] the [ ] features? [ ] of [ ] the [ ] gfdl)?
                            )?
                           )? [ ]? [,:]? \Z/xso
      ){
        return 0;
    }

    # GFDL license, assume it is bad unless it
    # explicitly states it has no "bad sections".
    foreach my $gfdl_fragment ($GFDL_FRAGMENTS->all) {
        my $gfdl_data = $GFDL_FRAGMENTS->value($gfdl_fragment);
        my $gfdlsectionsregex = $gfdl_data->{'gfdlsectionsregex'};
        if ($gfdlsections =~ m{$gfdlsectionsregex}) {
            my $acceptonlyinfile = $gfdl_data->{'acceptonlyinfile'};
            if ($name =~ m{$acceptonlyinfile}) {
                my $applytag = $gfdl_data->{'tag'};
                if(defined($applytag)) {
                    unless(defined($licenseproblemhash->{$applytag})) {
                        # lie will allow checking more blocks
                        _tag_gfdl($applytag, $name, $gfdlsections);
                        $licenseproblemhash->{$applytag} = 1;
                        return 0;
                    }
                }
                return 0;
            }else {
                _tag_gfdl('license-problem-gfdl-invariants',
                    $name, $gfdlsections);
                return 1;
            }
        }
    }

    # catch all clause
    _tag_gfdl('license-problem-gfdl-invariants', $name, $gfdlsections);
    return 1;
}

# whitelist good rfc
sub _rfc_whitelist_filename {
    my (
        $info, $source_pkg, $name,
        $basename,$block,$blocknumber,
        $cleanedblock,$matchedkeyword,$licenseproblemhash,
        $licenseproblem,%matchedhash
    )= @_;
    return 0 if $name eq 'debian/copyright';
    my $lcname = lc($basename);

    foreach my $rfc_regexp ($RFC_WHITELIST->all) {
        my $regex = $RFC_WHITELIST->value($rfc_regexp);
        if($lcname =~ m/$regex/xms) {
            return 0;
        }
    }
    tag $licenseproblem, $name;
    return 1;
}

# whitelist php source
sub _php_source_whitelist {
    my (
        $info, $source_pkg, $name,
        $basename,$block,$blocknumber,
        $cleanedblock,$matchedkeyword,$licenseproblemhash,
        $licenseproblem,%matchedhash
    )= @_;

    my $copyright_path = $info->index_resolved_path('debian/copyright');
    if (    $copyright_path
        and $copyright_path->file_contents
        =~ m{^Source: https?://pecl.php.net/package/.*$}m) {
        return 0;
    }

    if($source_pkg =~ m,^php\d*(?:\.\d+)?$,xms) {
        return 0;
    }
    tag $licenseproblem, $name;
    return 1;
}

sub _clean_block {
    my ($text) = @_;

    # be paranoiac replace gnu with texinfo by gnu
    $text =~ s{
                 (?:@[[:alpha:]]*?\{)?\s*gnu\s*\}                   # Texinfo cmd
             }{ gnu }gxms;

    # pod2man formatting
    $text =~ s{ \\ \* \( [LR] \" }{\"}gxsm;
    $text =~ s{ \\ -}{-}gxsm;

    # replace some shortcut (clisp)
    $text =~ s{\(&fdl;\)}{ }gxsm;
    $text =~ s{&fsf;}{free software foundation}gxsm;

    # non breaking space
    $text =~ s{&nbsp;}{ }gxsm;

    # replace some common comment-marker/markup with space
    $text =~ s{^\.\\\"}{ }gxms;               # man comments

    # po comment may include html tag
    $text =~ s/\"\s?\v\#~\s?\"//gxms;

    # strip .rtf paragraph marks (#892967)
    $text =~ s/\\par\b//gxms;

    $text =~ s/\\url[{][^}]*?[}]/ /gxms;      # (la)?tex url
    $text =~ s/\\emph[{]/ /gxms;              # (la)?tex emph
    $text =~ s/\\href[{][^}]*?[}]
                     [{]([^}]*?)[}]/ $1 /gxms;# (la)?tex href
    $text =~ s/\\hyperlink
                 [{][^}]*?[}]
                 [{]([^}]*?)[}]/ $1 /gxms;    # (la)?tex hyperlink
    $text =~ s,-\\/,-,gxms;                   # tex strange hyphen
    $text =~ s,\\char, ,gxms;                 # tex  char command

    # Texinfo comment with end section
    $text =~ s/\@c(?:omment)?\h+
                end \h+ ifman\s+/ /gxms;
    $text =~ s/\@c(?:omment)?\s+
                noman\s+/ /gxms;              # Texinfo comment no manual

    $text =~ s/\@c(?:omment)?\s+/ /gxms;      # Texinfo comment

    # Texinfo bold,italic, roman, fixed width
    $text =~ s/\@[birt][{]/ /gxms;
    $text =~ s/\@sansserif[{]/ /gxms;         # Texinfo sans serif
    $text =~ s/\@slanted[{]/ /gxms;             # Texinfo slanted
    $text =~ s/\@var[{]/ /gxms;                 # Texinfo emphasis

    $text =~ s/\@(?:small)?example\s+/ /gxms; # Texinfo example
    $text =~ s/\@end \h+
               (?:small)example\s+/ /gxms;    # Texinfo end example tag
    $text =~ s/\@group\s+/ /gxms;             # Texinfo group
    $text =~ s/\@end\h+group\s+/ /gxms;       # Texinfo end group

    $text =~ s/<!--/ /gxms;                   # XML comments
    $text =~ s/-->/ /gxms;                    # end XML comment

    $text =~ s{</?a[^>]*?>}{ }gxms;           # a link
    $text =~ s{<br\s*/?>}{ }gxms;             # (X)?HTML line
    # breaks
    $text =~ s{</?citetitle[^>]*?>}{ }gxms;   # DocBook citation title
    $text =~ s{</?div[^>]*?>}{ }gxms;         # html style
    $text =~ s{</?font[^>]*?>}{ }gxms;        # font
    $text =~ s{</?i[^>]*?>}{ }gxms;           # italic
    $text =~ s{</?link[^>]*?>}{ }gxms;        # xml link
    $text =~ s{</?p[^>]*?>}{ }gxms;           # html paragraph
    $text =~ s{</?quote[^>]*?>}{ }gxms;       # xml quote
    $text =~ s{</?span[^>]*?>}{ }gxms;        # span tag
    $text =~ s{</?ulink[^>]*?>}{ }gxms;       # ulink DocBook
    $text =~ s{</?var[^>]*?>}{ }gxms;         # var used by texinfo2html

    $text =~ s{\&[lr]dquo;}{ }gxms;           # html rquote

    $text =~ s{\(\*note.*?::\)}{ }gxms;       # info file note

    # String array (e.g. "line1",\n"line2")
    $text =~ s/\"\s*,/ /gxms;
    # String array (e.g. "line1"\n ,"line2"),
    $text =~ s/,\s*\"/ /gxms;
    $text =~ s/\\n/ /gxms;                    # Verbatim \n in string array

    $text =~ s/\\&/ /gxms;                    # pod2man formatting
    $text =~ s/\\s(?:0|-1)/ /gxms;            # pod2man formatting

    $text =~ s/(?:``|'')/ /gxms;              # quote like

    # diff/patch lines (should be after html tag)
    $text =~ s/^[-\+!<>]/ /gxms;
    $text =~ s/\@\@ \s*
               [-+] \d+,\d+ \s+
               [-+] \d+,\d+ \s*
               \@\@/ /gxms;                   # patch line

    # Texinfo end tag (could be more clever but brute force is fast)
    $text =~ s/}/ /gxms;
    # Tex section titles
    $text =~ s/^\s*\\(sub)*section\*?\{\s*\S+/ /gxms;
    # single char at end
    # String, C-style comment/javadoc indent,
    # quotes for strings, pipe and backslash, tilde in some txt
    $text =~ s,[%\*\"\|\\\#~], ,gxms;
    # delete double spacing now and normalize spacing
    # to space character
    $text =~ s{\s++}{ }gsm;
    strip($text);

    return $text;
}

# do not use space around punctuation
sub _strip_punct() {
    my ($text) = @_;
    # replace final punctuation
    $text =~ s{(?:
        \s*[,\.;]\s*\Z               |  # final punctuation
        \A\s*[,\.;]\s*                  # punctuation at the beginning
    )}{ }gxms;

    # delete double spacing now and normalize spacing
    # to space character
    $text =~ s{\s++}{ }gsm;
    strip($text);

    return $text;
}

sub lc_block {
    return $_ = lc($_);
}

# check based on md5sums
sub _md5sum_based_check {
    my ($name, $md5sum, $data, $tag) = @_;
    if (my $datavalue = $data->value($md5sum)) {
        my $usualname= $datavalue->{'name'};
        my $reason= $datavalue->{'reason'};
        my $link= $datavalue->{'link'};
        tag $tag, $name,
          'usual name is', "$usualname.", "$reason", "See also $link.";

        # should be stripped so pass other test
        return 1;
    }
    return 0;
}

# check bad license
sub _license_check {
    my (
        $info, $source_pkg, $name,
        $basename,$licensesdatas, $block,
        $blocknumber,$cleanedblock,$matchedkeyword,
        $licenseproblemhash
    )= @_;
    my $ret = 0;

    # avoid to check lintian
    if($source_pkg eq 'lintian') {
        return $ret;
    }
  LICENSE:
    foreach my $licenseproblem ($licensesdatas->all) {
        my $licenseproblemdata = $licensesdatas->value($licenseproblem);
        if(defined($licenseproblemhash->{$licenseproblem})) {
            next LICENSE;
        }
        # do fast keyword search
        my @keywordslist = @{$licenseproblemdata->{'keywords'}};
        foreach my  $keyword (@keywordslist) {
            my $thiskeyword = $matchedkeyword->{$keyword};
            if(not defined($thiskeyword)) {
                if(index($block, $keyword) > -1) {
                    $matchedkeyword->{$keyword} = 1;
                }else {
                    $matchedkeyword->{$keyword} = 0;
                    next LICENSE;
                }
            } elsif ($thiskeyword == 0) {
                next LICENSE;
            }
        }
        # clean block now in order to normalise space and check a sentence
        unless(defined($$cleanedblock)) {
            $$cleanedblock = _clean_block($block);
        }

        my $foundsentence = 0;
        my @sentencelist =  @{$licenseproblemdata->{'sentence'}};
        foreach my $sentence (@sentencelist) {
            if(index($$cleanedblock,$sentence) > -1){
                $foundsentence = 1;
            }
        }

        unless($foundsentence) {
            next LICENSE;
        }
        my $regex
          = $blocknumber
          ? $licenseproblemdata->{'regex'}
          : $licenseproblemdata->{'firstregex'};
        unless($$cleanedblock =~ $regex) {
            next LICENSE;
        }

        if(defined($licenseproblemdata->{'callsub'})) {
            my $subresult= $licenseproblemdata->{'callsub'}->(
                $info, $source_pkg, $name,
                $basename,$block,$blocknumber,
                $cleanedblock,$matchedkeyword,$licenseproblemhash,
                $licenseproblem,%+
            );
            if($subresult) {
                $licenseproblemhash->{$licenseproblem} = 1;
                $ret = 1;
                next LICENSE;
            }
        }else {
            tag $licenseproblem, $name;
            $licenseproblemhash->{$licenseproblem} = 1;
            $ret = 1;
            next LICENSE;
        }
    }
    return $ret;
}

sub _ships_examples {
    my ($group) = @_;
    my @procs = $group->get_processables('binary');
    return 1 if not @procs;
    foreach my $binpkg (@procs) {
        my $name = $binpkg->pkg_name;
        # If we have an -examples package, assume we ship examples.
        return 1 if $name =~ m{-examples$};
        my @files = $binpkg->info->sorted_index;
        return 1
          if any { m{^usr/share/doc/(.+/)?examples/$} } @files;
    }
    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
