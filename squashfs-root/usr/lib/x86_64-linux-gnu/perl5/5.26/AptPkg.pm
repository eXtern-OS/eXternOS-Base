package AptPkg;

require 5.005_62;
use strict;
use warnings;

require DynaLoader;

our @ISA = qw(DynaLoader);
our $VERSION = 1.18;

bootstrap AptPkg $VERSION;

1;

__END__

=head1 NAME

AptPkg - interface to libapt-pkg

=head1 SYNOPSIS

use AptPkg;

=head1 DESCRIPTION

The AptPkg module provides a low-level XS interface to libapt-pkg.

Note that this interface is intended to be internal, and may change,
see the AptPkg::Config, AptPkg::System, AptPkg::Version, AptPkg::Cache,
Apt::Policy and AptPkg::Source classes for a higher level interface.

=head2 AptPkg

The AptPkg package provides the following functions:

=over 4

=item _init_config(I<CONF>)

Initialise a Configuration object (pkgInitConfig).  See the init
method in AptPkg::Config.

=item _init_system(I<CONF>)

Return a pointer to the system object (pkgInitSystem).  See the system
method in AptPkg::Config.

=item _parse_cmdline(I<CONF>, I<ARG_DEFS>, ...)

Constructs a CommandLine instance, invokes the Parse method and
returns the remaining arguments.  See the parse_cmdline method in
AptPkg::Config.

=back

=head2 AptPkg::_config

The AptPkg::_config package wraps a Perl class around the
Configuration class.  It provides an instance of the global _config
object, and exposes the following methods:

    Find, FindFile, FindDir, FindB, FindAny, Set, Exists,
    ExistsAny, Tree and Dump.

The functions ReadConfigFile and ReadConfigDir are also provided
within the package and may be used as methods.

=head2 AptPkg::_config::item

The AptPkg::_config::item package wraps a Perl class around the
Configuration::Item class.  The AptPkg::_config Tree method returns an
instance of this class.

Methods:

    Value, Tag, FullTag, Parent, Child and Next.

=head2 AptPkg::System

The AptPkg::System package wraps a Perl class around the pkgSystem
class.  It provides an instance of the global _system object, and
exposes the following methods:

    Label, VS, Lock and UnLock.

=head2 AptPkg::Version

The AptPkg::Version package wraps a Perl class around the
pkgVersioningSystem class.  It exposes the following methods:

    Label, CmpVersion, CmpReleaseVer, CheckDep and UpstreamVersion.

=head2 AptPkg::_cache

The AptPkg::_cache package wraps a Perl class around the pkgCacheFile
class.  It exposes the following methods:

    Open, Close, FindPkg, PkgBegin, FileList, Packages, Policy, MultiArchCache
    and NativeArch.

=head2 AptPkg::Cache::_package

The AptPkg::Cache::_package package wraps a Perl class around the
pkgCache::PkgIterator class.  It exposes the following methods:

    Next, Name, FullName, Arch, Section, VersionList, CurrentVer,
    RevDependsList, ProvidesList, Index, SelectedState, InstState,
    CurrentState and Flags.

=head2 AptPkg::Cache::_version

The AptPkg::Cache::_version package wraps a Perl class around the
pkgCache::VerIterator class.  It exposes the following methods:

    VerStr, Section, MultiArch, Arch, ParentPkg, DescriptionList,
    TranslatedDescription, DependsList, ProvidesList, FileList, Index
    and Priority.

=head2 AptPkg::Cache::_depends

The AptPkg::Cache::_depends package wraps a Perl class around the
pkgCache::DepIterator class.  It exposes the following methods:

    TargetVer, TargetPkg, ParentVer, ParentPkg, Index, CompType and
    DepType.

=head2 AptPkg::Cache::_provides

The AptPkg::Cache::_provides package wraps a Perl class around the
pkgCache::PrvIterator class.  It exposes the following methods:

    Name, ProvideVersion, OwnerVer, OwnerPkg and Index.

=head2 AptPkg::Cache::_description

The AptPkg::Cache::_description package wraps a Perl class around the
pkgCache::DescIterator class.  It exposes the following methods:

    LanguageCode, md5 and FileList.

=head2 AptPkg::Cache::_pkg_file

