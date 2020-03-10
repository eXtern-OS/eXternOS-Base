# changelog-file -- lintian check script -*- perl -*-

# Copyright (C) 1998 Christian Schwarz
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

package Lintian::changelog_file;
use strict;
use warnings;
use autodie;

use Date::Format qw(time2str);
use Encode qw(decode);
use List::Util qw(first);
use List::MoreUtils qw(any);
use Parse::DebianChangelog;

use Lintian::Check qw(check_spelling spelling_tag_emitter);
use Lintian::Relation::Version qw(versions_gt);
use Lintian::Tags qw(tag);
use Lintian::Util qw(file_is_encoded_in_non_utf8 strip);

use Lintian::Data ();

my $BUGS_NUMBER
  = Lintian::Data->new('changelog-file/bugs-number', qr/\s*=\s*/o);
my $INVALID_DATES
  = Lintian::Data->new('changelog-file/invalid-dates', qr/\s*=\>\s*/o);

my $SPELLING_ERROR_IN_NEWS
  = spelling_tag_emitter('spelling-error-in-news-debian');
my $SPELLING_ERROR_CHANGELOG
  = spelling_tag_emitter('spelling-error-in-changelog');

sub run {
    my ($pkg, undef, $info, undef, $group) = @_;
    my $found_html = 0;
    my $found_text = 0;
    my ($native_pkg, $foreign_pkg, @doc_files);

    # skip packages which have a /usr/share/doc/$pkg -> foo symlink
    return
      if  $info->index("usr/share/doc/$pkg")
      and $info->index("usr/share/doc/$pkg")->is_symlink;

    if (my $docdir = $info->index("usr/share/doc/$pkg/")) {
        for my $path ($docdir->children) {
            my $basename = $path->basename;

            next unless $path->is_file or $path->is_symlink;

            push(@doc_files, $basename);

            # Check a few things about the NEWS.Debian file.
            if ($basename =~ m{\A NEWS\.Debian (?:\.gz)? \Z}ixsm) {
                if ($basename !~ m{ \.gz \Z }xsm) {
                    tag 'debian-news-file-not-compressed', $path->name;
                } elsif ($basename ne 'NEWS.Debian.gz') {
                    tag 'wrong-name-for-debian-news-file', $path->name;
                }
            }

            # Check if changelog files are compressed with gzip -9.
            # It's a bit of an open question here what we should do
            # with a file named ChangeLog.  If there's also a
            # changelog file, it might be a duplicate, or the packager
            # may have installed NEWS as changelog intentionally.
            next
              unless $basename =~ m{\A changelog (?:\.html|\.Debian)?
                                       (?:\.gz)? \Z}xsm;

            if ($basename !~ m{ \.gz \Z}xsm) {
                tag 'changelog-file-not-compressed', $basename;
            } else {
                my $max_compressed = 0;
                my $file_info = $path->file_info;
                if ($path->is_symlink) {
                    my $normalized = $path->link_normalized;
                    if (defined($normalized)) {
                        $file_info = $path->file_info;
                    }
                }
                if (defined($file_info)) {
                    if (index($file_info, 'max compression') != -1) {
                        $max_compressed = 1;
                    }
                    if (not $max_compressed
                        and index($file_info, 'gzip compressed') != -1) {
                        tag 'changelog-not-compressed-with-max-compression',
                          $basename;
                    }
                }
            }

            if (   $basename eq 'changelog.html'
                or $basename eq 'changelog.html.gz') {
                $found_html = 1;
            } elsif ($basename eq 'changelog' or $basename eq 'changelog.gz') {
                $found_text = 1;
            }
        }
    }

    # Check a NEWS.Debian file if we have one.  Save the parsed version of the
    # file for later checks against the changelog file.
    my $news;
    my $dnews = $info->lab_data_path('NEWS.Debian');
    if (-f $dnews) {
        my $line = file_is_encoded_in_non_utf8($dnews);
        if ($line) {
            tag 'debian-news-file-uses-obsolete-national-encoding',
              "at line $line";
        }
        my $changes = Parse::DebianChangelog->init({
            infile => $dnews,
            quiet => 1,
        });
        if (my @errors = $changes->get_parse_errors) {
            for (@errors) {
                tag 'syntax-error-in-debian-news-file', "line $_->[1]",
                  "\"$_->[2]\"";
            }
        }

        # Some checks on the most recent entry.
        if ($changes->data and defined(($changes->data)[0])) {
            ($news) = $changes->data;
            if ($news->Distribution && $news->Distribution =~ /unreleased/i) {
                tag 'debian-news-entry-has-strange-distribution',
                  $news->Distribution;
            }
            check_spelling($news->Changes, $group->info->spelling_exceptions,
                $SPELLING_ERROR_IN_NEWS);
            if ($news->Changes =~ /^\s*\*\s/) {
                tag 'debian-news-entry-uses-asterisk';
            }
        }
    }

    if ($found_html && !$found_text) {
        tag 'html-changelog-without-text-version';
    }

    # is this a native Debian package?
    # If the version is missing, we assume it to be non-native
    # as it is the most likely case.
    my $version = $info->field('version', '0-1');
    $native_pkg  = $info->native;
    $foreign_pkg = (!$native_pkg && $version !~ m/-0\./);
    # A version of 1.2.3-0.1 could be either, so in that
    # case, both vars are false

    if ($native_pkg) {
        # native Debian package
        if (any { m/^changelog(?:\.gz)?$/} @doc_files) {
            # everything is fine
        } elsif (
            my $chg = first {
                m/^changelog\.debian(?:\.gz)$/i;
            }
            @doc_files
          ) {
            tag 'wrong-name-for-changelog-of-native-package',
              "usr/share/doc/$pkg/$chg";
        } else {
            tag 'changelog-file-missing-in-native-package';
        }
    } else {
        # non-native (foreign :) Debian package

        # 1. check for upstream changelog
        my $found_upstream_text_changelog = 0;
        if (any { m/^changelog(\.html)?(?:\.gz)?$/ } @doc_files) {
            $found_upstream_text_changelog = 1 unless $1;
            # everything is fine
        } else {
            # search for changelogs with wrong file name
            my $found = 0;
            for (@doc_files) {
                if (m/^change/i and not m/debian/i) {
                    tag 'wrong-name-for-upstream-changelog',
                      "usr/share/doc/$pkg/$_";
                    $found = 1;
                    last;
                }
            }
            if (not $found) {
                tag 'no-upstream-changelog'
                  unless $info->is_pkg_class('transitional');
            }
        }

        # 2. check for Debian changelog
        if (any { m/^changelog\.Debian(?:\.gz)?$/ } @doc_files) {
            # everything is fine
        } elsif (
            my $chg = first {
                m/^changelog\.debian(?:\.gz)?$/i;
            }
            @doc_files
          ) {
            tag 'wrong-name-for-debian-changelog-file',
              "usr/share/doc/$pkg/$chg";
        } else {
            if ($foreign_pkg && $found_upstream_text_changelog) {
                tag 'debian-changelog-file-missing-or-wrong-name';
            } elsif ($foreign_pkg) {
                tag 'debian-changelog-file-missing';
            }
            # TODO: if uncertain whether foreign or native, either
            # changelog.gz or changelog.debian.gz should exists
            # though... but no tests catches this (extremely rare)
            # border case... Keep in mind this is only happening if we
            # have a -0.x version number... So not my priority to fix
            # --Jeroen
        }
    }

    my $dchpath = $info->lab_data_path('changelog');
    # Everything below involves opening and reading the changelog file, so bail
    # with a warning at this point if all we have is a symlink.  Ubuntu permits
    # such symlinks, so their profile will suppress this tag.
    if (-l $dchpath) {
        tag 'debian-changelog-file-is-a-symlink';
        return;
    }

    # Bail at this point if the changelog file doesn't exist.  We will have
    # already warned about this.
    unless (-f $dchpath) {
        return;
    }

    # check that changelog is UTF-8 encoded
    my $line = file_is_encoded_in_non_utf8($dchpath);
    if ($line) {
        tag 'debian-changelog-file-uses-obsolete-national-encoding',
          "at line $line";
    }

    my $changelog = $info->changelog;
    if (my @errors = $changelog->get_parse_errors) {
        foreach (@errors) {
            tag 'syntax-error-in-debian-changelog', "line $_->[1]",
              "\"$_->[2]\"";
        }
    }

    # Check for some things in the raw changelog file and compute the
    # "offset" to the first line of the first entry.  We use this to
    # report the line number of "too-long" lines.  (#657402)
    my $chloff = check_dch($dchpath);

    my @entries = $changelog->data;
    if (@entries) {
        my %versions;
        my $first_timestamp = $entries[0]->Timestamp;
        for my $entry (@entries) {
            if ($entry->Maintainer) {
                if ($entry->Maintainer =~ /<([^>\@]+\@[^>.]*)>/) {
                    tag 'debian-changelog-file-contains-invalid-email-address',
                      $1;
                }
            }
            $versions{$entry->Version} = 1 if defined $entry->Version;
        }

        if ($first_timestamp) {
            my $warned = 0;
            my $dch_date = $entries[0]->Date;
            foreach my $re ($INVALID_DATES->all()) {
                if ($dch_date =~ m/($re)/i) {
                    my $repl = $INVALID_DATES->value($re);
                    tag 'invalid-date-in-debian-changelog', "($1 -> $repl)";
                    $warned = 1;
                }
            }
            my ($weekday_declared, $date) = split(m/,\s*/, $dch_date, 2);
            $date //= '';
            my ($tz, $weekday_actual);

            if ($date =~ m/[ ]+ ([^ ]+)\Z/xsm) {
                $tz = $1;
                $weekday_actual = time2str('%a', $first_timestamp, $tz);
            }
            if (not $warned and $tz and $weekday_declared ne $weekday_actual) {
                my $real_weekday = time2str('%A', $first_timestamp, $tz);
                my $short_date = time2str('%Y-%m-%d', $first_timestamp, $tz);
                tag 'debian-changelog-has-wrong-day-of-week',
                  "$short_date is a $real_weekday";
            }
        }

        if (@entries > 1) {
            my $second_timestamp = $entries[1]->Timestamp;

            if ($first_timestamp && $second_timestamp) {
                tag 'latest-changelog-entry-without-new-date'
                  unless (($first_timestamp - $second_timestamp) > 0
                    or lc($entries[0]->Distribution) eq 'unreleased');
            }

            my $first_version = $entries[0]->Version;
            my $second_version = $entries[1]->Version;
            if ($first_version and $second_version) {
                tag 'latest-debian-changelog-entry-without-new-version'
                  unless versions_gt(
                    $first_version =~ s/^([^:]+)://r,
                    $second_version =~ s/^([^:]+)://r
                  )
                  or $entries[0]->Changes =~ /backport/i
                  or $entries[0]->Source ne $entries[1]->Source;
                tag 'latest-debian-changelog-entry-changed-to-native'
                  if $native_pkg and $second_version =~ m/-/;
            }

            my $first_upstream = $first_version;
            $first_upstream =~ s/-[^-]+$//;
            my $second_upstream = $second_version;
            $second_upstream =~ s/-[^-]+$//;
            my $first_debian =substr $first_version, length($first_upstream);
            $first_debian =~ s/-([^-]+)$/$1/ if length($first_debian) > 0;
            my $second_debian =substr $second_version,length($second_upstream);
            $second_debian =~ s/-([^-]+)$/$1/ if length($second_debian) > 0;

            if ($first_upstream eq $second_upstream) {
                if ($entries[0]->Changes
                    =~ /^\s*\*\s+new\s+upstream\s+(?:\S+\s+)?release\b/im) {
                    tag 'possible-new-upstream-release-without-new-version';
                }
                if ($first_debian =~ /^\d+$/ and $second_debian =~ /^\d+$/) {
                    unless ($first_debian == $second_debian + 1) {
                        tag 'non-consecutive-debian-revision';
                    }
                }
            }

            my $first_dist = lc $entries[0]->Distribution;
            my $second_dist = lc $entries[1]->Distribution;
            if ($first_dist eq 'unstable' and $second_dist eq 'experimental') {
                unless ($entries[0]->Changes
                    =~ /\bto\s+['"‘“]?(?:unstable|sid)['"’”]?\b/im) {
                    tag 'experimental-to-unstable-without-comment';
                }
            }

            my ($first_epoch) = ($first_version =~ /^([^:]+):/, '(none)');
            my ($second_epoch) = ($second_version =~ /^([^:]+):/, '(none)');
            if ($first_epoch and $second_epoch ne $first_epoch) {
                tag 'epoch-change-without-comment',
                  "$second_epoch -> $first_epoch"
                  unless $entries[0]->Changes =~ /\bepoch\b/im;
            }
        }

        # Some checks should only be done against the most recent
        # changelog entry.
        my $entry = $entries[0];
        my $changes = $entry->Changes || '';

        if (@entries == 1) {
            if ($entry->Version and $entry->Version =~ /-1$/) {
                tag 'new-package-should-close-itp-bug'
                  unless @{ $entry->Closes };
            }
            if ($changes=~ /(?:#?\s*)(?:\d|n)+ is the bug number of your ITP/i)
            {
                tag 'changelog-is-dh_make-template';
            }
        }
        while ($changes =~ /(closes\s*(?:bug)?\#?\s?\d{6,})[^\w]/ig) {
            tag 'possible-missing-colon-in-closes', $1 if $1;
        }
        if ($changes =~ m/(TEMP-\d{7}-[0-9a-fA-F]{6})/) {
            tag 'changelog-references-temp-security-identifier', $1;
        }

        # check for bad intended distribution
        if (
            $changes =~ /uploads? \s+ to \s+
                            (?'intended'testing|unstable|experimental|sid)/xi
          ){
            my $intended = lc($+{intended});
            if($intended eq 'sid') {
                $intended = 'unstable';
            }
            my $uploaded = $entry->Distribution;
            unless ($uploaded eq 'UNRELEASED') {
                unless($uploaded eq $intended) {
                    tag 'bad-intended-distribution',
                      "intended to $intended but uploaded to $uploaded";
                }
            }
        }

        if($changes =~ /Close:\s+(\#\d+)/xi) {
            tag 'misspelled-closes-bug',$1;
        }

        my $changesempty = $changes;
        $changesempty =~ s,\W,,gms;
        if (length($changesempty)==0) {
            tag 'changelog-empty-entry';
        }

        my $closes = $entry->Closes;
        # before bug 50004 bts removed bug instead of archiving
        for my $bug (@$closes) {
            if (   $bug < $BUGS_NUMBER->value('min-bug')
                || $bug > $BUGS_NUMBER->value('max-bug')) {
                tag 'improbable-bug-number-in-closes', $bug;
            }
        }

        # unstable, testing, and stable shouldn't be used in Debian
        # version numbers.  unstable should get a normal version
        # increment and testing and stable should get suite-specific
        # versions.
        #
        # NMUs get a free pass because they need to work with the
        # version number that was already there.
        my $changelog_version;
        if ($info->native) {
            $changelog_version = $entry->Version || '';
        } else {
            if ($entry->Version) {
                ($changelog_version) = (split('-', $entry->Version))[-1];
            } else {
                $changelog_version = '';
            }
        }
        unless (not $info->native and $changelog_version =~ /\./) {
            if (    $info->native
                and $changelog_version =~ /testing|(?:un)?stable/i) {
                tag 'version-refers-to-distribution', $entry->Version;
            } elsif ($changelog_version =~ /woody|sarge|etch|lenny|squeeze/) {
                my %unreleased_dists
                  = map { $_ => 1 } qw(unstable experimental);
                if (exists($unreleased_dists{$entry->Distribution})) {
                    tag 'version-refers-to-distribution', $entry->Version;
                }
            }
        }

        # Compare against NEWS.Debian if available.
        if ($news and $news->Version) {
            if ($entry->Version eq $news->Version) {
                for my $field (qw/Distribution Urgency/) {
                    if ($entry->$field ne $news->$field) {
                        tag 'changelog-news-debian-mismatch', lc($field),
                          $entry->$field . ' != ' . $news->$field;
                    }
                }
            }
            unless ($versions{$news->Version}) {
                tag 'debian-news-entry-has-unknown-version', $news->Version;
            }
        }

        # We have to decode into UTF-8 to get the right length for the
        # length check.  For some reason, use open ':utf8' isn't
        # sufficient.  If the changelog uses a non-UTF-8 encoding,
        # this will mangle it, but it doesn't matter for the length
        # check.
        #
        # Parse::DebianChangelog adds an additional space to the
        # beginning of each line, so we have to adjust for that in the
        # length check.
        my @lines = split("\n", decode('utf-8', $changes));
        for my $i (0 .. $#lines) {
            my $line = $i + $chloff;
            tag 'debian-changelog-line-too-short', $1, "(line $line)"
              if $lines[$i] =~ /^   [*]\s(.{1,5})$/ and $1 !~ /:$/;
            if (length($lines[$i]) > 81
                and $lines[$i] !~ /^[\s.o*+-]*(?:[Ss]ee:?\s+)?\S+$/) {
                tag 'debian-changelog-line-too-long', "line $line";
            }
        }

        # Strip out all lines that contain the word spelling to avoid false
        # positives on changelog entries for spelling fixes.
        $changes =~ s/^.*(?:spelling|typo).*\n//gm;
        check_spelling($changes, $group->info->spelling_exceptions,
            $SPELLING_ERROR_CHANGELOG);
    }

    return;
}

# read the changelog itself and check for some issues we cannot find
# with Parse::DebianChangelog.  Also return the "real" line number for
# the first line of text in the first entry.
#
sub check_dch {
    my ($path) = @_;

    # emacs only looks at the last "local variables" in a file, and only at
    # one within 3000 chars of EOF and on the last page (^L), but that's a bit
    # pesky to replicate.  Demanding a match of $prefix and $suffix ought to
    # be enough to avoid false positives.

    my ($prefix, $suffix);
    my $lineno = 0;
    my ($estart, $tstart) = (0, 0);
    open(my $fd, '<', $path);
    while (<$fd>) {

        unless ($tstart) {
            $lineno++;
            $estart = 1 if m/^\S/;
            $tstart = 1 if m/^\s+\S/;
        }

        if (
               m/closes:\s*(((?:bug)?\#?\s?\d*)[[:alpha:]]\w*)/io
            || m/closes:\s*(?:bug)?\#?\s?\d+
              (?:,\s*(?:bug)?\#?\s?\d+)*
              (?:,\s*(((?:bug)?\#?\s?\d*)[[:alpha:]]\w*))/iox
          ) {
            tag 'wrong-bug-number-in-closes', "l$.:$1" if $2;
        }

        if (/^(.*)Local\ variables:(.*)$/i) {
            $prefix = $1;
            $suffix = $2;
        }
        # emacs allows whitespace between prefix and variable, hence \s*
        if (   defined $prefix
            && defined $suffix
            && m/^\Q$prefix\E\s*add-log-mailing-address:.*\Q$suffix\E$/) {
            tag 'debian-changelog-file-contains-obsolete-user-emacs-settings';
        }
    }
    close($fd);
    return $lineno;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
