# Copyright © 2008 Frank Lichtenheld <frank@lichtenheld.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, you can find it on the World Wide
# Web at http://www.gnu.org/copyleft/gpl.html, or write to the Free
# Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston,
# MA 02110-1301, USA.

package Lintian::Output;

use strict;
use warnings;

use v5.8.0; # for PerlIO
use parent qw(Class::Accessor::Fast);
# The limit is including the "use --foo to see all tags".
use constant DEFAULT_INTERACTIVE_TAG_LIMIT => 4;

use Exporter qw(import);

# Force export as soon as possible, since some of the modules we load also
# depend on us and the sequencing can cause things not to be exported
# otherwise.
our (%EXPORT_TAGS, @EXPORT_OK);

BEGIN {
    %EXPORT_TAGS = (
        messages => [qw(msg v_msg warning debug_msg delimiter perf_log)],
        util => [qw(_global_or_object)]);
    @EXPORT_OK = (@{$EXPORT_TAGS{messages}},@{$EXPORT_TAGS{util}},'string');
}

=head1 NAME

Lintian::Output - Lintian messaging handling

=head1 SYNOPSIS

    # non-OO
    use Lintian::Output qw(:messages);

    $Lintian::Output::GLOBAL->verbosity_level(1);

    msg("Something interesting");
    v_msg("Something less interesting");
    debug_msg(3, "Something very specific");

    # OO
    use Lintian::Output;

    my $out = Lintian::Output->new;

    $out->verbosity_level(-1);
    $out->msg("Something interesting");
    $out->v_msg("Something less interesting");
    $out->debug_msg(3, "Something very specific");

=head1 DESCRIPTION

Lintian::Output is used for all interaction between lintian and the user.
It is designed to be easily extensible via subclassing.

To simplify usage in the most common cases, many Lintian::Output methods
can be used as class methods and will therefor automatically use the object
$Lintian::Output::GLOBAL unless their first argument C<isa('Lintian::Output')>.

=cut

use Lintian::Tags ();

# support for ANSI color output via colored()
use Term::ANSIColor ();

=head1 ACCESSORS

The following fields define the behaviours of Lintian::Output.

=over 4

=item verbosity_level

Determine how verbose the output should be.  "0" is the default value
(tags and msg only), "-1" is quiet (tags only) and "1" is verbose
(tags, msg and v_msg).

=item debug

If set to a positive integer, will enable all debug messages issued with
a level lower or equal to its value.

=item color

Can take the values "never", "always", "auto" or "html".

Whether to colorize tags based on their severity.  The default is "never",
which never uses color.  "always" will always use color, "auto" will use
color only if the output is going to a terminal.

"html" will output HTML <span> tags with a color style attribute (instead
of ANSI color escape sequences).

=item stdout

I/O handle to use for output of messages and tags.  Defaults to C<\*STDOUT>.

=item stderr

I/O handle to use for warnings.  Defaults to C<\*STDERR>.

=item showdescription

Whether to show the description of a tag when printing it.

=item issuedtags

Hash containing the names of tags which have been issued.

=item tag_display_limit

Get/Set the number of times a tag is emitted per processable.

=back

=cut

Lintian::Output->mk_accessors(
    qw(verbosity_level debug color colors stdout
      stderr perf_log_fd perf_debug showdescription
      issuedtags tag_display_limit)
);

# for the non-OO interface
my %default_colors = (
    'E' => 'red',
    'W' => 'yellow',
    'I' => 'cyan',
    'P' => 'green',
    'C' => 'blue',
);

our $GLOBAL = Lintian::Output->new;

sub new {
    my ($class, %options) = @_;
    my $self = {%options};

    bless($self, $class);

    $self->stdout(\*STDOUT);
    $self->stderr(\*STDERR);
    $self->perf_log_fd(\*STDOUT);
    $self->colors({%default_colors});
    $self->issuedtags({});
    $self->{'proc_id2tag_count'} = {};

    # Set defaults to avoid "uninitialized" warnings
    $self->verbosity_level(0);
    $self->perf_debug(0);
    $self->color('never');
    return $self;
}

=head1 CLASS/INSTANCE METHODS

These methods can be used both with and without an object.  If no object
is given, they will fall back to the $Lintian::Output::GLOBAL object.

=over 4

=item C<msg(@args)>

Will output the strings given in @args, one per line, each line prefixed
with 'N: '.  Will do nothing if verbosity_level is less than 0.

=item C<v_msg(@args)>

Will output the strings given in @args, one per line, each line prefixed
with 'N: '.  Will do nothing unless verbosity_level is greater than 0.

=item C<debug_msg($level, @args)>

$level should be a positive integer.

Will output the strings given in @args, one per line, each line prefixed
with 'N: '.  Will do nothing unless debug is set to a positive integer
>= $level.

