# Display (X.org) related problems
# Author: Bryce Harrington <bryce@canonical.com>
# (C) 2009 Canonical Ltd.
# License: GPL v2 or later.

from glob import glob
import subprocess
import apport.hookutils
import time
import os

description = 'Display (X.org)'

def problem_boot_fail(report, ui):
    prompt = "What type of boot failure do you experience?"
    problems = [
        {'desc':"Go back", 'package':None},
        {'desc':"Black or blank screen",
         'tags':'blank',
         'info':"See http://wiki.ubuntu.com/X/Troubleshooting/BlankScreen for help working around and debugging blank screen on boot issues.",
         'package':report['VideoDriver']},
        {'desc':"White screen after logging in",
         'info':"White screens generally indicate a failure initializing Compiz or kwin; thus, as a workaround try disabiling Desktop Effects",
         'package':'mesa'},
        {'desc':"Solid brown or other color",
         'tags':'freeze',
         'package':report['VideoDriver']},
        {'desc':"Garbage or corruption on screen",
         'tags':'freeze corruption',
         'info':"If possible, please also take a photo of the screen and attach to the bug report.  Sometimes the style of corruption can give clues as to where in memory the error has occurred.",
         'package':report['VideoDriver']},
        ]

    choice = []
    for item in problems:
        choices.append(item['desc'])
                        
    choice = ui.choice(prompt, choices)[0]
    if choice is None:
        raise StopIteration

    return problem[choice]['package']


def run(report, ui):
    prompt = 'What display problem do you observe?'
    choice = ui.choice(prompt,
        ['I don\'t know',
         'Freezes or hangs during boot or usage',
         'Crashes or restarts back to login screen',
         'Resolution is incorrect',
         'Shows screen corruption',
         'Performance is worse than expected',
         'Fonts are the wrong size',
         'Other display-related problem',
        ])

    if choice is None or choice == [0]:
        raise StopIteration
    choice = choice[0]

    report.setdefault('Tags', '')

    # Tag kubuntu bugs
    if subprocess.call(['pgrep', '-u', str(os.getuid()), '-x', 'ksmserver']) == 0:
        report['Tags'] += ' kubuntu'

    # Process problems
    if choice == 1:
        ui.information('To debug X freezes, please see https://wiki.ubuntu.com/X/Troubleshooting/Freeze')
        report['Tags'] += ' freeze'
        report['Title'] = 'Xorg freeze'
        return 'xorg'
    if choice == 2:
        ui.information('Please reproduce the crash and collect a backtrace.  See https://wiki.ubuntu.com/X/Backtracing for directions.')
        report['Tags'] += ' crash'
        report['Title'] = 'Xorg crash'
        # TODO:  Look in /var/crash and let user select a crash file, and then parse it
        return 'xorg'
    if choice == 3:
        report['Tags'] += ' resolution'
        return 'xorg'
    if choice == 4:
        ui.information('Please take a photo of the screen showing the corruption and attach to the bug report')
        report['Tags'] += ' corruption'
        # TODO:  Let user upload the file
        return 'xorg'
    if choice == 5:
        report['Tags'] += ' performance'
        return 'xorg'
    if choice == 6:
        report['Tags'] += ' fonts'
        return 'xorg'
    if choice == 7:
        return 'xorg'

    ui.information('Please run "ubuntu-bug <packagename>" to report this bug')
    return None

