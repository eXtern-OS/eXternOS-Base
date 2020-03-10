# python -- lintian check script -*- perl -*-
#
# Copyright (C) 2016 Chris Lamb
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

package Lintian::python;
use strict;
use warnings;
use autodie;

use List::MoreUtils qw(any none);

use Lintian::Tags qw(tag);
use Lintian::Relation qw(:constants);

my @FIELDS = qw(Depends Pre-Depends Recommends Suggests);
my @IGNORE = qw(-dev$ -docs?$ -common$ -tools$);
my @PYTHON2 = qw(python python2.7 python-dev);

my %DJANGO_PACKAGES = (
    '^python3-django-' => 'python3-django',
    '^python2?-django-' => 'python-django',
);

my %REQUIRED_DEPENDS = (
    'python2' => 'python-minimal:any | python:any',
    'python3' => 'python3-minimal:any | python3:any',
);

my %MISMATCHED_SUBSTVARS = (
    '^python3-.+' => '${python:Depends}',
    '^python2?-.+' => '${python3:Depends}',
);

sub run {
    my ($pkg, $type, $info) = @_;

    if ($type eq 'source') {
        _run_source($pkg, $info);
    } else {
        _run_binary($pkg, $info);
    }

    return;
}

sub _run_source {
    my ($pkg, $info) = @_;

    my @package_names = $info->binaries;
    foreach my $bin (@package_names) {
        # Python 2 modules
        if ($bin =~ /^python2?-(.*)$/) {
            my $suffix = $1;
            next if any { $bin =~ /$_/ } @IGNORE;
            next if any { $_ eq "python3-${suffix}" } @package_names;
            # Don't trigger if we ship any Python 3 module
            next if any {
                $info->binary_relation($_, 'all')
                  ->implies('${python3:Depends}')
            }
            @package_names;
            tag 'python-foo-but-no-python3-foo', $bin;
        }
    }

    my $build_all = $info->relation('build-depends-all');
    tag 'build-depends-on-python-sphinx-only'
      if $build_all->implies('python-sphinx')
      and not $build_all->implies('python3-sphinx');

    tag 'alternatively-build-depends-on-python-sphinx-and-python3-sphinx'
      if $info->field('build-depends', '')
      =~ m,\bpython-sphinx\s+\|\s+python3-sphinx\b,g;

    # Mismatched substvars
    foreach my $regex (keys %MISMATCHED_SUBSTVARS) {
        my $substvar = $MISMATCHED_SUBSTVARS{$regex};
        for my $binpkg ($info->binaries) {
            next if any { $binpkg =~ /$_/ } @IGNORE;
            next if $binpkg !~ qr/$regex/;
            tag 'mismatched-python-substvar', $binpkg, $substvar
              if $info->binary_relation($binpkg, 'all')->implies($substvar);
        }
    }

    return;
}

sub _run_binary {
    my ($pkg, $info) = @_;

    my $deps = Lintian::Relation->and($info->relation('all'),
        $info->relation('provides'), $pkg);
    my @entries = $info->changelog ? $info->changelog->data : ();

    # Check for missing dependencies
    if ($pkg !~ /-dbg$/) {
        foreach my $file ($info->sorted_index) {
            if (    $file->is_file
                and $file
                =~ m,usr/lib/(?<version>python[23])[\d.]*/(?:site|dist)-packages,
                and not $deps->implies($REQUIRED_DEPENDS{$+{version}})) {
                tag 'python-package-missing-depends-on-python';
                last;
            }
        }
    }

    # Python 2 modules
    if (    $pkg =~ /^python2?-/
        and none { $pkg =~ /$_$/ } @IGNORE
        and @entries == 1
        and $entries[0]->Changes
        !~ /\bpython 2(?:\.x)? (?:variant|version)\b/im
        and index($entries[0]->Changes, $pkg) == -1) {
        tag 'new-package-should-not-package-python2-module', $pkg;
    }

    # Python applications
    if ($pkg !~ /^python[23]?-/ and none { $_ eq $pkg } @PYTHON2) {
        for my $field (@FIELDS) {
            for my $dep (@PYTHON2) {
                tag 'dependency-on-python-version-marked-for-end-of-life',
                  "($field: $dep)"
                  if $info->relation($field)->implies("$dep:any");
            }
        }
    }

    # Django modules
    foreach my $regex (keys %DJANGO_PACKAGES) {
        my $basepkg = $DJANGO_PACKAGES{$regex};
        next if $pkg !~ /$regex/;
        next if any { $pkg =~ /$_/ } @IGNORE;
        tag 'django-package-does-not-depend-on-django', $basepkg
          if not $info->relation('strong')->implies($basepkg);
    }

    if ($pkg =~ /^python([23]?)-/ and none { $pkg =~ /$_/ } @IGNORE) {
        my $version = $1 || '2'; # Assume python-foo is a Python 2.x package
        my @prefixes = ($version eq '2') ? 'python3' : ('python', 'python2');

        for my $field (@FIELDS) {
            for my $prefix (@prefixes) {
                my $visit = sub {
                    my $rel = $_;
                    return if any { $rel =~ /$_/ } @IGNORE;
                    #<<< No tidy (tag name too long)
                    tag 'python-package-depends-on-package-from-other-python-variant',
                        "$field: $rel" if /^$prefix-/;
                    #>>>
                };
                $info->relation($field)->visit($visit, VISIT_PRED_NAME);
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
