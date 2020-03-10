#!/usr/bin/perl -w

use strict;
use Net::DBus;

my $bus = Net::DBus->system;

# Get a handle to the HAL service
my $hal = $bus->get_service("org.freedesktop.Hal");

# Get the device manager
my $manager = $hal->get_object("/org/freedesktop/Hal/Manager", "org.freedesktop.Hal.Manager");

print "Warning. There may be a slight pause while this next\n";
print "method times out, if your version of HAL still just\n";
print "silently ignores unsupported method calls, rather than\n";
print "returning an error. The timeout is ~60 seconds\n";

# List devices
foreach my $dev (sort { $a cmp $b } @{$manager->GetAllDevices}) {
    print $dev, "\n";
}
