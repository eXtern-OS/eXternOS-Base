#!/usr/bin/perl

use strict;
use warnings;

use Error qw(:try);

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
    my $caught = 0;
    try
    {
        if ($i % 10 == 0)
        {
            throw MyError;
        }
    }
    catch MyError with
    {
        my $E = shift;
        $caught = 1;
    };
    if ($caught)
    {
        next SHLOMIF_FOREACH;
    }
    print "$i\n";
}
