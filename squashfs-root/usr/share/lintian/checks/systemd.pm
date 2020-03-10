# systemd -- lintian check script -*- perl -*-
#
# Copyright © 2013 Michael Stapelberg
#
# based on the apache2 checks file by:
# Copyright © 2012 Arno Töll
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

package Lintian::systemd;

use strict;
use warnings;
use autodie;

use File::Basename;
use List::MoreUtils qw(any first_index);
use Text::ParseWords qw(shellwords);

use Lintian::Tags qw(tag);
use Lintian::Util qw(internal_error lstrip rstrip);

use Lintian::Data;

# Init script that do not need a service file
my $INIT_WHITELIST = Lintian::Data->new('systemd/init-whitelist');

# Usual WantedBy= targets
my $WANTEDBY_WHITELIST = Lintian::Data->new('systemd/wantedby-whitelist');

sub run {
    my ($pkg, undef, $info) = @_;

    # non-service checks
    if (my $tmpfiles = $info->index_resolved_path('etc/tmpfiles.d/')) {
        for my $file ($tmpfiles->children('breadth-first')) {
            if ($file->basename =~ m,\.conf$,) {
                tag 'systemd-tmpfiles.d-outside-usr-lib', $file;
            }
        }
    }

    my @init_scripts = get_init_scripts($info);
    my @service_files = get_systemd_service_files($pkg, $info);

    # A hash of names reference which are provided by the service files.
    # This includes Alias= directives, so after parsing
    # NetworkManager.service, it will contain NetworkManager and
    # network-manager.
    my $services = get_systemd_service_names($info, \@service_files);

    for my $script (@init_scripts) {
        check_init_script($info, $script, $services);
    }

    check_maintainer_scripts($info);
    return;
}

sub get_init_service_name {
    my ($file) = @_;
    my $basename = $file->basename;
    # sysv generator drops the .sh suffix
    $basename =~ s/\.sh$//;
    return $basename;
}

sub get_init_scripts {
    my ($info) = @_;
    my @scripts;
    if (my $initd_path = $info->index_resolved_path('etc/init.d/')) {
        for my $init_script ($initd_path->children) {
            # sysv generator drops the .sh suffix
            my $basename = get_init_service_name($init_script);
            next if $INIT_WHITELIST->known($basename);
            next
              if $init_script->is_symlink
              && $init_script->link eq '/lib/init/upstart-job';

            push(@scripts, $init_script);
        }
    }
    return @scripts;
}

