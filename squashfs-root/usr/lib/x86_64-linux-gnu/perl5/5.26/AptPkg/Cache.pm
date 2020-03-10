package AptPkg::Cache;

require 5.005_62;
use strict;
use warnings;
use AptPkg;
use AptPkg::hash;

require Exporter;

our @ISA = qw(Exporter AptPkg::hash);
our @EXPORT = ();
our $VERSION = 1.25;

sub new
{
    my $class = shift;
    my $self = $class->SUPER::new;
    $self->_xs->Open(@_) ? $self : undef;
}

sub files
{
    my $self = shift;
    my $files = $self->_priv->{files} ||= [
	map AptPkg::Cache::PkgFile->new($_), $self->_xs->FileList
    ];

    wantarray ? @$files : $files;
}

sub packages
{
    my $self = shift;
    $self->_priv->{packages} ||= do {
	require AptPkg::PkgRecords;
	bless \$self->_xs->Packages, 'AptPkg::PkgRecords';
    };
}

sub policy
{
    my $self = shift;
    $self->_priv->{policy} ||= do {
	require AptPkg::Policy;
	bless \$self->_xs->Policy, 'AptPkg::Policy';
    };
}

sub exists { shift->_xs->FindPkg(@_) }
sub get
{
    my $value = shift->exists(@_);
    $value ? AptPkg::Cache::Package->new($value) : undef;
}

sub is_multi_arch { shift->_xs->MultiArchCache() }
sub native_arch { shift->_xs->NativeArch() }

package AptPkg::Cache::Iter;

sub new
{
    my $class = shift;
    my $obj = shift;
    my $self = $obj->_xs->PkgBegin(@_);

    bless \$self, $class;
}

sub next
{
    my $self = shift;
    my $obj = $$self or return;
    my $key = $obj->FullName;
    $obj->Next or $$self = undef;
    $key;
}

package AptPkg::Cache;

# helper functions to convert XS iterators to tied hashes
sub _make_class
{
    my ($obj, $class) = @_;
    (my $method = (caller 1)[3]) =~ s/^.*:://;
    my $value = $obj->_xs->$method or return;
    $class->new($value);
}

sub _make_class_list
{
    my ($obj, $class) = @_;
    (my $method = (caller 1)[3]) =~ s/^.*:://;
    my @values = $obj->_xs->$method or return;
    [ map $class->new($_), @values ];
}

package AptPkg::Cache::Package;

our @ISA = qw(AptPkg::hash::method);
our @KEYS = qw(
    Name FullName ShortName Arch Section VersionList CurrentVer RevDependsList
    ProvidesList Index SelectedState InstState CurrentState Flags
);

sub ShortName
{
    # Same as Name for native, and FullName for non-native packages.
    shift->_xs->FullName(1); # Pretty=true
}

sub VersionList
{
    AptPkg::Cache::_make_class_list shift, 'AptPkg::Cache::Version';
}

sub CurrentVer
{
    AptPkg::Cache::_make_class shift, 'AptPkg::Cache::Version';
}

sub RevDependsList
{
    AptPkg::Cache::_make_class_list shift, 'AptPkg::Cache::Depends';
}

sub ProvidesList
{
    AptPkg::Cache::_make_class_list shift, 'AptPkg::Cache::Provides';
}

package AptPkg::Cache::Package::Iter;
our @ISA = qw(AptPkg::hash::method::iter);

package AptPkg::Cache::Version;

our @ISA = qw(AptPkg::hash::method);
our @KEYS = qw(
    VerStr Section Arch MultiArch ParentPkg DescriptionList
    TranslatedDescription DependsList ProvidesList FileList InstalledSize
    Size Index Priority
);

sub ParentPkg
{
    AptPkg::Cache::_make_class shift, 'AptPkg::Cache::Package';
}

sub DescriptionList
{
    AptPkg::Cache::_make_class_list shift, 'AptPkg::Cache::Description';
}

sub TranslatedDescription
{
    AptPkg::Cache::_make_class shift, 'AptPkg::Cache::Description';
}

sub DependsList
{
    AptPkg::Cache::_make_class_list shift, 'AptPkg::Cache::Depends';
}

sub ProvidesList
{
    AptPkg::Cache::_make_class_list shift, 'AptPkg::Cache::Provides';
}

sub FileList
{
    AptPkg::Cache::_make_class_list shift, 'AptPkg::Cache::VerFile';
}

package AptPkg::Cache::Version::Iter;
our @ISA = qw(AptPkg::hash::method::iter);

package AptPkg::Cache::Depends;

our @ISA = qw(AptPkg::hash::method);
our @KEYS = qw(
    TargetVer TargetPkg ParentVer ParentPkg Index CompType CompTypeDeb
    DepType
);

sub TargetPkg { AptPkg::Cache::_make_class shift, 'AptPkg::Cache::Package' }
sub ParentVer { AptPkg::Cache::_make_class shift, 'AptPkg::Cache::Version' }
sub ParentPkg { AptPkg::Cache::_make_class shift, 'AptPkg::Cache::Package' }

