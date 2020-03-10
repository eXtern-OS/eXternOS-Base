#
#
#
# TODO:
#	should we look at signals etc. for enums/flags?
#	we're getting warnings about unregistered types with new enums/flags 
#	stuff, quell them.
#

package Glib::GenPod;

our $VERSION = '1.326';

use strict;
use warnings;
use Carp;
use File::Spec;
use Data::Dumper;
use POSIX qw(strftime);

use Glib;

use base 'Exporter';

our @EXPORT = qw(
	add_types
	xsdoc2pod
	podify_properties
	podify_child_properties
	podify_style_properties
	podify_values
	podify_signals
	podify_ancestors
	podify_interfaces
	podify_methods
	podify_enums_and_flags
	podify_deprecated_by
);

our $COPYRIGHT = undef;
our $AUTHORS = 'Gtk2-Perl Team';
our $MAIN_MOD = undef;
our $YEAR = strftime "%Y", gmtime($ENV{SOURCE_DATE_EPOCH} || time);

our ($xspods, $data);
	
=head1 NAME

Glib::GenPod - POD generation utilities for Glib-based modules

=head1 SYNOPSIS

 use Glib::GenPod;

 # use the defaults:
 xsdoc2pod ($xsdocparse_output_file, $destination_dir);

 # or take matters into your own hands
 require $xsdocparse_output_file;
 foreach my $package (sort keys %$data) {
     print "=head1 NAME\n\n$package\n\n";
     print "=head1 METHODS\n\n" . podify_methods ($package) . "\n\n";
 }

=head1 DESCRIPTION 

This module includes several utilities for creating pod for xs-based Perl
modules which build on the Glib module's foundations.  The most important bits
are the logic to convert the data structures created by xsdocparse.pl to
describe xsubs and pods into method docs, with call signatures and argument
descriptions, and converting C type names into Perl type names.  The rest of
the module is mostly boiler-plate code to format and pretty-print information
that may be queried from the Glib type system.

To make life easy for module maintainers, we also include a do-it-all function,
xsdoc2pod(), which does pretty much everything for you.  All of the pieces it
uses are publically usable, so you can do whatever you like if you don't like
the default output.

=head1 DOCUMENTING THE XS FILES

All of the information used as input to the methods included here comes from
the XS files of your project, and is extracted by Glib::ParseXSDoc's
C<xsdocparse>.  This function creates an file containing Perl code that may be
eval'd or require'd to recreate the parsed data structures, which are a list of
pods from the verbatim C portion of the XS file (the xs api docs), and a hash
of the remaining data, keyed by package name, and including the pods and xsubs
read from the rest of each XS file following the first MODULE line.

Several custom POD directives are recognized in the XSubs section.  Note that
each one is sought as a paragraph starter, and must follow a C<=cut> directive.

=over

=item =for object Package::Name

All xsubs and pod from here until the next object directive or MODULE line
will be placed under the key 'I<Package::Name>' in xsdocparse's data
structure.  Everything from this line to the next C<=cut> is included as a
description POD.

=item =for object Package::Name (Other::Package::Name)

Generate POD in I<Package::Name> but for the package I<Other::Package::Name>.
This is useful if you want POD to appear in a different namespace but still
want the automatically generated hierarchy, signal and property listing,
etc. from the original namespace.  For example:

  =for object Gnome2::PanelApplet::main (Gnome2::PanelApplet)
  =cut

This will create Gnome2/PanelApplet/main.pod containing the automatically
generated documentation for Gnome2::PanelApplet (hierarchy, signals, etc.) plus
the method listing from the current XS file.

=item =for enum Package::Name

=item =for flags Package::Name

This causes xsdoc2pod to call C<podify_values> on I<Package::Name> when
writing the pod for the current package (as set by an object directive or
MODULE line).  Any text in this paragraph, to the next C<=cut>, is included
in that section.

=item =for deprecated_by Package::Name

Used to add a deprecation warning, indicating I<Package::Name> as an
alternative way to achieve the same functionality.  There may be any number
these in each package.

=item =for see_also L<some_thing_to_see>

Used to add extra see alsos onto the end of the parents, if any, for a given
object.  Anything following the space behind see_also up to the end of the
line will be placed onto the list of "see also"s.  There may be any number of
these in each package.

=item =for apidoc

=item =for apidoc Full::Symbol::name

Paragraphs of this type document xsubs, and are associated with the xsubs
by xsdocparse.pl.  If the full symbol name is not included, the paragraph
must be attached to the xsub declaration (no blank lines between C<=cut> and
the xsub).

Within the apidoc PODs, we recognize a few special directives (the "for\s+"
is optional on these):

=over

=item =for signature ...

Override the generated call signature with the ... text.  If you include
multiple signature directives, they will all be used.  This is handy when
you want to change the return type or list different ways to invoke an
overloaded method, like this:

 =for apidoc

 =signature bool Class->foo

 =signature ($thing, @other) = $object->foo ($it, $something)

 Text in here is included in the generated documentation.
 You can actually include signature and arg directives
 at any point in this pod -- they are stripped after.
 In fact, any pod is valid in here, until the =cut.

 =cut
 void foo (...)
     PPCODE:
        /* crazy code follows */

=item =for arg name (type) description

=item =for arg name description

The arg directive adds or overrides an argument description.  The
description text is optional, as is the type specification (the part
in parentheses).  If you want to hide an argument, specify C<__hide__>
as its type.  The arg name does I<not> need to include a sigil,
as dollar signs will be added.  FIXME what about @ for lists?

=back

Also, we honor a couple of "modifiers" on the =for apidoc line, following the
symbol name, if present:

=over

