# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2015 HP Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch
#

# Std Lib
import os
import os.path
import gzip
import re
import time
import tempfile
import glob

# Local
from base.g import *
from base import utils, models, os_utils
from base.sixext import PY3

INVALID_PRINTER_NAME_CHARS = """~`!@#$%^&*()=+[]{}()\\/,.<>?'\";:| """

# Handle case where cups.py (via device.py) is loaded
# and cupsext doesn't exist yet. This happens in the
# installer and in a fresh sandbox if the Python extensions
# aren't installed yet.
try:
    current_language = os.getenv("LANG")
    newlang = "C"

    # this is a workaround due CUPS rejecting all encoding except ASCII
    # and utf-8
    # if the locale contains the encoding, switch to the same locale,
    # but with utf-8 encoding. Otherwise use C locale.
    if current_language is not None and current_language.count('.'):
        newlang, encoding = current_language.split('.')
        newlang += ".UTF-8"

    os.environ['LANG'] = newlang

    import cupsext

    # restore the old env values
    if current_language is not None:
        os.environ['LANG'] = current_language

except ImportError:
    if not os.getenv("HPLIP_BUILD"):
        log.warn("CUPSEXT could not be loaded. Please check HPLIP installation.")
        sys.exit(1)


IPP_PRINTER_STATE_IDLE = 3
IPP_PRINTER_STATE_PROCESSING = 4
IPP_PRINTER_STATE_STOPPED = 5

# Std CUPS option types
PPD_UI_BOOLEAN = 0   # True or False option
PPD_UI_PICKONE = 1   # Pick one from a list
PPD_UI_PICKMANY = 2  # Pick zero or more from a list

# Non-std: General
UI_SPINNER = 100           # Simple spinner with opt. suffix (ie, %)
UI_UNITS_SPINNER = 101     # Spinner control w/pts, cm, in, etc. units (not impl.)
UI_BANNER_JOB_SHEETS = 102 # dual combos for banner job-sheets
UI_PAGE_RANGE = 103        # Radio + page range entry field

# Non-std: Job storage
UI_JOB_STORAGE_MODE = 104      # Combo w/linkage
UI_JOB_STORAGE_PIN = 105       # Radios w/PIN entry
UI_JOB_STORAGE_USERNAME = 106  # Radios w/text entry
UI_JOB_STORAGE_ID = 107        # Radios w/text entry
UI_JOB_STORAGE_ID_EXISTS = 108 # Combo

UI_INFO = 109        # Information field, required Information name and Value

# ipp_op_t
IPP_PAUSE_PRINTER = 0x0010
IPP_RESUME_PRINTER = 0x011
IPP_PURGE_JOBS = 0x012
CUPS_GET_DEFAULT = 0x4001
CUPS_GET_PRINTERS = 0x4002
CUPS_ADD_MODIFY_PRINTER = 0x4003
CUPS_DELETE_PRINTER = 0x4004
CUPS_GET_CLASSES = 0x4005
CUPS_ADD_MODIFY_CLASS = 0x4006
CUPS_DELETE_CLASS = 0x4007
CUPS_ACCEPT_JOBS = 0x4008
CUPS_REJECT_JOBS = 0x4009
CUPS_SET_DEFAULT = 0x400a
CUPS_GET_DEVICES = 0x400b
CUPS_GET_PPDS = 0x400c
CUPS_MOVE_JOB = 0x400d
CUPS_AUTHENTICATE_JOB = 0x400e

# ipp_jstate_t
IPP_JOB_PENDING = 3    # Job is waiting to be printed
IPP_JOB_HELD = 4       # Job is held for printing
IPP_JOB_PROCESSING = 5 # Job is currently printing
IPP_JOB_STOPPED = 6    # Job has been stopped
IPP_JOB_CANCELLED = 7  # Job has been cancelled
IPP_JOB_ABORTED = 8    # Job has aborted due to error
IPP_JOB_COMPLETED = 8  # Job has completed successfully