The AptPkg::Cache::_pkg_file package wraps a Perl class around the
pkgCache::PkgFileIterator class.  It exposes the following methods:

    FileName, Archive, Component, Version, Origin, Label, Site,
    IndexType and Index.

=head2 AptPkg::Cache::_ver_file

The AptPkg::Cache::_ver_file package wraps a Perl class around the
pkgCache::VerFileIterator class.  It exposes the following methods:

    File, Index, Offset and Size.

=head2 AptPkg::Cache::_desc_file

The AptPkg::Cache::_desc_file package wraps a Perl class around the
pkgCache::DescFileIterator class.  It exposes the following methods:

    File

=head2 AptPkg::Cache::_pkg_records

The AptPkg::Cache::_pkg_records package wraps a Perl class around the
pkgRecords class.  It exposes the following methods:

    Lookup.

=head2 AptPkg::_policy

The AptPkg::_policy package wraps a Perl class around the pkgPolicy
class.  It exposes the following methods:

    GetPriority, GetMatch and GetCandidateVer.

=head2 AptPkg::_source_list

The AptPkg::_source_list package wraps a Perl class around
the pkgSourceList class.  Required as an argument to the
AptPkg::_src_records constructor.

=head2 AptPkg::_src_records

The AptPkg::_src_records package wraps a Perl class around
the pkgSrcRecords class.  It exposes the following methods:

    Restart, Find.

=head2 Constants

The following B<APT> enumerations are included, used by attributes of
AptPkg::Cache.

=head3 pkgCache::Version::VerMultiArch

C<AptPkg::Version::No>,
C<AptPkg::Version::All>,
C<AptPkg::Version::Foreign>,
C<AptPkg::Version::Same>,
C<AptPkg::Version::Allowed>,
C<AptPkg::Version::AllForeign> and
C<AptPkg::Version::AllAllowed>.

=head3 pkgCache::Dep::DepType

C<AptPkg::Dep::Depends>,
C<AptPkg::Dep::PreDepends>,
C<AptPkg::Dep::Suggests>,
C<AptPkg::Dep::Recommends>,
C<AptPkg::Dep::Conflicts>,
C<AptPkg::Dep::Replaces>,
C<AptPkg::Dep::Obsoletes>
C<AptPkg::Dep::DpkgBreaks> and
C<AptPkg::Dep::Enhances>.

=head3 pkgCache::Dep::DepCompareOp

C<AptPkg::Dep::Or>,
C<AptPkg::Dep::NoOp>,
C<AptPkg::Dep::LessEq>,
C<AptPkg::Dep::GreaterEq>,
C<AptPkg::Dep::Less>,
C<AptPkg::Dep::Greater>,
C<AptPkg::Dep::Equals> and
C<AptPkg::Dep::NotEquals>.

=head3 pkgCache::State::VerPriority

C<AptPkg::State::Important>,
C<AptPkg::State::Required>,
C<AptPkg::State::Standard>,
C<AptPkg::State::Optional> and
C<AptPkg::State::Extra>.

=head3 pkgCache::State::PkgSelectedState

C<AptPkg::State::Unknown>,
C<AptPkg::State::Install>,
C<AptPkg::State::Hold>,
C<AptPkg::State::DeInstall> and
C<AptPkg::State::Purge>.

=head3 pkgCache::State::PkgInstState

C<AptPkg::State::Ok>,
C<AptPkg::State::ReInstReq>,
C<AptPkg::State::HoldInst> and
C<AptPkg::State::HoldReInstReq>.

=head3 pkgCache::State::PkgCurrentState

C<AptPkg::State::NotInstalled>,
C<AptPkg::State::UnPacked>,
C<AptPkg::State::HalfConfigured>,
C<AptPkg::State::HalfInstalled>,
C<AptPkg::State::ConfigFiles>,
C<AptPkg::State::Installed>,
C<AptPkg::State::TriggersAwaited> and
C<AptPkg::State::TriggersPending>.

=head3 pkgCache::Flag::PkgFlags

C<AptPkg::Flag::Auto>,
C<AptPkg::Flag::Essential> and
C<AptPkg::Flag::Important>.

=head1 SEE ALSO

AptPkg::Config(3pm), AptPkg::System(3pm), AptPkg::Version(3pm),
AptPkg::Cache(3pm), AptPkg::Source(3pm).

=head1 AUTHOR

Brendan O'Dea <bod@debian.org>

=cut
