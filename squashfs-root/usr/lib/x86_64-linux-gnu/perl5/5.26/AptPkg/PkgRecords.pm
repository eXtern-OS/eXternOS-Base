package AptPkg::PkgRecords;

require 5.005_62;
use strict;
use warnings;
use AptPkg;

our $VERSION = 1.2;

sub lookup
{
    my ($self, $pack) = @_;
    my $xs = $$self;
    my %extra;
    unless (ref $pack)
    {
	my $p = do {
	    my $_p = $xs->cache->FindPkg($pack)	or return;
	    AptPkg::Cache::Package->new($_p);
	};

	my $v = ($p->{VersionList} || [])->[0]	or return;
	$pack = ($v->{FileList}    || [])->[0]	or return;
	$extra{$_} = $v->{$_} for qw/Section VerStr/;

	# Get translated ShortDesc and LongDesc
	if (my $t = $v->{TranslatedDescription})
	{
	    if (my %e = $xs->Lookup($t->{FileList}->_xs))
	    {
		$extra{$_} = $e{$_} for grep /^(Long|Sort)Desc$/, keys %e;;
	    }
	}
    }

    my %r = $xs->Lookup($pack->_xs) or return;
    $r{$_} = $extra{$_} for keys %extra;
    wantarray ? %r : \%r;
}

1;

__END__

=head1 NAME

AptPkg::PkgRecords - APT package description class

=head1 SYNOPSIS

use AptPkg::PkgRecords;

=head1 DESCRIPTION

The AptPkg::PkgRecords module provides an interface to the parsed
contents of package files.

=head2 AptPkg::PkgRecords

The AptPkg::PkgRecords package Implements the B<APT> pkgRecords class.

An instance of the AptPkg::PkgRecords class may be fetched using the
C<packages> method from an AptPkg::Cache object.

=head3 Methods

=over 4

=item lookup(I<PACK>)

Return a hash (or hash reference, depending on context) for the given
package.

I<PACK> may either be an AptPkg::Cache::VerFile object, an
AptPkg::Cache::DescFile object or a package name.

The hash contains the following keys:

=over 4

C<FileName>, C<Checksum-FileSize>, C<MD5Hash>, C<SHA256>, C<SourcePkg>,
C<Maintainer>, C<ShortDesc>, C<LongDesc> and C<Name>.

=back

with values taken from the packages or translation file.

Note that C<LongDesc> is generally not useful for AptPkg::Cache::VerFile
objects, which refer to the Packages file, as these no longer contain the full
description (now in the Translation files).

If I<PACK> is a package name, these additional values are set:

=over 4

C<Section> and C<VerStr>.

=back

and the following values are overriden with the translated versions:

=over 4

C<ShortDesc> and C<LongDesc>.

=back

=back

=head1 SEE ALSO

AptPkg::Cache(3pm), AptPkg(3pm).

=head1 AUTHOR

Brendan O'Dea <bod@debian.org>

=cut
