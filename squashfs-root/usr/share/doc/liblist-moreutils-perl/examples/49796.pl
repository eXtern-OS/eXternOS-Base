#!/usr/bin/perl 

use strict;
use warnings;
use List::MoreUtils;
print List::MoreUtils->VERSION, "\n";

my $obj = MyObj->new;
for (;;) {
  eval { List::MoreUtils::uniq ($obj, $obj) };
}


package MyObj;
use overload '""' => \&stringize;
sub new {
  my ($class) = @_;
  return bless {}, $class;
}
sub stringize {
  die "MyObj stringize error";
}
