#! /usr/bin/perl

use strict;

while (<>)
{
    chomp;
    s/Fixed\ Font=Oxygen\ Mono/Fixed\ Font=Hack/;
    s/Sans\ Serif\ Font=Oxygen-Sans/Sans\ Serif\ Font=Noto\ Sans/;
    s/Serif\ Font=Oxygen-Sans/Serif\ Font=Noto\ Sans/;
    s/Standard Font=Oxygen-Sans/Standard\ Font=Noto\ Sans/;
    s/Fonts=Oxygen-Sans,Oxygen\ Mono,Oxygen-Sans,Oxygen-Sans/Fonts=Noto\ Sans,Hack,Noto\ Sans,Noto\ Sans/;
    print "$_\n";
}
