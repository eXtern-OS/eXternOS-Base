# rules -- lintian check script -*- perl -*-

# Copyright (C) 2006 Russ Allbery <rra@debian.org>
# Copyright (C) 2005 René van Bevern <rvb@pro-linux.de>
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

package Lintian::rules;
use strict;
use warnings;
use autodie;
use Carp qw(croak);

use List::MoreUtils qw(any none);

use Lintian::Data;
use Lintian::Tags qw(tag);
use Lintian::Util qw(rstrip);

our $PYTHON_DEPEND
  = 'python:any | python-dev:any | python-all:any | python-all-dev:any';
our $PYTHON3_DEPEND
  = 'python3:any | python3-dev:any | python3-all:any | python3-all-dev:any';
our $PYTHON2X_DEPEND = 'python2.7:any | python2.7-dev:any';
our $PYTHON3X_DEPEND= join(' | ',
    map { "python${_}:any | python${_}-dev:any" } qw(3.4 3.5 3.6 3.7));
our $ANYPYTHON_DEPEND
  = "$PYTHON_DEPEND | $PYTHON2X_DEPEND | $PYTHON3_DEPEND | $PYTHON3X_DEPEND";

my $KNOWN_MAKEFILES = Lintian::Data->new('rules/known-makefiles', '\|\|');
my $DEPRECATED_MAKEFILES = Lintian::Data->new('rules/deprecated-makefiles');
my $POLICYRULES = Lintian::Data->new('rules/policy-rules', qr/\s++/);

# forbidden construct in rules
my $BAD_CONSTRUCT_IN_RULES
  = Lintian::Data->new('rules/rules-should-not-use', qr/\s*~~\s*/,
    sub { return qr/$_[1]/xs });

my $BAD_MULTILINE_CONSTRUCT_IN_RULES
  = Lintian::Data->new('rules/rules-should-not-use-multiline',
    qr/\s*~~\s*/,sub { return qr/$_[1]/xsm });

# Certain build tools must be listed in Build-Depends even if there are no
# arch-specific packages because they're required in order to run the clean
# rule.  (See Policy 7.6.)  The following is a list of package dependencies;
# regular expressions that, if they match anywhere in the debian/rules file,
# say that this package is allowed (and required) in Build-Depends; and
# optional tags to use for reporting the problem if some information other
# than the default is required.
our @GLOBAL_CLEAN_DEPENDS = (
    [ant => qr'^include\s*/usr/share/cdbs/1/rules/ant\.mk'],
    [cdbs => qr'^include\s+/usr/share/cdbs/'],
    [cdbs => qr'^include\s+/usr/share/R/debian/r-cran\.mk'],
    [dbs => qr'^include\s+/usr/share/dbs/'],
    ['dh-make-php' => qr'^include\s+/usr/share/cdbs/1/class/pear\.mk'],
    [debhelper => qr'^include\s+/usr/share/cdbs/1/rules/debhelper\.mk'],
    [debhelper => qr'^include\s+/usr/share/R/debian/r-cran\.mk'],
    [dpatch => qr'^include\s+/usr/share/cdbs/1/rules/dpatch\.mk'],
    ['gnome-pkg-tools' => qr'^include\s+/usr/share/gnome-pkg-tools/'],
    [quilt => qr'^include\s+/usr/share/cdbs/1/rules/patchsys-quilt\.mk'],
    [dpatch => qr'^include\s+/usr/share/dpatch/'],
    ['mozilla-devscripts' => qr'^include\s+/usr/share/mozilla-devscripts/'],
    [quilt => qr'^include\s+/usr/share/quilt/'],
    ['ruby-pkg-tools' => qr'^include\s+/usr/share/ruby-pkg-tools/1/class/'],
    ['r-base-dev' => qr'^include\s+/usr/share/R/debian/r-cran\.mk'],
    [
        $ANYPYTHON_DEPEND => qr'/usr/share/cdbs/1/class/python-distutils\.mk',
        'missing-python-build-dependency'
    ],
);

# A list of packages; regular expressions that, if they match anywhere in the
# debian/rules file, this package must be listed in either Build-Depends or
# Build-Depends-Indep as appropriate; and optional tags as above.
my @GLOBAL_DEPENDS=(
    ['dh-ocaml, ocaml-nox | ocaml' => qr'^\t\s*dh_ocaml(?:init|doc)\s'],
);

