# Security related problems
# Author: Marc Deslauriers <marc.deslauriers@ubuntu.com>
# (C) 2010 Canonical Ltd.
# License: GPL v3 or later.

from glob import glob
import subprocess
import apport.hookutils
import time
import os

description = 'Security related problems'

def run(report, ui):
    problem = ui.choice('What particular problem do you observe?',
        ['I can see my password as I type when using ssh and sudo',
         'The root account is disabled by default',
         'I am not prompted for my password when I run sudo a second time',
         'I am not prompted for a password when booting to rescue mode',
         'Other users can access files in my home directory',
         'My screen isn\'t locked when I come out of suspend or hibernate',
         'My screen doesn\'t lock automatically after being idle',
         'Other screen locking issue',
         'Other problem',
        ])

    if problem is None:
        raise StopIteration
    problem = problem[0]

    if problem == 0:
        ui.information('This is expected as there is no "tty" allocated when running commands directly via ssh. Adding the "-t" flag will allocate a tty and prevent sudo from echoing the password.\n\nFor more information, please see:\nhttps://wiki.ubuntu.com/SecurityTeam/FAQ#SSH')
        raise StopIteration
    if problem == 1:
        ui.information('By default, the root account is disabled in Ubuntu and use of the "sudo" command is recommended.\n\nFor more information, please see:\nhttps://help.ubuntu.com/community/RootSudo')
        raise StopIteration
    if problem == 2:
        ui.information('Sudo is designed to keep a "ticket" valid for 15 minutes after you use your password for the first time. This is configurable.\n\nFor more information, please see:\nhttps://wiki.ubuntu.com/SecurityTeam/FAQ#Sudo')
        raise StopIteration
    if problem == 3:
        ui.information('By default, the root account is disabled in Ubuntu and use of the "sudo" command is recommended. Since the root account is disabled, it\'s not possible to prompt for the root password when entering single user mode.\n\nFor more information, please see:\nhttps://wiki.ubuntu.com/SecurityTeam/FAQ#Rescue%20Mode')
        raise StopIteration
    if problem == 4:
        ui.information('By default, Ubuntu is designed to allow users to easily share files and help each other. To support this, each user\'s default home directory is readable by all other users.\n\nFor more information, please see:\nhttps://wiki.ubuntu.com/SecurityTeam/Policies#Permissive%20Home%20Directory%20Access')
        raise StopIteration
    if problem == 5:
        report['Title'] = 'Screen not locked when coming out of suspend/hibernate'
        return 'gnome-screensaver'
    if problem == 6:
        report['Title'] = 'Screen not locked after inactivity'
        return 'gnome-screensaver'
    if problem == 7:
        report['Title'] = 'Screen locking issue'
        return 'gnome-screensaver'
    if problem == 8:
        ui.information('Please use "ubuntu-bug <packagename>" to report a bug against the particular package')
        raise StopIteration

    assert False, 'not reached'

