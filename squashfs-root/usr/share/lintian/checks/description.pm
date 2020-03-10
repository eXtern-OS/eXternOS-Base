# description -- lintian check script -*- perl -*-

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

package Lintian::description;
use strict;
use warnings;
use autodie;

# Compared to a lower-case string, so it must be all lower-case
use constant DH_MAKE_PERL_TEMPLATE => 'this description was'
  . ' automagically extracted from the module by dh-make-perl';

use Encode qw(decode);

use Lintian::Data;
use Lintian::Check
  qw(check_spelling check_spelling_picky spelling_tag_emitter);
use Lintian::Tags qw(tag);
use Lintian::Util qw(strip);

my $PLANNED_FEATURES = Lintian::Data->new('description/planned-features');

my $SPELLING_ERROR_IN_SYNOPSIS
  = spelling_tag_emitter('spelling-error-in-description-synopsis');
my $SPELLING_ERROR_IN_DESCRIPTION
  = spelling_tag_emitter('spelling-error-in-description');

my $PICKY_SPELLING_ERROR_IN_SYNOPSIS
  = spelling_tag_emitter('capitalization-error-in-description-synopsis');
my $PICKY_SPELLING_ERROR_IN_DESCRIPTION
  = spelling_tag_emitter('capitalization-error-in-description');

