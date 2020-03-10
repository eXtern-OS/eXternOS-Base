# menus -- lintian check script -*- perl -*-

# somewhat of a misnomer -- it doesn't only check menus

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

package Lintian::menus;
use strict;
use warnings;
use autodie;

use Lintian::Check
  qw(check_spelling check_spelling_picky $known_shells_regex spelling_tag_emitter);
use Lintian::Data;
use Lintian::Tags qw(tag);
use Lintian::Util qw(file_is_encoded_in_non_utf8 strip);

# Supported documentation formats for doc-base files.
our %known_doc_base_formats = map { $_ => 1 }
  ('html', 'text', 'pdf', 'postscript', 'info', 'dvi', 'debiandoc-sgml');

# Known fields for doc-base files.  The value is 1 for required fields and 0
# for optional fields.
our %KNOWN_DOCBASE_MAIN_FIELDS = (
    'document' => 1,
    'title'    => 1,
    'section'  => 1,
    'abstract' => 0,
    'author'   => 0
);
our %KNOWN_DOCBASE_FORMAT_FIELDS = (
    'format'  => 1,
    'files'   => 1,
    'index'   => 0
);

our $SECTIONS = Lintian::Data->new('doc-base/sections');

sub run {
    my ($pkg, undef, $info, undef, $group) = @_;
    my (%all_files, %all_links);

    my %preinst;
    my %postinst;
    my %prerm;
    my %postrm;

    my $menu_file;
    my $menumethod_file;
    my $anymenu_file;
    my $documentation;

    check_script($pkg, scalar $info->control_index('preinst'), \%preinst);
    check_script($pkg, scalar $info->control_index('postinst'), \%postinst);
    check_script($pkg, scalar $info->control_index('prerm'), \%prerm);
    check_script($pkg, scalar $info->control_index('postrm'), \%postrm);

    # read package contents
    for my $file ($info->sorted_index) {

        add_file_link_info($info, $file->name, \%all_files, \%all_links);
        my $operm = $file->operm;

        if ($file->is_file) { # file checks
            # menu file?
            if ($file =~ m,^usr/(lib|share)/menu/\S,o) { # correct permissions?
                if ($operm & 0111) {
                    tag 'executable-menu-file',
                      sprintf('%s %04o', $file, $operm);
                }

                next if $file =~ m,^usr/(?:lib|share)/menu/README$,;

                if ($file =~ m,^usr/lib/,o) {
                    tag 'menu-file-in-usr-lib', $file;
                }

                $menu_file = $file;

                if (    $file =~ m,usr/(?:lib|share)/menu/menu$,o
                    and $pkg ne 'menu') {
                    tag 'bad-menu-file-name', $file;
                }
            }
            #menu-methods file?
            elsif ($file =~ m,^etc/menu-methods/\S,o) {
                #TODO: we should test if the menu-methods file
                # is made executable in the postinst as recommended by
                # the menu manual

                my $menumethod_includes_menu_h = 0;
                $menumethod_file = $file;

                if ($file->is_open_ok) {
                    my $fd = $file->open;
                    while (<$fd>) {
                        chomp;
                        if (m,^!include menu.h,o) {
                            $menumethod_includes_menu_h = 1;
                            last;
                        }
                    }
                    close($fd);
                }
                tag 'menu-method-should-include-menu-h', $file
                  unless $menumethod_includes_menu_h
                  or $pkg eq 'menu';
            }
            # package doc dir?
            elsif (
                $file =~ m{ \A usr/share/doc/(?:[^/]+/)?
                                 (.+\.(?:html|pdf))(?:\.gz)?
                          \Z}xsmo
              ) {
                my $name = $1;
                unless ($name =~ m/^changelog\.html$/o
                    or $name =~ m/^README[.-]/o
                    or $name =~ m|examples|o) {
                    $documentation = 1;
                }
            }
        }
    }

    # prerm scripts should not call update-menus
    if ($prerm{'calls-updatemenus'}) {
        tag 'prerm-calls-updatemenus';
    }

    # postrm scripts should not call install-docs
    if ($postrm{'calls-installdocs'} or $postrm{'calls-installdocs-r'}) {
        tag 'postrm-calls-installdocs';
    }

    # preinst scripts should not call either update-menus nor installdocs
    if ($preinst{'calls-updatemenus'}) {
        tag 'preinst-calls-updatemenus';
    }

    if ($preinst{'calls-installdocs'}) {
        tag 'preinst-calls-installdocs';
    }

    $anymenu_file = $menu_file || $menumethod_file;

    # No one needs to call install-docs any more; triggers now handles that.
    if ($postinst{'calls-installdocs'} or $postinst{'calls-installdocs-r'}) {
        tag 'postinst-has-useless-call-to-install-docs';
    }
    if ($prerm{'calls-installdocs'} or $prerm{'calls-installdocs-r'}) {
        tag 'prerm-has-useless-call-to-install-docs';
    }

    # check consistency
    # docbase file?
    if (my $db_dir = $info->index_resolved_path('usr/share/doc-base/')) {
        for my $dbpath ($db_dir->children) {
            next if not $dbpath->is_open_ok;
            if ($dbpath->resolve_path->is_executable) {
                tag 'executable-in-usr-share-docbase', $dbpath,
                  sprintf('%04o', $dbpath->operm);
                next;
            }
            check_doc_base_file($dbpath, $pkg, \%all_files,\%all_links,$group);
        }
    } elsif ($documentation) {
        if ($pkg =~ /^libghc6?-.*-doc$/) {
            # This is the library documentation for a haskell library. Haskell
            # libraries register their documentation via the ghc compiler's
            # documentation registration mechanism.  See bug #586877.
        } else {
            tag 'possible-documentation-but-no-doc-base-registration';
        }
    }

    if ($anymenu_file) {
        # postinst and postrm should not need to call update-menus
        # unless there is a menu-method file.  However, update-menus
        # currently won't enable packages that have outstanding
        # triggers, leading to an update-menus call being required for
        # at least some packages right now.  Until this bug is fixed,
        # we still require it.  See #518919 for more information.
        #
        # That bug does not require calling update-menus from postrm,
        # but debhelper apparently currently still adds that to the
        # maintainer script, so don't warn if it's done.
        if (not $postinst{'calls-updatemenus'}) {
            tag 'postinst-does-not-call-updatemenus', $anymenu_file;
        }
        if ($menumethod_file and not $postrm{'calls-updatemenus'}) {
            tag 'postrm-does-not-call-updatemenus', $menumethod_file
              unless $pkg eq 'menu';
        }
    } else {
        if ($postinst{'calls-updatemenus'}) {
            tag 'postinst-has-useless-call-to-update-menus';
        }
        if ($postrm{'calls-updatemenus'}) {
            tag 'postrm-has-useless-call-to-update-menus';
        }
    }

    return;
}

