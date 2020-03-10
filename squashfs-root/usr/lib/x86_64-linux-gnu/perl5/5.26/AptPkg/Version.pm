package AptPkg::Version;

require 5.005_62;
use strict;
use warnings;
use AptPkg;
use Carp;

require Exporter;

our @ISA = qw(Exporter);
our @EXPORT_OK = qw();
our @EXPORT = ();

our $VERSION = 1.7;

sub label       { shift->Label(@_) }
sub compare     { shift->CmpVersion(@_) }
sub rel_compare { shift->CmpReleaseVer(@_) }
sub upstream    { shift->UpstreamVersion(@_) }

{
    my %DEB_RELATION = (
	'<<'	=> AptPkg::Dep::Less,
	'<='	=> AptPkg::Dep::LessEq,
	'='	=> AptPkg::Dep::Equals,
	'>='	=> AptPkg::Dep::GreaterEq,
	'>>'	=> AptPkg::Dep::Greater,

	# deprecated
	'<'	=> AptPkg::Dep::LessEq,
	'>'	=> AptPkg::Dep::GreaterEq,
    );

    sub check_dep
    {
	my $self = shift;
	my ($pkg, $op_str, $dep) = @_;
	my $op = $DEB_RELATION{$op_str} || croak "invalid relation for check_dep `$op_str'";

	$self->CheckDep($pkg, $op, $dep);
    }
}

1;

__END__

=head1 NAME

AptPkg::Version - APT package versioning class

=head1 SYNOPSIS

use AptPkg::Version;

=head1 DESCRIPTION

The AptPkg::Version module provides an interface to B<APT>'s package
version handling.

=head2 AptPkg::Version

The AptPkg::Version package implements the B<APT> pkgVersioningSystem
class.

An instance of the AptPkg::Version class may be fetched using the
C<versioning> method from an AptPkg::System object.

The following methods are implemented:

=over 4

=item label

Return the description of the versioning system, for example:

    Standard .deb

for Debian systems.

=item compare(I<A>, I<B>)

Compare package version I<A> with I<B>, returning a negative value if
I<A> is an earlier version than I<B>, zero if the same or a positive
value if I<A> is later.

=item rel_compare(I<A>, I<B>)

Compare distribution release numbers.

=item check_dep(I<PKG>, I<OP>, I<DEP>)

Check that the package version I<PKG> satisfies the relation I<OP> to
the dependency version I<DEP>.

The relation I<OP> is specified in the Debian syntax regardless of the
versioning system:

    <<	strictly earlier
    <=	earlier or equal
    =	exactly equal
    >=	later or equal
    >>	strictly later

=item upstream(I<VER>)

Return the upstream component of the given version string.

=back

=head1 SEE ALSO

AptPkg::Config(3pm), AptPkg::System(3pm), AptPkg(3pm).

=head1 AUTHOR

Brendan O'Dea <bod@debian.org>

=cut
