# dbus -- lintian check script, vaguely based on apache2 -*- perl -*-
#
# Copyright © 2012 Arno Töll
# Copyright © 2014 Collabora Ltd.
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

package Lintian::dbus;

use strict;
use warnings;
use autodie;

use Lintian::Tags qw(tag);

sub run {
    my ($pkg, $type, $info) = @_;

    my @files;
    foreach my $dirname (qw(session system)) {
        if (my $dir = $info->index_resolved_path("etc/dbus-1/${dirname}.d")) {
            push @files, $dir->children;
        }
    }

    foreach my $file (@files) {
        next unless $file->is_open_ok;
        _check_policy($file);
    }

    if (my $dir = $info->index_resolved_path('usr/share/dbus-1/services')) {
        foreach my $file ($dir->children) {
            next unless $file->is_open_ok;
            _check_service($file, session => 1);
        }
    }

    if (my $dir
        = $info->index_resolved_path('usr/share/dbus-1/system-services')) {
        foreach my $file ($dir->children) {
            next unless $file->is_open_ok;
            _check_service($file);
        }
    }

    return;
}

my $PROPERTIES = 'org.freedesktop.DBus.Properties';

sub _check_policy {
    my ($file) = @_;

    my $xml = $file->file_contents;

    # Parsing XML via regexes is evil, but good enough here...
    # note that we are parsing the entire file as one big string,
    # so that we catch <policy\nat_console="true"\n> or whatever.

    my @rules;
    # a small rubbish state machine: we want to match a <policy> containing
    # any <allow> or <deny> rule that is about sending
    my $policy = '';
    while ($xml =~ m{(<policy[^>]*>)|(</policy\s*>)|(<(?:allow|deny)[^>]*>)}sg)
    {
        if (defined $1) {
            $policy = $1;
        } elsif (defined $2) {
            $policy = '';
        } else {
            push(@rules, $policy.$3);
        }
    }
    foreach my $rule (@rules) {
        # normalize whitespace a bit so we can report it sensibly:
        # typically it will now look like
        # <policy context="default"><allow send_destination="com.example.Foo"/>
        $rule =~ s{\s+}{ }g;

        if ($rule =~ m{send_} && $rule !~ m{send_destination=}) {
            # It is about sending but does not specify a send-destination.
            # This could be bad.

            if ($rule =~ m{[^>]*user=['"]root['"].*<allow}) {
                # skip it: it's probably the "agent" pattern (as seen in
                # e.g. BlueZ), and cannot normally be a security flaw
                # because root can do anything anyway
            } else {
                tag('dbus-policy-without-send-destination', $file, $rule);

                if (   $rule =~ m{send_interface=}
                    && $rule !~ m{send_interface=['"]\Q${PROPERTIES}\E['"]}) {
                    # That's undesirable, because it opens up communication
                    # with arbitrary services and can undo DoS mitigation
                    # efforts; but at least it's specific to an interface
                    # other than o.fd.DBus.Properties, so all that should
                    # happen is that the service sends back an error message.
                    #
                    # Properties doesn't count as an effective limitation,
                    # because it's a sort of meta-interface.
                } elsif ($rule =~ m{<allow}) {
                    # Looks like CVE-2014-8148 or similar. This is really bad;
                    # emit an additional tag.
                    tag('dbus-policy-excessively-broad', $file, $rule);
                }
            }
        }

        if ($rule =~ m{at_console=['"]true}) {
            tag('dbus-policy-at-console', $file, $rule);
        }
    }

    return;
}

sub _check_service {
    my ($file, %kwargs) = @_;

    my $basename = $file->basename;
    my $text = $file->file_contents;

    while ($text =~ m{^Name=(.*)$}gm) {
        my $name = $1;
        if ($basename ne "${name}.service") {
            if ($kwargs{session}) {
                tag('dbus-session-service-wrong-name',
                    "${name}.service", $file);
            } else {
                tag('dbus-system-service-wrong-name',"${name}.service", $file);
            }
        }
    }

    return;
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
