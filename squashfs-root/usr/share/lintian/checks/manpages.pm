# manpages -- lintian check script -*- perl -*-

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

package Lintian::manpages;
use strict;
use warnings;
use autodie;

use constant LINTIAN_COVERAGE => ($ENV{'LINTIAN_COVERAGE'}?1:0);

use File::Basename;
use List::MoreUtils qw(any none);
use Text::ParseWords ();

use Lintian::Check qw(check_spelling spelling_tag_emitter);
use Lintian::Tags qw(tag);
use Lintian::Util qw(clean_env do_fork drain_pipe internal_error open_gz);

sub run {
    my (undef, undef, $info, $proc, $group) = @_;
    my $ginfo = $group->info;
    my (%binary, %link, %manpage, @running_man, @running_lexgrog);

    # Read package contents...
    foreach my $file ($info->sorted_index) {
        my $file_info = $file->file_info;
        my $link = $file->link || '';
        my ($fname, $path, undef) = fileparse($file);

        # Binary that wants a manual page?
        #
        # It's tempting to check the section of the man page depending on the
        # location of the binary, but there are too many mismatches between
        # bin/sbin and 1/8 that it's not clear it's the right thing to do.
        if (
            ($file->is_symlink or $file->is_file)
            and (  ($path eq 'bin/')
                or ($path eq 'sbin/')
                or ($path eq 'usr/bin/')
                or ($path eq 'usr/bin/X11/')
                or ($path eq 'usr/bin/mh/')
                or ($path eq 'usr/sbin/')
                or ($path eq 'usr/games/'))
          ) {

            my $bin = $fname;
            $binary{$bin} = $file;
            $link{$bin} = $link if $link;

            next;
        }

        if (($path =~ m,usr/share/man/$,) and ($fname ne '')) {
            tag 'manpage-in-wrong-directory', $file;
            next;
        }

        # manual page?
        next
          unless ($file->is_symlink or $file->is_file)
          and $path =~ m,^usr/share/man(/\S+),o;
        my $t = $1;

        if ($file =~ m{/_build_} or $file =~ m{_tmp_buildd}) {
            tag 'manpage-named-after-build-path', $file;
        }

        if ($file =~ m,/README\.,) {
            tag 'manpage-has-overly-generic-name', $file;
        }

        if (not $t =~ m,^.*man(\d)/$,o) {
            tag 'manpage-in-wrong-directory', $file;
            next;
        }
        my $section = $1;
        my $lang = '';
        $lang = $1 if $t =~ m,^/([^/]+)/man\d/$,o;

        # The country should not be part of the man page locale
        # directory unless it's one of the known cases where the
        # language is significantly different between countries.
        if ($lang =~ /_/ && $lang !~ /^(?:pt_BR|zh_[A-Z][A-Z])$/) {
            tag 'manpage-locale-dir-country-specific', $file;
        }

        my @pieces = split(/\./, $fname);
        my $ext = pop @pieces;
        if ($ext ne 'gz') {
            push @pieces, $ext;
            tag 'manpage-not-compressed', $file;
        } elsif ($file->is_file) { # so it's .gz... files first; links later
            if ($file_info !~ m/gzip compressed data/o) {
                tag 'manpage-not-compressed-with-gzip', $file;
            } elsif ($file_info !~ m/max compression/o) {
                tag 'manpage-not-compressed-with-max-compression', $file;
            }
        }
        my $fn_section = pop @pieces;
        my $section_num = $fn_section;
        if (scalar @pieces && $section_num =~ s/^(\d).*$/$1/) {
            my $bin = join('.', @pieces);
            $manpage{$bin} = [] unless $manpage{$bin};
            push @{$manpage{$bin}}, { file => $file, lang => $lang };

            # number of directory and manpage extension equal?
            if ($section_num != $section) {
                tag 'manpage-in-wrong-directory', $file;
            }
        } else {
            tag 'manpage-has-wrong-extension', $file;
        }

        # check symbolic links to other manual pages
        if ($file->is_symlink) {
            if ($link =~ m,(^|/)undocumented,o) {
                # undocumented link in /usr/share/man -- possibilities
                #    undocumented... (if in the appropriate section)
                #    ../man?/undocumented...
                #    ../../man/man?/undocumented...
                #    ../../../share/man/man?/undocumented...
                #    ../../../../usr/share/man/man?/undocumented...
                if ((
                    #<<< no perl tidy for now
                            $link =~ m,^undocumented\.([237])\.gz,o
                        and $path =~ m,^usr/share/man/man$1,)
                    or $link =~ m,^\.\./man[237]/undocumented\.[237]\.gz$,o
                    or $link =~ m,^\.\./\.\./man/man[237]/undocumented\.[237]\.gz$,o
                    or $link =~ m,^\.\./\.\./\.\./share/man/man[237]/undocumented\.[237]\.gz$,o
                    or $link =~ m,^\.\./\.\./\.\./\.\./usr/share/man/man[237]/undocumented\.[237]\.gz$,o
                    #>>>
                  ) {
                    tag 'link-to-undocumented-manpage', $file;
                } else {
                    tag 'bad-link-to-undocumented-manpage', $file;
                }
            }
        } else { # not a symlink
            my $fs_path = $file->fs_path;
            my $fd;
            if ($file_info =~ m/gzip compressed/) {
                $fd = $file->open_gz;
            } else {
                $fd = $file->open;
            }
            my @manfile = <$fd>;
            close $fd;
            # Is it a .so link?
            if ($file->size < 256) {
                my ($i, $first) = (0, '');
                do {
                    $first = $manfile[$i++] || '';
                } while ($first =~ /^\.\\"/ && $manfile[$i]); #");

                unless ($first) {
                    tag 'empty-manual-page', $file;
                    next;
                } elsif ($first =~ /^\.so\s+(.+)?$/) {
                    my $dest = $1;
                    if ($dest =~ m,^([^/]+)/(.+)$,) {
                        my ($manxorlang, $rest) = ($1, $2);
                        if ($manxorlang !~ /^man\d+$/) {
                            # then it's likely a language subdir, so let's run
                            # the other component through the same check
                            if ($rest =~ m,^([^/]+)/(.+)$,) {
                                my (undef, $rest) = ($1, $2);
                                if ($rest !~ m,^[^/]+\.\d(?:\S+)?(?:\.gz)?$,) {
                                    tag 'bad-so-link-within-manual-page',$file;
                                }
                            } else {
                                tag 'bad-so-link-within-manual-page', $file;
                            }
                        }
                    } else {
                        tag 'bad-so-link-within-manual-page', $file;
                    }
                    next;
                }
            }

            # If it's not a .so link, use lexgrog to find out if the
            # man page parses correctly and make sure the short
            # description is reasonable.
            #
            # This check is currently not applied to pages in
            # language-specific hierarchies, because those pages are
            # not currently scanned by mandb (bug #29448), and because
            # lexgrog can't handle pages in all languages at the
            # moment, leading to huge numbers of false negatives. When
            # man-db is fixed, this limitation should be removed.
            if ($path =~ m,/man/man\d/,) {
                my $pid = open(my $lexgrog_fd, '-|');
                if ($pid == 0) {
                    clean_env;
                    open(STDERR, '>&', \*STDOUT);
                    exec('lexgrog', $fs_path)
                      or internal_error("exec lexgrog failed: $!");
                }
                if (@running_lexgrog > 2) {
                    process_lexgrog_output(\@running_lexgrog);
                }
                # lexgrog can have a high start up time, so revisit
                # this later.
                push(@running_lexgrog, [$file, $lexgrog_fd, $pid]);
            }

            # If it's not a .so link, run it through 'man' to check for errors.
            # If it is in a directory with the standard man layout, cd to the
            # parent directory before running man so that .so directives are
            # processed properly.  (Yes, there are man pages that include other
            # pages with .so but aren't simple links; rbash, for instance.)
            my @cmd = qw(man --warnings -E UTF-8 -l -Tutf8 -Z);
            my $dir;
            if ($fs_path =~ m,^(.*)/(man\d/.*)$,) {
                $dir = $1;
                push @cmd, $2;
            } else {
                push(@cmd, $fs_path);
            }
            my ($read, $write);
            pipe($read, $write);
            my $pid = do_fork();
            if ($pid == 0) {
                clean_env;
                close STDOUT;
                close $read;
                open(STDOUT, '>', '/dev/null');
                open(STDERR, '>&', $write);
                if ($dir) {
                    chdir($dir);
                }
                $ENV{MANROFFSEQ} = '';
                $ENV{MANWIDTH} = 80;
                exec { $cmd[0] } @cmd
                  or internal_error("cannot run man -E UTF-8 -l: $!");
            } else {
                # parent - close write end
                close $write;
            }

            if (@running_man > 3) {
                process_man_output(\@running_man);
            }
            # man can have a high start up time, so revisit this
            # later.
            push(@running_man, [$file, $read, $pid, $lang, \@manfile]);

            # Now we search through the whole man page for some common errors
            my $lc = 0;
            my $stag_emitter
              = spelling_tag_emitter('spelling-error-in-manpage', $file);
            foreach my $line (@manfile) {
                $lc++;
                chomp $line;
                next if $line =~ /^\.\\\"/o; # comments .\"
                if ($line =~ /^\.TH\s/) { # header
                    my (undef, undef, $th_section, undef)
                      = Text::ParseWords::parse_line('\s+', 0, $line);
                    if ($th_section && (lc($fn_section) ne lc($th_section))) {
                        tag 'manpage-section-mismatch',
                          "$file:$lc $fn_section != $th_section";
                    }
                }
                if (($line =~ m,(/usr/(dict|doc|etc|info|man|adm|preserve)/),o)
                    || ($line =~ m,(/var/(adm|catman|named|nis|preserve)/),o)){
                    # FSSTND dirs in man pages
                    # regexes taken from checks/files
                    tag 'FSSTND-dir-in-manual-page', "$file:$lc $1";
                }
                if ($line eq '.SH "POD ERRORS"') {
                    tag 'manpage-has-errors-from-pod2man', "$file:$lc";
                }
                # Check for spelling errors if the manpage is English
                check_spelling($line, $ginfo->spelling_exceptions,
                    $stag_emitter, 0)
                  if ($path =~ m,/man/man\d/,);
            }
        }
    }
    # If we have any running sub processes, wait for them here.
    process_lexgrog_output(\@running_lexgrog) if @running_lexgrog;
    process_man_output(\@running_man) if @running_man;

    # Check our dependencies:
    foreach my $depproc (@{ $ginfo->direct_dependencies($proc) }) {
        # Find the manpages in our related dependencies
        my $depinfo = $depproc->info;
        foreach my $file ($depinfo->sorted_index){
            my ($fname, $path, undef) = fileparse($file, qr,\..+$,o);
            my $lang = '';
            next
              unless ($file->is_file or $file->is_symlink)
              and $path =~ m,^usr/share/man/\S+,o;
            next unless ($path =~ m,man\d/$,o);
            $manpage{$fname} = [] unless exists $manpage{$fname};
            $lang = $1 if $path =~ m,/([^/]+)/man\d/$,o;
            $lang = '' if $lang eq 'man';
            push @{$manpage{$fname}}, {file => $file, lang => $lang};
        }
    }

    for my $f (sort keys %binary) {
        if (exists $manpage{$f}) {
            if (none { $_->{lang} eq '' } @{$manpage{$f}}) {
                tag 'binary-without-english-manpage', "$binary{$f}";
            }
        } else {
            tag 'binary-without-manpage', "$binary{$f}";
        }
    }

    return;
}

