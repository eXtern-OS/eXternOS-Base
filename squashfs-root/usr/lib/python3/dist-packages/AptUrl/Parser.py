# Copyright (c) 2007-2008 Canonical
#
# AUTHOR:
# Michael Vogt <mvo@ubuntu.com>
# With contributions by Siegfried-A. Gevatter <rainct@ubuntu.com>
#
# This file is part of AptUrl
#
# AptUrl is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# AptUrl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with AptUrl; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import string
from string import Template
from .Helpers import get_dist
from .Helpers import _

class InvalidUrlException(Exception):
    def __init__(self, url, msg=""):
        self.url = url
        self.message = msg
    def __str__(self):
        return self.message

MAX_URL_LEN=255

# substituion mapping
apturl_substitution_mapping = {
    "distro" : get_dist(),
    "kernel" : os.uname()[2] 
}

# whitelist for the uri
whitelist = []
whitelist.extend(string.ascii_letters)
whitelist.extend(string.digits)
whitelist.extend(['_',':','?','/','+','.','~','=','<','>','-',',','$','&'])


class AptUrl(object):
    " a class that contains the parsed data from an apt url "
    def __init__(self):
        self.package = None
        self.schema = None
        self.minver = None
        self.refresh = None
        # for added repos
        self.keyfile = None
        self.repo_url = None
        self.dist = '/'     
        # for known sections 
        self.section = []
        # for known channels
        self.channel = None

def is_format_package_name(string):
    " return True if string would be an acceptable name for a Debian package "
    
    return (string.replace("+", "").replace("-", "").replace(".", "").replace(":", "").isalnum() 
        and string.islower() and string[0].isalnum() and len(string) > 1)

def do_apt_url_substitution(apt_url, mapping):
    " substitute known templates against the field package and channel "
    for field in ["package","channel"]:
        if getattr(apt_url, field):
            s=Template(getattr(apt_url, field))
            setattr(apt_url, field, s.substitute(mapping))

def match_against_whitelist(raw_url):
    " test if the url matches the internal whitelist "
    for char in raw_url:
        if not char in whitelist:
            raise InvalidUrlException(
                raw_url, _("Non whitelist char in the uri"))
    return True

def set_value(apt_url, s):
    " set a key,value pair from string s to AptUrl object "
    (key, value) = s.split("=")
    try:
        if ' ' in value:
            raise InvalidUrlException(apt_url, _("Whitespace in key=value"))
        if type(getattr(apt_url, key)) == type([]):
            getattr(apt_url, key).append(value)
        else:
            setattr(apt_url, key, value)
    except Exception as e:
        raise InvalidUrlException(apt_url, _("Exception '%s'") % e)


def parse(full_url, mapping=apturl_substitution_mapping):
    " parse an apt url and return a list of AptUrl objects "
    # apt:pkg1?k11=v11?k12=v12,pkg2?k21=v21?k22=v22,...
    res = []
    
    if len(full_url) > MAX_URL_LEN:
        url = "%s ..." % full_url[0:(MAX_URL_LEN // 10)]
        raise InvalidUrlException(url, _("Url string '%s' too long") % url)

    # check against whitelist
    match_against_whitelist(full_url)
    for url in full_url.split(";"):
        if not ":" in url:
            raise InvalidUrlException(url, _("No ':' in the uri"))

        # now parse it

        (schema, packages) = url.split(":", 1)
        packages = packages.split(",")

        for package in packages:
            apt_url = AptUrl()
            apt_url.schema = schema
            # check for schemas of the form: apt+http://
            if schema.startswith("apt+"):
                apt_url.repo_url = schema[len("apt+"):] + ":" + package.split("?",1)[0]
            else:
                if "?" in package:
                    apt_url.package = package.split("?")[0].lstrip("/").rstrip("/")
                else:
                    apt_url.package = package.lstrip("/").rstrip("/")

            # now parse the ?... bits
            if "?" in package:
                key_value_pairs = package.split("?")[1:]
                for s in key_value_pairs:
                    if "&" in s:
                        and_key_value_pairs = s.split("&")
                        for s in and_key_value_pairs:
                            set_value(apt_url, s)
                    else:
                        set_value(apt_url, s)

            # do substitution (if needed) 
            do_apt_url_substitution(apt_url, mapping)
            
            # check if the package name is valid
            if not is_format_package_name(apt_url.package):
                raise InvalidUrlException(url, "Invalid package name '%s'" % apt_url.package)
            
            res.append(apt_url)
    return res    
