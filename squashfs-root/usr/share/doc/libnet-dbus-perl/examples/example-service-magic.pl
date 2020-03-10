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

#use Class::MethodMaker [ scalar => [ qw(name email age) ]];

#dbus_property("name", "string");
#dbus_property("email", "string", "read");
#dbus_property("age", "int32", "write");

sub new {
    my $class = shift;
    my $service = shift;
    my $self = $class->SUPER::new($service, "/SomeObject");
    bless $self, $class;
    
    return $self;
}

dbus_method("HelloWorld", ["string", "caller"], [["array", "string"]]);
sub HelloWorld {
    my $self = shift;
    my $message = shift;
    my $caller = shift;
    print "Do hello world from $caller\n";
    print $message, "\n";
    return ["Hello", " from example-service.pl"];
}

dbus_method("GetDict", ["caller"], [["dict", "string", "string"]]);
sub GetDict {
    my $self = shift;
    my $caller = shift;
    print "Do get dict from $caller\n";
    return {"first" => "Hello Dict", "second" => " from example-service.pl"};
}

dbus_method("GetTuple", ["caller"], [["struct", "string", "string"]]);
sub GetTuple {
    my $self = shift;
    my $caller = shift;
    print "Do get tuple from $caller\n";
    return ["Hello Tuple", " from example-service.pl"];
}

package main;

my $bus = Net::DBus->session();
my $service = $bus->export_service("org.designfu.SampleService");
my $object = SomeObject->new($service);

Net::DBus::Reactor->main->run();
