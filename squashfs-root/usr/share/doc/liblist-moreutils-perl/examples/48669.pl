#!/usr/bin/perl 
use strict;
use warnings;
use List::MoreUtils;
print List::MoreUtils->VERSION, "\n";

for (;;) {
  eval { List::MoreUtils::any {die} 1 };
}
