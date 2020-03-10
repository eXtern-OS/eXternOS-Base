#/usr/bin/perl

use warnings;
use strict;

use Net::DBus;
use Carp qw(cluck carp confess);
#$SIG{__WARN__} = sub { cluck $_[0] };
#$SIG{__DIE__} = sub { confess "[". $_[0] ."]"};

my $bus = Net::DBus->session();

my $service = $bus->get_service("org.designfu.SampleService");
my $object = $service->get_object("/SomeObject");

my $list = $object->HelloWorld("Hello from example-client.pl!");

print "[", join(", ", map { "'$_'" } @{$list}), "]\n";

my $tuple = $object->GetTuple();

print "(", join(", ", map { "'$_'" } @{$tuple}), ")\n";

my $dict = $object->GetDict();

print "{", join(", ", map { "'$_': '" . $dict->{$_} . "'"} keys %{$dict}), "}\n";

if (1) {
    $object->name("John Doe");
    $object->salary(100000);
    # Email is readonly, so we expect this to fail
    eval {
	$object->email('john.doe@example.com');
    };
    
    print $object->name, " ", $object->email, "\n";

}
