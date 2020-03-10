#
# Configuration file for the oops.kernel.org kernel crash collector
#

#
# Set the following variable to "yes" if you want to automatically
# submit your oopses to the database for use by your distribution or the
# Linux kernel developers
#
#
# PRIVACY NOTE
# Enabling this option will cause your system to submit certain kernel
# output to the oops.kernel.org website, where it will be available via
# this website to developers and everyone else.
# The submitted info are so-called "oopses", kernel crash signature.
# However, due to the nature of oopses, it may happen that a few 
# surrounding lines of the oops in the "dmesg" are being sent together
# with the oops.
#
# Default is "ask" which uses a UI application t ask the user for permission
#
allow-submit = ask

#
# Set the following variable to "yes" if you want to allow your 
# Linux distribution vendor to pass the oops on to the central oops.kernel.org
# database as used by the Linux kernel developers
#
allow-pass-on = yes

#
# URL for submitting the oopses
#

submit-url = http://oops.kernel.org/submitoops.php

#
# Path to syslog file containing full kernel logging output
#

log-file = /var/log/kern.log

#
# Script or program to pipe oops submits to
# Comment out for no pipe submission
#

submit-pipe = /usr/share/apport/kernel_oops
