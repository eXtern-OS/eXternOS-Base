#!/usr/bin/env perl

use strict;
use warnings;

use CGI;
use Template;

my $cgi = CGI->new;
my $template_vars;

if ( $cgi->param ) {
	foreach my $var ( qw/ magnification letter x y / ) {
		$template_vars->{$var} = $cgi->param(
			$var =~ /^[xy]$/ ? "picture.$var" : $var
		);
	}
}

my $tt  = Template->new;
print $cgi->header(
    -type    => 'text/html',
    -charset => 'utf-8',
);

$tt->process( \*DATA,$template_vars ) or warn $tt->error;

__DATA__
<!DOCTYPE html>
<html>
	<head>
		<meta charset="UTF-8">
		<title>A Clickable Image</title>
	</head>
	<body>
		<h1>A Clickable Image</h1>
		</a>
		<p>Sorry, this isn't very exciting!</p>
		<form method="post" action="/clickable_image/">
			<input type="image" name="picture" src="/wilogo.gif" />
			<p>Give me a:
			<select name="letter" >[%- FOREACH letter_opt IN [ 'A','B','C','D','E','W' ] %]
				<option value="[% letter_opt %]" [% IF letter == letter_opt %]selected[% END %]>[% letter_opt %]</option>
			[%- END %]</select>
			</p>
			<p>Magnification:
			[% FOREACH magnification_opt IN [ 1,2,4,20 ] -%]
				[%- %]<label><input type="radio" name="magnification" value="[% magnification_opt %]"[%
						IF magnification.defined AND magnification == magnification_opt %] checked="checked"[% END
					%]/>[% magnification_opt %]X</label>
			[% END -%]
			[%- IF x.defined AND y.defined %]
				<p>Selected Position <strong>([% x %],[% y %])</strong></p>
			[% END %]
	</body>
</html>
