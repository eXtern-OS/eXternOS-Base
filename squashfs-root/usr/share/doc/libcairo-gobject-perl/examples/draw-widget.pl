#!/usr/bin/perl
use Cairo::GObject;
use Glib::Object::Introspection;

Glib::Object::Introspection->setup (
  basename => 'Gtk',
  version => '3.0',
  package => 'Gtk3');
Gtk3::init ([]);

my $window = Gtk3::Window->new ('toplevel');
my $button = Gtk3::Button->new_with_label ('Kazam!');
$window->add ($button);
$window->show_all;

my ($width, undef) = $button->get_preferred_width;
my ($height, undef) = $button->get_preferred_height;
my $surf = Cairo::ImageSurface->create ('argb32', $width,$height);
my $cr = Cairo::Context->create ($surf);

Glib::Idle->add (sub { $button->draw ($cr); Gtk3::main_quit (); });
Gtk3::main ();

$surf->write_to_png ('draw-widget.png');
