#!/usr/bin/perl -w
#
# lintian-info -- transform lintian tags into descriptive text
#
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

use strict;
use warnings;

use Getopt::Long();

# turn file buffering off:
STDOUT->autoflush;

use Lintian::Data;
use Lintian::Internal::FrontendUtil qw(split_tag);
use Lintian::Profile;

sub compat();

sub main {
    my ($annotate, $list_tags, $tags, $help, $prof);
    my (%already_displayed, $profile);
    my %opthash = (
        'annotate|a' => \$annotate,
        'list-tags|l' => \$list_tags,
        'tags|tag|t' => \$tags,
        'help|h' => \$help,
        'profile=s' => \$prof,
    );

    if (compat) {
        my $error = sub {
            die("The --$_[0] must be the first option if given\n");
        };
        $opthash{'include-dir=s'} = $error;
        $opthash{'user-dirs!'} = $error;
    }

    Getopt::Long::config('bundling', 'no_getopt_compat', 'no_auto_abbrev');
    Getopt::Long::GetOptions(%opthash) or die("error parsing options\n");

    # help
    if ($help) {
        my $me = 'dplint info';
        $me = 'lintian-info' if compat;
        print <<"EOT";
Usage: $me [log-file...] ...
       $me --annotate [overrides ...]
       $me --tags tag ...

Options:
    -a, --annotate     display descriptions of tags in Lintian overrides
    -l, --list-tags    list all tags Lintian knows about
    -t, --tag, --tags  display tag descriptions
    --profile X        use vendor profile X to determine severities
EOT
        if (compat) {
            # if we are called as lintian-info, we also accept
            # --include-dir and --[no-]user-dirs
            print <<'EOT';
    --include-dir DIR check for Lintian data in DIR
    --[no-]user-dirs  whether to include profiles from user directories

Note that --include-dir and --[no-]user-dirs must appear as the first
options if used.  Otherwise, they will trigger a deprecation warning.
EOT
        }

        exit 0;
    }

    $profile = dplint::load_profile($prof);

    Lintian::Data->set_vendor($profile);

    if ($list_tags) {
        foreach my $tag (sort $profile->tags) {
            print "$tag\n";
        }
        exit 0;
    }

    # If tag mode was specified, read the arguments as tags and display the
    # descriptions for each one.  (We don't currently display the severity,
    # although that would be nice.)
    if ($tags) {
        my $unknown = 0;
        for my $tag (@ARGV) {
            my $info = $profile->get_tag($tag, 1);
            if ($info) {
                print $info->code . ": $tag\n";
                print "N:\n";
                print $info->description('text', 'N:   ');
            } else {
                print "N: $tag\n";
                print "N:\n";
                print "N:   Unknown tag.\n";
                $unknown = 1;
            }
            print "N:\n";
        }
        exit($unknown ? 1 : 0);
    }

    my $type_re = qr/(?:binary|changes|source|udeb)/o;

    # Otherwise, read input files or STDIN, watch for tags, and add
    # descriptions whenever we see one, can, and haven't already
    # explained that tag.  Strip off color and HTML sequences.
    while (<>) {
        print;
        chomp;
        next if /^\s*$/;
        s/\e[\[\d;]*m//g;
        s/<span style=\"[^\"]+\">//g;
        s,</span>,,g;

        my $tag;
        if ($annotate) {
            my $tagdata;
            next unless m/^(?:                     # start optional part
                    (?:\S+)?                       # Optionally starts with package name
                    (?: \s*+ \[[^\]]+?\])?         # optionally followed by an [arch-list] (like in B-D)
                    (?: \s*+ $type_re)?            # optionally followed by the type
                  :\s++)?                          # end optional part
                ([\-\.a-zA-Z_0-9]+ (?:\s.+)?)$/ox; # <tag-name> [extra] -> $1
            $tagdata = $1;
            ($tag, undef) = split m/ /o, $tagdata, 2;
        } else {
            my @parts = split_tag($_);
            next unless @parts;
            $tag = $parts[5];
        }
        next if $already_displayed{$tag}++;
        my $info = $profile->get_tag($tag, 1);
        next unless $info;
        print "N:\n";
        print $info->description('text', 'N:   ');
        print "N:\n";
    }
    exit(0);
}

{
    my $backwards_compat;

    sub compat() {
        return $backwards_compat if defined($backwards_compat);
        $backwards_compat = 0;
        if (exists($ENV{'LINTIAN_DPLINT_CALLED_AS'})) {
            my $called_as = $ENV{'LINTIAN_DPLINT_CALLED_AS'};
            $backwards_compat = 1
              if $called_as =~ m{ (?: \A | /) lintian-info \Z}xsm;
        }
        return $backwards_compat;
    }
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
