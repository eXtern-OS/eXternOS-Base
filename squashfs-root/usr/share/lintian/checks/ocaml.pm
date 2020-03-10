# ocaml -- lintian check script -*- perl -*-
#
# Copyright © 2009 Stéphane Glondu
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

package Lintian::ocaml;

use strict;
use warnings;
use autodie;

use File::Basename;
use Lintian::Relation ();
use Lintian::Tags qw(tag);

# The maximum number of *.cmi files to show individually.
our $MAX_CMI = 3;

sub run {
    my ($pkg, undef, $info) = @_;

    # Collect information about .a files from ar-info dump
    my %provided_o;
    open(my $fd, '<', $info->lab_data_path('ar-info'));
    while (my $line = <$fd>) {
        chomp($line);
        if ($line =~ /^(?:\.\/)?([^:]+): (.*)$/) {
            my ($filename, $contents) = ($1, $2);
            my $dirname = dirname($filename);
            for my $entry (split m/ /o, $contents) {
                # Note: a .o may be legitimately in several different .a
                $provided_o{"$dirname/$entry"} = $filename;
            }
        }
    }
    close($fd);

    # is it a library package?
    my $is_lib_package = 0;
    if ($pkg =~ /^lib/) {
        $is_lib_package = 1;
    }

    # is it a development package?
    my $is_dev_package = 0;
    if (
        $pkg =~ m/
           (?: -dev
              |\A camlp[45](?:-extra)?
              |\A ocaml  (?:
                     -nox
                    |-interp
                    |-compiler-libs
                  )?
           )\Z/xsm
      ){
        $is_dev_package = 1;
    }

    # for libraries outside /usr/lib/ocaml
    my $outside_number = 0;
    my $outside_prefix;

    # dangling .cmi files (we show only $MAX_CMI of them)
    my $cmi_number = 0;

    # dev files in nondev package
    my $dev_number = 0;
    my $dev_prefix;

    # does the package provide a META file?
    my $has_meta = 0;

    foreach my $file ($info->sorted_index) {

        # For each .cmxa file, there must be a matching .a file (#528367)
        $_ = $file;
        if (s/\.cmxa$/.a/ && !$info->index($_)) {
            tag 'ocaml-dangling-cmxa', $file;
        }

        # For each .cmxs file, there must be a matching .cma or .cmo file
        # (at least, in library packages)
        if ($is_lib_package) {
            $_ = $file;
            if (   s/\.cmxs$/.cm/
                && !$info->index("${_}a")
                && !$info->index("${_}o")) {
                tag 'ocaml-dangling-cmxs', $file;
            }
        }

        # The .cmx counterpart: for each .cmx file, there must be a
        # matching .o file, which can be there by itself, or embedded in a
        # .a file in the same directory
        $_ = $file;
        if (   s/\.cmx$/.o/
            && !$info->index($_)
            && !(exists $provided_o{$_})) {
            tag 'ocaml-dangling-cmx', $file;
        }

        # $somename.cmi should be shipped with $somename.mli or $somename.ml
        $_ = $file;
        if (   $is_dev_package
            && s/\.cmi$/.ml/
            && !$info->index("${_}i")
            && !$info->index($_)) {
            $cmi_number++;
            if ($cmi_number <= $MAX_CMI) {
                tag 'ocaml-dangling-cmi', $file;
            }
        }

        # non-dev packages should not ship .cmi, .cmx or .cmxa files
        if ($file =~ m/\.cm(i|xa?)$/) {
            $dev_number++;
            if (defined $dev_prefix) {
                chop $dev_prefix while ($file !~ m@^$dev_prefix@);
            } else {
                $dev_prefix = $file;
            }
        }

        # $somename.cmo should usually not be shipped with $somename.cma
        $_ = $file;
        if (s/\.cma$/.cmo/ && $info->index($_)) {
            tag 'ocaml-stray-cmo', $file;
        }

        # development files outside /usr/lib/ocaml (.cmi, .cmx, .cmxa)
        # .cma, .cmo and .cmxs are excluded because they can be plugins
        if ($file =~ m/\.cm(i|xa?)$/ && $file !~ m@^usr/lib/ocaml/@) {
            $outside_number++;
            if (defined $outside_prefix) {
                chop $outside_prefix while ($file !~ m@^$outside_prefix@);
            } else {
                $outside_prefix = $file;
            }
        }

        # If there is a META file, ocaml-findlib should be at least suggested.
        $has_meta = 1 if $file =~ m@^usr/lib/ocaml/(.+/)?META(\..*)?$@;
    }

    if ($is_dev_package) {
        # summary about .cmi files
        if ($cmi_number > $MAX_CMI) {
            my $plural = ($cmi_number - $MAX_CMI == 1) ? '' : 's';
            tag 'ocaml-dangling-cmi', ($cmi_number - $MAX_CMI),
              "more file$plural not shown";
        }
        # summary about /usr/lib/ocaml
        if ($outside_number) {
            $outside_prefix = dirname($outside_prefix);
            my $plural = ($outside_number == 1) ? '' : 's';
            tag 'ocaml-dev-file-not-in-usr-lib-ocaml',
              "$outside_number file$plural in $outside_prefix";
        }
        if ($has_meta) {
            my $depends = $info->relation('all');
            tag 'ocaml-meta-without-suggesting-findlib'
              unless $depends->implies('ocaml-findlib');
        }
    } else {
        # summary about dev files
        if ($dev_number > 0) {
            $dev_prefix = dirname($dev_prefix);
            my $plural = ($dev_number == 1) ? '' : 's';
            tag 'ocaml-dev-file-in-nondev-package',
              "$dev_number file$plural in $dev_prefix";
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
