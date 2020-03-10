'''applications.py: common classes for ufw'''
#
# Copyright 2008-2018 Canonical Ltd.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3,
#    as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import re
import stat
import ufw.util
from ufw.util import debug, warn
from ufw.common import UFWError

import sys
if sys.version_info[0] < 3:  # pragma: no cover
    import ConfigParser
else:  # pragma: no cover
    import configparser


def get_profiles(profiles_dir):
    '''Get profiles found in profiles database.  Returns dictionary with
       profile name as key and tuples for fields
    '''
    if not os.path.isdir(profiles_dir):
        err_msg = _("Profiles directory does not exist")
        raise UFWError(err_msg)

    max_size = 10 * 1024 * 1024  # 10MB
    profiles = {}

    files = os.listdir(profiles_dir)
    files.sort()

    total_size = 0
    pat = re.compile(r'^\.')
    for f in files:
        abs_path = profiles_dir + "/" + f
        if not os.path.isfile(abs_path):
            continue

        if pat.search(f):
            debug("Skipping '%s': hidden file" % (f))
            continue

        if f.endswith('.dpkg-new') or f.endswith('.dpkg-old') or \
           f.endswith('.dpkg-dist') or f.endswith('.rpmnew') or \
           f.endswith('.rpmsave') or f.endswith('~'):
            debug("Skipping '%s'" % (f))
            continue

        # Try to gracefully handle huge files for the user (no security
        # benefit, just usability)
        size = 0
        try:
            size = os.stat(abs_path)[stat.ST_SIZE]
        except Exception:
            warn_msg = _("Skipping '%s': couldn't stat") % (f)
            warn(warn_msg)
            continue

        if size > max_size:
            warn_msg = _("Skipping '%s': too big") % (f)
            warn(warn_msg)
            continue

        if total_size + size > max_size:
            warn_msg = _("Skipping '%s': too many files read already") % (f)
            warn(warn_msg)
            continue

        total_size += size

        if sys.version_info[0] < 3:  # pragma: no cover
            cdict = ConfigParser.RawConfigParser()
        else:  # pragma: no cover
            cdict = configparser.RawConfigParser()

        try:
            cdict.read(abs_path)
        except Exception:
            warn_msg = _("Skipping '%s': couldn't process") % (f)
            warn(warn_msg)
            continue

        # If multiple occurences of profile name, use the last one
        for p in cdict.sections():
            if len(p) > 64:
                warn_msg = _("Skipping '%s': name too long") % (p)
                warn(warn_msg)
                continue

            if not valid_profile_name(p):
                warn_msg = _("Skipping '%s': invalid name") % (p)
                warn(warn_msg)
                continue

            try:
                ufw.util.get_services_proto(p)
                warn_msg = _("Skipping '%s': also in /etc/services") % (p)
                warn(warn_msg)
                continue
            except Exception:
                pass

            skip = False
            for key, value in cdict.items(p):
                if len(key) > 64:
                    warn_msg = _("Skipping '%s': field too long") % (p)
                    warn(warn_msg)
                    skip = True
                    break
                if len(value) > 1024:
                    warn_msg = _("Skipping '%(value)s': value too long for " \
                                 "'%(field)s'") % \
                                 ({'value': p, 'field': key})
                    warn(warn_msg)
                    skip = True
                    break
            if skip:
                continue

            if p in profiles:
                warn_msg = _("Duplicate profile '%s', using last found") % (p)
                warn(warn_msg)

            pdict = {}
            for key, value in cdict.items(p):
                #debug("add '%s' = '%s' to '%s'" % (key, value, p))
                pdict[key] = value

            try:
                verify_profile(p, pdict)
                profiles[p] = pdict
            except UFWError as e:
                warn(e)

    return profiles


def valid_profile_name(name):
    '''Only accept a limited set of characters for name'''
    # Reserved profile name
    if name == "all":
        return False

    # Don't allow integers (ports)
    try:
        int(name)
        return False
    except Exception:
        pass

    # Require first character be alpha, so we can avoid collisions with port
    # numbers.
    if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9 _\-\.+]*$', name):
        return True
    return False


def verify_profile(name, profile):
    '''Make sure profile has everything needed'''
    app_fields = ['title', 'description', 'ports']

    for f in app_fields:
        if f not in profile:
            err_msg = _("Profile '%(fn)s' missing required field '%(f)s'") % \
                        ({'fn': name, 'f': f})

            raise UFWError(err_msg)
        elif not profile[f]:
            err_msg = _("Profile '%(fn)s' has empty required field '%(f)s'") \
                        % ({'fn': name, 'f': f})
            raise UFWError(err_msg)

    ports = profile['ports'].split('|')
    try:
        for p in ports:
            (port, proto) = ufw.util.parse_port_proto(p)
            # quick checks if error in profile
            if proto == "any" and (':' in port or ',' in port):
                raise UFWError(err_msg)
            rule = ufw.common.UFWRule("ACCEPT", proto, port)
            debug(rule)
    except Exception as e:
        debug(e)
        err_msg = _("Invalid ports in profile '%s'") % (name)
        raise UFWError(err_msg)

    return True


def get_title(profile):
    '''Retrieve the title from the profile'''
    s = ""
    field = 'title'
    if field in profile and profile[field]:
        s = profile[field]
    return s


def get_description(profile):
    '''Retrieve the description from the profile'''
    s = ""
    field = 'description'
    if field in profile and profile[field]:
        s = profile[field]
    return s


def get_ports(profile):
    '''Retrieve a list of ports from a profile'''
    ports = []
    field = 'ports'
    if field in profile and profile[field]:
        ports = profile[field].split('|')

    return ports
