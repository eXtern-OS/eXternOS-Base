# watch-file -- lintian check script -*- perl -*-
#
# Copyright (C) 2008 Patrick Schoenfeld
# Copyright (C) 2008 Russ Allbery
# Copyright (C) 2008 Raphael Geissert
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

package Lintian::watch_file;
use strict;
use warnings;
use autodie;

use Lintian::Tags qw(tag);
use Lintian::Util qw($PKGREPACK_REGEX);

our $WATCH_VERSION = Lintian::Data->new('watch-file/version', qr/\s*=\s*/o);
our $SIGNING_KEY_FILENAMES= Lintian::Data->new('common/signing-key-filenames');

sub run {
    my (undef, undef, $info) = @_;
    my $template = 0;
    my $withgpgverification = 0;
    my $wfile = $info->index_resolved_path('debian/watch');
    my ($repack, $prerelease, $watchver, %dversions);

    if (not $wfile or not $wfile->is_open_ok) {
        tag 'debian-watch-file-is-missing' unless ($info->native);
        return;
    }

    # Perform the other checks even if it is a native package
    tag 'debian-watch-file-in-native-package' if ($info->native);

    # Check if the Debian version contains anything that resembles a repackaged
    # source package sign, for fine grained version mangling check
    # If the version field is missing, we assume a neutral non-native one.
    my $version = $info->field('version', '0-1');
    if ($version =~ $PKGREPACK_REGEX) {
        $repack = $1;
    }
    if ($version =~ /(alpha|beta|rc)/i) {
        $prerelease = $1;
    }

    # Gather information from the watch file and look for problems we can
    # diagnose on the first time through.
    my $fd = $wfile->open;
    local $_;
    while (<$fd>) {
        $template = 1 if m/^\s*\#\s*Example watch control file for uscan/io;
        next if /^\s*\#/;
        next if /^\s*$/;
        s/^\s*//;

      CHOMP:
        chomp;
        if (s/(?<!\\)\\$//) {
            # This is caught by uscan.
            last if eof($fd);
            $_ .= <$fd>;
            goto CHOMP;
        }

        if (/^version\s*=\s*(\d+)(?:\s|\Z)/) {
            if (defined $watchver) {
                tag 'debian-watch-file-declares-multiple-versions', "line $.";
            }
            $watchver = $1;
            my $minver = $WATCH_VERSION->value('min-version');
            my $maxver = $WATCH_VERSION->value('max-version');
            if ($watchver < $minver or $watchver > $maxver) {
                tag 'debian-watch-file-unknown-version', $watchver;
            }
        } else {
            unless (defined($watchver)) {
                tag 'debian-watch-file-missing-version';
                $watchver = 1;
            }
            # Version 1 watch files are too broken to try checking them.
            next if ($watchver == 1);

            my (
                $repack_mangle, $repack_dmangle,
                $prerelease_mangle, $prerelease_umangle
            ) = (0, 0, 0, 0);
            my ($opts, @opts);
            if (   s/^opt(?:ion)?s=\"((?:[^\"]|\\\")+)\"\s+//
                || s/^opt(?:ion)?s=(\S+)\s+//) {
                $opts = $1;
                @opts = split($watchver >= 4 ? '\s*,\s*' : ',', $opts);
                for (@opts) {
                    $repack_mangle = 1
                      if defined $repack
                      and /^[ud]?versionmangle\s*=.*$repack/;
                    $repack_dmangle = 1
                      if defined $repack
                      and /^dversionmangle\s*=.*$repack/;
                    $prerelease_mangle = 1
                      if defined $prerelease
                      and /^[ud]?versionmangle\s*=.*$prerelease/;
                    $prerelease_umangle = 1
                      if defined $prerelease
                      and /^uversionmangle\s*=.*$prerelease/;
                    $withgpgverification = 1
                      if /^pgpsigurlmangle\s*=\s*/;
                    $withgpgverification = 1
                      if /^pgpmode\s*=\s*(?!none\s*$)\S.*$/;
                }
            }

            if (m%qa\.debian\.org/watch/sf\.php\?%) {
                tag 'debian-watch-file-uses-deprecated-sf-redirector-method',
                  "line $.";
            } elsif (m%githubredir\.debian\.net%) {
                tag 'debian-watch-file-uses-deprecated-githubredir',"line $.";
            } elsif (
                m{ (?:https?|ftp)://
                   (?:(?:.+\.)?dl|(?:pr)?downloads?|ftp\d?|upload) \.
                   (?:sourceforge|sf)\.net}xsm
                or m{https?://(?:www\.)?(?:sourceforge|sf)\.net
                              /project/showfiles\.php}xsm
                or m{https?://(?:www\.)?(?:sourceforge|sf)\.net
                              /projects/.+/files}xsm
              ) {
                tag 'debian-watch-file-should-use-sf-redirector', "line $.";
            } elsif (m%((?:http|ftp):(?!//sf.net/)\S+)%) {
                tag 'debian-watch-uses-insecure-uri',$1;
            }

            # This bit is as-is from uscan.pl:
            my ($base, $filepattern, $lastversion, $action) = split ' ', $_, 4;
            # Per #765995, $base might be undefined.
            next unless defined($base);
            if ($base =~ s%/([^/]*\([^/]*\)[^/]*)$%/%) {
               # Last component of $base has a pair of parentheses, so no
               # separate filepattern field; we remove the filepattern from the
               # end of $base and rescan the rest of the line
                $filepattern = $1;
                (undef, $lastversion, $action) = split ' ', $_, 3;
            }
            push @{$dversions{$lastversion}}, $. if (defined($lastversion));
            $lastversion = 'debian' unless (defined($lastversion));

            my $needs_repack_mangling = ($repack and $lastversion eq 'debian');
            # If the version of the package contains dfsg, assume that it needs
            # to be mangled to get reasonable matches with upstream.
            if ($needs_repack_mangling and not $repack_mangle) {
                tag 'debian-watch-file-should-mangle-version', "line $.";
            }
            if (    $needs_repack_mangling
                and $repack_mangle
                and not $repack_dmangle) {
                tag
                  'debian-watch-file-should-dversionmangle-not-uversionmangle',
                  "line $.";
            }

            my $needs_prerelease_mangling
              = ($prerelease and $lastversion eq 'debian');
            if (    $needs_prerelease_mangling
                and $prerelease_mangle
                and not $prerelease_umangle) {
                tag
                  'debian-watch-file-should-uversionmangle-not-dversionmangle',
                  "line $.";
            }
        }
    }
    close($fd);

    tag 'debian-watch-contains-dh_make-template' if ($template);
    tag 'debian-watch-does-not-check-gpg-signature'
      unless ($withgpgverification);

    # Look for upstream signing key
    my $key_found = 0;
    for my $key_name ($SIGNING_KEY_FILENAMES->all) {
        my $path = $info->index_resolved_path("debian/$key_name");
        if ($path and $path->is_file) {
            $key_found = $path;
            last;
        }
    }

    if ($withgpgverification) {
        # Check upstream key is present if needed
        tag 'debian-watch-file-pubkey-file-is-missing' unless $key_found;
    } else {
        # Check upstream key is used if present
        tag 'debian-watch-could-verify-download', $key_found if $key_found;
    }

    my $changes = $info->changelog;
    if (defined $changes and %dversions) {
        my $data = $changes->data;
        my %changelog_versions;
        my $count = 1;
        for my $entry (@{$data}) {
            my $uversion = $entry->Version;
            $uversion =~ s/-[^-]+$//; # revision
            $uversion =~ s/^\d+://; # epoch
            $changelog_versions{'orig'}{$entry->Version} = $count;

            # Preserve the first value here to correctly detect old versions.
            $changelog_versions{'mangled'}{$uversion} = $count
              unless (exists($changelog_versions{'mangled'}{$uversion}));
            $count++;
        }

        while (my ($dversion, $lines) = each %dversions) {
            next if (!defined($dversion) || $dversion eq 'debian');
            local $" = ', ';
            if (!$info->native
                && exists($changelog_versions{'orig'}{$dversion})) {
                tag 'debian-watch-file-specifies-wrong-upstream-version',
                  $dversion, "line @{$lines}";
                next;
            }
            if (exists($changelog_versions{'mangled'}{$dversion})
                && $changelog_versions{'mangled'}{$dversion} != 1) {
                tag 'debian-watch-file-specifies-old-upstream-version',
                  $dversion, "line @{$lines}";
                next;
            }
        }
    }

    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
