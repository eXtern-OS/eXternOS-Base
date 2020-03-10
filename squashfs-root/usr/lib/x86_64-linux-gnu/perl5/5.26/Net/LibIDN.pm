package Net::LibIDN;

use 5.006;
use strict;
use warnings;
use Errno;
use Carp;

require Exporter;
require DynaLoader;
use AutoLoader;

our @ISA = qw(Exporter DynaLoader);

# Items to export into callers namespace by default. Note: do not export
# names by default without a very good reason. Use EXPORT_OK instead.
# Do not simply export all your public functions/methods/constants.

# This allows declaration	use Net::LibIDN ':all';
# If you do not need this, moving things directly into @EXPORT or @EXPORT_OK
# will save memory.
our %EXPORT_TAGS = ( 'all' => [ qw(
	idn_to_ascii
	idn_to_unicode
	idn_punycode_encode
	idn_punycode_decode
	idn_prep_name
	idn_prep_kerberos5
	idn_prep_node
	idn_prep_resource
	idn_prep_plain
	idn_prep_trace
	idn_prep_sasl
	idn_prep_iscsi
	tld_check
	tld_get
	tld_get_table
	IDNA_ALLOW_UNASSIGNED
	IDNA_USE_STD3_ASCII_RULES
) ] );

our @EXPORT_OK = ( @{ $EXPORT_TAGS{'all'} } );

our @EXPORT = qw(
	IDNA_ALLOW_UNASSIGNED
	IDNA_USE_STD3_ASCII_RULES
);
our $VERSION = '0.12';

# avoid prototyping error message

sub IDNA_ALLOW_UNASSIGNED
{
	return constant("IDNA_ALLOW_UNASSIGNED", length("IDNA_ALLOW_UNASSIGNED"));
}

sub IDNA_USE_STD3_ASCII_RULES
{
	return constant("IDNA_USE_STD3_ASCII_RULES", length("IDNA_USE_STD3_ASCII_RULES"));
}

sub AUTOLOAD {
    # This AUTOLOAD is used to 'autoload' constants from the constant()
    # XS function.  If a constant is not found then control is passed
    # to the AUTOLOAD in AutoLoader.

	my $constname;
	our $AUTOLOAD;
	($constname = $AUTOLOAD) =~ s/.*:://;
	croak "& not defined" if $constname eq 'constant';
	my $val = constant($constname, @_ ? $_[0] : 0);
	if ($! != 0)
	{
		if ($!{EINVAL})
		{
	    	$AutoLoader::AUTOLOAD = $AUTOLOAD;
	    	goto &AutoLoader::AUTOLOAD;
		}
		else
		{
	    	croak "Your vendor has not defined Net::LibIDN macro $constname";
		}
	}
	{
		no strict 'refs';
		# Fixed between 5.005_53 and 5.005_61
		if ($] >= 5.00561) 
		{
			*$AUTOLOAD = sub () { $val };
		}
		else
		{
			*$AUTOLOAD = sub { $val };
		}
	}
	goto &$AUTOLOAD;
}

bootstrap Net::LibIDN $VERSION;

# Preloaded methods go here.

# Autoload methods go after =cut, and are processed by the autosplit program.

1;
__END__

=encoding latin1

=head1 NAME

Net::LibIDN - Perl bindings for GNU Libidn

=head1 SYNOPSIS

  use Net::LibIDN ':all';

  idn_to_ascii("Räksmörgås.Josefßon.ORG") eq
    idn_to_ascii(idn_to_unicode("xn--rksmrgs-5wao1o.josefsson.org"));

  idn_prep_name("LibÜDN") eq "libüdn";

  idn_punycode_encode("kistenmöhre") eq
    idn_punycode_encode(idn_punycode_decode("kistenmhre-kcb"));

  my $errpos;
  tld_check("mèrle.se", $errpos) eq undef;
    $errpos == 1;

  tld_get("mainbase.mars") eq "mars";

  my $hashref = Net::LibIDN::tld_get_table("de");

  print "$hashref->{version}\n";
  foreach (@{$hashref->{valid}})
  {
    print "Unicode range from ".$_->{start}." to ".$_->{end}."\n";
  }

=head1 DESCRIPTION

Provides bindings for GNU Libidn, a C library for handling Internationalized
Domain Names according to IDNA (RFC 3490), in a way very much inspired by
Turbo Fredriksson's PHP-IDN.

=head2 Functions

=over 4

=item B<Net::LibIDN::idn_to_ascii>(I<$clear_hostname>, [I<$charset>, [I<$flags>]]);