=cut

sub msg {
    my ($self, @args) = _global_or_object(@_);

    return if $self->verbosity_level < 0;
    $self->_message(@args);
    return;
}

sub v_msg {
    my ($self, @args) = _global_or_object(@_);

    return unless $self->verbosity_level > 0;
    $self->_message(@args);
    return;
}

sub debug_msg {
    my ($self, $level, @args) = _global_or_object(@_);

    return unless $self->debug && ($self->debug >= $level);

    $self->_message(@args);
    return;
}

=item C<warning(@args)>

Will output the strings given in @args on stderr, one per line, each line
prefixed with 'warning: '.

=cut

sub warning {
    my ($self, @args) = _global_or_object(@_);

    return if $self->verbosity_level < 0;
    $self->_warning(@args);
    return;
}

=item  C<perf_log(@args)>

Like "v_msg", except output is possibly sent to a dedicated log
file.

Will output the strings given in @args, one per line.  The lines will
not be prefixed.  Will do nothing unless perf_debug is set to a
positive integer.

=cut

sub perf_log {
    my ($self, @args) = _global_or_object(@_);

    return unless $self->perf_debug;

    $self->_print($self->perf_log_fd, '', @args);
    return;
}

=item C<delimiter()>

Gives back a string that is usable for separating messages in the output.
Note: This does not print anything, it just gives back the string, use
with one of the methods above, e.g.

 v_msg('foo', delimiter(), 'bar');

=cut

sub delimiter {
    my ($self) = _global_or_object(@_);

    return $self->_delimiter;
}

=item C<issued_tag($tag_name)>

Indicate that the named tag has been issued.  Returns a boolean value
indicating whether the tag had previously been issued by the object.

=cut

sub issued_tag {
    my ($self, $tag_name) = _global_or_object(@_);

    return $self->issuedtags->{$tag_name}++ ? 1 : 0;
}

=item C<string($lead, @args)>

TODO: Is this part of the public interface?

=cut

sub string {
    my ($self, $lead, @args) = _global_or_object(@_);

    my $output = '';
    if (@args) {
        my $prefix = '';
        $prefix = "$lead: " if $lead;
        foreach (@args) {
            $output .= "${prefix}${_}\n";
        }
    } elsif ($lead) {
        $output .= $lead.".\n";
    }

    return $output;
}

=back

=head1 INSTANCE METHODS FOR CONTEXT-AWARE OUTPUT

The following methods are designed to be called at specific points
during program execution and require very specific arguments.  They
can only be called as instance methods.

=over 4

=item C<print_tag($pkg_info, $tag_info, $extra, $override)>

Print a tag.  The first two arguments are hash reference with the
information about the package and the tag, $extra is the extra
information for the tag (if any) as an array reference, and $override
is either undef if the tag is not overridden or the
L<override|Lintian::Tag::Override> for this tag.  Called from
Lintian::Tags::tag().

=cut

sub print_tag {
    my ($self, $pkg_info, $tag_info, $information, $override) = @_;
    $information = ' ' . $self->_quote_print($information)
      if $information ne '';
    my $code = $tag_info->code;
    my $tag_color = $self->{colors}{$code};
    my $fpkg_info = $self->_format_pkg_info($pkg_info, $tag_info, $override);
    my $tag_name = $tag_info->tag;
    my $limit = $self->tag_display_limit;
    my $tag;

    # Limit the output so people do not drown in tags.  Some tags are
    # insanely noisy (hi static-library-has-unneeded-section)
    if ($limit) {
        my $proc_id = $pkg_info->{'processable'}->identifier;
        my $emitted_count
          = $self->{'proc_id2tag_count'}{$proc_id}{$tag_name}++;
        return if $emitted_count >= $limit;
        my $msg
          = ' ... use --no-tag-display-limit to see all (or pipe to a file/program)';
        $information = $self->_quote_print($msg)
          if $emitted_count >= $limit-1;
    }
    if ($self->_do_color) {
        if ($self->color eq 'html') {
            my $escaped = $tag_name;
            $escaped =~ s/&/&amp;/g;
            $escaped =~ s/</&lt;/g;
            $escaped =~ s/>/&gt;/g;
            $tag .= qq(<span style="color: $tag_color">$escaped</span>);
        } else {
            $tag .= Term::ANSIColor::colored($tag_name, $tag_color);
        }
    } else {
        $tag .= $tag_name;
    }

    if ($override && @{ $override->comments }) {
        foreach my $c (@{ $override->comments }) {
            $self->msg($self->_quote_print($c));
        }
    }

    $self->_print('', $fpkg_info, "$tag$information");
    if (not $self->issued_tag($tag_info->tag) and $self->showdescription) {
        my $description;
        if ($self->_do_color && $self->color eq 'html') {
            $description = $tag_info->description('html', '   ');
        } else {
            $description = $tag_info->description('text', '   ');
        }
        $self->_print('', 'N', '');
        $self->_print('', 'N', split("\n", $description));
        $self->_print('', 'N', '');
    }
    return;
}