=item - __hide__

Do not document this xsub.  This is handy in certain situations, e.g., for
private functions.  DESTROY always has this turned on, for example.

=item - __gerror__

This function or method can generate a Glib::Error exception.

=item - __function__

Generate a function-style signature for this xsub.  The default is to
generate method-style signatures.

=item - __deprecated__

This function or method is deprecated and should not be used in newly written
code.

=back

(These are actually handled by Glib::ParseXSDoc, but we list them here
because, well, they're an important part of how you document the XS files.)

=back

=head1 FUNCTIONS

=over

=cut

=item xsdoc2pod ($datafile, $outdir='blib/lib', index=undef)

Given a I<$datafile> containing the output of xsdocparse.pl, create in 
I<$outdir> a pod file for each package, containing everything we can think
of for that module.  Output is controlled by the C<=for object> directives
and such in the source code.

If you don't want each package to create a separate pod file, then use
this function's code as a starting point for your own pretty-printer.

=cut

sub xsdoc2pod
{
	my $datafile = shift();
	my $outdir   = shift() || 'blib/lib';
	my $index    = shift;

	mkdir $outdir unless (-d $outdir);

	die "usage: $0 datafile [outdir]\n"
		unless defined $datafile;

	require "./$datafile";

	my @files = ();

	my $pkgdata;
	my $ret;

	foreach my $package (sort { ($a->isa('Glib::Object') ? -1 : 1) } 
				keys %$data)
	{
		$pkgdata = $data->{$package};

		my $pod = File::Spec->catfile ($outdir, split /::/, $package)
		        . '.pod';
		my (undef, @dirs, undef) = File::Spec->splitpath ($pod);
		mkdir_p (File::Spec->catdir (@dirs));

		open POD, ">$pod" or die "can't open $pod for writing: $!\n";
		select POD;

		$package = $pkgdata->{object} if (exists $pkgdata->{object});

		preprocess_pod ($_) foreach (@{$pkgdata->{pods}});

		push @files, {
			name => $package,
			file => $pod,
			blurb => $pkgdata->{blurb},
		};

		# podify_pods() always returns proper POD with a =cut at the
		# end.  But all the other =head1 below need a closing =cut.

		print "=head1 NAME\n\n$package";
		if (exists ($pkgdata->{blurb})) {
			print ' - '.$pkgdata->{blurb};
		} else {
			my $cname = convert_to_cname ($package);
			if (defined $cname) {
				print " - wrapper for $cname";
			}
		}
		print "\n\n=cut\n\n";

		#                   pods            , position 
		$ret = podify_pods ($pkgdata->{pods}, 'SYNOPSIS');
		print "$ret\n\n" if ($ret);
		
		$ret = podify_pods ($pkgdata->{pods}, 'DESCRIPTION');
		print "$ret\n\n" if ($ret);
		
		my $parents;
		($ret, $parents) = podify_ancestors ($package);
		print "=head1 HIERARCHY\n\n$ret\n\n=cut\n\n" if ($ret);
		
		$ret = podify_pods ($pkgdata->{pods}, 'post_hierarchy');
		print "$ret\n\n" if ($ret);
		
		$ret = podify_interfaces ($package);
		print "=head1 INTERFACES\n\n$ret\n\n=cut\n\n" if ($ret);
		
		$ret = podify_pods ($pkgdata->{pods}, 'post_interfaces');
		print "$ret\n\n" if ($ret);

		$ret = podify_pods ($pkgdata->{pods});
		print "$ret\n\n" if ($ret);

		$ret = podify_deprecated_by ($package, @{ $pkgdata->{deprecated_bys} });
		print "\n=head1 DEPRECATION WARNING\n\n$ret\n\n=cut\n\n" if ($ret);

		$ret = podify_methods ($package, $pkgdata->{xsubs});
		print "\n=head1 METHODS\n\n$ret\n\n=cut\n\n" if ($ret);
		
		$ret = podify_pods ($pkgdata->{pods}, 'post_methods');
		print "$ret\n\n" if ($ret);

		$ret = podify_properties ($package);	
		print "\n=head1 PROPERTIES\n\n$ret\n\n=cut\n\n" if ($ret);

		$ret = podify_child_properties ($package);
		print "\n=head1 CHILD PROPERTIES\n\n$ret\n\n=cut\n\n" if ($ret);

		$ret = podify_style_properties ($package);
		print "\n=head1 STYLE PROPERTIES\n\n$ret\n\n=cut\n\n" if ($ret);

		$ret = podify_pods ($pkgdata->{pods}, 'post_properties');
		print "$ret\n\n" if ($ret);

		$ret = podify_signals ($package);	
		print "\n=head1 SIGNALS\n\n$ret\n\n=cut\n\n" if ($ret);

		$ret = podify_pods ($pkgdata->{pods}, 'post_signals');
		print "$ret\n\n" if ($ret);

		$ret = podify_enums_and_flags ($pkgdata, $package);	
		print "\n=head1 ENUMS AND FLAGS\n\n$ret\n\n=cut\n\n" if ($ret);

		$ret = podify_pods ($pkgdata->{pods}, 'post_enums');
		print "$ret\n\n" if ($ret);

		$ret = podify_pods ($pkgdata->{pods}, 'SEE_ALSO');
		if ($ret)
		{
			print "$ret\n\n";
		}
		else
		{
			# don't link to yourself
			pop @$parents;
			# link to the toplevel, if we can.
			unshift @$parents, $MAIN_MOD if $MAIN_MOD;

			$ret = podify_see_alsos (@$parents,
			                         $pkgdata->{see_alsos}
						 ? @{ $pkgdata->{see_alsos} }
			                         : ());
			print "\n=head1 SEE ALSO\n\n$ret\n\n=cut\n\n" if ($ret);
		}

		$ret = podify_pods ($pkgdata->{pods}, 'COPYRIGHT');
		if ($ret)
		{
			# copyright over-ridden
			print "$ret\n\n" 
		}
		else
		{
			# use normal copyright system
			$ret = get_copyright ();
			print "\n=head1 COPYRIGHT\n\n$ret\n\n=cut\n\n" if ($ret);
		}

		close POD;
	}

	if ($index) {
		open INDEX, ">$index"
			or die "can't open $index for writing: $!\b";
		select INDEX;

		foreach (sort {$a->{name} cmp $b->{name}} @files) {
			print join("\t", $_->{file},
				   $_->{name},
				   $_->{blurb} ? $_->{blurb} : () ) . "\n";
		}
		
		close INDEX;
	}
}

# more sensible names for the basic types
our %basic_types = (
	# the perl wrappers for the GLib fundamentals
	'Glib::Scalar'  => 'scalar',
	'Glib::String'  => 'string',
	'Glib::Int'     => 'integer',
	'Glib::Uint'    => 'unsigned',
	'Glib::Double'  => 'double',
	'Glib::Float'   => 'float',
	'Glib::Boolean' => 'boolean',

	# sometimes we can get names that are already mapped...
	# e.g., from =for arg lines.  pass them unbothered.
	scalar     => 'scalar',
	subroutine => 'subroutine',
	integer    => 'integer',
	string     => 'string',
	package    => 'package',
	list       => 'list',

	# other C names which may sneak through
	bool     => 'boolean', # C++ keyword, but provided by the perl api
	boolean  => 'boolean',
	int      => 'integer',
	uint     => 'unsigned',
	float    => 'double',
	double   => 'double',
	char     => 'string',
	unsigned => 'unsigned',

	gboolean => 'boolean',
	gint     => 'integer',
	gint8    => 'integer',
	gint16   => 'integer',
	gint32   => 'integer',
	guint8   => 'unsigned',
	guint16  => 'unsigned',
	guint32  => 'unsigned',
	glong    => 'integer',
	gulong   => 'unsigned',
	gshort   => 'integer',
	guint    => 'integer',
	gushort  => 'unsigned',
	gint64   => '64 bit integer',
	guint64  => '64 bit unsigned',
	gfloat   => 'double',
	gdouble  => 'double',
	gsize    => 'unsigned',
	gssize   => 'integer',
	goffset  => '64 bit integer',
	gchar    => 'string',

	SV       => 'scalar',
	UV       => 'unsigned',
	IV       => 'integer',
	CV       => 'subroutine',
	AV       => 'arrayref',

	gchar_length => 'string',
	gchar_utf8_length => 'string',

	char_byte => 'byte string',

	FILE => 'file handle',
	time_t => 'unix timestamp',

	GPerlFilename	=> 'localized file name',
	GPerlFilename_const	=> 'localized file name',
);

unless (Glib->CHECK_VERSION (2, 4, 0)) {
	$basic_types{'Glib::Strv'} = 'ref to array of strings';
}

=item add_types (@filenames)

Parse the given I<@filenames> for entries to add to the C<%basic_types> used
for C type name to Perl package name mappings of types that are not registered
with the Glib type system.  The file format is dead simple: blank lines are
ignored; /#.*$/ is stripped from each line as comments; the first token on
each line is considered to be a C type name, and the remaining tokens are the
description of that type.  For example, a valid file may look like this:

  # a couple of special types
  FooBar      Foo::Bar
  Frob        localized frobnicator

C type decorations such as "const" and "*" are implied (do not include them),
and the _ornull variant is handled for you.

=cut

sub add_types {
	my @files = @_;
	foreach my $f (@files) {
		open IN, $f or die "can't open types file $f: $!\n";
		my $n = 0;
		while (<IN>) {
			chomp;
			s/#.*//;
			next if m/^\s*$/;
			my ($c_name, @bits) = split;
			if (@bits) {
				$basic_types{$c_name} = join ' ', @bits;
				$n++;
			} else {
				warn "$f:$.: no description for $c_name\n"
			}
		}
		print "Loaded $n extra types from $f\n";
		close IN;
	}
}


=item $string = podify_properties ($packagename)

Pretty-print the object properties owned by the Glib::Object derivative
I<$packagename> and return the text as a string.  Returns undef if there
are no properties or I<$package> is not a Glib::Object.

=cut

sub podify_properties {
	my $package = shift;
	my @properties;
	eval { @properties = Glib::Object::list_properties($package); 1; }
	  || return undef;
	return _podify_pspecs($package, @properties);
}

sub _podify_pspecs {
	my ($package, @properties) = @_;
	return undef unless (@properties);

	# we have a non-zero number of properties, but there may still be
	# none for this particular class.  keep a count of how many
	# match this class, so we can return undef if there were none.
	my $nmatch = 0;
	my $str = "=over\n\n";
	foreach my $p (sort { $a->{name} cmp $b->{name} } @properties) {
		next unless $p->{owner_type} eq $package;
		++$nmatch;
		my $stat = join " / ",  @{ $p->{flags} };
		my $type = exists $basic_types{$p->{type}}
		      ? $basic_types{$p->{type}}
		      : $p->{type};
		my $default = _pspec_formatted_default($p);
		$str .= "=item '$p->{name}' ($type : default $default : $stat)\n\n";
		$str .= "$p->{descr}\n\n" if (exists ($p->{descr}));
	}
	$str .= "=back\n\n";

	return $nmatch ? $str : undef;
}

# return a POD string which is the default value of $pspec, nicely formatted
sub _pspec_formatted_default {
  my ($pspec) = @_;
  my $default = $pspec->get_default_value;
  if (! defined $default) {
    return 'undef';
  }
  my $pname = $pspec->get_name;
  my $type = $pspec->get_value_type;

  # Crib: "eq" here because Glib::Boolean->isa('Glib::Boolean') is false,
  # it's not an actual perl module
  if ($type eq 'Glib::Boolean') {
    $default = ($default ? 'true' : 'false');

  } elsif ($type->isa('Glib::Flags')) {
    $default = join ",", @$default;

  } elsif ($pspec->isa('Glib::Param::Unichar')) {
    # $default is a single-char string, show as ordinal and string.
    # $type is only Glib::UInt, so this must be before plain UInts below.
    # Eg. Gtk2::Entry property "invisible-char".
    $default = ord($default) . ' ' . Data::Dumper->new([$default])
      ->Useqq(1)->Terse(1)->Indent(0)->Dump;

  } elsif ($type eq 'Glib::Double' && $default == POSIX::DBL_MAX()) {
    # Show DBL_MAX symbolically.
    # Eg. Gtk2::Range property "fill-level" is DBL_MAX.
    $default = "DBL_MAX";
  } elsif ($type eq 'Glib::Double' && $default == - POSIX::DBL_MAX()) {
    $default = "-DBL_MAX";
  } elsif ($type eq 'Glib::Float' && $default == POSIX::FLT_MAX()) {
    $default = "FLT_MAX";
  } elsif ($type eq 'Glib::Float' && $default == - POSIX::FLT_MAX()) {
    $default = "-FLT_MAX";

  } elsif ($type eq 'Glib::Double' || $type eq 'Glib::Float') {
    # Limit the decimals shown in floats,
    # eg. Gtk2::Menu style property "arrow-scaling" is 0.7 and comes out as
    # 0.6999999999 if not restricted a bit
    $default = sprintf '%.6g', $default;

  } elsif ($pname =~ /keyval/
	   && $type eq 'Glib::UInt'
	   && eval { require Gtk2; 1 }) {
    # Keyvals in hex the same as gdkkeysyms.h, and show the symbol if known.
    # The pspec type of keyvals is only UInt, must guess from the property
    # name whether a uint is in fact a keyval.
    # eg. Gtk2::Label property "mnemonic-keyval" is 0xFFFFFF=VoidSymbol
    my $keyname = Gtk2::Gdk->keyval_name ($default);
    $default = sprintf '0x%02X', $default;  # two or more hex digits
    if (defined $keyname) {
      $default = "$default $keyname";
    }

  } elsif ($type eq 'Glib::Int' && $default == POSIX::INT_MAX()) {
    # Show INT_MAX symbolically
    # eg. Gtk2::Paned property "max-position" is INT_MAX
    $default = "INT_MAX";
  } elsif ($type eq 'Glib::Int' && $default == POSIX::INT_MIN()) {
    $default = "INT_MIN";
  } elsif ($type eq 'Glib::UInt' && $default == POSIX::UINT_MAX()) {
    $default = "UINT_MAX";

  } else {
    # Strings quoted for clarity, unprintables shown backslashed
    # eg. Gtk2::UIManager property "ui" has newlines
    # eg. Gtk2::TreeView style property "tree-line-pattern" is bytes "\001\001"
    $default = Data::Dumper->new([$default])
      ->Useqq(1)->Terse(1)->Indent(0)->Dump;
  }

  # Escape "<" to E<lt> etc.
  # eg. Gtk2::UIManager property "ui" is "<ui></ui>"
  $default = _pod_escape($default);

  return $default;
}

# Return $str with characters escaped ready to appear in pod.  This means
# non-ascii escaped to E<123> and "<" to E<lt>.  Strictly speaking "<" only
# has to be escaped if it would be B<... etc, but it's easier to do it
# always and might help some of the pod formatters.  $str is assumed to have
# no non-printables (control chars etc).
# (ENHANCE-ME: Is there a module to do char->pod like this?  Pod::Escapes is
# the converse pod->char ...)
sub _pod_escape {
  my ($str) = @_;
  $str =~ s{([^[:ascii:]])|(<)}
	   {defined $1 ? ('E<'.ord($1).'>') : 'E<lt>'}eg;
  return $str;
}

=item $string = podify_child_properties ($packagename)

Pretty-print the child properties owned by the Gtk2::Container derivative
I<$packagename> and return the text as a string.  Returns undef if there are
no child properties or I<$package> is not a Gtk2::Container or similar class
with a C<list_child_properties()> method.

=cut

sub podify_child_properties {
	my ($package) = shift;
	# Call list_child_properties() as a method so as to perhaps work on
	# Goo::Canvas::Item which has a similar child properties scheme of
	# its own (it's not a Gtk2::Container subclass), though that method
	# is not wrapped as of Goo::Canvas 0.06.
	if ($package->can('list_child_properties')) {
	  return _podify_pspecs($package, $package->list_child_properties);
	} else {
	  return undef;
	}
}

=item $string = podify_style_properties ($packagename)

Pretty-print the style properties owned by the Gtk2::Widget derivative
I<$packagename> and return the text as a string.  Returns undef if there are
no style properties or I<$package> is not a Gtk2::Widget or similar class
with a C<list_style_properties()> method.

=cut

sub podify_style_properties {
	my ($package) = shift;
	my @properties;
	if ($package->can('list_style_properties')) {
	  return _podify_pspecs($package, $package->list_style_properties);
	} else {
	  return undef;
	}
}

=item $string = podify_values ($packagename)

List and pretty-print the values of the GEnum or GFlags type I<$packagename>,
and return the text as a string.  Returns undef if I<$packagename> isn't an
enum or flags type.

=cut

sub podify_values {
	my $package = shift;
	my @values;
	eval { @values = Glib::Type->list_values ($package); 1; };
	return undef unless (@values or not $@);

	return "=over\n\n"
	     . join ("\n\n", map { "=item * '$_->{nick}' / '$_->{name}'" } @values)
	     . "\n\n=back\n\n";
}

=item $string = podify_signals ($packagename)

Query, list, and pretty-print the signals associated with I<$packagename>.
Returns the text as a string, or undef if there are no signals or
I<$packagename> is not a Glib::Object derivative.

=cut

sub podify_signals {
    my $str = undef;
    eval {
	my @sigs = Glib::Type->list_signals (shift);
	return undef unless @sigs;
	$str = "=over\n\n";
	foreach (sort {$a->{signal_name} cmp $b->{signal_name} } @sigs) {
		$str .= '=item ';
		$str .= convert_type ($_->{return_type}).' = '
			if exists $_->{return_type};
		$str .= "B<$_->{signal_name}> (";
		$str .= join ', ', map { convert_type ($_) }
				$_->{itype}, @{$_->{param_types}};
		$str .= ")\n\n";
	}
	$str .= "=back\n\n";
    };
    return $str
}

=item $string = podify_deprecated_by ($packagename, @deprecated_by)

Creates a deprecation warning for $packagename, suggesting using the items
inside @deprecated_by instead.

=cut

sub podify_deprecated_by
{
	my $package       = shift;
	my @deprecated_by = @_;

	return undef unless scalar @deprecated_by;

	my $str = "$package has been marked as deprecated, and should not be "
	        . "used in newly written code.\n\n";

	# create the deprecated for list
	$str .= "You should use "
	      . join (', ',
	              map {
			if (/^\s*L</) {
				$_;
			}
			else {
				"L<$_>";
			}
		      } @deprecated_by)
	      . " instead of $package.\n";

	return $str;
}

sub podify_enums_and_flags
{
	my $pkgdata = shift;
	my $package = shift;
	
	my %types = ();
	
	my $name;
	my $pod;
	my %info = ();
	foreach (@{$pkgdata->{enums}})
	{
		$name = convert_type ($_->{name});
			
		$pod = $_->{pod};
		shift @{ $pod->{lines} };
		pop @{ $pod->{lines} } if $pod->{lines}[-1] =~ /^=cut/;

		$info{$name} = {
			type => $_->{type},
			pod  => $pod->{lines},
		};
		$types{$name}++;
	}

	foreach my $xsub (@{$pkgdata->{xsubs}})
	{
		if ($xsub->{return_type})
		{
			foreach my $ret (@{$xsub->{return_type}})
			{
				$name = convert_type ($ret);
				$types{$name}++;
			}
		}
		if ($xsub->{args})
		{
			foreach my $arg (@{$xsub->{args}})
			{
				if ($arg->{type})
				{
					$name = convert_type ($arg->{type});
					$types{$name}++;
				}
			}
		}
	}

	if ($package)
	{
		my @props;
		eval { @props = Glib::Object::list_properties($package); 1; };
		foreach my $prop (@props)
		{
			next unless ($prop->{type});
			next unless $prop->{owner_type} eq $package;
			$name = convert_type ($prop->{type});
			$types{$name}++;
		}
		
		my @sigs;
		eval { @sigs = Glib::Type->list_signals ($package); 1; };
		foreach my $sig (@sigs)
		{
			if ($sig->{return_type})
			{
				$name = convert_type ($sig->{return_type});
				$types{$name}++;
			}
			foreach (@{$sig->{param_types}})
			{
				next unless ($_);
				$name = convert_type ($_);
				$types{$name}++;
			}
		}
	}

	my $ret = '';
	foreach (sort keys %types)
	{
		s/\s.*//;

		next if $_ eq 'Glib::Enum' || $_ eq 'Glib::Flags';

		my $values_pod = podify_values ($_);

		if ($values_pod || exists $info{$_})
		{
			my $type = UNIVERSAL::isa ($_, 'Glib::Flags') ?
					'flags' : 'enum';
			$ret .= "=head2 $type $_\n\n";
			$ret .= join ("\n", @{$info{$_}{pod}}) . "\n\n"
				if ($info{$_}{pod});
			$ret .= podify_values ($_) . "\n";
		}
	}
	
	return $ret;
}


=item $string = podify_pods ($pods, $position)

Helper function to allow specific placement of generic pod within the auto
generated pages. Pod sections starting out with =for position XXX, where XXX
is one of the following will be placed at a specified position. In the case of
pod that is to be placed after a particular section that doesn't exist, that
pod will be still be placed there.

This function is called at all of the specified points through out the process
of generating pod for a page. Any pod matching the I<position> passed will be
returned, undef if no matches were found.  If I<position> is undef all pods
without specific position information will be returned. I<pods> is a reference
to an array of pod hashes.

=over

=item * SYNOPSIS

After the NAME section

=item * DESCRIPTION

After the SYNOPSIS section.

=item * post_hierarchy

After the HIERARCHY section.

=item * post_interfaces

After the INTERFACE section.

=item * post_methods

After the METHODS section.

=item * post_properties

After the PROPERTIES section.

=item * post_signals

After the SIGNALS section.

=item * post_enums

After the ENUMS AND FLAGS section.

=item * SEE_ALSO

Replacing the autogenerated SEE ALSO section completely.

=item * COPYRIGHT

Replacing the autogenerated COPYRIGHT section completely.

=back

=cut

sub podify_pods
{
	my $pods = shift;
	my $position = shift;

	my $ret = '';

	if ($position)
	{
		foreach (@$pods)
		{
			$ret .= join ("\n", @{$_->{lines}})."\n\n"
				if (exists ($_->{position}) and 
				    $_->{position} eq $position);
		}
	}
	else
	{
		foreach (@$pods)
		{
			$ret .= join ("\n", @{$_->{lines}})."\n\n"
				unless ($_->{position});
		}
	}
	return $ret ne '' ? $ret : undef;
}

=item $string = podify_ancestors ($packagename)

Pretty-prints the ancestry of I<$packagename> from the Glib type system's
point of view.  This uses Glib::Type->list_ancestors; see that function's
docs for an explanation of why that's different from looking at @ISA.

Returns the new text as a string, or undef if I<$packagename> is not a
registered GType.

=cut

sub podify_ancestors {
	my @anc;
	eval { @anc = Glib::Type->list_ancestors (shift); 1; };
	return undef unless (@anc or not $@);

	my $parents = [ reverse @anc ];

	my $depth = 0;
	my $str = '  '.pop(@anc)."\n";
	foreach (reverse @anc) {
		$str .= "  " . "     "x$depth . "+----$_\n";
		$depth++;
	}
	$str .= "\n";

	return ($str, $parents);
}

=item $string = podify_interfaces ($packagename)

Pretty-print the list of GInterfaces that I<$packagename> implements.
Returns the text as a string, or undef if the type implements no interfaces.

=cut

sub podify_interfaces {
	my @int;
	eval { @int = Glib::Type->list_interfaces (shift); 1; };
	return undef unless (@int or not defined ($@));
	return '  '.join ("\n  ", @int)."\n\n";
}

=item $string = podify_methods ($packagename)

Call C<xsub_to_pod> on all the xsubs under the key I<$packagename> in the
data extracted by xsdocparse.pl.

Returns the new text as a string, or undef if there are no xsubs in
I<$packagename>.

=cut

sub podify_methods
{
	my $package = shift;
	my $xsubs = shift;
	return undef unless $xsubs && @$xsubs;
	# we will be re-using $package from here on out.

	my $str = '';
	my $nfound = 0;
	my $nused  = 0;
	my $method;

	# based on rm's initial thought and then code/ideas by Marc 'HE'
	# Brockschmidt, and Peter Haworth
	@$xsubs = sort { 
		my ($at, $bt);
		for ($at=$a->{symname}, $bt=$b->{symname})
		{
			# remove prefixes
			s/^.+:://;
			# new's goto the front
			s/^new/\x00/;
			# group set's/get'ss
			s/^(get|set)_(.+)/$2_$1/;
			# put \<set\>'s with \<get\>'s
			s/^(get|set)$/get_$1/;
		}
		# now actually do the sorting compare
		$at cmp $bt; 
	} @$xsubs;

	#$str .= "=over\n\n";
	foreach (@$xsubs) {
		# skip if the method is hidden
		next if ($_->{hidden});
		
		$_->{symname} =~ m/^(?:([\w:]+)::)?([\w]+)$/;
		$package = $1 || $_->{package};
		$method = $2;

		# skip DESTROY altogether
		next if $method eq 'DESTROY';

		++$nfound;

		# don't document it if we can't actually call it.
		if ($package->can ($method)) {
			$str .= xsub_to_pod ($_, '=head2');
			++$nused;
		} else {
			# this print should only be temporary
			print STDERR "missing: $package->$method\n";
		}
	}
	#$str .= "=back\n\n";

	if ($nused == 0) {
		# no xsubs were used.
		if ($nfound > 0) {
			# but some were found and not used.  
			# say something to that effect.
			print STDERR "No methods found for $package\n";
			$str = "

Some methods defined for $package are not available in the particular
library versions against which this module was compiled. 

";
		} else {
			# no methods found, nothing to say
			$str = undef;
		}
	}
			
	$str;
}

=item $string = podify_see_alsos (@entries)

Creates a list of links to be placed in the SEE ALSO section of the page.
Returns undef if nothing is in the input list.

=cut

sub podify_see_alsos
{
	my @entries = @_;

	return undef unless scalar @entries;
	
	# create the see also list
	join (', ',
		map {
			if (/^\s*L</) {
				$_;
			} else {
				"L<$_>";
			}
		}
		@entries)
	    . "\n";
}

=item $string = get_copyright

Returns a string that will/should be placed on each page.  You can control
the text of this string by calling the class method I<set_copyright>.

If no text has been set, we will attempt to create one for you, using what
has been passed to I<set_year>, I<set_authors>, and I<set_main_mod>.  The
year defaults to the current year, the authors default to
'The Gtk2-Perl Team', and the main mod is empty by default.  You want the
main mod to be set to the main module of your extension for the SEE ALSO
section, and on the assumption that a decent license notice can be found in
that module's doc, we point the reader there.

So, in general, you will want to specify at least one of these, so that you
don't credit your work to us under the LGPL.

To set them do something similar to the following in the first part of your
postamble section in Makefile.PL.  All occurrences of <br> in the copyright
are replaced with newlines, to make it easier to put in a multi-line string.

  POD_SET=Glib::GenPod::set_copyright(qq{Copyright 1999 team-foobar<br>LGPL});

Glib::MakeHelper::postamble_docs_full() does this sort of thing for you.

=cut

sub get_copyright
{
	my $str = $COPYRIGHT;
	if (! $str) {
		# construct a default.
		$str = "\nCopyright (C) $YEAR $AUTHORS\n\n";
		$str .= "This software is licensed under the LGPL;"
		     . " see $MAIN_MOD for a full notice.\n"
			if $MAIN_MOD;
	}

	# a way to make returns	
	$str =~ s/<br>/\n/g;
	return $str."\n";
}

sub set_copyright {
	$COPYRIGHT = shift;
}

sub set_year {
	$YEAR = shift;
}

sub set_authors {
	$AUTHORS = shift;
}

sub set_main_mod {
	$MAIN_MOD = shift;
}

sub preprocess_pod
{
	my $pod = shift;

	foreach (@{$pod->{lines}})
	{
		# =for include filename
		# =for include !cmd
		if (/^=for\s+include\s+(!)?(.*)$/)
		{
			if ($1)
			{
				chomp($_ = `$2`);
			}
			else
			{
				if (open INC, "<$2")
				{
					local $/ = undef;
					$_ = <INC>;
				}
				else
				{
					carp "\n\nunable to open $2 for inclusion, at ".
					     $pod->{filename}.':'.$pod->{line};
				}
			}
		}
	}
}

=back

=head2 Helpers

=over

=item $perl_type = convert_type ($ctypestring)

Convert a C type name to a Perl type name.

Uses %Glib::GenPod::basic_types to look for some known basic types,
and uses Glib::Type->package_from_cname to look up the registered
package corresponding to a C type name.  If no suitable mapping can
be found, this just returns the input string.

=cut

sub convert_type {
	my $typestr = shift;

	$typestr =~ /^\s*				# leading space
	              (?:const\s+)?			# maybe a const
	              ([:\w]+)				# the name
	              (\s*\*)?				# maybe a star
	              \s*$/x;				# trailing space
	my $ctype   = $1 || '!!';
	if ($ctype eq '!!') {
		warn "Glib::GenPod: Unable to parse type '$typestr'";
	}

	# variant type
	$ctype =~ s/(?:_(ornull|copy|own_ornull|own|noinc_ornull|noinc))$//;
	my $variant = $1 || "";

	my $perl_type;

	if (exists $basic_types{$ctype}) {
		$perl_type = $basic_types{$ctype};

	} elsif ($ctype =~ m/::/) {
		# :: is not valid in GLib type names, so there's no point
		# in asking the GLib type system if it knows this name,
		# because it's probably already a perl type name.
		$perl_type = $ctype;

	} else {
		eval
		{
			$perl_type = Glib::Type->package_from_cname ($ctype);
			1;
		} or do {
			# this warning will have something to do with the
			# package not being registered, a fact which will
			# of interest to a person documenting or developing
			# the documented module, but not to us developing
			# the documentation generator.  thus, this warning
			# doesn't need a line number attribution.
			# let's strip that...
			$@ =~ s/\s*at (.*) line \d+\.$/./;
			warn "$@";
			# ... and fall back gracefully.
			$perl_type = $ctype;
		}
	}

	if ($variant && $variant =~ m/ornull/) {
		$perl_type .= " or undef";
	}

	$perl_type
}


=item $string = xsub_to_pod ($xsub, $sigprefix='')

Convert an xsub hash into a string of pod describing it.  Includes the
call signature, argument listing, and description, honoring special
switches in the description pod (arg and signature overrides).

=cut

sub xsub_to_pod {
	my $xsub = shift;
	my $sigprefix = shift || '';
	my $alias = $xsub->{symname};
	my $str;

	# ensure that if there's pod for this xsub, we have it now.
	# this should probably happen somewhere outside of this function,
	# but, eh...
	my @podlines = ();
	if (defined $xsub->{pod}) {
		@podlines = @{ $xsub->{pod}{lines} };
	}

	# look for annotations in the pod lines.
	# stuff in the pods overrides whatever we'd generate.
	my @signatures = ();
	if (@podlines) {
		# since we're modifying the list while traversing
		# it, go back to front.
		for (my $i = $#podlines ; $i >= 0 ; $i--) {
			if ($podlines[$i] =~ s/^=(for\s+)?signature\s+//) {
				unshift @signatures, $podlines[$i];
				splice @podlines, $i, 1;
			} elsif ($podlines[$i] =~ /^=(?:for\s+)?arg\s+
			                           (\$?[\w.]+)   # arg name
			                           (?:\s*\(([^)]*)\))? # type
			                           \s*
			                           (.*)$/x) { # desc
				# this is a little convoluted, because we
				# need to ensure that the args array and
				# hash exist before using them.  we may be
				# getting an =arg command on something that
				# doesn't list this name in the xsub
				# declaration.
				$xsub->{args} = [] if not exists $xsub->{args};
				my ($a, undef) =
					grep { $_->{name} eq $1 }
				                  @{ $xsub->{args} };
				$a = {}, push @{$xsub->{args}}, $a
					if not defined $a;
				$a->{name} = $1 if not defined $a->{name};
				$a->{desc} = $3;
				if ($2) {
					if ($2 =~ m/^_*hide_*$/i) {
						$a->{hide}++;
					} else {
						$a->{type} = $2;
					}
				}
				# "just eat it!  eat it!  get yourself and
				# egg and beat it!"  -- weird al
				splice @podlines, $i, 1;
			}
		}
	}

	#
	# the call signature(s).
	#
	push @signatures, compile_signature ($xsub)
		unless @signatures;

	foreach (@signatures) {
		s/>(\w+)/>B<$1>/;
		$str .= "$sigprefix $_\n\n";
	}

	#
	# list all the arg types.
	#
	my @args;
	@args = @{ $xsub->{args} } if ($xsub->{args});
	shift @args unless $xsub->{function};

	$str .= "=over\n\n" if @args;
	foreach my $a (@args) {
		my $type;
		next if $a->{hide};
		if ($a->{name} eq '...') {
			$type = 'list';
		} else {
			if (not defined $a->{type}) {
				warn "$alias: no type defined for arg"
				   . " \$$a->{name}\n";
				$type = "(unknown)";
			} else {
				$type = convert_arg_type ($a->{type});
			}
		}
		$str .= "=item * "
		      . fixup_arg_name ($a->{name})
		      . " ($type) "
		      . ($a->{desc} ? $a->{desc} : "")
		      . "\n\n";
	}
	$str .= "=back\n\n" if @args;

	if (@podlines) {
		shift @podlines;
		pop @podlines;
		$str .= join("\n", @podlines)."\n\n";
	}

	$str .= "May croak with a L<Glib::Error> in \$@ on failure.\n\n"
		if ($xsub->{gerror});

	$str .= "This method is deprecated and should not be used in newly written code.\n\n"
		if ($xsub->{deprecated});


	# When there are multiple version guards of the same type, we only want
	# the innermost.
	my %version_conditions;
	my %prefix_to_name = (
		GTK => 'gtk+',
	);
	foreach (@{ $xsub->{preprocessor_conditionals} }) {
		if (m/^\s*(\w+)_CHECK_VERSION\s*\((\d+),\s*(\d+)/) {
			my $lib_name = $prefix_to_name{$1} || lc $1;
			$version_conditions{$lib_name} = "$2.$3";
		}
	}
	foreach my $lib_name (keys %version_conditions) {
		$str .= "Since: $lib_name $version_conditions{$lib_name}\n\n";
	}

	$str
}

=item $string = compile_signature ($xsub)

Given an xsub hash, return a string with the call signature for that
xsub.

=cut

sub compile_signature {
	my $xsub = shift;

	my @args;
	@args = @{ $xsub->{args} } if ($xsub->{args});

	my $call;

	if ($xsub->{function}) {
		$call = $xsub->{symname};
	} else {
		# find the method's short name
		my $method = $xsub->{symname};
		$method =~ s/^(.*):://;

		my $package = $1 || $xsub->{package};

		# methods always eat the first arg as the instance.
		my $instance = shift @args;

		my $obj = defined ($instance->{type})
		        ? '$'.$instance->{name}
			: $package;

		$call = "$obj\-E<gt>$method";
	}

	# compile the arg list string
	my $argstr = join ", ", map {
			fixup_arg_name ($_->{name})
			. (defined $_->{default}
			   ? '='.fixup_default ($_->{default})
			   : '')
		} @args;

	# compile the return list string
	my @outlist = map { $_->{name} } @{ $xsub->{outlist} };
	if (defined $xsub->{return_type}) {
		my @retnames = map { convert_return_type_to_name ($_) }
				@{ $xsub->{return_type} };
		unshift @outlist, @retnames;
	}
	my $retstr = @outlist
	           ? (@outlist > 1
		      ? "(".join (", ", @outlist).")"
		      : $outlist[0]
		     )." = "
		   : (defined $xsub->{codetype} and
		      $xsub->{codetype} eq 'PPCODE'
		      ? 'list = '
		      : ''
		     );
	
	"$retstr$call ".($argstr ? "($argstr)" : "");
}

=item $string = fixup_arg_name ($name)

Prepend a $ to anything that's not the literal ellipsis string '...'.

=cut

sub fixup_arg_name {
	my $name = shift;
	my $sigil = $name eq '...' ? '' : '$';
	return $sigil.$name;
}

=item fixup_default

Mangle default parameter values from C to Perl values.  Mostly, this
does NULL => undef.

=cut

sub fixup_default {
	my $value = shift;
	return (defined ($value) 
	        ? ($value eq 'NULL' ? 'undef' : $value)
		: '');
}

=item convert_arg_type

C type to Perl type conversion for argument types.

=cut

sub convert_arg_type { convert_type (@_) }


=item convert_return_type_to_name

C type to Perl type conversion suitable for return types.

=cut

sub convert_return_type_to_name {
	my $type = convert_type (@_);
	if ($type =~ s/^.*:://) {
		$type = lc $type;
	}
	return $type;
}

sub mkdir_p {
	my $path = shift;
	my @dirs = File::Spec->splitdir ($path);
	my $p = shift @dirs;
	do {
		mkdir $p or die "can't create dir $p: $!\n" unless -d $p;
		$p = File::Spec->catdir ($p, shift @dirs);
	} while (@dirs);
}

sub convert_to_cname {
	my $perlname = shift;
	my $cname = $perlname;
	$cname =~ s/^Gtk2::Gdk::/Gdk/;
	$cname =~ s/^Gtk2::/Gtk/;
	$cname =~ s/^Gnome2::Bonobo::/Bonobo/;
	$cname =~ s/^Gnome2::/Gnome/;
	$cname =~ s/:://g;
	my $tmp;
	eval { $tmp = Glib::Type->package_from_cname($cname); };
	if ($@ || $tmp ne $perlname) {
		return;
	}
	return $cname;
}

1;
__END__

=back

=head1 SEE ALSO

L<Glib::ParseXSDoc>

=head1 AUTHORS

muppet bashed out the xsub signature generation in a few hours on a wednesday
night when band practice was cancelled at the last minute; he and ross
mcfarland hacked this module together via irc and email over the next few days.

=head1 COPYRIGHT AND LICENSE

Copyright (C) 2003-2004, 2010-2013 by the gtk2-perl team

This library is free software; you can redistribute it and/or modify
it under the terms of the Lesser General Public License (LGPL).  For
more information, see http://www.fsf.org/licenses/lgpl.txt

=cut