# ipp_status_e
IPP_OK = 0x0000 # successful-ok
IPP_OK_SUBST = 0x001 # successful-ok-ignored-or-substituted-attributes
IPP_OK_CONFLICT = 0x002 # successful-ok-conflicting-attributes
IPP_OK_IGNORED_SUBSCRIPTIONS = 0x003 # successful-ok-ignored-subscriptions
IPP_OK_IGNORED_NOTIFICATIONS = 0x004 # successful-ok-ignored-notifications
IPP_OK_TOO_MANY_EVENTS = 0x005 # successful-ok-too-many-events
IPP_OK_BUT_CANCEL_SUBSCRIPTION = 0x006 # successful-ok-but-cancel-subscription
IPP_OK_EVENTS_COMPLETE = 0x007 # successful-ok-events-complete
IPP_REDIRECTION_OTHER_SITE = 0x300
IPP_BAD_REQUEST = 0x0400 # client-error-bad-request
IPP_FORBIDDEN = 0x0401 # client-error-forbidden
IPP_NOT_AUTHENTICATED = 0x0402 # client-error-not-authenticated
IPP_NOT_AUTHORIZED = 0x0403 # client-error-not-authorized
IPP_NOT_POSSIBLE = 0x0404 # client-error-not-possible
IPP_TIMEOUT = 0x0405 # client-error-timeout
IPP_NOT_FOUND = 0x0406 # client-error-not-found
IPP_GONE = 0x0407 # client-error-gone
IPP_REQUEST_ENTITY = 0x0408 # client-error-request-entity-too-large
IPP_REQUEST_VALUE = 0x0409 # client-error-request-value-too-long
IPP_DOCUMENT_FORMAT = 0x040a # client-error-document-format-not-supported
IPP_ATTRIBUTES = 0x040b # client-error-attributes-or-values-not-supported
IPP_URI_SCHEME = 0x040c # client-error-uri-scheme-not-supported
IPP_CHARSET = 0x040d # client-error-charset-not-supported
IPP_CONFLICT = 0x040e # client-error-conflicting-attributes
IPP_COMPRESSION_NOT_SUPPORTED = 0x040f # client-error-compression-not-supported
IPP_COMPRESSION_ERROR = 0x0410 # client-error-compression-error
IPP_DOCUMENT_FORMAT_ERROR = 0x0411 # client-error-document-format-error
IPP_DOCUMENT_ACCESS_ERROR = 0x0412 # client-error-document-access-error
IPP_ATTRIBUTES_NOT_SETTABLE = 0x0413 # client-error-attributes-not-settable
IPP_IGNORED_ALL_SUBSCRIPTIONS = 0x0414 # client-error-ignored-all-subscriptions
IPP_TOO_MANY_SUBSCRIPTIONS = 0x0415 # client-error-too-many-subscriptions
IPP_IGNORED_ALL_NOTIFICATIONS = 0x0416 # client-error-ignored-all-notifications
IPP_PRINT_SUPPORT_FILE_NOT_FOUND = 0x0417 # client-error-print-support-file-not-found
IPP_INTERNAL_ERROR = 0x0500 # server-error-internal-error
IPP_OPERATION_NOT_SUPPORTED = 0x0501 # server-error-operation-not-supported
IPP_SERVICE_UNAVAILABLE = 0x0502 # server-error-service-unavailable
IPP_VERSION_NOT_SUPPORTED = 0x0503 # server-error-version-not-supported
IPP_DEVICE_ERROR = 0x0504 # server-error-device-error
IPP_TEMPORARY_ERROR = 0x0505 # server-error-temporary-error
IPP_NOT_ACCEPTING = 0x0506 # server-error-not-accepting-jobs
IPP_PRINTER_BUSY = 0x0507 # server-error-busy
IPP_ERROR_JOB_CANCELLED = 0x0508 # server-error-job-canceled
IPP_MULTIPLE_JOBS_NOT_SUPPORTED = 0x0509 # server-error-multiple-document-jobs-not-supported
IPP_PRINTER_IS_DEACTIVATED = 0x050a # server-error-printer-is-deactivated

