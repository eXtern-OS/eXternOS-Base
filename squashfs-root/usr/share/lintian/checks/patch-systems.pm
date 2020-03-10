# patch-systems -- lintian check script -*- perl -*-
#
# Copyright (C) 2007 Marc Brockschmidt
# Copyright (C) 2008 Raphael Hertzog
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

package Lintian::patch_systems;
use strict;
use warnings;
use autodie;

use constant PATCH_DESC_TEMPLATE => 'TODO: Put a short summary on'
  . ' the line above and replace this paragraph';

use List::MoreUtils qw(none);

use Lintian::Check qw(check_spelling spelling_tag_emitter);
use Lintian::Tags qw(tag);
use Lintian::Util qw(internal_error strip);

sub run {
    my (undef, undef, $info, undef, $group) = @_;

    # Some (cruft) checks are valid for every patch system, so we need
    # to record that:
    my $uses_patch_system = 0;

    # Get build deps so we can decide which build system the
    # maintainer meant to use:
    my $build_deps = $info->relation('build-depends-all');
    # Get source package format
    my $format = $info->field('format', '');
    my $quilt_format = ($format =~ /3\.\d+ \(quilt\)/) ? 1 : 0;

    my $droot = $info->index_resolved_path('debian/');
    return if not $droot;
    my $dpdir = $droot->resolve_path('patches');
    my $patch_series;
    my %known_files;

    # Find debian/patches/series, assuming debian/patches is a (symlink to a)
    # dir.  There are cases, where it is a file (ctwm: #778556)
    if ($dpdir and ($dpdir->is_dir or $dpdir->is_symlink)) {
        my $resolved = $dpdir->resolve_path;
        $patch_series = $resolved->resolve_path('series') if $resolved->is_dir;
    }

    #----- dpatch
    if ($build_deps->implies('dpatch')) {
        my $list_file;
        tag 'package-uses-deprecated-dpatch-patch-system';
        $uses_patch_system++;
        $list_file = $dpdir->resolve_path('00list') if $dpdir;
        #check for a debian/patches file:
        if (not $list_file or not $list_file->is_file) {
            tag 'dpatch-build-dep-but-no-patch-list';
        } else {
            my $list_uses_cpp = 0;
            my $opt_file = $dpdir->resolve_path('00options');
            my @list_files
              = grep {$_->basename =~ m/^00list.*/ and $_->is_open_ok;}
              $dpdir->children;
            if ($opt_file and $opt_file->is_open_ok) {
                my $fd = $opt_file->open;
                $known_files{$opt_file->basename}++;
                while(<$fd>) {
                    if (/DPATCH_OPTION_CPP=1/) {
                        $list_uses_cpp = 1;
                        last;
                    }
                }
                close($fd);
            }
            for my $list_file (@list_files) {
                my @patches;
                $known_files{$list_file->basename}++;
                my $fd = $list_file->open;
                while(<$fd>) {
                    chomp;
                    next if (/^\#/); #ignore comments or CPP directive
                    s%//.*%% if $list_uses_cpp; # remove C++ style comments
                    if ($list_uses_cpp && m%/\*%) {
                        # remove C style comments
                        $_ .= <$fd> while($_ !~ m%\*/%);
                        s%/\*[^*]*\*/%%g;
                    }
                    next if (/^\s*$/); #ignore blank lines
                    push @patches, split(' ', $_);
                }
                close($fd);

                # Check each patch.
                foreach my $patch_name (@patches) {
                    $known_files{$patch_name}++;
                    my $patch_file = $dpdir->child($patch_name);
                    $patch_file = $dpdir->child("${patch_name}.dpatch")
                      if not $patch_file;
                    if (not $patch_file) {
                        tag 'dpatch-index-references-non-existent-patch',
                          $patch_name;
                        next;
                    }
                    next unless $patch_file->is_open_ok;

                    my $description = '';
                    my $fd = $patch_file->open;
                    while (<$fd>) {
                        # stop if something looking like a patch
                        # starts:
                        last if /^---/;
                        # note comment if we find a proper one
                        $description .= $1
                          if (/^\#+\s*DP:\s*(\S.*)$/
                            && $1 !~ /^no description\.?$/i);
                        $description .= $1
                          if /^\# (?:Description|Subject): (.*)/;
                    }
                    close($fd);
                    unless ($description) {
                        tag 'dpatch-missing-description', $patch_name;
                    }
                    check_patch($group, $patch_file, $description);
                }
            }
        }
    }

    #----- quilt
    if ($build_deps->implies('quilt') or $quilt_format) {
        $uses_patch_system++;
        # check for a debian/patches file:
        if (not $patch_series or not $patch_series->is_open_ok) {
            tag 'quilt-build-dep-but-no-series-file' unless $quilt_format;
        } else {
            my (@patches, @badopts);
            my $series_fd = $patch_series->open;
            while (my $patch = <$series_fd>) {
                $patch =~ s/(?:^|\s+)#.*$//; # Strip comment
                if (rindex($patch,"\n") < 0) {
                    tag 'quilt-series-without-trailing-newline';
                }
                strip($patch); # Strip leading/trailing spaces
                next if $patch eq '';
                if ($patch =~ m{^(\S+)\s+(\S.*)$}) {
                    my $patch_options;
                    ($patch, $patch_options) = ($1, $2);
                    if ($patch_options ne '-p1') {
                        push(@badopts, $patch);
                    }
                }
                push(@patches, $patch);
            }
            close($series_fd);
            if (scalar(@badopts)) {
                tag 'quilt-patch-with-non-standard-options', @badopts;
            }

            # Check each patch.
            foreach my $patch_filename (@patches) {
                my $patch = $dpdir->resolve_path($patch_filename);
                if (not $patch or not $patch->is_file) {
                    tag 'quilt-series-references-non-existent-patch',
                      $patch_filename;
                    next;
                }
                next if not $patch->is_open_ok;
                my $description = '';
                my $has_template_description = 0;
                my $patch_fd = $patch->open;
                while (<$patch_fd>) {
                    # stop if something looking like a patch starts:
                    last if /^---/;
                    next if /^\s*$/;
                    # Skip common "lead-in" lines
                    $description .= $_
                      unless m{^(?:Index: |=+$|diff .+|index )};
                    $has_template_description = 1
                      if index($_, PATCH_DESC_TEMPLATE) != -1;
                }
                close($patch_fd);
                unless ($description) {
                    tag 'quilt-patch-missing-description', $patch_filename;
                }
                if ($has_template_description) {
                    tag 'quilt-patch-using-template-description',
                      $patch_filename;
                }
                check_patch($group, $patch, $description);
            }
        }
        if ($quilt_format) { # 3.0 (quilt) specific checks
            # Format 3.0 packages may generate a debian-changes-$version patch
            my $version = $info->field('version');
            my $patch_header = $droot->resolve_path('source/patch-header');
            my $versioned_patch;
            $versioned_patch = $dpdir->resolve_path("debian-changes-$version")
              if $dpdir;
            if ($versioned_patch and $versioned_patch->is_file) {
                if (not $patch_header or not $patch_header->is_file) {
                    tag 'format-3.0-but-debian-changes-patch';
                }
            }
        }
    } elsif ($patch_series and $patch_series->is_file) {
        # 3.0 (quilt) sources don't need quilt as dpkg-source will
        # do the work
        tag 'quilt-series-but-no-build-dep' unless $quilt_format;
    }

    #----- look for README.source
    if ($uses_patch_system && !$quilt_format) {
        my $readme = $droot->resolve_path('README.source');
        tag 'patch-system-but-no-source-readme'
          if not $readme;
    }

    #----- look for unreferenced files in debian/patches
    if ($dpdir and $dpdir->is_dir and $format ne '2.0') {
        # Check all series files, including $vendor.series
        foreach my $file ($dpdir->children) {
            next unless $file =~ /\/(.+\.)?series$/;
            next unless $file->is_open_ok;
            $known_files{$file->basename}++;
            my $fd = $file->open;
            while (<$fd>) {
                $known_files{$1}++ if m{^\s*(?:#+\s*)?(\S+)};
            }
            close($fd);
        }

        foreach my $file ($dpdir->children('breadth-first')) {
            next if $file->basename =~ /^README(\.patches)?$/;
            # Use path relative to debian/patches for "subdir/foo"
            my $name = substr($file, length $dpdir);
            tag 'patch-file-present-but-not-mentioned-in-series', $name
              unless $known_files{$name} or $file->is_dir;
        }
    }

    #----- general cruft checking:
    if ($uses_patch_system > 1) {
        tag 'more-than-one-patch-system';
    }
    my @direct;
    open(my $fd, '<', $info->diffstat);
    while (<$fd>) {
        my ($file) = (m,^\s+(.*?)\s+\|,)
          or internal_error("syntax error in diffstat file: $_");
        push(@direct, $file) if ($file !~ m,^debian/,);
    }
    close($fd);
    if (@direct) {
        my $files= (@direct > 1) ? "$direct[0] and $#direct more" : $direct[0];

        if ($uses_patch_system) {
            for my $patched_file (@direct) {
                tag 'patch-system-but-direct-changes-in-diff', $patched_file;
            }
        }
        tag 'direct-changes-in-diff-but-no-patch-system', $files
          if (not $uses_patch_system);
    }
    return;
}

# Checks on patches common to all build systems.
sub check_patch {
    my ($group, $patch_file, $description) = @_;
    if (none { /(spelling|typo)/i } ($patch_file, $description)) {
        my $tag_emitter
          = spelling_tag_emitter('spelling-error-in-patch-description',
            $patch_file);
        # Check the first line separately to avoid duplicates
        foreach my $x (split(/\n/, $description, 2)) {
            check_spelling($x, $group->info->spelling_exceptions,$tag_emitter);
        }
    }
    # Use --strip=1 to strip off the first layer of directory in case
    # the parent directory in which the patches were generated was
    # named "debian".  This will produce false negatives for --strip=0
    # patches that modify files in the debian/* directory, but as of
    # 2010-01-01, all cases where the first level of the patch path is
    # "debian/" in the archive are false positives.
    open(my $fd, '-|', 'lsdiff', '--strip=1', $patch_file->fs_path);
    while (<$fd>) {
        chomp;
        if (m|^(?:\./)?debian/|o) {
            tag 'patch-modifying-debian-files', $patch_file->basename, $_;
        }
    }
    close($fd);
    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
