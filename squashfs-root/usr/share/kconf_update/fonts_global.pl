#! /usr/bin/perl

use strict;

while (<>)
{
    chomp;
    s/font=Oxygen-Sans/font=Noto\ Sans/;
    s/fixed=Oxygen\ Mono/fixed=Hack/;
    s/menuFont=Oxygen-Sans/menuFont=Noto\ Sans/;
    s/smallestReadableFont=Oxygen-Sans/smallestReadableFont=Noto\ Sans/;
    s/toolBarFont=Oxygen-Sans/toolBarFont=Noto\ Sans/;
    print "$_\n";
}
