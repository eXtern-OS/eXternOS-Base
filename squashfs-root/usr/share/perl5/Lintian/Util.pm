# Hey emacs! This is a -*- Perl -*- script!
# Lintian::Util -- Perl utility functions for lintian

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

package Lintian::Util;
use strict;
use warnings;
use autodie;

use Carp qw(croak);
use Cwd qw(abs_path);
use Errno qw(ENOENT);
use Exporter qw(import);
use POSIX qw(sigprocmask SIG_BLOCK SIG_UNBLOCK SIG_SETMASK);
use YAML::XS ();

use constant {
    DCTRL_DEBCONF_TEMPLATE => 1,
    DCTRL_NO_COMMENTS => 2,
};

# Force export as soon as possible, since some of the modules we load also
# depend on us and the sequencing can cause things not to be exported
# otherwise.
our (@EXPORT_OK, %EXPORT_TAGS);

BEGIN {
    %EXPORT_TAGS
      = (constants => [qw(DCTRL_DEBCONF_TEMPLATE DCTRL_NO_COMMENTS)]);

    eval { require PerlIO::gzip };
    if ($@) {
        *open_gz = \&__open_gz_ext;
    } else {
        *open_gz = \&__open_gz_pio;
    }

    @EXPORT_OK = (qw(
          visit_dpkg_paragraph
          parse_dpkg_control
          read_dpkg_control
          read_dpkg_control_utf8
          get_deb_info
          get_dsc_info
          get_file_checksum
          get_file_digest
          slurp_entire_file
          file_is_encoded_in_non_utf8
          is_string_utf8_encoded
          fail
          internal_error
          do_fork
          run_cmd
          strip
          lstrip
          rstrip
          system_env
          delete_dir
          copy_dir
          gunzip_file
          open_gz
          touch_file
          perm2oct
          check_path
          clean_env
          normalize_pkg_path
          parse_boolean
          is_ancestor_of
          locate_helper_tool
          drain_pipe
          signal_number2name
          dequote_name
          load_state_cache
          save_state_cache
          find_backlog
          pipe_tee
          untaint
          $PKGNAME_REGEX
          $PKGREPACK_REGEX
          $PKGVERSION_REGEX
          ),
        @{ $EXPORT_TAGS{constants} });
}

use Digest::MD5;
use Digest::SHA;
use Encode ();
use File::Temp qw(tempfile);
use FileHandle;
use List::Util qw(shuffle);
use Scalar::Util qw(openhandle);

use Lintian::Command qw(spawn);
use Lintian::Relation::Version qw(versions_equal versions_comparator);

=head1 NAME

Lintian::Util - Lintian utility functions

=head1 SYNOPSIS

 use Lintian::Util qw(slurp_entire_file normalize_pkg_path);
 
 my $text = slurp_entire_file('some-file');
 if ($text =~ m/regex/) {
    # ...
 }

 my $path = normalize_pkg_path('usr/bin/', '../lib/git-core/git-pull');
 if (defined $path) {
    # ...
 }
 
 my (@paragraphs);
 eval { @paragraphs = read_dpkg_control_utf8('some/debian/ctrl/file'); };
 if ($@) {
    # syntax error etc.
    die "ctrl/file: $@";
 }
 
 foreach my $para (@paragraphs) {
    my $value = $para->{'some-field'};
    if (defined $value) {
        # ...
    }
 }

=head1 DESCRIPTION

This module contains a number of utility subs that are nice to have,
but on their own did not warrant their own module.

Most subs are imported only on request.

=head2 Debian control parsers

At first glance, this module appears to contain several debian control
parsers.  In practise, there is only one real parser
(L</visit_dpkg_paragraph>) - the rest are convenience functions around
it.

If you have very large files (e.g. Packages_amd64), you almost
certainly want L</visit_dpkg_paragraph>.  Otherwise, one of the
convenience functions are probably what you are looking for.

=over 4

=item Use L</get_deb_info> when

You have a I<.deb> (or I<.udeb>) file and you want the control file
from it.

=item Use L</get_dsc_info> when

You have a I<.dsc> (or I<.changes>) file.  Alternative, it is also
useful if you have a control file and only care about the first
paragraph.

=item Use L</read_dpkg_control_utf8> or L</read_dpkg_control> when

You have a debian control file (such I<debian/control>) and you want
a number of paragraphs from it.

=item Use L</parse_dpkg_control> when

When you would have used L</read_dpkg_control_utf8>, except you have an
open filehandle rather than a file name.

=back

=head1 CONSTANTS

The following constants can be passed to the Debian control file
parser functions to alter their parsing flag.

=over 4

=item DCTRL_DEBCONF_TEMPLATE

The file should be parsed as debconf template.  These have slightly
syntax rules for whitespace in some cases.

=item DCTRL_NO_COMMENTS

The file do not allow comments.  With this flag, any comment in the
file is considered a syntax error.

=back

=head1 VARIABLES

=over 4

=item $PKGNAME_REGEX

Regular expression that matches valid package names.  The expression
is not anchored and does not enforce any "boundary" characters.

=cut

our $PKGNAME_REGEX = qr/[a-z0-9][-+\.a-z0-9]+/o;

=item $PKGREPACK_REGEX

Regular expression that matches "repacked" package names.  The expression is
not anchored and does not enforce any "boundary" characters.

=cut

our $PKGREPACK_REGEX = qr/(dfsg|debian|ds|repack)/o;

=item $PKGVERSION_REGEX

Regular expression that matches valid package versions.  The
expression is not anchored and does not enforce any "boundary"
characters.

=cut

our $PKGVERSION_REGEX = qr/
                 (?: \d+ : )?                # Optional epoch
                 [0-9][0-9A-Za-z.+:~]*       # Upstream version (with no hyphens)
                 (?: - [0-9A-Za-z.+:~]+ )*   # Optional debian revision (+ upstreams versions with hyphens)
                          /xoa;

=back

=head1 FUNCTIONS

=over 4

=item parse_dpkg_control(HANDLE[, FLAGS[, LINES]])

Reads a debian control file from HANDLE and returns a list of
paragraphs in it.  A paragraph is represented via a hashref, which
maps (lower cased) field names to their values.

FLAGS (if given) is a bitmask of the I<DCTRL_*> constants.  Please
refer to L</CONSTANTS> for the list of constants and their meaning.
The default value for FLAGS is 0.

