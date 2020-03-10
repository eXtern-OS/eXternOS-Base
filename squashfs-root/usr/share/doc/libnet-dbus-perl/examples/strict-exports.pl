#!/usr/bin/perl
# -*- perl -*-

use strict;
use warnings;

package MyStrictObject;

use base qw(Net::DBus::Object);
use Net::DBus::Exporter "org.example.MyObject";

sub new {
    my $class = shift;
    my $self = $class->SUPER::new(@_);

    $self->{name} = "Joe";
    $self->{salary} = 100000;

    bless $self, $class;

    return $self;
}

dbus_method("name", [], ["string"]);
sub name {
    my $self = shift;
    return $self->{name};
}

sub salary {
    my $self = shift;
    return $self->{salary};
}

package MyFlexibleObject;

use base qw(Net::DBus::Object);
use Net::DBus::Exporter qw(org.example.MyObject);

dbus_no_strict_exports;

sub new {
    my $class = shift;
    my $self = $class->SUPER::new(@_);

    $self->{name} = "Joe";
    $self->{salary} = 100000;

    bless $self, $class;

    return $self;
}

dbus_method("name", [], ["string"]);
sub name {
    my $self = shift;
    return $self->{name};
}

sub salary {
    my $self = shift;
    return $self->{salary};
}

package main;

use Net::DBus;
use Net::DBus::Reactor;

my $bus = Net::DBus->session;
my $service = $bus->export_service("org.cpan.Net.Bus.test");
my $object1 = MyStrictObject->new($service, "/org/example/MyStrictObject");
my $object2 = MyFlexibleObject->new($service, "/org/example/MyFlexibleObject");

Net::DBus::Reactor->main->run();