# Helper function to "print_tag" to decide the output format of the tag line.  Used by
# the "FullEWI" subclass.
#
sub _format_pkg_info {
    my ($self, $pkg_info, $tag_info, $override) = @_;
    my $code = $tag_info->code;
    $code = 'X' if $tag_info->experimental;
    $code = 'O' if defined $override;
    my $type = '';
    $type = " $pkg_info->{type}" if $pkg_info->{type} ne 'binary';
    return "$code: $pkg_info->{package}$type";
}

=item C<print_start_pkg($pkg_info)>

Called before lintian starts to handle each package.  The version in
Lintian::Output uses v_msg() for output.  Called from Tags::select_pkg().

=cut

sub print_start_pkg {
    my ($self, $pkg_info) = @_;

    my $object = 'package';
    if ($pkg_info->{type} eq 'changes') {
        $object = 'file';
    }

    $self->v_msg(
        $self->delimiter,
        join(q{ },
            "Processing $pkg_info->{type} $object $pkg_info->{package}",
            "(version $pkg_info->{version}, arch $pkg_info->{arch}) ..."));
    return;
}

=item C<print_start_pkg($pkg_info)>

Called after lintian is finished with a package.  The version in
Lintian::Output does nothing.  Called from Lintian::Tags::file_start() and
Lintian::Tags::file_end().

=cut

sub print_end_pkg {
    return;
}

=back

=head1 INSTANCE METHODS FOR SUBCLASSING

The following methods are only intended for subclassing and are
only available as instance methods.  The methods mentioned in
L</CLASS/INSTANCE METHODS>
usually only check whether they should do anything at all (according
to the values of verbosity_level and debug) and then call one of
the following methods to do the actual printing. Almost all of them
finally call _print() to do that.  This convoluted scheme is necessary
to be able to use the methods above as class methods and still make
the behaviour overridable in subclasses.

=over 4

=item C<_message(@args)>

Called by msg(), v_msg(), and debug_msg() to print the
message.

=cut

sub _message {
    my ($self, @args) = @_;

    $self->_print('', 'N', @args);
    return;
}

=item C<_warning(@args)>

Called by warning() to print the warning.

=cut

sub _warning {
    my ($self, @args) = @_;

    $self->_print($self->stderr, 'warning', @args);
    return;
}

=item C<_print($stream, $lead, @args)>

Called by _message(), _warning(), and print_tag() to do
the actual printing.

If you override these three methods, you can change
the calling convention for this method to pretty much
whatever you want.

The version in Lintian::Output prints the strings in
@args, one per line, each line preceded by $lead to
the I/O handle given in $stream.

=cut

sub _print {
    my ($self, $stream, $lead, @args) = @_;
    $stream ||= $self->stdout;

    my $output = $self->string($lead, @args);
    print {$stream} $output;
    return;
}

=item C<_delimiter()>

Called by delimiter().

=cut

sub _delimiter {
    return '----';
}

=item C<_do_color()>

Called by print_tag() to determine whether to produce colored
output.

=cut

sub _do_color {
    my ($self) = @_;

    return (
             $self->color eq 'always'
          || $self->color eq 'html'
          || ($self->color eq 'auto'
            && -t $self->stdout));
}

=item C<_quote_print($string)>

Called to quote a string.  By default it will replace all
non-printables with "?".  Sub-classes can override it if
they allow non-ascii printables etc.

=cut

sub _quote_print {
    my ($self, $string) = @_;
    $string =~ s/[^[:print:]]/?/go;
    return $string;
}

=back

=head1 CLASS METHODS

=over 4

=item C<_global_or_object(@args)>

If $args[0] is an object which satisfies C<isa('Lintian::Output')>
returns @args, otherwise returns C<($Lintian::Output::GLOBAL, @_)>.

=back

=cut

sub _global_or_object {
    if (ref($_[0]) and $_[0]->isa('Lintian::Output')) {
        return @_;
    } else {
        return ($Lintian::Output::GLOBAL, @_);
    }
}

1;
__END__

=head1 EXPORTS

Lintian::Output exports nothing by default, but the following export
tags are available:

=over 4

=item :messages

Exports all the methods in L</CLASS/INSTANCE METHODS>

=item :util

Exports all the methods in L<CLASS METHODS>

=back

=head1 AUTHOR

Originally written by Frank Lichtenheld <djpig@debian.org> for Lintian.

=head1 SEE ALSO

lintian(1)

=cut

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
