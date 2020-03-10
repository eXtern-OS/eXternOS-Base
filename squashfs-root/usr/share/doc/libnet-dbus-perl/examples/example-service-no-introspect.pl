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

sub new {
    my $class = shift;
    my $service = shift;
    my $self = $class->SUPER::new($service, "/SomeObject");
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
    return {"first" => "Hello Dict", "second" => " from example-service.py"};
}

sub GetTuple {
    my $self = shift;
    print "Do get tuple\n";
    return ["Hello Tuple", " from example-service.py"];
}

package main;

my $bus = Net::DBus->session();
my $service = $bus->export_service("org.designfu.SampleService");
my $object = SomeObject->new($service);

Net::DBus::Reactor->main->run();
