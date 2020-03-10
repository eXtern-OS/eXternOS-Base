#!/usr/bin/perl
use strict;
use warnings;

my $surface = Cairo::ImageSurface->create ('argb32', 1000, 1000);
my $context = CustomContext->create ($surface);
$context->draw_star;
$context->show_page;
$surface->write_to_png ($0 . '.png');

package CustomContext;

use strict;
use warnings;
use Cairo;
use Math::Trig qw/pi/;

use base qw/Cairo::Context/;

sub create {
  my ($package, $surface) = @_;

  my $self = $package->SUPER::create($surface);

  return bless $self, $package;
}

sub draw_star {
  my ($self) = @_;

  my $width = $self->get_target()->get_width();
  my $height = $self->get_target()->get_height();

  $self->rectangle (0, 0, $width, $height);
  $self->set_source_rgb (1, 1, 1);
  $self->fill;

  $self->save;
  {
    $self->set_source_rgba (0, 0, 0, 0.5);
    $self->translate ($width / 2, $height / 2);

    my $mx = $width / 3.0;
    my $count = 100;
    foreach (0 .. $count-1) {
      $self->new_path;
      $self->move_to (0, 0);
      $self->rel_line_to (-$mx, 0);
      $self->stroke;
      $self->rotate ((pi() * 2) / $count);
    }
  }
  $self->restore;
}