package AptPkg::Cache::Depends::Iter;
our @ISA = qw(AptPkg::hash::method::iter);

package AptPkg::Cache::Provides;

our @ISA = qw(AptPkg::hash::method);
our @KEYS = qw(Name ProvideVersion OwnerVer OwnerPkg Index);

sub OwnerVer { AptPkg::Cache::_make_class shift, 'AptPkg::Cache::Version' }
sub OwnerPkg { AptPkg::Cache::_make_class shift, 'AptPkg::Cache::Package' }

package AptPkg::Cache::Provides::Iter;
our @ISA = qw(AptPkg::hash::method::iter);

package AptPkg::Cache::Description;

our @ISA = qw(AptPkg::hash::method);
our @KEYS = qw(LanguageCode md5 FileList);

sub FileList
{
    AptPkg::Cache::_make_class shift, 'AptPkg::Cache::DescFile';
}


package AptPkg::Cache::Description::Iter;
our @ISA = qw(AptPkg::hash::method::iter);

package AptPkg::Cache::PkgFile;
package AptPkg::Cache::PkgFile;

our @ISA = qw(AptPkg::hash::method);
our @KEYS = qw(
    FileName Archive Component Version Origin Label Site Index IndexType IsOk
);

package AptPkg::Cache::PkgFile::Iter;
our @ISA = qw(AptPkg::hash::method::iter);

package AptPkg::Cache::VerFile;

our @ISA = qw(AptPkg::hash::method);
our @KEYS = qw(File Index Offset Size);

sub File { AptPkg::Cache::_make_class shift, 'AptPkg::Cache::PkgFile' }

package AptPkg::Cache::VerFile::Iter;
our @ISA = qw(AptPkg::hash::method::iter);

package AptPkg::Cache::DescFile;

our @ISA = qw(AptPkg::hash::method);
our @KEYS = qw(File);

sub File { AptPkg::Cache::_make_class shift, 'AptPkg::Cache::PkgFile' }

package AptPkg::Cache::DescFile::Iter;
our @ISA = qw(AptPkg::hash::method::iter);

1;

__END__

=head1 NAME

AptPkg::Cache - APT package cache interface

=head1 SYNOPSIS

use AptPkg::Cache;

=head1 DESCRIPTION

The AptPkg::Cache module provides an interface to B<APT>'s package
cache.

=head2 AptPkg::Cache

The AptPkg::Cache package implements the B<APT> pkgCacheFile class as
a hash reference (inherits from AptPkg::hash).  The hash keys are the
names of packages in the cache, and the values are
AptPkg::Cache::Package objects (which in turn appear as hash
references, see below).

=head3 Constructor

=over 4

=item new([I<LOCK>])

Instantiation of the object uses configuration from the
$AptPkg::Config::_config and $AptPkg::System::_system objects
(automatically initialised if not done explicitly).

The cache initialisation can be quite verbose--controlled by the value
of $_config->{quiet}, which is set to "2" (quiet) if the $_config
object is auto-initialised.

The cache directory is locked if LOCK is true.

It is important to note that the structure of the returned object
contains self-referential elements, so some care must be taken if
attempting to traverse it recursively.

=back

=head3 Methods

=over 4

=item files

Return a list of AptPkg::Cache::PkgFile objects describing the package
files.

=item packages

Return an AptPkg::PkgRecords object which may be used to retrieve
additional information about packages.

=item get, exists, keys

These methods are used to implement the hashref abstraction:
$obj->get($pack) and $obj->{$pack} are equivalent.

=item is_multi_arch

Cache is multi-arch enabled.

=item native_arch

Native architecture.

=back

=head2 AptPkg::Cache::Package

Implements the B<APT> pkgCache::PkgIterator class as a hash reference.

=head3 Keys

=over 4

=item Name

=item Section

=item Arch

Package name, section and architecture.

=item FullName

Fully qualified name, including architecture.

=item ShortName

The shortest unambiguous package name: the same as C<Name> for native
packages, and C<FullName> for non-native.

=item SelectedState

=item InstState

=item CurrentState

Package state from the status file.

SelectedState may be C<Unknown>, C<Install>, C<Hold>, C<DeInstall> or
C<Purge>.

InstState may be C<Ok>, C<ReInstReq>, C<HoldInst> or C<HoldReInstReq>.

CurrentState may be C<NotInstalled>, C<UnPacked>, C<HalfConfigured>,
C<HalfInstalled>, C<ConfigFiles> or C<Installed>.

In a numeric context, SelectedState, InstState and CurrentState
evaluate to an AptPkg::State:: constant.

=item VersionList

A reference to an array of AptPkg::Cache::Version objects describing
available versions of the package.

=item CurrentVer

An AptPkg::Cache::Version object describing the currently installed
version (if any) of the package.

=item RevDependsList

A reference to an array of AptPkg::Cache::Depends objects describing
packages which depend upon the current package.

=item ProvidesList

For virtual packages, this is a reference to an array of
AptPkg::Cache::Provides objects describing packages which provide the
current package.

=item Flags

A comma separated list if flags:  C<Auto>, C<Essential> or
C<Important>.

