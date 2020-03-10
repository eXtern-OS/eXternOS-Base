#!/usr/bin/perl

use Net::DBus qw(:typing);


my $bus = Net::DBus->session;

my $svc = $bus->get_service("org.freedesktop.Notifications");
my $obj = $svc->get_object("/org/freedesktop/Notifications");

$obj->Notify("notification.pl",
	     0,
	     '',
	     "Demo notification",
	     "Demonstrating using of desktop\n" .
	     "notifications from Net::DBus\n",
	     ["done", "Done"],
	     {"desktop-entry" => "virt-manager", x => dbus_variant(dbus_int32(200)), y => dbus_variant(dbus_int32(200))},
	     2_000);
