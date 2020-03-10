package AptPkg::hash;

require 5.005_62;
use strict;
use warnings;
use Scalar::Util 'weaken';

our $VERSION = 1.6;

sub new
{
    my ($class, $xs) = @_;
    my $self = \my %h;
    my $priv = {};
    unless ($xs)
    {
	my $xs_prefix = '';
	(my $xs_class = $class) =~ s/(.*::)// and $xs_prefix = $1;
	$xs_class =~ s/([A-Z])/_\l$1/g;
	$xs = "$xs_prefix$xs_class"->new;
    }

    {
	no strict;
	no warnings;
	local *keys = *{"$class\::KEYS"};
	$priv->{$_}++ for @keys;
    }

    tie %h => __PACKAGE__, $self, $xs, $priv;
    bless $self, $class;
}

sub _self { (tied %{$_[0]})->[0] }
sub _xs   { (tied %{$_[0]})->[1] }
sub _priv { (tied %{$_[0]})->[2] }

sub keys
{
    my $self = shift;
    (my $iter_class = $self) =~ s/=.*/::Iter/;
    my $iter = $iter_class->new($self, @_);
    return $iter unless wantarray;

    my @keys;
    while (my $key = $iter->next) { push @keys, $key }

    @keys;
}

sub TIEHASH
{
    my $class = shift;
    my $self = [@_];
    weaken $self->[0]; # prevent reference loop
    bless $self, $class;
}

sub FETCH	{ shift->[0]->get(@_) }
sub STORE	{ shift->[0]->set(@_) }
sub EXISTS	{ shift->[0]->exists(@_) }
sub FIRSTKEY	{ ($_[0][3] = $_[0][0]->keys) ? $_[0][3]->next : undef }
sub NEXTKEY	{  $_[0][3]                   ? $_[0][3]->next : undef }

package AptPkg::hash::method;

our @ISA = qw(AptPkg::hash);

sub get
{
    my ($self, $key) = @_;
    my $keys = $self->_priv;
    return unless exists $keys->{$key};

    # try object first, then XS
    $self->_self->can($key) ? $self->_self->$key : $self->_xs->$key;
}

*exists = \&get;

package AptPkg::hash::method::iter;

sub new
{
    my ($class, $obj) = @_;
    my $keys = $obj->_priv;
    keys %$keys; # reset iterator
    bless \$obj, $class;
}

sub next
{
    my $self = shift;
    my $obj = $$self;
    my $keys = $obj->_priv;
    while (my $key = each %$keys)
    {
	return $key if $obj->exists($key);
    }

    undef;
}

1;

__END__

=head1 NAME

AptPkg::hash - a helper class for implementing tied hashes

=head1 SYNOPSIS

use AptPkg::hash;

=head1 DESCRIPTION

The AptPkg::hash class provides hash-like access for objects which
have an underlying XS implementation.

Such objects need to add AptPkg::hash to @ISA, provide get, set and
exists methods, and an iterator class.

=head2 AptPkg::hash

=over 4

=item new([I<XS_OBJECT>])

Create a object as a tied hash.  The object is implemented as a hash
reference blessed into the class, which in turn is tied to
AptPkg::hash.

This means that both $obj->method() and $obj->{key} valid, the latter
invoking get/set (through FETCH/STORE).

The tie associates an array reference with the hash, which initially
contains a reference to the hash, the XS object and an anon hash
which may be used by subclasses to store state information.

If no XS object is passed, one is created via new in the XS class.
The name of that class is constructed from the class name, by
lower-casing the last component and prefixing it with an underscore
(eg. AptPkg::Config becomes AptPkg::_config).

If the module contains a @KEYS array, then the private hash will be
populated with those entries as keys (see the description below of the
AptPkg::hash::method class).

=item _self, _xs, _priv

Accessors which may be used in subclass methods to fetch the three
array elements associated with the hash reference.

=item keys(I<ARGS>)

In a scalar context, creates and returns a new iterator object (the
class name with the suffix ::Iter appended).

The XS object, the private hash and any arguments are passed to the
constructor.

In an array context, the iterator is used to generate a list of keys
which are then returned.

The iterator class must implement a next method, which returns the
current key and advances to the next.

=back

=head2 AptPkg::hash::method

The AptPkg::hash::method class extends AptPkg::hash, providing a
simple way to map a fixed set of keys (defined by the @KEYS array)
into method calls on either the object, or the internal XS object.

Classes inheriting from AptPkg::hash::method should provide an
iterator class which inherits from AptPkg::hash::method::iter.

=head1 AUTHOR

Brendan O'Dea <bod@debian.org>

=cut
