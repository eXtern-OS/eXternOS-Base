package AptPkg::Source;

require 5.005_62;
use strict;
use warnings;
use AptPkg;
use AptPkg::hash;

require Exporter;

our @ISA = qw(Exporter AptPkg::hash);
our @EXPORT = ();
our $VERSION = 1.4;

sub new
{
    my $class = shift;
    my $srclist = AptPkg::_source_list->new(@_);
    my $xs = AptPkg::_src_records->new($srclist);
    my $self = $class->SUPER::new($xs);
    $self->_priv->{srclist} = $srclist;
    $self;
}

sub exists { scalar shift->_xs->Find(@_) }
sub find
{
    my $self = shift;
    $self->_xs->Restart;

    return $self->_xs->Find(@_) unless wantarray;

    my @r;
    while (my %m = $self->_xs->Find(@_)) { push @r, \%m }
    @r;
}

sub get
{
    my $self = shift;
    my @r = $self->find(@_);
    wantarray ? @r : [ @r ];
}

1;

__END__

=head1 NAME

AptPkg::Source - APT source package interface

=head1 SYNOPSIS

use AptPkg::Source;

=head1 DESCRIPTION

The AptPkg::Source module provides an interface to B<APT>'s source
package lists.

=head2 AptPkg::Source

The AptPkg::Source package implements the B<APT> pkgSrcRecords class
as a hash reference (inherits from AptPkg::hash).  The hash is keyed
on source or binary package name and the value is an array reference
of the details of matching source packages.

Note that there is no iterator class, so it is not possible to get a
list of all keys (with keys or each).

=head3 Constructor

=over 4

=item new([I<SOURCELIST>])

Instantiation of the object uses configuration from the
$AptPkg::Config::_config object (automatically initialised if not done
explicitly).

If no I<SOURCELIST> is specified, then the value of
Dir::Etc::sourcelist from the configuration object is used (generally
/etc/apt/sources.list).

=back

=head3 Methods

=over 4

=item find(I<PACK>, [I<SRCONLY>])

In a list context, return a list of source package details for the
given I<PACK>, which may either be a source package name, or the name
of one of the binaries provided (unless I<SRCONLY> is provided and
true).

In a scalar context, the source package name of the first entry is
returned.

=item get, exists

These methods are used to implement the hashref abstraction:
$obj->get($pack) and $obj->{$pack} are equivalent.

The get method has the same semantics as find, but returns an array
reference in a scalar context.

=back

The list returned by the find (and get) methods consists of hashes
which describe each available source package (in order of discovery
from the deb-src files described in sources.list).

Each hash contains the following entries:

=over 4

=item Package

=item Version

=item Maintainer

=item Section

Strings giving the source package name, version, maintainer and
section.

=item AsStr

The full source record as a string in L<Debian control file syntax|https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-controlsyntax>,
which is an RFC822-like set of key-value pairs with the values potentially
wrapped.  It is relatively trivial to parse:

  my %fields = map { split /:\s+/ } split /\n(?! )/, $as_str;

=item Binaries

A list of binary package names from the package.

=item BuildDepends

A hash describing the build dependencies of the package.  Possible
keys are:

=over 4

C<Build-Depends>, C<Build-Depends-Indep>, C<Build-Conflicts>,
C<Build-Conflicts-Indep>.

=back

The values are a list of dependencies/conflicts with each item being a
list containing the package name followed optionally by an operator
and version number.

Operator values evaluate to a comparison string* (>, >=, etc) or one
of the AptPkg::Dep:: constants in a numeric context (see
L<AptPkg(3pm)/"pkgCache::Dep::DepCompareOp">).

*Note that this is a normalised, rather than Debian-style (>> vs >)
string.

=item Files

A list of files making up the source package, each described by a hash
containing the keys:

=over 4

C<Checksum-FileSize>, C<MD5Hash>, C<SHA256>, C<Size>, C<ArchiveURI>,
C<Type>.

=back

=back

=head1 SEE ALSO

AptPkg::Config(3pm), AptPkg::Cache(3pm), AptPkg(3pm), AptPkg::hash(3pm).

=head1 AUTHOR

Brendan O'Dea <bod@debian.org>

=cut
