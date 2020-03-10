#!/usr/bin/perl

use warnings;
use strict;

use Carp qw(confess cluck);
use Net::DBus;
use Net::DBus::Service;
use Net::DBus::Reactor;

#...  continued at botom


package SomeObject;

use base qw(Net::DBus::Object);
use Net::DBus::Exporter qw(org.designfu.SampleInterface);

sub new {
    my $class = shift;
    my $service = shift;
    my $self = $class->SUPER::new($service, "/SomeObject");
    bless $self, $class;

    return $self;
}

dbus_method("HelloWorld", ["string"], [["array", "string"]]);
sub HelloWorld {
    my $self = shift;
    my $message = shift;
    print "Do hello world\n";
    print $message, "\n";
    sleep 10;
    return ["Hello", " from example-service-async.pl"];
}

dbus_method("GetDict", [], [["dict", "string", "string"]]);
sub GetDict {
    my $self = shift;
    print "Do get dict\n";
    sleep 10;
    return {"first" => "Hello Dict", "second" => " from example-service.pl"};
}

dbus_method("GetTuple", [], [["struct", "string", "string"]]);
sub GetTuple {
    my $self = shift;
    print "Do get tuple\n";
    sleep 10;
    return ["Hello Tuple", " from example-service.pl"];
}

package main;

my $bus = Net::DBus->session();
my $service = $bus->export_service("org.designfu.SampleService");
my $object = SomeObject->new($service);

Net::DBus::Reactor->main->run();
