#!/usr/bin/perl

use warnings;
use strict;

use Net::DBus;
use Net::DBus::Dumper;
use Carp qw(confess);

$SIG{__DIE__} = sub {confess $_[0] };

my $bus = Net::DBus->find;

if (int(@ARGV) != 2) {
    die "syntax: $0 SERVICE OBJECT";
}

my $service = $bus->get_service(shift @ARGV);
my $object = $service->get_object(shift @ARGV);
my $xml = $object->_introspector->format();
print $xml, "\n";


