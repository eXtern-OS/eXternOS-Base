package Net::DNS::Resolver::os390;

#
# $Id: os390.pm 1565 2017-05-05 22:00:01Z willem $
#
our $VERSION = (qw$LastChangedRevision: 1565 $)[1];


=head1 NAME

Net::DNS::Resolver::os390 - IBM OS/390 resolver class

=cut


use strict;
use warnings;
use base qw(Net::DNS::Resolver::Base);


use Sys::Hostname;

my ($host) = split /[.]/, uc hostname();

my @resolv_conf = ( "//'$host.TCPPARMS(TCPDATA)'", "/etc/resolv.conf" );


my @config_path;
my $dotfile = '.resolv.conf';
push( @config_path, $ENV{HOME} ) if exists $ENV{HOME};
push( @config_path, '.' );

my @config_file = grep -f $_ && -o _, map "$_/$dotfile", @config_path;


sub _untaint {
	map { m/^(.*)$/; $1 } grep defined, @_;
}


sub _init {
	my $defaults = shift->_defaults;

	foreach my $conf (@resolv_conf) {
		eval {
			local *FILE;
			open( FILE, $conf ) or die;

			my @nameserver;
			my @searchlist;
			local $_;

			while (<FILE>) {
				s/[;#].*$//;			# strip comment
				s/^\s+//;			# strip leading white space
				next unless $_;			# skip empty line

				/^($host:)?(NSINTERADDR|NAMESERVER)/oi && do {
					my ( $keyword, @ip ) = grep defined, split;
					push @nameserver, @ip;
					next;
				};


				/^($host:)?(DOMAINORIGIN|DOMAIN)/oi && do {
					my ( $keyword, $domain ) = grep defined, split;
					$defaults->domain( _untaint $domain );
					next;
				};


				/^($host:)?SEARCH/oi && do {
					my ( $keyword, @domain ) = grep defined, split;
					push @searchlist, @domain;
					next;
				};

			}

			close(FILE);

			$defaults->nameservers( _untaint @nameserver );
			$defaults->searchlist( _untaint @searchlist );
		};
	}


	map $defaults->_read_config_file($_), @config_file;

	$defaults->_read_env;
}


1;
__END__


=head1 SYNOPSIS

    use Net::DNS::Resolver;

=head1 DESCRIPTION

This class implements the OS specific portions of C<Net::DNS::Resolver>.

No user serviceable parts inside, see L<Net::DNS::Resolver>
for all your resolving needs.

=head1 COPYRIGHT

Copyright (c)2017 Dick Franks.

All rights reserved.

=head1 LICENSE

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted, provided
that the above copyright notice appear in all copies and that both that
copyright notice and this permission notice appear in supporting
documentation, and that the name of the author not be used in advertising
or publicity pertaining to distribution of the software without specific
prior written permission.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

=head1 SEE ALSO

L<perl>, L<Net::DNS>, L<Net::DNS::Resolver>

=cut

