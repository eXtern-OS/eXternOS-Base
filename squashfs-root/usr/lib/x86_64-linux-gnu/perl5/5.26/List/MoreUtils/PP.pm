package List::MoreUtils::PP;

use 5.006;
use strict;
use warnings;

our $VERSION = '0.416';

=pod

=head1 NAME

List::MoreUtils::PP - Provide List::MoreUtils pure Perl implementation

=head1 SYNOPSIS

  BEGIN { $ENV{LIST_MOREUTILS_PP} = 1; }
  use List::MoreUtils qw(:all);

=cut

sub any (&@)
{
    my $f = shift;
    foreach (@_)
    {
        return 1 if $f->();
    }
    return 0;
}

sub all (&@)
{
    my $f = shift;
    foreach (@_)
    {
        return 0 unless $f->();
    }
    return 1;
}

sub none (&@)
{
    my $f = shift;
    foreach (@_)
    {
        return 0 if $f->();
    }
    return 1;
}

sub notall (&@)
{
    my $f = shift;
    foreach (@_)
    {
        return 1 unless $f->();
    }
    return 0;
}

sub one (&@)
{
    my $f     = shift;
    my $found = 0;
    foreach (@_)
    {
        $f->() and $found++ and return 0;
    }
    $found;
}

sub any_u (&@)
{
    my $f = shift;
    return if !@_;
    $f->() and return 1 foreach (@_);
    return 0;
}

sub all_u (&@)
{
    my $f = shift;
    return if !@_;
    $f->() or return 0 foreach (@_);
    return 1;
}

sub none_u (&@)
{
    my $f = shift;
    return if !@_;
    $f->() and return 0 foreach (@_);
    return 1;
}

sub notall_u (&@)
{
    my $f = shift;
    return if !@_;
    $f->() or return 1 foreach (@_);
    return 0;
}

sub one_u (&@)
{
    my $f = shift;
    return if !@_;
    my $found = 0;
    foreach (@_)
    {
        $f->() and $found++ and return 0;
    }
    $found;
}

sub true (&@)
{
    my $f     = shift;
    my $count = 0;
    $f->() and ++$count foreach (@_);
    return $count;
}

sub false (&@)
{
    my $f     = shift;
    my $count = 0;
    $f->() or ++$count foreach (@_);
    return $count;
}

