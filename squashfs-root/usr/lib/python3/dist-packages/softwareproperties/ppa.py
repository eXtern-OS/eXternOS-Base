#  software-properties PPA support
#
#  Copyright (c) 2004-2009 Canonical Ltd.
#
#  Author: Michael Vogt <mvo@debian.org>
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

from __future__ import print_function

import apt_pkg
import json
import os
import re
import shutil
import subprocess
import tempfile

from gettext import gettext as _
from threading import Thread

from softwareproperties.shortcuts import ShortcutException

try:
    import urllib.request
    from urllib.error import HTTPError, URLError
    import urllib.parse
    from http.client import HTTPException
    NEED_PYCURL = False
except ImportError:
    NEED_PYCURL = True
    import pycurl
    HTTPError = pycurl.error


SKS_KEYSERVER = 'https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&exact=on&search=0x%s'
# maintained until 2015
LAUNCHPAD_PPA_API = 'https://launchpad.net/api/1.0/%s/+archive/%s'
LAUNCHPAD_USER_API = 'https://launchpad.net/api/1.0/%s'
LAUNCHPAD_USER_PPAS_API = 'https://launchpad.net/api/1.0/%s/ppas'
LAUNCHPAD_DISTRIBUTION_API = 'https://launchpad.net/api/1.0/%s'
LAUNCHPAD_DISTRIBUTION_SERIES_API = 'https://launchpad.net/api/1.0/%s/%s'
# Specify to use the system default SSL store; change to a different path
# to test with custom certificates.
LAUNCHPAD_PPA_CERT = "/etc/ssl/certs/ca-certificates.crt"


class CurlCallback:
    def __init__(self):
        self.contents = ''

    def body_callback(self, buf):
        self.contents = self.contents + buf


class PPAException(Exception):

    def __init__(self, value, original_error=None):
        self.value = value
        self.original_error = original_error

    def __str__(self):
        return repr(self.value)


def encode(s):
    return re.sub("[^a-zA-Z0-9_-]", "_", s)

def get_info_from_https(url, accept_json):
    if NEED_PYCURL:
        # python2 has no cert verification so we need pycurl
        data = _get_https_content_pycurl(url, accept_json)
    else:
        # python3 has cert verification so we can use the buildin urllib
        data = _get_https_content_py3(url, accept_json)
    if accept_json:
        return json.loads(data)
    else:
        return data

def get_info_from_lp(lp_url):
    return get_info_from_https(lp_url, True)

def get_ppa_info_from_lp(owner_name, ppa):
    if owner_name[0] != '~':
        owner_name = '~' + owner_name
    lp_url = LAUNCHPAD_PPA_API % (owner_name, ppa)
    return get_info_from_lp(lp_url)

def series_valid_for_distro(distribution, series):
    lp_url = LAUNCHPAD_DISTRIBUTION_SERIES_API % (distribution, series)
    try:
        get_info_from_lp(lp_url)
        return True
    except PPAException:
        return False

def get_current_series_from_lp(distribution):
    lp_url = LAUNCHPAD_DISTRIBUTION_API % distribution
    return os.path.basename(get_info_from_lp(lp_url)["current_series_link"])


def _get_https_content_py3(lp_url, accept_json):
    try:
        headers = {"Accept":" application/json"} if accept_json else {}
        request = urllib.request.Request(str(lp_url), headers=headers)
        lp_page = urllib.request.urlopen(request, cafile=LAUNCHPAD_PPA_CERT)
        data = lp_page.read().decode("utf-8", "strict")
    except (URLError, HTTPException) as e:
        # HTTPException doesn't have a reason but might have a string
        # representation
        reason = hasattr(e, "reason") and e.reason or e
        raise PPAException("Error reading %s: %s" % (lp_url, reason), e)
    return data

def _get_https_content_pycurl(lp_url, accept_json):
    # this is the fallback code for python2
    try:
        callback = CurlCallback()
        curl = pycurl.Curl()
        curl.setopt(pycurl.SSL_VERIFYPEER, 1)
        curl.setopt(pycurl.SSL_VERIFYHOST, 2)
        curl.setopt(pycurl.WRITEFUNCTION, callback.body_callback)
        if LAUNCHPAD_PPA_CERT:
            curl.setopt(pycurl.CAINFO, LAUNCHPAD_PPA_CERT)
        curl.setopt(pycurl.URL, str(lp_url))
        if accept_json:
            curl.setopt(pycurl.HTTPHEADER, ["Accept: application/json"])
        curl.perform()
        response = curl.getinfo(curl.RESPONSE_CODE)
        curl.close()
        data = callback.contents
    except pycurl.error as e:
        raise PPAException("Error reading %s: %s" % (lp_url, e), e)
    if response != 200:
        raise PPAException("Error reading %s: response code %i" % (lp_url, response))
    return data


