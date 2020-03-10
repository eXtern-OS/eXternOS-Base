#!/usr/bin/perl 
use strict;
use warnings;

# use Carp;

use List::MoreUtils;

my @a = (10,11,12,13,14,15);
print "odd numbers: ", (List::MoreUtils::indexes {$_&1} @a), "\n";

for (;;) {
  List::MoreUtils::indexes {$_&1} @a;
}