CUPS_ERROR_BAD_NAME = 0x0f00
CUPS_ERROR_BAD_PARAMETERS = 0x0f01

nickname_pat = re.compile(r'''\*NickName:\s*\"(.*)"''', re.MULTILINE)
pat_cups_error_log = re.compile("""^loglevel\s?(debug|debug2|warn|info|error|none)""", re.I)
ppd_pat = re.compile(r'''.*hp-(.*?)(-.*)*\.ppd.*''', re.I)



def getPPDPath(addtional_paths=None):
    """
        Returns the CUPS ppd path (not the foomatic one under /usr/share/ppd).
        Usually this is /usr/share/cups/model.
    """
    if addtional_paths is None:
        addtional_paths = []

    search_paths = prop.ppd_search_path.split(';') + addtional_paths

    for path in search_paths:
        ppd_path = os.path.join(path, 'cups/model')
        if os.path.exists(ppd_path):
            return ppd_path


def getAllowableMIMETypes():
    """
        Scan all /etc/cups/*.convs and /usr/share/cups/mime
        files for allowable file formats.
    """
    paths = []
    allowable_mime_types = []
    files = []
    if os.path.exists("/etc/cups"):
        paths.append("/etc/cups/*.convs")
    if os.path.exists("/usr/share/cups/mime"):
        paths.append("/usr/share/cups/mime/*.convs")
    for path in paths:
        files.extend(glob.glob(path))
    for f in files:
        #log.debug( "Capturing allowable MIME types from: %s" % f )
        conv_file = open(f, 'r')

        for line in conv_file:
            if not line.startswith("#") and len(line) > 1:
                try:
                    source, dest, cost, prog =  line.split()
                except ValueError:
                    continue

                if source not in ('application/octet-stream', 'application/vnd.cups-postscript'):
                    allowable_mime_types.append(source)

    # Add some well-known MIME types that may not appear in the .convs files
    allowable_mime_types.append("image/x-bmp")
    allowable_mime_types.append("text/cpp")
    allowable_mime_types.append("application/x-python")
    allowable_mime_types.append("application/hplip-fax")

    return allowable_mime_types


def getPPDDescription(f):
    if f.endswith('.gz'):
        nickname = gzip.GzipFile(f, 'r').read(4096)
    else:
        nickname = open(f, 'r').read(4096)

    try:
        desc = nickname_pat.search(nickname.decode('utf-8')).group(1)
    except AttributeError:
        desc = ''

    return desc


def getSystemPPDs():
    major, minor, patch = getVersionTuple()
    ppds = {} # {'ppd name' : 'desc', ...}

    if major == 1 and minor < 2:
        ppd_dir = sys_conf.get('dirs', 'ppd')
        log.debug("(CUPS 1.1.x) Searching for PPDs in: %s" % ppd_dir)

        for f in utils.walkFiles(ppd_dir, pattern="HP*ppd*;hp*ppd*", abs_paths=True):
            desc = getPPDDescription(f)

            if not ('foo2' in desc or
                    'gutenprint' in desc.lower() or
                    'gutenprint' in f):

                ppds[f] = desc
                log.debug("%s: %s" % (f, desc))

    else: # 1.2.x
        log.debug("(CUPS 1.2.x) Getting list of PPDs using CUPS_GET_PPDS...")
        ppd_dict = cupsext.getPPDList()
        cups_ppd_path = getPPDPath() # usually /usr/share/cups/model
        foomatic_ppd_path = sys_conf.get('dirs', 'ppdbase', '/usr/share/ppd')

        if not foomatic_ppd_path or not os.path.exists(foomatic_ppd_path):
            foomatic_ppd_path = '/usr/share/ppd'

        log.debug("CUPS PPD base path = %s" % cups_ppd_path)
        log.debug("Foomatic PPD base path = %s" % foomatic_ppd_path)

        for ppd in ppd_dict:
            if not ppd:
                continue

            if 'hp-' in ppd.lower() or 'hp_' in ppd.lower() and \
                ppd_dict[ppd]['ppd-make'] == 'HP':

                desc = ppd_dict[ppd]['ppd-make-and-model']

                if not ('foo2' in desc.lower() or
                        'gutenprint' in desc.lower() or
                        'gutenprint' in ppd):

                    # PPD files returned by CUPS_GET_PPDS (and by lpinfo -m)
                    # can be relative to /usr/share/ppd/ or to
                    # /usr/share/cups/model/. Not sure why this is.
                    # Here we will try both and see which one it is...

                    if os.path.exists(ppd):
                        path = ppd
                    else:
                        try:
                            path = os.path.join(foomatic_ppd_path, ppd)
                        except AttributeError: # happens on some boxes with provider: style ppds (foomatic: etc)
                            path = ppd
                        else:
                            if not os.path.exists(path):
                                try:
                                    path = os.path.join(cups_ppd_path, ppd)
                                except AttributeError:
                                    path = ppd
                                else:
                                    if not os.path.exists(path):
                                        path = ppd # foomatic: or some other driver

                    ppds[path] = desc
                    #log.debug("%s: %s" % (path, desc))

    return ppds


