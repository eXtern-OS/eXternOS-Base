#
# $Id$
#

package Glib::MakeHelper;

our $VERSION = '1.326';

=head1 NAME

Glib::MakeHelper - Makefile.PL utilities for Glib-based extensions

=head1 SYNOPSIS

 eval "use Glib::MakeHelper; 1"
     or complain_that_glib_is_too_old_and_die();
 
 %xspod_files = Glib::MakeHelper->do_pod_files (@xs_files);

 package MY;
 sub postamble {
     return Glib::MakeHelper->postamble_clean ()
          . Glib::MakeHelper->postamble_docs (@main::xs_files)
          . Glib::MakeHelper->postamble_rpms (
                 MYLIB     => $build_reqs{MyLib},
            );
 }

=head1 DESCRIPTION

The Makefile.PL for your typical Glib-based module is huge and hairy, thanks to
all the crazy hoops you have to jump through to get things right.  This module
wraps up some of the more intense and error-prone bits to reduce the amount of
copied code and potential for errors.

=cut

use strict;
use warnings;
use Carp;
use Cwd;

our @gend_pods = ();

=head1 METHODS

=over

=item HASH = Glib::MakeHelper->do_pod_files (@xs_files)

Scan the I<@xs_files> and return a hash describing the pod files that will
be created.  This is in the format wanted by WriteMakefile(). If @ARGV contains
the string C<disable-apidoc> an empty list will be returned and thus no apidoc
pod will be generated speeding up the build process.

=cut

sub do_pod_files
{
	return () if (grep /disable[-_]apidoc/i, @ARGV);
	print STDERR "Including generated API documentation...\n";

	shift; # package name

	# try to get it from pwd first, then fall back to installed
	# this is so Glib will get associated copy, and everyone else
	# should use the installed glib copy
	eval { require './lib/Glib/ParseXSDoc.pm'; 1; } or require Glib::ParseXSDoc;
	$@ = undef;
	import Glib::ParseXSDoc;

	my %pod_files = ();

	open PARSE, '>build/doc.pl';
	select PARSE;
	my $pods = xsdocparse (@_);
	select STDOUT;
	@gend_pods = ();
	foreach (@$pods)
	{
		my $pod = $_;
		my $path = '$(INST_LIB)';
		$pod = File::Spec->catfile ($path, split (/::/, $_)) . ".pod";
		push @gend_pods, $pod;
		$pod_files{$pod} = '$(INST_MAN3DIR)/'.$_.'.$(MAN3EXT)';
	}
	$pod_files{'$(INST_LIB)/$(FULLEXT)/index.pod'} = '$(INST_MAN3DIR)/$(NAME)::index.$(MAN3EXT)';

	return %pod_files;
}

=item LIST = Glib::MakeHelper->select_files_by_version ($stem, $major, $minor)

Returns a list of all files that match "$stem-\d+\.\d+" and for which the first
number is bigger than I<$major> and the second number is bigger than I<$minor>.
If I<$minor> is odd, it will be incremented by one so that the version number of
an upcoming stable release can be used during development as well.

=cut

sub select_files_by_version {
	my ($class, $stem, $major, $minor) = @_;

	# make minors even, so that we don't have to deal with stable/unstable
	# file naming changes.
	$minor++ if ($minor % 2);

	my @files = ();
	foreach (glob $stem . '-*.*') {
		if (/$stem-(\d+)\.(\d+)/) {
			push @files, $_
				if  $1 <= $major
				and $2 <= $minor;
		}
	}

	return @files;
}

=item LIST = Glib::MakeHelper->read_source_list_file ($filename)

Reads I<$filename>, removes all comments (starting with "#") and leading and
trailing whitespace, and returns a list of all lines that survived the treatment.

=cut

sub read_source_list_file {
	my ($class, $filename) = @_;
	my @list = ();
	open IN, $filename or die "can't read $filename: $!\n";
	while (<IN>) {
		s/#.*$//;		# eat comments
		s/^\s*//;		# trim leading space
		s/\s*$//;		# trim trailing space
		push @list, $_ if $_;	# keep non-blanks
	}
	close IN;
	return @list;
}

=item string = Glib::MakeHelper->get_configure_requires_yaml (%module_to_version)

Generates YAML code that lists every module found in I<%module_to_version>
under the C<configure_requires> key.  This can be used with
L<ExtUtils::MakeMaker>'s C<EXTRA_META> parameter to specify which modules are
needed at I<Makefile.PL> time.

