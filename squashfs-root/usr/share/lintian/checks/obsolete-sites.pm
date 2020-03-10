# obsolete-sites -- lintian check script -*- perl -*-

# Copyright (C) 2015 Axel Beckert <abe@debian.org>
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

package Lintian::obsolete_sites;
use strict;
use warnings;
use autodie;

use Lintian::Tags qw(tag);
use Lintian::Data ();

our $OBSOLETE_SITES = Lintian::Data->new('obsolete-sites/obsolete-sites');
my @interesting_files = qw(
  control
  copyright
  watch
  upstream
  upstream-metadata.yaml
);

sub run {
    my ($pkg, $type, $info, $proc) = @_;

    my $debian_dir = $info->index_resolved_path('debian/');
    return unless $debian_dir;
    foreach my $file (@interesting_files) {
        my $dfile = $debian_dir->child($file);
        search_for_obsolete_sites($dfile, "debian/$file");
    }

    my $upstream_dir = $info->index_resolved_path('debian/upstream');
    return unless $upstream_dir;

    my $dfile = $upstream_dir->child('metadata');
    search_for_obsolete_sites($dfile, 'debian/upstream/metadata');

    return;
}

sub search_for_obsolete_sites {
    my ($dfile, $file) = @_;

    if (defined($dfile) and $dfile->is_regular_file and $dfile->is_open_ok) {

        my $dcontents = $dfile->file_contents;

        # Strip comments
        $dcontents =~ s/^\s*#.*$//gm;

        foreach my $site ($OBSOLETE_SITES->all) {
            if ($dcontents
                =~ m((\w+://(?:[\w.]*\.)?\Q$site\E[/:][^\s\"<>\$]*))i) {
                tag 'obsolete-url-in-packaging', $file, $1;
            }
        }

        tag 'obsolete-url-in-packaging', $file, $1
          if $dcontents =~m{(ftp://(?:ftp|security)\.debian\.org)}i;
    }

    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
