#!/usr/bin/env perl 

# short example script

use lib 'lib';
use Authen::SASL;

# This part is in the user script

my $sasl = Authen::SASL->new(
  mechanism => 'PLAIN CRAM-MD5 EXTERNAL ANONYMOUS',
  callback => {
    user => 'gbarr',
    pass => 'fred',
    authname => 'none'
  },
);

# $sasl is then passed to a library (eg Net::LDAP)
# which will then do

my $conn = $sasl->client_new("ldap","localhost", "noplaintext noanonymous");

# The library would also set properties on the connection
#$conn->property(
#  iplocal  => $socket->sockname,
#  ipremote => $socket->peername,
#);

# It would then start things off and send this info to the server

my $initial = $conn->client_start;
my $mech    = $conn ->mechanism;

print "$mech;", unpack("H*",$initial),";\n";

# When the server want more information, the library would call

print unpack "H*", $conn->client_step("xyz");
print "\n";