def mangle_ppa_shortcut(shortcut):
    ppa_shortcut = shortcut.split(":")[1]
    if ppa_shortcut.startswith("/"):
        ppa_shortcut = ppa_shortcut.lstrip("/")
    user = ppa_shortcut.split("/")[0]
    if (user[0] == "~"):
        user = user[1:]
    ppa_path_objs = ppa_shortcut.split("/")[1:]
    ppa_path = []
    if (len(ppa_path_objs) < 1):
        ppa_path = ['ubuntu', 'ppa']
    elif (len(ppa_path_objs) == 1):
        ppa_path.insert(0, "ubuntu")
        ppa_path.extend(ppa_path_objs)
    else:
        ppa_path = ppa_path_objs
    ppa = "~%s/%s" % (user, "/".join(ppa_path))
    return ppa

def verify_keyid_is_v4(signing_key_fingerprint):
    """Verify that the keyid is a v4 fingerprint with at least 160bit"""
    return len(signing_key_fingerprint) >= 160/8


class AddPPASigningKey(object):
    " thread class for adding the signing key in the background "

    def __init__(self, ppa_path, keyserver=None):
        self.ppa_path = ppa_path
        self._homedir = tempfile.mkdtemp()

    def __del__(self):
        shutil.rmtree(self._homedir)

    def gpg_cmd(self, args):
        cmd = "gpg -q --homedir %s --no-default-keyring --no-options --import --import-options %s" % (self._homedir, args)
        return subprocess.Popen(cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        
    def _recv_key(self, signing_key_fingerprint):
        try:
            # double check that the signing key is a v4 fingerprint (160bit)
            if not verify_keyid_is_v4(signing_key_fingerprint):
                print("Error: signing key fingerprint '%s' too short" %
                    signing_key_fingerprint)
                return False
        except TypeError:
            print("Error: signing key fingerprint does not exist")
            return False

        return get_info_from_https(SKS_KEYSERVER % signing_key_fingerprint, accept_json=False)

    def _minimize_key(self, key):
        p = self.gpg_cmd("import-minimal,import-export")
        (minimal_key, _) = p.communicate(key.encode())
        
        if p.returncode != 0:
            return False
        return minimal_key

    def _get_fingerprints(self, key):
        fingerprints = []
        p = self.gpg_cmd("show-only --fingerprint --batch --with-colons")
        (output, _) = p.communicate(key)
        if p.returncode == 0:
            for line in output.decode('utf-8').splitlines():
                if line.startswith("fpr:"):
                    fingerprints.append(line.split(":")[9])
        return fingerprints

    def _verify_fingerprint(self, key, expected_fingerprint):
        got_fingerprints = self._get_fingerprints(key)
        if len(got_fingerprints) != 1:
            print("Got '%s' fingerprints, expected only one" %
                  len(got_fingerprints))
            return False
        got_fingerprint = got_fingerprints[0]
        if got_fingerprint != expected_fingerprint:
            print("Fingerprints do not match, not importing: '%s' != '%s'" % (
                    expected_fingerprint, got_fingerprint))
            return False
        return True

    def add_ppa_signing_key(self, ppa_path=None):
        """Query and add the corresponding PPA signing key.

        The signing key fingerprint is obtained from the Launchpad PPA page,
        via a secure channel, so it can be trusted.
        """
        if ppa_path is None:
            ppa_path = self.ppa_path

        try:
            ppa_info = get_ppa_info(ppa_path)
        except PPAException as e:
            print(e.value)
            return False
        try:
            signing_key_fingerprint = ppa_info["signing_key_fingerprint"]
        except IndexError as e:
            print("Error: can't find signing_key_fingerprint at %s" % ppa_path)
            return False
        
        #  download the armored_key
        armored_key = self._recv_key(signing_key_fingerprint)
        if not armored_key:
            return False

        trustedgpgd = apt_pkg.config.find_dir("Dir::Etc::trustedparts")
        apt_keyring = os.path.join(trustedgpgd, encode(ppa_info["reference"][1:]))

        minimal_key = self._minimize_key(armored_key)
        if not minimal_key:
            return False
        
        if not self._verify_fingerprint(minimal_key, signing_key_fingerprint):
            return False

        with open('%s.gpg' % apt_keyring, 'wb') as f:
            f.write(minimal_key)

        return True


class AddPPASigningKeyThread(Thread, AddPPASigningKey):
    # This class is legacy.  There are no users inside the software-properties
    # codebase other than a test case.  It was left in case there were outside
    # users.  Internally, we've changed from having a class implement the
    # tread to explicitly launching a thread and invoking a method in it
    # see check_and_add_key_for_whitelisted_shortcut for how.
    def __init__(self, ppa_path, keyserver=None):
        Thread.__init__(self)
        AddPPASigningKey.__init__(self, ppa_path=ppa_path, keyserver=keyserver)

    def run(self):
        self.add_ppa_signing_key(self.ppa_path)


def _get_suggested_ppa_message(user, ppa_name):
    try:
        msg = []
        try:
            try:
                lp_user = get_info_from_lp(LAUNCHPAD_USER_API % user)
            except PPAException:
                return _("ERROR: '{user}' user or team does not exist.").format(user=user)
            lp_ppas = get_info_from_lp(LAUNCHPAD_USER_PPAS_API % user)
            entity_name = _("team") if lp_user["is_team"] else _("user")
            if lp_ppas["total_size"] > 0:
                # Translators: %(entity)s is either "team" or "user"
                msg.append(_("The %(entity)s named '%(user)s' has no PPA named '%(ppa)s'") % {
                        'entity' : entity_name,
                         'user' : user,
                         'ppa' : ppa_name})
                msg.append(_("Please choose from the following available PPAs:"))
                for ppa in lp_ppas["entries"]:
                    msg.append(_(" * '%(name)s':  %(displayname)s") % {
                                 'name' : ppa["name"],
                                 'displayname' : ppa["displayname"]})
            else:
                # Translators: %(entity)s is either "team" or "user"
                msg.append(_("The %(entity)s named '%(user)s' does not have any PPA") % {
                             'entity' : entity_name, 'user' : user})
            return '\n'.join(msg)
        except KeyError:
            return ''
    except ImportError:
        return _("Please check that the PPA name or format is correct.")


def get_ppa_info(shortcut):
    user = shortcut.split("/")[0]
    ppa = "/".join(shortcut.split("/")[1:])
    try:
        ret = get_ppa_info_from_lp(user, ppa)
        ret["distribution"] = ret["distribution_link"].split('/')[-1]
        ret["owner"] = ret["owner_link"].split('/')[-1]
        return ret
    except (HTTPError, Exception):
        msg = []
        msg.append(_("Cannot add PPA: 'ppa:%s/%s'.") % (
            user, ppa))

        # If the PPA does not exist, then try to find if the user/team
        # exists. If it exists, list down the PPAs
        raise ShortcutException('\n'.join(msg) + "\n" +
                                _get_suggested_ppa_message(user, ppa))

    except (ValueError, PPAException):
        raise ShortcutException(
            _("Cannot access PPA (%s) to get PPA information, "
              "please check your internet connection.") % \
              (LAUNCHPAD_PPA_API % (user, ppa)))


class PPAShortcutHandler(object):
    def __init__(self, shortcut):
        super(PPAShortcutHandler, self).__init__()
        try:
            self.shortcut = mangle_ppa_shortcut(shortcut)
        except:
            raise ShortcutException(_("ERROR: '{shortcut}' is not a valid ppa format")
                                      .format(shortcut=shortcut))
        info = get_ppa_info(self.shortcut)

        if "private" in info and info["private"]:
            raise ShortcutException(
                _("Adding private PPAs is not supported currently"))

        self._info = info

    def info(self):
        return self._info

    def expand(self, codename, distro=None):
        if (distro is not None
                and distro != self._info["distribution"]
                and not series_valid_for_distro(self._info["distribution"], codename)):
            # The requested PPA is for a foreign distribution.  Guess that
            # the user wants that distribution's current series.
            # This only applies if the local distribution is not the same
            # distribution the remote PPA is associated with AND the local
            # codename is not equal to the PPA's series.
            # e.g. local:Foobar/xenial and ppa:Ubuntu/xenial will use 'xenial'
            #      local:Foobar/fluffy and ppa:Ubuntu/xenial will use '$latest'
            codename = get_current_series_from_lp(self._info["distribution"])
        debline = "deb http://ppa.launchpad.net/%s/%s/%s %s main" % (
            self._info["owner"][1:], self._info["name"],
            self._info["distribution"], codename)
        sourceslistd = apt_pkg.config.find_dir("Dir::Etc::sourceparts")
        filename = os.path.join(sourceslistd, "%s-%s-%s-%s.list" % (
            encode(self._info["owner"][1:]), encode(self._info["distribution"]),
            encode(self._info["name"]), codename))
        return (debline, filename)

    def should_confirm(self):
        return True

    def add_key(self, keyserver=None):
        apsk = AddPPASigningKey(self._info["reference"], keyserver=keyserver)
        return apsk.add_ppa_signing_key()


def shortcut_handler(shortcut):
    if not shortcut.startswith("ppa:"):
        return None
    return PPAShortcutHandler(shortcut)


if __name__ == "__main__":
    import sys
    ppa = sys.argv[1].split(":")[1]
    print(get_ppa_info(ppa))
