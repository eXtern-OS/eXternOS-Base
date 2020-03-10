# gir -- lintian check script for GObject-Introspection -*- perl -*-
#
# Copyright © 2012 Arno Töll
# Copyright © 2014 Collabora Ltd.
# Copyright © 2016 Simon McVittie
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

package Lintian::gir;

use strict;
use warnings;
use autodie;

use Lintian::Tags qw(tag);

my $MA_DIRS = Lintian::Data->new('common/multiarch-dirs', qr/\s++/);

sub run {
    my ($pkg, $type, $info, $proc, $group) = @_;

    if ($type eq 'source') {
        _run_source($pkg, $type, $info, $proc, $group);
    } else {
        _run_binary($pkg, $type, $info, $proc, $group);
    }

    return;
}

sub _run_source {
    my (undef, undef, $info) = @_;

    foreach my $bin ($info->binaries) {
        if ($bin =~ m/^gir1\.2-/) {
            if (
                not $info->binary_relation($bin, 'strong')
                ->implies('${gir:Depends}')) {
                tag('typelib-missing-gir-depends', $bin);
            }
        }
    }

    return;
}

sub _run_binary {
    my ($pkg, undef, $info, $proc, $group) = @_;
    my @girs;
    my @typelibs;
    my $section = $info->field('section', 'NONE');
    my $madir = $MA_DIRS->value($proc->pkg_arch);
    # Slightly contrived, but it might be Architecture: all, in which
    # case this is the best we can do
    $madir = '${DEB_HOST_MULTIARCH}' unless defined $madir;

    if (my $xmldir = $info->index_resolved_path('usr/share/gir-1.0/')) {
        foreach my $child ($xmldir->children) {
            next unless $child =~ m/\.gir$/;
            push @girs, $child;
        }
    }

    if (my $dir = $info->index_resolved_path('usr/lib/girepository-1.0/')) {
        push @typelibs, $dir->children;
        foreach my $typelib ($dir->children) {
            tag('typelib-not-in-multiarch-directory',
                $typelib,"usr/lib/$madir/girepository-1.0");
        }
    }

    if (my $dir= $info->index_resolved_path("usr/lib/$madir/girepository-1.0"))
    {
        push @typelibs, $dir->children;
    }

    if ($section ne 'libdevel') {
        foreach my $gir (@girs) {
            tag('gir-section-not-libdevel', $gir, $section);
        }
    }

    if ($section ne 'introspection') {
        foreach my $typelib (@typelibs) {
            tag('typelib-section-not-introspection', $typelib, $section);
        }
    }

    if ($proc->pkg_arch eq 'all') {
        foreach my $gir (@girs) {
            tag('gir-in-arch-all-package', $gir);
        }
        foreach my $typelib (@typelibs) {
            tag('typelib-in-arch-all-package', $typelib);
        }
    }

  GIR: foreach my $gir (@girs) {
        my $expected = 'gir1.2-' . lc($gir->basename);
        $expected =~ s/\.gir$//;
        $expected =~ tr/_/-/;
        my $version = $info->field('version');

        foreach my $bin ($group->get_binary_processables) {
            next unless $bin->pkg_name =~ m/^gir1\.2-/;
            my $other = $bin->pkg_name.' (= '.$bin->info->field('version').')';
            if (    $bin->info->relation('provides')->implies($expected)
                and $info->relation('strong')->implies($other)) {
                next GIR;
            }
        }

        if (not $info->relation('strong')->implies("$expected (= $version)")) {
            tag('gir-missing-typelib-dependency', $gir, $expected);
        }
    }

    foreach my $typelib (@typelibs) {
        my $expected = 'gir1.2-' . lc($typelib->basename);
        $expected =~ s/\.typelib$//;
        $expected =~ tr/_/-/;
        if ($pkg ne $expected
            and not $info->relation('provides')->implies($expected)) {
            tag('typelib-package-name-does-not-match', $typelib, $expected);
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