This function is B<deprecated> since L<ExtUtils::MakeMaker> 6.46 removed
support for C<EXTRA_META> in favor of the new keys C<META_MERGE> and
C<META_ADD>.

=cut

sub get_configure_requires_yaml {
  shift; # package name
  my %prereqs = @_;

  my $yaml = "configure_requires:\n";
  while (my ($module, $version) = each %prereqs) {
    $yaml .= "   $module: $version\n";
  }

  return $yaml;
}

=item string = Glib::MakeHelper->postamble_clean (@files)

Create and return the text of a realclean rule that cleans up after much 
of the autogeneration performed by Glib-based modules.  Everything in @files
will be deleted, too (it may be empty).

The reasoning behind using this instead of just having you use the 'clean'
or 'realclean' keys is that this avoids you having to remember to put Glib's
stuff in your Makefile.PL's WriteMakefile arguments.

=cut

our @ADDITIONAL_FILES_TO_CLEAN = ();

sub postamble_clean
{
	shift; # package name
"
realclean ::
	-\$(RM_RF) build perl-\$(DISTNAME).spec @ADDITIONAL_FILES_TO_CLEAN @_
";
}

=item string = Glib::MakeHelper->postamble_docs (@xs_files)

NOTE: this is The Old Way.  see L<postamble_docs_full> for The New Way.

Create and return the text of Makefile rules to build documentation from
the XS files with Glib::ParseXSDoc and Glib::GenPod.

Use this in your MY::postamble to enable autogeneration of POD.

This updates dependencies with the list of pod names generated by an earlier
run of C<do_pod_files>.

There is a special Makefile variable POD_DEPENDS that should be set to the
list of files that need to be created before the doc.pl step is run, include
files.

There is also a variable BLIB_DONE which should be used as a dependency
anywhere a rule needs to be sure that a loadable and working module resides in
the blib directory before running.

=cut

sub postamble_docs
{
	my ($class, @xs_files) = @_;
	return Glib::MakeHelper->postamble_docs_full (XS_FILES => \@xs_files);
}

=item string = Glib::MakeHelper->postamble_docs_full (...)

Create and return the text of Makefile rules to build documentation from
the XS files with Glib::ParseXSDoc and Glib::GenPod.

Use this in your MY::postamble to enable autogeneration of POD.

This updates dependencies with the list of pod names generated by an earlier
run of C<do_pod_files>.

There is a special Makefile variable POD_DEPENDS that should be set to the
list of files that need to be created before the doc.pl step is run, include
files.

There is also a variable BLIB_DONE which should be used as a dependency
anywhere a rule needs to be sure that a loadable and working module resides in
the blib directory before running.

The parameters are a list of key=>value pairs.  You must specify at minimum
either DEPENDS or XS_FILES.

=over

=item DEPENDS => ExtUtils::Depends object

Most gtk2-perl modules use ExtUtils::Depends to find headers, typemaps,
and other data from parent modules and to install this data for child
modules.  We can find from this object the list of XS files to scan for
documentation, doctype mappings for parent modules, and other goodies.

=item XS_FILES => \@xs_file_names

A list of xs files to scan for documentation.  Ignored if DEPENDS is
used.

=item DOCTYPES => \@doctypes_file_names

List of filenames to pass to C<Glib::GenPod::add_types>.  May be omitted.

=item COPYRIGHT => string

POD text to be inserted in the 'COPYRIGHT' section of each generated page.
May be omitted.

=item COPYRIGHT_FROM => file name

The name of a file containing the POD to be inserted in the 'COPYRIGHT'
section of each generated page.  May be omitted.

=item NAME => extension name

The name of the extension, used to set the main mod for Glib::GenPod (used in the
generated see-also listings).  May be omitted in favor of the name held
inside the ExtUtils::Depends object.  If DEPENDS is also specified, NAME wins.

=back

=cut

