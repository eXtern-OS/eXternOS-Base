# fields -- lintian check script (rewrite) -*- perl -*-
#
# Copyright (C) 2004 Marc Brockschmidt
#
# Parts of the code were taken from the old check script, which
# was Copyright (C) 1998 Richard Braakman (also licensed under the
# GPL 2 or higher)
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

package Lintian::fields;
use strict;
use warnings;
use autodie;

use Dpkg::Version qw(version_check);
use List::MoreUtils qw(any true);

use Lintian::Architecture qw(:all);
use Lintian::Data ();
use Lintian::Check qw(check_maintainer);
use Lintian::Relation qw(:constants);
use Lintian::Relation::Version qw(versions_compare);
use Lintian::Tags qw(tag);
use Lintian::Util qw($PKGNAME_REGEX $PKGVERSION_REGEX);

use constant {
    BUILT_USING_REGEX => qr/^$PKGNAME_REGEX \(= $PKGVERSION_REGEX\)$/o,
};

our $KNOWN_ESSENTIAL = Lintian::Data->new('fields/essential');
our $KNOWN_TOOLCHAIN = Lintian::Data->new('fields/toolchain');
our $KNOWN_METAPACKAGES = Lintian::Data->new('fields/metapackages');
our $NO_BUILD_DEPENDS = Lintian::Data->new('fields/no-build-depends');
our $KNOWN_SECTIONS = Lintian::Data->new('fields/archive-sections');
our $known_build_essential
  = Lintian::Data->new('fields/build-essential-packages');
our $KNOWN_BINARY_FIELDS = Lintian::Data->new('fields/binary-fields');
our $KNOWN_UDEB_FIELDS = Lintian::Data->new('fields/udeb-fields');
our $KNOWN_BUILD_PROFILES = Lintian::Data->new('fields/build-profiles');
our $KNOWN_VCS_BROWSERS
  = Lintian::Data->new('fields/vcs-browsers', qr/\s*~~\s*/, sub { $_[1]; });

our %KNOWN_ARCHIVE_PARTS = map { $_ => 1 } ('non-free', 'contrib');

my $KNOWN_PRIOS = Lintian::Data->new('fields/priorities');

our @supported_source_formats = (qr/1\.0/, qr/3\.0\s*\((quilt|native)\)/);

# Still in the archive but shouldn't be the primary Emacs dependency.
our %known_obsolete_emacs = map { $_ => 1 }
  map { $_, $_.'-el', $_.'-gtk', $_.'-nox', $_.'-lucid' }
  qw(emacs21 emacs22 emacs23);

our %known_libstdcs = map { $_ => 1 } (
    'libstdc++2.9-glibc2.1', 'libstdc++2.10',
    'libstdc++2.10-glibc2.2','libstdc++3',
    'libstdc++3.0', 'libstdc++4',
    'libstdc++5','libstdc++6',
    'lib64stdc++6',
);

our %known_tcls = map { $_ => 1 }
  ('tcl74', 'tcl8.0', 'tcl8.2', 'tcl8.3', 'tcl8.4', 'tcl8.5',);

our %known_tclxs
  = map { $_ => 1 } ('tclx76', 'tclx8.0.4', 'tclx8.2', 'tclx8.3', 'tclx8.4',);

our %known_tks
  = map { $_ => 1 } ('tk40', 'tk8.0', 'tk8.2', 'tk8.3', 'tk8.4', 'tk8.5',);

our %known_libpngs = map { $_ => 1 } ('libpng12-0', 'libpng2', 'libpng3',);

our @known_java_pkg = map { qr/$_/ } (
    'default-j(?:re|dk)(?:-headless)?',
    # java-runtime and javaX-runtime alternatives (virtual)
    'java\d*-runtime(?:-headless)?',
    # openjdk-X and sun-javaX
    '(openjdk-|sun-java)\d+-j(?:re|dk)(?:-headless)?',
    'gcj-(?:\d+\.\d+-)?jre(?:-headless)?', 'gcj-(?:\d+\.\d+-)?jdk', # gcj
    'gij',
    'java-gcj-compat(?:-dev|-headless)?', # deprecated/transitional packages
    'kaffe', 'cacao', 'jamvm',
    'classpath', # deprecated packages (removed in Squeeze)
);

# Mapping of package names to section names
my $NAME_SECTION_MAPPINGS = Lintian::Data->new(
    'fields/name_section_mappings',
    qr/\s*=>\s*/,
    sub {
        return {'regex' =>  qr/$_[0]/x, 'section' => $_[1]};
    });

our $DH_ADDONS = Lintian::Data->new('common/dh_addons', '=');
our %DH_ADDONS_VALUES = map { $DH_ADDONS->value($_) => 1 } $DH_ADDONS->all;

