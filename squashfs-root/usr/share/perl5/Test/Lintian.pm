# Copyright (C) 1998 Richard Braakman
# Copyright (C) 2012 Niels Thykier
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

package Test::Lintian;

=head1 NAME

Test::Lintian -- Check Lintian files for issues

=head1 SYNOPSIS

 # file 1
 use Test::Lintian;
 use Test::More import => ['done_testing'];
 test_load_profiles('some/path');
 
 done_testing;
 
 # file 2
 use Test::Lintian;
 use Test::More import => ['done_testing'];
 load_profile_for_test('vendor/profile', 'some/path', '/usr/share/lintian');
 test_check_desc('some/path/checks');
 test_load_checks('some/path/checks');
 test_tags_implemented('some/path/checks');
 
 done_testing;

=head1 DESCRIPTION

A testing framework for testing various Lintian files for common
errors.

=cut

use strict;
use warnings;

my $CLASS = __PACKAGE__;
my $PROFILE;
our @EXPORT = qw(
  load_profile_for_test

  test_check_desc
  test_load_checks
  test_load_profiles
  test_tags_implemented

  program_name_to_perl_paths
);

use parent 'Test::Builder::Module';

use Cwd qw(realpath);
use File::Basename qw(basename);
use File::Find ();

use Lintian::Check qw(check_spelling);
use Lintian::Data;
use Lintian::Profile;
use Lintian::Tag::Info;
use Lintian::Tags;
use Lintian::Util
  qw(read_dpkg_control slurp_entire_file is_string_utf8_encoded);

# We want data files loaded early to avoid problems with missing data
# files ending up in releases (like in 2.5.17 and 2.5.18).
$Lintian::Data::LAZY_LOAD = 0;

my %severities = map { $_ => 1 } @Lintian::Tags::SEVERITIES;
my %certainties = map { $_ => 1 } @Lintian::Tags::CERTAINTIES;
my %check_types = map { $_ => 1 } qw(binary changes source udeb);
my %known_html_tags = map { $_ => 1 } qw(a em i tt);

# We use this to check for explicit links where it is possible to use
# a manual ref.
my $MANUALS = $Lintian::Tag::Info::MANUALS;
# lazy-load this (so loading a profile can affect it)
my %URLS;

=head1 FUNCTIONS

=over 4

=item test_check_desc([OPTS, ]CHECKS...)

Test check desc files (and the tags in them) for common errors.

OPTS is an optional HASHREF containing key/value pairs, which are
described below.

CHECKS is a list of paths in which to check desc files.  Any given
element in CHECKS can be either a file or a dir.  Files are assumed to
be check desc file.  Directories are searched and all I<.desc> files
in those dirs are processed.

As the number of tests depends on the number of tags in desc, it is
difficult to "plan ahead" when using this test.  It is therefore
recommended to not specify a plan and use done_testing().

This sub uses a Data file (see L</load_profile_for_test ([PROFNAME[, INC...]])>).

OPTS may contain the following key/value pairs:

=over 4

=item coll-dir

Path to the collection directory (defaults to:
/usr/share/lintian/collection).  This is mostly useful for testing
Lintian itself.

If set to C<undef>, the test of Needs-Info containing only existing
collections will be skipped.

=item filter

If defined, it is a filter function that examines $_ (or its first
argument) and returns a truth value if C<$_> should be considered or
false otherwise.  C<$_> will be the path to the current file (or dir)
in question; it may be relative or absolute.

NB: I<all> elements in CHECKS are subject to the filter.

CAVEAT: If the filter rejects a directory, none of the files in it will be
considered either.  Even if the filter accepts a file, that file will
only be processed if it has the proper extension (i.e. with I<.desc>).

=item translation

If defined and a truth value, the desc files are expected to contain
translations.  Otherwise, they must be regular checks.

=back

=cut