sub postamble_docs_full {
	my $class = shift; # package name
	my %params = @_;

	croak "Usage: $class\->postamble_docs_full (...)\n"
	    . "  where ... is a list of key/value pairs including at the\n"
	    . "  very least one of DEPENDS=>\$extutils_depends_object or\n"
	    . "  XS_FILES=>\@xs_files\n"
	    . "    "
		unless $params{DEPENDS} or $params{XS_FILES};

	my @xs_files = ();
	my @doctypes = ();
	my $add_types = '';
	my $copyright = '';
	my $name = '';

	if ($params{DOCTYPES}) {
		@doctypes = ('ARRAY' eq ref $params{DOCTYPES})
		          ? @{$params{DOCTYPES}}
		          : ($params{DOCTYPES});
	}

	if (UNIVERSAL::isa ($params{DEPENDS}, 'ExtUtils::Depends')) {
		my $dep = $params{DEPENDS};

		# fetch list of XS files from depends object.
		# HACK ALERT: the older versions of ExtUtils::Depends
		# (<0.2) use a different key layout and don't store enough
		# metadata about the dependencies, so we require >=0.2;
		# however, the older versions don't support import version
		# checking (in fact they don't support version-checking at
		# all), so the "use" test in a Makefile.PL can't tell if
		# it has loaded a new enough version!
		# the rewrite at version 0.200 added the get_dep() method,
		# which we use, so let's check for that.
		unless (defined &ExtUtils::Depends::get_deps) {
			use ExtUtils::MakeMaker;
			warn "ExtUtils::Depends is too old, need at "
			   . "least version 0.2";
			# this is so that CPAN builds will do the upgrade
			# properly.
			WriteMakefile(
				PREREQ_FATAL => 1,
				PREREQ_PM => { 'ExtUtils::Depends' => 0.2, },
			);
			exit 1; # not reached.
		}
		# continue with the excessive validation...
		croak "value of DEPENDS key must be an ExtUtils::Depends object"
			unless UNIVERSAL::isa $dep, 'ExtUtils::Depends';
		croak "corrupt or invalid ExtUtils::Depends instance -- "
		    . "the xs key is "
		    .(exists ($dep->{xs}) ? "missing" : "broken")."!"
			unless exists $dep->{xs}
			   and 'ARRAY' eq ref $dep->{xs};

		# finally, *this* is what we wanted.
		@xs_files = @{$dep->{xs}};

		# fetch doctypes files from the depends' dependencies.
		my %deps = $dep->get_deps;
		foreach my $d (keys %deps) {
			my $f = File::Spec->catfile ($deps{$d}{instpath},
			                             'doctypes');
			#warn "looking for $f\n";
			push @doctypes, $f
				if -f $f;
		}

		# the depends object conveniently knows the main module name.
		$name = $dep->{name};
	} else {
		@xs_files = @{ $params{XS_FILES} };
	}

	if ($params{COPYRIGHT}) {
		$copyright = $params{COPYRIGHT};
	} elsif ($params{COPYRIGHT_FROM}) {
		open IN, $params{COPYRIGHT_FROM} or
			croak "can't open $params{COPYRIGHT_FROM} for reading: $!\n";
		local $/ = undef;
		$copyright = <IN>;
		close IN;
	}

	if ($copyright) {
		# this text has to be escaped for both make and the shell.
		$copyright =~ s/\n/\\n/gm; # collapse to one line.
		$copyright =~ s|/|\\/|g;   # escape slashes for qq//
		$copyright = "Glib::GenPod::set_copyright(qq/$copyright/);";
	}

	# the module name specified explicitly overrides the one in a
	# depends object.
	$name = $params{NAME} if $params{NAME};
	# now sanitize
	if ($name) {
		# this is supposed to be a module name; names don't have
		# things in them that need escaping, so let's leave it alone.
		# that way, if there's a quoting error, the user will figure
		# it out real quick.
		$name = "Glib::GenPod::set_main_mod(qq($name));";
	}

	#warn "".scalar(@doctypes)." doctype files\n";
	#warn "".scalar(@xs_files)." xs files\n";

	if (@doctypes) {
		$add_types = 'add_types ('
		           . join(', ', map {'qq(' . quotemeta ($_) . ')'} @doctypes)
		           . '); '
	}

	my $docgen_code = ''
	    . $add_types
	    . ' '
	    . $copyright
	    . ' '
	    . $name
	    . ' $(POD_SET) '
	    . 'xsdoc2pod(q(build/doc.pl), q($(INST_LIB)), q(build/podindex));';

	#warn "docgen_code: $docgen_code\n";

	# BLIB_DONE should be set to something we can depend on that will
	# ensure that we are safe to link against an up to date module out
	# of blib. basically what we need to wait on is the static/dynamic
	# lib file to be created. the following trick is intended to handle
	# both of those cases without causing the other to happen.

	return <<"__EOM__";

BLIB_DONE=build/blib_done_\$(LINKTYPE)

build/blib_done_dynamic :: \$(INST_DYNAMIC)
	\$(NOECHO) \$(TOUCH) \$@

build/blib_done_static :: \$(INST_STATIC)
	\$(NOECHO) \$(TOUCH) \$@

build/blib_done_ :: build/blib_done_dynamic
	\$(NOECHO) \$(TOUCH) \$@

# documentation stuff
\$(INST_LIB)/Glib/GenPod.pm \$(INST_LIB)/Glib/ParseXSDoc.pm: pm_to_blib

build/doc.pl :: Makefile @xs_files
	\$(NOECHO) \$(ECHO) Parsing XS files...
	\$(NOECHO) \$(FULLPERLRUN) -I \$(INST_LIB) -I \$(INST_ARCHLIB) -MGlib::ParseXSDoc \\
		-e "xsdocparse (qw(@xs_files))" > \$@

# passing all of these files through the single podindex file, which is 
# created at the same time, prevents problems with -j4 where xsdoc2pod would 
# have multiple instances
@gend_pods :: build/podindex

build/podindex :: \$(BLIB_DONE) Makefile build/doc.pl \$(POD_DEPENDS)
	\$(NOECHO) \$(ECHO) Generating POD...
	\$(NOECHO) \$(FULLPERLRUN) -I \$(INST_LIB) -I \$(INST_ARCHLIB) -MGlib::GenPod -M\$(NAME) \\
		-e "$docgen_code"

\$(INST_LIB)/\$(FULLEXT)/:
	\$(FULLPERLRUN) -MExtUtils::Command -e mkpath \$@

\$(INST_LIB)/\$(FULLEXT)/index.pod :: \$(INST_LIB)/\$(FULLEXT)/ build/podindex
	\$(NOECHO) \$(ECHO) Creating POD index...
	\$(NOECHO) \$(FULLPERLRUN) -e "print qq(\\n=head1 NAME\\n\\n\$(NAME) \\\\- API Reference Pod Index\\n\\n=head1 PAGES\\n\\n=over\\n\\n)" \\
		> \$(INST_LIB)/\$(FULLEXT)/index.pod
	\$(NOECHO) \$(FULLPERLRUN) -ne "print q(=item L<) . (split q( ))[1] . qq(>\\n\\n);" < build/podindex >> \$(INST_LIB)/\$(FULLEXT)/index.pod
	\$(NOECHO) \$(FULLPERLRUN) -e "print qq(=back\\n\\n);" >> \$(INST_LIB)/\$(FULLEXT)/index.pod
__EOM__
}