If LINES is given, it should be a reference to an empty list.  On
return, LINES will be populated with a hashref for each paragraph (in
the same order as the returned list).  Each hashref will also have a
special key "I<START-OF-PARAGRAPH>" that gives the line number of the
first field in that paragraph.  These hashrefs will map the field name
of the given paragraph to the line number where the field name
appeared.

This is a convenience sub around L</visit_dpkg_paragraph> and can
therefore produce the same errors as it.  Please see
L</visit_dpkg_paragraph> for the finer semantics of how the
control file is parsed.

NB: parse_dpkg_control does I<not> close the handle for the caller.

=cut

sub parse_dpkg_control {
    my ($handle, $flags, $lines) = @_;
    my @result;
    my $c = sub {
        my ($para, $line) = @_;
        push @result, $para;
        push @$lines, $line if defined $lines;
    };
    visit_dpkg_paragraph($c, $handle, $flags);
    return @result;
}

=item visit_dpkg_paragraph (CODE, HANDLE[, FLAGS])

Reads a debian control file from HANDLE and passes each paragraph to
CODE.  A paragraph is represented via a hashref, which maps (lower
cased) field names to their values.

FLAGS (if given) is a bitmask of the I<DCTRL_*> constants.  Please
refer to L</CONSTANTS> for the list of constants and their meaning.
The default value for FLAGS is 0.

If the file is empty (i.e. it contains no paragraphs), the method will
contain an I<empty> list.  The deb822 contents may be inside a
I<signed> PGP message with a signature.

visit_dpkg_paragraph will require the PGP headers to be correct (if
present) and require that the entire file is covered by the signature.
However, it will I<not> validate the signature (in fact, the contents
of the PGP SIGNATURE part can be empty).  The signature should be
validated separately.

visit_dpkg_paragraph will pass paragraphs to CODE as they are
completed.  If CODE can process the paragraphs as they are seen, very
large control files can be processed without keeping all the
paragraphs in memory.

As a consequence of how the file is parsed, CODE may be passed a
number of (valid) paragraphs before parsing is stopped due to a syntax
error.

NB: visit_dpkg_paragraph does I<not> close the handle for the caller.

CODE is expected to be a callable reference (e.g. a sub) and will be
invoked as the following:

=over 4

=item CODE->(PARA, LINE_NUMBERS)

The first argument, PARA, is a hashref to the most recent paragraph
parsed.  The second argument, LINE_NUMBERS, is a hashref mapping each
of the field names to the line number where the field name appeared.
LINE_NUMBERS will also have a special key "I<START-OF-PARAGRAPH>" that
gives the line number of the first field in that paragraph.

The return value of CODE is ignored.

If the CODE invokes die (or similar) the error is propagated to the
caller.

=back


I<On syntax errors>, visit_dpkg_paragraph will call die with the
following string:

  "syntax error at line %d: %s\n"

Where %d is the line number of the issue and %s is one of:

=over

=item Duplicate field %s

The field appeared twice in the paragraph.

=item Continuation line outside a paragraph (maybe line %d should be " .")

A continuation line appears outside a paragraph - usually caused by an
unintended empty line before it.

=item Whitespace line not allowed (possibly missing a ".")

An empty continuation line was found.  This usually means that a
period is missing to denote an "empty line" in (e.g.) the long
description of a package.

=item Cannot parse line "%s"

Generic error containing the text of the line that confused the
parser.  Note that all non-printables in %s will be replaced by
underscores.

=item Comments are not allowed

A comment line appeared and FLAGS contained DCTRL_NO_COMMENTS.

=item PGP signature seen before start of signed message

A "BEGIN PGP SIGNATURE" header is seen and a "BEGIN PGP MESSAGE" has
not been seen yet.

=item Two PGP signatures (first one at line %d)

Two "BEGIN PGP SIGNATURE" headers are seen in the same file.

=item Unexpected %s header

A valid PGP header appears (e.g. "BEGIN PUBLIC KEY BLOCK").

=item Malformed PGP header

An invalid or malformed PGP header appears.

=item Expected at most one signed message (previous at line %d)

Two "BEGIN PGP MESSAGE" headers appears in the same message.

=item End of file but expected an "END PGP SIGNATURE" header

The file ended after a "BEGIN PGP SIGNATURE" header without being
followed by an "END PGP SIGNATURE".

=item PGP MESSAGE header must be first content if present

The file had content before PGP MESSAGE.

=item Data after the PGP SIGNATURE

The file had data after the PGP SIGNATURE block ended.

=item End of file before "BEGIN PGP SIGNATURE"

The file had a "BEGIN PGP MESSAGE" header, but no signature was
present.

=back

=cut

