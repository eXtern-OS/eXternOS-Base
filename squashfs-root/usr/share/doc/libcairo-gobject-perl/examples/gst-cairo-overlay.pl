#!/usr/bin/perl

# This is a Perl port written by g.schlmm at googlemail dot com of the
# cairo_overlay.c example found at
# <http://cgit.freedesktop.org/gstreamer/gst-plugins-good/tree/tests/examples/cairo/cairo_overlay.c>.

use strict;
use warnings;
use Glib qw(TRUE FALSE);
use GStreamer '-init';
use Cairo::GObject;

my $loop = Glib::MainLoop->new;

# create the pipeline
my $pipeline = GStreamer::Pipeline->new ('cairo-overlay-example');

my ($source, $a1, $a2, $sink) = GStreamer::ElementFactory->make (
    videotestsrc => 'source',
    ffmpegcolorspace => 'a1',
    ffmpegcolorspace => 'a2',
    autovideosink => 'sink'
);

my $cairo_overlay = GStreamer::ElementFactory->make ('cairooverlay', 'overlay');

my ($width, $height, $valid);
$cairo_overlay->signal_connect (draw => sub {
    my ($overlay, $context, $timestamp, $duration) = @_;
    return if (!$valid);
    my $scale = 2 * ((($timestamp / int(1e7)) % 70) + 30) / 100.0;
    $context->translate ($width / 2, ($height / 2) - 30);
    $context->scale ($scale, $scale);
    $context->move_to (0, 0);
    $context->curve_to (0, -30, -50, -30, -50, 0);
    $context->curve_to (-50, 30, 0, 35, 0, 60);
    $context->curve_to (0, 35, 50, 30, 50, 0);
    $context->curve_to (50, -30, 0, -30, 0, 0);
    $context->set_source_rgba (0.9, 0.0, 0.1, 0.7);
    $context->fill;
});

$cairo_overlay->signal_connect (caps_changed => sub {
    my ($overlay, $caps) = @_;
    $width = 0; $height = 0;
    for (@{$caps->get_structure(0)->{fields}}) {
        $width = $_->[2]
            if ($_->[0] eq 'width');
        $height = $_->[2]
            if ($_->[0] eq 'height');
        last if ($height > 0 && $width > 0);
    }
    $valid = 1 if ($height > 0 && $width > 0);
});

$pipeline->add ($source, $a1, $cairo_overlay, $a2, $sink);
$source->link ($a1);
$a1->link ($cairo_overlay);
$cairo_overlay->link ($a2);
$a2->link ($sink);

my $bus = $pipeline->get_bus;
$bus->add_signal_watch;
$bus->signal_connect(message => sub {
    my ($bus, $message) = @_;
    if ($message->type eq 'eos') {
      $loop->quit();
    }
    return TRUE;
});

$pipeline->set_state ('playing');

$loop->run;

$pipeline->set_state ('null');