=item string = Glib::MakeHelper->postamble_rpms (HASH)

Create and return the text of Makefile rules to manage building RPMs.
You'd put this in your Makefile.PL's MY::postamble.

I<HASH> is a set of search and replace keys for the spec file.  All 
occurrences of @I<key>@ in the spec file template perl-$(DISTNAME).spec.in
will be replaced with I<value>.  'VERSION' and 'SOURCE' are supplied for
you.  For example:

 Glib::MakeHelper->postamble_rpms (
        MYLIB     => 2.0.0, # we can work with anything from this up
        MYLIB_RUN => 2.3.1, # we are actually compiled against this one
        PERL_GLIB => 1.01,  # you must have this version of Glib
 );

will replace @MYLIB@, @MYLIB_RUN@, and @PERL_GLIB@ in spec file.  See
the build setups for Glib and Gtk2 for examples.

Note: This function just returns an empty string on Win32.

=cut

sub postamble_rpms
{
	shift; # package name

	return '' unless $ENV{GPERL_BUILD_RPMS};
	
	my @dirs = qw{$(RPMS_DIR) $(RPMS_DIR)/BUILD $(RPMS_DIR)/RPMS 
		      $(RPMS_DIR)/SOURCES $(RPMS_DIR)/SPECS $(RPMS_DIR)/SRPMS};
	my $cwd = getcwd();
	
	chomp (my $date = `date +"%a %b %d %Y"`);

	my %subs = (
		'VERSION' => '$(VERSION)',
		'SOURCE'  => '$(DISTNAME)-$(VERSION).tar.gz',
		'DATE'    => $date,
		@_,
	);
	
	my $substitute = '$(PERL) -npe \''.join('; ', map {
			"s/\\\@$_\\\@/$subs{$_}/g";
		} keys %subs).'\'';

"

RPMS_DIR=\$(HOME)/rpms

\$(RPMS_DIR)/:
	-mkdir @dirs

SUBSTITUTE=$substitute

perl-\$(DISTNAME).spec :: perl-\$(DISTNAME).spec.in \$(VERSION_FROM) Makefile
	\$(SUBSTITUTE) \$< > \$@

dist-rpms :: Makefile dist perl-\$(DISTNAME).spec \$(RPMS_DIR)/
	cp \$(DISTNAME)-\$(VERSION).tar.gz \$(RPMS_DIR)/SOURCES/
	rpmbuild -ba --define \"_topdir \$(RPMS_DIR)\" perl-\$(DISTNAME).spec

dist-srpms :: Makefile dist perl-\$(DISTNAME).spec \$(RPMS_DIR)/
	cp \$(DISTNAME)-\$(VERSION).tar.gz \$(RPMS_DIR)/SOURCES/
	rpmbuild -bs --nodeps --define \"_topdir \$(RPMS_DIR)\" perl-\$(DISTNAME).spec
";
}

