# copyright-file -- lintian check script -*- perl -*-

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

package Lintian::copyright_file;
use strict;
use warnings;
use autodie;

use constant {
    DH_MAKE_TODO_BOILERPLATE_1 =>join(q{ },
        '# Please also look if there are files or directories',
        "which have a\n\# different copyright/license attached",
        'and list them here.'),
    DH_MAKE_TODO_BOILERPLATE_2 =>join(q{ },
        '# If you want to use GPL v2 or later for the /debian/\*',
        "files use\n\# the following clauses, or change it to suit.",
        'Delete these two lines'),
};

use Encode qw(decode);
use List::MoreUtils qw(any);

use Lintian::Check qw(check_spelling spelling_tag_emitter);
use Lintian::Data ();
use Lintian::Tags qw(tag);
use Lintian::Util
  qw(slurp_entire_file file_is_encoded_in_non_utf8 read_dpkg_control);

our $KNOWN_ESSENTIAL = Lintian::Data->new('fields/essential');
our $KNOWN_COMMON_LICENSES
  =  Lintian::Data->new('copyright-file/common-licenses');

my $SPELLING_ERROR_IN_COPYRIGHT
  = spelling_tag_emitter('spelling-error-in-copyright');

sub run {
    my ($pkg, undef, $info, $proc, $group) = @_;
    my $found = 0;
    my $linked = 0;
    my $path = "usr/share/doc/$pkg";

    if ($info->index("$path/copyright.gz")) {
        tag 'copyright-file-compressed';
        $found = 1;
    }

    if (my $index_info = $info->index("$path/copyright")) {
        $found = 1;
        if ($index_info->is_symlink) {
            tag 'copyright-file-is-symlink';
            $linked = 1;
            # Fall through here - coll/copyright-file protects us
            # from reading through an "evil" link.
        }
    }

    if (not $found) {
        my $index_info = $info->index($path);
        if (defined $index_info && $index_info->is_symlink) {
            my $link = $index_info->link;

            # check if this symlink references a directory elsewhere
            if ($link =~ m,^(?:\.\.)?/,) {
                tag 'usr-share-doc-symlink-points-outside-of-usr-share-doc',
                  $link;
                return;
            }

            # The symlink may point to a subdirectory of another
            # /usr/share/doc directory.  This is allowed if this
            # package depends on link and both packages come from the
            # same source package.
            #
            # Policy requires that packages be built from the same
            # source if they're going to do this, which by my (rra's)
            # reading means that we should have a strict version
            # dependency.  However, in practice the copyright file
            # doesn't change a lot and strict version dependencies
            # cause other problems (such as with arch: any / arch: all
            # package combinations and binNMUs).
            #
            # We therefore just require the dependency for now and
            # don't worry about the version number.
            $link =~ s,/.*,,;
            if (not depends_on($info, $proc, $link)) {
                tag 'usr-share-doc-symlink-without-dependency', $link;
                return;
            }
            # Check if the link points to a package from the same source.
            check_cross_link($group, $link);
            return;
        }
    }

    if (not $found) {
        # #522827: special exception for perl for now
        tag 'no-copyright-file'
          unless $pkg eq 'perl';
        return;
    }

    my $dcopy = $info->lab_data_path('copyright');
    # check that copyright is UTF-8 encoded
    my $line = file_is_encoded_in_non_utf8($dcopy);
    if ($line) {
        tag 'debian-copyright-file-uses-obsolete-national-encoding',
          "at line $line";
    }

    # check contents of copyright file
    $_ = slurp_entire_file($dcopy);

    if (m,\r,) {
        tag 'copyright-has-crs';
    }

    my $wrong_directory_detected = 0;

    if (m{ (usr/share/common-licenses/ ( [^ \t]*? ) \.gz) }xsm) {
        my ($path, $license) = ($1, $2);
        if ($KNOWN_COMMON_LICENSES->known($license)) {
            tag 'copyright-refers-to-compressed-license', $path;
        }
    }

    # Avoid complaining about referring to a versionless license file
    # if the word "version" appears nowhere in the copyright file.
    # This won't catch all of our false positives for GPL references
    # that don't include a specific version number, but it will get
    # the obvious ones.
    if (m,(usr/share/common-licenses/(L?GPL|GFDL))([^-]),i) {
        my ($ref, $license, $separator) = ($1, $2, $3);
        if ($separator =~ /[\d\w]/) {
            tag 'copyright-refers-to-nonexistent-license-file',
              "$ref$separator";
        } elsif (m,\b(?:any|or)\s+later(?:\s+version)?\b,i
            || m,License: $license-[\d\.]+\+,i
            || m,as Perl itself,i
            || m,License-Alias:\s+Perl,
            || m,License:\s+Perl,) {
            tag 'copyright-refers-to-symlink-license', $ref;
        } else {
            tag 'copyright-refers-to-versionless-license-file', $ref
              if /\bversion\b/;
        }
    }

    # References to /usr/share/common-licenses/BSD are deprecated as of Policy
    # 3.8.5.
    if (m,/usr/share/common-licenses/BSD,) {
        tag 'copyright-refers-to-deprecated-bsd-license-file';
    }

    if (m,(usr/share/common-licences),) {
        tag 'copyright-refers-to-incorrect-directory', $1;
        $wrong_directory_detected = 1;
    }

    if (m,usr/share/doc/copyright,) {
        tag 'copyright-refers-to-old-directory';
        $wrong_directory_detected = 1;
    }

    if (m,usr/doc/copyright,) {
        tag 'copyright-refers-to-old-directory';
        $wrong_directory_detected = 1;
    }

    # Lame check for old FSF zip code.  Try to avoid false positives from other
    # Cambridge, MA addresses.
    if (m/(?:Free\s*Software\s*Foundation.*02139|02111-1307)/s) {
        tag 'old-fsf-address-in-copyright-file';
    }

    # Whether the package is covered by the GPL, used later for the
    # libssl check.
    my $gpl;

    if (
        length($_) > 12_000
        and (
            m/  \b \QGNU GENERAL PUBLIC LICENSE\E \s*
                    \QTERMS AND CONDITIONS FOR COPYING,\E \s*
                    \QDISTRIBUTION AND MODIFICATION\E\b/mx
            or (    m/\bGNU GENERAL PUBLIC LICENSE\s*Version 3/
                and m/\bTERMS AND CONDITIONS\s/))
      ) {
        tag 'copyright-file-contains-full-gpl-license';
        $gpl = 1;
    }

    if (    length($_) > 12_000
        and m/\bGNU Free Documentation License\s*Version 1\.2/
        and m/\b1\. APPLICABILITY AND DEFINITIONS/) {
        tag 'copyright-file-contains-full-gfdl-license';
    }

    if (    length($_) > 10_000
        and m/\bApache License\s+Version 2\.0,/
        and m/TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION/) {
        tag 'copyright-file-contains-full-apache-2-license';
    }

    # wtf?
    if ((m,common-licenses(/\S+),) && (!m,/usr/share/common-licenses/,)) {
        tag 'copyright-does-not-refer-to-common-license-file', $1;
    }

    # This check is a bit prone to false positives, since some other
    # licenses mention the GPL.  Also exclude any mention of the GPL
    # following what looks like mail header fields, since sometimes
    # e-mail discussions of licensing are included in the copyright
    # file but aren't referring to the license of the package.
    if (
        not(
               m,/usr/share/common-licenses,
            || m/Zope Public License/
            || m/LICENSE AGREEMENT FOR PYTHON 1.6.1/
            || m/LaTeX Project Public License/
            || m/(?:^From:.*^To:|^To:.*^From:).*(?:GNU General Public License|GPL)/ms
            || m/AFFERO GENERAL PUBLIC LICENSE/
            || m/GNU Free Documentation License[,\s]*Version 1\.1/
            || m/CeCILL FREE SOFTWARE LICENSE AGREEMENT/ #v2.0
            || m/FREE SOFTWARE LICENSING AGREEMENT CeCILL/ #v1.1
            || m/CNRI OPEN SOURCE GPL-COMPATIBLE LICENSE AGREEMENT/
            || m/compatible\s+with\s+(?:the\s+)?(?:GNU\s+)?GPL/
            || m/(?:GNU\s+)?GPL\W+compatible/
            || m/was\s+previously\s+(?:distributed\s+)?under\s+the\s+GNU/
            || m/means\s+either\s+the\s+GNU\s+General\s+Public\s+License/
            || $wrong_directory_detected
        )
      ) {
        if (
            check_names_texts(
                qr/\b(?:GFDL|gnu[-_]free[-_]documentation[-_]license)\b/i,
                qr/GNU Free Documentation License|(?-i:\bGFDL\b)/i
            )
          ) {
            tag 'copyright-should-refer-to-common-license-file-for-gfdl';
        }elsif (
            check_names_texts(
qr/\b(?:LGPL|gnu[-_](?:lesser|library)[-_]general[-_]public[-_]license)\b/i,
qr/GNU (?:Lesser|Library) General Public License|(?-i:\bLGPL\b)/i
            )
          ) {
            tag 'copyright-should-refer-to-common-license-file-for-lgpl';
        }elsif (
            check_names_texts(
                qr/\b(?:GPL|gnu[-_]general[-_]public[-_]license)\b/i,
                qr/GNU General Public License|(?-i:\bGPL\b)/i
            )
          ) {
            tag 'copyright-should-refer-to-common-license-file-for-gpl';
            $gpl = 1;
        }elsif (
            check_names_texts(
                qr/\bapache[-_]2/i,
                qr/\bApache License\s*,?\s*Version 2|\b(?-i:Apache)-2/i
            )
          ) {
            tag 'copyright-should-refer-to-common-license-file-for-apache-2';
        }
    }

    if (
        check_names_texts(
            qr/\b(?:perl|artistic)\b/,
            sub {
                /(?:under )?(?:the )?(?:same )?(?:terms )?as Perl itself\b/i
                  &&!m,usr/share/common-licenses/,;
            })
      ) {
        tag 'copyright-file-lacks-pointer-to-perl-license';
    }

    # Checks for various packaging helper boilerplate.

    if (
           m,\<fill in (?:http/)?ftp site\>,o
        or m,\<Must follow here\>,o
        or m,\<Put the license of the package here,o
        or m,\<put author[\'\(]s\)? name and email here\>,o
        or m,\<Copyright \(C\) YYYY Name OfAuthor\>,o
        or m,Upstream Author\(s\),o
        or m,\<years\>,o
        or m,\<special license\>,o
        or m,\<Put the license of the package here indented by 1 space\>,o
        or m,\Q<This follows the format of Description: lines\E \s*
             \Qin control file>\E,ox
        or m,\<Including paragraphs\>,o
        or m,\<likewise for another author\>,o
      ) {
        tag 'helper-templates-in-copyright';
    }

    if (m/This copyright info was automatically extracted/o) {
        tag 'copyright-contains-automatically-extracted-boilerplate';
    }

    if (m,url://,o) {
        tag 'copyright-has-url-from-dh_make-boilerplate';
    }

    if (   index($_, DH_MAKE_TODO_BOILERPLATE_1) != -1
        or index($_, DH_MAKE_TODO_BOILERPLATE_2) != -1) {
        tag 'copyright-contains-dh_make-todo-boilerplate';
    }

    if (m,The\s+Debian\s+packaging\s+is\s+\(C\)\s+\d+,io) {
        tag 'copyright-with-old-dh-make-debian-copyright';
    }

    # Other flaws in the copyright phrasing or contents.
    if ($found && !$linked) {
        tag 'copyright-without-copyright-notice'
          unless /(?:Copyright|Copr\.|\302\251)(?:.*|[\(C\):\s]+)\b\d{4}\b
               |\bpublic(?:\s+|-)domain\b/xi;
    }

    check_spelling($_, $group->info->spelling_exceptions,
        $SPELLING_ERROR_IN_COPYRIGHT);

    # Now, check for linking against libssl if the package is covered
    # by the GPL.  (This check was requested by ftp-master.)  First,
    # see if the package is under the GPL alone and try to exclude
    # packages with a mix of GPL and LGPL or Artistic licensing or
    # with an exception or exemption.
    if ($gpl || m,/usr/share/common-licenses/GPL,) {
        unless (m,exception|exemption|/usr/share/common-licenses/(?!GPL)\S,){
            my @depends;
            if (my $field = $info->field('depends')) {
                @depends = split(/\s*,\s*/, $field);
            }
            if (my $field = $info->field('pre-depends')) {
                push(@depends, split(/\s*,\s*/, $field));
            }
            if (any { /^libssl[0-9.]+(?:\s|\z)/ && !/\|/ } @depends) {
                tag 'possible-gpl-code-linked-with-openssl';
            }
        }
    }

    return;
} # </run>

# -----------------------------------

# Returns true if the package whose information is in $info depends $package
# or if $package is essential.
sub depends_on {
    my ($info, $proc, $package) = @_;
    my ($strong, $arch);
    return 1 if $KNOWN_ESSENTIAL->known($package);
    $strong = $info->relation('strong');
    return 1 if $strong->implies($package);
    $arch = $proc->pkg_arch;
    return 1 if $arch ne 'all' and $strong->implies("${package}:${arch}");
    return 0;
}

# Checks cross pkg links for /usr/share/doc/$pkg links
sub check_cross_link {
    my ($group, $fpkg) = @_;
    my $src = $group->get_source_processable;
    if ($src) {
        # source package is available; check it's list of binary
        return if defined $src->info->binary_package_type($fpkg);
        tag 'usr-share-doc-symlink-to-foreign-package', $fpkg;
    } else {
        # The source package is not available, but the binary could
        # be present anyway;  If they are in the same group, they claim
        # to have the same source (and source version)
        foreach my $proc ($group->get_processables('binary')){
            return if($proc->pkg_name eq $fpkg);
        }
        # It was not, but since the source package was not present, we cannot
        # tell if it is foreign or not at this point.
        #<<< No perltidy - tag name too long
        tag 'cannot-check-whether-usr-share-doc-symlink-points-to-foreign-package';
        #>>>
    }
    return;
}

# Checks the name and text of every license in the file against given name and
# text check coderefs, if the file is in the new format, if the file is in the
# old format only runs the text coderef against the whole file.
sub check_names_texts {
    my ($name_check, $text_check) = @_;

    my $make_check = sub {
        my $action = $_[0];

        if ((ref($action) || '') eq 'Regexp') {
            return sub { ${$_[0]} =~ $action };
        }
        return sub {
            $_ = ${$_[0]};
            return $action->();
        };
    };
    $text_check = $make_check->($text_check);

    my $file = \$_;
    local $@;
    local $_;
    eval {
        foreach my $paragraph (read_dpkg_control($file)) {
            next unless exists $paragraph->{license};

            my ($license_name, $license_text)
              = $paragraph->{license} =~ /^\s*([^\r\n]+)\r?\n(.*)\z/s;

            next if ($license_text||'') =~ /^[\s\r\n]*\z/;

            die 'MATCH'
              if $license_name =~ $name_check
              && $text_check->(\$license_text);
        }
    };
    if ($@)
    { # match or parse error: copyright not in new format, just check text
        return 1 if $@ =~ /^MATCH/;

        return $text_check->($file);
    }

    return; # did not match anything
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
