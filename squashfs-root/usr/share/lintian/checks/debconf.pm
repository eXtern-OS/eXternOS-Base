# debconf -- lintian check script -*- perl -*-

# Copyright (C) 2001 Colin Watson
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

package Lintian::debconf;
use strict;
use warnings;
use autodie;

use Lintian::Relation;
use Lintian::Tags qw(tag);
use Lintian::Util qw(read_dpkg_control :constants $PKGNAME_REGEX);

# From debconf-devel(7), section 'THE TEMPLATES FILE', up to date with debconf
# version 1.5.24.  Added indices for cdebconf (indicates sort order for
# choices); debconf doesn't support it, but it ignores it, which is safe
# behavior. Likewise, help is supported as of cdebconf 0.143 but is not yet
# supported by debconf.
my %template_fields
  = map { $_ => 1 } qw(template type choices indices default description help);

# From debconf-devel(7), section 'THE TEMPLATES FILE', up to date with debconf
# version 1.5.24.
my %valid_types = map { $_ => 1 } qw(
  string
  password
  boolean
  select
  multiselect
  note
  error
  title
  text);

# From debconf-devel(7), section 'THE DEBCONF PROTOCOL' under 'INPUT', up to
# date with debconf version 1.5.24.
my %valid_priorities = map { $_ => 1 } qw(low medium high critical);

# All the packages that provide debconf functionality.  Anything using debconf
# needs to have dependencies that satisfy one of these.
my $ANY_DEBCONF = Lintian::Relation->new(
    join(
        ' | ', qw(debconf debconf-2.0 cdebconf
          cdebconf-udeb libdebconfclient0 libdebconfclient0-udeb)
    ));