sub visit_dpkg_paragraph {
    my ($code, $CONTROL, $flags) = @_;
    $flags//=0;
    my $lines = {};
    my $section = {};
    my $open_section = 0;
    my $last_tag;
    my $debconf = $flags & DCTRL_DEBCONF_TEMPLATE;
    my $signed = 0;
    my $signature = 0;

    local $_;
    while (<$CONTROL>) {
        chomp;

        if (substr($_, 0, 1) eq '#') {
            next unless $flags & DCTRL_NO_COMMENTS;
            die "syntax error at line $.: Comments are not allowed.\n";
        }

        # empty line?
        if ($_ eq '' || (!$debconf && m/^\s*$/)) {
            if ($open_section) { # end of current section
                # pass the current section to the handler
                $code->($section, $lines);
                $section = {};
                $lines = {};
                $open_section = 0;
            }
        }
        # pgp sig? Be strict here (due to #696230)
        # According to http://tools.ietf.org/html/rfc4880#section-6.2
        # The header MUST start at the beginning of the line and MUST NOT have
        # any other text (except whitespace) after the header.
        elsif (m/^-----BEGIN PGP SIGNATURE-----[ \r\t]*$/)
        { # skip until end of signature
            my $saw_end = 0;
            if (not $signed or $signature) {
                die join(q{ },
                    "syntax error at line $.:",
                    "PGP signature seen before start of signed message\n")
                  if not $signed;
                die join(q{ },
                    "syntax error at line $.:",
                    "Two PGP signatures (first one at line $signature)\n");
            }
            $signature = $.;
            while (<$CONTROL>) {
                if (m/^-----END PGP SIGNATURE-----[ \r\t]*$/o) {
                    $saw_end = 1;
                    last;
                }
            }
            # The "at line X" may seem a little weird, but it keeps the
            # message format identical.
            die join(q{ },
                "syntax error at line $.:",
                qq{End of file but expected an "END PGP SIGNATURE" header\n})
              unless $saw_end;
        }
        # other pgp control?
        elsif (m/^-----(?:BEGIN|END) PGP/) {
            # At this point it could be a malformed PGP header or one
            # of the following valid headers (RFC4880):
            #  * BEGIN PGP MESSAGE
            #    - Possibly a signed Debian CTRL, so okay (for now)
            #  * BEGIN PGP {PUBLIC,PRIVATE} KEY BLOCK
            #    - Valid header, but not a Debian CTRL file.
            #  * BEGIN PGP MESSAGE, PART X{,/Y}
            #    - Valid, but we don't support partial messages, so
            #      bail on those.

            unless (m/^-----BEGIN PGP SIGNED MESSAGE-----[ \r\t]*$/) {
                # Not a (full) PGP MESSAGE; reject.

                my $key = qr/(?:BEGIN|END) PGP (?:PUBLIC|PRIVATE) KEY BLOCK/;
                my $msgpart = qr{BEGIN PGP MESSAGE, PART \d+(?:/\d+)?};
                my $msg
                  = qr/(?:BEGIN|END) PGP (?:(?:COMPRESSED|ENCRYPTED) )?MESSAGE/;

                if (m/^-----($key|$msgpart|$msg)-----[ \r\t]*$/o) {
                    die "syntax error at line $.: Unexpected $1 header\n";
                } else {
                    die "syntax error at line $.: Malformed PGP header\n";
                }
            } else {
                if ($signed) {
                    die join(q{ },
                        "syntax error at line $.:",
                        'Expected at most one signed message',
                        "(previous at line $signed)\n");
                }
                if ($last_tag) {
                    # NB: If you remove this, keep in mind that it may
                    # allow two paragraphs to merge.  Consider:
                    #
                    # Field-P1: some-value
                    # -----BEGIN PGP SIGNATURE-----
                    #
                    # Field-P2: another value
                    #
                    # At the time of writing: If $open_section is
                    # true, it will remain so until the empty line
                    # after the PGP header.
                    die join(q{ },
                        "syntax error at line $.:",
                        'PGP MESSAGE header must be first',
                        "content if present\n");
                }
                $signed = $.;
            }

            # skip until the next blank line
            while (<$CONTROL>) {
                last if /^\s*$/o;
            }
        }
       # did we see a signature already?  We allow all whitespace/comment lines
       # outside the signature.
        elsif ($signature) {
            # Accept empty lines after the signature.
            next if m/^\s*$/;

            # NB: If you remove this, keep in mind that it may allow
            # two paragraphs to merge.  Consider:
            #
            # Field-P1: some-value
            # -----BEGIN PGP SIGNATURE-----
            # [...]
            # -----END PGP SIGNATURE-----
            # Field-P2: another value
            #
            # At the time of writing: If $open_section is true, it
            # will remain so until the empty line after the PGP
            # header.
            die "syntax error at line $.: Data after the PGP SIGNATURE\n";
        }
        # new empty field?
        elsif (m/^([^: \t]+):\s*$/o) {
            $lines->{'START-OF-PARAGRAPH'} = $. if not $open_section;
            $open_section = 1;

            my ($tag) = (lc $1);
            $section->{$tag} = '';
            $lines->{$tag} = $.;

            $last_tag = $tag;
        }
        # new field?
        elsif (m/^([^: \t]+):\s*(.*)$/o) {
            $lines->{'START-OF-PARAGRAPH'} = $. if not $open_section;
            $open_section = 1;

            # Policy: Horizontal whitespace (spaces and tabs) may occur
            # immediately before or after the value and is ignored there.
            my ($tag,$value) = (lc $1,$2);
            rstrip($value);
            if (exists $section->{$tag}) {
                # Policy: A paragraph must not contain more than one instance
                # of a particular field name.
                die "syntax error at line $.: Duplicate field $tag.\n";
            }
            $section->{$tag} = $value;
            $lines->{$tag} = $.;

            $last_tag = $tag;
        }
        # continued field?
        elsif (m/^([ \t].*\S.*)$/o) {
            $open_section
              or die join(q{ },
                "syntax error at line $.:",
                'Continuation line outside a paragraph (maybe line',
                ($. - 1), qq{should be " .").\n});

            # Policy: Many fields' values may span several lines; in this case
            # each continuation line must start with a space or a tab.  Any
            # trailing spaces or tabs at the end of individual lines of a
            # field value are ignored.
            my $value = rstrip($1);
            $section->{$last_tag} .= "\n" . $value;
        }
        # None of the above => syntax error
        else {
            my $message = "syntax error at line $.";
            if (m/^\s+$/) {
                $message
                  .= ": Whitespace line not allowed (possibly missing a \".\").\n";
            } else {
                # Replace non-printables and non-space characters with
                # "_" - just in case.
                s/[^[:graph:][:space:]]/_/go;
                $message .= ": Cannot parse line \"$_\"\n";
            }
            die $message;
        }
    }
    # pass the last section (if not already done).
    $code->($section, $lines) if $open_section;

    # Given the API, we cannot use this check to prevent any
    # paragraphs from being emitted to the code argument, so we might
    # as well just do this last.
    if ($signed and not $signature) {
        # The "at line X" may seem a little weird, but it keeps the
        # message format identical.
        die join(q{ },
            "syntax error at line $.:",
            qq{End of file before "BEGIN PGP SIGNATURE"\n"});
    }
}

=item read_dpkg_control_utf8(FILE[, FLAGS[, LINES]])

=item read_dpkg_control(FILE[, FLAGS[, LINES]])

This is a convenience function to ease using L</parse_dpkg_control>
with paths to files (rather than open handles).  The first argument
must be the path to a FILE, which should be read as a debian control
file.  If the file is empty, an empty list is returned.

Otherwise, this behaves like:

 use autodie;
 
 open(my $fd, '<:encoding(UTF-8)', FILE); # or '<'
 my @p = parse_dpkg_control($fd, FLAGS, LINES);
 close($fd);
 return @p;

This goes without saying that may fail with any of the messages that
L</parse_dpkg_control(HANDLE[, FLAGS[, LINES]])> do.  It can also emit
autodie exceptions if open or close fails.

=cut

sub read_dpkg_control {
    my ($file, $flags, $lines) = @_;

    open(my $CONTROL, '<', $file);
    my @data = parse_dpkg_control($CONTROL, $flags, $lines);
    close($CONTROL);

    return @data;
}

sub read_dpkg_control_utf8 {
    my ($file, $flags, $lines) = @_;

    open(my $CONTROL, '<:encoding(UTF-8)', $file);
    my @data = parse_dpkg_control($CONTROL, $flags, $lines);
    close($CONTROL);

    return @data;
}

=item get_deb_info(DEBFILE)

Extracts the control file from DEBFILE and returns it as a hashref.

Basically, this is a fancy convenience for setting up an ar + tar pipe
and passing said pipe to L</parse_dpkg_control(HANDLE[, FLAGS[, LINES]])>.

DEBFILE must be an ar file containing a "control.tar.gz" member, which
in turn should contain a "control" file.  If the "control" file is
empty this will return an empty list.

Note: the control file is only expected to have a single paragraph and
thus only the first is returned (in the unlikely case that there are
more than one).

This function may fail with any of the messages that
L</parse_dpkg_control> do.  It can also emit:

 "cannot fork to unpack %s: %s\n"

=cut

{

    sub get_deb_info {
        my ($file) = @_;

        # dpkg-deb -f $file is very slow. Instead, we use ar and tar.
        my $opts = {
            fail => 'exception',
            pipe_out => FileHandle->new
        };

        spawn(
            $opts, ['dpkg-deb', '--ctrl-tarfile', $file],
            '|', ['tar', '--wildcards', '-xO', '-f', '-', '*control']);
        my @data = parse_dpkg_control($opts->{pipe_out});

        # Consume all data before exiting so that we don't kill child processes
        # with SIGPIPE.  This will normally only be an issue with malformed
        # control files.
        drain_pipe($opts->{pipe_out});
        close($opts->{pipe_out});
        $opts->{harness}->finish;
        return $data[0];
    }
}

=item get_dsc_control (DSCFILE)

Convenience function for reading dsc files.  It will read the DSCFILE
using L</read_dpkg_control(FILE[, FLAGS[, LINES]])> and then return the
first paragraph.  If the file has no paragraphs, C<undef> is returned
instead.

Note: the control file is only expected to have a single paragraph and
thus only the first is returned (in the unlikely case that there are
more than one).

This function may fail with any of the messages that
L</read_dpkg_control(FILE[, FLAGS[, LINES]])> do.

=cut

sub get_dsc_info {
    my ($file) = @_;
    my @data = read_dpkg_control($file);
    return (defined($data[0])? $data[0] : undef);
}

=item slurp_entire_file (FOH[, NOCLOSE])

Reads the contents of FOH into memory and return it as a scalar.  FOH
can be either the path to a file or an open file handle.

If it is a handle, the optional NOCLOSE parameter can be used to
prevent the sub from closing the handle.  The NOCLOSE parameter has no
effect if FOH is not a handle.

=cut

sub slurp_entire_file {
    my ($file, $noclose) = @_;
    my $fd;
    if (openhandle($file)) {
        $fd = $file;
    } else {
        open($fd, '<', $file);
    }
    local $/;
    local $_ = <$fd>;
    close($fd) unless $noclose && openhandle($file);
    return $_;
}

=item drain_pipe(FD)

Reads and discards any remaining contents from FD, which is assumed to
be a pipe.  This is mostly done to avoid having the "write"-end die
with a SIGPIPE due to a "broken pipe" (which can happen if you just
close the pipe).

May cause an exception if there are issues reading from the pipe.

Caveat: This will block until the pipe is closed from the "write"-end,
so only use it with pipes where the "write"-end will eventually close
their end by themselves (or something else will make them close it).

=cut

sub drain_pipe {
    my ($fd) = @_;
    my $buffer;

    1 while (read($fd, $buffer, 4096) > 0);

    return 1;
}

=item get_file_digest(ALGO, FILE)

Creates an ALGO digest object that is seeded with the contents of
FILE.  If you just want the hex digest, please use
L</get_file_checksum(ALGO, FILE)> instead.

ALGO can be 'md5' or shaX, where X is any number supported by
L<Digest::SHA> (e.g. 'sha256').

This sub is a convenience wrapper around Digest::{MD5,SHA}.

=cut

sub get_file_digest {
    my ($alg, $file) = @_;
    open(my $fd, '<', $file);
    my $digest;
    if ($alg eq 'md5') {
        $digest = Digest::MD5->new;
    } elsif ($alg =~ /sha(\d+)/) {
        $digest = Digest::SHA->new($1);
    }
    $digest->addfile($fd);
    close($fd);
    return $digest;
}

=item get_file_checksum(ALGO, FILE)

Returns a hexadecimal string of the message digest checksum generated
by the algorithm ALGO on FILE.

ALGO can be 'md5' or shaX, where X is any number supported by
L<Digest::SHA> (e.g. 'sha256').

This sub is a convenience wrapper around Digest::{MD5,SHA}.

=cut

sub get_file_checksum {
    my $digest = get_file_digest(@_);
    return $digest->hexdigest;
}

=item is_string_utf8_encoded(STRING)

Returns a truth value if STRING can be decoded as valid UTF-8.

=cut

{
    my $decoder = Encode::find_encoding('UTF-8');
    die('No UTF-8 decoder !?') unless ref($decoder);

    sub is_string_utf8_encoded {
        my ($str) = @_;
        if ($str =~ m,\e[-!"\$%()*+./],) {
            # ISO-2022
            return 0;
        }
        eval {$decoder->decode($str, Encode::FB_CROAK);};
        if ($@) {
            # fail
            return 0;
        }
        # pass
        return 1;
    }
}

=item file_is_encoded_in_non_utf8 (...)

Undocumented

=cut

sub file_is_encoded_in_non_utf8 {
    my ($file) = @_;

    open(my $fd, '<', $file);
    my $line = 0;
    while (<$fd>) {
        if (!is_string_utf8_encoded($_)) {
            $line = $.;
            last;
        }
    }
    close($fd);

    return $line;
}

=item do_fork()

Overrides fork to reset signal handlers etc. in the child.

=cut

sub do_fork() {
    my ($pid, $fork_error);
    my $orig_mask = POSIX::SigSet->new;
    my $fork_mask = POSIX::SigSet->new;
    $fork_mask->fillset;
    sigprocmask(SIG_BLOCK, $fork_mask, $orig_mask)
      or die("sigprocmask failed: $!\n");
    $pid = CORE::fork();
    $fork_error = $!;
    if (defined($pid) and $pid == 0) {

        for my $sig (keys(%SIG)) {
            if (ref($SIG{$sig}) eq 'CODE') {
                $SIG{$sig} = 'DEFAULT';
            }
        }
    }
    if (!sigprocmask(SIG_SETMASK, $orig_mask, undef)) {
        # The child MUST NOT use die as the caller cannot distinguish
        # the caller from the child via an exception.
        my $sigproc_error = $!;
        if (not defined($pid) or $pid != 0) {
            die("sigprocmask failed (do_fork, parent): $sigproc_error\n");
        }
        print STDERR "sigprocmask failed (do_fork, child): $sigproc_error\n";
        POSIX::_exit(255);
    }
    if (not defined($pid)) {
        $! = $fork_error;
    }
    return $pid;
}

=item system_env (CMD)

Behaves like system (CMD) except that the environment of CMD is
cleaned (as defined by L</clean_env>(1)).

=cut

sub system_env {
    my $pid = do_fork;
    if (not defined $pid) {
        return -1;
    } elsif ($pid == 0) {
        clean_env(1);
        exec @_ or die("exec of $_[0] failed: $!\n");
    } else {
        waitpid $pid, 0;
        return $?;
    }
}

=item clean_env ([CLOC])

Destructively cleans %ENV - removes all variables %ENV except a
selected few whitelisted variables.

The list of whitelisted %ENV variables are:

 PATH
 LC_ALL (*)
 TMPDIR

(*) LC_ALL is a special case as clean_env will change its value to
either "C.UTF-8" or "C" (if CLOC is given and a truth value).

=cut

sub clean_env {
    my ($cloc) = @_;
    my @whitelist = qw(PATH TMPDIR);
    my %newenv
      = map { exists $ENV{$_} ? ($_ => $ENV{$_}) : () } (@whitelist);
    %ENV = %newenv;
    $ENV{'LC_ALL'} = 'C.UTF-8';

    if ($cloc) {
        $ENV{LC_ALL} = 'C';
    }
    return;
}

=item perm2oct(PERM)

Translates PERM to an octal permission.  PERM should be a string describing
the permissions as done by I<tar t> or I<ls -l>.  That is, it should be a
string like "-rw-r--r--".

If the string does not appear to be a valid permission, it will cause
a trappable error.

Examples:

 # Good
 perm2oct('-rw-r--r--') == 0644
 perm2oct('-rwxr-xr-x') == 0755

 # Bad
 perm2oct('broken')      # too short to be recognised
 perm2oct('-resurunet')  # contains unknown permissions

=cut

sub perm2oct {
    my ($t) = @_;

    my $o = 0;

    # Types:
    #  file (-), block/character device (b & c), directory (d),
    #  hardlink (h), symlink (l), named pipe (p).
    if (
        $t !~ m/^   [-bcdhlp]                # file type
                    ([-r])([-w])([-xsS])     # user
                    ([-r])([-w])([-xsS])     # group
                    ([-r])([-w])([-xtT])     # other
               /xsmo
      ) {
        croak "$t does not appear to be a permission string";
    }

    $o += 00400 if $1 eq 'r';   # owner read
    $o += 00200 if $2 eq 'w';   # owner write
    $o += 00100 if $3 eq 'x';   # owner execute
    $o += 04000 if $3 eq 'S';   # setuid
    $o += 04100 if $3 eq 's';   # setuid + owner execute
    $o += 00040 if $4 eq 'r';   # group read
    $o += 00020 if $5 eq 'w';   # group write
    $o += 00010 if $6 eq 'x';   # group execute
    $o += 02000 if $6 eq 'S';   # setgid
    $o += 02010 if $6 eq 's';   # setgid + group execute
    $o += 00004 if $7 eq 'r';   # other read
    $o += 00002 if $8 eq 'w';   # other write
    $o += 00001 if $9 eq 'x';   # other execute
    $o += 01000 if $9 eq 'T';   # stickybit
    $o += 01001 if $9 eq 't';   # stickybit + other execute

    return $o;
}

=item run_cmd([OPTS, ]COMMAND[, ARGS...])

Executes the given C<COMMAND> with the (optional) arguments C<ARGS> and
returns the status code as one would see it from a shell script.  Shell
features cannot be used.

OPTS, if given, is a hash reference with zero or more of the following key-value pairs:

=over 4

=item chdir

The child process with chdir to the given directory before executing the command.

=item in

The STDIN of the child process will be reopened and read from the filename denoted by the value of this key.
By default, STDIN will reopened to read from /dev/null.

=item out

The STDOUT of the child process will be reopened and write to filename denoted by the value of this key.
By default, STDOUT is discarded.

=item update-env-vars

Each key/value pair defined in the hashref associated with B<update-env-vars> will be updated in the
child processes's environment.  If a value is C<undef>, then the corresponding environment variable
will be removed (if set).  Otherwise, the environment value will be set to that value.

=back

=cut

sub run_cmd {
    my (@cmd_args) = @_;
    my ($opts, $pid);
    if (ref($cmd_args[0]) eq 'HASH') {
        $opts = shift(@cmd_args);
    } else {
        $opts = {};
    }
    $pid = do_fork();
    if (not defined($pid)) {
        # failed
        die("fork failed: $!\n");
    } elsif ($pid > 0) {
        # parent
        waitpid($pid, 0);
        if ($?) {
            my $exit_code = ($? >> 8) & 0xff;
            my $signal = $? & 0x7f;
            my $cmd = join(' ', @cmd_args);
            if ($exit_code) {
                die("Command $cmd returned: $exit_code\n");
            } else {
                my $signame = signal_number2name($signal);
                die("Command $cmd received signal: $signame ($signal)\n");
            }
        }
    } else {
        # child
        if (defined(my $env = $opts->{'update-env-vars'})) {
            while (my ($k, $v) = each(%{$env})) {
                if (defined($v)) {
                    $ENV{$k} = $v;
                } else {
                    delete($ENV{$k});
                }
            }
        }
        if ($opts->{'in'}) {
            open(STDIN, '<', $opts->{'in'});
        } else {
            open(STDIN, '<', '/dev/null');
        }
        if ($opts->{'out'}) {
            open(STDOUT, '>', $opts->{'out'});
        } else {
            open(STDOUT, '>', '/dev/null');
        }
        chdir($opts->{'chdir'}) if $opts->{'chdir'};
        # Avoid shell evaluation.
        CORE::exec {$cmd_args[0]} @cmd_args
          or die("Failed to exec '$_[0]': $!\n");
    }
    return 1;
}

=item delete_dir (ARGS)

Convenient way of calling I<rm -fr ARGS>.

=cut

sub delete_dir {
    return run_cmd('rm', '-rf', '--', @_);
}

=item copy_dir (ARGS)

Convenient way of calling I<cp -a ARGS>.

=cut

sub copy_dir {
    # --reflink=auto (coreutils >= 7.5).  On FS that support it,
    # make a CoW copy of the data; otherwise fallback to a regular
    # deep copy.
    return run_cmd('cp', '-a', '--reflink=auto', '--', @_);
}

=item gunzip_file (IN, OUT)

Decompresses contents of the file IN and stores the contents in the
file OUT.  IN is I<not> removed by this call.  On error, this function
will cause a trappable error.

=cut

sub gunzip_file {
    my ($in, $out) = @_;
    run_cmd({out => $out}, 'gzip', '-dc', $in);
    return;
}

=item open_gz (FILE)

Opens a handle that reads from the GZip compressed FILE.

On failure, this sub emits a trappable error.

Note: The handle may be a pipe from an external processes.

=cut

# Preferred implementation of open_gz (used if the perlio layer
# is available)
sub __open_gz_pio {
    my ($file) = @_;
    open(my $fd, '<:gzip', $file);
    return $fd;
}

# Fallback implementation of open_gz
sub __open_gz_ext {
    my ($file) = @_;
    open(my $fd, '-|', 'gzip', '-dc', $file);
    return $fd;
}

=item touch_file(FILE)

Updates the "mtime" of FILE.  If FILE does not exist, it will be
created.

On failure, this sub will emit a trappable error.

=cut

sub touch_file {
    my ($file) = @_;

    # We use '>>' because '>' truncates the file if it has contents
    # (which `touch file` doesn't).
    open(my $fd, '>>', $file);
    # open with '>>' does not update the mtime if the file already
    # exists, so use utime to solve that.
    utime(undef, undef, $fd);
    close($fd);

    return 1;
}

=item internal_error (MSG[, ...])

Use to signal an internal error. The argument(s) will used to print a
diagnostic message to the user.

If multiple arguments are given, they will be merged into a single
string (by join (' ', @_)).  If only one argument is given it will be
stringified and used directly.

=item fail (MSG[, ...])

Deprecated alias of "internal_error".

=cut

sub fail {
    warnings::warnif('deprecated',
        '[deprecation] fail() has been replaced by internal_error()');
    goto \&internal_error;
}

sub internal_error {
    my $str = 'internal error: ';
    if (@_) {
        $str .= join ' ', @_;
    } else {
        if ($!) {
            $str .= "$!";
        } else {
            $str .= 'No context.';
        }
    }
    croak $str;
}

=item locate_helper_tool(TOOLNAME)

Given the name of a helper tool, returns the path to it.  The tool
must be available in the "helpers" subdir of one of the "lintian root"
directories used by Lintian.

The tool name should follow the same rules as check names.
Particularly, third-party checks should namespace their tools in the
same way they namespace their checks.  E.g. "python/some-helper".

If the tool cannot be found, this sub will cause a trappable error.

=cut

{
    my %_CACHE;

    sub locate_helper_tool {
        my ($toolname) = @_;
        if ($toolname =~ m{(?:\A|/) \.\. (?:\Z|/)}xsm) {
            internal_error("$toolname is not a valid tool name");
        }
        return $_CACHE{$toolname} if exists $_CACHE{$toolname};

        my $toolpath_str = $ENV{'LINTIAN_HELPER_DIRS'};
        if (defined($toolpath_str)) {
            # NB: We rely on LINTIAN_HELPER_DIRS to contain only
            # absolute paths.  Otherwise we may return relative
            # paths.
            for my $dir (split(':', $toolpath_str)) {
                my $tool = "$dir/$toolname";
                next unless -f -x $tool;
                $_CACHE{$toolname} = $tool;
                return $tool;
            }
        }
        $toolpath_str //= '<N/A>';
        internal_error(
            sprintf(
                'Cannot locate %s (search dirs: %s)',
                $toolname, $toolpath_str
            ));
    }
}

=item strip ([LINE])

Strips whitespace from the beginning and the end of LINE and returns
it.  If LINE is omitted, C<$_> will be used instead. Example

 @lines = map { strip } <$fd>;

In void context, the input argument will be modified so it can be
used as a replacement for chomp in some cases:

  while ( my $line = <$fd> ) {
    strip ($line);
    # $line no longer has any leading or trailing whitespace
  }

Otherwise, a copy of the string is returned:

  while ( my $orig = <$fd> ) {
    my $stripped = strip ($orig);
    if ($stripped ne $orig) {
        # $orig had leading or/and trailing whitespace
    }
  }

=item lstrip ([LINE])

Like L<strip|/strip ([LINE])> but only strip leading whitespace.

=item rstrip ([LINE])

Like L<strip|/strip ([LINE])> but only strip trailing whitespace.

=cut

# prototype for default to $_
sub strip (_) { ## no critic (Subroutines::RequireFinalReturn)
    if (defined wantarray) {
        # perl 5.14 s///r would have been useful here.
        my ($arg) = @_;
        $arg =~ s/^\s++//;
        # unpack 'A*' is faster than s/\s++$//
        return unpack('A*', $arg);
    }
    $_[0] =~ s/^\s++//;
    $_[0] = unpack('A*', $_[0]);
    # void context, so no return needed here.
}

# prototype for default to $_
sub lstrip (_) { ## no critic (Subroutines::RequireFinalReturn)
    if (defined wantarray) {
        # perl 5.14 s///r would have been useful here.
        my ($arg) = @_;
        $arg =~ s/^\s++//;
        return $arg;
    }
    $_[0] =~ s/^\s++//;
    # void context, so no return needed here.
}

# prototype for default to $_
sub rstrip (_) {  ## no critic (Subroutines::RequireFinalReturn)
    if (defined wantarray) {
        # unpack 'A*' is faster than s/\s++$//
        return unpack('A*', $_[0]);
    }
    $_[0] = unpack('A*', $_[0]);
    # void context, so no return needed here.
}

=item check_path (CMD)

Returns 1 if CMD can be found in PATH (i.e. $ENV{PATH}) and is
executable.  Otherwise, the function return 0.

=cut

sub check_path {
    my $command = shift;

    return 0 unless exists $ENV{PATH};
    for my $element (split ':', $ENV{PATH}) {
        next unless length $element;
        return 1 if -f "$element/$command" and -x _;
    }
    return 0;
}

=item dequote_name(STR, REMOVESLASH)

Strip an extra layer quoting in index file names and optionally
remove an initial "./" if any.

Remove initial ./ by default

=cut

sub dequote_name {
    my ($name, $slsd) = @_;
    $slsd = 1 unless defined $slsd;
    $name =~ s,^\.?/,, if $slsd;
    # Optimise for the case where the filename does not contain
    # backslashes.  It is a fairly rare to see that in practise.
    if (index($name, '\\') > -1) {
        $name =~ s/(\G|[^\\](?:\\\\)*)\\(\d{3})/"$1" . chr(oct $2)/ge;
        $name =~ s/\\\\/\\/g;
    }
    return $name;
}

=item signal_number2name(NUM)

Given a number, returns the name of the signal (without leading
"SIG").  Example:

    signal_number2name(2) eq 'INT'

=cut

{
    my @signame;

    sub signal_number2name {
        my ($number) = @_;
        if (not @signame) {
            require Config;
            # Doubt this happens for Lintian, but the code might
            # Cargo-cult-copied or copy-wasted into another project.
            # Speaking of which, thanks to
            #  http://www.ccsf.edu/Pub/Perl/perlipc/Signals.html
            defined($Config::Config{sig_name})
              or die "Signals not available\n";
            my $i = 0;
            for my $name (split(' ', $Config::Config{sig_name})) {
                $signame[$i] = $name;
                $i++;
            }
        }
        return $signame[$number];
    }
}

=item normalize_pkg_path(PATH)

Normalize PATH by removing superfluous path segments.  PATH is assumed
to be relative the package root.  Note that the result will never
start nor end with a slash, even if PATH does.

As the name suggests, this is a path "normalization" rather than a
true path resolution (for that use Cwd::realpath).  Particularly,
it assumes none of the path segments are symlinks.

normalize_pkg_path will return C<q{}> (i.e. the empty string) if PATH
is normalized to the root dir and C<undef> if the path cannot be
normalized without escaping the package root.

Examples:
  normalize_pkg_path('usr/share/java/../../../usr/share/ant/file')
    eq 'usr/share/ant/file'
  normalize_pkg_path('usr/..') eq q{};

 The following will return C<undef>:
  normalize_pkg_path('usr/bin/../../../../etc/passwd')

=item normalize_pkg_path(CURDIR, LINK_TARGET)

Normalize the path obtained by following a link with LINK_TARGET as
its target from CURDIR as the current directory.  CURDIR is assumed to
be relative to the package root.  Note that the result will never
start nor end with a slash, even if CURDIR or DEST does.

normalize_pkg_path will return C<q{}> (i.e. the empty string) if the
target is the root dir and C<undef> if the path cannot be normalized
without escaping the package root.

B<CAVEAT>: This function is I<not always sufficient> to test if it is
safe to open a given symlink.  Use
L<is_ancestor_of|Lintian::Util/is_ancestor_of(PARENTDIR, PATH)> for
that.  If you must use this function, remember to check that the
target is not a symlink (or if it is, that it can be resolved safely).

Examples:

  normalize_pkg_path('usr/share/java', '../ant/file') eq 'usr/share/ant/file'
  normalize_pkg_path('usr/share/java', '../../../usr/share/ant/file')
  normalize_pkg_path('usr/share/java', '/usr/share/ant/file')
    eq 'usr/share/ant/file'
  normalize_pkg_path('/usr/share/java', '/') eq q{};
  normalize_pkg_path('/', 'usr/..') eq q{};

 The following will return C<undef>:
  normalize_pkg_path('usr/bin', '../../../../etc/passwd')
  normalize_pkg_path('usr/bin', '/../etc/passwd')

=cut

sub normalize_pkg_path {
    my ($path, $dest) = @_;
    my (@normalised, @queue);

    if (@_ == 2) {
        # We are doing CURDIR + LINK_TARGET
        if (substr($dest, 0, 1) eq '/') {
            # Link is absolute
            # short circuit $dest eq '/' case.
            return q{} if $dest eq '/';
            $path = $dest;
        } else {
            # link is relative
            $path = join('/', $path, $dest);
        }
    }

    $path =~ s,//++,/,go;
    $path =~ s,/$,,o;
    $path =~ s,^/,,o;

    # Add all segments to the queue
    @queue = split(m,/,o, $path);

    # Loop through @queue and modify @normalised so that in the end of
    # the loop, @normalised will contain the path that.
    #
    # Note that @normalised will be empty if we end in the root
    # (e.g. '/' + 'usr' + '..' -> '/'), this is fine.
    while (my $target = shift(@queue)) {
        if ($target eq '..') {
            # are we out of bounds?
            return unless @normalised;
            # usr/share/java + '..' -> usr/share
            pop(@normalised);
        } else {
            # usr/share + java -> usr/share/java
            # but usr/share + "." -> usr/share
            push(@normalised, $target) if $target ne '.';
        }
    }
    return q{} unless @normalised;
    return join('/', @normalised);
}

=item parse_boolean (STR)

Attempt to parse STR as a boolean and return its value.
If STR is not a valid/recognised boolean, the sub will
invoke croak.

The following values recognised (string checks are not
case sensitive):

=over 4

=item The integer 0 is considered false

=item Any non-zero integer is considered true

=item "true", "y" and "yes" are considered true

=item "false", "n" and "no" are considered false

=back

=cut

sub parse_boolean {
    my ($str) = @_;
    return $str == 0 ? 0 : 1 if $str =~ m/^-?\d++$/o;
    $str = lc $str;
    return 1 if $str eq 'true' or $str =~ m/^y(?:es)?$/;
    return 0 if $str eq 'false' or $str =~ m/^no?$/;
    croak "\"$str\" is not a valid boolean value";
}

=item is_ancestor_of(PARENTDIR, PATH)

Returns true if and only if PATH is PARENTDIR or a path stored
somewhere within PARENTDIR (or its subdirs).

This function will resolve the paths; any failure to resolve the path
will cause a trappable error.

=cut

sub is_ancestor_of {
    my ($ancestor, $file) = @_;
    my $resolved_file = abs_path($file)// croak("resolving $file failed: $!");
    my $resolved_ancestor = abs_path($ancestor)
      // croak("resolving $ancestor failed: $!");
    my $len;
    return 1 if $resolved_ancestor eq $resolved_file;
    # add a slash, "path/some-dir" is not "path/some-dir-2" and this
    # allows us to blindly match against the root dir.
    $resolved_file .= '/';
    $resolved_ancestor .= '/';

    # If $resolved_file is contained within $resolved_ancestor, then
    # $resolved_ancestor will be a prefix of $resolved_file.
    $len = length($resolved_ancestor);
    if (substr($resolved_file, 0, $len) eq $resolved_ancestor) {
        return 1;
    }
    return 0;
}

=item pipe_tee(INHANDLE, OUTHANDLES[, OPTS])

Read bytes from INHANDLE and copy them into all of the handles in the
listref OUTHANDLES. The optional OPTS argument is a hashref of
options, see below.

The subroutine will continue to read from INHANDLE until it is
exhausted or an error occurs (either during read or write).  In case
of errors, a trappable error will be raised.  The handles are left
open when the subroutine returns, caller must close them afterwards.

Caller should ensure that handles are using "blocking" I/O.  The
subroutine will use L<sysread|perlfunc/sysread> and
L<syswrite|perlfunc/syswrite> when reading and writing.


OPTS, if given, may contain the following key-value pairs:

=over 4

=item chunk_size

A suggested buffer size for read/write.  If given, it will be to
sysread as LENGTH argument when reading from INHANDLE.

=back

=cut

sub pipe_tee {
    my ($in_fd, $out_ref, $opts) = @_;
    my $read_size = ($opts && $opts->{'chunk_size'}) // 8096;
    my @outs = @{$out_ref};
    my $buffer;
    while (1) {
        # Disable autodie, because it includes the buffer
        # exception.  Said buffer will get printed on errors
        # yielding completely unreadable errors and a terminal
        # drowned in binary characters.
        no autodie qw(sysread syswrite);
        my $rlen = sysread($in_fd, $buffer, $read_size);
        if (not $rlen) {
            last if defined($rlen);
            croak("Failed to read from input handle: $!");
        }
        for my $out_fd (@outs) {
            my $written = 0;
            while ($written < $rlen) {
                my $remain = $rlen - $written;
                my $res = syswrite($out_fd, $buffer, $remain,$written);
                if (!defined($res)) {
                    croak("Failed to write to output handle: $!");
                }
                $written += $res;
            }
        }
    }
    return 1;
}

=item load_state_cache(STATE_DIR)

[Reporting tools only] Load the state cache from STATE_DIR.

=cut

sub load_state_cache {
    my ($state_dir) = @_;
    my $state_file = "$state_dir/state-cache";
    my $state = {};
    my $fd;
    eval {open($fd, '<:raw', $state_file);};
    if (my $err = $@) {
        if ($err->errno != ENOENT) {
            # Present, but unreadable for some reason
            die($err);
        }
        # Not present; presume empty
        return $state;
    }
    eval {$state = YAML::XS::Load(slurp_entire_file($fd, 1));};
    # Not sure what Load does in case of issues; perldoc YAML says
    # very little about it.  Based on YAML::Error, I guess it will
    # write stuff to STDERR and use die/croak, but it remains a
    # guess.
    if (my $err = $@) {
        die("$state_file was invalid; please fix or remove it.\n$err");
    }
    $state //= {};

    if (ref($state) ne 'HASH') {
        die("$state_file was invalid; please fix or remove it.");
    }
    close($fd);
    return $state;
}

=item save_state_cache(STATE_DIR, STATE)

[Reporting tools only] Save the STATE cache to STATE_DIR.

=cut

sub save_state_cache {
    my ($state_dir, $state) = @_;
    my $state_file = "$state_dir/state-cache";
    my ($tmp_fd, $tmp_path);

    ($tmp_fd, $tmp_path) = tempfile('state-cache-XXXXXX', DIR => $state_dir);
    ## TODO: Should tmp_fd be binmode'd as we use YAML::XS?

    # atomic replacement of the state file; not a substitute for
    # proper locking, but it will at least ensure that the file
    # is in a consistent state.
    eval {
        print {$tmp_fd} YAML::XS::Dump($state);

        close($tmp_fd) or die("close $tmp_path: $!");

        # There is no secret in this.  Set it to 0644, so it does not
        # require sudo access on lintian.d.o to read the file.
        chmod(0644, $tmp_path);

        rename($tmp_path, $state_file)
          or die("rename $tmp_path -> $state_file: $!");
    };
    if (my $err = $@) {
        if (-e $tmp_path) {
            # Ignore error as we have a more important one
            no autodie qw(unlink);
            unlink($tmp_path);
        }
        die($err);
    }
    return 1;
}

=item find_backlog(LINTIAN_VERSION, STATE)

[Reporting tools only] Given the current lintian version and the
harness state, return a list of group ids that are part of the
backlog.  The list is sorted based on what version of Lintian
processed the package.

Note the result is by design not deterministic to reduce the
risk of all large packages being in the same run (e.g. like
gcc-5 + gcc-5-cross + gcc-6 + gcc-6-cross).

=cut

sub find_backlog {
    my ($lintian_version, $state) = @_;
    my (@backlog, %by_version, @low_priority);
    for my $group_id (keys(%{$state->{'groups'}})) {
        my $last_version = '0';
        my $group_data = $state->{'groups'}{$group_id};
        my $is_out_of_date;
        # Does this group repeatedly fail with the current version
        # of lintian?
        if (    exists($group_data->{'processing-errors'})
            and $group_data->{'processing-errors'} > 2
            and exists($group_data->{'last-error-by'})
            and $group_data->{'last-error-by'} ne $lintian_version) {
            # To avoid possible "starvation", we will give lower priority
            # to packages that repeatedly fail.  They will be retried as
            # the backlog is cleared.
            push(@low_priority, $group_id);
            next;
        }
        if (exists($group_data->{'out-of-date'})) {
            $is_out_of_date = $group_data->{'out-of-date'};
        }
        if (exists($group_data->{'last-processed-by'})) {
            $last_version = $group_data->{'last-processed-by'};
        }
        $is_out_of_date = 1
          if not versions_equal($last_version, $lintian_version);
        push(@{$by_version{$last_version}}, $group_id) if $is_out_of_date;
    }
    for my $v (sort(versions_comparator keys(%by_version))) {
        push(@backlog, shuffle(@{$by_version{$v}}));
    }
    push(@backlog, shuffle(@low_priority)) if @low_priority;
    return @backlog;
}

=item untaint(VALUE)

Untaint VALUE

=cut

sub untaint {
    return $_[0] = $1 if $_[0] =~ m/^(.*)$/;
    return;
}

=back

=head1 SEE ALSO

lintian(1)

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
