#!/usr/bin/perl

use strict;
use warnings;

use Error qw(:try);
use Scalar::Util qw(blessed);

use IO::Handle;

package MyError;

use base 'Error';

package SecondError;

use base 'Error';

package main;

autoflush STDOUT 1;

SHLOMIF_FOREACH:
foreach my $i (1 .. 100)
{
    eval
    {
        if ($i % 10 == 0)
        {
            throw MyError;
        }
    };
    my $E = $@;
    if (blessed($E) && $E->isa('MyError'))
    {
        next SHLOMIF_FOREACH;
    }
    print "$i\n";
}