my %VCS_EXTRACT = (
    browser => sub { return @_;},
    arch    => sub { return @_;},
    bzr     => sub { return @_;},
    # cvs rootdir followed by optional module name:
    cvs     => sub { return shift =~ /^(.+?)(?:\s+(\S*))?$/;},
    darcs   => sub { return @_;},
    hg      => sub { return @_;},
    # git uri followed by optional " -b " + branchname:
    git     => sub { return shift =~ /^(.+?)(?:\s+-b\s+(\S*))?$/;},
    svn     => sub { return @_;},
    # New "mtn://host?branch" uri or deprecated "host branch".
    mtn     => sub { return shift =~ /^(.+?)(?:\s+\S+)?$/;},
);
my %VCS_CANONIFY = (
    browser => sub {
        $_[0] =~ s{https?://svn\.debian\.org/wsvn/}
                  {https://anonscm.debian.org/viewvc/};
        $_[0] =~ s{https?\Q://git.debian.org/?p=\E}
                  {https://anonscm.debian.org/git/};
        $_[0] =~ s{https?\Q://bzr.debian.org/loggerhead/\E}
                  {https://anonscm.debian.org/loggerhead/};
        $_[0] =~ s{https?\Q://salsa.debian.org/\E([^/]+/[^/]+)\.git/?$}
                  {https://salsa.debian.org/$1};

        if ($_[0] =~ m{https?\Q://anonscm.debian.org/viewvc/\E}xsm) {
            if ($_[0] =~ s{\?(.*[;\&])?op=log(?:[;\&](.*))?\Z}{}xsm) {
                my (@keep) = ($1, $2, $3);
                my $final = join('', grep {defined} @keep);
                $_[0] .= '?' . $final if ($final ne '');
                $_[1] = 'vcs-field-bitrotted';
            }
        }
    },
    cvs      => sub {
        if (
            $_[0] =~ s{\@(?:cvs\.alioth|anonscm)\.debian\.org:/cvsroot/}
                      {\@anonscm.debian.org:/cvs/}
          ) {
            $_[1] = 'vcs-field-bitrotted';
        }
        $_[0]=~ s{\@\Qcvs.alioth.debian.org:/cvs/}{\@anonscm.debian.org:/cvs/};
    },
    arch     => sub {
        $_[0] =~ s{https?\Q://arch.debian.org/arch/\E}
                  {https://anonscm.debian.org/arch/};
    },
    bzr     => sub {
        $_[0] =~ s{https?\Q://bzr.debian.org/\E}
                  {https://anonscm.debian.org/bzr/};
        $_[0] =~ s{https?\Q://anonscm.debian.org/bzr/bzr/\E}
                  {https://anonscm.debian.org/bzr/};
    },
    git     => sub {
        if (
            $_[0] =~ s{git://(?:git|anonscm)\.debian\.org/~}
                      {https://anonscm.debian.org/git/users/}
          ) {
            $_[1] = 'vcs-git-uses-invalid-user-uri';
        }
        $_[0] =~ s{https?\Q://git.debian.org/\E(?:git/?)?}
                  {https://anonscm.debian.org/git/};
        $_[0] =~ s{https?\Q://anonscm.debian.org/git/git/\E}
                  {https://anonscm.debian.org/git/};
        $_[0] =~ s{\Qgit://git.debian.org/\E(?:git/?)?}
                  {https://anonscm.debian.org/git/};
        $_[0] =~ s{\Qgit://anonscm.debian.org/git/\E}
                  {https://anonscm.debian.org/git/};
        $_[0] =~ s{https?\Q://salsa.debian.org/\E([^/]+/[^/\.]+)(?!\.git)$}
                  {https://salsa.debian.org/$1.git};
    },
    hg      => sub {
        $_[0] =~ s{https?\Q://hg.debian.org/\E}
                  {https://anonscm.debian.org/hg/};
        $_[0] =~ s{https?\Q://anonscm.debian.org/hg/hg/\E}
                  {https://anonscm.debian.org/hg/};
    },
    svn     => sub {
        $_[0] =~ s{\Qsvn://cvs.alioth.debian.org/\E}
                  {svn://anonscm.debian.org/};
        $_[0] =~ s{\Qsvn://svn.debian.org/\E}
                  {svn://anonscm.debian.org/};
        $_[0] =~ s{\Qsvn://anonscm.debian.org/svn/\E}
                  {svn://anonscm.debian.org/};
    },
);
# Valid URI formats for the Vcs-* fields
# currently only checks the protocol, not the actual format of the URI
my %VCS_RECOMMENDED_URIS = (
    browser => qr;^https?://;,
    arch    => qr;^https?://;,
    bzr     => qr;^(?:lp:|(?:nosmart\+)?https?://);,
    cvs     => qr;^:(?:pserver:|ext:_?anoncvs);,
    darcs   => qr;^https?://;,
    hg      => qr;^https?://;,
    git     => qr;^(?:git|https?|rsync)://;,
    svn     => qr;^(?:svn|(?:svn\+)?https?)://;,
    mtn     => qr;^mtn://;,
);
my %VCS_VALID_URIS = (
    arch    => qr;^https?://;,
    bzr     => qr;^(?:sftp|(?:bzr\+)?ssh)://;,
    cvs     => qr;^(?:-d\s*)?:(?:ext|pserver):;,
    hg      => qr;^ssh://;,
    git     => qr;^(?:git\+)?ssh://|^[\w.]+@[a-zA-Z0-9.]+:[/a-zA-Z0-9.];,
    svn     => qr;^(?:svn\+)?ssh://;,
    mtn     => qr;^[\w.-]+$;,
);

# Python development packages that are used almost always just for building
# architecture-dependent modules.  Used to check for unnecessary build
# dependencies for architecture-independent source packages.
our $PYTHON_DEV = join(' | ',
    qw(python-dev python-all-dev python3-dev python3-all-dev),
    map { "python$_-dev" } qw(2.7 3 3.4 3.5));

our $PERL_CORE_PROVIDES = Lintian::Data->new('fields/perl-provides', '\s+');
our $OBSOLETE_PACKAGES
  = Lintian::Data->new('fields/obsolete-packages',qr/\s*=>\s*/);
our $VIRTUAL_PACKAGES   = Lintian::Data->new('fields/virtual-packages');
our $SOURCE_FIELDS      = Lintian::Data->new('common/source-fields');
our $MAIL_TRANSPORT_AGENTS= Lintian::Data->new('fields/mail-transport-agents');

sub run {
    my ($pkg, $type, $info, $proc, $group) = @_;
    my ($version, $arch_indep);

    #---- Format

    if ($type eq 'source') {
        if (defined(my $format = $info->field('format'))) {
            my $supported = 0;
            foreach my $f (@supported_source_formats){
                if($format =~ /^\s*$f\s*\z/){
                    $supported = 1;
                }
            }
            tag 'unsupported-source-format', $format
              unless $supported;
        }
    }

    #---- Package

    if ($type eq 'binary') {
        if (not defined $info->field('package')) {
            tag 'no-package-name';
        } else {
            my $name = $info->field('package');

            unfold('package', \$name);
            tag 'bad-package-name' unless $name =~ /^$PKGNAME_REGEX$/i;
            tag 'package-not-lowercase' if ($name =~ /[A-Z]/);
            tag 'unusual-documentation-package-name' if $name =~ /-docs$/;
        }
    }

    #---- Version

    if (not defined $info->field('version')) {
        tag 'no-version-field';
    } else {
        $version = $info->field('version');

        unfold('version', \$version);
        my $dversion = Dpkg::Version->new($version);

        if ($dversion->is_valid) {
            my ($epoch, $upstream, $debian)
              = ($dversion->epoch, $dversion->version, $dversion->revision);
            # Dpkg::Version sets the debian revision to 0 if there is
            # no revision.  So we need to check if the raw version
            # ends with "-0".
            tag 'debian-revision-should-not-be-zero', $version
              if $version =~ m/-0$/o;
            my $ubuntu;
            if($debian =~ m/^(?:[^.]+)(?:\.[^.]+)?(?:\.[^.]+)?(\..*)?$/o){
                my $extra = $1;
                if (
                    defined $extra
                    && $debian =~ m/\A
                            (?:[^.]+ubuntu[^.]+)(?:\.\d+){1,3}(\..*)?
                    \Z/oxsm
                  ) {
                    $ubuntu = 1;
                    $extra = $1;
                }
                if (defined $extra) {
                    tag 'debian-revision-not-well-formed', $version;
                }
            } else {
                tag 'debian-revision-not-well-formed', $version;
            }
            if ($debian =~ /^[^.-]+\.[^.-]+\./o and not $ubuntu) {
                tag 'binary-nmu-debian-revision-in-source', $version
                  if $type eq 'source';
            }
            if ($version =~ /\+b\d+$/ && $type eq 'source') {
                tag 'binary-nmu-debian-revision-in-source', $version;
            }
            if (
                $upstream =~ m/[^~a-z]
                    (rc|alpha|beta|pre(?:view|release)?)
                   ([^a-z].*|\Z)
                 /xsm
              ) {
                my $expected = $upstream;
                my $rc = $1;
                my $rest = $2//'';
                my $suggestion;
                # Remove the rc-part and the preceding symbol (if any).
                $expected =~ s/[\.\+\-\:]?\Q$rc\E.*//;
                $suggestion = "$expected~$rc$rest";
                tag 'rc-version-greater-than-expected-version', $upstream, '>',
                  $expected, "(consider using $suggestion)",
                  if $info->native
                  or ($debian eq q{1} or $debian =~ m,^0(?:\.1|ubuntu1)?$,);
            }

            # Checks for the dfsg convention for repackaged upstream
            # source.  Only check these against the source package to not
            # repeat ourselves too much.
            if ($type eq 'source') {
                if ($version =~ /dfsg/ and $info->native) {
                    tag 'dfsg-version-in-native-package', $version;
                } elsif ($version =~ /\.dfsg/) {
                    tag 'dfsg-version-with-period', $version;
                } elsif ($version =~ /dsfg/) {
                    tag 'dfsg-version-misspelled', $version;
                }
            }

            my $name = $info->field('package');
            if (   $name
                && $PERL_CORE_PROVIDES->known($name)
                && perl_core_has_version($name, '>=', "$epoch:$upstream")) {
                my $core_version = $PERL_CORE_PROVIDES->value($name);
                tag 'package-superseded-by-perl', "with $core_version";
            }
        } else {
            tag 'bad-version-number', $version;
        }
    }

    #---- Multi-Arch

    if (defined(my $march = $info->field('multi-arch'))){
        unfold('multi-arch', \$march);
        tag 'unknown-multi-arch-value', $pkg, $march
          unless $march =~ m/^(?:no|foreign|allowed|same)$/o;
        if (   $march eq 'same'
            && $type eq 'binary'
            && defined $info->field('architecture')) {
            my $arch = $info->field('architecture');
            # Do not use unfold to avoid duplicate warning
            $arch =~ s/\n//o;
            tag 'illegal-multi-arch-value', $arch, $march if ($arch eq 'all');
        }

    }

    if ($type eq 'source') {
        for my $bin ($info->binaries) {
            my $arch = $info->binary_field($bin, 'architecture');
            my $fname = "debian/$bin.lintian-overrides.$arch";
            next unless $info->binary_field($bin, 'multi-arch', '') eq 'same';
            tag 'multi-arch-same-package-has-arch-specific-overrides', $fname
              if $info->index_resolved_path($fname);
        }
    }

    if ($type eq 'binary'){
        if ($pkg =~ /^x?fonts-/) {
            tag 'font-package-not-multi-arch-foreign'
              unless $info->field('multi-arch', 'no')
              =~ m/^(?:foreign|allowed)$/o;
        }
    }

    #---- Architecture

    if (not defined $info->field('architecture')) {
        tag 'no-architecture-field';
    } else {
        my $archs = $info->field('architecture');
        unfold('architecture', \$archs);

        my @archs = split(m/ /o, $archs);
        if (@archs > 1) { # Check for magic architecture combinations.
            my %archmap;
            my $magic = 0;
            $archmap{$_}++ for (@archs);
            $magic++ if ($type ne 'source' && $archmap{'all'});
            if ($archmap{'any'}){
                delete $archmap{'any'};
                # Allow 'all' to be present in source packages as well
                # (#626775)
                delete $archmap{'all'} if $type eq 'source';
                $magic++ if %archmap;
            }
            tag 'magic-arch-in-arch-list' if $magic;
        }
        for my $arch (@archs) {
            tag 'unknown-architecture', $arch
              unless is_arch_or_wildcard($arch);
            tag 'arch-wildcard-in-binary-package', $arch
              if ($type eq 'binary' && is_arch_wildcard($arch));
        }

        if ($type eq 'binary') {
            tag 'too-many-architectures' if (@archs > 1);
            if (@archs > 0) {
                tag 'aspell-package-not-arch-all'
                  if ( $pkg =~ /^aspell-[a-z]{2}(?:-.*)?$/
                    && $archs[0] ne 'all');
                if ($pkg =~ /-docs?$/ && $archs[0] ne 'all') {
                    tag 'documentation-package-not-architecture-independent';
                }
            }
        }
        # Used for later tests.
        $arch_indep = 1 if (@archs == 1 && $archs[0] eq 'all');
    }

    #---- Subarchitecture (udeb)

    if (defined(my $subarch = $info->field('subarchitecture'))) {
        unfold('subarchitecture', \$subarch);
    }

    #---- Maintainer
    #---- Uploaders

    my $is_comaintained = 0;
    for my $f (qw(maintainer uploaders)) {
        if (not defined $info->field($f)) {
            tag 'no-maintainer-field' if $f eq 'maintainer';
        } else {
            my $maintainer = $info->field($f);

            my $is_list = $maintainer =~ /\@lists(?:\.alioth)?\.debian\.org\b/;
            $is_comaintained = 1 if $is_list;

            # Note, not expected to hit on uploaders anymore, as dpkg
            # now strips newlines for the .dsc, and the newlines don't
            # hurt in debian/control
            unfold($f, \$maintainer);

            if ($f eq 'uploaders') {
                # check for empty field see  #783628
                if($maintainer =~ m/,\s*,/) {
                    tag 'uploader-name-missing','you have used a double comma';
                    $maintainer =~ s/,\s*,/,/g;
                }
                my %duplicate_uploaders;
                my @uploaders = map { split /\@\S+\K\s*,\s*/ }
                  split />\K\s*,\s*/, $maintainer;
                for my $uploader (@uploaders) {
                    $is_comaintained = 1;
                    check_maintainer($uploader, 'uploader');
                    if (   ((true { $_ eq $uploader } @uploaders) > 1)
                        and($duplicate_uploaders{$uploader}++ == 0)) {
                        tag 'duplicate-uploader', $uploader;
                    }
                }
            } else {
                check_maintainer($maintainer, $f);
                if (   $type eq 'source'
                    && $is_list
                    && !defined $info->field('uploaders')) {
                    tag 'no-human-maintainers';
                }
            }
        }
    }

    if (   defined $info->field('uploaders')
        && defined $info->field('maintainer')) {
        my $maint = $info->field('maintainer');
        tag 'maintainer-also-in-uploaders'
          if $info->field('uploaders') =~ m/\Q$maint/;
    }

    #---- Source

    # Optional in binary packages, required in source packages, but we
    # cannot check it as dpkg-source(1) refuses to unpack source packages
    # without this field (and fields indirectly depends on unpacked)...
    if (defined(my $source = $info->field('source'))) {
        unfold('source', \$source);

        if ($type eq 'source') {
            my $filename = $proc->pkg_path;
            my ($base) = ($filename =~ m,(?:\a|/)([^/]+)$,o);
            my ($n) = ($base =~ m/^([^_]+)_/o);

            if ($source ne $n) {
                tag 'source-field-does-not-match-pkg-name', "$source != $n";
            }
            if ($source !~ /^[a-z0-9][-+\.a-z0-9]+\z/) {
                tag 'source-field-malformed', $source;
            }
        } elsif (
            $source !~ /^ $PKGNAME_REGEX
            \s*
            # Optional Version e.g. (1.0)
            (?:\((?:\d+:)?(?:[-\.+:a-zA-Z0-9~]+?)(?:-[\.+a-zA-Z0-9~]+)?\))?\s*$/x
          ) {
            tag 'source-field-malformed', $source;
        }
    }

    #---- Essential

    if (defined(my $essential = $info->field('essential'))) {
        unfold('essential', \$essential);

        tag 'essential-in-source-package' if ($type eq 'source');
        tag 'essential-no-not-needed' if ($essential eq 'no');
        tag 'unknown-essential-value'
          if ($essential ne 'no' and $essential ne 'yes');
        if ($essential eq 'yes' and not $KNOWN_ESSENTIAL->known($pkg)) {
            tag 'new-essential-package';
        }
    }

    #---- Section

    if (not defined $info->field('section')) {
        tag 'no-section-field' if ($type eq 'binary');
    } else {
        my $section = $info->field('section');

        unfold('section', \$section);

        if ($section eq '') {
            tag 'empty-section-field';
        } elsif ($type eq 'udeb') {
            unless ($section eq 'debian-installer') {
                tag 'wrong-section-for-udeb', $section;
            }
        } else {
            my @parts = split(m{/}, $section, 2);

            if (scalar @parts > 1) {
                tag 'unknown-section', $section
                  unless $KNOWN_ARCHIVE_PARTS{$parts[0]};
                tag 'unknown-section', $section
                  unless $KNOWN_SECTIONS->known($parts[1]);
            } elsif ($parts[0] eq 'unknown') {
                tag 'section-is-dh_make-template';
            } else {
                tag 'unknown-section', $section
                  unless $KNOWN_SECTIONS->known($parts[0]);
            }

            # Check package name <-> section.  oldlibs is a special case; let
            # anything go there.
            if ($parts[-1] ne 'oldlibs') {
                foreach my $name_section ($NAME_SECTION_MAPPINGS->all()) {
                    my $regex = $NAME_SECTION_MAPPINGS->value($name_section)
                      ->{'regex'};
                    my $section = $NAME_SECTION_MAPPINGS->value($name_section)
                      ->{'section'};
                    next unless ($pkg =~ m{$regex});

                    my $area = '';
                    $area = "$parts[0]/" if (scalar @parts == 2);
                    tag 'wrong-section-according-to-package-name',
                      "$pkg => ${area}$section"
                      unless $parts[-1] eq $section;
                    last;
                }
            }
            if ($parts[-1] eq 'debug') {
                if($pkg !~ /-dbg(?:sym)?$/) {
                    tag 'wrong-section-according-to-package-name',"$pkg";
                }
            }
            if ($info->is_pkg_class('transitional')) {
                my $pri = $info->field('priority', '');
                # Cannot use "unfold" as it could emit a tag for priority,
                # which will be duplicated below.
                $pri =~ s/\n//;
                tag 'transitional-package-should-be-oldlibs-optional',
                  "$parts[-1]/$pri"
                  unless $pri eq 'optional' && $parts[-1] eq 'oldlibs';
            }
        }
    }

    #---- Priority

    if (not defined $info->field('priority')) {
        tag 'no-priority-field' if $type eq 'binary';
    } else {
        my $priority = $info->field('priority');

        unfold('priority', \$priority);

        if ($priority eq 'extra') {
            tag 'priority-extra-is-replaced-by-priority-optional'
              if $type eq 'source'
              or not $info->is_pkg_class('auto-generated');
            # Re-map to optional to avoid an additional warning from
            # lintian
            $priority = 'optional';
        }

        tag 'unknown-priority', $priority
          unless $KNOWN_PRIOS->known($priority);

        tag 'excessive-priority-for-library-package', $priority
          if $pkg =~ m/^lib/o
          and $pkg !~ m/-bin$/o
          and $pkg !~ m/^libc[0-9.]+$/o
          and any { $_ eq $info->field('section', '') } qw(libdevel libs)
          and any { $_ eq $priority } qw(required important standard);
    }

    #---- Standards-Version
    # handled in checks/standards-version

    #---- Description
    # handled in checks/description

    #--- Homepage

    if (defined(my $homepage = $info->field('homepage'))) {
        my $orig = $homepage;

        unfold('homepage', \$homepage);

        if ($homepage =~ /^<(?:UR[LI]:)?.*>$/i) {
            tag 'superfluous-clutter-in-homepage', $orig;
            $homepage = substr($homepage, 1, length($homepage) - 2);
        }

        require URI;
        my $uri = URI->new($homepage);

        # not an absolute URI or (most likely) an invalid protocol
        unless ($uri->scheme && $uri->scheme =~ m/^(?:ftp|https?|gopher)$/o) {
            tag 'bad-homepage', $orig;
        }

        if ($homepage=~ m,/(?:search\.cpan\.org|metacpan\.org)/.*-[0-9._]+/*$,)
        {
            tag 'homepage-for-cpan-package-contains-version', $orig;
        }
        if ($homepage=~ m,/cran\.r-project\.org/web/packages/.+,){
            tag 'homepage-for-cran-package-not-canonical', $orig;
        }
        if ($homepage=~ m,bioconductor\.org/packages/.*/bioc/html/.*\.html*$,){
            tag 'homepage-for-bioconductor-package-not-canonical', $orig;
        }
        if (   $homepage =~ m,^ftp://,
            or $homepage
            =~m,^http://(?:[^\.]+\.)?(?:github\.com|metacpan\.org|debian\.org|cran\.r-project\.org|bioconductor\.org)/,
          ){
            tag 'homepage-field-uses-insecure-uri', $orig;
        }
    } elsif (not $info->native) {
        if ($type eq 'source') {
            my $binary_has_homepage_field = 0;
            for my $binary ($info->binaries) {
                if (defined $info->binary_field($binary, 'homepage')) {
                    $binary_has_homepage_field = 1;
                    last;
                }
            }
            if ($binary_has_homepage_field) {
                tag 'homepage-in-binary-package';
            } else {
                tag 'no-homepage-field';
            }
        }
    }

    #---- Installer-Menu-Item (udeb)

    if (defined(my $menu_item = $info->field('installer-menu-item'))) {
        unfold('installer-menu-item', \$menu_item);

        $menu_item =~ /^\d+$/ or tag 'bad-menu-item', $menu_item;
    }

    #---- Package relations (binary package)

    # Check whether the package looks like a metapackage, used for later
    # dependency checks.  We consider a package to possibly be a metapackage if
    # it is a binary package with no files outside of /usr/share/doc and a few
    # other directories found in metapackages.  This also catches documentation
    # packages, but that doesn't matter for our purposes.
    my $metapackage = 0;
    if ($type eq 'binary') {
        $metapackage = 1;
        for my $file ($info->sorted_index) {
            next if $file->is_dir;
            next if $file =~ m%^usr/share/doc/%;
            next if $file =~ m%^usr/share/lintian/overrides/%;
            next if $file =~ m%^usr/share/cdd/%;
            $metapackage = 0;
            last;
        }

        # Packages we say are metapackages are always metapackages even if
        # they don't look like it.
        $metapackage = 1 if $KNOWN_METAPACKAGES->known($pkg);
    }
    if (($type eq 'binary') || ($type eq 'udeb')) {
        my $javalib = 0;
        my $replaces = $info->relation('replaces');
        my %nag_once;
        $javalib = 1 if($pkg =~ m/^lib.*-java$/o);
        for my $field (
            qw(depends pre-depends recommends suggests conflicts provides enhances replaces breaks)
          ) {
            next unless defined $info->field($field);
            #Get data and clean it
            my $data = $info->field($field);
            my $javadep = 0;
            unfold($field, \$data);

            my (
                @seen_libstdcs, @seen_tcls, @seen_tclxs,
                @seen_tks, @seen_libpngs
            );

            my $is_dep_field = sub {
                any { $_ eq $_[0] }qw(depends pre-depends recommends suggests);
            };

            tag 'alternates-not-allowed', $field
              if ($data =~ /\|/ && !&$is_dep_field($field));
            check_field($info, $field, $data) if &$is_dep_field($field);

            for my $dep (split /\s*,\s*/, $data) {
                my (@alternatives, @seen_obsolete_packages);
                push @alternatives, [_split_dep($_), $_]
                  for (split /\s*\|\s*/, $dep);

                if (&$is_dep_field($field)) {
                    push @seen_libstdcs, $alternatives[0][0]
                      if defined $known_libstdcs{$alternatives[0][0]};
                    push @seen_tcls, $alternatives[0][0]
                      if defined $known_tcls{$alternatives[0][0]};
                    push @seen_tclxs, $alternatives[0][0]
                      if defined $known_tclxs{$alternatives[0][0]};
                    push @seen_tks, $alternatives[0][0]
                      if defined $known_tks{$alternatives[0][0]};
                    push @seen_libpngs, $alternatives[0][0]
                      if defined $known_libpngs{$alternatives[0][0]};
                }

                # Only for (Pre-)?Depends.
                tag 'virtual-package-depends-without-real-package-depends',
                  "$field: $alternatives[0][0]"
                  if (
                       $VIRTUAL_PACKAGES->known($alternatives[0][0])
                    && ($field eq 'depends' || $field eq 'pre-depends')
                    && ($pkg ne 'base-files' || $alternatives[0][0] ne 'awk')
                    # ignore phpapi- dependencies as adding an
                    # alternative, real, package breaks its purpose
                    && $alternatives[0][0] !~ m/^phpapi-/
                  );

                # Check defaults for transitions.  Here, we only care
                # that the first alternative is current.
                tag 'depends-on-old-emacs', "$field: $alternatives[0][0]"
                  if ( &$is_dep_field($field)
                    && $known_obsolete_emacs{$alternatives[0][0]});

                tag 'depends-on-mail-transport-agent-without-alternatives',
                  $dep
                  if &$is_dep_field($field)
                  and $MAIL_TRANSPORT_AGENTS->known($dep);

                for my $part_d (@alternatives) {
                    my ($d_pkg, undef, $d_version, undef, undef, $rest,
                        $part_d_orig)
                      = @$part_d;

                    tag 'invalid-versioned-provides', $part_d_orig
                      if ( $field eq 'provides'
                        && $d_version->[0]
                        && $d_version->[0] ne '=');

                    tag 'bad-provided-package-name', $d_pkg
                      if $d_pkg !~ /^[a-z0-9][-+\.a-z0-9]+$/;

                    tag 'breaks-without-version', $part_d_orig
                      if ( $field eq 'breaks'
                        && !$d_version->[0]
                        && !$VIRTUAL_PACKAGES->known($d_pkg)
                        && !$replaces->implies($part_d_orig));

                    tag 'conflicts-with-version', $part_d_orig
                      if ($field eq 'conflicts' && $d_version->[0]);

                    tag 'obsolete-relation-form', "$field: $part_d_orig"
                      if (
                        $d_version && any { $d_version->[0] eq $_ }
                        ('<', '>'));

                    tag 'bad-version-in-relation', "$field: $part_d_orig"
                      if ($d_version->[0] && !version_check($d_version->[1]));

                    tag 'package-relation-with-self', "$field: $part_d_orig"
                      if ($pkg eq $d_pkg)
                      && ( $field ne 'conflicts'
                        && $field ne 'replaces'
                        && $field ne 'provides');

                    tag 'bad-relation', "$field: $part_d_orig"
                      if $rest;

                    push @seen_obsolete_packages, [$part_d_orig, $d_pkg]
                      if ( $OBSOLETE_PACKAGES->known($d_pkg)
                        && &$is_dep_field($field));

                    tag 'depends-on-metapackage', "$field: $part_d_orig"
                      if (  $KNOWN_METAPACKAGES->known($d_pkg)
                        and not $metapackage
                        and &$is_dep_field($field));

                    # diffutils is a special case since diff was
                    # renamed to diffutils, so a dependency on
                    # diffutils effectively is a versioned one.
                    tag 'depends-on-essential-package-without-using-version',
                      "$field: $part_d_orig"
                      if ( $KNOWN_ESSENTIAL->known($d_pkg)
                        && !$d_version->[0]
                        && &$is_dep_field($field)
                        && $d_pkg ne 'diffutils'
                        && $d_pkg ne 'dash');

                    tag 'package-depends-on-an-x-font-package',
                      "$field: $part_d_orig"
                      if ( $field =~ /^(?:pre-)?depends$/
                        && $d_pkg =~ /^xfont.*/
                        && $d_pkg ne 'xfonts-utils'
                        && $d_pkg ne 'xfonts-encodings');

                    tag 'depends-on-packaging-dev',
                      $field
                      if ((
                               $field =~ /^(?:pre-)?depends$/
                            || $field eq 'recommends'
                        )
                        && $d_pkg eq 'packaging-dev'
                        && !$info->is_pkg_class('any-meta'));

                    tag 'needless-suggest-recommend-libservlet-java', "$d_pkg"
                      if (($field eq 'recommends' || $field eq 'suggests')
                        && $d_pkg =~ m/libservlet[\d\.]+-java/);

                    tag 'needlessly-depends-on-awk', $field
                      if ( $d_pkg eq 'awk'
                        && !$d_version->[0]
                        && &$is_dep_field($field)
                        && $pkg ne 'base-files');

                    tag 'depends-on-libdb1-compat', $field
                      if ( $d_pkg eq 'libdb1-compat'
                        && $pkg !~ /^libc(?:6|6.1|0.3)/
                        && $field =~ m/^(?:pre-)?depends$/o);

                    tag 'depends-on-python-minimal', $field,
                      if ( $d_pkg =~ /^python[\d.]*-minimal$/
                        && &$is_dep_field($field)
                        && $pkg !~ /^python[\d.]*-minimal$/);

                    tag 'doc-package-depends-on-main-package', $field
                      if ("$d_pkg-doc" eq $pkg
                        && $field =~ /^(?:pre-)?depends$/);

                    # only trigger this for the preferred alternative
                    tag 'versioned-dependency-satisfied-by-perl',
                      "$field: $part_d_orig"
                      if $alternatives[0][-1] eq $part_d_orig
                      && &$is_dep_field($field)
                      && perl_core_has_version($d_pkg, $d_version->[0],
                        $d_version->[1]);

                    tag 'package-relation-with-perl-modules', "$field: $d_pkg"
                      # matches "perl-modules" (<= 5.20) as well as
                      # perl-modules-5.xx (>> 5.20)
                      if $d_pkg =~ /^perl-modules/
                      && $field ne 'replaces'
                      && $proc->pkg_src ne 'perl';

                    tag 'depends-exclusively-on-makedev', $field,
                      if ( $field eq 'depends'
                        && $d_pkg eq 'makedev'
                        && @alternatives == 1);

                    tag 'lib-recommends-documentation', "$field: $part_d_orig"
                      if ( $field eq 'recommends'
                        && $pkg =~ m/^lib/
                        && $pkg !~ m/-(?:dev|docs?|tools|bin)$/
                        && $part_d_orig =~ m/-docs?$/);

                    tag 'binary-package-depends-on-toolchain-package',
                      "$field: $part_d_orig"
                      if $KNOWN_TOOLCHAIN->known($d_pkg)
                      and not $pkg =~ m/^dh-/
                      and not $pkg =~ m/-(source|src)$/
                      and not $DH_ADDONS_VALUES{$pkg};

                    # default-jdk-doc must depend on openjdk-X-doc (or
                    # classpath-doc) to be useful; other packages
                    # should depend on default-jdk-doc if they want
                    # the Java Core API.
                    tag 'depends-on-specific-java-doc-package',
                      $field
                      if (
                           &$is_dep_field($field)
                        && $pkg ne 'default-jdk-doc'
                        && (   $d_pkg eq 'classpath-doc'
                            || $d_pkg =~ m/openjdk-\d+-doc/o));

                    if ($javalib && $field eq 'depends'){
                        foreach my $reg (@known_java_pkg){
                            if($d_pkg =~ m/$reg/){
                                $javadep++;
                                last;
                            }

                        }
                    }
                }

                for my $d (@seen_obsolete_packages) {
                    my ($dep, $pkg_name) = @{$d};
                    my $replacement = $OBSOLETE_PACKAGES->value($pkg_name)
                      // '';
                    $replacement = ' => ' . $replacement
                      if $replacement ne '';
                    if ($pkg_name eq $alternatives[0][0]
                        or scalar @seen_obsolete_packages
                        == scalar @alternatives) {
                        tag 'depends-on-obsolete-package',
                          "$field: $dep${replacement}";
                    } else {
                        tag 'ored-depends-on-obsolete-package',
                          "$field: $dep${replacement}";
                    }
                }

                # Only emit the tag if all the alternatives are
                # JVM/JRE/JDKs
                # - assume that <some-lib> | openjdk-X-jre-headless
                #   makes sense for now.
                if (scalar(@alternatives) == $javadep
                    && !exists $nag_once{'needless-dependency-on-jre'}){
                    $nag_once{'needless-dependency-on-jre'} = 1;
                    tag 'needless-dependency-on-jre';
                }
            }
            tag 'package-depends-on-multiple-libstdc-versions', @seen_libstdcs
              if (scalar @seen_libstdcs > 1);
            tag 'package-depends-on-multiple-tcl-versions', @seen_tcls
              if (scalar @seen_tcls > 1);
            tag 'package-depends-on-multiple-tclx-versions', @seen_tclxs
              if (scalar @seen_tclxs > 1);
            tag 'package-depends-on-multiple-tk-versions', @seen_tks
              if (scalar @seen_tks > 1);
            tag 'package-depends-on-multiple-libpng-versions', @seen_libpngs
              if (scalar @seen_libpngs > 1);
        }

        # If Conflicts or Breaks is set, make sure it's not inconsistent with
        # the other dependency fields.
        for my $conflict (qw/conflicts breaks/) {
            next unless $info->field($conflict);
            for my $field (qw(depends pre-depends recommends suggests)) {
                next unless $info->field($field);
                my $relation = $info->relation($field);
                for my $package (split /\s*,\s*/, $info->field($conflict)) {
                    tag 'conflicts-with-dependency', $field, $package
                      if $relation->implies($package);
                }
            }
        }
    }

    #---- Built-Using
    if (defined(my $built_using = $info->field('built-using'))) {
        my $built_using_rel = Lintian::Relation->new($built_using);
        $built_using_rel->visit(
            sub {
                if ($_ !~ BUILT_USING_REGEX) {
                    tag 'invalid-value-in-built-using-field', $_;
                    return 1;
                }
                return 0;
            },
            VISIT_OR_CLAUSE_FULL | VISIT_STOP_FIRST_MATCH
        );

    }

    #---- Package relations (source package)

    if ($type eq 'source') {
        my @binpkgs = $info->binaries;

        #Get number of arch-indep packages:
        my $arch_indep_packages = 0;
        my $arch_dep_packages = 0;
        foreach my $binpkg (@binpkgs) {
            my $arch = $info->binary_field($binpkg, 'architecture', '');
            if ($arch eq 'all') {
                $arch_indep_packages++;
            } else {
                $arch_dep_packages++;
            }
        }

        tag 'build-depends-indep-without-arch-indep'
          if (defined $info->field('build-depends-indep')
            && $arch_indep_packages == 0);
        tag 'build-depends-arch-without-arch-dependent-binary'
          if (defined $info->field('build-depends-arch')
            && $arch_dep_packages == 0);

        my $is_dep_field = sub {
            any { $_ eq $_[0] }
            qw(build-depends build-depends-indep build-depends-arch);
        };

        my %depend;
        for my $field (
            qw(build-depends build-depends-indep build-depends-arch build-conflicts build-conflicts-indep build-conflicts-arch)
          ) {
            if (defined $info->field($field)) {
                #Get data and clean it
                my $data = $info->field($field);
                unfold($field, \$data);
                check_field($info, $field, $data);
                $depend{$field} = $data;

                for my $dep (split /\s*,\s*/, $data) {
                    my (@alternatives, @seen_obsolete_packages);
                    push @alternatives, [_split_dep($_), $_]
                      for (split /\s*\|\s*/, $dep);

                    tag 'virtual-package-depends-without-real-package-depends',
                      "$field: $alternatives[0][0]"
                      if ( $VIRTUAL_PACKAGES->known($alternatives[0][0])
                        && &$is_dep_field($field));

                    for my $part_d (@alternatives) {
                        my ($d_pkg, undef, $d_version, $d_arch, $d_restr,
                            $rest,$part_d_orig)
                          = @$part_d;

                        for my $arch (@{$d_arch->[0]}) {
                            if ($arch eq 'all' || !is_arch_or_wildcard($arch)){
                                tag 'invalid-arch-string-in-source-relation',
                                  "$arch [$field: $part_d_orig]";
                            }
                        }

                        for my $restrlist (@{$d_restr}) {
                            for my $prof (@{$restrlist}) {
                                $prof =~ s/^!//;
                                tag 'invalid-profile-name-in-source-relation',
                                  "$prof [$field: $part_d_orig]"
                                  unless $KNOWN_BUILD_PROFILES->known($prof)
                                  or $prof =~ /^pkg\.[a-z0-9][a-z0-9+.-]+\../;
                            }
                        }

                        if (   $d_pkg =~ m/^openjdk-\d+-doc$/o
                            or $d_pkg eq 'classpath-doc'){
                            tag 'build-depends-on-specific-java-doc-package',
                              $d_pkg;
                        }

                        if ($d_pkg eq 'java-compiler'){
                            tag 'build-depends-on-an-obsolete-java-package',
                              $d_pkg;
                        }

                        if (    $d_pkg =~ m/^libdb\d+\.\d+.*-dev$/o
                            and &$is_dep_field($field)) {
                            tag 'build-depends-on-versioned-berkeley-db',
                              "$field:$d_pkg";
                        }

                        tag 'conflicting-negation-in-source-relation',
                          "$field: $part_d_orig"
                          unless (not $d_arch
                            or $d_arch->[1] == 0
                            or $d_arch->[1] eq @{ $d_arch->[0] });

                        tag 'depends-on-packaging-dev', $field
                          if ($d_pkg eq 'packaging-dev');

                        tag 'build-depends-on-build-essential', $field
                          if ($d_pkg eq 'build-essential');

                        #<<< no tidy, tag name too long
                        tag 'build-depends-on-build-essential-package-without-using-version',
                        #>>>
                          "$d_pkg [$field: $part_d_orig]"
                          if ($known_build_essential->known($d_pkg)
                            && !$d_version->[1]);

                        #<<< no tidy, tag name too long
                        tag 'build-depends-on-essential-package-without-using-version',
                        #>>>
                          "$field: $part_d_orig"
                          if ( $KNOWN_ESSENTIAL->known($d_pkg)
                            && !$d_version->[0]
                            && $d_pkg ne 'dash');
                        push @seen_obsolete_packages, [$part_d_orig, $d_pkg]
                          if ( $OBSOLETE_PACKAGES->known($d_pkg)
                            && &$is_dep_field($field));

                        tag 'build-depends-on-metapackage',
                          "$field: $part_d_orig"
                          if (  $KNOWN_METAPACKAGES->known($d_pkg)
                            and &$is_dep_field($field));

                        tag 'build-depends-on-non-build-package',
                          "$field: $part_d_orig"
                          if (  $NO_BUILD_DEPENDS->known($d_pkg)
                            and &$is_dep_field($field));

                        tag 'build-depends-on-1-revision',
                          "$field: $part_d_orig"
                          if ( $d_version->[0] eq '>='
                            && $d_version->[1] =~ /-1$/
                            && &$is_dep_field($field));

                        tag 'bad-relation', "$field: $part_d_orig"
                          if $rest;

                        tag 'bad-version-in-relation', "$field: $part_d_orig"
                          if ($d_version->[0]
                            && !version_check($d_version->[1]));

                        tag 'package-relation-with-perl-modules',
                          "$field: $part_d_orig"
                          # matches "perl-modules" (<= 5.20) as well as
                          # perl-modules-5.xx (>> 5.20)
                          if $d_pkg =~ /^perl-modules/
                          && $proc->pkg_src ne 'perl';

                        # only trigger this for the preferred alternative
                        tag 'versioned-dependency-satisfied-by-perl',
                          "$field: $part_d_orig"
                          if $alternatives[0][-1] eq $part_d_orig
                          && &$is_dep_field($field)
                          && perl_core_has_version($d_pkg, $d_version->[0],
                            $d_version->[1]);
                    }

                    my $all_obsolete = 0;
                    $all_obsolete = 1
                      if scalar @seen_obsolete_packages == @alternatives;
                    for my $d (@seen_obsolete_packages) {
                        my ($dep, $pkg_name) = @{$d};
                        my $replacement = $OBSOLETE_PACKAGES->value($pkg_name)
                          // '';
                        $replacement = ' => ' . $replacement
                          if $replacement ne '';
                        if (   $pkg_name eq $alternatives[0][0]
                            or $all_obsolete) {
                            tag 'build-depends-on-obsolete-package',
                              "$field: $dep${replacement}";
                        } else {
                            tag 'ored-build-depends-on-obsolete-package',
                              "$field: $dep${replacement}";
                        }
                    }
                }
            }
        }

        # Check for duplicates.
        my $build_all = $info->relation('build-depends-all');
        my @dups = $build_all->duplicates;
        for my $dup (@dups) {
            tag 'package-has-a-duplicate-build-relation', join(', ', @$dup);
        }

        # Make sure build dependencies and conflicts are consistent.
        for (
            $depend{'build-conflicts'},
            $depend{'build-conflicts-indep'},
            $depend{'build-conflicts-arch'}
          ) {
            next unless $_;
            for my $conflict (split /\s*,\s*/, $_) {
                if ($build_all->implies($conflict)) {
                    tag 'build-conflicts-with-build-dependency', $conflict;
                }
            }
        }

        my (@arch_dep_pkgs, @dbg_pkgs);
        foreach my $gproc ($group->get_binary_processables) {
            my $binpkg = $gproc->pkg_name;
            if ($binpkg =~ m/-dbg$/) {
                push(@dbg_pkgs, $gproc);
            } elsif ($info->binary_field($binpkg, 'architecture', '') ne 'all')
            {
                push @arch_dep_pkgs, $binpkg;
            }
        }
        my $dstr = join('|', map { quotemeta($_) } @arch_dep_pkgs);
        my $depregex = qr/^(?:$dstr)$/;
        for my $dbg_proc (@dbg_pkgs) {
            my $deps = $info->binary_relation($dbg_proc->pkg_name, 'strong');
            my $missing = 1;
            $missing = 0 if $deps->matches($depregex, VISIT_PRED_NAME);
            if ($missing and $dbg_proc->info->is_pkg_class('transitional')) {
                # If it is a transitional package, allow it to depend
                # on another -dbg instead.
                $missing = 0
                  if $deps->matches(qr/-dbg \Z/xsm, VISIT_PRED_NAME);
            }
            tag 'dbg-package-missing-depends', $dbg_proc->pkg_name
              if $missing;
        }

        # Check for a python*-dev build dependency in source packages that
        # build only arch: all packages.
        if ($arch_dep_packages == 0 and $build_all->implies($PYTHON_DEV)) {
            tag 'build-depends-on-python-dev-with-no-arch-any';
        }

        # libmodule-build-perl
        # matches() instead of implies() because of possible OR relation
        if ($info->relation('build-depends-indep')
            ->matches(qr/^libmodule-build-perl$/, VISIT_PRED_NAME)
            && !$info->relation('build-depends')
            ->matches(qr/^libmodule-build-perl$/, VISIT_PRED_NAME)) {
            tag 'libmodule-build-perl-needs-to-be-in-build-depends';
        }

        # libmodule-build-tiny-perl
        if ($info->relation('build-depends-indep')
            ->implies('libmodule-build-tiny-perl')
            && !$info->relation('build-depends')
            ->implies('libmodule-build-tiny-perl')) {
            tag 'libmodule-build-tiny-perl-needs-to-be-in-build-depends';
        }
    }

    #----- Origin

    if (defined(my $origin = $info->field('origin'))) {
        unfold('origin', \$origin);

        tag 'redundant-origin-field' if lc($origin) eq 'debian';
    }

    #----- Bugs

    if (defined(my $bugs = $info->field('bugs'))) {
        unfold('bugs', \$bugs);

        tag 'redundant-bugs-field'
          if $bugs =~ m,^debbugs://bugs.debian.org/?$,i;

        tag 'bugs-field-does-not-refer-to-debian-infrastructure', $bugs,
          "(line $.)"
          unless $bugs =~ m,\.debian\.org, or $pkg =~ /[-]dbgsym$/;
    }

    #----- Python-Version

    if (defined(my $pyversion = $info->field('python-version'))) {
        unfold('python-version', \$pyversion);

        my @valid = (
            ['\d+\.\d+', '\d+\.\d+'],['\d+\.\d+'],
            ['\>=\s*\d+\.\d+', '\<\<\s*\d+\.\d+'],['\>=\s*\d+\.\d+'],
            ['current', '\>=\s*\d+\.\d+'],['current'],
            ['all']);

        my @pyversion = split(/\s*,\s*/, $pyversion);

        if ($pyversion =~ m/^current/) {
            tag 'python-version-current-is-deprecated';
        }

        if (@pyversion > 2) {
            if (any { !/^\d+\.\d+$/ } @pyversion) {
                tag 'malformed-python-version', $pyversion;
            }
        } else {
            my $okay = 0;
            for my $rule (@valid) {
                if (
                    $pyversion[0] =~ /^$rule->[0]$/
                    && ((
                               $pyversion[1]
                            && $rule->[1]
                            && $pyversion[1] =~ /^$rule->[1]$/
                        )
                        || (!$pyversion[1] && !$rule->[1]))
                  ) {
                    $okay = 1;
                    last;
                }
            }
            tag 'malformed-python-version', $pyversion unless $okay;
        }
    }

    #----- Dm-Upload-Allowed

    if (defined(my $dmupload = $info->field('dm-upload-allowed'))) {
        tag 'dm-upload-allowed-is-obsolete';

        unfold('dm-upload-allowed', \$dmupload);

        unless ($dmupload eq 'yes') {
            tag 'malformed-dm-upload-allowed', $dmupload;
        }
    }

    #----- Vcs-*

    my %seen_vcs;
    while (my ($vcs, $splitter) = each %VCS_EXTRACT) {
        if (defined $info->field("vcs-$vcs")) {
            my $uri = $info->field("vcs-$vcs");
            unfold("vcs-$vcs", \$uri);
            my @parts = &$splitter($uri);
            if (not @parts or not $parts[0]) {
                tag 'vcs-field-uses-unknown-uri-format', "vcs-$vcs", $uri;
            } else {
                if (    $VCS_RECOMMENDED_URIS{$vcs}
                    and $parts[0] !~ $VCS_RECOMMENDED_URIS{$vcs}) {
                    if (    $VCS_VALID_URIS{$vcs}
                        and $parts[0] =~ $VCS_VALID_URIS{$vcs}) {
                        tag 'vcs-field-uses-not-recommended-uri-format',
                          "vcs-$vcs", $uri;
                    } else {
                        tag 'vcs-field-uses-unknown-uri-format', "vcs-$vcs",
                          $uri;
                    }
                }
                if (any { $_ and /\s/} @parts) {
                    tag 'vcs-field-has-unexpected-spaces', "vcs-$vcs", $uri;
                }
                if (   $parts[0] =~ m%^(?:git|(?:nosmart\+)?http|svn)://%
                    or $parts[0] =~ m%^(?:lp|:pserver):%) {
                    tag 'vcs-field-uses-insecure-uri', "vcs-$vcs", $uri;
                }
            }
            if ($VCS_CANONIFY{$vcs}) {
                my $canonicalized = $parts[0];
                my $tag = 'vcs-field-not-canonical';
                foreach my $canonify ($VCS_CANONIFY{$vcs}) {
                    &$canonify($canonicalized, $tag);
                }
                if ($canonicalized ne $parts[0]) {
                    tag $tag, $parts[0], $canonicalized;
                }
            }
            if ($vcs eq 'browser') {
                tag 'vcs-browser-links-to-empty-view', $uri
                  if $uri =~ m%rev=0&sc=0%;
            } else {
                $seen_vcs{$vcs}++;
            }
            if ($uri =~ m{//([^.]+)\.debian\.org/}) {
                tag 'vcs-deprecated-in-debian-infrastructure', "vcs-$vcs", $uri
                  if $1 ne 'salsa';
            } else {
                tag 'orphaned-package-not-maintained-in-debian-infrastructure',
                  "vcs-$vcs", $uri
                  if $info->field('maintainer', '')
                  =~ /packages\@qa.debian.org/
                  and $vcs ne 'browser';
            }
        }
    }
    tag 'vcs-fields-use-more-than-one-vcs', sort keys %seen_vcs
      if keys %seen_vcs > 1;

    tag 'co-maintained-package-with-no-vcs-fields'
      if $type eq 'source'
      and $is_comaintained
      and not %seen_vcs;

    # Check for missing Vcs-Browser headers
    if (!defined $info->field('vcs-browser')) {
        foreach my $regex ($KNOWN_VCS_BROWSERS->all) {
            my $vcs = $KNOWN_VCS_BROWSERS->value($regex);
            if ($info->field("vcs-$vcs", '') =~ m/^($regex.*)/xi) {
                tag 'missing-vcs-browser-field', "vcs-$vcs", $1;
                last; # Only warn once
            }
        }
    }

    #---- Checksums

    tag 'no-strong-digests-in-dsc'
      if $type eq 'source' && !$info->field('checksums-sha256');

    #----- Field checks (without checking the value)

    for my $field (keys %{$info->field}) {

        tag 'unknown-field-in-dsc', $field
          if ($type eq 'source' && !$SOURCE_FIELDS->known($field));

        tag 'unknown-field-in-control', $field
          if ($type eq 'binary' && !$KNOWN_BINARY_FIELDS->known($field));

        tag 'unknown-field-in-control', $field
          if ($type eq 'udeb' && !$KNOWN_UDEB_FIELDS->known($field));
    }

    return;
}

# splits "foo:bar (>= 1.2.3) [!i386 ia64] <stage1 !nocheck> <cross>" into
# ( "foo", "bar", [ ">=", "1.2.3" ], [ [ "i386", "ia64" ], 1 ], [ [ "stage1", "!nocheck" ] , [ "cross" ] ], "" )
#                                                         ^^^                                               ^^
#                     count of negated arches, if ! was given                                               ||
#                                                              rest (should always be "" for valid dependencies)
sub _split_dep {
    my $dep = shift;
    my ($pkg, $dmarch, $version, $darch, $restr)
      = ('', '', ['',''], [[], 0], []);

    if ($dep =~ s/^\s*([^<\s\[\(]+)\s*//) {
        ($pkg, $dmarch) = split(/:/, $1, 2);
        $dmarch //= '';  # Ensure it is defined (in case there is no ":")
    }

    if (length $dep) {
        if ($dep
            =~ s/\s* \( \s* (<<|<=|<|=|>=|>>|>) \s* ([^\s(]+) \s* \) \s*//x) {
            @$version = ($1, $2);
        }
        if ($dep && $dep =~ s/\s*\[([^\]]+)\]\s*//) {
            my $t = $1;
            $darch->[0] = [split /\s+/, $t];
            my $negated = 0;
            for my $arch (@{ $darch->[0] }) {
                $negated++ if $arch =~ s/^!//;
            }
            $darch->[1] = $negated;
        }
        while ($dep && $dep =~ s/\s*<([^>]+)>\s*//) {
            my $t = $1;
            push @$restr, [split /\s+/, $t];
        }
    }

    return ($pkg, $dmarch, $version, $darch, $restr, $dep);
}

sub perl_core_has_version {
    my ($package, $op, $version) = @_;
    my $core_version = $PERL_CORE_PROVIDES->value($package);
    return 0 if !defined $core_version;
    return 0 unless version_check($version);
    return versions_compare($core_version, $op, $version);
}

sub unfold {
    my ($field, $line) = @_;

    $$line =~ s/\n$//;

    if ($$line =~ s/\n//g) {
        tag 'multiline-field', $field;
        # Remove leading space as it confuses some of the other checks
        # that are anchored.  This happens if the field starts with a
        # space and a newline, i.e ($ marks line end):
        #
        # Vcs-Browser: $
        #  http://somewhere.com/$
        $$line=~s/^\s*+//;
    }
    return;
}

sub check_field {
    my ($info, $field, $data) = @_;
    my @seen;
    $info->relation($field)->visit(sub { push @seen, $_; }, VISIT_PRED_NAME);

    my $has_default_mta = any { $_ eq 'default-mta' } @seen;
    my $has_mail_transport_agent = any { $_ eq 'mail-transport-agent' } @seen;

    if ($has_default_mta) {
        tag 'default-mta-dependency-not-listed-first',"$field: $data"
          if $seen[0] ne 'default-mta';
        tag 'default-mta-dependency-does-not-specify-mail-transport-agent',
          "$field: $data"
          unless $has_mail_transport_agent;
    } elsif ($has_mail_transport_agent) {
        tag 'mail-transport-agent-dependency-does-not-specify-default-mta',
          "$field: $data"
          unless $has_default_mta;
    }
    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