Converts I<$clear_hostname> which might contain characters outside
the range allowed in DNS names, to IDNA ACE. If I<$charset> is
specified, treats string as being encoded in it, otherwise
assumes it is ISO-8859-1 encoded. If flag
B<IDNA_ALLOW_UNASSIGNED> is set in I<$flags>, accepts also unassigned
Unicode characters, if B<IDNA_USE_STD3_ASCII_RULES> is set, accepts
only ASCII LDH characters (letter-digit-hyphen). Flags can be
combined with ||. Returns result of conversion or B<undef> on
error.

=item B<Net::LibIDN::idn_to_unicode>(I<$idn_hostname>, [I<$charset>, [I<$flags>]]);

Converts ASCII I<$idn_hostname>, which might be IDNA ACE
encoded, into the decoded form in I<$charset> or ISO-8859-1. Flags
are interpreted as above. Returns result of conversion
or B<undef> on error.

=item B<Net::LibIDN::idn_punycode_encode>(I<$string>, [I<$charset>]);

Encodes I<$string> into "punycode" (RFC 3492). If I<$charset>
is present, treats I<$string> as being in I<$charset>, otherwise
uses ISO-8859-1. Returns result of conversion
or B<undef> on error.

=item B<Net::LibIDN::idn_punycode_decode>(I<$string>, [I<$charset>]);

Decodes I<$string> from "punycode" (RFC 3492). If I<$charset>
is present, result is converted to I<$charset>, otherwise
it is converted to ISO-8859-1. Returns result of conversion
or B<undef> on error.

=item B<Net::LibIDN::idn_prep_name>(I<$string>, [I<$charset>]);

=item B<Net::LibIDN::idn_prep_kerberos5>(I<$string>, [I<$charset>]);

=item B<Net::LibIDN::idn_prep_node>(I<$string>, [I<$charset>]);

=item B<Net::LibIDN::idn_prep_resource>(I<$string>, [I<$charset>]);

=item B<Net::LibIDN::idn_prep_plain>(I<$string>, [I<$charset>]);

=item B<Net::LibIDN::idn_prep_trace>(I<$string>, [I<$charset>]);

=item B<Net::LibIDN::idn_prep_sasl>(I<$string>, [I<$charset>]);

=item B<Net::LibIDN::idn_prep_iscsi>(I<$string>, [I<$charset>]);

Performs "stringprep" (RFC 3454) on $string according to the named
profile (e.g. *_name -> "nameprep" (RFC 3491)).
If I<$charset> is present, converts from and to this charset before and after
the operation respectively. Returns result string, or B<undef> on error.



=item B<Net::LibIDN::tdl_check>(I<$string>, I<$errpos>, [I<$charset>, [I<$tld>]]);

Checks whether or not I<$string> conforms to the restrictions on the sets
of valid characters defined by TLD authorities around the World. Treats
I<$string> as a hostname if I<$tld> is not present, determining the TLD
from the hostname. If I<$tld> is present, uses the restrictions defined
by the parties responsible for TLD I<$tld>. I<$charset> may be used to
specify the character set the I<$string> is in. Should an invalid character
be detected, returns 0 and the 0-based position of the offending character
in I<$errpos>. In case of other failure conditions, I<$errpos> is not touched,
and B<undef> is returned. Should I<$string> conform to the TLD restrictions,
1 is returned.

=item B<Net::LibIDN::tld_get>(I<$hostname>);

Returns top level domain of I<$hostname>, or B<undef> if an error
occurs or if no top level domain was found.

=item B<Net::LibIDN::tld_get_table>(I<$tld>);

Retrieves a hash reference with the TLD restriction info of given
TLD I<$tld>, or B<undef> if I<$tld> is not found. The hash ref contains the
following fields:

=over 4

=item * I<$h->>I<{name}> ... name of TLD

=item * I<$h->>I<{version}> ... version string of this restriction table

=item * I<$h->>I<{nvalid}> ... number of Unicode intervals

=item * I<$h->>I<{valid}> ...  [ {I<start> => number, I<end> => number}, ...] ... Unicode intervals

=back

=back

=head2 Limitations

There is currently no support for Perl's unicode capabilities (man perlunicode).
All input strings are assumed to be octet strings, all output strings are 
generated as octet strings. Thus, if you require Perl's unicode features, you 
will have to convert your strings manually. For example:

=over 4

use Encode;

use Data::Dumper;

print Dumper(Net::LibIDN::idn_to_unicode('xn--uro-j50a.com', 'utf-8'));

print Dumper(decode('utf-8', Net::LibIDN::idn_to_unicode('xn--uro-j50a.com', 'utf-8')));

=back

=head1 AUTHOR

Thomas Jacob, http://internet24.de

=head1 SEE ALSO

perl(1), RFC 3454, RFC 3490-3492, http://www.gnu.org/software/libidn.

=cut
