# -*- perl -*-
# Lintian::Architecture

# Copyright (C) 2011 Niels Thykier
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

package Lintian::Architecture;

use strict;
use warnings;

use Exporter qw(import);

use Lintian::Data;

our (@EXPORT_OK, %EXPORT_TAGS);

@EXPORT_OK = (qw(
      is_arch_wildcard
      is_arch
      is_arch_or_wildcard
      expand_arch_wildcard
      wildcard_includes_arch
));

%EXPORT_TAGS = (all => \@EXPORT_OK);

=encoding utf-8

=head1 NAME

Lintian::Architecture -- Lintian API for handling architectures and wildcards

=head1 SYNOPSIS

 use Lintian::Architecture qw(:all);
 
 print "arch\n" if is_arch ('i386');
 print "wildcard\n" if is_arch_wildcard ('any');
 print "either arch or wc\n" if is_arch_or_wildcard ('linux-any');
 foreach my $arch (expand_arch_wildcard ('any')) {
     print "any expands to $arch\n";
 }

=head1 DESCRIPTION

Lintian API for checking and expanding architectures and architecture
wildcards.  The functions are backed by a L<data|Lintian::Data> file,
so it may be out of date (use private/refresh-archs to update it).

Generally all architecture names are in the format "$os-$arch" and
wildcards are "$os-any" or "any-$cpu", though there are exceptions:

=over 4

=item * "all" is the "architecture independent" architecture.

Source: Policy §5.6.8 (v3.9.3)

=item * "any" is a wildcard matching any architecture except "all".

Source: Policy §5.6.8 (v3.9.3)

=item * All other cases of "$arch" are short for "linux-$arch"

Source: Policy §11.1 (v3.9.3)

=back

Note that the architecture and cpu name are not always identical
(example architecture "armhf" has cpu name "arm").

=head1 FUNCTIONS

The following methods are exportable:

=over 4

=cut

# Setup code

# Valid architecture wildcards.
my %ARCH_WILDCARDS;
# Maps aliases to the "original" arch name.
# (e.g. "linux-amd64" => "amd64")
my %ALT_ARCH_NAMES;

sub _parse_arch {
    my ($archstr, $raw) = @_;
    # NB: "$os-$cpu" ne $archstr in some cases
    my ($os, $cpu) = split /\s++/o, $raw;
    # map $os-any (e.g. "linux-any") and any-$arch (e.g. "any-amd64") to
    # the relevant architectures.
    $ARCH_WILDCARDS{"$os-any"}{$archstr} = 1;
    $ARCH_WILDCARDS{"any-$cpu"}{$archstr} = 1;
    $ARCH_WILDCARDS{'any'}{$archstr} = 1;
    if ($os eq 'linux') {
        my ($long, $short);
        # Per Policy §11.1 (3.9.3):
        #
        #"""[architecture] strings are in the format "os-arch", though
        # the OS part is sometimes elided, as when the OS is Linux."""
        #
        # i.e. "linux-amd64" and "amd64" are aliases, so handle them
        # as such.  Currently, dpkg-architecture -L gives us "amd64"
        # but in case it changes to "linux-amd64", we are prepared.
        if ($archstr =~ m/^linux-/) {
            # It may be temping to use $cpu here, but it does not work
            # for (e.g.) arm based architectures.  Instead extract the
            # "short" architecture name from $archstr
            (undef, $short) = split m/-/, $archstr, 2;
            $long = $archstr;
        } else {
            $short = $archstr;
            $long = "$os-$short";
        }
        $ALT_ARCH_NAMES{$short} = $archstr;
        $ALT_ARCH_NAMES{$long} = $archstr;
    }
    return 1;
}

my $ARCH_RAW = Lintian::Data->new('common/architectures', qr/\s*+\Q||\E\s*+/o,
    \&_parse_arch);

=item is_arch_wildcard ($wc)

Returns a truth value if $wc is a known architecture wildcard.

Note: 'any' is considered a wildcard and not an architecture.

=cut

sub is_arch_wildcard {
    my ($wc) = @_;
    $ARCH_RAW->known('any') unless %ARCH_WILDCARDS;
    return exists $ARCH_WILDCARDS{$wc} ? 1 : 0;
}

=item is_arch ($arch)

Returns a truth value if $arch is (an alias of) a Debian machine
architecture OR the special value "all".  It returns a false value for
architecture wildcards (including "any") and unknown architectures.

=cut

sub is_arch {
    my ($arch) = @_;
    return 0 if $arch eq 'any';
    return 1
      if $arch eq 'all'
      or $ARCH_RAW->known($arch)
      or exists $ALT_ARCH_NAMES{$arch};
    return 0;
}

=item is_arch_or_wildcard ($arch)

Returns a truth value if $arch is either an architecture or an
architecture wildcard.

Shorthand for:

 is_arch ($arch) || is_arch_wildcard ($arch)

=cut

sub is_arch_or_wildcard {
    my ($arch) = @_;
    return is_arch($arch) || is_arch_wildcard($arch);
}

=item expand_arch_wildcard ($wc)

Returns a list of architectures that this wildcard expands to.  No
order is guaranteed (even between calls).  Returned values must not be
modified.

Note: This list is based on the architectures in Lintian's data file.
However, many of these are not supported or used in Debian or any of
its derivatives.

The returned values matches the list generated by dpkg-architecture -L,
so the returned list may use (e.g.) "amd64" for "linux-amd64".

=cut

sub expand_arch_wildcard {
    my ($wc) = @_;
    # Load the wildcards if it has not been done yet.
    $ARCH_RAW->known('any') unless %ARCH_WILDCARDS;
    return () unless exists $ARCH_WILDCARDS{$wc};
    return keys %{ $ARCH_WILDCARDS{$wc} };
}

=item wildcard_includes_arch ($wc, $arch)

Returns a truth value if $arch is included in the list of
architectures that $wc expands to.

This is generally faster than

  grep { $_ eq $arch } expand_arch_wildcard ($wc)

It also properly handles cases like "linux-amd64" and "amd64" being
aliases.

=cut

sub wildcard_includes_arch {
    my ($wc, $arch) = @_;
    # Load the wildcards if it has not been done yet.
    $ARCH_RAW->known('any') unless %ARCH_WILDCARDS;
    $arch = $ALT_ARCH_NAMES{$arch} if exists $ALT_ARCH_NAMES{$arch};
    return exists $ARCH_WILDCARDS{$wc}{$arch} ? 1 : 0;
}

=back



=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