## TODO: Move this to CUPSEXT for better performance
def levenshtein_distance(a,b):
    """
    Calculates the Levenshtein distance between a and b.
    Written by Magnus Lie Hetland.
    """
    n, m = len(a), len(b)
    if n > m:
        a,b = b,a
        n,m = m,n

    current = list(range(n+1))
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*m

        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]

            if a[j-1] != b[i-1]:
                change = change + 1

            current[j] = min(add, delete, change)

    return current[n]


number_pat = re.compile(r""".*?(\d+)""", re.IGNORECASE)

STRIP_STRINGS2 = ['foomatic:', 'hp-', 'hp_', 'hp ', '.gz', '.ppd',
                  'drv:', '-pcl', '-pcl3', '-jetready',
                 '-zxs', '-zjs', '-ps', '-postscript',
                 '-jr', '-lidl', '-lidil', '-ldl', '-hpijs']


for p in list(models.TECH_CLASS_PDLS.values()):
    pp = '-%s' % p
    if pp not in STRIP_STRINGS2:
        STRIP_STRINGS2.append(pp)


STRIP_STRINGS = STRIP_STRINGS2[:]
STRIP_STRINGS.extend(['-series', ' series', '_series'])


def stripModel2(model): # For new 2.8.10+ PPD find algorithm
    model = model.lower()

    for x in STRIP_STRINGS2:
        model = model.replace(x, '')

    return model


def stripModel(model): # for old PPD find algorithm (removes "series" as well)
    model = model.lower()

    for x in STRIP_STRINGS:
        model = model.replace(x, '')

    return model


def getPPDFile(stripped_model, ppds): # Old PPD find
    """
        Match up a model name to a PPD from a list of system PPD files.
    """
    log.debug("1st stage edit distance match")
    mins = {}
    eds = {}
    min_edit_distance = sys.maxsize

    log.debug("Determining edit distance from %s (only showing edit distances < 4)..." % stripped_model)
    for f in ppds:
        t = stripModel(os.path.basename(f))
        eds[f] = levenshtein_distance(stripped_model, t)
        if eds[f] < 4:
            log.debug("dist('%s') = %d" % (t, eds[f]))
        min_edit_distance = min(min_edit_distance, eds[f])

    log.debug("Min. dist = %d" % min_edit_distance)

    for f in ppds:
        if eds[f] == min_edit_distance:
            for m in mins:
                if os.path.basename(m) == os.path.basename(f):
                    break # File already in list possibly with different path (Ubuntu, etc)
            else:
                mins[f] = ppds[f]

    log.debug(mins)

    if len(mins) > 1: # try pattern matching the model number
        log.debug("2nd stage matching with model number")

        try:
            model_number = number_pat.match(stripped_model).group(1)
            model_number = int(model_number)
        except AttributeError:
            pass
        except ValueError:
            pass
        else:
            log.debug("model_number=%d" % model_number)
            matches = {} #[]
            for x in range(3): # 1, 10, 100
                factor = 10**x
                log.debug("Factor = %d" % factor)
                adj_model_number = int(model_number/factor)*factor
                number_matching, match = 0, ''

                for m in mins:
                    try:
                        mins_model_number = number_pat.match(os.path.basename(m)).group(1)
                        mins_model_number = int(mins_model_number)
                        log.debug("mins_model_number= %d" % mins_model_number)
                    except AttributeError:
                        continue
                    except ValueError:
                        continue

                    mins_adj_model_number = int(mins_model_number/factor)*factor
                    log.debug("mins_adj_model_number=%d" % mins_adj_model_number)
                    log.debug("adj_model_number=%d" % adj_model_number)

                    if mins_adj_model_number == adj_model_number:
                        log.debug("match")
                        number_matching += 1
                        matches[m] = ppds[m]
                        log.debug(matches)

                    log.debug("***")

                if len(matches):
                    mins = matches
                    break

    return mins