# -----------------------------------

sub check_doc_base_file {
    my ($dbpath, $pkg, $all_files, $all_links, $group) = @_;

    my $dbfile = $dbpath->basename;
    my $line = file_is_encoded_in_non_utf8($dbpath->fs_path);
    if ($line) {
        tag 'doc-base-file-uses-obsolete-national-encoding', "$dbfile:$line";
    }

    my $knownfields = \%KNOWN_DOCBASE_MAIN_FIELDS;
    my ($field, @vals);
    my %sawfields;        # local for each section of control file
    my %sawformats;       # global for control file
    $line           = 0;  # global

    my $fd = $dbpath->open;

    while (<$fd>) {
        chomp;

        # New field.  check previous field, if we have any.
        if (/^(\S+)\s*:\s*(.*)$/) {
            my (@new) = ($1, $2);
            if ($field) {
                check_doc_base_field(
                    $pkg, $dbfile, $line, $field,
                    \@vals,\%sawfields, \%sawformats, $knownfields,
                    $all_files, $all_links, $group
                );
            }
            $field = lc $new[0];
            @vals  = ($new[1]);
            $line  = $.;

            # Continuation of previously defined field.
        } elsif ($field && /^\s+\S/) {
            push(@vals, $_);

            # All tags will be reported on the last continuation line of the
            # doc-base field.
            $line  = $.;

            # Sections' separator.
        } elsif (/^(\s*)$/) {
            tag 'doc-base-file-separator-extra-whitespace', "$dbfile:$."
              if $1;
            next unless $field; # skip successive empty lines

            # Check previously defined field and section.
            check_doc_base_field(
                $pkg, $dbfile, $line, $field,
                \@vals,\%sawfields, \%sawformats, $knownfields,
                $all_files, $all_links, $group
            );
            check_doc_base_file_section($dbfile, $line + 1, \%sawfields,
                \%sawformats, $knownfields);

            # Initialize variables for new section.
            undef $field;
            undef $line;
            @vals      = ();
            %sawfields = ();

            # Each section except the first one is format section.
            $knownfields = \%KNOWN_DOCBASE_FORMAT_FIELDS;

            # Everything else is a syntax error.
        } else {
            tag 'doc-base-file-syntax-error', "$dbfile:$.";
        }
    }

    # Check the last field/section of the control file.
    if ($field) {
        check_doc_base_field(
            $pkg, $dbfile, $line, $field,
            \@vals, \%sawfields,\%sawformats, $knownfields,
            $all_files,$all_links, $group
        );
        check_doc_base_file_section($dbfile, $line, \%sawfields, \%sawformats,
            $knownfields);
    }

    # Make sure we saw at least one format.
    tag 'doc-base-file-no-format-section', "$dbfile:$." unless %sawformats;

    close($fd);

    return;
}