sub test_check_desc {
    my ($opts, @descs);
    my $builder = $CLASS->builder;
    my $colldir = '/usr/share/lintian/collection';
    my $find_opt = {'filter' => undef,};
    my $tested = 0;

    if (ref $_[0] eq 'HASH') {
        $opts = shift;
        $colldir = $opts->{'coll-dir'}//'' if exists $opts->{'coll-dir'};
        $find_opt->{'filter'} = $opts->{'filter'} if exists $opts->{'filter'};
    }
    $opts //= {};
    @descs = @_;
    load_profile_for_test();

    foreach my $desc_file (map { _find_check($find_opt, $_) } @descs) {
        my ($header, @tagpara);
        eval {($header, @tagpara) = read_dpkg_control($desc_file);};
        if (my $err = $@) {
            $err =~ s/ at .*? line \d+\s*\n//;
            $builder->ok(0, "Cannot parse $desc_file");
            $builder->diag("Error: $err");
            next;
        }
        my $content_type = 'Check';
        my $cname = $header->{'check-script'}//'';
        my $ctype = $header->{'type'} // '';
        my $needs = $header->{'needs-info'} // '';
        my $i = 1; # paragraph counter.
        $builder->ok(1, "Can parse check $desc_file");

        $builder->isnt_eq($cname, '',"$content_type has a name ($desc_file)");

        # From here on, we just use "$cname" as name of the check, so
        # we don't need to choose been it and $tname.
        $cname = '<missing>' if $cname eq '';
        $tested += 2;

        if ($cname eq 'lintian') {
            my $reason = 'check "lintian" does not have a type';
            # skip these two tests for this special case...
            $builder->skip("Special case, $reason");
            $builder->skip("Special case, $reason");
        } elsif ($builder->isnt_eq($ctype, '', "$cname has a type")) {
            my @bad;
            # new lines are not allowed, map them to "\\n" for readability.
            $ctype =~ s/\n/\\n/go;
            foreach my $type (split m/\s*+,\s*+/o, $ctype) {
                push @bad, $type unless exists $check_types{$type};
            }
            $builder->is_eq(join(', ', @bad),'',"The type of $cname is valid");
        } else {
            $builder->skip(
                "Cannot check type of $cname is valid (field is empty/missing)"
            );
        }

        if ($needs and $colldir ne '') {
            my @bad;
            # new lines are not allowed, map them to "\\n" for readability.
            $needs =~ s/\n/\\n/go;
            foreach my $need (split m/\s*+,\s*+/o, $needs) {
                push @bad, $need unless -f "$colldir/$need.desc";
            }
            $builder->is_eq(join(', ', @bad),
                '', "$cname has unknown collections in Needs-Info");
        } else {
            $builder->ok(1, "$content_type has a valid Needs-Info (empty)")
              if $colldir ne '';
            $builder->skip(
                'Needs-Info test checks skipped due to empty coll-dir')
              if $needs ne '';
        }
        if (my $d = $header->{'info'}) {
            my $mistakes = 0;
            my $handler = sub {
                my ($incorrect, $correct) = @_;
                $builder->diag("Spelling ($cname): $incorrect => $correct");
                $mistakes++;
            };
            check_spelling($d, $handler);
            $builder->is_eq($mistakes, 0,"$cname Info has no spelling errors");
        } else {
            $builder->ok(0, "$cname has an Info field");
        }
        foreach my $tpara (@tagpara) {
            my $tag = $tpara->{'tag'}//'';
            my $severity = $tpara->{'severity'}//'';
            my $certainty = $tpara->{'certainty'}//'';
            my $info = $tpara->{'info'} // '';
            my (@htmltags, %seen);

            $i++;

            # Tag name
            $builder->isnt_eq($tag, '', "Tag in check $cname has a name")
              or $builder->diag("$cname: Paragraph number $i\n");
            $tag = '<N/A>' if $tag eq '';
            $builder->ok($tag =~ /^[\w0-9.+-]+$/, 'Tag has valid characters')
              or $builder->diag("$cname: $tag\n");
            $builder->cmp_ok(length $tag, '<=', 68, 'Tag is not too long')
              or $builder->diag("$cname: $tag\n");

            # Severity / Certainty
            $builder->ok($severity && exists $severities{$severity},
                'Tag has valid severity')
              or $builder->diag("$cname: $tag severity: $severity\n");
            $builder->ok($certainty && exists $certainties{$certainty},
                'Tag has valid certainty')
              or $builder->diag("$cname: $tag certainty: $certainty\n");

            # Info
            my $mistakes = 0;
            my $handler = sub {
                my ($incorrect, $correct) = @_;
                $builder->diag(
                    "Spelling ($cname/$tag): $incorrect => $correct");
                $mistakes++;
            };
            # FIXME: There are a couple of known false-positives that
            # breaks the test.
            # check_spelling($info, $handler);
            $builder->is_eq($mistakes, 0,
                "$content_type $cname: $tag has no spelling errors");

            $builder->ok($info !~ /(?:^| )(?:[Ww]e|I)\b/,
                'Tag info does not speak of "I", or "we"')
              or $builder->diag("$content_type $cname: $tag\n");

            $builder->ok(
                $info !~ /(\S\w)\. [^ ]/
                  || $1 =~ '/^\.[ge]$/', # for 'e.g.'/'i.e.'
                'Tag info uses two spaces after a full stop'
            ) or $builder->diag("$content_type $cname: $tag\n");

            $builder->ok($info !~ /(\S\w\.   )/,
                'Tag info uses only two spaces after a full stop')
              or $builder->diag("$content_type $cname: $tag ($1)\n");

            $builder->ok(
                is_string_utf8_encoded($info),
                'Tag info must be written in UTF-8'
            ) or $builder->diag("$content_type $cname: $tag\n");

            # Check the tag info for unescaped <> or for unknown tags (which
            # probably indicate the same thing).
            while ($info =~ s,<([^\s>]+)(?:\s+href=\"[^\"]+\")?>.*?</\1>,,s) {
                push @htmltags, $1;
            }
            @htmltags
              = grep { !exists $known_html_tags{$_} && !$seen{$_}++ }@htmltags;
            $builder->is_eq(join(', ', @htmltags),
                '', 'Tag info has no unknown html tags')
              or $builder->diag("$content_type $cname: $tag\n");

            $builder->ok($info !~ /[<>]/,
                'Tag info has no stray angle brackets')
              or $builder->diag("$content_type $cname: $tag\n");

            if ($tpara->{'ref'}) {
                my @issues = _check_reference($tpara->{'ref'});
                my $text = join("\n\t", @issues);
                $builder->ok(!@issues, 'Proper references are used')
                  or $builder->diag("$content_type $cname: $tag\n\t$text");
            }
        }
    }

    $builder->cmp_ok($tested, '>', 0, 'Tested at least one desc file')
      if @descs;
    return;
}

=item test_load_profiles(ROOT, INC...)

Test that all profiles in I<ROOT/profiles> are loadable.  INC will be
the INC path used as include path for the profile.

If INC is omitted, then the include path will consist of (ROOT,
'/usr/share/lintian').  Otherwise, INC will be used as is (and should
include ROOT).

This sub will do one test per profile loaded.

=cut

sub test_load_profiles {
    my ($dir, @inc) = @_;
    my $builder = $CLASS->builder;
    my $absdir = realpath $dir;
    my $sre;
    my %opt = ('no_chdir' => 1,);
    if (not defined $absdir) {
        die "$dir cannot be resolved: $!";
    }
    $absdir = "$absdir/profiles";
    $sre = qr,\Q$absdir\E/,;

    @inc = ($absdir, '/usr/share/lintian') unless @inc;

    $opt{'wanted'} = sub {
        my $profname = $File::Find::name;
        my ($err, $prof);

        return unless $profname =~ s/\.profile$//o;
        $profname =~ s,^$sre,,;

        eval {$prof = Lintian::Profile->new($profname, \@inc);};
        $err = $@;

        $builder->ok($prof, "$profname is loadable.")
          or $builder->diag("Load error: $err\n");
    };

    File::Find::find(\%opt, $absdir);
    return;
}

=item test_load_checks([OPTS, ]DIR[, CHECKNAMES...])

Test that the Perl module implementation of the checks can be loaded
and has a run sub.

OPTS is an optional HASHREF containing key/value pairs, which are
described below.

DIR is the directory where the checks can be found.

CHECKNAMES is a list of check names.  If CHECKNAMES is given, only the
checks in this list will be processed.  Otherwise, all the checks in
DIR will be processed.

For planning purposes, every check processed counts for 2 tests and
the call itself does on additional check.  So if CHECKNAMES contains
10 elements, then 21 tests will be done (2 * 10 + 1).  Filtered out
checks will I<not> be counted.

All data files created at compile time or in the file scope will be
loaded immediately (instead of lazily as done during the regular
runs).  This is done to spot missing data files or typos in their
names.  Therefore, this sub will load a profile if one hasn't been
loaded already.  (see L</load_profile_for_test ([PROFNAME[,
INC...]])>)

OPTS may contain the following key/value pairs:

=over 4

=item filter

If defined, it is a filter function that examines $_ (or its first
argument) and returns a truth value if C<$_> should be considered or
false otherwise.  C<$_> will be the path to the current file (or dir)
in question; it may be relative or absolute.

NB: filter is I<not> used if CHECKNAMES is given.

CAVEAT: If the filter rejects a directory, none of the files in it will be
considered either.  Even if the filter accepts a file, that file will
only be processed if it has the proper extension (i.e. with I<.desc>).

=back

=cut

sub test_load_checks {
    my ($opts, $dir, @checknames);
    my $builder = $CLASS->builder;

    if ($_[0] and ref $_[0] eq 'HASH') {
        ($opts, $dir, @checknames) = @_;
    } else {
        $opts = {};
        ($dir, @checknames) = @_;
    }

    unless (@checknames) {
        my $find_opt = {'want-check-name' => 1,};
        $find_opt->{'filter'} = $opts->{'filter'} if exists $opts->{'filter'};
        @checknames = _find_check($find_opt, $dir);
        $builder->cmp_ok(scalar @checknames, '>', 0, 'Found checks to test');
    } else {
        $builder->skip('Given an explicit list of checks');
    }

    load_profile_for_test();

    foreach my $checkname (@checknames) {
        my $cs;
        eval {$cs = Lintian::CheckScript->new($dir, $checkname);};
        if (my $err = $@) {
            $err =~ s/ at .*? line \d+\s*\n//;
            $builder->ok(0, "Cannot parse ${checkname}.desc");
            $builder->diag("Error: $err\n");
            $builder->skip("Cannot parse ${checkname}.desc");
            next;
        }
        my $cname = $cs->name;
        my $ppkg = $cname;
        my $path = $cs->script_path;
        my $err;
        my $rs_ref = 'MISSING';

        eval {require $path;};

        if (!$builder->is_eq($@//'', '', "Check $cname can be loaded")) {
            $builder->skip(
                "Cannot check if $cname has a run sub due to load error");
            next;
        }

        $ppkg =~ s,[-.],_,go;
        $ppkg =~ s,/,::,go;
        $ppkg = "Lintian::$ppkg";
        eval {
            # minimal "no strict refs" scope.
            no strict 'refs';
            $rs_ref = 'PRESENT'
              if defined &{$ppkg . '::run'};
        };
        $err = $@//'';
        if (!$builder->is_eq($rs_ref, 'PRESENT', "Check $cname has runsub")) {
            $builder->diag("Expected package name is $ppkg\n");
            $builder->diag("Error: $err\n") if $err;
        }
    }
    return;
}

=item test_tags_implemented ([OPTS, ]DIR[, CHECKNAMES...])

Test a given check implements all the tags listed in its desc file.
For planning purposes, each check counts as one test and the call
itself do one additional check.  So if 10 checks are tested, the plan
should account for 11 tests.

This is a simple scan of the source code looking asserting that the
tag names I<appear> (in the actual code part).  For a vast majority of
Lintian's tags it is reliable enough to be useful.  However it has
false-positives and false-negatives - the former can be handled via
"exclude-pattern" (see below).

The DIR argument is the directory in which to find the checks.

CHECKNAMES is a list of the check names.  If CHECKNAMES is given, only
the checks in this list will be processed.  Otherwise, all the checks
in DIR will be processed.

The optional parameter OPTS is a hashref.  If passed it must be the
first argument.  The following key/value pairs are defined:

=over 4

=item exclude-pattern

The value is assumed to be a regex (or a string describing a regex).
Any tag matching this regex will be excluded from this test and is
assumed to be implemented (regardless of whether that is true or not).

This is useful for avoiding false-positives with cases like:

  foreach my $x (@y) {
    tag "some-tag-for-$x", "blah blah $x"
        unless f($x);
  }

=item filter

If defined, it is a filter function that examines $_ (or its first
argument) and returns a truth value if C<$_> should be considered or
false otherwise.  C<$_> will be the path to the current file (or dir)
in question; it may be relative or absolute.

NB: filter is I<not> used if CHECKNAMES is given.

CAVEAT: If the filter rejects a directory, none of the files in it will be
considered either.  Even if the filter accepts a file, that file will
only be processed if it has the proper extension (i.e. with I<.desc>).

=back

As mentioned, this test assert that the tag name appears in the code.
Consider the following example:

 my $tagname = 'my-tag';
 $tagname = 'my-other-tag' if $condition;

In this example, this test would conclude that 'my-tag' and
'my-other-tag' are both implemented.  Which is good when $tagname is
eventually passed to L<tag|Lintian::Tags/tag>, and a false-negative
otherwise.

Comment lines are I<not> ignored, so comments can be used as an
alternative to the exclude-pattern (above).

=cut

sub test_tags_implemented {
    my ($opts, $dir, @checknames);
    my $pattern;
    my $builder = $CLASS->builder;

    if ($_[0] and ref $_[0] eq 'HASH') {
        ($opts, $dir, @checknames) = @_;
    } else {
        $opts = {};
        ($dir, @checknames) = @_;
    }

    unless (@checknames) {
        my $find_opt = {'want-check-name' => 1,};
        $find_opt->{'filter'} = $opts->{'filter'} if exists $opts->{'filter'};
        @checknames = _find_check($find_opt, $dir);
        $builder->cmp_ok(scalar @checknames, '>', 0, 'Found checks to test');
    } else {
        $builder->skip('Given an explicit list of checks');
    }

    if (exists $opts->{'exclude-pattern'}) {
        if (ref $opts->{'exclude-pattern'} eq 'Regexp') {
            $pattern = $opts->{'exclude-pattern'};
        } else {
            $pattern = qr/$opts->{'exclude-pattern'}/;
        }
    }

    foreach my $checkname (@checknames) {
        my ($cs, @tags, $codestr, @missing);
        eval {$cs = Lintian::CheckScript->new($dir, $checkname);};
        if (my $err = $@) {
            $err =~ s/ at .*? line \d+\s*\n//;
            $builder->ok(0, "Cannot parse ${checkname}.desc");
            $builder->diag("Error: $err\n");
            next;
        }
        my $cname = $cs->name;
        my $check = $cs->script_path;

        @tags = $cs->tags unless defined $pattern;
        @tags = grep { !m/$pattern/ } $cs->tags
          if defined $pattern;

        # Any tags left to check?
        unless (@tags) {
            $builder->skip("All tags $cname are excluded");
            next;
        }

        $codestr = slurp_entire_file($check);

        for my $tag (@tags) {
            push @missing, $tag unless $codestr =~ /\Q$tag/;
        }

        $builder->is_eq(join(', ', @missing),
            '',"$cname has all tags implemented");
    }
    return;
}

=item load_profile_for_test ([PROFNAME[, INC...]])

Load a Lintian::Profile and ensure Data files can be used.  This is
needed if the test needs to access a data file or if a special profile
is needed for the test.  It does I<not> test the profile for issues.

PROFNAME is the name of the profile to load.  It can be omitted, in
which case the sub ensures that a profile has been loaded.  If no
profile has been loaded, 'debian/main' will be loaded.

INC is a list of extra "include dirs" (or Lintian "roots") to be used
for finding the profile.  If not specified, it defaults to
I<$ENV{'LINTIAN_TEST_ROOT'}> and I</usr/share/lintian> (in order).
INC is ignored if a profile has already been loaded.

CAVEAT: Only one profile can be loaded in a given test.  Once a
profile has been loaded, it is not possible to replace it with another
one.  So if this is invoked multiple times, PROFNAME must be omitted
or must match the name of the loaded profile.

=cut

sub load_profile_for_test {
    my ($profname, @inc) = @_;

    # We have loaded a profile and are not asked to
    # load a specific one - then current one will do.
    return if $PROFILE and not $profname;

    die "Cannot load two profiles.\n"
      if $PROFILE and $PROFILE->name ne $profname;

    return if $PROFILE; # Already loaded? stop here
    # We just need it for spell checking, so debian/main should
    # do just fine...
    $profname ||= 'debian/main';

    unless (@inc) {
        push @inc, $ENV{'LINTIAN_TEST_ROOT'} if $ENV{'LINTIAN_TEST_ROOT'};
        push @inc, '/usr/share/lintian' if -d '/usr/share/lintian';
    }

    $PROFILE = Lintian::Profile->new($profname, \@inc);
    Lintian::Data->set_vendor($PROFILE);
    $ENV{'LINTIAN_HELPER_DIRS'} = join(':', map { "$_/helpers" } @inc);
    $ENV{'LINTIAN_INCLUDE_DIRS'} = join(':', @inc);
    return;
}

sub _check_reference {
    my ($refdata) = @_;
    my @issues;

    unless (%URLS) {
        $MANUALS->known(''); # force it to load the manual refs
        foreach my $manid ($MANUALS->all) {
            my $table = $MANUALS->value($manid);
            foreach my $section (keys %{$table}) {
                my $url = $table->{$section}{url};
                next unless $url;
                $URLS{$url} = "$manid $section";
            }
        }
    }

    foreach my $reference (split /\s*,\s*/, $refdata) {
        if (   $reference =~ m,^https?://bugs.debian.org/(\d++)$,
            or $reference
            =~ m,^https?://bugs.debian.org/cgi-bin/bugreport.cgi\?/.*bug=(\d++).*$,
          ) {
            push @issues, "replace \"$reference\" with \"#$1\"";
        } elsif (exists $URLS{$reference}) {
            push @issues, "replace \"$reference\" with \"$URLS{$reference}\"";
        } elsif ($reference =~ m/^([\w-]++)\s++(\S++)$/) {
            my ($manual, $section) = ($1, $2);
            if ($MANUALS->known($manual)) {
                push @issues, "unknown section \"$section\" in $manual"
                  unless exists $MANUALS->value($manual)->{$section};
            } else {
                push @issues, "unknown manual \"$manual\"";
            }
        } else {
            # Check it is a valid reference like URLs or #123456
            # NB: "policy 10.1" references already covered above
            my $ok = 0;
            $ok = 1 if $reference =~ m/^#\d++$/; # debbugs reference
            $ok = 1 if $reference =~ m,^(?:ftp|https?)://,; # browser URL
            $ok = 1 if $reference =~ m,^/,; # local file reference
            $ok = 1 if $reference =~ m,[\w_-]+\(\d\w*\)$,; # man reference
            push @issues, "unknown/malformed reference \"$reference\""
              unless $ok;
        }
    }
    return @issues;
}

sub _find_check {
    my ($find_opt, $input) = @_;
    $find_opt//= {};
    my $filter = $find_opt->{'filter'};

    if ($filter) {
        local $_ = $input;
        # filtered out?
        return () unless $filter->($_);
    }

    if (-d $input) {
        my (@result, $regex);
        if ($find_opt->{'want-check-name'}) {
            $regex = qr,^\Q$input\E/*,;
        }
        my $wanted = sub {
            if (defined $filter) {
                local $_ = $_;
                if (not $filter->($_)) {
                    # filtered out; if a dir - filter the
                    # entire dir.
                    $File::Find::prune = 1 if -d $_;
                    return;
                }
            }
            return unless m/\.desc$/ and -f $_;
            if ($regex) {
                s/$regex//;
                s/\.desc$//;
            }
            push @result, $_;
        };
        my $opt = {
            'wanted' => $wanted,
            'no_chdir' => 1,
        };
        File::Find::find($opt, $input);
        return @result;
    }

    return ($input);
}

=item program_name_to_perl_paths(PROGNAME)

Map the program name (e.g. C<$0>) to a list of directories or/and
files that should be processed.

This helper sub is mostly useful for splitting up slow tests run over
all Perl scripts/modules in Lintian.  This allows better use of
multiple cores.  Example:


  t/scripts/my-test/
   runner.pl
   checks.t -> runner.pl
   collection.t -> runner.pl
   ...

And then in runner.pl:

  use Test::Lintian;
  
  my @paths = program_name_to_perl_paths($0);
  # test all files/dirs listed in @paths

For a more concrete example, see t/scripts/01-critic/ and the
files/symlinks beneath it.

=cut

{

    my %SPECIAL_PATHS = (
        'docs-examples' => ['doc/examples/checks'],
        'test-scripts' => [qw(t/scripts t/helpers t/runtests)],
    );

    sub program_name_to_perl_paths {
        my ($program) = @_;
        # We need the basename before resolving the path (because
        # afterwards it is "runner.pl" and we want it to be e.g.
        # "checks.t" or "collections.t").
        my $basename = basename($program, '.t');

        if (exists($SPECIAL_PATHS{$basename})) {
            return @{$SPECIAL_PATHS{$basename}};
        }

        return ($basename);
    }
}

=back

=cut

1;