def getPPDFile2(mq,model, ppds): # New PPD find
    # This routine is for the new PPD naming scheme begun in 2.8.10
    # and beginning with implementation in 2.8.12 (Qt4 hp-setup)
    # hp-<model name from models.dat w/o beginning hp_>[-<pdl>][-<pdl>][...].ppd[.gz]
    # 3.9.6: Added handling for hpijs vs. hpcups PPDs/DRVs


    #Check if common ppd name is already given in models.dat(This is needed because in case of devices having more than one derivatives
    #will have diffrent model name strings in device ID, because of which we don't get the common ppd name for search)
    model = models.normalizeModelName(model)
    ppd_name = mq.get('ppd-name',0)
    if ppd_name == 0:
        stripped_model = stripModel2(model)
    else:
        stripped_model = stripModel2(ppd_name)

    log.debug("Matching PPD list to model  %s..." % stripped_model)

    matches = []
    for f in ppds:
        match = ppd_pat.match(f)
        if match is not None:
            if match.group(1) == stripped_model:
                log.debug("Found match: %s" % f)
                try:
                    pdls = match.group(2).split('-')
                except AttributeError:
                    pdls = []

                if (prop.hpcups_build and 'hpijs' not in f) or \
                    ((prop.hpijs_build and 'hpijs' in pdls) or (prop.hpcups_build and 'hpijs' not in pdls)) or \
                    ('ps' in pdls):
                    matches.append((f, [p for p in pdls if p and p != 'hpijs']))

    log.debug(matches)
    num_matches = len(matches)

    if num_matches == 0:
        log.debug("No PPD found for model %s using new algorithm. Trying old algorithm..." % stripped_model)
        #Using Old algo, ignores the series keyword in ppd searching.
        matches2 = list(getPPDFile(stripModel(stripped_model), ppds).items())
        log.debug(matches2)
        num_matches2 = len(matches2)
        if num_matches2:
            for f, d in matches2:
                match = ppd_pat.match(f)
                if match is not None:
                    log.debug("Found match: %s" % f)
                    try:
                        pdls = match.group(2).split('-')
                    except AttributeError:
                        pdls = []

                    if (prop.hpcups_build and 'hpijs' not in f) or \
                       ((prop.hpijs_build and 'hpijs' in pdls) or (prop.hpcups_build and 'hpijs' not in pdls)) or \
                       ('ps' in pdls):
                        matches.append((f, [p for p in pdls if p and p != 'hpijs']))

        log.debug(matches)
        num_matches = len(matches)

    if num_matches == 0:
        log.error("No PPD found for model %s using old algorithm." % stripModel(stripped_model))
        return None

    elif num_matches == 1:
        log.debug("One match found.")
        return (matches[0][0], '')

    # > 1
    log.debug("%d matches found. Searching based on PDL: Host > PS > PCL/Other" % num_matches)
    for p in [models.PDL_TYPE_HOST, models.PDL_TYPE_PS, models.PDL_TYPE_PCL]:
        for f, pdl_list in matches:
            for x in pdl_list:
                # default to HOST-based PDLs, as newly supported PDLs will most likely be of this type
                if models.PDL_TYPES.get(x, models.PDL_TYPE_HOST) == p:
                    log.debug("Selecting '-%s' PPD: %s" % (x, f))
                    return (f, '')

    log.debug("%d matches found. Searching based on Filters: HPCUPS > HPIJS" % num_matches)
    for p in ["hpcups","hpijs"]:
        for f, pdl_list in matches:
            if p in f:
                log.debug("Selecting PPD: %s" % (f))
                return (f, '')

    # No specific PDL or Filter found, so just return 1st found PPD file
    log.debug("No specific PDL located. Defaulting to first found PPD file.")
    return (matches[0][0], '')

