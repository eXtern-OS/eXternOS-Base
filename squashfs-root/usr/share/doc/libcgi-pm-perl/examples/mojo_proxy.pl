#!/usr/bin/env perl

use Mojolicious::Lite;
use Mojolicious::Plugin::CGI;

my %cgi_scripts = (
	'/clickable_image' => "clickable_image.cgi",
	'/cookie'          => "cookie.cgi",
	'/crash'           => "crash.cgi",
	'/file_upload'     => "file_upload.cgi",
	'/wikipedia_ex'    => "wikipedia_example.cgi",
);

foreach my $route ( sort keys( %cgi_scripts ) ) {
	plugin CGI => [ $route => $cgi_scripts{$route} ];
}

any '/' => sub {
	my ( $c ) = @_;
	$c->stash( { cgi_scripts => { %cgi_scripts } } );
	$c->render( 'index' );
};

app->start;

__DATA__
@@ index.html.ep
<!doctype html><html>
	<head><title>CGI Examples</title></head>
	<body>
		<h3>CGI Examples</h3>
		% for my $route ( sort keys( %{ $cgi_scripts } ) ) {
			<a href="<%= $route %>"><%= $cgi_scripts->{$route} %></a><br />
		% }
	</body>
</html>
