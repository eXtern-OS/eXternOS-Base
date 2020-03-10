# deb-format -- lintian check script -*- perl -*-

# Copyright (C) 2009 Russ Allbery
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

package Lintian::deb_format;
use strict;
use warnings;
use autodie;

use List::MoreUtils qw(first_index none);

use Lintian::Command qw(safe_qx spawn);
use Lintian::Data;
use Lintian::Tags qw(tag);

# The files that contain error messages from tar, which we'll check and issue
# tags for if they contain something unexpected, and their corresponding tags.
# - These files are created by bin-pkg-control, index and unpacked respectively
our %ERRORS = (
    'control-errors'       => 'tar-errors-from-control',
    'control-index-errors' => 'tar-errors-from-control',
    'index-errors'         => 'tar-errors-from-data',
    'unpacked-errors'      => 'tar-errors-from-data'
);

my $EXTRA_MEMBERS = Lintian::Data->new('deb-format/extra-members');

sub run {
    my (undef, $type, $info) = @_;
    my $deb = $info->lab_data_path('deb');

    # Run ar t on the *.deb file.  deb will be a symlink to it.
    my $failed; # set to one when something is so bad that we can't continue
    my $opts = {};
    my $success = spawn($opts, ['ar', 't', $deb]);
    if ($success) {
        my @members = split("\n", ${ $opts->{out} });
        my $count = scalar(@members);
        my ($ctrl_member, $data_member);
        if ($count < 3) {
            tag 'malformed-deb-archive',
              "found only $count members instead of 3";
        } elsif ($members[0] ne 'debian-binary') {
            tag 'malformed-deb-archive',
              "first member $members[0] not debian-binary";
        } elsif (
            $count == 3 and none {
                substr($_, 0, 1) eq '_';
            }
            @members
          ) {
            # Fairly common case - if there are only 3 members without
            # "_", we can trivially determine their (expected)
            # positions.  We only use this case when there are no
            # "extra" members, because they can trigger more tags
            # (see below)
            (undef, $ctrl_member, $data_member) = @members;
        } else {
            my $ctrl_index
              = first_index { substr($_, 0, 1) ne '_' } @members[1..$#members];
            my $data_index;

            if ($ctrl_index != -1) {
                # Since we searched only a sublist of @members, we have to
                # add 1 to $ctrl_index
                $ctrl_index++;
                $ctrl_member = $members[$ctrl_index];
                $data_index = first_index { substr($_, 0, 1) ne '_' }
                @members[$ctrl_index+1..$#members];
                if ($data_index != -1) {
                    # Since we searched only a sublist of @members, we
                    # have to adjust $data_index
                    $data_index += $ctrl_index + 1;
                    $data_member = $members[$data_index];
                }
            }

            # Extra members
            # NB: We deliberately do not allow _extra member,
            # since various tools seems to be unable to cope
            # with them particularly dak
            # see https://wiki.debian.org/Teams/Dpkg/DebSupport
            for my $i (1..$#members) {
                my $member = $members[$i];
                my $actual_index = $i;
                my ($expected, $text);
                next if $i == $ctrl_index or $i == $data_index;
                $expected = $EXTRA_MEMBERS->value($member);
                if (defined($expected)) {
                    next if $expected eq 'ANYWHERE';
                    next if $expected == $actual_index;
                    $text = "expected at position $expected, but appeared";
                } elsif (substr($member,0,1) eq '_') {
                    $text = 'unexpected _member';
                } else {
                    $text = 'unexpected member';
                }
                tag 'misplaced-extra-member-in-deb',
                  "$member ($text at position $actual_index)";
            }
        }

        if (not defined($ctrl_member)) {
            # Somehow I doubt we will ever get this far without a control
            # file... :)
            tag 'malformed-deb-archive', 'Missing control.tar.gz member';
            $failed = 1;
        } else {
            if (
                $ctrl_member !~ m/\A
                     control\.tar(?:\.(?:gz|xz))?  \Z/xsm
              ) {
                tag 'malformed-deb-archive',
                  join(' ',
                    "second (official) member $ctrl_member",
                    'not control.tar.(gz|xz)');
                $failed = 1;
            } elsif ($ctrl_member eq 'control.tar') {
                tag 'uses-no-compression-for-control-tarball';
            }
            tag 'control-tarball-compression-format',
              $ctrl_member =~ s/^control\.tar\.?//r || '(none)';
        }

        if (not defined($data_member)) {
            # Somehow I doubt we will ever get this far without a data
            # member (i.e. I suspect unpacked and index will fail), but
            # mah
            tag 'malformed-deb-archive', 'Missing data.tar member';
            $failed = 1;
        } else {
            if (
                $data_member !~ m/\A
                     data\.tar(?:\.(?:gz|bz2|xz|lzma))?  \Z/xsm
              ) {
                # wasn't okay after all
                tag 'malformed-deb-archive',
                  join(' ',
                    "third (official) member $data_member",
                    'not data.tar.(gz|bz2|xz)');
                $failed = 1;
            } elsif ($type eq 'udeb'
                && $data_member !~ m/^data\.tar\.[gx]z$/) {
                tag 'udeb-uses-unsupported-compression-for-data-tarball';
            } elsif ($data_member eq 'data.tar.lzma') {
                tag 'uses-deprecated-compression-for-data-tarball', 'lzma';
                # Ubuntu's archive allows lzma packages.
                tag 'lzma-deb-archive';
            } elsif ($data_member eq 'data.tar.bz2') {
                tag 'uses-deprecated-compression-for-data-tarball', 'bzip2';
            } elsif ($data_member eq 'data.tar') {
                tag 'uses-no-compression-for-data-tarball';
            }
            tag 'data-tarball-compression-format',
              $data_member =~ s/^data\.tar\.?//r || '(none)';
        }
    } else {
        # unpack will probably fail so we'll never get here, but may as well be
        # complete just in case.
        my $error = ${ $opts->{err} };
        $error =~ s/\n.*//s;
        $error =~ s/^ar:\s*//;
        $error =~ s/^deb:\s*//;
        tag 'malformed-deb-archive', "ar error: $error";
    }

    # Check the debian-binary version number.  We probably won't get
    # here because dpkg-deb will decline to unpack the deb, but be
    # thorough just in case.  We may eventually have a case where dpkg
    # supports a newer format but it's not permitted in the archive
    # yet.
    if (not defined($failed)) {
        my $output = safe_qx('ar', 'p', $deb, 'debian-binary');
        if ($? != 0) {
            tag 'malformed-deb-archive', 'cannot read debian-binary member';
        } elsif ($output !~ /^2\.\d+\n/) {
            my ($version) = split(m/\n/, $output);
            tag 'malformed-deb-archive', "version $version not 2.0";
        }
    }

    # If either control-errors or index-errors exist, tar produced
    # error output when processing the package.  We want to report
    # those as tags unless they're just tar noise that doesn't
    # represent an actual problem.
    for my $file (keys %ERRORS) {
        my $tag = $ERRORS{$file};
        my $path = $info->lab_data_path($file);
        if (-s $path) {
            open(my $fd, '<', $path);
            while (my $line = <$fd>) {
                chomp($line);
                $line =~ s,^(?:[/\w]+/)?tar: ,,;

                # Record size errors are harmless.  Ignore implausibly
                # old timestamps in the data section since we already
                # check for that elsewhere, but still warn for
                # control.
                next if $line =~ /^Record size =/;
                if ($tag eq 'tar-errors-from-data') {
                    next if $line =~ /implausibly old time stamp/;
                }
                tag $tag, $line;
            }
            close($fd);
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