In a numeric context, evaluates to a combination of AptPkg::Flag::
constants.

[Note:  the only one of these you need worry about is C<Essential>,
which is set based on the package's header of the same name.  C<Auto>
seems to be used internally by B<APT>, and C<Important> seems to only
be set on the apt package.]

=item Index

Internal B<APT> unique reference for the package record.

=back

=head2 AptPkg::Cache::Version

Implements the B<APT> pkgCache::VerIterator class as a hash reference.

=head3 Keys

=over 4

=item VerStr

=item Section

=item Arch

The package version, section and architecture.

=item MultiArch

Multi-arch state: C<No>, C<All>, C<Foreign>, C<Same>, C<Allowed>,
C<AllForeign> or C<AllAllowed>.

In a numeric context, evaluates to an AptPkg::Version:: constant.

=item ParentPkg

An AptPkg::Cache::Package objct describing the package providing this
version.

=item DescriptionList

A list of AptCache::Cache::Description objects describing the files which
descrie a package version.  The list includes both Package files and
Translation files, which contain translated Description fields.

=item TranslatedDescription

An AptCache::Cache::Description object for the current locale, which will
generally be a Translation file.

=item DependsList

A reference to an array of AptPkg::Cache::Depends objects describing
packages which the current package depends upon.

=item ProvidesList

A reference to an array of AptPkg::Cache::Provides objects describing
virtual packages provided by this version.

=item FileList

A reference to an array of AptPkg::Cache::VerFile objects describing
the packages files which include the current version.

=item Size

The F<.deb> file size, in bytes.

=item InstalledSize

The disk space used when installed, in bytes.

=item Index

Internal B<APT> unique reference for the version record.

=item Priority

Package priority:  C<important>, C<required>, C<standard>, C<optional>
or C<extra>.

In a numeric context, evaluates to an AptPkg::VerPriority:: constant.

=back

=head2 AptPkg::Cache::Depends

Implements the B<APT> pkgCache::DepIterator class as a hash reference.

=head3 Keys

=over 4

=item DepType

Type of dependency:  C<Depends>, C<PreDepends>, C<Suggests>,
C<Recommends>, C<Conflicts>, C<Replaces> or C<Obsoletes>.

In a numeric context, evaluates to an AptPkg::Dep:: constant.

=item ParentPkg

=item ParentVer

AptPkg::Cache::Package and AptPkg::Cache::Version objects describing
the package declaring the dependency.

=item TargetPkg

AptPkg::Cache::Package object describing the depended package.

=item TargetVer

For versioned dependencies, TargetVer is a string giving the version
of the target package required.

=item CompType

=item CompTypeDeb

CompType gives a normalised comparison operator (>, >=, etc)
describing the relationship to TargetVer ("" if none).

CompTypeDeb returns Debian-style operators (>> rather than >).

In a numeric context, both CompType and CompTypeDeb evaluate to an
AptPkg::Dep:: constant.

Alternative dependencies (Depends: a | b) are identified by all but
the last having the AptPkg::Dep::Or bit set in the numeric
representation of CompType (and CompTypeDeb).

=item Index

Internal B<APT> unique reference for the dependency record.

=back

=head2 AptPkg::Cache::Provides

Implements the B<APT> pkgCache::PrvIterator class as a hash reference.

=head3 Keys

=over 4

=item Name

Name of virtual package.

=item OwnerPkg

=item OwnerVer

AptPkg::Cache::Package and AptPkg::Cache::Version objects describing
the providing package.

=item ProvideVersion

Version of the virtual package.  [Not currently supported by dpkg]

=item Index

Internal B<APT> unique reference for the provides record.

=back

=head2 AptPkg::Cache::VerFile

Implements the B<APT> pkgCache::VerFileIterator class as a hash
reference.

=head3 Keys

=over 4

=item File

An AptPkg::Cache::PkgFile object describing the packages file.

=item Offset

=item Size

The byte offset and length of the entry in the file.

=item Index

Internal B<APT> unique reference for the version file record.

=back

=head2 AptPkg::Cache::PkgFile

Implements the B<APT> pkgCache::PkgFileIterator class as a hash
reference.

=head3 Keys

=over 4

=item FileName

Packages file path.

=item IndexType

File type: C<Debian Package Index>, C<Debian dpkg status file>.

=item Archive

=item Component

=item Version

=item Origin

=item Label

=item Site

Fields from the Release file.

=item IsOk

True if the cache is in sync with this file.

=item Index

Internal B<APT> unique reference for the package file record.

=back

=head2 AptPkg::Cache::DescFile

Implements the B<APT> pkgCache::DescFileIterator class as a hash
reference.

=head3 Keys

=over 4

=item File

An AptPkg::Cache::PkgFile object describing the packages file.

=back

=head1 SEE ALSO

AptPkg::Config(3pm), AptPkg::System(3pm), AptPkg(3pm),
AptPkg::hash(3pm), AptPkg::PkgRecords(3pm), AptPkg::Policy(3pm).

=head1 AUTHOR

Brendan O'Dea <bod@debian.org>

=cut