sub firstidx (&@)
{
    my $f = shift;
    foreach my $i ( 0 .. $#_ )
    {
        local *_ = \$_[$i];
        return $i if $f->();
    }
    return -1;
}

sub firstval (&@)
{
    my $test = shift;
    foreach (@_)
    {
        return $_ if $test->();
    }
    return undef;
}

sub firstres (&@)
{
    my $test = shift;
    foreach (@_)
    {
        my $testval = $test->();
        $testval and return $testval;
    }
    return undef;
}

sub onlyidx (&@)
{
    my $f = shift;
    my $found;
    foreach my $i ( 0 .. $#_ )
    {
        local *_ = \$_[$i];
        $f->() or next;
        defined $found and return -1;
        $found = $i;
    }
    return defined $found ? $found : -1;
}

sub onlyval (&@)
{
    my $test   = shift;
    my $result = undef;
    my $found  = 0;
    foreach (@_)
    {
        $test->() or next;
        $result = $_;
        $found++ and return undef;
    }
    return $result;
}

sub onlyres (&@)
{
    my $test   = shift;
    my $result = undef;
    my $found  = 0;
    foreach (@_)
    {
        my $rv = $test->() or next;
        $result = $rv;
        $found++ and return undef;
    }
    return $found ? $result : undef;
}

sub lastidx (&@)
{
    my $f = shift;
    foreach my $i ( reverse 0 .. $#_ )
    {
        local *_ = \$_[$i];
        return $i if $f->();
    }
    return -1;
}

sub lastval (&@)
{
    my $test = shift;
    my $ix;
    for ( $ix = $#_; $ix >= 0; $ix-- )
    {
        local *_ = \$_[$ix];
        my $testval = $test->();

        # Simulate $_ as alias
        $_[$ix] = $_;
        return $_ if $testval;
    }
    return undef;
}

sub lastres (&@)
{
    my $test = shift;
    my $ix;
    for ( $ix = $#_; $ix >= 0; $ix-- )
    {
        local *_ = \$_[$ix];
        my $testval = $test->();

        # Simulate $_ as alias
        $_[$ix] = $_;
        return $testval if $testval;
    }
    return undef;
}

sub insert_after (&$\@)
{
    my ( $f, $val, $list ) = @_;
    my $c = &firstidx( $f, @$list );
    @$list = ( @{$list}[ 0 .. $c ], $val, @{$list}[ $c + 1 .. $#$list ], ) and return 1 if $c != -1;
    return 0;
}

sub insert_after_string ($$\@)
{
    my ( $string, $val, $list ) = @_;
    my $c = firstidx { defined $_ and $string eq $_ } @$list;
    @$list = ( @{$list}[ 0 .. $c ], $val, @{$list}[ $c + 1 .. $#$list ], ) and return 1 if $c != -1;
    return 0;
}

sub apply (&@)
{
    my $action = shift;
    &$action foreach my @values = @_;
    wantarray ? @values : $values[-1];
}

sub after (&@)
{
    my $test = shift;
    my $started;
    my $lag;
    grep $started ||= do
    {
        my $x = $lag;
        $lag = $test->();
        $x;
    }, @_;
}

sub after_incl (&@)
{
    my $test = shift;
    my $started;
    grep $started ||= $test->(), @_;
}

sub before (&@)
{
    my $test = shift;
    my $more = 1;
    grep $more &&= !$test->(), @_;
}

sub before_incl (&@)
{
    my $test = shift;
    my $more = 1;
    my $lag  = 1;
    grep $more &&= do
    {
        my $x = $lag;
        $lag = !$test->();
        $x;
    }, @_;
}

sub indexes (&@)
{
    my $test = shift;
    grep {
        local *_ = \$_[$_];
        $test->()
    } 0 .. $#_;
}

sub pairwise (&\@\@)
{
    my $op = shift;

    # Symbols for caller's input arrays
    use vars qw{ @A @B };
    local ( *A, *B ) = @_;

    # Localise $a, $b
    my ( $caller_a, $caller_b ) = do
    {
        my $pkg = caller();
        no strict 'refs';
        \*{ $pkg . '::a' }, \*{ $pkg . '::b' };
    };

    # Loop iteration limit
    my $limit = $#A > $#B ? $#A : $#B;

    # This map expression is also the return value
    local ( *$caller_a, *$caller_b );
    map {
        # Assign to $a, $b as refs to caller's array elements
        ( *$caller_a, *$caller_b ) = \( $A[$_], $B[$_] );

        # Perform the transformation
        $op->();
    } 0 .. $limit;
}

sub each_array (\@;\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@)
{
    return each_arrayref(@_);
}

sub each_arrayref
{
    my @list  = @_;    # The list of references to the arrays
    my $index = 0;     # Which one the caller will get next
    my $max   = 0;     # Number of elements in longest array

    # Get the length of the longest input array
    foreach (@list)
    {
        unless ( ref $_ eq 'ARRAY' )
        {
            require Carp;
            Carp::croak("each_arrayref: argument is not an array reference\n");
        }
        $max = @$_ if @$_ > $max;
    }

    # Return the iterator as a closure wrt the above variables.
    return sub {
        if (@_)
        {
            my $method = shift;
            unless ( $method eq 'index' )
            {
                require Carp;
                Carp::croak("each_array: unknown argument '$method' passed to iterator.");
            }

            # Return current (last fetched) index
            return undef if $index == 0 || $index > $max;
            return $index - 1;
        }

        # No more elements to return
        return if $index >= $max;
        my $i = $index++;

        # Return ith elements
        return map $_->[$i], @list;
      }
}

sub natatime ($@)
{
    my $n    = shift;
    my @list = @_;
    return sub {
        return splice @list, 0, $n;
      }
}

sub mesh (\@\@;\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@\@)
{
    my $max = -1;
    $max < $#$_ && ( $max = $#$_ ) foreach @_;
    map {
        my $ix = $_;
        map $_->[$ix], @_;
    } 0 .. $max;
}

sub uniq (@)
{
    my %seen = ();
    my $k;
    my $seen_undef;
    grep { defined $_ ? not $seen{ $k = $_ }++ : not $seen_undef++ } @_;
}

sub singleton (@)
{
    my %seen = ();
    my $k;
    my $seen_undef;
    grep { 1 == ( defined $_ ? $seen{ $k = $_ } : $seen_undef ) }
      grep { defined $_ ? not $seen{ $k = $_ }++ : not $seen_undef++ } @_;
}

sub minmax (@)
{
    return unless @_;
    my $min = my $max = $_[0];

    for ( my $i = 1; $i < @_; $i += 2 )
    {
        if ( $_[ $i - 1 ] <= $_[$i] )
        {
            $min = $_[ $i - 1 ] if $min > $_[ $i - 1 ];
            $max = $_[$i]       if $max < $_[$i];
        }
        else
        {
            $min = $_[$i]       if $min > $_[$i];
            $max = $_[ $i - 1 ] if $max < $_[ $i - 1 ];
        }
    }

    if ( @_ & 1 )
    {
        my $i = $#_;
        if ( $_[ $i - 1 ] <= $_[$i] )
        {
            $min = $_[ $i - 1 ] if $min > $_[ $i - 1 ];
            $max = $_[$i]       if $max < $_[$i];
        }
        else
        {
            $min = $_[$i]       if $min > $_[$i];
            $max = $_[ $i - 1 ] if $max < $_[ $i - 1 ];
        }
    }

    return ( $min, $max );
}

sub part (&@)
{
    my ( $code, @list ) = @_;
    my @parts;
    push @{ $parts[ $code->($_) ] }, $_ foreach @list;
    return @parts;
}

sub bsearch(&@)
{
    my $code = shift;

    my $rc;
    my $i = 0;
    my $j = @_;
    do
    {
        my $k = int( ( $i + $j ) / 2 );

        $k >= @_ and return;

        local *_ = \$_[$k];
        $rc = $code->();

        $rc == 0
          and return wantarray ? $_ : 1;

        if ( $rc < 0 )
        {
            $i = $k + 1;
        }
        else
        {
            $j = $k - 1;
        }
    } until $i > $j;

    return;
}

sub bsearchidx(&@)
{
    my $code = shift;

    my $rc;
    my $i = 0;
    my $j = @_;
    do
    {
        my $k = int( ( $i + $j ) / 2 );

        $k >= @_ and return -1;

        local *_ = \$_[$k];
        $rc = $code->();

        $rc == 0 and return $k;

        if ( $rc < 0 )
        {
            $i = $k + 1;
        }
        else
        {
            $j = $k - 1;
        }
    } until $i > $j;

    return -1;
}

sub sort_by(&@)
{
    my ( $code, @list ) = @_;
    return map { $_->[0] }
      sort     { $a->[1] cmp $b->[1] }
      map { [ $_, scalar( $code->() ) ] } @list;
}

sub nsort_by(&@)
{
    my ( $code, @list ) = @_;
    return map { $_->[0] }
      sort     { $a->[1] <=> $b->[1] }
      map { [ $_, scalar( $code->() ) ] } @list;
}

sub _XScompiled { 0 }

=head1 SEE ALSO

L<List::Util>

=head1 AUTHOR

Jens Rehsack E<lt>rehsack AT cpan.orgE<gt>

Adam Kennedy E<lt>adamk@cpan.orgE<gt>

Tassilo von Parseval E<lt>tassilo.von.parseval@rwth-aachen.deE<gt>

=head1 COPYRIGHT AND LICENSE

Some parts copyright 2011 Aaron Crane.

Copyright 2004 - 2010 by Tassilo von Parseval

Copyright 2013 - 2016 by Jens Rehsack

This library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself, either Perl version 5.8.4 or,
at your option, any later version of Perl 5 you may have available.

=cut

1;