sub run {
    my ($pkg, $type, $info, undef, $group) = @_;
    my $tabs = 0;
    my $lines = 0;
    my $template = 0;
    my $unindented_list = 0;
    my $synopsis;
    my $description;

    # description?
    my $full_description = $info->field('description');
    unless (defined $full_description) {
        tag 'package-has-no-description';
        return;
    }

    $full_description =~ m/^([^\n]*)\n(.*)$/s;
    ($synopsis, $description) = ($1, $2);
    unless (defined $synopsis) {
        # The first line will always be completely stripped but
        # continuations may have leading whitespace.  Therefore we
        # have to strip $full_description to restore this property,
        # when we use it as a fall-back value of the synopsis.
        $synopsis = strip($full_description);
        $description = '';
    }

    $description = '' unless defined($description);

    if ($synopsis =~ m/^\s*$/) {
        tag 'description-synopsis-is-empty';
    } else {
        if ($synopsis =~ m/^\Q$pkg\E\b/i) {
            tag 'description-starts-with-package-name';
        }
        if ($synopsis =~ m/^(an?|the)\s/i) {
            tag 'description-synopsis-starts-with-article';
        }
        if ($synopsis =~ m/(?<!etc)\.(?:\s*$|\s+\S+)/i) {
            tag 'description-synopsis-might-not-be-phrased-properly';
        }
        if ($synopsis =~ m/\t/) {
            tag 'description-contains-tabs' unless $tabs++;
        }
        if ($synopsis =~ m/^missing\s*$/i) {
            tag 'description-is-debmake-template' unless $template++;
        } elsif ($synopsis =~ m/<insert up to 60 chars description>/) {
            tag 'description-is-dh_make-template' unless $template++;
        }
        if ($synopsis !~ m/\s/) {
            tag 'description-too-short', $synopsis;
        }
        my $pkg_fmt = lc $pkg;
        my $synopsis_fmt = lc $synopsis;
        # made a fuzzy match
        $pkg_fmt =~ s,[-_], ,g;
        $synopsis_fmt =~ s,[-_/\\], ,g;
        $synopsis_fmt =~ s,\s+, ,g;
        if ($pkg_fmt eq $synopsis_fmt) {
            tag 'description-is-pkg-name', $synopsis;
        }

        # We have to decode into UTF-8 to get the right length for the
        # length check.  If the changelog uses a non-UTF-8 encoding,
        # this will mangle it, but it doesn't matter for the length
        # check.
        if (length(decode('utf-8', $synopsis)) >= 80) {
            tag 'description-too-long';
        }
    }

    my $flagged_homepage;
    foreach (split /\n/, $description) {
        next if m/^ \.\s*$/o;

        if ($lines == 0) {
            my $firstline = lc $_;
            my $lsyn = lc $synopsis;
            if ($firstline =~ /^\Q$lsyn\E$/) {
                tag 'description-synopsis-is-duplicated';
            } else {
                $firstline =~ s/[^a-zA-Z0-9]+//g;
                $lsyn =~ s/[^a-zA-Z0-9]+//g;
                if ($firstline eq $lsyn) {
                    tag 'description-synopsis-is-duplicated';
                }
            }
        }

        $lines++;

        if (m/^ \.\s*\S/o) {
            tag 'description-contains-invalid-control-statement';
        } elsif (m/^ [\-\*]/o) {
       # Print it only the second time.  Just one is not enough to be sure that
       # it's a list, and after the second there's no need to repeat it.
            tag 'possible-unindented-list-in-extended-description'
              if $unindented_list++ == 2;
        }

        if (m/\t/o) {
            tag 'description-contains-tabs' unless $tabs++;
        }

        if (m,^\s*Homepage: <?https?://,i) {
            tag 'description-contains-homepage';
            $flagged_homepage = 1;
        }

        foreach my $regex ($PLANNED_FEATURES->all()) {
            tag 'description-mentions-planned-features', "(line $lines)"
              if m/$regex/i;
        }

        if (index(lc($_), DH_MAKE_PERL_TEMPLATE) != -1) {
            tag 'description-contains-dh-make-perl-template';
        }

        my $first_person = $_;
        while ($first_person
            =~ m/(?:^|\s)(I|[Mm]y|[Oo]urs?|mine|myself|me|us|[Ww]e)(?:$|\s)/) {
            my $word = $1;
            $first_person =~ s/\Q$word//;
            tag 'using-first-person-in-description', "line $lines: $word";
        }

        if ($lines == 1) {
            # checks for the first line of the extended description:
            if (m/^ \s/o) {
                tag 'description-starts-with-leading-spaces';
            }
            if (m/^\s*missing\s*$/oi) {
                tag 'description-is-debmake-template' unless $template++;
            } elsif (m/<insert long description, indented with spaces>/) {
                tag 'description-is-dh_make-template' unless $template++;
            }
        }

        if (length(decode('utf-8', $_)) > 80) {
            tag 'extended-description-line-too-long';
        }
    }

    if ($type ne 'udeb') {
        if ($lines == 0) {
            # Ignore debug packages with empty "extended" description
            # "debug symbols for pkg foo" is generally descriptive
            # enough.
            tag 'extended-description-is-empty'
              if not $info->is_pkg_class('debug');
        } elsif ($lines <= 2 and not $synopsis =~ /(?:dummy|transition)/i) {
            tag 'extended-description-is-probably-too-short'
              unless $info->is_pkg_class('any-meta')
              or $pkg =~ m{-dbg\Z}xsm;
        } elsif ($description =~ /^ \.\s*\n|\n \.\s*\n \.\s*\n|\n \.\s*\n?$/) {
            tag 'extended-description-contains-empty-paragraph';
        }
    }

    # Check for a package homepage in the description and no Homepage
    # field.  This is less accurate and more of a guess than looking
    # for the old Homepage: convention in the body.
    unless ($info->field('homepage') or $flagged_homepage) {
        if (
            $description =~ /homepage|webpage|website|url|upstream|web\s+site
                         |home\s+page|further\s+information|more\s+info
                         |official\s+site|project\s+home/xi
            and $description =~ m,\b(https?://[a-z0-9][^>\s]+),i
          ) {
            tag 'description-possibly-contains-homepage', $1;
        } elsif ($description =~ m,\b(https?://[a-z0-9][^>\s]+)>?\.?\s*\z,i) {
            tag 'description-possibly-contains-homepage', $1;
        }
    }

    if ($synopsis) {
        check_spelling($synopsis, $group->info->spelling_exceptions,
            $SPELLING_ERROR_IN_SYNOPSIS);
        # Auto-generated dbgsym packages will use the package name in
        # their synopsis.  Unfortunately, some package names trigger a
        # capitalization error, such as "dbus" -> "D-Bus".  Therefore,
        # we exempt auto-generated packages from this check.
        check_spelling_picky($synopsis, $PICKY_SPELLING_ERROR_IN_SYNOPSIS)
          if not $info->is_pkg_class('auto-generated');
    }

    if ($description) {
        check_spelling(
            $description,
            $group->info->spelling_exceptions,
            $SPELLING_ERROR_IN_DESCRIPTION
        );
        check_spelling_picky($description,
            $PICKY_SPELLING_ERROR_IN_DESCRIPTION);
    }

    if ($pkg =~ /^lib(.+)-perl$/) {
        my $mod = $1;
        my @mod_path_elements = split(/-/, $mod);
        $mod = join('::', map {ucfirst} @mod_path_elements);
        my $mod_lc = lc($mod);

        my $pm_found = 0;
        my $pmpath = join('/', @mod_path_elements).'.pm';
        my $pm     = $mod_path_elements[-1].'.pm';

        foreach my $filepath ($info->sorted_index) {
            if ($filepath =~ m(\Q$pmpath\E\z|/\Q$pm\E\z)i) {
                $pm_found = 1;
                last;
            }
        }

        tag 'perl-module-name-not-mentioned-in-description', $mod
          if (index(lc($description), $mod_lc) < 0 and $pm_found);
    }

    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
