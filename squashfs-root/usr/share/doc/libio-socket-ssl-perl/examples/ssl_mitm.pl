#!/usr/bin/perl
# simple HTTPS proxy with SSL bridging, uses Net::PcapWriter to
# to log unencrypted traffic

my $listen = '127.0.0.1:8443';      # where to listen
my $connect = 'www.google.com:443'; # where to connect

use strict;
use warnings;
use IO::Socket::SSL;
use IO::Socket::SSL::Intercept;
use IO::Socket::SSL::Utils;

my ($proxy_cert,$proxy_key) = CERT_create(
    CA => 1,
    subject => { commonName => 'foobar' }
);


my $mitm = IO::Socket::SSL::Intercept->new(
    proxy_cert => $proxy_cert,
    proxy_key  => $proxy_key,
);

my $listener = IO::Socket::INET->new(
    LocalAddr => $listen,
    Listen => 10,
    Reuse => 1,
) or die "failed to create listener: $!";

while (1) {
    # get connection from client
    my $toc = $listener->accept or next;

    # create new connection to server
    my $tos = IO::Socket::SSL->new(
	PeerAddr => $connect,
	SSL_verify_mode => 1,
	SSL_ca_path => '/etc/ssl/certs',
    ) or die "ssl connect to $connect failed: $!,$SSL_ERROR";

    # clone cert from server
    my ($cert,$key) = $mitm->clone_cert( $tos->peer_certificate );

    # and upgrade connection to client to SSL with cloned cert
    IO::Socket::SSL->start_SSL($toc,
	SSL_server => 1,
	SSL_cert => $cert,
	SSL_key => $key,
    ) or die "failed to ssl upgrade: $SSL_ERROR";

    # transfer data
    my $readmask = '';
    vec($readmask,fileno($tos),1) = 1;
    vec($readmask,fileno($toc),1) = 1;
    while (1) {
	select( my $can_read = $readmask,undef,undef,undef ) >0 or die $!;
	# try to read the maximum frame size of SSL to avoid issues
	# with pending data
	if ( vec($can_read,fileno($tos),1)) {
	    sysread($tos,my $buf,16384) or last;
	    print $toc $buf;
	}
	if ( vec($can_read,fileno($toc),1)) {
	    sysread($toc,my $buf,16384) or last;
	    print $tos $buf;
	}
    }
}
    
    
