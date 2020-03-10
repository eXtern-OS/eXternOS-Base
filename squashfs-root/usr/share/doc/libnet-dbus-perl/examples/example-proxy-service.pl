#!/usr/bin/perl

use warnings;
use strict;

use Carp qw(confess cluck);
use Net::DBus;
use Net::DBus::Service;
use Net::DBus::Reactor;

#...  continued at botom


package SomeObject;

use Class::MethodMaker [ scalar => [ qw(name email salary) ]];

sub new {
    my $class = shift;
    my $self = {};

    bless $self, $class;
    
    return $self;
}

sub HelloWorld {
    my $self = shift;
    my $message = shift;
    print "Do hello world\n";
    print $message, "\n";
    return ["Hello", " from example-service.pl"];
}

sub GetDict {
    my $self = shift;
    print "Do get dict\n";
    return {"first" => "Hello Dict", "second" => " from example-service.pl"};
}

sub GetTuple {
    my $self = shift;
    print "Do get tuple\n";
    return ["Hello Tuple", " from example-service.pl"];
}

package SomeObject::DBus;

use base qw(Net::DBus::ProxyObject);
use Net::DBus::Exporter qw(org.designfu.SampleInterface);

dbus_property("name", "string");
dbus_property("email", "string", "read");
dbus_property("salary", "int32", "write");

sub new {
    my $class = shift;
    my $service = shift;
    my $impl = shift;
    my $self = $class->SUPER::new($service, "/SomeObject", $impl);
    bless $self, $class;
    
    return $self;
}

dbus_method("HelloWorld", ["string"], [["array", "string"]], { param_names => ["message"], return_names => ["reply"] });
dbus_method("GetDict", [], [["dict", "string", "string"]]);
dbus_method("GetTuple", [], [["struct", "string", "string"]]);


package main;

my $bus = Net::DBus->session();
my $object = SomeObject->new();
my $service = $bus->export_service("org.designfu.SampleService");
my $proxy = SomeObject::DBus->new($service, $object);

$object->email('joe@example.com');

Net::DBus::Reactor->main->run();
