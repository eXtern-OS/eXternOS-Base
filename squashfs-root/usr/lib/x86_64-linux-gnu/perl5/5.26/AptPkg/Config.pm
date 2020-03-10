package AptPkg::Config;

require 5.005_62;
use strict;
use warnings;
use AptPkg;
use AptPkg::hash;
use Carp;

require Exporter;

our @ISA = qw(Exporter AptPkg::hash);
our @EXPORT_OK = qw($_config);
our @EXPORT = ();

our $VERSION = 1.7;
our $_config = __PACKAGE__->new($AptPkg::_config::_config);

sub get
{
    my $xs = shift->_xs;
    return $xs->FindAny(@_) unless @_ and $_[0] =~ /(.+)::$/;

    # special case where name ends with ::
    my $tree = $xs->Tree($1);
    return unless $tree and $tree = $tree->Child;

    my @r;
    while ($tree)
    {
	my $v = $tree->Value;
	push @r, $v if defined $v;
	$tree = $tree->Next;
    }

    wantarray ? @r : "@r"; # what *should* this return in a scalar context?
}

sub get_file	{ shift->_xs->FindFile(@_) }
sub get_dir	{ shift->_xs->FindDir(@_) }
sub get_bool	{ shift->_xs->FindB(@_) }
sub set		{ shift->_xs->Set(@_) }
sub exists	{ shift->_xs->ExistsAny(@_) }
sub dump	{ shift->_xs->Dump(@_) }
sub read_file	{ shift->_xs->ReadConfigFile(@_) }
sub read_dir	{ shift->_xs->ReadConfigDir(@_) }

sub init
{
    AptPkg::_init_config shift->_xs;
}

sub system
{
    require AptPkg::System;
    AptPkg::_init_system shift->_xs;
}

sub parse_cmdline
{
    AptPkg::_parse_cmdline shift->_xs, @_;
}

sub AUTOLOAD
{
    (my $method = our $AUTOLOAD) =~ s/.*:://;

    return if $method eq 'DESTROY';

    my $self = shift;
    my $xs = $self->_xs;
    my $sub = $xs->can($method);

    croak "method `$method' not implemented" unless $sub;

    unshift @_, $xs;
    goto &$sub;
}

package AptPkg::Config::Iter;

sub new
{
    my $class = shift;
    my $obj = shift;
    my $self = $obj->_xs->Tree(@_);
    bless \$self, $class;
}

sub next
{
    my $self = shift;
    my $tree = $$self or return;
    my $key = $tree->FullTag;

    $$self = $tree->Child || $tree->Next;
    until ($$self)
    {
	last unless $tree = $tree->Parent;
	$$self = $tree->Next;
    }

    $key;
}

1;