# Similarly, this list of packages, regexes, and optional tags say that if the
# regex matches in one of clean, build-arch, binary-arch, or a rule they
# depend on, this package is allowed (and required) in Build-Depends.
my @RULE_CLEAN_DEPENDS =(
    [ant => qr'^\t\s*(\S+=\S+\s+)*ant\s'],
    [debhelper => qr'^\t\s*dh_.+'],
    ['dh-ocaml, ocaml-nox | ocaml' => qr'^\t\s*dh_ocamlinit\s'],
    [dpatch => qr'^\t\s*(\S+=\S+\s+)*dpatch\s'],
    ['po-debconf' => qr'^\t\s*debconf-updatepo\s'],
    [$PYTHON_DEPEND => qr'^\t\s*python\s', 'missing-python-build-dependency'],
    [
        $PYTHON3_DEPEND => qr'^\t\s*python3\s',
        'missing-python-build-dependency'
    ],
    [
        $ANYPYTHON_DEPEND => qr'\ssetup\.py\b',
        'missing-python-build-dependency'
    ],
    [quilt => qr'^\t\s*(\S+=\S+\s+)*quilt\s'],
);

# Rules about required debhelper command ordering.  Each command is put into a
# class and the tag is issued if they're called in the wrong order for the
# classes.  Unknown commands won't trigger this flag.
my %debhelper_order = (
    dh_makeshlibs => 1,
    dh_shlibdeps  => 2,
    dh_installdeb => 2,
    dh_gencontrol => 2,
    dh_builddeb   => 3
);

