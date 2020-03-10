#!/usr/bin/perl -w

use warnings;
use strict;

use Net::DBus;
use Net::DBus::Reactor;

use Carp qw(confess cluck);

#$SIG{__WARN__} = sub { cluck $_[0] };
#$SIG{__DIE__} = sub { confess $_[0] };

my $bus = Net::DBus->session();

my $service = $bus->get_service("org.designfu.TestService");
my $object  = $service->get_object("/org/designfu/TestService/object",
				   "org.designfu.TestService");

my $sig1;
my $sig2;

my $sig1ref = \$sig1;
my $sig2ref = \$sig2;

sub hello_signal_handler1 {
    my $greeting = shift;
    print ${$sig1ref} . " Received hello signal with greeting '$greeting'\n";

}
sub hello_signal_handler2 {
    my $greeting = shift;
    print ${$sig2ref} . " Received hello signal with greeting '$greeting'\n";

    $object->disconnect_from_signal("HelloSignal", ${$sig2ref});
    ${$sig2ref} = undef;
}

$sig1 = $object->connect_to_signal("HelloSignal", \&hello_signal_handler1);
$sig2 = $object->connect_to_signal("HelloSignal", \&hello_signal_handler2);

my $reactor = Net::DBus::Reactor->main();

my $ticks = 0;
$reactor->add_timeout(5000, sub {
    $object->emitHelloSignal();
    if ($ticks++ == 10) {
      $reactor->shutdown();
    }
});

$reactor->run();