sub process_lexgrog_output {
    my ($running) = @_;
    for my $lex_proc (@{$running}) {
        my ($file, $lexgrog_fd, undef) = @{$lex_proc};
        my $desc = <$lexgrog_fd>;
        $desc =~ s/^[^:]+: \"(.*)\"$/$1/;
        if ($desc =~ /(\S+)\s+-\s+manual page for \1/i) {
            tag 'manpage-has-useless-whatis-entry', $file;
        } elsif ($desc =~ /\S+\s+-\s+programs? to do something/i) {
            tag 'manpage-is-dh_make-template', $file;
        }
        drain_pipe($lexgrog_fd);
        eval {close($lexgrog_fd);};
        if (my $err = $@) {
            # Problem closing the pipe?
            internal_error("close pipe: $err") if $err->errno;
            # No, then lexgrog returned with a non-zero exit code.
            tag 'manpage-has-bad-whatis-entry', $file;
        }
    }
    @{$running} = ();
    return;
}

sub process_man_output {
    my ($running) = @_;
    for my $man_proc (@{$running}) {
        my ($file, $read, $pid, $lang, $contents) = @{$man_proc};
        while (<$read>) {
            # Devel::Cover causes some annoying deep recursion
            # warnings and sometimes in our child process.
            # Filter them out, but only during coverage.
            next if LINTIAN_COVERAGE and m{
                    \A Deep [ ] recursion [ ] on [ ] subroutine [ ]
                    "[^"]+" [ ] at [ ] .*B/Deparse.pm [ ] line [ ]
                   \d+}xsm;
            # ignore progress information from man
            next if /^Reformatting/;
            next if /^\s*$/;
            # ignore errors from gzip, will be dealt with at other places
            next if /^(?:man|gzip)/;
            # ignore wrapping failures for Asian man pages (groff problem)
            if ($lang =~ /^(?:ja|ko|zh)/) {
                next if /warning \[.*\]: cannot adjust line/;
                next if /warning \[.*\]: can\'t break line/;
            }
            # ignore wrapping failures if they contain URLs (.UE is an
            # extension for marking the end of a URL).
            next
              if/:(\d+): warning \[.*\]: (?:can\'t break|cannot adjust) line/
              and ($contents->[$1 - 1] =~ m,(?:https?|ftp|file)://.+,i
                or $contents->[$1 - 1] =~ m,^\s*\.\s*UE\b,);
            # ignore common undefined macros from pod2man << Perl 5.10
            next if /warning: (?:macro )?\`(?:Tr|IX)\' not defined/;
            chomp;
            s/^[^:]+://o;
            tag 'manpage-has-errors-from-man', $file, $_;
            last;
        }
        close($read);
        # reap man process
        waitpid($pid, 0);
    }
    @{$running} = ();
    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
