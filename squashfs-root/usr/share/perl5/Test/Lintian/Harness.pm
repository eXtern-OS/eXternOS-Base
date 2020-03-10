# Copyright © 1998 Richard Braakman
# Copyright © 2008 Frank Lichtenheld
# Copyright © 2008, 2009 Russ Allbery
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
# MA 02110-1301, USA

package Test::Lintian::Harness;

=head1 NAME

Test::Lintian::Harness -- Helper tools for t/runtests

=head1 SYNOPSIS

  use Test::Lintian::Harness qw(up_to_date);
  if (not up_to_date('some/build-stamp', 'some/dir')) {
    # do rebuild
  }

=head1 DESCRIPTION

Helper functions for t/runtests.

=cut

use strict;
use warnings;
use autodie;

use Exporter qw(import);
use File::Basename qw(basename dirname);
use File::Find qw(find);
use File::stat;
use File::Temp qw(tempfile);
use POSIX qw(ENOENT);
use Text::Template;

use Lintian::Util
  qw(do_fork internal_error read_dpkg_control slurp_entire_file);

our @EXPORT_OK = qw(
  chdir_runcmd
  check_test_depends
  copy_template_dir
  fill_in_tmpl
  find_tests_for_tag
  generic_find_test_for_tag
  is_tag_in_file
  read_test_desc
  runsystem
  runsystem_ok
  skip_reason
  up_to_date
);

=head1 FUNCTIONS

=over 4

=item skip_reaon(SKIP_FILE)

Return the (human-readable) reason for skipping a test by reading the
SKIP_FILE.

=cut

sub skip_reason {
    my ($skipfile) = @_;
    my $reason;
    open(my $fd, '<', $skipfile);
    $reason = <$fd>;
    close($fd);
    chomp($reason) if defined $reason;
    $reason //= 'No reason given in "skip" file';
    return $reason;
}

=item copy_template_dir(SKEL_DIR, TEST_SRC_DIR, TEST_TARGET_DIR, [EXCL_SKEL[, EXCL_SRC]])

Populate TEST_TARGET_DIR with files/dirs from SKEL_DIR and
TEST_SRC_DIR.  If given, EXCL_SKEL and EXCL_SRC must be a listref
containing rsync "--exclude" options.

=cut

sub copy_template_dir {
    my ($skel, $tsrc, $targetdir, $exskel, $extsrc) = @_;
    my (@exs, @ext);
    @exs = @$exskel if $exskel;
    @ext = @$extsrc if $extsrc;
    runsystem('rsync', '-rpc', "$skel/", "$targetdir/", @exs);
    runsystem('rsync', '-rpc', "$tsrc/", "$targetdir/", @ext)
      if -d "$tsrc/";
    return;
}

=item runsystem(CMD...)

Run CMD via system, but throw an error if CMD does not return 0.

=cut

sub runsystem {
    system(@_) == 0
      or internal_error("failed: @_\n");
    return;
}

=item runsystem_ok(CMD...)

Run CMD via system, but throw an error if CMD does not return 0 or 1.

Returns 1 if CMD returned successfully (i.e. 0), otherwise 0.

This is mostly useful for running Lintian, which may return 0 or 1 on
"success".

=cut

sub runsystem_ok {
    my $errcode = system(@_);
    $errcode == 0
      or $errcode == (1 << 8)
      or internal_error("failed: @_\n");
    return $errcode == 0;
}

=item up_to_date(STAMPFILE, DIR[, RUNNER_TS])

Returns true if the mtime of STAMPFILE is greater than or equal to the
mtime of all files in DIR.  If RUNNER_TS is given, then the mtime of
STAMPFILE must also be greater than or equal to the value of
RUNNER_TS.

If STAMPFILE does not exist, this function returns false
unconditionally.

=cut