# Checks one field of a doc-base control file.  $vals is array ref containing
# all lines of the field.  Modifies $sawfields and $sawformats.
sub check_doc_base_field {
    my (
        $pkg, $dbfile, $line, $field,
        $vals, $sawfields, $sawformats,$knownfields,
        $all_files, $all_links, $group
    ) = @_;

    tag 'doc-base-file-unknown-field', "$dbfile:$line", $field
      unless defined $knownfields->{$field};
    tag 'doc-base-file-duplicated-field', "$dbfile:$line", $field
      if $sawfields->{$field};
    $sawfields->{$field} = 1;

    # Index/Files field.
    #
    # Check if files referenced by doc-base are included in the package.  The
    # Index field should refer to only one file without wildcards.  The Files
    # field is a whitespace-separated list of files and may contain wildcards.
    # We skip without validating wildcard patterns containing character
    # classes since otherwise we'd need to deal with wildcards inside
    # character classes and aren't there yet.
    if ($field eq 'index' or $field eq 'files') {
        my @files = map { split('\s+', $_) } @$vals;

        if ($field eq 'index' && @files > 1) {
            tag 'doc-base-index-references-multiple-files', "$dbfile:$line";
        }
        for my $file (@files) {
            next if $file eq '';
            my $realfile = delink($file, $all_links);
            # openoffice.org-dev-doc has thousands of files listed so try to
            # use the hash if possible.
            my $found;
            if ($realfile =~ /[*?]/) {
                my $regex = quotemeta($realfile);
                unless ($field eq 'index') {
                    next if $regex =~ /\[/;
                    $regex =~ s%\\\*%[^/]*%g;
                    $regex =~ s%\\\?%[^/]%g;
                    $regex .= '/?';
                }
                $found = grep { /^$regex\z/ } keys %$all_files;
            } else {
                $found = $all_files->{$realfile} || $all_files->{"$realfile/"};
            }
            unless ($found) {
                tag 'doc-base-file-references-missing-file', "$dbfile:$line",
                  $file;
            }
        }
        undef @files;

        # Format field.
    } elsif ($field eq 'format') {
        my $format = join(' ', @$vals);
        strip($format);
        $format = lc $format;
        tag 'doc-base-file-unknown-format', "$dbfile:$line", $format
          unless $known_doc_base_formats{$format};
        tag 'doc-base-file-duplicated-format', "$dbfile:$line", $format
          if $sawformats->{$format};
        $sawformats->{$format} = 1;

        # Save the current format for the later section check.
        $sawformats->{' *current* '} = $format;

        # Document field.
    } elsif ($field eq 'document') {
        $_ = join(' ', @$vals);

        tag 'doc-base-invalid-document-field', "$dbfile:$line", $_
          unless /^[a-z0-9+.-]+$/;
        tag 'doc-base-document-field-ends-in-whitespace', "$dbfile:$line"
          if /[ \t]$/;
        tag 'doc-base-document-field-not-in-first-line', "$dbfile:$line"
          unless $line == 1;

        # Title field.
    } elsif ($field eq 'title') {
        if (@$vals) {
            my $stag_emitter
              = spelling_tag_emitter('spelling-error-in-doc-base-title-field',
                "${dbfile}:${line}");
            check_spelling(
                join(' ', @$vals),
                $group->info->spelling_exceptions,
                $stag_emitter
            );
            check_spelling_picky(join(' ', @$vals), $stag_emitter);
        }

        # Section field.
    } elsif ($field eq 'section') {
        $_ = join(' ', @$vals);
        unless ($SECTIONS->known($_)) {
            if (m,^App(?:lication)?s/(.+)$, and $SECTIONS->known($1)) {
                tag 'doc-base-uses-applications-section', "$dbfile:$line", $_;
            } elsif (m,^(.+)/(?:[^/]+)$, and $SECTIONS->known($1)) {
                # allows creating a new subsection to a known section
            } else {
                tag 'doc-base-unknown-section', "$dbfile:$line", $_;
            }
        }

        # Abstract field.
    } elsif ($field eq 'abstract') {
        # The three following variables are used for checking if the field is
        # correctly phrased.  We detect if each line (except for the first
        # line and lines containing single dot) of the field starts with the
        # same number of spaces, not followed by the same non-space character,
        # and the number of spaces is > 1.
        #
        # We try to match fields like this:
        #  ||Abstract: The Boost web site provides free peer-reviewed portable
        #  ||  C++ source libraries.  The emphasis is on libraries which work
        #  ||  well with the C++ Standard Library.  One goal is to establish
        #
        # but not like this:
        #  ||Abstract:  This is "Ding"
        #  ||  * a dictionary lookup program for Unix,
        #  ||  * DIctionary Nice Grep,
        my $leadsp;            # string with leading spaces from second line
        my $charafter;         # first non-whitespace char of second line
        my $leadsp_ok = 1;     # are spaces OK?

        # Intentionally skipping the first line.
        for my $idx (1 .. $#{$vals}) {
            $_ = $vals->[$idx];
            if (/manage\s+online\s+manuals\s.*Debian/o) {
                tag 'doc-base-abstract-field-is-template', "$dbfile:$line"
                  unless $pkg eq 'doc-base';
            } elsif (/^(\s+)\.(\s*)$/o and ($1 ne ' ' or $2)) {
                tag 'doc-base-abstract-field-separator-extra-whitespace',
                  "$dbfile:" . ($line - $#{$vals} + $idx);
            } elsif (!$leadsp && /^(\s+)(\S)/o) {
                # The regexp should always match.
                ($leadsp, $charafter) = ($1, $2);
                $leadsp_ok = $leadsp eq ' ';
            } elsif (!$leadsp_ok && /^(\s+)(\S)/o) {
                # The regexp should always match.
                undef $charafter if $charafter && $charafter ne $2;
                $leadsp_ok = 1
                  if ($1 ne $leadsp) || ($1 eq $leadsp && $charafter);
            }
        }
        unless ($leadsp_ok) {
            tag 'doc-base-abstract-might-contain-extra-leading-whitespace',
              "$dbfile:$line";
        }

        # Check spelling.
        if (@$vals) {
            my $stag_emitter
              = spelling_tag_emitter(
                'spelling-error-in-doc-base-abstract-field',
                "${dbfile}:${line}");
            check_spelling(
                join(' ', @$vals),
                $group->info->spelling_exceptions,
                $stag_emitter
            );
            check_spelling_picky(join(' ', @$vals), $stag_emitter);
        }
    }

    return;
}

# Checks the section of the doc-base control file.  Tries to find required
# fields missing in the section.
sub check_doc_base_file_section {
    my ($dbfile, $line, $sawfields, $sawformats, $knownfields) = @_;

    tag 'doc-base-file-no-format', "$dbfile:$line"
      if ((defined $sawfields->{'files'} || defined $sawfields->{'index'})
        && !(defined $sawfields->{'format'}));

    # The current format is set by check_doc_base_field.
    if ($sawfields->{'format'}) {
        my $format =  $sawformats->{' *current* '};
        tag 'doc-base-file-no-index', "$dbfile:$line"
          if ( $format
            && ($format eq 'html' || $format eq 'info')
            && !$sawfields->{'index'});
    }
    for my $field (sort keys %$knownfields) {
        tag 'doc-base-file-lacks-required-field', "$dbfile:$line", $field
          if ($knownfields->{$field} == 1 && !$sawfields->{$field});
    }

    return;
}

# Add file and link to $all_files and $all_links.  Note that both files and
# links have to include a leading /.
sub add_file_link_info {
    my ($info, $file, $all_files, $all_links) = @_;
    my $link = $info->index($file)->link;
    my $ishard = $info->index($file)->is_hardlink;

    $file = '/' . $file if (not $file =~ m%^/%); # make file absolute
    $file =~ s%/+%/%g;                           # remove duplicated `/'
    $all_files->{$file} = 1;

    if (defined $link) {
        $link = './' . $link if $link !~ m,^/,;
        if ($ishard) {
            $link =~ s,^\./,/,;
        } elsif (not $link =~ m,^/,) {            # not absolute link
            $link
              = '/' . $link;                  # make sure link starts with '/'
            $link =~ s,/+\./+,/,g;                # remove all /./ parts
            my $dcount = 1;
            while ($link =~ s,^/+\.\./+,/,) {     #\ count & remove
                $dcount++;                         #/ any leading /../ parts
            }
            my $f = $file;
            while ($dcount--) {                   #\ remove last $dcount
                $f =~ s,/[^/]*$,,;                #/ path components from $file
            }
            $link
              = $f. $link;                   # now we should have absolute link
        }
        $all_links->{$file} = $link unless ($link eq $file);
    }

    return;
}

# Dereference all symlinks in file.
sub delink {
    my ($file, $all_links) = @_;

    $file =~ s%/+%/%g;                            # remove duplicated '/'
    return $file unless %$all_links;              # package doesn't symlinks

    my $p1 = '';
    my $p2 = $file;
    my %used_links;

    # In the loop below we split $file into two parts on each '/' until
    # there's no remaining slashes.  We try substituting the first part with
    # corresponding symlink and if it succeeds, we start the procedure from
    # beginning.
    #
    # Example:
    #    Let $all_links{"/a/b"} == "/d", and $file == "/a/b/c"
    #    Then 0) $p1 == "",     $p2 == "/a/b/c"
    #         1) $p1 == "/a",   $p2 == "/b/c"
    #         2) $p1 == "/a/b", $p2 == "/c"      ; substitute "/d" for "/a/b"
    #         3) $p1 == "",     $p2 == "/d/c"
    #         4) $p1 == "/d",   $p2 == "/c"
    #         5) $p1 == "/d/c", $p2 == ""
    #
    # Note that the algorithm supposes, that
    #    i) $all_links{$X} != $X for each $X
    #   ii) both keys and values of %all_links start with '/'

    while (($p2 =~ s%^(/[^/]*)%%g) > 0) {
        $p1 .= $1;
        if (defined $all_links->{$p1}) {
            return '!!! SYMLINK LOOP !!!' if defined $used_links{$p1};
            $p2 = $all_links->{$p1} . $p2;
            $p1 = '';
            $used_links{$p1} = 1;
        }
    }

    # After the loop $p2 should be empty and $p1 should contain the target
    # file.  In some rare cases when $file contains no slashes, $p1 will be
    # empty and $p2 will contain the result (which will be equal to $file).
    return $p1 ne '' ? $p1 : $p2;
}

sub check_script {
    my ($pkg, $spath, $pres) = @_;
    my ($no_check_menu, $no_check_installdocs, $interp);

    # control files are regular files and not symlinks, pipes etc.
    return if not $spath or $spath->is_symlink or not $spath->is_open_ok;

    my $fd = $spath->open;
    $interp = <$fd>;
    $interp = '' unless defined $interp;
    if ($interp =~ m,^\#\!\s*/bin/$known_shells_regex,) {
        $interp = 'sh';
    } elsif ($interp =~ m,^\#\!\s*/usr/bin/perl,) {
        $interp = 'perl';
    } else {
        if ($interp =~ m,^\#\!\s*(.+),) {
            $interp = $1;
        } else { # hmm, doesn't seem to start with #!
            # is it a binary? look for ELF header
            if ($interp =~ m/^\177ELF/) {
                return; # nothing to do here
            }
            $interp = 'unknown';
        }
    }

    while (<$fd>) {
        # skip comments
        s/\#.*$//o;

        ##
        # update-menus will satisfy the checks that the menu file
        # installed is properly used
        ##

        # does the script check whether update-menus exists?
        if (   /-x\s+\S*update-menus/o
            or /(?:which|type)\s+update-menus/o
            or /command\s+.*?update-menus/o) {
            # yes, it does.
            $pres->{'checks-for-updatemenus'} = 1;
        }

        # does the script call update-menus?
        # TODO this regex-magic should be moved to some lib for checking
        # whether a certain word is likely called as command... --Jeroen
        if (
            m{ (?:^\s*|[;&|]\s*|(?:then|do|exec)\s+)
               (?:\/usr\/bin\/)?update-menus
               (?:\s|[;&|<>]|\Z)}xsm
          ) {
            # yes, it does.
            $pres->{'calls-updatemenus'} = 1;

            # checked first?
            if (not $pres->{'checks-for-updatemenus'} and $pkg ne 'menu') {
                #<<< no perltidy - tag name too long
                tag 'maintainer-script-does-not-check-for-existence-of-updatemenus',
                #>>>
                  "$spath:$."
                  unless $no_check_menu++;
            }
        }

        # does the script check whether install-docs exists?
        if (   s/-x\s+\S*install-docs//o
            or /(?:which|type)\s+install-docs/o
            or s/command\s+.*?install-docs//o) {
            # yes, it does.
            $pres->{'checks-for-installdocs'} = 1;
        }

        # does the script call install-docs?
        if (
            m{ (?:^\s*|[;&|]\s*|(?:then|do)\s+)
               (?:\/usr\/sbin\/)?install-docs
               (?:\s|[;&|<>]|\Z) }xsm
          ) {
            # yes, it does.  Does it remove or add a doc?
            if (m/install-docs\s+(?:-r|--remove)\s/) {
                $pres->{'calls-installdocs-r'} = 1;
            } else {
                $pres->{'calls-installdocs'} = 1;
            }
            # checked first?
            if (not $pres->{'checks-for-installdocs'}) {
                #<<< no perltidy - tag name too long
                tag 'maintainer-script-does-not-check-for-existence-of-installdocs',
                #>>>
                  $spath
                  unless $no_check_installdocs++;
            }
        }
    }
    close($fd);
    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
