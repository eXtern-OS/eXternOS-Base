# version-substvars -- lintian check script -*- perl -*-
#
# Copyright (C) 2006 Adeodato Simó
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

# SUMMARY
# =======
#
# What breaks
# -----------
#
# (b1) any -> any (= ${source:Version})          -> use b:V
# (b2) any -> all (= ${binary:Version}) [or S-V] -> use s:V
# (b3) all -> any (= ${either-of-them})          -> use (>= ${s:V}),
#                                                   optionally (<< ${s:V}.1~)
#
# Note (b2) also breaks if (>= ${binary:Version}) [or S-V] is used.
#
# Always warn on ${Source-Version} even if it doesn't break since the substvar
# is now considered deprecated.

package Lintian::version_substvars;
use strict;
use warnings;
use autodie;

use Lintian::Relation qw(:constants);
use Lintian::Tags qw(tag);
use Lintian::Util qw($PKGNAME_REGEX);

sub run {

    my (undef, undef, $info) = @_;

    my @dep_fields
      = qw(depends pre-depends recommends suggests conflicts replaces);

    foreach my $pkg1 ($info->binaries) {
        my ($pkg1_is_any, $pkg2, $pkg2_is_any, $substvar_strips_binNMU);

        $pkg1_is_any
          = ($info->binary_field($pkg1, 'architecture', '') ne 'all');

        foreach my $field (@dep_fields) {
            next unless $info->binary_field($pkg1, $field);
            my $rel = $info->binary_relation($pkg1, $field);
            my $svid = 0;
            my $visitor = sub {
                if (m/\$[{]Source-Version[}]/o and not $svid) {
                    $svid++;
                    tag 'substvar-source-version-is-deprecated', $pkg1;
                }
                if (
                    m/^($PKGNAME_REGEX)(?: :[-a-z0-9]+)? \s*   # pkg-name $1
                       \(\s*[\>\<]?[=\>\<]\s*                  # REL 
                        \$[{](?:Source-|source:|binary:)Version[}] # {subvar}
                     /x
                  ) {
                    my $other = $1;
                    # We can't test dependencies on packages whose names are
                    # formed via substvars expanded during the build.  Assume
                    # those maintainers know what they're doing.
                    tag 'version-substvar-for-external-package',
                      "$pkg1 -> $other"
                      unless $info->binary_field($other, 'architecture')
                      or $other =~ /\$\{\S+\}/;
                }
            };
            $rel->visit($visitor, VISIT_PRED_FULL);
        }

        foreach (
            split(
                m/,/,
                (
                        $info->binary_field($pkg1, 'pre-depends', '').', '
                      . $info->binary_field($pkg1, 'depends', '')))
          ) {
            next
              unless m/($PKGNAME_REGEX)(?: :any)? \s*               # pkg-name
                       \(\s*(\>)?=\s*                               # rel
                       \$[{]((?:Source-|source:|binary:)Version)[}] # subvar
                      /x;

            my $gt = $2//'';
            $pkg2 = $1;
            $substvar_strips_binNMU = ($3 eq 'source:Version');

            if (not $info->binary_field($pkg2, 'architecture')) {
                # external relation or subst var package - either way,
                # handled above.
                next;
            }
            $pkg2_is_any
              = ($info->binary_field($pkg2, 'architecture', '') ne 'all');

            if ($pkg1_is_any) {
                if ($pkg2_is_any and $substvar_strips_binNMU) {
                    unless ($gt) {
                        # (b1) any -> any (= ${source:Version})
                        tag 'not-binnmuable-any-depends-any', "$pkg1 -> $pkg2";
                    } else {
                        # any -> any (>= ${source:Version})
                        # technically this can be "binNMU'ed", though it is
                        # a bit weird.
                        1;
                    }
                } elsif (not $pkg2_is_any) {
                    # (b2) any -> all ( = ${binary:Version}) [or S-V]
                    # or  -- same --  (>= ${binary:Version}) [or S-V]
                    tag 'not-binnmuable-any-depends-all', "$pkg1 -> $pkg2"
                      if not $substvar_strips_binNMU;
                    if ($substvar_strips_binNMU and not $gt) {
                        tag 'maybe-not-arch-all-binnmuable', "$pkg1 -> $pkg2";
                    }
                }
            } elsif ($pkg2_is_any && !$gt) {
                # (b3) all -> any (= ${either-of-them})
                tag 'not-binnmuable-all-depends-any', "$pkg1 -> $pkg2";
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
