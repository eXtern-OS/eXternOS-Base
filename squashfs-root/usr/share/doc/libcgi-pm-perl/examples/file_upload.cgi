#!/usr/bin/env perl -T

use strict;
use warnings;

use CGI;
use CGI::Carp qw/ fatalsToBrowser /;
use Template;

my $cgi           = CGI->new;
my $template_vars = {
	cgi_version => $CGI::VERSION,
};

# Process the form if there is a file name entered
if ( my $file = $cgi->param( 'filename' ) ) {

	die "filename passed as ARG" if $file =~ /ARG/;

    my $tmpfile  = $cgi->tmpFileName( $file );
    my $mimetype = $cgi->uploadInfo( $file )->{'Content-Type'} || '';

	@{$template_vars}{qw/file temp_file mimetype/}
		= ( $file,$tmpfile,$mimetype );

	my %wanted = map { $_ => 1 } $cgi->multi_param( 'count' );

    while ( <$file> ) {
		$template_vars->{lines}++               if $wanted{"count lines"};
		$template_vars->{words} += split(/\s+/) if $wanted{"count words"};
		$template_vars->{chars} += length       if $wanted{"count chars"};
    }
    close( $file );
}

print $cgi->header(
    -type    => 'text/html',
    -charset => 'utf-8',
);

my $tt = Template->new;
$tt->process( \*DATA,$template_vars ) or warn $tt->error;

__DATA__
<!DOCTYPE html>
<html>
	<head>
		<meta charset="UTF-8">
		<title>File Upload Example</title>
	</head>
	<body>
		<b>Version</b> [% cgi_version %]
		<h1>File Upload Example</h1>
		<p>This example demonstrates how to prompt the remote user to select a remote file for uploading.</p>
		<p>Select the <cite>browser</cite> button to choose a text file to upload.</p>
		<p>When you press the submit button, this script will count the number of lines, words, and characters in the file.</p>
		<form method="post" action="file_upload" enctype="multipart/form-data">Enter the file to process:
			<input type="file" name="filename" size="45" /><br />
			<label><input type="checkbox" name="count" value="count lines" checked="checked" />count lines</label>
			<label><input type="checkbox" name="count" value="count words" checked="checked" />count words</label>
			<label><input type="checkbox" name="count" value="count chars" checked="checked" />count characters</label>
			<input type="reset"  name=".reset" />
			<input type="submit" name="submit" value="Process File" />
			<input type="hidden" name=".cgifields" value="count"  />
		</form>
		<hr />
		[% IF file.defined %]
			<h2>[% file %]</h2>
			<h3>[% temp_file %]</h3>
			<h4>MIME Type: <i>[% mime_type %]</i></h4>
			<b>Lines: </b>[% lines %]<br />
			<b>Words: </b>[% words %]<br />
			<b>Characters: </b>[% chars %]<br />
		[% END %]
	</body>
</html>
