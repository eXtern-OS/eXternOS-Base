#!/usr/bin/env perl 

# short script to check compatability with previous Authen::SASL library

use lib 'lib';
use Authen::SASL;

my $sasl = Authen::SASL->new('CRAM-MD5', password => 'fred');

$sasl->user('gbarr');

$initial = $sasl->initial;
$mech = $sasl->name;

print "$mech;", unpack("H*",$initial),";\n";

print unpack "H*", $sasl->challenge('xyz');
print "\n";