sub run {
    my (undef, undef, $info, undef, $group) = @_;
    my $debian_dir = $info->index_resolved_path('debian');
    my $rules;
    $rules = $debian_dir->child('rules') if $debian_dir;

    return if not $rules;

    # Policy could be read as allowing debian/rules to be a symlink to
    # some other file, and in a native Debian package it could be a
    # symlink to a file that we didn't unpack.  Warn if it's a symlink
    # (dpkg-source does as well) and skip all the tests if we then
    # can't read it.
    if ($rules->is_symlink) {
        tag 'debian-rules-is-symlink';
        return unless $rules->is_open_ok;
    }

    my $architecture = $info->field('architecture', '');
    my $version = $info->field('version');
    # If the version field is missing, we assume a neutral non-native one.
    $version = '0-1' unless defined $version;

    my $rules_fd = $rules->open;

    # Check for required #!/usr/bin/make -f opening line.  Allow -r or -e; a
    # strict reading of Policy doesn't allow either, but they seem harmless.
    my $start = <$rules_fd>;
    $start //= q{};
    tag 'debian-rules-not-a-makefile'
      unless $start =~ m%^\#!\s*/usr/bin/make\s+-[re]?f[re]?\s*$%;

    # Holds which dependencies are required.  The keys in %needed and
    # %needed_clean are the dependencies; the values are the tags to use or the
    # empty string to use the default tag.
    my (%needed, %needed_clean);

    # Scan debian/rules.  We would really like to let make do this for
    # us, but unfortunately there doesn't seem to be a way to get make
    # to syntax-check and analyze a makefile without running at least
    # $(shell) commands.
    #
    # We skip some of the rule analysis if debian/rules includes any
    # other files, since to chase all includes we'd have to have all
    # of its build dependencies installed.
    local $_;
    my $build_all = $info->relation('build-depends-all');
    my @arch_rules = (qr/^clean$/, qr/^binary-arch$/, qr/^build-arch$/);
    my @indep_rules = (qr/^build$/, qr/^build-indep$/, qr/^binary-indep$/);
    my (@current_targets, %rules_per_target,  %debhelper_group);
    my (%seen, %overridden);
    my ($maybe_skipping, @conditionals);
    my %variables;
    my $uses_makefile_pl = 0;
    my $includes = 0;

    while (<$rules_fd>) {
        while (s,\\$,, and defined(my $cont = <$rules_fd>)) {
            $_ .= $cont;
        }
        my $line = $_;

        tag 'debian-rules-is-dh_make-template'
          if $line =~ m/dh_make generated override targets/;

        next if /^\s*\#/;
        if (m/^\s*[s-]?include\s+(\S++)/o){
            my $makefile = $1;
            my $targets = $KNOWN_MAKEFILES->value($makefile);
            if (defined $targets){
                foreach my $target (split m/\s*+,\s*+/o, $targets){
                    $seen{$target}++ if $POLICYRULES->known($target);
                }
            } else {
                $includes = 1;
            }
            if ($DEPRECATED_MAKEFILES->known($makefile)){
                tag 'debian-rules-uses-deprecated-makefile', "line $.",
                  $makefile;
            }
        }
        $uses_makefile_pl = 1 if m/Makefile\.PL/o;

        # Check for DH_COMPAT settings outside of any rule, which are now
        # deprecated.  It's a bit easier structurally to do this here than in
        # debhelper.
        if (/^\s*(?:export\s+)?DH_COMPAT\s*:?=/ && keys(%seen) == 0) {
            tag 'debian-rules-sets-DH_COMPAT', "line $.";
        }

        # Check for problems that can occur anywhere in debian/rules.
        if (   m/^\t\s*-(?:\$[\(\{]MAKE[\}\)]|make)\s.*(?:dist)?clean/s
            || m/^\t\s*(?:\$[\(\{]MAKE[\}\)]|make)\s(?:.*\s)?-(\w*)i.*(?:dist)?clean/s
          ) {
            # Ignore "-C<dir>" (#671537)
            if (not $1 or $1 !~ m,^C,) {
                tag 'debian-rules-ignores-make-clean-error', "line $.";
            }
        }

        if (/^\s*(?:export\s+)?DEB_BUILD_OPTIONS\s*:?=/ && keys(%seen) == 0) {
            tag 'debian-rules-sets-DEB_BUILD_OPTIONS', "line $.";
        }

        if (
            /^
                \s*(?:export\s+)?
                (DEB_(?:HOST|BUILD|TARGET)_(?:ARCH|MULTIARCH|GNU)[A-Z_]*)\s*:?=
            /x
            && keys(%seen) == 0
          ) {
            tag 'debian-rules-sets-dpkg-architecture-variable', "$1 (line $.)";
        }

        # check generic problem
        foreach my $bad_construct ($BAD_CONSTRUCT_IN_RULES->all) {
            my $badregex = $BAD_CONSTRUCT_IN_RULES->value($bad_construct);
            if ($line =~ m/$badregex/) {
                if (defined($+{info})) {
                    tag $bad_construct, $+{info}, "(line $.)";
                } else {
                    tag $bad_construct, "line $.";
                }
            }
        }

        if ($uses_makefile_pl && m/install.*PREFIX/s && !/DESTDIR/) {
            tag 'debian-rules-makemaker-prefix-is-deprecated', "line $.";
        }

        # General assignment - save the variable
        if (/^\s*(?:\S+\s+)*?(\S+)\s*[:\?\+]?=\s*(.*+)?$/so) {
            # This is far too simple from a theoretical PoV, but should do
            # rather well.
            my ($var, $value) = ($1, $2);
            $variables{$var} = $value;
            tag 'unnecessary-source-date-epoch-assignment', "(line $.)"
              if $var eq 'SOURCE_DATE_EPOCH'
              and not $build_all->implies(
                'dpkg-dev (>= 1.18.8) | debhelper (>= 10.10)');
        }

        # Keep track of whether this portion of debian/rules may be optional
        if (/^ifn?(?:eq|def)\s(.*)/) {
            push(@conditionals, $1);
            $maybe_skipping++;
        } elsif (/^endif\s/) {
            $maybe_skipping--;
        }

        # Check for strings anywhere in debian/rules that have implications for
        # our dependencies.
        for my $rule (@GLOBAL_CLEAN_DEPENDS) {
            if (/$rule->[1]/ and not $maybe_skipping) {
                $needed_clean{$rule->[0]}
                  = $rule->[2] || $needed_clean{$rule->[0]} || '';
            }
        }
        for my $rule (@GLOBAL_DEPENDS) {
            if (/$rule->[1]/ && !$maybe_skipping) {
                $needed{$rule->[0]} = $rule->[2] || $needed{$rule->[0]} || '';
            }
        }

        # Listing a rule as a dependency of .PHONY is sufficient to make it
        # present for the purposes of GNU make and therefore the Policy
        # requirement.
        if (/^(?:[^:]+\s)?\.PHONY(?:\s[^:]+)?:(.+)/s) {
            my @targets = split(' ', $1);
            local $_;
            for (@targets) {
                # Is it $(VAR) ?
                if (m/^\$[\(\{]([^\)\}]++)[\)\}]$/) {
                    my $name = $1;
                    my $val = $variables{$name};
                    if ($val) {
                        # we think we know what it will expand to - note
                        # we ought to "delay" it was a "=" variable rather
                        # than ":=" or "+=".
                        for (split m/\s++/o, rstrip($val)) {
                            $seen{$_}++ if $POLICYRULES->known($_);
                        }
                        last;
                    }
                    # We don't know, so just mark the target as seen.
                }
                $seen{$_}++ if $POLICYRULES->known($_);
            }
            next; #.PHONY implies the rest will not match
        }

        if (!$includes
            && m/dpkg-parsechangelog.*(?:Source|Version|Date|Timestamp)/s) {
            tag 'debian-rules-parses-dpkg-parsechangelog', "(line $.)";
        }

        if (!/^ifn?(?:eq|def)\s/ && m/^([^\s:][^:]*):+(.*)/s) {
            my ($target_names, $target_dependencies) = ($1, $2);
            @current_targets = split ' ', $target_names;
            my @depends = map {
                $_ = quotemeta $_;
                s/\\\$\\\([^\):]+\\:([^=]+)\\=([^\)]+)\1\\\)/$2.*/g;
                qr/^$_$/;
            } split(' ', $target_dependencies);
            for my $target (@current_targets) {
                $overridden{$1} = $. if $target =~ m/override_(.+)/;
                if ($target =~ m/%/o) {
                    my $pattern = quotemeta $target;
                    $pattern =~ s/\\%/.*/g;
                    for my $rulebypolicy ($POLICYRULES->all) {
                        $seen{$rulebypolicy}++ if $rulebypolicy =~ m/$pattern/;
                    }
                } else {
                    # Is it $(VAR) ?
                    if ($target =~ m/^\$[\(\{]([^\)\}]++)[\)\}]$/) {
                        my $name = $1;
                        my $val = $variables{$name};
                        if ($val) {
                            # we think we know what it will expand to - note
                            # we ought to "delay" it was a "=" variable rather
                            # than ":=" or "+=".
                            local $_;
                            for (split m/\s++/o, rstrip($val)) {
                                $seen{$_}++ if $POLICYRULES->known($_);
                            }
                            last;
                        }
                        # We don't know, so just mark the target as seen.
                    }
                    $seen{$target}++ if $POLICYRULES->known($target);
                }
                if (any { $target =~ /$_/ } @arch_rules) {
                    push(@arch_rules, @depends);
                }
            }
            undef %debhelper_group;
        } elsif (/^define /) {
            # We don't want to think the body of the define is part of
            # the previous rule or we'll get false positives on tags
            # like binary-arch-rules-but-pkg-is-arch-indep.  Treat a
            # define as the end of the current rule, although that
            # isn't very accurate either.
            @current_targets = ();
        } else {
            # If we have non-empty, non-comment lines, store them for
            # all current targets and check whether debhelper programs
            # are called in a reasonable order.
            if (m/^\s+[^\#]/) {
                my ($arch, $indep) = (0, 0);
                for my $target (@current_targets) {
                    $rules_per_target{$target} ||= [];
                    push @{$rules_per_target{$target}}, $_;
                    $arch = 1 if (any { $target =~ /$_/ } @arch_rules);
                    $indep = 1 if (any { $target =~ /$_/ } @indep_rules);
                    $indep = 1 if $target eq '%';
                    $indep = 1 if $target =~ /^override_/;
                }
                if (not $maybe_skipping and ($arch or $indep)) {
                    my $table = \%needed;
                    $table = \%needed_clean if $arch;
                    for my $rule (@RULE_CLEAN_DEPENDS) {
                        my ($dep, $pattern, $tagname) = @$rule;
                        next unless /$pattern/;
                        $table->{$dep} = $tagname || $table->{$dep} || '';
                    }
                }
                if (m/^\s+(dh_\S+)\b/ and $debhelper_order{$1}) {
                    my $command = $1;
                    my ($package) = /\s(?:-p|--package=)(\S+)/;
                    $package ||= '';
                    my $group = $debhelper_order{$command};
                    $debhelper_group{$package} ||= 0;
                    if ($group < $debhelper_group{$package}) {
                        tag 'debian-rules-calls-debhelper-in-odd-order',
                          $command, "(line $.)";
                    } else {
                        $debhelper_group{$package} = $group;
                    }
                }
            }
        }
    }
    close($rules_fd);

    unless ($includes) {
        # Make sure all the required rules were seen.
        for my $target ($POLICYRULES->all) {
            unless ($seen{$target}) {
                my $typerule = $POLICYRULES->value($target);
                if($typerule eq 'required') {
                    tag 'debian-rules-missing-required-target', $target;
                } elsif ($typerule eq 'recommended_allindep') {
                    tag 'debian-rules-missing-recommended-target', $target;
                } else {
                    $typerule ||= '<N/A>';
                    croak(
                        join(' ',
                            'unknown type of policy rules:',
                            "$typerule (target: $target)"));
                }
            }
        }
    }

    # Make sure we have no content for binary-arch if we are arch-indep:
    $rules_per_target{'binary-arch'} ||= [];
    if ($architecture eq 'all' && scalar @{$rules_per_target{'binary-arch'}}) {
        my $nonempty = 0;
        foreach (@{$rules_per_target{'binary-arch'}}) {
            # dh binary-arch is actually a no-op if there is no
            # Architecture: any package in the control file
            unless (m/^\s*dh\s+(?:binary-arch|\$\@)/) {
                $nonempty = 1;
            }
        }
        tag 'binary-arch-rules-but-pkg-is-arch-indep' if $nonempty;
    }

    foreach my $cmd (qw(dh_clean dh_fixperms)) {
        foreach my $suffix ('', '-indep', '-arch') {
            my $line = $overridden{"$cmd$suffix"};
            tag "override_$cmd-does-not-call-$cmd", "(line $line)"
              if $line
              and none { m/^\t\s*-?($cmd\b|\$\(overridden_command\))/ }
            @{$rules_per_target{"override_$cmd$suffix"}};
        }
    }

    if (my $line = $overridden{'dh_auto_test'}) {
        my @lines = grep {
                  $_ !~ m{^\t\s*[\:\[]}
              and $_ !~ m{\bdh_auto_test\b}
              and $_
              !~ m{^\t\s*[-@]?(?:(?:/usr)?/bin/)?(?:cp|chmod|echo|ln|mv|mkdir|rm|test|true)}
        } @{$rules_per_target{'override_dh_auto_test'}};
        tag 'override_dh_auto_test-does-not-check-DEB_BUILD_OPTIONS',
          "(line $line)"
          if @lines and none { m/(DEB_BUILD_OPTIONS|nocheck)/ } @conditionals;
    }

    tag 'debian-rules-contains-unnecessary-get-orig-source-target'
      if any { m/^\s+uscan\b/ } @{$rules_per_target{'get-orig-source'}};

    # Make sure that all the required build dependencies are there.  Don't
    # issue missing-build-dependency errors for debhelper, since there's
    # another test that does that and it would just be a duplicate.
    my $build_regular = $info->relation('build-depends');
    my $build_indep   = $info->relation('build-depends-indep');
    for my $package (keys %needed_clean) {
        delete $needed{$package};
        my $tag = $needed_clean{$package} || 'missing-build-dependency';
        unless ($build_regular->implies($package)) {
            if ($build_indep->implies($package)) {
                tag 'clean-should-be-satisfied-by-build-depends', $package;
            } else {
                if ($tag eq 'missing-build-dependency') {
                    tag $tag, $package if $package ne 'debhelper';
                } else {
                    tag $tag;
                }
            }
        }
    }
    my $noarch = $info->relation_noarch('build-depends-all');
    for my $package (keys %needed) {
        my $tag = $needed{$package} || 'missing-build-dependency';

        unless ($noarch->implies($package)) {
            if ($tag eq 'missing-build-dependency') {
                tag $tag, $package;
            } else {
                tag $tag;
            }
        }
    }

    $rules_fd = $rules->open;
    my $sfd = Lintian::SlidingWindow->new($rules_fd);
    my $block;
    while ($block = $sfd->readwindow) {
        foreach my $tag ($BAD_MULTILINE_CONSTRUCT_IN_RULES->all) {
            my $regex = $BAD_MULTILINE_CONSTRUCT_IN_RULES->value($tag);
            tag $tag if $block =~ m/$regex/;
        }
    }
    close($rules_fd);

    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