# Verify that each init script includes /lib/lsb/init-functions,
# because that is where the systemd diversion happens.
sub check_init_script {
    my ($info, $file, $services) = @_;
    my $basename = $file->basename;
    my $servicename = get_init_service_name($file);
    my $lsb_source_seen;
    my $is_rcs_script = 0;

    if (!$file->is_regular_file) {
        unless ($file->is_open_ok) {
            tag 'init-script-is-not-a-file', $file;
            return;
        }
    }
    my $fh = $file->open;
    while (<$fh>) {
        lstrip;
        if ($. == 1 and m{\A [#]! \s*/lib/init/init-d-script}xsm) {
            $lsb_source_seen = 1;
        }
        if (m,#.*Default-Start:.*S,) {
            $is_rcs_script = 1;
        }

        next if /^#/;
        if (m,(?:\.|source)\s+/lib/(?:lsb/init-functions|init/init-d-script),){
            $lsb_source_seen = 1;
        }
    }
    close($fh);

    tag 'init.d-script-does-not-source-init-functions', $file
      unless $lsb_source_seen;

    if (!$services->{$servicename}) {
        # rcS scripts are particularly bad; always tag
        if ($is_rcs_script) {
            tag 'missing-systemd-service-for-init.d-rcS-script', $basename;
        } else {
            if (%{$services}) {
                tag 'omitted-systemd-service-for-init.d-script', $basename;
            } else {
                tag 'missing-systemd-service-for-init.d-script', $basename;
            }
        }
    }

    return;
}

sub get_systemd_service_files {
    my ($pkg, $info) = @_;
    my @res;
    my @potential
      = grep { m,/systemd/system/.*\.service$, } $info->sorted_index;

    for my $file (@potential) {
        push(@res, $file) if check_systemd_service_file($pkg, $info, $file);
    }
    return @res;
}

sub get_systemd_service_names {
    my ($info,$files_ref) = @_;
    my %services;

    my $safe_add_service = sub {
        my ($name) = @_;
        if (exists $services{$name}) {
            # should add a tag here
            return;
        }
        $services{$name} = 1;
    };

    for my $file (@{$files_ref}) {
        my $name = $file->basename;
        $name =~ s/\.service$//;
        $safe_add_service->($name);

        my @aliases= extract_service_file_values($file, 'Install', 'Alias', 1);

        for my $alias (@aliases) {
            tag 'systemd-service-alias-without-extension', $file
              if $alias !~ m/\.service$/;
            $alias =~ s/\.service$//;
            $safe_add_service->($alias);
        }
    }
    return \%services;
}

sub check_systemd_service_file {
    my ($pkg, $info, $file) = @_;

    tag 'systemd-service-file-outside-lib', $file
      if ($file =~ m,^etc/systemd/system/,);
    tag 'systemd-service-file-outside-lib', $file
      if ($file =~ m,^usr/lib/systemd/system/,);

    unless ($file->is_open_ok
        || ($file->is_symlink && $file->link eq '/dev/null')) {
        tag 'service-file-is-not-a-file', $file;
        return 0;
    }
    my @values = extract_service_file_values($file, 'Unit', 'After');
    my @obsolete = grep { /^(?:syslog|dbus)\.target$/ } @values;
    tag 'systemd-service-file-refers-to-obsolete-target', $file, $_
      for @obsolete;

    tag 'systemd-service-file-refers-to-obsolete-bindto', $file,
      if extract_service_file_values($file, 'Unit', 'BindTo', 1);

    for my $key (
        qw(ExecStart ExecStartPre ExecStartPost ExecReload ExecStop ExecStopPost)
      ) {
        tag 'systemd-service-file-wraps-init-script', $file, $key
          if any { m,^/etc/init\.d/, }
        extract_service_file_values($file, 'Service', $key, 1);
    }

    if (not $file->is_symlink or $file->link ne '/dev/null') {
        my @wanted_by
          = extract_service_file_values($file, 'Install', 'WantedBy',1);
        foreach my $target (@wanted_by) {
            tag 'systemd-service-file-refers-to-unusual-wantedby-target',
              $file, $target
              unless any { $target eq $_ } $WANTEDBY_WHITELIST->all
              or $pkg eq 'systemd';
        }
        tag 'systemd-service-file-missing-documentation-key', $file,
          unless extract_service_file_values($file, 'Unit', 'Documentation',1);
        #<<< no perltidy - These are better formatted one per line
        tag 'systemd-service-file-missing-install-key', $file,
          unless @wanted_by
          or extract_service_file_values($file, 'Install', 'RequiredBy',1)
          or extract_service_file_values($file, 'Install', 'Also',1)
          or any { /^oneshot$/ } extract_service_file_values($file, 'Service', 'Type')
          or $file =~ m,@\.service$,;
        #>>>
    }

    return 1;
}

sub service_file_lines {
    my ($path) = @_;
    my (@lines, $continuation);
    return if $path->is_symlink and $path->link eq '/dev/null';

    my $fh = $path->open;
    while (<$fh>) {
        chomp;

        if (defined($continuation)) {
            $_ = $continuation . $_;
            $continuation = undef;
        }

        if (/\\$/) {
            $continuation = $_;
            $continuation =~ s/\\$/ /;
            next;
        }

        rstrip;

        next if $_ eq '';

        next if /^[#;\n]/;

        push @lines, $_;
    }
    close($fh);

    return @lines;
}

# Extracts the values of a specific Key from a .service file
sub extract_service_file_values {
    my ($file, $extract_section, $extract_key, $skip_tag) = @_;

    my (@values, $section);

    my @lines = service_file_lines($file);
    my $key_ws = first_index { /^[[:alnum:]]+(\s*=\s|\s+=)/ } @lines;
    if ($key_ws > -1) {
        tag 'service-key-has-whitespace', $file, 'at line', $key_ws
          unless $skip_tag;
    }
    if (any { /^\.include / } @lines) {
        my $parent_dir = $file->parent_dir;
        @lines = map {
            if (/^\.include (.+)$/) {
                my $path = $parent_dir->resolve_path($1);
                if (defined($path)
                    && $path->is_open_ok) {
                    service_file_lines($path);
                } else {
                    # doesn't exist, exists but not a file or "out-of-bounds"
                    $_;
                }
            } else {
                $_;
            }
        } @lines;
    }
    for (@lines) {
        # section header
        if (/^\[([^\]]+)\]$/) {
            $section = $1;
            next;
        }

        if (!defined($section)) {
            # Assignment outside of section. Ignoring.
            next;
        }

        my ($key, $value) = ($_ =~ m,^(.*)\s*=\s*(.*)$,);
        if (   $section eq $extract_section
            && $key eq $extract_key) {
            if ($value eq '') {
                # Empty assignment resets the list
                @values = ();
            } else {
                push(@values, shellwords($value));
            }
        }
    }

    return @values;
}

sub check_maintainer_scripts {
    my ($info) = @_;

    open(my $fd, '<', $info->lab_data_path('control-scripts'));

    while (<$fd>) {
        m/^(\S*) (.*)$/
          or internal_error("bad line in control-scripts file: $_");
        my $interpreter = $1;
        my $file = $2;
        my $path = $info->control_index_resolved_path($file);

        # Don't follow unsafe links
        next if not $path or not $path->is_open_ok;
        # Don't try to parse the file if it does not appear to be a
        # shell script
        next if $interpreter !~ m/sh\b/;

        my $sfd = $path->open;
        while (<$sfd>) {
            # skip comments
            next if substr($_, 0, $-[0]) =~ /#/;

            # systemctl should not be called in maintainer scripts at all,
            # except for systemctl --daemon-reload calls.
            if (m/^(?:.+;)?\s*systemctl\b/ && !/daemon-reload/) {
                tag 'maintainer-script-calls-systemctl', "$file:$.";
            }
        }
        close($sfd);
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
