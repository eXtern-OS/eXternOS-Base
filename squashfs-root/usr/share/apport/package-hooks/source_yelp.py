from apport.hookutils import *
from os import path
import webbrowser

lp_bug_tracker = "https://answers.launchpad.net"

def add_info(report, ui):
    if report['ProblemType'] == 'Crash':
        return

    response = ui.choice("How would you describe the issue?", ["I'm having problems with the Help Browser.", "I need help performing a Task."], False)
    if response == None:
        raise StopIteration
    if response == [0]: # bug on the documentation or yelp
        return
    # user is requesting help rather than having a bug.
    ui.information("Since you're requesting help rather than having a bug on the application please raise it at the Launchpad Support Tracker: %s. Thanks in advance." % lp_bug_tracker)
    webbrowser.open(lp_bug_tracker)
    raise StopIteration
