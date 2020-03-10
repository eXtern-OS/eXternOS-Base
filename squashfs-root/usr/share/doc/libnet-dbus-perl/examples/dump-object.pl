#!/usr/bin/perl

use warnings;
use strict;

use Net::DBus;
use Net::DBus::Dumper;
use Carp qw(confess);

$SIG{__DIE__} = sub {confess $_[0] };

my $bus = Net::DBus->find;

if (@ARGV) {
    my $service = $bus->get_service(shift @ARGV);
    
    if (@ARGV) {
	my $object = $service->get_object(shift @ARGV);
	print dbus_dump($object);
    } else {
	print dbus_dump($service);
    }
} else {
    print dbus_dump($bus);
}

