#!/usr/bin/perl 
use strict;
use warnings;

use List::MoreUtils qw(pairwise);
my @left = (1..100);
my @right = (101..200);
pairwise { $a+ $b} @left, @right while 1;

