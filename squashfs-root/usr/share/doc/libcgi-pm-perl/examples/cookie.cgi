#!/usr/bin/env perl

use strict;
use warnings;

use CGI;
use Template;

my $cgi = CGI->new;

my $template_vars = {
	animals => [
		sort qw/lion tiger bear pig porcupine ferret zebra gnu ostrich
			emu moa goat weasel yak chicken sheep hyena dodo lounge-lizard
			squirrel rat mouse hedgehog racoon baboon kangaroo hippopotamus
			giraffe
		/
	],
};

# Recover the previous animals from the magic cookie.
# The cookie has been formatted as an associative array
# mapping animal name to the number of animals.
my %zoo = $cgi->cookie( 'animals' );

# Recover the new animal(s) from the parameter 'new_animal'
if ( my @new = $cgi->multi_param( 'new_animals' ) ) {

	# If the action is 'add', then add new animals to the zoo.  Otherwise
	# delete them.
	foreach ( @new ) {
		if ( $cgi->param('action') eq 'Add' ) {
			$zoo{$_}++;
		} elsif ( $cgi->param('action') eq 'Delete' ) {
			$zoo{$_}-- if $zoo{$_};
			delete $zoo{$_} unless $zoo{$_};
		}
	}

	$template_vars->{zoo} = \%zoo if keys( %zoo );
}

# Add new animals to old, and put them in a cookie
my $the_cookie = $cgi->cookie(
	-name    => 'animals',
	-value   => \%zoo,
	-expires => '+1h'
);

my $tt  = Template->new;

# Print the header, incorporating the cookie and the expiration date...
print $cgi->header(
	-cookie  => $the_cookie,
    -type    => 'text/html',
    -charset => 'utf-8',
);

$tt->process( \*DATA,$template_vars ) or warn $tt->error;

__DATA__
<!DOCTYPE html>
<html>
	<head>
		<meta charset="UTF-8">
		<title>Animal crackers</title>
	</head>
	<body>
		<h1>Animal Crackers</h1>
		<p>
			Choose the animals you want to add to the zoo, and click "add".
			Come back to this page any time within the next hour and the list of 
			animals in the zoo will be resurrected.  You can even quit the browser
			completely!
		</p>
		<p>
			Try adding the same animal several times to the list.  Does this
			remind you vaguely of a shopping cart?
		</p>
		<p>
			<center>
				<table border>
					<tr><th>Add/Delete<th>Current Contents
					<tr><td><form method="post" action="https://127.0.0.1:3333/cookie/" enctype="multipart/form-data">
						<select name="new_animals"  size="10" multiple="multiple">
						[% FOREACH animal IN animals %]
							<option value="[% animal %]">[% animal %]</option>
						[% END %]
						</select>
					<br>
					<input type="submit" name="action" value="Delete" />
					<input type="submit" name="action" value="Add" />
					<div>
						<input type="hidden" name=".cgifields" value="new_animals"  />
					</div>
				</form>
				<td>
					[% IF zoo.defined %]
						<ul>
						[% FOREACH animal IN zoo.keys.sort %]
							<li>[% zoo.$animal %] [% animal %]</li>
						[% END %]
						</ul>
					[% ELSE %]
						<strong>The zoo is empty.</strong>
					[% END %]
				</table>
			</center>
		<hr>
	</body>
</html>
