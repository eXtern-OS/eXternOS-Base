#
# a test client for testing IO::Socket::SSL-class's behavior

use strict;
use warnings;
use IO::Socket::SSL;
use Getopt::Long qw(:config posix_default bundling);

my ($cert_file,$key_file,$key_pass,$ca,$name,$no_verify);
GetOptions(
    'd|debug:i' => \$IO::Socket::SSL::DEBUG,
    'h|help'    => sub { usage() },
    'C|cert=s'  => \$cert_file,
    'K|key=s'   => \$key_file,
    'P|pass=s'  => \$key_pass,
    'ca=s'      => \$ca,
    'name=s'    => \$name,
    'no-verify' => \$no_verify,
) or usage("bad option");

sub usage {
    print STDERR "Error: @_\n" if @_;
    print STDERR <<USAGE;
Usage: $0 [options] ip:port
ip:port - where to connect to
Options:
  -d|--debug [level]      enable debugging with optional debug level
  -h|--help               this help
  -C|--cert  cert-file    file containing optional client certificate
  -K|--key   key-file     file containing private key to certificate, default cert-file
  -P|--pass  passphrase   passphrase for private key, default none
  --ca dir|file           use given dir/file as trusted CA store
  --name hostname         use hostname for SNI and certificate check
  --no-verify             don't verify certificate
USAGE
    exit(2);
}

my $addr = shift(@ARGV) or usage("no target address given");
@ARGV and usage("too much arguments");
$key_file ||= $cert_file;

my $cl = IO::Socket::SSL->new(
    PeerAddr => $addr,
    $ca ? ( -d $ca ? ( SSL_ca_path => $ca ):( SSL_ca_file => $ca ) ):(),
    $name ? ( SSL_hostname => $name ):(),
    $no_verify ? ( SSL_verify_mode => 0 ):(),
    $cert_file ? (
	SSL_cert_file => $cert_file,
	SSL_key_file  => $key_file,
	defined($key_pass) ? ( SSL_passwd_cb => sub { $key_pass } ):(),
    ):()
) or die "failed to connect to $addr: $!,$SSL_ERROR";

warn "new SSL connection with cipher=".$cl->get_cipher." version=".$cl->get_sslversion." certificate:\n".
    "\tsubject=".$cl->peer_certificate('subject')."\n".
    "\tissuer=".$cl->peer_certificate('issuer')."\n"
