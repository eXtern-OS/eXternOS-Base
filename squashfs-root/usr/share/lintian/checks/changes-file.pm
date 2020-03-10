# changes-file -- lintian check script -*- perl -*-

# Copyright (C) 1998 Christian Schwarz and Richard Braakman
#
# This program is free software.  It is distributed under the terms of
# the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any
# later version.
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

package Lintian::changes_file;
use strict;
use warnings;
use autodie;

use List::MoreUtils qw(none);

use Lintian::Tags qw(tag);
use Lintian::Check qw(check_maintainer);
use Lintian::Data;
use Lintian::Util qw(get_file_checksum);

my $KNOWN_DISTS = Lintian::Data->new('changes-file/known-dists');
my $SIGNING_KEY_FILENAMES = Lintian::Data->new('common/signing-key-filenames');

sub run {
    my (undef, undef, $info, undef, $group) = @_;

    # If we don't have a Format key, something went seriously wrong.
    # Tag the file and skip remaining processing.
    if (!$info->field('format')) {
        tag 'malformed-changes-file';
        return;
    }

    # Description is mandated by dak, but only makes sense if binary
    # packages are included.  Don't tag pure source uploads.
    if (  !$info->field('description')
        && $info->field('architecture', '') ne 'source') {
        tag 'no-description-in-changes-file';
    }

    # check distribution field
    if (defined $info->field('distribution')) {
        my @distributions = split /\s+/o, $info->field('distribution');
        for my $distribution (@distributions) {
            if ($distribution eq 'UNRELEASED') {
                # ignore
            } else {
                my $dist = $distribution;
                if ($dist !~ m/^(?:sid|unstable|experimental)/) {
                    # Strip common "extensions" for distributions
                    # (except sid and experimental, where they would
                    # make no sense)
                    $dist =~ s/- (?:backports(?:-sloppy)?
                                   |lts
                                   |proposed(?:-updates)?
                                   |updates
                                   |security
                                   |volatile)$//xsmo;

                    if ($distribution =~ /backports/) {
                        my $bpo1 = 1;
                        if ($info->field('version') =~ m/~bpo(\d+)\+(\d+)$/) {
                            my $distnumber = $1;
                            my $bpoversion = $2;
                            if (
                                ($dist eq 'squeeze' && $distnumber ne '60')
                                ||(    $distribution eq 'wheezy-backports'
                                    && $distnumber ne '70')
                                ||($distribution eq 'wheezy-backports-sloppy'
                                    && $distnumber ne '7')
                                ||($dist eq 'jessie' && $distnumber ne '8')
                              ) {
                                tag
'backports-upload-has-incorrect-version-number',
                                  $info->field('version'),
                                  $distribution;
                            }
                            $bpo1 = 0 if ($bpoversion > 1);
                        } else {
                            tag
                              'backports-upload-has-incorrect-version-number',
                              $info->field('version');
                        }
                        # for a ~bpoXX+2 or greater version, there
                        # probably will be only a single changelog entry
                        if ($bpo1) {
                            my $changes_versions = 0;
                            foreach my $change_line (
                                split("\n", $info->field('changes'))) {
                      # from Parse/DebianChangelog.pm
                      # the changelog entries in the changes file are in a
                      # different format than in the changelog, so the standard
                      # parsers don't work. We just need to know if there is
                      # info for more than 1 entry, so we just copy part of the
                      # parse code here
                                if ($change_line
                                    =~ m/^\s*(?:\w[-+0-9a-z.]*) \((?:[^\(\) \t]+)\)(?:(?:\s+[-+0-9a-z.]+)+)\;\s*(?:.*)$/i
                                  ) {
                                    $changes_versions++;
                                }
                            }
                            # only complain if there is a single entry,
                            # if we didn't find any changelog entry, there is
                            # probably something wrong with the parsing, so we
                            # don't emit a tag
                            if ($changes_versions == 1) {
                                tag 'backports-changes-missing';
                            }
                        }
                    }
                }
                if (!$KNOWN_DISTS->known($dist)) {
                    # bad distribution entry
                    tag 'bad-distribution-in-changes-file', $distribution;
                }

                my $changes = $info->field('changes');
                if (defined $changes) {
                    # take the first non-empty line
                    $changes =~ s/^\s+//s;
                    $changes =~ s/\n.*//s;

                    if ($changes
                        =~ m/^\s*(?:\w[-+0-9a-z.]*)\s*\([^\(\) \t]+\)\s*([-+0-9A-Za-z.]+)\s*;/
                      ) {
                        my $changesdist = $1;
                        if ($changesdist eq 'UNRELEASED') {
                            tag 'unreleased-changes';
                        } elsif ($changesdist ne $distribution
                            && $changesdist ne $dist) {
                            if (   $changesdist eq 'experimental'
                                && $dist ne 'experimental') {
                                tag 'distribution-and-experimental-mismatch',
                                  $distribution;
                            } elsif ($KNOWN_DISTS->known($dist)) {
                                tag 'distribution-and-changes-mismatch',
                                  $distribution, $changesdist;
                            }
                        }
                    }
                }
            }
        }

        if ($#distributions > 0) {
            tag 'multiple-distributions-in-changes-file',
              $info->field('distribution');
        }

    }

    # Urgency is only recommended by Policy.
    if (!$info->field('urgency')) {
        tag 'no-urgency-in-changes-file';
    } else {
        my $urgency = lc $info->field('urgency');
        $urgency =~ s/ .*//o;
        unless ($urgency =~ /^(?:low|medium|high|critical|emergency)$/o) {
            tag 'bad-urgency-in-changes-file', $info->field('urgency');
        }
    }

    # Changed-By is optional in Policy, but if set, must be
    # syntactically correct.  It's also used by dak.
    if ($info->field('changed-by')) {
        check_maintainer($info->field('changed-by'), 'changed-by');
    }

    my $has_signing_key = 0;
    my $src = $group->get_source_processable;
    if ($src) {
        for my $key_name ($SIGNING_KEY_FILENAMES->all) {
            my $path = $src->info->index_resolved_path("debian/$key_name");
            if ($path and $path->is_file) {
                $has_signing_key = 1;
                last;
            }
        }
    }

    my $files = $info->files;
    my $path = readlink($info->lab_data_path('changes'));
    my %num_checksums;
    $path =~ s#/[^/]+$##;
    foreach my $file (keys %$files) {
        my $file_info = $files->{$file};

        # Ensure all orig tarballs have a signature if we have an upstream
        # signature.
        if (   $has_signing_key
            && $file =~ m/(^.*\.orig(?:-[A-Za-z\d-]+)?\.tar)\./
            && $file !~ m/\.asc$/
            && !$info->repacked) {
            tag 'orig-tarball-missing-upstream-signature', $file
              if none { exists $files->{"$_.asc"} } ($file, $1);
        }

        # check section
        if (   ($file_info->{section} eq 'non-free')
            or ($file_info->{section} eq 'contrib')) {
            tag 'bad-section-in-changes-file', $file, $file_info->{section};
        }

        foreach my $alg (qw(sha1 sha256)) {
            my $checksum_info = $file_info->{checksums}{$alg};
            if (defined $checksum_info) {
                if ($file_info->{size} != $checksum_info->{filesize}) {
                    tag 'file-size-mismatch-in-changes-file', $file,
                      $file_info->{size} . ' != ' .$checksum_info->{filesize};
                }
            }
        }

        # check size
        my $filename = "$path/$file";
        my $size = -s $filename;

        if ($size ne $file_info->{size}) {
            tag 'file-size-mismatch-in-changes-file', $file,
              $file_info->{size} . " != $size";
        }

        # check checksums
        foreach my $alg (qw(md5 sha1 sha256)) {
            next unless exists $file_info->{checksums}{$alg};

            my $real_checksum = get_file_checksum($alg, $filename);
            $num_checksums{$alg}++;

            if ($real_checksum ne $file_info->{checksums}{$alg}{sum}) {
                tag 'checksum-mismatch-in-changes-file', $alg, $file;
            }
        }
    }

    # Check that we have a consistent number of checksums and files
    foreach my $alg (keys %num_checksums) {
        my $seen = $num_checksums{$alg};
        my $expected = keys %{$files};
        tag 'checksum-count-mismatch-in-changes-file',
          "$seen $alg checksums != $expected files"
          if $seen != $expected;
    }

    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
