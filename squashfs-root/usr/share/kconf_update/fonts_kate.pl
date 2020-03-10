#! /usr/bin/perl

use strict;

while (<>)
{
    chomp;
    s/Font=Oxygen\ Mono/Font=Hack/;
    print "$_\n";
}