##
# Function :- getFaxPPDFile()
# Arguments:-
#   1) mq  -->  Device model query object
#    2) model --> Fax model name
# Return arguments:-
#   1) fax_ppd --> Found Fax ppd file. (Returns None if not found)
#   2) expt_fax_ppd_name  -> Expected Fax PPD name
#   3) nick --> Expected Fax PPD description
#
def getFaxPPDFile(mq, model):
    try:
        fax_ppd = None
        nick = "HP Fax hpcups"
        expected_fax_ppd_name = "HP-Fax-hpcups"
        log.debug("Searching for fax PPD for model %s  hpcups_build =%d" % (model,prop.hpcups_build))
        if prop.hpcups_build:
            if mq.get('fax-type', FAX_TYPE_NONE) == FAX_TYPE_MARVELL:
                expected_fax_ppd_name = "HP-Fax3-hpcups" # Fixed width (2528 pixels) and 300dpi rendering
                nick = "HP Fax3 hpcups"
            elif mq.get('fax-type', FAX_TYPE_NONE) == FAX_TYPE_SOAP or mq.get('fax-type', FAX_TYPE_NONE) == FAX_TYPE_LEDMSOAP:
                expected_fax_ppd_name = "HP-Fax2-hpcups" # Fixed width (2528 pixels) and 300dpi rendering
                nick = "HP Fax2 hpcups"
            elif mq.get('fax-type', FAX_TYPE_NONE) == FAX_TYPE_LEDM:
                expected_fax_ppd_name = "HP-Fax4-hpcups"# Fixed width (2528 pixels) and 300dpi rendering
                nick = "HP Fax4 hpcups"
            else:
                expected_fax_ppd_name = "HP-Fax-hpcups" # Standard
                nick = "HP Fax hpcups"

        else: # hpijs
            if mq.get('fax-type', FAX_TYPE_NONE) == FAX_TYPE_MARVELL:
                expected_fax_ppd_name = "HP-Fax3-hpijs" # Fixed width (2528 pixels) and 300dpi rendering
                nick = "HP Fax3 hpijs"
            if mq.get('fax-type', FAX_TYPE_NONE) == FAX_TYPE_SOAP or mq.get('fax-type', FAX_TYPE_NONE) == FAX_TYPE_LEDMSOAP:
                expected_fax_ppd_name = "HP-Fax2-hpijs" # Fixed width (2528 pixels) and 300dpi rendering
                nick = "HP Fax2 hpijs"
            if mq.get('fax-type', FAX_TYPE_NONE) == FAX_TYPE_LEDM:
                expected_fax_ppd_name = "HP-Fax4-hpijs" # Fixed width (2528 pixels) and 300dpi rendering
                nick = "HP Fax4 hpijs"
            else:
                expected_fax_ppd_name = "HP-Fax-hpijs" # Standard
                nick = "HP Fax hpijs"

        ppds = []
        for f in utils.walkFiles(sys_conf.get('dirs', 'ppd'), pattern="HP-Fax*.ppd*", abs_paths=True):
            ppds.append(f)
        log.debug("ppds=%s"%ppds)
        for f in ppds:
            if f.find(expected_fax_ppd_name) >= 0 and getPPDDescription(f) == nick:
                fax_ppd = f
                log.debug("Found fax PPD: %s" % f)
                break
        else:
            log.error("Unable to locate the HPLIP Fax PPD file: %s.ppd.gz file."%expected_fax_ppd_name)

    finally:
        return fax_ppd,expected_fax_ppd_name, nick




