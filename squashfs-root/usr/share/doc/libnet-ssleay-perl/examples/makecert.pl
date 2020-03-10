#!/usr/bin/perl
# 19.6.1998, Sampo Kellomaki <sampo@iki.fi>
# 31.3.1999, Upgraded to OpenSSL-0.9.2b, --Sampo
# 31.7.1999, Upgraded to OpenSSL-0.9.3a, fixed depending on symlinks
#            (thanks to schinder@@pobox_.com) --Sampo
# 7.4.2001,  Upgraded to OpenSSL-0.9.6a --Sampo
# 9.11.2001, EGD patch from Mik Firestone <mik@@speed.stdio._com> --Sampo
#
# Make a self signed cert

use strict;
use warnings;
use File::Copy;
use File::Spec::Functions qw(catfile);

my $dir      = shift || usage();
my $exe_path = shift || '/usr/local/ssl/bin/openssl';
my $egd      = defined( $ENV{EGD_POOL} ) ? "-rand $ENV{EGD_POOL}" : '';

my $conf = catfile($dir, 'req.conf');
my $key  = catfile($dir, 'key.pem' );
my $cert = catfile($dir, 'cert.pem');

open (REQ, "|$exe_path req -config $conf "
      . "-x509 -days 3650 -new -keyout $key $egd >$cert")
    or die "cant open req. check your path ($!)";
print REQ <<DISTINGUISHED_NAME;
XX
Net::SSLeay
test land
Test City
Net::SSLeay Organization
Test Unit
127.0.0.1
sampo\@iki.fi
DISTINGUISHED_NAME
    ;
close REQ;
system "$exe_path verify $cert";  # Just to check

# Generate an encrypted password too
system "$exe_path rsa -in $key -des -passout pass:secret -out $key.e"; 

### Prepare examples directory as certificate directory

my $hash = `$exe_path x509 -inform pem -hash -noout <$cert`;
chomp $hash;

my $hash_file = catfile($dir, "$hash.0");
unlink $hash_file;
copy($cert, $hash_file) or die "Can't symlink $dir/$hash.0 ($!)";

sub usage {
    die "Usage: $0 DIR [PATH_TO_OPENSSL]";
}
