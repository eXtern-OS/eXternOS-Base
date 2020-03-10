#
# a test server for testing IO::Socket::SSL-class's behavior

use strict;
use warnings;
use IO::Socket::SSL;
use Getopt::Long qw(:config posix_default bundling);

my ($cert_file,$key_file,$key_pass,$ca);
GetOptions(
    'd|debug:i' => \$IO::Socket::SSL::DEBUG,
    'h|help'    => sub { usage() },
    'C|cert=s'  => \$cert_file,
    'K|key=s'   => \$key_file,
    'P|pass=s'  => \$key_pass,
    'ca=s'      => \$ca,
) or usage("bad option");

sub usage {
    print STDERR "Error: @_\n" if @_;
    print STDERR <<USAGE;
Usage: $0 [options] ip:port
ip:port - where to listen
Options:
  -d|--debug [level]      enable debugging with optional debug level
  -h|--help               this help
  -C|--cert  cert-file    file containing certificate
  -K|--key   key-file     file containing private key, default cert-file
  -P|--pass  passphrase   passphrase for private key, default none
  --ca dir|file           request a client certificate and use given dir/file as 
                          trusted CA store to verify it
USAGE
    exit(2);
}

my $addr = shift(@ARGV) or usage("no listen address given");
@ARGV and usage("too much arguments");
$cert_file or usage("no certificate given");
$key_file ||= $cert_file;

my $ioclass = IO::Socket::SSL->can_ipv6 || 'IO::Socket::INET';
my $server = $ioclass->new(
    Listen => 5,
    LocalAddr => $addr,
    Reuse => 1,
) or die "failed to create SSL server at $addr: $!";

my $ctx = IO::Socket::SSL::SSL_Context->new(
    SSL_server => 1,
    SSL_cert_file => $cert_file,
    SSL_key_file  => $key_file,
    defined($key_pass) ? ( SSL_passwd_cb => sub { $key_pass } ):(),
    $ca ? (
	SSL_verify_mode => SSL_VERIFY_PEER,
	-d $ca ? ( SSL_ca_path => $ca ):( SSL_ca_file => $ca, SSL_client_ca_file => $ca )
    ):(),
) or die "cannot create context: $SSL_ERROR";

while (1) {
    warn "waiting for next connection.\n";
    my $cl = $server->accept or do {
	warn "failed to accept: $!\n";
	next;
    };

    IO::Socket::SSL->start_SSL($cl, SSL_server => 1, SSL_reuse_ctx => $ctx) or do {
	warn "ssl handshake failed: $SSL_ERROR\n";
	next;
    };

    if ( $cl->peer_certificate ) {
	warn "new SSL connection with client certificate\n".
	    "\tsubject=".$cl->peer_certificate('subject')."\n".
	    "\tissuer=".$cl->peer_certificate('issuer')."\n"
    } else {
	warn "new SSL connection without client certificate\n"
    }

    print $cl "connected with cipher=".$cl->get_cipher." version=".$cl->get_sslversion."\n";
}