=item string = Glib::MakeHelper->postamble_precompiled_headers (@headers)

Create and return the text of Makefile rules for a 'precompiled-headers' target
that precompiles I<@headers>.  If you call this before you call
C<postamble_clean>, all temporary files will be removed by the 'realclean'
target.

=cut

sub postamble_precompiled_headers
{
	shift; # package name
	my @headers = @_;
	my @precompiled_headers = ();
	my $rules = "";
	foreach my $header (@headers) {
		my $output = $header . '.gch';
		push @precompiled_headers, $output;
		push @ADDITIONAL_FILES_TO_CLEAN, $output;
		$rules .= <<PCH;

$output: $header
	\$(CCCMD) \$(CCCDLFLAGS) "-I\$(PERL_INC)" \$(PASTHRU_DEFINE) \$(DEFINE) $header
PCH
	}
	$rules .= <<PCH;

precompiled-headers: @precompiled_headers
PCH
}

package MY;

=back

=head1 NOTICE

The MakeMaker distributed with perl 5.8.x generates makefiles with a bug that
causes object files to be created in the wrong directory.  There is an override
inserted by this module under the name MY::const_cccmd to fix this issue.

=cut

sub const_cccmd {
	my $inherited = shift->SUPER::const_cccmd (@_);
	return '' unless $inherited;
	require Config;
	# a more sophisticated match may be necessary, but this works for me.
	if ($Config::Config{cc} eq "cl") {
		$inherited .= ' /Fo$@';
	} else {
		$inherited .= ' -o $@';
	}
	$inherited;
}

#
# And, some black magick to help make learn to shut the hell up.
#

sub quiet_rule {
	my $cmds = shift;
	my @lines = split /\n/, $cmds;
	foreach (@lines) {
		if (/NOECHO/) {
			# already quiet
		} elsif (/XSUBPP/) {
			s/^\t/\t\$(NOECHO) \$(ECHO) [ XS \$< ]\n\t\$(NOECHO) /;
		} elsif (/CCCMD/) {
			s/^\t/\t\$(NOECHO) \$(ECHO) [ CC \$< ]\n\t\$(NOECHO) /;
		} elsif (/\bLD\b/) {
			s/^\t/\t\$(NOECHO) \$(ECHO) [ LD \$@ ]\n\t\$(NOECHO) /;
		} elsif (/[_\b]AR\b/) {
			s/^\t/\t\$(NOECHO) \$(ECHO) [ AR \$@ ]\n\t\$(NOECHO) /;
		}
	}
	return join "\n", @lines;
}

sub c_o { return quiet_rule (shift->SUPER::c_o (@_)); }
sub xs_o { return quiet_rule (shift->SUPER::xs_o (@_)); }
sub xs_c { return quiet_rule (shift->SUPER::xs_c (@_)); }
sub dynamic_lib { return quiet_rule (shift->SUPER::dynamic_lib (@_)); }
sub static_lib { return quiet_rule (shift->SUPER::static_lib (@_)); }

1;

=head1 AUTHOR

Ross McFarland E<lt>rwmcfa1 at neces dot comE<gt>

hacked up and documented by muppet.

=head1 COPYRIGHT AND LICENSE

Copyright 2003-2004, 2012 by the gtk2-perl team

This library is free software; you can redistribute it and/or modify
it under the terms of the Lesser General Public License (LGPL).  For 
more information, see http://www.fsf.org/licenses/lgpl.txt

=cut
