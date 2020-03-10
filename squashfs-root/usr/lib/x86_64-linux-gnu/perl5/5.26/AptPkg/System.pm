package AptPkg::System;

require 5.005_62;
use strict;
use warnings;
use AptPkg;

require Exporter;

our @ISA = qw(Exporter);
our @EXPORT_OK = qw($_system);
our @EXPORT = ();

our $VERSION = 1.4;
our $_system;

sub label      { shift->Label(@_) }
sub lock       { shift->Lock(@_) }
sub unlock     { shift->UnLock(@_) }

sub versioning
{
    require AptPkg::Version;
    shift->VS(@_)
}

1;

__END__

=head1 NAME

AptPkg::System - APT system abstraction class

=head1 SYNOPSIS

use AptPkg::System;

=head1 DESCRIPTION

The AptPkg::System module provides an interface to B<APT>'s system
abstraction mechanism.

=head2 AptPkg::System

The AptPkg::System package implements the B<APT> pkgSystem class.

An instance of the AptPkg::System class appropriate for the particular
back-end packaging system (deb, rpm, etc.) may be fetched using the
system method from AptPkg::Config.

A global instance of the libapt-pkg _system instance is provided as
$AptPkg::System::_system, and may be imported.

The following methods are implemented:

=over 4

=item label

Return the description of the packaging system, for example:

    Debian dpkg interface

for Debian systems.

=item lock

Lock the packaging system.

=item unlock(I<QUIET>)

Unlock the packaging system, ignoring errors if I<QUIET> is non-zero.

=item versioning

Return an instance of the AptPkg::Version class for this system.

=back

=head1 SEE ALSO

AptPkg::Config(3pm), AptPkg::Version(3pm), AptPkg(3pm).

=head1 AUTHOR

Brendan O'Dea <bod@debian.org>

=cut
