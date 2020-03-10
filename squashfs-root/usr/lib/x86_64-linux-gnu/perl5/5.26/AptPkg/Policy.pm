package AptPkg::Policy;

require 5.005_62;
use strict;
use warnings;
use AptPkg;

our $VERSION = 1.1;

sub priority
{
    my ($self, $arg) = @_;
    my $xs = $$self;
    $xs->GetPriority($arg->_xs);
}

sub match
{
    my ($self, $pkg) = @_;
    my $xs = $$self;
    my $ver = $xs->GetMatch($pkg->_xs) or return;
    AptPkg::Cache::Version->new($ver);
}

sub candidate
{
    my ($self, $pkg) = @_;
    my $xs = $$self;
    my $ver = $xs->GetCandidateVer($pkg->_xs) or return;
    AptPkg::Cache::Version->new($ver);
}

1;

__END__

=head1 NAME

AptPkg::Policy - APT package version policy class

=head1 SYNOPSIS

use AptPkg::Policy;

=head1 DESCRIPTION

The AptPkg::Policy module provides an interface to B<APT>'s package
version policy.

=head2 AptPkg::Policy

The AptPkg::Policy package implements the B<APT> pkgPolicy class.

An instance of the AptPkg::Policy class may be fetched using the
C<policy> method from an AptPkg::Cache object.

The following methods are implemented:

=over 4

=item priority(I<PKG>|I<FILE>)

Return the pin priority for the given I<PKG> (AptPkg::Cache::Package)
or I<FILE> (AptPkg::Cache::PkgFile) object.

=item match(I<PKG>)

Find the pinned version of I<PKG>.  Returns an AptPkg::Cache::Version
object.

=item candidate(I<PKG>)

Returns the installation candidate version for I<PKG>.

=back

=head1 SEE ALSO

AptPkg::Cache(3pm), AptPkg(3pm).

=head1 AUTHOR

Brendan O'Dea <bod@debian.org>

=cut
