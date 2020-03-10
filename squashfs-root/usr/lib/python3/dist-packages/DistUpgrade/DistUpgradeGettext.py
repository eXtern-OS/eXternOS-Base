# DistUpgradeGettext.py - safe wrapper around gettext
#  
#  Copyright (c) 2008 Canonical
#  
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
# 
#  This program is free software; you can redistribute it and/or 
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

import logging
import gettext as mygettext
_gettext_method = "gettext"
_ngettext_method = "ngettext"


def _verify(message, translated):
    """ 
    helper that verifies that the message and the translated 
    message have the same number (and type) of % args
    """
    arguments_in_message = message.count("%") - message.count("\%")
    arguments_in_translation = translated.count("%") - translated.count("\%")
    return arguments_in_message == arguments_in_translation


_translation_singleton = None


def _translation():
    """Return a suitable gettext.*Translations instance."""
    global _translation_singleton
    if _translation_singleton is None:
        domain = mygettext.textdomain()
        _translation_singleton = mygettext.translation(
            domain, mygettext.bindtextdomain(domain), fallback=True)
    return _translation_singleton


def unicode_gettext(translation, message):
    return getattr(translation, _gettext_method)(message)


def unicode_ngettext(translation, singular, plural, n):
    return getattr(translation, _ngettext_method)(singular, plural, n)


def gettext(message):
    """
    version of gettext that logs errors but does not crash on incorrect
    number of arguments
    """
    if message == "":
        return ""
    translated_msg = unicode_gettext(_translation(), message)
    if not _verify(message, translated_msg):
        logging.error(
            "incorrect translation for message '%s' to '%s' "
            "(wrong number of arguments)" % (message, translated_msg))
        return message
    return translated_msg


def ngettext(msgid1, msgid2, n):
    """
    version of ngettext that logs errors but does not crash on incorrect
    number of arguments
    """
    translated_msg = unicode_ngettext(_translation(), msgid1, msgid2, n)
    if not _verify(msgid1, translated_msg):
        logging.error(
            "incorrect translation for ngettext message "
            "'%s' plural: '%s' to '%s' (wrong number of arguments)" % (
                msgid1, msgid2, translated_msg))
        # dumb fallback to not crash
        if n == 1:
            return msgid1
        return msgid2
    return translated_msg
