'''apport package hook for cryptsetup

(c) 2009 Author: Reinhard Tartler <siretart@tauware.de>
(c) 2015 Author: Jonas Meurer <jonas@freesources.org>
'''

from apport.hookutils import *

msg = \
"""

Providing additional information can help diagnose problems with cryptsetup.
Specifically, this would include:
- kernel cmdline (copy of /proc/cmdline).
- crypttab configuration (copy of /etc/crypttab).
- fstab configuration (copy of /etc/fstab).
If this information is not relevant for your bug report or you have privacy
concerns, please choose no.

Do you want to provide additional information?
(you will be able to review the data before it is sent)

"""

def add_info(report, ui):
	attach_files = False

	if ui:
		if ui.yesno(msg) == None:
			# user decided to cancel
			raise StopIteration

		# user is allowing files to be attached.
		attach_files = True

	if attach_files == False:
		# do not attach any files
		return

	attach_file(report, '/proc/cmdline', 'cmdline')
	attach_file(report, '/etc/fstab', 'fstab')
	attach_file_if_exists(report, '/etc/crypttab', 'crypttab')

