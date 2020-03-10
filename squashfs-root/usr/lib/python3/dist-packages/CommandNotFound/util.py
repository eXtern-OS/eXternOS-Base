# (c) Zygmunt Krynicki 2008
# Licensed under GPL, see COPYING for the whole text

from __future__ import print_function

import gettext
import sys


if sys.version >= "3":
    _gettext_method = "gettext"
else:
    _gettext_method = "ugettext"
_ = getattr(gettext.translation("command-not-found", fallback=True), _gettext_method)


def crash_guard(callback, bug_report_url, version):
    """ Calls callback and catches all exceptions.
    When something bad happens prints a long error message
    with bug report information and exits the program"""
    try:
        try:
            callback()
        except Exception as ex:
            print(_("Sorry, command-not-found has crashed! Please file a bug report at:"), file=sys.stderr)
            print(bug_report_url, file=sys.stderr)
            print(_("Please include the following information with the report:"), file=sys.stderr)
            print(file=sys.stderr)
            print(_("command-not-found version: %s") % version, file=sys.stderr)
            print(_("Python version: %d.%d.%d %s %d") % sys.version_info, file=sys.stderr)
            try:
                import subprocess
                subprocess.call(["lsb_release", "-i", "-d", "-r", "-c"], stdout=sys.stderr)
            except (ImportError, OSError):
                pass
            print(_("Exception information:"), file=sys.stderr)
            print(file=sys.stderr)
            print(ex, file=sys.stderr)
            try:
                import traceback
                traceback.print_exc()
            except ImportError:
                pass
    finally:
        sys.exit(127)


__all__ = ["crash_guard"]
