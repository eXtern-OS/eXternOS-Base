package Text::Levenshtein;
$Text::Levenshtein::VERSION = '0.13';
use 5.006;
use strict;
use warnings;
use Exporter;
use Carp;
use List::Util ();

our @ISA         = qw(Exporter);
our @EXPORT      = ();
our @EXPORT_OK   = qw(distance fastdistance);
our %EXPORT_TAGS = ();


sub distance
{
    my $opt = pop(@_) if @_ > 0 && ref($_[-1]) eq 'HASH';
    croak "distance() takes 2 or more arguments" if @_ < 2;
	my ($s,@t)=@_;
    my @results;

    $opt = {} if not defined $opt;

	foreach my $t (@t) {
		push(@results, fastdistance($s, $t, $opt));
	}

	return wantarray ? @results : $results[0];
}

my $eq_with_diacritics = sub {
    my ($x, $y) = @_;
    return $x eq $y;
};

my $eq_without_diacritics;

# This is the "Iterative with two matrix rows" version
# from the wikipedia page
# http://en.wikipedia.org/wiki/Levenshtein_distance#Computing_Levenshtein_distance
sub fastdistance
{
    my $opt = pop(@_) if @_ > 0 && ref($_[-1]) eq 'HASH';
    croak "fastdistance() takes 2 or 3 arguments" unless @_ == 2;
    my ($s, $t) = @_;
    my (@v0, @v1);
    my ($i, $j);
    my $eq;

    $opt = {} if not defined $opt;
    if ($opt->{ignore_diacritics}) {
        if (not defined $eq_without_diacritics) {
            require Unicode::Collate;
            my $collator = Unicode::Collate->new(normalization => undef, level => 1);
            $eq_without_diacritics = sub {
                return $collator->eq(@_);
            };
        }
        $eq = $eq_without_diacritics;
    }
    else {
        $eq = $eq_with_diacritics;
    }

    return 0 if $s eq $t;
    return length($s) if !$t || length($t) == 0;
    return length($t) if !$s || length($s) == 0;

    my $s_length = length($s);
    my $t_length = length($t);

    for ($i = 0; $i < $t_length + 1; $i++) {
        $v0[$i] = $i;
    }

    for ($i = 0; $i < $s_length; $i++) {
        $v1[0] = $i + 1;

        for ($j = 0; $j < $t_length; $j++) {
            # my $cost = substr($s, $i, 1) eq substr($t, $j, 1) ? 0 : 1;
            my $cost = $eq->(substr($s, $i, 1), substr($t, $j, 1)) ? 0 : 1;
            $v1[$j + 1] = List::Util::min(
                              $v1[$j] + 1,
                              $v0[$j + 1] + 1,
                              $v0[$j] + $cost,
                             );
        }

        for ($j = 0; $j < $t_length + 1; $j++) {
            $v0[$j] = $v1[$j];
        }
    }

    return $v1[ $t_length];
}

1;

__END__

=encoding UTF8

=head1 NAME

Text::Levenshtein - calculate the Levenshtein edit distance between two strings

=head1 SYNOPSIS

 use Text::Levenshtein qw(distance);

 print distance("foo","four");
 # prints "2"

 my @words     = qw/ four foo bar /;
 my @distances = distance("foo",@words);

 print "@distances";
 # prints "2 0 3"

=head1 DESCRIPTION

This module implements the Levenshtein edit distance,
which measures the difference between two strings,
in terms of the I<edit distance>.
This distance is the number of substitutions, deletions or insertions ("edits") 
needed to transform one string into the other one (and vice versa).
When two strings have distance 0, they are the same.

To learn more about the Levenshtein metric,
have a look at the
L<wikipedia page|http://en.wikipedia.org/wiki/Levenshtein_distance>.

=head2 distance()

The simplest usage will take two strings and return the edit distance:

 $distance = distance('brown', 'green');
 # returns 3, as 'r' and 'n' don't change

Instead of a single second string, you can pass a list of strings.
Each string will be compared to the first string passed, and a list
of the edit distances returned:

 @words     = qw/ green trainee brains /;
 @distances = distances('brown', @words);
 # returns (3, 5, 3)

=head2 fastdistance()

Previous versions of this module provided an alternative
implementation, in the function C<fastdistance()>.
This function is still provided, for backwards compatibility,
but they now run the same function to calculate the edit distance.

Unlike C<distance()>, C<fastdistance()> only takes two strings,
and returns the edit distance between them.

=head1 ignore_diacritics

Both the C<distance()> and C<fastdistance()> functions can take
a hashref with optional arguments, as the final argument.
At the moment the only option is C<ignore_diacritics>.
If this is true, then any diacritics are ignored when calculating
edit distance. For example, "cafe" and "café" normally have an edit
distance of 1, but when diacritics are ignored, the distance will be 0:

 use Text::Levenshtein 0.11 qw/ distance /;
 $distance = distance($word1, $word2, {ignore_diacritics => 1});

If you turn on this option, then L<Unicode::Collate> will be loaded,
and used when comparing characters in the words.

Early version of C<Text::Levenshtein> didn't support this version,
so you should require version 0.11 or later, as above.

=head1 SEE ALSO

There are many different modules on CPAN for calculating the edit
distance between two strings. Here's just a selection.

L<Text::LevenshteinXS> and L<Text::Levenshtein::XS> are both versions
of the Levenshtein algorithm that require a C compiler,
but will be a lot faster than this module.

The Damerau-Levenshtein edit distance is like the Levenshtein distance,
but in addition to insertion, deletion and substitution, it also
considers the transposition of two adjacent characters to be a single edit.
The module L<Text::Levenshtein::Damerau> defaults to using a pure perl
implementation, but if you've installed L<Text::Levenshtein::Damerau::XS>
then it will be a lot quicker.

L<Text::WagnerFischer> is an implementation of the
Wagner-Fischer edit distance, which is similar to the Levenshtein,
but applies different weights to each edit type.

L<Text::Brew> is an implementation of the Brew edit distance,
which is another algorithm based on edit weights.

L<Text::Fuzzy> provides a number of operations for partial or fuzzy
matching of text based on edit distance. L<Text::Fuzzy::PP> is a pure
perl implementation of the same interface.

L<String::Similarity> takes two strings and returns a value between
0 (meaning entirely different) and 1 (meaning identical).
Apparently based on edit distance.

L<Text::Dice> calculates
L<Dice's coefficient|https://en.wikipedia.org/wiki/Sørensen–Dice_coefficient>
for two strings. This formula was originally developed to measure the
similarity of two different populations in ecological research.

=head1 REPOSITORY

L<https://github.com/neilbowers/Text-Levenshtein>

=head1 AUTHOR

Dree Mistrut originally wrote this module and released it to CPAN in 2002.

Josh Goldberg then took over maintenance and released versions between
2004 and 2008.

Neil Bowers (NEILB on CPAN) is now maintaining this module.
Version 0.07 was a complete rewrite, based on one of the algorithms
on the wikipedia page.

=head1 COPYRIGHT AND LICENSE

This software is copyright (C) 2002-2004 Dree Mistrut.
Copyright (C) 2004-2014 Josh Goldberg.
Copyright (C) 2014- Neil Bowers.

This is free software; you can redistribute it and/or modify it under
the same terms as the Perl 5 programming language system itself.

=cut