sub up_to_date {
    my ($stampfile, $dir, $runner_ts) = @_;
    my $newest = 0;
    my $stamp_stat = stat($stampfile);
    if (not defined($stamp_stat)) {
        die("stat $stampfile: $!")
          if $! != ENOENT;
        # Missing file implies "out-of-date"
        return 0;
    }
    if (defined($runner_ts) and $runner_ts > $stamp_stat->mtime) {
        return 0;
    }
    my $tester = sub {
        my $path = $File::Find::name;
        my $st = stat($path) // die "stat $path: $!";
        $newest = $st->mtime if (-f _ && $st->mtime > $newest);
    };
    my %options = (
        'wanted' => $tester,
        'no_chdir' => 1,
    );
    find(\%options, $dir);
    return $stamp_stat->mtime >= $newest;
}

=item check_test_depends(TESTDATA)

Given a TESTDATA with a dependency requirement, check whether the
dependency requirement is satisfied.  If satisfied, return C<undef>,
otherwise return a (human-readable) string containing the missing
dependencies.

=cut

sub check_test_depends {
    my ($testdata) = @_;
    my ($missing, $pid, $fd, $err);
    my ($test_fd, $test_file) = tempfile('bd-test-XXXXXXXXX', TMPDIR => 1);

    # dpkg-checkbuilddeps requires that the Source: field is present.
    print {$test_fd} "Source: bd-test-pkg\n";
    print {$test_fd} "Build-Depends: $testdata->{'test-depends'}\n"
      if $testdata->{'test-depends'};
    print {$test_fd} "Build-Conflicts: $testdata->{'test-conflicts'}\n"
      if $testdata->{'test-conflicts'};
    close($test_fd);

    $pid = open($fd, '-|');
    if (!$pid) {
        open(STDIN, '<', '/dev/null');
        open(STDERR, '>&', \*STDOUT);
        exec 'dpkg-checkbuilddeps', $test_file
          or internal_error("exec dpkg-checkbuilddeps: $!");
    }
    $missing = slurp_entire_file($fd, 1);
    eval {close($fd);};
    $err = $@;
    unlink($test_file);
    if ($missing =~ s{\A dpkg-checkbuilddeps: [ ] (?:error: [ ])? }{}xsm) {
        $missing =~ s{ \b build \b }{test}gxi;
        chomp($missing);
        if ($missing =~ s{\n}{\\n}gxsm) {
            # We expect exactly one line.
            internal_error(
                "Unexpected output from dpkg-checkbuilddeps: $missing");
        }
        return $missing;
    }
    if ($err) {
        # Problem closing the pipe?
        internal_error("close pipe: $err") if $err->errno;
        internal_error($err);
    }
    return;
}

=item read_test_desc(FILENAME)

Parse FILENAME as a test description file, do a quick validation of
its contents and return it in a hashref.  This is similar
L<get_dsc_control (DSCFILE)|Lintian::Util/get_dsc_control (DSCFILE)>
except for the extra validation.

=cut

sub read_test_desc {
    my ($filename) = @_;
    my @paragraphs = read_dpkg_control($filename);
    my ($testdata, $expected_name);

    if (scalar(@paragraphs) != 1) {
        internal_error("$filename does not have exactly one paragraph");
    }
    $testdata = $paragraphs[0];
    if ($filename =~ m{/desc$}) {
        # t/<suite>/<testname>/desc
        $expected_name = basename(dirname($filename));
    } else {
        # t/changes/<testname>.desc
        $expected_name = basename($filename, '.desc');
    }

    if (!exists $testdata->{'testname'}) {
        internal_error("$filename is missing Testname field");
    }
    if ($expected_name ne $testdata->{'testname'}) {
        internal_error("$filename is called $testdata->{'testname'}"
              . " instead of $expected_name");
    }
    $testdata->{'sequence'} //= 6000;
    return $testdata;
}

=item fill_in_tmpl(FILE, DATA)

Create FILE using "${FILE}.in" as a template and DATA as template
data.

=cut

