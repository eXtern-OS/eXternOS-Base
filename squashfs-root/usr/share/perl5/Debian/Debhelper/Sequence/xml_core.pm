#!/usr/bin/perl

use warnings;
use strict;
use Debian::Debhelper::Dh_Lib;

insert_after('dh_installcatalogs', 'dh_installxmlcatalogs');

1