sub run {
    my ($pkg, $type, $info) = @_;
    my ($seenconfig, $seentemplates, $usespreinst);

    if ($type eq 'source') {
        my @binaries = $info->binaries;
        my @files = map { "$_.templates" } @binaries;
        push @files, 'templates';

        foreach my $file (@files) {
            my $dfile = "debian/$file";
            my $templates_file = $info->index_resolved_path($dfile);
            my $binary = $file;
            $binary =~ s/\.?templates$//;
            # Single binary package (so @files contains "templates" and
            # "binary.templates")?
            if (!$binary && @files == 2) {
                $binary = $binaries[0];
            }

            if ($templates_file and $templates_file->is_open_ok) {
                my @templates;
                eval {
                    @templates
                      = read_dpkg_control($templates_file->fs_path,
                        DCTRL_DEBCONF_TEMPLATE);
                };
                if ($@) {
                    chomp $@;
                    $@ =~ s/^internal error: //;
                    $@ =~ s/^syntax error in //;
                    tag 'syntax-error-in-debconf-template', "$file: $@";
                    next;
                }

                foreach my $template (@templates) {
                    if (    exists $template->{template}
                        and exists $template->{_choices}) {
                        tag 'template-uses-unsplit-choices',
                          "$binary - $template->{template}";
                    }
                }
            }
        }

        # The remainder of the checks are for binary packages, so we exit now
        return;
    }

    my $preinst = $info->control_index('preinst');
    my $ctrl_config = $info->control_index('config');
    my $ctrl_templates = $info->control_index('templates');

    if ($preinst and $preinst->is_file and $preinst->is_open_ok) {
        my $fd = $preinst->open;
        while (<$fd>) {
            s/\#.*//;    # Not perfect for Perl, but should be OK
            if (   m,/usr/share/debconf/confmodule,
                or m/(?:Debconf|Debian::DebConf)::Client::ConfModule/) {
                $usespreinst=1;
                last;
            }
        }
        close($fd);
    }

    $seenconfig = 1 if $ctrl_config and $ctrl_config->is_file;
    $seentemplates = 1 if $ctrl_templates and $ctrl_templates->is_file;

    # This still misses packages that use debconf only in the postrm.
    # Packages that ask debconf questions in the postrm should load
    # the confmodule in the postinst so that debconf can register
    # their templates.
    return unless $seenconfig or $seentemplates or $usespreinst;

    # parse depends info for later checks

    # Consider every package to depend on itself.
    my $selfrel;
    if (defined $info->field('version')) {
        $_ = $info->field('version');
        $selfrel = "$pkg (= $_)";
    } else {
        $selfrel = "$pkg";
    }

    # Include self and provides as a package providing debconf presumably
    # satisfies its own use of debconf (if any).
    my $selfrelation
      = Lintian::Relation->and($info->relation('provides'), $selfrel);
    my $alldependencies
      = Lintian::Relation->and($info->relation('strong'), $selfrelation);

    # See if the package depends on dbconfig-common.  Packages that do
    # are allowed to have a config file with no templates, since they
    # use the dbconfig-common templates.
    my $usesdbconfig = $alldependencies->implies('dbconfig-common');

    # Check that both debconf control area files are present.
    if ($seenconfig and not $seentemplates and not $usesdbconfig) {
        tag 'no-debconf-templates';
    } elsif ($seentemplates
        and not $seenconfig
        and not $usespreinst
        and $type ne 'udeb') {
        tag 'no-debconf-config';
    }

    if ($seenconfig and not $ctrl_config->is_executable) {
        tag 'debconf-config-not-executable';
    }

    # Lots of template checks.

    my (@templates, %potential_db_abuse, @templates_seen);

    if ($seentemplates) {
        eval {
            # $seentemplates (above) will be false if $ctrl_templates is a
            # symlink or not a file, so this should be safe without
            # (re-checking) with -f/-l.
            @templates
              = read_dpkg_control($ctrl_templates->fs_path,
                DCTRL_DEBCONF_TEMPLATE);
        };
        if ($@) {
            chomp $@;
            $@ =~ s/^internal error: //;
            $@ =~ s/^syntax error in //;
            tag 'syntax-error-in-debconf-template', "templates: $@";
            @templates = ();
        }
    }

    foreach my $template (@templates) {
        my $isselect = '';

        if (not exists $template->{template}) {
            tag 'no-template-name';
            $template->{template} = 'no-template-name';
        } else {
            push @templates_seen, $template->{template};
            if ($template->{template}!~m|[A-Za-z0-9.+-](?:/[A-Za-z0-9.+-])|) {
                tag 'malformed-template-name', "$template->{template}";
            }
        }

        if (not exists $template->{type}) {
            tag 'no-template-type', "$template->{template}";
        } elsif (not $valid_types{$template->{type}}) {
            # cdebconf has a special "entropy" type
            tag 'unknown-template-type', "$template->{type}"
              unless ($template->{type} eq 'entropy'
                and $alldependencies->implies('cdebconf'));
        } elsif ($template->{type} eq 'select') {
            $isselect = 1;
        } elsif ($template->{type} eq 'multiselect') {
            $isselect = 1;
        } elsif ($template->{type} eq 'boolean') {
            tag 'boolean-template-has-bogus-default',
              "$template->{template} $template->{default}"
              if defined $template->{default}
              and $template->{default} ne 'true'
              and $template->{default} ne 'false';
        }

        if ($template->{choices} && ($template->{choices} !~ /^\s*$/)) {
            my $nrchoices = count_choices($template->{choices});
            for my $key (keys %$template) {
                if ($key =~ /^choices-/) {
                    if (!$template->{$key} || ($template->{$key} =~ /^\s*$/o)){
                        tag 'empty-translated-choices',
                          "$template->{template} $key";
                    }
                    if (count_choices($template->{$key}) != $nrchoices) {
                        tag 'mismatch-translated-choices',
                          "$template->{template} $key";
                    }
                }
            }
            if ($template->{choices} =~ /^\s*(yes\s*,\s*no|no\s*,\s*yes)\s*$/i)
            {
                tag 'select-with-boolean-choices', "$template->{template}";
            }
        }

        if ($isselect and not exists $template->{choices}) {
            tag 'select-without-choices', "$template->{template}";
        }

        if (not exists $template->{description}) {
            tag 'no-template-description', "$template->{template}";
        } elsif ($template->{description}=~m/^\s*(.*?)\s*?\n\s*\1\s*$/) {
            # Check for duplication. Should all this be folded into the
            # description checks?
            tag 'duplicate-long-description-in-template',
              "$template->{template}";
        }

        my %languages;
        foreach my $field (sort keys %$template) {
            # Tests on translations
            my ($mainfield, $lang) = split m/-/, $field, 2;
            if (defined $lang) {
                $languages{$lang}{$mainfield}=1;
            }
            unless ($template_fields{$mainfield}){ # Ignore language codes here
                tag 'unknown-field-in-templates',
                  "$template->{template} $field";
            }
        }

        if ($template->{template} && $template->{type}) {
            $potential_db_abuse{$template->{template}} = 1
              if ( ($template->{type} eq 'note')
                or ($template->{type} eq 'text'));
        }

        # Check the description against the best practices in the
        # Developer's Reference, but skip all templates where the
        # short description contains the string "for internal use".
        my ($short, $extended);
        if (defined $template->{description}) {
            ($short, $extended) = split(/\n/, $template->{description}, 2);
            unless (defined $short) {
                $short = $template->{description};
                $extended = '';
            }
        } else {
            ($short, $extended) = ('', '');
        }
        my $ttype = $template->{type} || '';
        unless ($short =~ /for internal use/i) {
            my $isprompt = grep { $_ eq $ttype } qw(string password);
            if ($isprompt) {
                if (
                    $short
                    && (   $short !~ m/:$/
                        || $short =~ m/^(what|who|when|where|which|how)/i)
                  ) {
                    tag 'malformed-prompt-in-templates', $template->{template};
                }
            }
            if ($isselect) {
                if ($short =~ /^(Please|Cho+se|Enter|Select|Specify|Give)/) {
                    tag 'using-imperative-form-in-templates',
                      $template->{template};
                }
            }
            if ($ttype eq 'boolean') {
                if ($short !~ /\?/) {
                    tag 'malformed-question-in-templates',
                      $template->{template};
                }
            }
            if (defined($extended) && $extended =~ /[^\?]\?(\s+|$)/) {
                tag 'using-question-in-extended-description-in-templates',
                  $template->{template};
            }
            if ($ttype eq 'note') {
                if ($short =~ /[.?;:]$/) {
                    tag 'malformed-title-in-templates', $template->{template};
                }
            }
            if (length($short) > 75) {
                tag 'too-long-short-description-in-templates',
                  $template->{template}
                  unless $type eq 'udeb' && $ttype eq 'text';
            }
            if (defined $template->{description}) {
                if ($template->{description}
                    =~ /(\A|\s)(I|[Mm]y|[Ww]e|[Oo]ur|[Oo]urs|mine|myself|ourself|me|us)(\Z|\s)/
                  ) {
                    tag 'using-first-person-in-templates',
                      $template->{template};
                }
                if (    $template->{description} =~ /[ \'\"]yes[ \'\",;.]/i
                    and $ttype eq 'boolean') {
                    tag 'making-assumptions-about-interfaces-in-templates',
                      $template->{template};
                }
            }

            # Check whether the extended description is too long.
            if ($extended) {
                my $lines = 0;
                for my $string (split("\n", $extended)) {
                    while (length($string) > 80) {
                        my $pos = rindex($string, ' ', 80);
                        if ($pos == -1) {
                            $pos = index($string, ' ');
                        }
                        if ($pos == -1) {
                            $string = '';
                        } else {
                            $string = substr($string, $pos + 1);
                            $lines++;
                        }
                    }
                    $lines++;
                }
                if ($lines > 20) {
                    tag 'too-long-extended-description-in-templates',
                      $template->{template};
                }
            }
        }
    }

    # Check the maintainer scripts.

    my ($config_calls_db_input, $db_purge);
    my (%templates_used, %template_aliases);
    for my $file (qw(config prerm postrm preinst postinst)) {
        my $potential_makedev = {};
        my $path = $info->control_index($file);
        if ($path and $path->is_file and $path->is_open_ok) {
            my ($usesconfmodule, $obsoleteconfmodule, $db_input, $isdefault);

            my $fd = $path->open;
            # Only check scripts.
            my $fl = <$fd>;
            unless ($fl && $fl =~ /^\#!/) {
                close($fd);
                next;
            }

            while (<$fd>) {
                s/#.*//;    # Not perfect for Perl, but should be OK
                next unless m/\S/;
                while (s%\\$%%) {
                    my $next = <$fd>;
                    last unless $next;
                    $_ .= $next;
                }
                if (   m,(?:\.|source)\s+/usr/share/debconf/confmodule,
                    || m/(?:use|require)\s+Debconf::Client::ConfModule/) {
                    $usesconfmodule=1;
                }
                if (
                    not $obsoleteconfmodule
                    and m,(/usr/share/debconf/confmodule\.sh|
                   Debian::DebConf::Client::ConfModule),x
                  ) {
                    my $cmod = $1;
                    tag 'loads-obsolete-confmodule', "$file:$. $cmod";
                    $usesconfmodule = 1;
                    $obsoleteconfmodule = 1;
                }
                if ($file eq 'config' and m/db_input/) {
                    $config_calls_db_input = 1;
                }
                if (    $file eq 'postinst'
                    and not $db_input
                    and m/db_input/
                    and not $config_calls_db_input) {
                    # TODO: Perl?
                    tag 'postinst-uses-db-input'
                      unless $type eq 'udeb';
                    $db_input=1;
                }
                if (m%/dev/%) {
                    $potential_makedev->{$.} = 1;
                }
                if (
                    m/\A \s*(?:db_input|db_text)\s+
                     [\"\']? (\S+?) [\"\']? \s+ (\S+)\s/xsm
                  ) {
                    my ($priority, $template) = ($1, $2);
                    $templates_used{$template} = 1;
                    if ($priority !~ /^\$\S+$/) {
                        tag 'unknown-debconf-priority', "$file:$. $1"
                          unless ($valid_priorities{$priority});
                        tag 'possible-debconf-note-abuse',
                          "$file:$. $template"
                          if (
                            $potential_db_abuse{$template}
                            and (
                                not($potential_makedev->{($. - 1)}
                                    and ($priority eq 'low')))
                            and ($priority =~ /^(low|medium)$/));
                    }
                }
                if (
                    m/ \A \s* (?:db_get|db_set(?:title)?) \s+ 
                       [\"\']? (\S+?) [\"\']? (?:\s|\Z)/xsm
                  ) {
                    $templates_used{$1} = 1;
                }
                # Try to handle Perl somewhat.
                if (   m/^\s*(?:.*=\s*get|set)\s*\(\s*[\"\'](\S+?)[\"\']/
                    || m/\b(?:metaget|settitle)\s*\(\s*[\"\'](\S+?)[\"\']/) {
                    $templates_used{$1} = 1;
                }
                if (m/^\s*db_register\s+[\"\']?(\S+?)[\"\']?\s+(\S+)\s/) {
                    my ($template, $question) = ($1, $2);
                    push @{$template_aliases{$template}}, $question;
                }
                if (not $isdefault and m/db_fset.*isdefault/) {
                    # TODO: Perl?
                    tag 'isdefault-flag-is-deprecated', $file;
                    $isdefault = 1;
                }
                if (not $db_purge and m/db_purge/) {    # TODO: Perl?
                    $db_purge = 1;
                }
            }

            if ($file eq 'postinst' or $file eq 'config') {
                unless ($usesconfmodule) {
                    tag "$file-does-not-load-confmodule"
                      unless ($type eq 'udeb'
                        || ($file eq 'postinst' && !$seenconfig));
                }
            }

            if ($file eq 'postrm') {
                # If we haven't seen db_purge we emit the tag unless the
                # package is a debconf provider (in which case db_purge
                # won't be available)
                unless ($db_purge or $selfrelation->implies($ANY_DEBCONF)) {
                    tag 'postrm-does-not-purge-debconf';
                }
            }

            close($fd);
        } elsif ($file eq 'postinst') {
            tag 'postinst-does-not-load-confmodule'
              unless ($type eq 'udeb' || !$seenconfig);
        } elsif ($file eq 'postrm') {
            # Make an exception for debconf providing packages as some of
            # them (incl. "debconf" itself) cleans up in prerm and have no
            # postrm script at all.
            tag 'postrm-does-not-purge-debconf'
              unless $type eq 'udeb'
              or $selfrelation->implies($ANY_DEBCONF);
        }
    }

    foreach my $template (@templates_seen) {
        $template =~ s/\s+\Z//;

        my $used = 0;

        if ($templates_used{$template}) {
            $used = 1;
        } else {
            foreach my $alias (@{$template_aliases{$template}}) {
                if ($templates_used{$alias}) {
                    $used = 1;
                    last;
                }
            }
        }

        unless ($used or $pkg eq 'debconf' or $type eq 'udeb') {
            tag 'unused-debconf-template', $template
              unless $template =~ m,^shared/packages-(wordlist|ispell)$,
              or $template =~ m,/languages$,;
        }
    }

    # Check that the right dependencies are in the control file.  Accept any
    # package that might provide debconf functionality.

    if ($usespreinst) {
        unless ($info->relation('pre-depends')->implies($ANY_DEBCONF)) {
            tag 'missing-debconf-dependency-for-preinst'
              unless $type eq 'udeb';
        }
    } else {
        unless ($alldependencies->implies($ANY_DEBCONF) or $usesdbconfig) {
            tag 'missing-debconf-dependency';
        }
    }

    # Now make sure that no scripts are using debconf as a registry.
    # Unfortunately this requires us to unpack to level 2 and grep all the
    # scripts in the package.
    # the following checks is ignored if the package being checked is debconf
    # itself.

    return if ($pkg eq 'debconf') || ($type eq 'udeb');

    foreach my $filename (sort keys %{$info->scripts}) {
        my $path = $info->index_resolved_path($filename);
        next if not $path or not $path->is_open_ok;
        my $fd = $path->open;
        while (<$fd>) {
            s/#.*//;    # Not perfect for Perl, but should be OK
            if (   m,/usr/share/debconf/confmodule,
                or m/(?:Debconf|Debian::DebConf)::Client::ConfModule/) {
                tag 'debconf-is-not-a-registry', $filename;
                last;
            }
        }
        close($fd);
    }

    return;
} # </run>

# -----------------------------------

# Count the number of choices.  Splitting code copied from debconf 1.5.8
# (Debconf::Question).
sub count_choices {
    my ($choices) = @_;
    my @items;
    my $item = '';
    for my $chunk (split /(\\[, ]|,\s+)/, $choices) {
        if ($chunk =~ /^\\([, ])$/) {
            $item .= $1;
        } elsif ($chunk =~ /^,\s+$/) {
            push(@items, $item);
            $item = '';
        } else {
            $item .= $chunk;
        }
    }
    push(@items, $item) if $item ne '';
    return scalar(@items);
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
