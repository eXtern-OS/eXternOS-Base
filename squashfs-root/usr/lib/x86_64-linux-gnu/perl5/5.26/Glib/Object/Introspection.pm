# Copyright (C) 2010-2014 Torsten Schoenfeld <kaffeetisch@gmx.de>
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Library General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Library General Public License for
# more details.
#
# See the LICENSE file in the top-level directory of this distribution for the
# full license terms.

package Glib::Object::Introspection;

use strict;
use warnings;
use Glib;

our $VERSION = '0.044';

use Carp;
$Carp::Internal{(__PACKAGE__)}++;

require XSLoader;
XSLoader::load(__PACKAGE__, $VERSION);

my @OBJECT_PACKAGES_WITH_VFUNCS;
my %SEEN;
our %_FORBIDDEN_SUB_NAMES = map { $_ => 1 } qw/AUTOLOAD CLONE DESTROY BEGIN
                                               UNITCHECK CHECK INIT END/;
our %_BASENAME_TO_PACKAGE;
our %_REBLESSERS;

sub _create_invoker_sub {
  my ($basename, $namespace, $name,
      $shift_package_name, $flatten_array_ref_return,
      $handle_sentinel_boolean) = @_;
  if ($flatten_array_ref_return && $handle_sentinel_boolean) {
    croak sprintf
      "Cannot handle the options flatten_array_ref and handle_sentinel_boolean " .
      "at the same time for %s%s::%s",
      $_BASENAME_TO_PACKAGE{$basename},
      defined $namespace ? "::$namespace" : '',
      $name;
  }
  if ($flatten_array_ref_return) {
    return sub {
      shift if $shift_package_name;
      my $ref = __PACKAGE__->invoke($basename, $namespace, $name, @_);
      return if not defined $ref;
      return wantarray ? @$ref : $ref->[$#$ref];
    };
  } elsif ($handle_sentinel_boolean) {
    return sub {
      shift if $shift_package_name;
      my ($bool, @stuff) = __PACKAGE__->invoke($basename, $namespace, $name, @_);
      return $bool
        ? @stuff[0..$#stuff] # slice to correctly behave in scalar context
        : ();
    };
  } else {
    return sub {
      shift if $shift_package_name;
      return __PACKAGE__->invoke($basename, $namespace, $name, @_);
    };
  }
}

sub setup {
  my ($class, %params) = @_;
  my $basename = $params{basename};
  my $version = $params{version};
  my $package = $params{package};
  my $search_path = $params{search_path} || undef;
  my $name_corrections = $params{name_corrections} || {};

  # Avoid repeating setting up a library as this can lead to issues, e.g., due
  # to types being registered more than once with perl-Glib.  In particular,
  # the lazy-loading mechanism of Glib::Object is not prepared to handle
  # repeated type registrations.
  if ($SEEN{$basename}{$version}{$package}++) {
    return;
  }

  $_BASENAME_TO_PACKAGE{$basename} = $package;

  my %shift_package_name_for = exists $params{class_static_methods}
    ? map { $_ => 1 } @{$params{class_static_methods}}
    : ();
  my %flatten_array_ref_return_for = exists $params{flatten_array_ref_return_for}
    ? map { $_ => 1 } @{$params{flatten_array_ref_return_for}}
    : ();
  my %handle_sentinel_boolean_for = exists $params{handle_sentinel_boolean_for}
    ? map { $_ => 1 } @{$params{handle_sentinel_boolean_for}}
    : ();
  my @use_generic_signal_marshaller_for = exists $params{use_generic_signal_marshaller_for}
    ? @{$params{use_generic_signal_marshaller_for}}
    : ();

  if (exists $params{reblessers}) {
    $_REBLESSERS{$_} = $params{reblessers}->{$_}
      for keys %{$params{reblessers}}
  }

  __PACKAGE__->_load_library($basename, $version, $search_path);

  my ($functions, $constants, $fields, $interfaces, $objects_with_vfuncs) =
    __PACKAGE__->_register_types($basename, $package);

  no strict qw(refs);
  no warnings qw(redefine);

  foreach my $namespace (keys %{$functions}) {
    my $is_namespaced = $namespace ne "";
    NAME:
    foreach my $name (@{$functions->{$namespace}}) {
      my $auto_name = $is_namespaced
        ? $package . '::' . $namespace . '::' . $name
        : $package . '::' . $name;
      my $corrected_name = exists $name_corrections->{$auto_name}
        ? $name_corrections->{$auto_name}
        : $auto_name;
      if (defined &{$corrected_name}) {
        next NAME;
      }
      *{$corrected_name} = _create_invoker_sub (
        $basename, $is_namespaced ? $namespace : undef, $name,
        $shift_package_name_for{$corrected_name},
        $flatten_array_ref_return_for{$corrected_name},
        $handle_sentinel_boolean_for{$corrected_name});
    }
  }

  foreach my $name (@{$constants}) {
    my $auto_name = $package . '::' . $name;
    my $corrected_name = exists $name_corrections->{$auto_name}
      ? $name_corrections->{$auto_name}
      : $auto_name;
    # Install a sub which, on the first invocation, calls _fetch_constant and
    # then overrides itself with a constant sub returning that value.
    *{$corrected_name} = sub {
      my $value = __PACKAGE__->_fetch_constant($basename, $name);
      {
        *{$corrected_name} = sub { $value };
      }
      return $value;
    };
  }

  foreach my $namespace (keys %{$fields}) {
    foreach my $field_name (@{$fields->{$namespace}}) {
      my $auto_name = $package . '::' . $namespace . '::' . $field_name;
      my $corrected_name = exists $name_corrections->{$auto_name}
        ? $name_corrections->{$auto_name}
        : $auto_name;
      *{$corrected_name} = sub {
        my ($invocant, $new_value) = @_;
        my $old_value = __PACKAGE__->_get_field($basename, $namespace,
                                                $field_name, $invocant);
        # If a new value is provided, even if it is undef, update the field.
        if (scalar @_ > 1) {
          __PACKAGE__->_set_field($basename, $namespace,
                                  $field_name, $invocant, $new_value);
        }
        return $old_value;
      };
    }
  }

  foreach my $name (@{$interfaces}) {
    my $adder_name = $package . '::' . $name . '::_ADD_INTERFACE';
    *{$adder_name} = sub {
      my ($class, $target_package) = @_;
      __PACKAGE__->_add_interface($basename, $name, $target_package);
    };
  }

  foreach my $object_name (@{$objects_with_vfuncs}) {
    my $object_package = $package . '::' . $object_name;
    my $installer_name = $object_package . '::_INSTALL_OVERRIDES';
    *{$installer_name} = sub {
      my ($target_package) = @_;
      # Delay hooking up the vfuncs until INIT so that we can see whether the
      # package defines the relevant subs or not.  FIXME: Shouldn't we only do
      # the delay dance if ${^GLOBAL_PHASE} eq 'START'?
      push @OBJECT_PACKAGES_WITH_VFUNCS,
           [$basename, $object_name, $target_package];
    };
  }

  foreach my $packaged_signal (@use_generic_signal_marshaller_for) {
    __PACKAGE__->_use_generic_signal_marshaller_for (@$packaged_signal);
  }

  return;
}

INIT {
  no strict qw(refs);

  # Hook up the implemented vfuncs first.
  foreach my $target (@OBJECT_PACKAGES_WITH_VFUNCS) {
    my ($basename, $object_name, $target_package) = @{$target};
    __PACKAGE__->_install_overrides($basename, $object_name, $target_package);
  }

  # And then, for each vfunc in our ancestry that has an implementation, add a
  # wrapper sub to our immediate parent.  We delay this step until after all
  # Perl overrides are in place because otherwise, the override code would see
  # the fallback vfuncs (via gv_fetchmethod) we are about to set up, and it
  # would mistake them for an actual implementation.  This would then lead it
  # to put Perl callbacks into the vfunc slots regardless of whether the Perl
  # class in question actually provides implementations.
  my %implementer_packages_seen;
  foreach my $target (@OBJECT_PACKAGES_WITH_VFUNCS) {
    my ($basename, $object_name, $target_package) = @{$target};
    my @non_perl_parent_packages =
      __PACKAGE__->_find_non_perl_parents($basename, $object_name,
                                          $target_package);

    # For each non-Perl parent, look at all the vfuncs it and its parents
    # provide.  For each vfunc which has an implementation in the parent
    # (i.e. the corresponding struct pointer is not NULL), install a fallback
    # sub which invokes the vfunc implementation.  This assumes that
    # @non_perl_parent_packages contains the parents in "ancestorial" order,
    # i.e. the first entry must be the immediate parent.
    IMPLEMENTER: for (my $i = 0; $i < @non_perl_parent_packages; $i++) {
      my $implementer_package = $non_perl_parent_packages[$i];
      next IMPLEMENTER if $implementer_packages_seen{$implementer_package}++;
      for (my $j = $i; $j < @non_perl_parent_packages; $j++) {
        my $provider_package = $non_perl_parent_packages[$j];
        my @vfuncs = __PACKAGE__->_find_vfuncs_with_implementation(
                       $provider_package, $implementer_package);
        VFUNC: foreach my $vfunc_name (@vfuncs) {
          my $perl_vfunc_name = uc $vfunc_name;
          if (exists $_FORBIDDEN_SUB_NAMES{$perl_vfunc_name}) {
            $perl_vfunc_name .= '_VFUNC';
          }
          my $full_perl_vfunc_name =
            $implementer_package . '::' . $perl_vfunc_name;
          next VFUNC if defined &{$full_perl_vfunc_name};
          *{$full_perl_vfunc_name} = sub {
            __PACKAGE__->_invoke_fallback_vfunc($provider_package,
                                                $vfunc_name,
                                                $implementer_package,
                                                @_);
          }
        }
      }
    }
  }

  @OBJECT_PACKAGES_WITH_VFUNCS = ();
}

# Monkey-patch Glib with a generic constructor for boxed types.  Glib cannot
# provide this on its own because it does not know how big the struct of a
# boxed type is.  FIXME: This sort of violates encapsulation.
{
  if (! defined &{Glib::Boxed::new}) {
    *{Glib::Boxed::new} = sub {
      my ($class, @rest) = @_;
      my $boxed = Glib::Object::Introspection->_construct_boxed ($class);
      my $fields = 1 == @rest ? $rest[0] : { @rest };
      foreach my $field (keys %$fields) {
        if ($boxed->can ($field)) {
          $boxed->$field ($fields->{$field});
        }
      }
      return $boxed;
    }
  }
}

package Glib::Object::Introspection::_FuncWrapper;

use overload
      '&{}' => sub {
                 my ($func) = @_;
                 return sub { Glib::Object::Introspection::_FuncWrapper::_invoke($func, @_) }
               },
      fallback => 1;

package Glib::Object::Introspection;

1;
__END__

=encoding utf8

=head1 NAME

Glib::Object::Introspection - Dynamically create Perl language bindings

=head1 SYNOPSIS

  use Glib::Object::Introspection;
  Glib::Object::Introspection->setup(
    basename => 'Gtk',
    version => '3.0',
    package => 'Gtk3');
  # now GtkWindow, to mention just one example, is available as
  # Gtk3::Window, and you can call gtk_window_new as Gtk3::Window->new

=head1 ABSTRACT

Glib::Object::Introspection uses the gobject-introspection and libffi projects
to dynamically create Perl bindings for a wide variety of libraries.  Examples
include gtk+, webkit, libsoup and many more.

=head1 DESCRIPTION FOR LIBRARY USERS

To allow Glib::Object::Introspection to create bindings for a library, the
library must have installed a typelib file, for example
C<$prefix/lib/girepository-1.0/Gtk-3.0.typelib>.  In your code you then simply
call C<< Glib::Object::Introspection->setup >> with the following key-value
pairs to set everything up:

=over

=item basename => $basename

The basename of the library that should be wrapped.  If your typelib is called
C<Gtk-3.0.typelib>, then the basename is 'Gtk'.

=item version => $version

The particular version of the library that should be wrapped, in string form.
For C<Gtk-3.0.typelib>, it is '3.0'.

=item package => $package

The name of the Perl package where every class and method of the library should
be rooted.  If a library with basename 'Gtk' contains an class 'GtkWindow',
and you pick as the package 'Gtk3', then that class will be available as
'Gtk3::Window'.

=back

The Perl wrappers created by C<Glib::Object::Introspection> follow the
conventions of the L<Glib> module and old hand-written bindings like L<Gtk2>.
You can use the included tool C<perli11ndoc> to view the documentation of all
installed libraries organized and displayed in accordance with these
conventions.  The guiding principles underlying the conventions are described
in the following.

=head2 Namespaces and Objects

The namespaces of the C libraries are mapped to Perl packages according to the
C<package> option specified, for example:

  gtk_ => Gtk3
  gdk_ => Gtk3::Gdk
  gdk_pixbuf_ => Gtk3::Gdk::Pixbuf
  pango_ => Pango

Classes, interfaces and boxed and fundamental types get their own namespaces,
in a way, as the concept of the GType is completely replaced in the Perl
bindings by the Perl package name.

  GtkButton => Gtk3::Button
  GdkPixbuf => Gtk3::Gdk::Pixbuf
  GtkScrolledWindow => Gtk3::ScrolledWindow
  PangoFontDescription => Pango::FontDescription

With this package mapping and Perl's built-in method lookup, the bindings can
do object casting for you.  This gives us a rather comfortably object-oriented
syntax, using normal Perl object semantics:

  in C:
    GtkWidget * b;
    b = gtk_check_button_new_with_mnemonic ("_Something");
    gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (b), TRUE);
    gtk_widget_show (b);

  in Perl:
    my $b = Gtk3::CheckButton->new_with_mnemonic ('_Something');
    $b->set_active (1);
    $b->show;

You see from this that cast macros are not necessary and that you don't need to
type namespace prefixes quite so often, so your code is a lot shorter.

=head2 Flags and Enums

Flags and enum values are handled as strings, because it's much more readable
than numbers, and because it's automagical thanks to the GType system.  Values
are referred to by their nicknames; basically, strip the common prefix,
lower-case it, and optionally convert '_' to '-':

  GTK_WINDOW_TOPLEVEL => 'toplevel'
  GTK_BUTTONS_OK_CANCEL => 'ok-cancel' (or 'ok_cancel')

Flags are a special case.  You can't (sensibly) bitwise-or these
string-constants, so you provide a reference to an array of them instead.
Anonymous arrays are useful here, and an empty anonymous array is a simple
way to say 'no flags'.

  FOO_BAR_BAZ | FOO_BAR_QUU | FOO_BAR_QUUX => [qw/baz quu qux/]
  0 => []

In some cases you need to see if a bit is set in a bitfield; methods
returning flags therefore return an overloaded object.  See L<Glib> for
more details on which operations are allowed on these flag objects, but
here is a quick example:

  in C:
    /* event->state is a bitfield */
    if (event->state & GDK_CONTROL_MASK) g_printerr ("control was down\n");

  in Perl:
    # $event->state is a special object
    warn "control was down\n" if $event->state & "control-mask";

But this also works:

  warn "control was down\n" if $event->state * "control-mask";
  warn "control was down\n" if $event->state >= "control-mask";
  warn "control and shift were down\n"
                            if $event->state >= ["control-mask", "shift-mask"];

=head2 Memory Handling

The functions for ref'ing and unref'ing objects and free'ing boxed structures
are not even mapped to Perl, because it's all handled automagically by the
bindings.  Objects will be kept alive so long as you have a Perl scalar
pointing to it or the object is referenced in another way, e.g. from a
container.

The only thing you have to be careful about is the lifespan of non
reference counted structures, which means most things derived from
C<Glib::Boxed>.  If it comes from a signal callback it might be good
only until you return, or if it's the insides of another object then
it might be good only while that object lives.  If in doubt you can
C<copy>.  Structs from C<copy> or C<new> are yours and live as long as
referred to from Perl.

=head2 Callbacks

Use normal Perl callback/closure tricks with callbacks.  The most common use
you'll have for callbacks is with the L<Glib> C<signal_connect> method:

  $widget->signal_connect (event => \&event_handler, $user_data);
  $button->signal_connect (clicked => sub { warn "hi!\n" });

$user_data is optional, and with Perl closures you don't often need it
(see L<perlsub/Persistent variables with closures>).

The userdata is held in a scalar, initialized from what you give in
C<signal_connect> etc.  It's passed to the callback in usual Perl
"call by reference" style which means the callback can modify its last
argument, ie. $_[-1], to modify the held userdata.  This is a little
subtle, but you can use it for some "state" associated with the
connection.

  $widget->signal_connect (activate => \&my_func, 1);
  sub my_func {
    print "activation count: $_[-1]\n";
    $_[-1] ++;
  }

Because the held userdata is a new scalar there's no change to the
variable (etc.) you originally passed to C<signal_connect>.

If you have a parent object in the userdata (or closure) you have to be careful
about circular references preventing parent and child being destroyed.  See
L<perlobj/Two-Phased Garbage Collection> about this generally.  Toplevel
widgets like C<Gtk3::Window> always need an explicit C<< $widget->destroy >> so
their C<destroy> signal is a good place to break circular references.  But for
other widgets it's usually friendliest to avoid circularities in the first
place, either by using weak references in the userdata, or possibly locating a
parent dynamically with C<< $widget->get_ancestor >>.

=head2 Exception handling

Anything that uses GError in C will C<croak> on failure, setting $@ to a
magical exception object, which is overloaded to print as the
returned error message.  The ideology here is that GError is to be used
for runtime exceptions, and C<croak> is how you do that in Perl.  You can
catch a croak very easily by wrapping the function in an eval:

  eval {
    my $pixbuf = Gtk3::Gdk::Pixbuf->new_from_file ($filename);
    $image->set_from_pixbuf ($pixbuf);
  };
  if ($@) {
    print "$@\n"; # prints the possibly-localized error message
    if (Glib::Error::matches ($@, 'Gtk3::Gdk::Pixbuf::Error',
                                  'unknown-format')) {
      change_format_and_try_again ();
    } elsif (Glib::Error::matches ($@, 'Glib::File::Error', 'noent')) {
      change_source_dir_and_try_again ();
    } else {
      # don't know how to handle this
      die $@;
    }
  }

This has the added advantage of letting you bunch things together as you would
with a try/throw/catch block in C++ -- you get cleaner code.  By using
Glib::Error exception objects, you don't have to rely on string matching
on a possibly localized error message; you can match errors by explicit and
predictable conditions.  See L<Glib::Error> for more information.

=head2 Output arguments, lists, hashes

In C you can only return one value from a function, and it is a common practice
to modify pointers passed in to simulate returning multiple values.  In Perl,
you can return lists; any functions which modify arguments are changed to
return them instead.

Arguments and return values that have the types GList or GSList or which are C
arrays of values will be converted to and from references to normal Perl
arrays.  The same holds for GHashTable and references to normal Perl hashes.

=head2 Object class functions

Object class functions like C<Gtk3::WidgetClass::find_style_propery> can be
called either with a package name or with an instance of the package.  For
example:

  Gtk3::WidgetClass::find_style_property ('Gtk3::Button', 'image-spacing')

  my $button = Gtk3::Button->new;
  Gtk3::WidgetClass::find_style_property ($button, 'image-spacing')

=head1 DESCRIPTION FOR LIBRARY BINDING AUTHORS

=head2 C<< Glib::Object::Introspection->setup >>

C<< Glib::Object::Introspection->setup >> takes a few optional arguments that
augment the generated API:

=over

=item search_path => $search_path

A path that should be used when looking for typelibs.  If you use typelibs from
system directories, or if your environment contains a properly set
C<GI_TYPELIB_PATH> variable, then this should not be necessary.

=item name_corrections => { auto_name => new_name, ... }

A hash ref that is used to rename functions and methods.  Use this if you don't
like the automatically generated mapping for a function or method.  For
example, if C<g_file_hash> is automatically represented as
C<Glib::IO::file_hash> but you want C<Glib::IO::File::hash> then pass

  name_corrections => {
    'Glib::IO::file_hash' => 'Glib::IO::File::hash'
  }

=item class_static_methods => [ function1, ... ]

An array ref of function names that you want to be treated as class-static
methods.  That is, if you want be able to call
C<Gtk3::Window::list_toplevels> as C<< Gtk3::Window->list_toplevels >>, then
pass

  class_static_methods => [
    'Gtk3::Window::list_toplevels'
  ]

The function names refer to those after name corrections.

=item flatten_array_ref_return_for => [ function1, ... ]

An array ref of function names that return an array ref that you want to be
flattened so that they return plain lists.  For example

  flatten_array_ref_return_for => [
    'Gtk3::Window::list_toplevels'
  ]

The function names refer to those after name corrections.  Functions occurring
in C<flatten_array_ref_return_for> may also occur in C<class_static_methods>.

=item handle_sentinel_boolean_for => [ function1, ... ]

An array ref of function names that return multiple values, the first of which
is to be interpreted as indicating whether the rest of the returned values are
valid.  This frequently occurs with functions that have out arguments; the
boolean then indicates whether the out arguments have been written.  With
C<handle_sentinel_boolean_for>, the first return value is taken to be the
sentinel boolean.  If it is true, the rest of the original return values will
be returned, and otherwise an empty list will be returned.

  handle_sentinel_boolean_for => [
    'Gtk3::TreeSelection::get_selected'
  ]

The function names refer to those after name corrections.  Functions occurring
in C<handle_sentinel_boolean_for> may also occur in C<class_static_methods>.

=item use_generic_signal_marshaller_for => [ [package1, signal1, [arg_converter1]], ... ]

Use an introspection-based generic signal marshaller for the signal C<signal1>
of type C<package1>.  If given, use the code reference C<arg_converter1> to
convert the arguments that are passed to the signal handler.  In contrast to
L<Glib>'s normal signal marshaller, the generic signal marshaller supports,
among other things, pointer arrays and out arguments.

=item reblessers => { package => \&reblesser, ... }

Tells G:O:I to invoke I<reblesser> whenever a Perl object is created for an
object of type I<package>.  Currently, this only applies to boxed unions.  The
reblesser gets passed the pre-created Perl object and needs to return the
modified Perl object.  For example:

  sub Gtk3::Gdk::Event::_rebless {
    my ($event) = @_;
    return bless $event, lookup_real_package_for ($event);
  }

=back

=head2 C<< Glib::Object::Introspection->invoke >>

To invoke specific functions manually, you can use the low-level C<<
Glib::Object::Introspection->invoke >>.

  Glib::Object::Introspection->invoke(
    $basename, $namespace, $function, @args)

=over

=item * $basename is the basename of a library, like 'Gtk'.

=item * $namespace refers to a namespace inside that library, like 'Window'.  Use
undef here if you want to call a library-global function.

=item * $function is the name of the function you want to invoke.  It can also
refer to the name of a constant.

=item * @args are the arguments that should be passed to the function.  For a
method, this should include the invocant.  For a constructor, this should
include the package name.

=back

C<< Glib::Object::Introspection->invoke >> returns whatever the function being
invoked returns.

=head2 Overrides

To override the behavior of a specific function or method, create an
appropriately named sub in the correct package and have it call C<<
Glib::Object::Introspection->invoke >>.  Say you want to override
C<Gtk3::Window::list_toplevels>, then do this:

  sub Gtk3::Window::list_toplevels {
    # ...do something...
    my $ref = Glib::Object::Introspection->invoke (
                'Gtk', 'Window', 'list_toplevels',
                @_);
    # ...do something...
    return wantarray ? @$ref : $ref->[$#$ref];
  }

The sub's name and package must be those after name corrections.

=head2 Converting a Perl variable to a GValue

If you need to marshal into a GValue, then Glib::Object::Introspection cannot
do this automatically because the type information is missing.  If you do have
this information in your module, however, you can use
Glib::Object::Introspection::GValueWrapper to do the conversion.  In the
wrapper for a function that expects a GValue, do this:

  ...
  my $type = ...; # somehow get the package name that
                  # corresponds to the correct GType
  my $wrapper =
    Glib::Object::Introspection::GValueWrapper->new ($type, $value);
  # now use Glib::Object::Introspection->invoke and
  # substitute $wrapper where you'd use $value
  ...

If you need to call a function that expects an already set-up GValue and
modifies it, use C<get_value> on the wrapper afterwards to obtain the value.
For example:

  my $wrapper =
    Glib::Object::Introspection::GValueWrapper->new ('Glib::Boolean', 0);
  $box->child_get_property ($label, 'expand', $gvalue);
  my $value = $gvalue->get_value

=head2 Handling raw enumerations and flags

If you need to handle raw enumerations/flags or extendable enumerations for
which more than the pre-defined values might be valid, then use C<<
Glib::Object::Introspection->convert_enum_to_sv >>, C<<
Glib::Object::Introspection->convert_sv_to_enum >>, C<<
Glib::Object::Introspection->convert_flags_to_sv >> and C<<
Glib::Object::Introspection->convert_sv_to_flags >>.  They will raise an
exception on unknown values; catching it then allows you to implement fallback
behavior.

  Glib::Object::Introspection->convert_enum_to_sv (package, enum_value)
  Glib::Object::Introspection->convert_sv_to_enum (package, sv)

  Glib::Object::Introspection->convert_flags_to_sv (package, flags_value)
  Glib::Object::Introspection->convert_sv_to_flags (package, sv)

=head1 SEE ALSO

=over

=item perl-Glib: L<Glib>

=item gobject-introspection: L<http://live.gnome.org/GObjectIntrospection>

=item libffi: L<http://sourceware.org/libffi/>

=back

=head1 AUTHORS

=over

=item Emmanuele Bassi <ebassi at linux intel com>

=item muppet <scott asofyet org>

=item Torsten Schönfeld <kaffeetisch at gmx de>

=back

=head1 LICENSE

This library is free software; you can redistribute it and/or modify it under
the terms of the Lesser General Public License (LGPL).  For more information,
see http://www.fsf.org/licenses/lgpl.txt

=cut
