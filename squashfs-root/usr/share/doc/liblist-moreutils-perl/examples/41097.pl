#!/usr/bin/perl 
use strict;
use warnings;

# use Carp;

use List::MoreUtils qw(part);
while(1) {
    my $i = 0;
    # returns [1,3,5,7], [2,4,6,8]
    my @part  = part { $i++ % 2 } 1..8;
}
