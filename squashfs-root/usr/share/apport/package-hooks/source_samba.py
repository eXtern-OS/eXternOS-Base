#!/usr/bin/python

'''Samba Apport interface

Copyright (C) 2010 Canonical Ltd/
Author: Chuck Short <chuck.short@canonical.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.
'''

import os
from subprocess import PIPE, Popen
from apport.hookutils import *

def run_testparm():
	'''
	Run the samba testparm(1) utility against /etc/samba/smb.conf.

	We do not use apport's command_output() method here because:
	- we need to discard stdout, as that includes smb.conf
	- we want to know if its exit status is not zero, but that in itself
	  is not an error in the test itself. command_output() would say the
	  command failed and that would be confusing.

	Returns stderr and the exit code (as a string) of testparm as a tuple or
	None in the case of an error.
	'''
	command = ['testparm', '-s', '/etc/samba/smb.conf']
	try:
		testparm = Popen(command, stdout=PIPE, stderr=PIPE)
	except OSError:
		return None
	_, err = testparm.communicate()
	exit_code = testparm.wait()
	return (err, str(exit_code))


def recent_smblog(pattern):
	'''Extract recent messages from log.smbd or messages which match a regex
	   pattern should be a "re" object. '''
	lines = ''
	if os.path.exists('/var/log/samba/log.smbd'):
		file = '/var/log/samba/log.smbd'
	else:
		return lines

	for line in open(file):
		if pattern.search(line):
			lines += line
	return lines

def recent_nmbdlog(pattern):
	''' Extract recent messages from log.nmbd or messages which match regex
	    pattern should be a "re" object. '''
	lines = ''
	if os.path.exists('/var/log/samba/log.nmbd'):
		file = '/var/log/samba/log.nmbd'
	else:
		return lines

	for line in open(file):
		if pattern.search(line):
			lines += line
	return lines

def add_info(report, ui):
	packages = ['samba', 'samba-common-bin', 'samba-common', 'samba-tools', 'smbclient', 'swat',
		'samba-doc', 'samba-doc-pdf', 'smbfs', 'libpam-smbpass', 'libsmbclient', 'libsmbclient-dev',
		'winbind', 'samba-dbg', 'libwbclient0']

	versions = ''
	for package in packages:
		try:
			version = packaging.get_version(package)
		except ValueError:
			version = 'N/A'
		if version is None:
			version = 'N/A'
		versions += '%s %s\n' %(package, version)
	report['SambaInstalledVersions'] = versions


	# Interactive report
	# start by checking if /etc/samba/smb.conf exists
	if not os.path.exists ('/etc/samba/smb.conf'):
		ui.information("The configuration file '/etc/samba/smb.conf' does not exist. This file, and its contents, are critical for the operation of the SAMBA package(s). A common situation for this is:\n  * you removed (but did not purge) SAMBA;\n  * later on, you (or somebody) manually deleted '/etc/samba/smb.conf;\n  * you reinstalled SAMBA.\nAs a result, this file is *not* reinstalled. If this is your case, please purge samba-common (e.g., sudo apt-get purge samba-common) and then reinstall SAMBA.\nYou may want to check other sources, like: https://answers.launchpad.net, https://help.ubuntu.com, and http://ubuntuforums.org. Please press any key to end apport's bug collection.")
		raise StopIteration # we are out

	ui.information("As a part of the bug reporting process, you'll be asked as series of questions to help provide a more descriptive bug report. Please answer the following questions to the best of your abilities. Afterwards, a browser will be opened to finish filing this as a bug in the Launchpad bug tracking system.")

	response = ui.choice("How would you best describe your setup?", ["I am running a Windows File Server.", "I am connecting to a Windows File Server."], False)
	
	if response == None:
		raise StopIteration # user has canceled
	elif response[0] == 0: #its a server
		response = ui.yesno("Did this used to work properly with a previous release?")
		if response == None: # user has canceled
			raise StopIteration
		if response == False:
			report['SambaServerRegression'] = "No"
		if response == True:
			report['SambaServerRegression'] = 'Yes'
	
		response = ui.choice("Which clients are failing to connect?", ["Windows", "Ubuntu", "Both", "Other"], False)
		if response == None:
			raise StopIteration # user has canceled
		if response[0] == 0:
			report['UbuntuFailedConnect'] = 'Yes'
		if response[0] == 1:
			report['WindowsFailedConnect'] = 'Yes'
		if response[0] == 2:
			report['BothFailedConnect']  = 'Yes'
		if response[0] == 3:
			report['OtherFailedConnect'] = 'Yes'

		response = ui.yesno("The contents of your /etc/samba/smb.conf file may help developers diagnose your bug more quickly. However, it may contain sensitive information.  Do you want to include it in your bug report?")
		if response == None:
			raise StopIteration
		if response == False:
			report['SmbConfIncluded'] = 'No'
		if response == True:
			report['SmbConfIncluded'] = 'Yes'
			attach_file_if_exists(report, '/etc/samba/smb.conf', key='SMBConf')
		if command_available('testparm') and os.path.exists('/etc/samba/smb.conf'):
			testparm_result = run_testparm()
			testparm_response = ui.yesno("testparm(1) is a samba utility that will check /etc/samba/smb.conf for correctness and report issues it may find.  Do you want to include its stderr output in your bug report? If you answer no, then we will only include its numeric exit status.")
			if testparm_response == None:
				raise StopIteration
			if testparm_response == True:
				if testparm_result:
					report['TestparmStderr'], report['TestparmExitCode'] = testparm_result
			else: # only include the exit code
				report['TestparmExitCode'] = testparm_result[1]

		response = ui.yesno("The contents of your /var/log/samba/log.smbd and /var/log/samba/log.nmbd may help developers diagnose your bug more quickly. However, it may contain sensitive information. Do you want to include it in your bug report?")
		if response == None:
			raise StopIteration
		elif response == False:
			ui.information("The contents of your /var/log/samba/log.smbd and /var/log/samba/log.nmbd will NOT be included in the bug report.")
		elif response == True:
			sec_re = re.compile('failed', re.IGNORECASE)
			report['SmbLog'] = recent_smblog(sec_re)
			report['NmbdLog'] = recent_nmbdlog(sec_re)

	elif response[0] == 1: #its a client
		response = ui.yesno("Did this used to work properly with a previous release?")
		if response == None: #user has canceled
			raise StopIteration
		if response == False:
			report['SambaClientRegression'] = "No"
		if response == True:
			report['SambaClientRegression'] = "Yes"

		response = ui.choice("How is the remote share accessed from the Ubuntu system?", ["Nautilus (or other GUI Client)", "smbclient (from the command line)", "cifs filesystem mount (from /etc/fstab or a mount command)"], False)
		if response == None: #user has canceled
			raise StopIteration
		if response[0] == 0:
			attach_related_packages(report, ['nautilus', 'gvfs'])
		if response[0] == 1:
			ui.information("Please attach the output of 'smbclient -L localhost' to the end of this bug report.")
		if response[0] == 2:
			report['CIFSMounts'] = command_output(['findmnt', '-n', '-t', 'cifs'])
			if os.path.exists('/proc/fs/cifs/DebugData'):
				report['CifsVersion'] = command_output(['cat', '/proc/fs/cifs/DebugData'])

	ui.information("After apport finishes collecting information, please document your steps to reproduce the issue when filling out the bug report.")
