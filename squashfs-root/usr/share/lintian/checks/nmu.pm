# nmu -- lintian check script -*- perl -*-

# Copyright (C) 2004 Jeroen van Wolffelaar
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

package Lintian::nmu;
use strict;
use warnings;
use autodie;

use List::MoreUtils qw(any);
use List::Util qw(first);

use Lintian::Tags qw(tag);
use Lintian::Util qw(strip);

sub run {
    my (undef, undef, $info) = @_;
    my $changelog_mentions_nmu = 0;
    my $changelog_mentions_local = 0;
    my $changelog_mentions_qa = 0;
    my $changelog_mentions_team_upload = 0;
    my $debian_dir = $info->index_resolved_path('debian/');
    my $chf;
    $chf = $debian_dir->child('changelog') if $debian_dir;

    # This isn't really an NMU check, but right now no other check
    # looks at debian/changelog in source packages.  Catch a
    # debian/changelog file that's a symlink.
    if ($chf and $chf->is_symlink) {
        tag 'changelog-is-symlink';
    }
    return if not $info->changelog;

    # Get some data from the changelog file.
    my ($entry) = $info->changelog->data;
    my $uploader = canonicalize($entry->Maintainer);
    my $changes = $entry->Changes;
    $changes =~ s/^(\s*\n)+//;
    my $firstline = first { /^\s*\*/ } split('\n', $changes);

    # Check the first line for QA, NMU or team upload mentions.
    if ($firstline) {
        local $_ = $firstline;
        if (/\bnmu\b/i or /non-maintainer upload/i or m/LowThresholdNMU/io) {
            unless (
                m/
                        (?:ackno|\back\b|confir|incorporat).*
                        (?:\bnmu\b|non-maintainer)/xi
              ) {
                $changelog_mentions_nmu = 1;
            }
        }
        $changelog_mentions_local = 1 if /\blocal\s+package\b/i;
        $changelog_mentions_qa = 1 if /orphan/i or /qa (?:group )?upload/i;
        $changelog_mentions_team_upload = 1 if /team upload/i;
    }

    # If the version field is missing, assume it to be a native,
    # maintainer upload as it is probably the most likely case.
    my $version = $info->field('version', '0-1');
    my $maintainer = canonicalize($info->field('maintainer', ''));
    my $uploaders = $info->field('uploaders');

    my $version_nmuness = 0;
    my $version_local = 0;

    if ($uploader =~ m/^\s|\s$/) {
        tag 'extra-whitespace-around-name-in-changelog-trailer';
        strip($uploader);
    }

    if ($version =~ /-[^.-]+(\.[^.-]+)?(\.[^.-]+)?$/) {
        $version_nmuness = 1 if defined $1;
        $version_nmuness = 2 if defined $2;
    }
    if ($version =~ /\+nmu\d+$/) {
        $version_nmuness = 1;
    }
    if ($version =~ /\+b\d+$/) {
        $version_nmuness = 2;
    }
    if ($version =~ /local/i) {
        $version_local = 1;
    }

    my $upload_is_nmu = $uploader ne $maintainer;
    if (defined $uploaders) {
        my @uploaders = map { canonicalize($_) } split />\K\s*,\s*/,$uploaders;
        $upload_is_nmu = 0 if any { $_ eq $uploader } @uploaders;
    }

    if ($maintainer =~ /packages\@qa.debian.org/) {
        tag 'orphaned-package-should-not-have-uploaders'
          if defined $uploaders;
        tag 'qa-upload-has-incorrect-version-number', $version
          if $version_nmuness == 1;
        tag 'changelog-should-mention-qa'
          if !$changelog_mentions_qa;
    } elsif ($changelog_mentions_team_upload) {
        tag 'team-upload-has-incorrect-version-number', $version
          if $version_nmuness == 1;
        tag 'unnecessary-team-upload' unless $upload_is_nmu;
    } else {
        # Local packages may be either NMUs or not.
        unless ($changelog_mentions_local || $version_local) {
            tag 'changelog-should-mention-nmu'
              if !$changelog_mentions_nmu && $upload_is_nmu;
            tag 'source-nmu-has-incorrect-version-number', $version
              if $upload_is_nmu && $version_nmuness != 1;
        }
        tag 'changelog-should-not-mention-nmu'
          if $changelog_mentions_nmu && !$upload_is_nmu;
        tag 'maintainer-upload-has-incorrect-version-number', $version
          if !$upload_is_nmu && $version_nmuness;
    }

    return;
}

# Canonicalize a maintainer address with respect to case.  E-mail addresses
# are case-insensitive in the right-hand side.
sub canonicalize {
    my ($maintainer) = @_;
    $maintainer =~ s/<([^>\@]+\@)([\w.-]+)>/<$1\L$2>/;
    return $maintainer;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