def getErrorLogLevel():
    cups_conf = '/etc/cups/cupsd.conf'
    try:
        f = open(cups_conf, 'r')
    except OSError:
        log.error("%s not found." % cups_conf)
    except IOError:
        log.error("%s: I/O error." % cups_conf)
    else:
        for l in f:
            m = pat_cups_error_log.match(l)
            if m is not None:
                level = m.group(1).lower()
                log.debug("CUPS error_log LogLevel: %s" % level)
                return level

    log.debug("CUPS error_log LogLevel: unknown")
    return 'unknown'


def getPrintJobErrorLog(job_id, max_lines=1000, cont_interval=5):
    ret = []
    s = '[Job %d]' % job_id
    #level = getErrorLogLevel()
    cups_conf = '/var/log/cups/error_log'

    #if level in ('debug', 'debug2'):
    if 1:
        try:
            f = open(cups_conf, 'r')
        except (IOError, OSError):
            log.error("Could not open the CUPS error_log file: %s" % cups_conf)
            return ''

        else:
            if s in open(cups_conf, 'r').read():
                queue = utils.Queue()
                job_found = False

                while True:
                    line = f.readline()

                    if s in line:
                        job_found = True

                        while len(queue):
                            ret.append(queue.get())

                        ret.append(line.strip())

                        if len(ret) > max_lines:
                            break

                    else:
                        if job_found:
                            queue.put(line.strip())

                            if len(queue) > cont_interval:
                                break

            return '\n'.join(ret)


#
# cupsext wrappers
#

def getDefaultPrinter():
    r = cupsext.getDefaultPrinter()
    if r is None:
        log.debug("The CUPS default printer is not set.")
    return r

def setDefaultPrinter(printer_name):
    if PY3:
       printer_name = str(printer_name, "utf-8")
    setPasswordPrompt("You do not have permission to set the default printer. You need authentication.")
    return cupsext.setDefaultPrinter(printer_name)

def accept(printer_name):
    setPasswordPrompt("You do not have permission to accept jobs on a printer queue. You need authentication.")
    return controlPrinter(printer_name, CUPS_ACCEPT_JOBS)

def reject(printer_name):
    setPasswordPrompt("You do not have permission to reject jobs on a printer queue. You need authentication.")
    return controlPrinter(printer_name, CUPS_REJECT_JOBS)

def start(printer_name):
    setPasswordPrompt("You do not have permission to start a printer queue. You need authentication.")
    return controlPrinter(printer_name, IPP_RESUME_PRINTER)

def stop(printer_name):
    setPasswordPrompt("You do not have permission to stop a printer queue. You need authentication.")
    return controlPrinter(printer_name, IPP_PAUSE_PRINTER)

def purge(printer_name):
    setPasswordPrompt("You do not have permission to purge jobs. You need authentication.")
    return controlPrinter(printer_name, IPP_PURGE_JOBS)

def controlPrinter(printer_name, cups_op):
    if cups_op in (CUPS_ACCEPT_JOBS, CUPS_REJECT_JOBS, IPP_PAUSE_PRINTER, IPP_RESUME_PRINTER, IPP_PURGE_JOBS):
        return cupsext.controlPrinter(printer_name, cups_op)

    return 0;

def openPPD(printer):
    if not printer:
        return

    return cupsext.openPPD(printer)

def closePPD():
    return cupsext.closePPD()

def getPPD(printer):
    if not printer:
        return

    return cupsext.getPPD(printer)

def getPPDOption(option):
    return cupsext.getPPDOption(option)

def getPPDPageSize():
    return cupsext.getPPDPageSize()

def getPrinters():
##    p2 = []
##    p = cupsext.getPrinters()
##    for pp in p:
##        print pp
##        try:
##            pn = pp.name.decode('utf-8')
##        except UnicodeError:
##            pass
##
##        p2.append(pp)
##
##    return p2
    return cupsext.getPrinters()

