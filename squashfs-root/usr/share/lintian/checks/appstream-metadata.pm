# appstream-metadata -- lintian check script -*- perl -*-

# Copyright © 2016 Petter Reinholdtsen
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

package Lintian::appstream_metadata;

# For .desktop files, the lintian check would be really easy: Check if
# .desktop file is there, check if matching file exists in
# /usr/share/metainfo, if not throw a warning. Maybe while we're at it
# also check for legacy locations (stuff in /usr/share/appdata) and
# legacy data (metainfo files starting with `<application>`).
#
# For modaliases, maybe udev rules could give some hints.
# Check modalias values to ensure hex numbers are using capital A-F.

use strict;
use warnings;

use XML::Simple qw(:strict);
use File::Basename qw(basename);

use Lintian::Tags qw(tag);

sub run {
    my ($pkg, $type, $info, $proc, $group) = @_;

    my (%desktopfiles, %metainfo, @udevrules);
    my $found_modalias = 0;
    my $modaliases = [];
    if (
        defined(
            my $dir = $info->index_resolved_path('usr/share/applications/'))
      ) {
        for my $file ($dir->children('breadth-first')) {
            $desktopfiles{$file} = 1 if ($file->is_file);
        }
    }
    if (defined(my $dir = $info->index_resolved_path('usr/share/metainfo/'))) {
        for my $file ($dir->children) {
            if ($file->is_file) {
                $metainfo{$file} = 1;
                $found_modalias |= check_modalias($info, $file, $modaliases);
            }
        }
    }
    if (defined(my $dir = $info->index_resolved_path('usr/share/appdata/'))) {
        for my $file ($dir->children('breadth-first')) {
            if ($file->is_file) {
                tag('appstream-metadata-in-legacy-location', $file);
                $found_modalias |= check_modalias($info, $file, $modaliases);
            }
        }
    }
    if (defined(my $dir = $info->index_resolved_path('lib/udev/rules.d/'))) {
        for my $file ($dir->children('breadth-first')) {
            push(@udevrules, $file) if ($file->is_file);
        }
    }

    for my $udevrule (@udevrules) {
        if (check_udev_rules($udevrule, \&provides_user_device, $modaliases)
            && !$found_modalias) {
            tag('appstream-metadata-missing-modalias-provide', $udevrule);
        }
    }
    return;
}

sub check_modalias {
    my ($info, $metadatafile, $modaliases) = @_;
    if (!$metadatafile->is_open_ok) {
        # FIXME report this as an error
        return;
    }
    my $xml = eval {
        XMLin(
            $metadatafile->fs_path,
            ForceArray => ['provides', 'modalias'],
            KeepRoot => 1,
            KeyAttr => [],
        );
    };
    if ($@) {
        tag 'appstream-metadata-invalid', basename($metadatafile->fs_path);
        return 0;
    }

    if (exists $xml->{'application'}) {
        tag('appstream-metadata-legacy-format', $metadatafile);
        return 0;
    }
    if (   exists $xml->{'component'}
        && exists $xml->{'component'}{'provides'}
        && exists $xml->{'component'}{'provides'}[0]{'modalias'}) {
        for (@{$xml->{'component'}{'provides'}[0]{'modalias'}}) {
            push(@{$modaliases}, $_);
            if (m/^usb:v[0-9a-f]{4}p[0-9a-f]{4}d/i
                && !m/^usb:v[0-9A-F]{4}p[0-9A-F]{4}d/) {
                tag(
                    'appstream-metadata-malformed-modalias-provide',
                    $metadatafile,
                    "include non-valid hex digit in USB matching rule '$_'"
                );
            }
        }
        return 1;
    }
    return 0;
}

sub provides_user_device {
    my ($udevrulefile, $linenum, $rule, $data) = @_;
    my $retval = 0;
    if (   m/plugdev/
        || m/uaccess/
        || m/MODE=\"0666\"/) {
        $retval = 1;
    }
    if ($rule =~ m/SUBSYSTEM=="usb"/) {
        my ($vmatch, $pmatch);
        if ($rule =~ m/ATTR\{idVendor\}=="([0-9a-fA-F]{4})"/) {
            $vmatch = 'v' . uc($1);
        }
        if ($rule =~ m/ATTR\{idProduct\}=="([0-9a-fA-F]{4})"/) {
            $pmatch = 'p' . uc($1);
        }
        if (defined $vmatch && defined $pmatch) {
            my $match = "usb:${vmatch}${pmatch}d";
            my $foundmatch;
            for my $aliasmatch (@{$data}) {
                if (0 == index($aliasmatch, $match)) {
                    $foundmatch = 1;
                }
            }
            if (!$foundmatch) {
                tag('appstream-metadata-missing-modalias-provide',
                    $udevrulefile, "match rule $match*");
            }
        }
    }
    return $retval;
}

sub check_udev_rules {
    my ($file, $check, $data) = @_;

    my $fd = $file->open;
    my $linenum = 0;
    my $cont;
    my $retval = 0;
    while (<$fd>) {
        chomp;
        $linenum++;
        if (defined $cont) {
            $_ = $cont . $_;
            $cont = undef;
        }
        if (/^(.*)\\$/) {
            $cont = $1;
            next;
        }
        next if /^#.*/; # Skip comments
        $retval |= $check->($file, $linenum, $_, $data);
    }
    close($fd);
    return $retval;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
