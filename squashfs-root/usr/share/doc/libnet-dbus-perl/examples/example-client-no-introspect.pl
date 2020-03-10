#/usr/bin/perl

use warnings;
use strict;

use Net::DBus;
use Carp qw(cluck carp);
#$SIG{__WARN__} = sub { cluck $_[0] };
#$SIG{__DIE__} = sub { carp $_[0] };

my $bus = Net::DBus->session();

my $service = $bus->get_service("org.designfu.SampleService");
my $object = $service->get_object("/SomeObject", "org.designfu.SampleInterface");

my $list = $object->HelloWorld("Hello from example-client.pl!");

print "[", join(", ", map { "'$_'" } @{$list}), "]\n";

my $tuple = $object->GetTuple();

print "(", join(", ", map { "'$_'" } @{$tuple}), ")\n";

my $dict = $object->GetDict();

print "{", join(", ", map { "'$_': '" . $dict->{$_} . "'"} keys %{$dict}), "}\n";