def getJobs(my_job=0, completed=0):
    return cupsext.getJobs(my_job, completed)

def getAllJobs(my_job=0):
    return cupsext.getJobs(my_job, 0) + cupsext.getJobs(my_job, 1)

def getVersion():
    return cupsext.getVersion()

def getVersionTuple():
    return cupsext.getVersionTuple()

def getServer():
    return cupsext.getServer()

def cancelJob(jobid, dest=None):
    setPasswordPrompt("You do not have permission to cancel a job. You need authentication.")
    if dest is not None:
        return cupsext.cancelJob(dest, jobid)
    else:
        jobs = cupsext.getJobs(0, 0)
        for j in jobs:
            if j.id == jobid:
                return cupsext.cancelJob(j.dest, jobid)

    return False

def resetOptions():
    return cupsext.resetOptions()

def addOption(option):
    return cupsext.addOption(option)

def getOptions():
    return cupsext.getOptions()

def duplicateSection(section):
    return cupsext.duplicateSection(section)

def printFile(printer, filename, title):
    if os.path.exists(filename):
        if not PY3:
            printer = printer.encode('utf-8')
            filename = filename.encode('utf-8')
            title = title.encode('utf-8')

        return cupsext.printFileWithOptions(printer, filename, title)

    else:
        return -1

def addPrinter(printer_name, device_uri, location, ppd_file, model, info):
    setPasswordPrompt("You do not have permission to add a printer. You need authentication.")
    log.debug("addPrinter('%s', '%s', '%s', '%s', '%s', '%s')" %
        ( printer_name, device_uri, location, ppd_file, model, info))

    if ppd_file and not os.path.exists(ppd_file):
        log.error("PPD file '%s' not found." % ppd_file)
        return (-1, "PPD file not found")

    return cupsext.addPrinter(printer_name, device_uri, location, ppd_file, model, info)

def delPrinter(printer_name):
    setPasswordPrompt("You do not have permission to delete a printer. You need authentication.")
    return cupsext.delPrinter(printer_name)

def enablePrinter(printer_name):
    setPasswordPrompt("You do not have permission to enable a printer. You need authentication.")
    cmd_full_path = utils.which('cupsenable', True)
    cmd= "%s %s" % (cmd_full_path, printer_name)
    return os_utils.execute(cmd)

def getGroupList():
    return cupsext.getGroupList()

def getGroup(group):
    return cupsext.getGroup(group)

def getOptionList(group):
    return cupsext.getOptionList(group)

def getOption(group, option):
    return cupsext.getOption(group, option)

def getChoiceList(group, option):
    return cupsext.getChoiceList(group, option)

def getChoice(group, option, choice):
    return cupsext.getChoice(group, option, choice)

def setOptions():
    return cupsext.setOptions()

def removeOption(option):
    return cupsext.removeOption(option)

def setPasswordCallback(func):
    return cupsext.setPasswordCallback(func)

def setPasswordPrompt(prompt):
    return cupsext.setPasswordPrompt(prompt)

def findPPDAttribute(name, spec):
    return cupsext.findPPDAttribute(name, spec)

def releaseCupsInstance():
    return cupsext.releaseCupsInstance()


def cups_operation(operation_func, mode, ui_toolkit, ui_obj, *cups_op_args):
    cnt = 0
    while cnt < 3:
        cnt += 1
        result, status_str = operation_func(*cups_op_args)
        if result != IPP_FORBIDDEN:
            break
        else:
            releaseCupsInstance()
            if cnt < 3:
                if mode == INTERACTIVE_MODE:
                    log.error("Could not connect to CUPS Server due to insufficient privileges.Try with valid user")
                elif ui_toolkit == 'qt3':
                    ui_obj.FailureUI("<b>Could not connect to CUPS Server due to insufficient privileges.</b><p>Try with valid user")
                else:
                    from ui4 import ui_utils
                    ui_utils.FailureUI(ui_obj, "<b>Could not connect to CUPS Server due to insufficient privileges.</b><p>Try with valid user")

    return result, status_str