sub fill_in_tmpl {
    my ($file, $data) = @_;
    my $tmpl = "$file.in";

    my $template = Text::Template->new(TYPE => 'FILE',  SOURCE => $tmpl);
    internal_error("Cannot read template $tmpl: $Text::Template::ERROR")
      if not $template;
    open(my $out, '>', $file);

    unless ($template->fill_in(OUTPUT => $out, HASH => $data)) {
        internal_error("cannot create $file");
    }
    close($out);
    return;
}

=item chdir_runcmd(DIR, CMD_REF[, LOG_FILE])

Fork, chdir to DIR and exec the command (plus arguments) contained in
CMD_REF.  The child process's STDERR is merged into its STDOUT.  The
STDOUT stream of the child process is either directed to the path
denoted by LOG_FILE (if given and not C<undef>) or to I</dev/null>.

Returns 0 on success and non-zero otherwise.

=cut

sub chdir_runcmd {
    my ($dir, $cmd, $log) = @_;
    my $pid = do_fork();
    if ($pid) {
        waitpid $pid, 0;
        return $?;
    } else {
        $log //= '/dev/null';
        chdir($dir);
        open(STDIN, '<', '/dev/null');
        open(STDOUT, '>', $log);
        open(STDERR, '>&', \*STDOUT);
        exec { $cmd->[0] } @$cmd
          or internal_error('exec ' . @$cmd . " failed: $!");
    }
}

=item is_tag_in_file(TAGNAME, FILENAME)

Returns true if FILENAME appears to be output from Lintian, which
emitted TAGNAME from that run.

=cut

sub is_tag_in_file {
    my ($tag, $file) = @_;
    my $res = 0;
    open(my $tags, '<', $file);
    while (my $line = <$tags>){
        next if $line =~ m/^N: /;
        next unless ($line =~ m/^.: \S+(?: (?:changes|source|udeb))?: (\S+)/);
        next unless $1 eq $tag;
        $res = 1;
        last;
    }
    close($tags);
    return $res;
}

=item find_tests_for_tag(TAGNAME, GLOB_EXPR)

Find checks for the Lintian tag denoted by TAGNAME that match the
GLOB_EXPR. Note that GLOB_EXPR must match only the "desc" file of the
tests.

This function returns a list of the test-data for each of these tests.

=cut

sub find_tests_for_tag {
    my ($tag, $glob) = @_;
    return generic_find_test_for_tag(
        $tag, $glob,
        sub {
            my ($tag, $desc) = @_;
            my $data = read_test_desc($desc);
            my $tagnames = $data->{'test-for'}//'';
            $tagnames .= ' ' . $data->{'test-against'}
              if $data->{'test-against'};
            my %table = map { $_ => 1 } split(m/\s++/o, $tagnames);
            return $data if $table{$tag};
            return 0;
        });
}

=item generic_find_test_for_tag(TAGNAME, GLOB_EXPR[, TCODE])

Looks for TAGNAME in all files returned by using glob on GLOB_EXPR.
TCODE is called for each file with TAGNAME as first argument and the
filename as second argument.  TCODE is expected to return a truth
value that if the test should be run.  If TCODE returns something
that is not just a raw truth value (e.g. a hash ref), this will be
taken as the "test", otherwise this sub will attempt to guess the test
name from the file.


If TCODE is omitted, L</is_tag_in_file(TAGNAME, FILENAME)> will be
used.

Returns a list of values returned by TCODE or guessed test names (as
per above)

=cut

sub generic_find_test_for_tag {
    my ($tag, $globstr, $tcode) = @_;
    my @tests;
    $tcode = \&is_tag_in_file unless defined $tcode;
    for my $file (glob $globstr){
        my $res = $tcode->($tag, $file);
        my $testname;
        next unless $res;

        if (not ref $res and $res =~ m/^\d+$/o){
            # returned a truth value; use the regex to deduce the test name
            ($testname) = ($file =~ m,.*/([^/]+)[/\.]tags$,);
        } else {
            # The code returned the test name or test data for us
            $testname = $res;
        }
        push @tests, $testname;
    }
    return @tests;
}

=back

=cut

1;

