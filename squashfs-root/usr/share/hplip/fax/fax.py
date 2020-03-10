# -*- coding: utf-8 -*-
#
# (c) Copyright 2015 HP Development Company, L.P.
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
import sys
import os
import threading
import pickle
import time
import struct

# Local
from base.g import *
from base.codes import *
from base.ldif import LDIFParser
from base import device, utils, vcard
from prnt import cups
from base.sixext import BytesIO
from base.sixext import to_bytes_utf8, to_long, to_unicode
try:
    from . import coverpages
except ImportError:
    pass

try:
    import dbus
except ImportError:
    log.error("dbus is required for PC send fax.")

import warnings
# Ignore: .../dbus/connection.py:242: DeprecationWarning: object.__init__() takes no parameters
# (occurring on Python 2.6/dBus 0.83/Ubuntu 9.04)
warnings.simplefilter("ignore", DeprecationWarning)


# Update queue values (Send thread ==> UI)
STATUS_IDLE = 0
STATUS_PROCESSING_FILES = 1
STATUS_SENDING_TO_RECIPIENT = 2
STATUS_DIALING = 3
STATUS_CONNECTING = 4
STATUS_SENDING = 5
STATUS_COMPLETED = 6
STATUS_CREATING_COVER_PAGE = 7
STATUS_ERROR = 8
STATUS_BUSY = 9
STATUS_CLEANUP = 10
STATUS_ERROR_IN_CONNECTING = 11
STATUS_ERROR_IN_TRANSMITTING = 12
STATUS_ERROR_PROBLEM_IN_FAXLINE = 13
STATUS_JOB_CANCEL = 14 

# Event queue values (UI ==> Send thread)
EVENT_FAX_SEND_CANCELED = 1
# Other values in queue are:
#EVENT_FAX_RENDER_COMPLETE_BEGIN = 8010
#EVENT_FAX_RENDER_COMPLETE_SENDDATA = 8011
#EVENT_FAX_RENDER_COMPLETE_END = 8012

# **************************************************************************** #
# HPLIP G3 Fax File Format (big endian)
#
# #==============================================#
# # File Header: Total 28 bytes                  #
# #..............................................#
# # Magic bytes: 8 bytes ("hplip_g3")            #
# # Format version: 8 bits (1)                   #
# # Total pages in file(=p): 32 bits             #
# # Hort DPI: 16 bits (200 or 300)               #
# # Vert DPI: 16 bits (100, 200, or 300)         #
# # Page Size: 8 bits (0=Unk, 1=Letter, 2=A4,    #
# #                    3=Legal)                  #
# # Resolution: 8 bits (0=Unk, 1=Std, 2=Fine,    #
# #                     3=300DPI)                #
# # Encoding: 8 bits (2=MH, 4=MMR, 7=JPEG)       #
# # Reserved1: 32 bits (0)                       #
# # Reserved2: 32 bits (0)                       #
# #----------------------------------------------#
# # Page 1 Header: Total 24 bytes                #
# #..............................................#
# # Page number: 32 bits (1 based)               #
# # Pixels per row: 32 bits                      #
# # Rows this page: 32 bits                      #
# # Image bytes this page(=x): 32 bits           #
# # Thumbnail bytes this page(=y): 32 bits       #
# #  (thumbnail not present if y == 0)           #
# #  (encoding?)                                 #
# #     letter: 134 px wide x 173 px high        #
# #     legal:  134 px wide x 221 px high        #
# #     a4 :    134 px wide x 190 px high        #
# # Reserved3: 32 bits (0)                       #
# #..............................................#
# # Image data: x bytes                          #
# #..............................................#
# # Thumbnail data: y bytes (if present)         #
# #----------------------------------------------#
# # Page 2 Header: Total 24 bytes                #
# #..............................................#
# # Image Data                                   #
# #..............................................#
# # Thumbnail data (if present)                  #
# #----------------------------------------------#
# # ... Pages 3 - (p-1) ...                      #
# #----------------------------------------------#
# # Page p Header: Total 24 bytes                #
# #..............................................#
# # Image Data                                   #
# #..............................................#
# # Thumbnail data (if present)                  #
# #==============================================#
#

RESOLUTION_STD = 1
RESOLUTION_FINE = 2
RESOLUTION_300DPI = 3

FILE_HEADER_SIZE = 28
PAGE_HEADER_SIZE = 24
# **************************************************************************** #

##skip_dn = ["uid=foo,ou=People,dc=example,dc=com",
##    "uid=bar,ou=People,dc=example,dc=com", "dc=example,dc=com"]

class FaxLDIFParser(LDIFParser):
    def __init__(self, input, db):
        LDIFParser.__init__(self, input)
        self.db = db

    def handle(self, dn, entry):
        if dn:
            try:
                firstname = entry['givenName'][0]
            except KeyError:
                try:
                    firstname = entry['givenname'][0]
                except KeyError:
                    firstname = ''

            try:
                lastname = entry['sn'][0]
            except KeyError:
                lastname = ''

            try:
                nickname = entry['cn'][0]
            except KeyError:
                nickname = firstname + ' ' + lastname

            try:
                fax = entry['facsimiletelephonenumber'][0] # fax
            except KeyError:
                try:
                    fax = entry['fax'][0]
                except KeyError:
                    fax  = ''

            grps = []
            try:
                grps = entry['ou']
            except KeyError:
                pass

            grps.append(to_unicode('All'))
            groups = [g for g in grps if g]

            if nickname:
                log.debug("Import: name=%s, fax=%s, group(s)=%s, notes=%s" % ( nickname, fax, ','.join(groups), dn))
                self.db.set(nickname, title, firstname, lastname, fax, groups, dn)



# **************************************************************************** #
class FaxAddressBook(object): # Pickle based address book
    def __init__(self):
        self._data = {}
        #
        # { 'name' : {'name': u'',
        #             'firstname' : u'', # NOT USED STARTING IN 2.8.9
        #             'lastname': u', # NOT USED STARTING IN 2.8.9
        #             'title' : u'',  # NOT USED STARTING IN 2.8.9
        #             'fax': u'',
        #             'groups' : [u'', u'', ...],
        #             'notes' : u'', } ...
        # }
        #
        self.load()

    def load(self):
        self._fab = "/dev/null"
        if prop.user_dir != None:
            self._fab = os.path.join(prop.user_dir, "fab.pickle")
            #old_fab = os.path.join(prop.user_dir, "fab.db")

            # Load the existing pickle if present
            if os.path.exists(self._fab):
               pickle_file = open(self._fab, "rb")
               self._data = pickle.load(pickle_file)
               pickle_file.close()
            else:
               self.save() # save the empty file to create the file


    def set(self, name, title, firstname, lastname, fax, groups, notes):
        # try:
        #     grps = [to_unicode(s) for s in groups]
        # except UnicodeDecodeError:
        #     grps = [to_unicode(s.decode('utf-8')) for s in groups]
        grps = [to_unicode(s) for s in groups]

        self._data[to_unicode(name)] = {'name' : to_unicode(name),
                                    'title': to_unicode(title),  # NOT USED STARTING IN 2.8.9
                                    'firstname': to_unicode(firstname), # NOT USED STARTING IN 2.8.9
                                    'lastname': to_unicode(lastname), # NOT USED STARTING IN 2.8.9
                                    'fax': to_unicode(fax),
                                    'notes': to_unicode(notes),
                                    'groups': grps}

        self.save()

    insert = set


    def set_key_value(self, name, key, value):
        self._data[to_unicode(name)][key] = value
        self.save()


    def get(self, name):
        return self._data.get(name, None)

    select = get

    def rename(self, old_name, new_name):
        try:
            self._data[old_name]
        except KeyError:
            return
        else:
            try:
                self._data[new_name]
            except KeyError:
                self._data[new_name] = self._data[old_name].copy()
                self._data[new_name]['name'] = new_name
                del self._data[old_name]
                self.save()


    def get_all_groups(self):
        all_groups = []
        for e, v in list(self._data.items()):
            for g in v['groups']:
                if g not in all_groups:
                    all_groups.append(g)
        return all_groups


    def get_all_records(self):
        return self._data


    def get_all_names(self):
        return list(self._data.keys())


    def save(self):
        try:
            pickle_file = open(self._fab, "wb")
            pickle.dump(self._data, pickle_file, protocol=2)
            pickle_file.close()
        except IOError:
            log.error("I/O error saving fab file.")


    def clear(self):
        self._data = {}
        self.save()


    def delete(self, name):
        if name in self._data:
            del self._data[name]
            self.save()
            return True

        return False


    def last_modification_time(self):
        try:
            return os.stat(self._fab).st_mtime
        except OSError:
            return 0


    def update_groups(self, group, members):
        for e, v in list(self._data.items()):
            if v['name'] in members: # membership indicated
                if not group in v['groups']:
                    v['groups'].append(to_unicode(group))
            else:
                if group in v['groups']:
                    v['groups'].remove(to_unicode(group))
        self.save()


    def delete_group(self, group):
        for e, v in list(self._data.items()):
            if group in v['groups']:
                v['groups'].remove(to_unicode(group))
        self.save()


    def group_members(self, group):
        members = []
        for e, v in list(self._data.items()):
            if group in v['groups']:
                members.append(e)
        return members


    def add_to_group(self, group, members):
        group_members = self.group_members(group)
        new_group_members = []
        for m in members:
            if m not in group_members:
                new_group_members.append(m)

        self.update_groups(group, group_members + new_group_members)


    def remove_from_group(self, group, remove_members):
        group_members = self.group_members(group)
        new_group_members = []
        for m in group_members:
            if m not in remove_members:
                new_group_members.append(m)

        self.update_groups(group, new_group_members)


    def rename_group(self, old_group, new_group):
        members = self.group_members(old_group)
        self.update_groups(old_group, [])
        self.update_groups(new_group, members)


    def import_ldif(self, filename):
        try:
            data = open(filename, 'r').read()
            log.debug_block(filename, data)
            parser = FaxLDIFParser(open(filename, 'r'), self)
            parser.parse()
            self.save()
            return True, ''
        except ValueError as e:
            return False, e.message


    def import_vcard(self, filename):
        data = open(filename, 'r').read()
        log.debug_block(filename, data)

        for card in vcard.VCards(vcard.VFile(vcard.opentextfile(filename))):
            log.debug(card)

            if card['name']:
                fax = ''
                for x in range(1, 9999):
                    if x == 1:
                        s = 'phone'
                    else:
                        s = 'phone%d' % x

                    try:
                        card[s]
                    except KeyError:
                        break
                    else:
                        if 'fax' in card[s]['type']:
                            fax = card[s]['number']
                            break

                org = card.get('organisation', '')
                if org:
                    org = [org]
                else:
                    org = card.get('categories', '').split(';')
                    if not org:
                        org = []

                org.append(to_unicode('All'))
                groups = [o for o in org if o]

                name = card['name']
                notes = card.get('notes', to_unicode(''))
                log.debug("Import: name=%s, fax=%s group(s)=%s notes=%s" % (name, fax, ','.join(groups), notes))
                self.set(name, to_unicode(''), to_unicode(''), to_unicode(''), fax, groups, notes)

        return True, ''


# **************************************************************************** #
class FaxDevice(device.Device):

    def __init__(self, device_uri=None, printer_name=None,
                 callback=None,
                 fax_type=FAX_TYPE_NONE,
                 disable_dbus=False):

        device.Device.__init__(self, device_uri, printer_name,
                               None, callback, disable_dbus)

        self.send_fax_thread = None
        self.upload_log_thread = None
        self.fax_type = fax_type

        if not disable_dbus:
            session_bus = dbus.SessionBus()
            self.service = session_bus.get_object('com.hplip.StatusService', "/com/hplip/StatusService")
        else:
            self.service = None


    def setPhoneNum(self, num):
        raise AttributeError

    def getPhoneNum(self):
        raise AttributeError

    phone_num = property(getPhoneNum, setPhoneNum)


    def setStationName(self, name):
        raise AttributeError

    def getStationName(self):
        raise AttributeError

    station_name = property(getStationName, setStationName)

    def setDateAndTime(self):
        raise AttributeError

    def uploadLog(self):
        raise AttributeError

    def isUploadLogActive(self):
        raise AttributeError

    def waitForUploadLogThread(self):
        raise AttributeError

    def sendFaxes(self, phone_num_list, fax_file_list, cover_message='', cover_re='',
                  cover_func=None, preserve_formatting=False, printer_name='',
                  update_queue=None, event_queue=None):

        raise AttributeError

    def isSendFaxActive(self):
        if self.send_fax_thread is not None:
            return self.send_fax_thread.isAlive()
        else:
            return False

    def waitForSendFaxThread(self):
        if self.send_fax_thread is not None and \
            self.send_fax_thread.isAlive():

            try:
                self.send_fax_thread.join()
            except KeyboardInterrupt:
                pass


# **************************************************************************** #


def getFaxDevice(device_uri=None, printer_name=None,
                 callback=None,
                 fax_type=FAX_TYPE_NONE,
                 disable_dbus=False):

    if fax_type == FAX_TYPE_NONE:
        if device_uri is None and printer_name is not None:
            printers = cups.getPrinters()

            for p in printers:
                if p.name.lower() == printer_name.lower():
                    device_uri = p.device_uri
                    break
            else:
                raise Error(ERROR_DEVICE_NOT_FOUND)

        if device_uri is not None:
            mq = device.queryModelByURI(device_uri)
            fax_type = mq['fax-type']

    log.debug("fax-type=%d" % fax_type)

    if fax_type in (FAX_TYPE_BLACK_SEND_EARLY_OPEN, FAX_TYPE_BLACK_SEND_LATE_OPEN):
        from .pmlfax import PMLFaxDevice
        return PMLFaxDevice(device_uri, printer_name, callback, fax_type, disable_dbus)

    elif fax_type == FAX_TYPE_SOAP:
        from .soapfax import SOAPFaxDevice
        return SOAPFaxDevice(device_uri, printer_name, callback, fax_type, disable_dbus)

    elif fax_type == FAX_TYPE_LEDMSOAP:
        from .ledmsoapfax import LEDMSOAPFaxDevice
        return LEDMSOAPFaxDevice(device_uri, printer_name, callback, fax_type, disable_dbus)

    elif fax_type == FAX_TYPE_MARVELL:
        from .marvellfax import MarvellFaxDevice
        return MarvellFaxDevice(device_uri, printer_name, callback, fax_type, disable_dbus)

    elif fax_type == FAX_TYPE_LEDM:
        from .ledmfax import LEDMFaxDevice
        return LEDMFaxDevice(device_uri, printer_name, callback, fax_type, disable_dbus)

    else:
        raise Error(ERROR_DEVICE_DOES_NOT_SUPPORT_OPERATION)

# **************************************************************************** #




# TODO: Define these in only 1 place!
STATE_DONE = 0
STATE_ABORTED = 10
STATE_SUCCESS = 20
STATE_BUSY = 25
STATE_READ_SENDER_INFO = 30
STATE_PRERENDER = 40
STATE_COUNT_PAGES = 50
STATE_NEXT_RECIPIENT = 60
STATE_COVER_PAGE = 70
STATE_SINGLE_FILE = 80
STATE_MERGE_FILES = 90
STATE_SINGLE_FILE = 100
STATE_SEND_FAX = 110
STATE_CLEANUP = 120
STATE_ERROR = 130

class FaxSendThread(threading.Thread):
    def __init__(self, dev, service, phone_num_list, fax_file_list,
                 cover_message='', cover_re='', cover_func=None, preserve_formatting=False,
                 printer_name='', update_queue=None, event_queue=None):

        threading.Thread.__init__(self)

        self.dev = dev # device.Device
        self.service = service # dbus proxy to status server object
        self.phone_num_list = phone_num_list
        self.fax_file_list = fax_file_list
        self.update_queue = update_queue
        self.event_queue = event_queue
        self.cover_message = cover_message
        self.cover_re = cover_re
        self.cover_func = cover_func
        self.current_printer = printer_name
        self.stream = BytesIO()
        self.prev_update = ''
        self.remove_temp_file = False
        self.preserve_formatting = preserve_formatting
        self.results = {} # {'file' : error_code,...}
        self.cover_page_present = False
        self.recipient_file_list = []
        self.f = None # final file of fax data to send (pages merged)
        self.job_hort_dpi = 0
        self.job_hort_dpi = 0
        self.job_vert_dpi = 0
        self.job_page_size = 0
        self.job_resolution = 0
        self.job_encoding = 0


    def pre_render(self, state):
        # pre-render each page that needs rendering
        # except for the cover page
        self.cover_page_present = False
        log.debug(self.fax_file_list)

        for fax_file in self.fax_file_list: # (file, type, desc, title)
            fax_file_name, fax_file_type, fax_file_desc, \
                fax_file_title, fax_file_pages = fax_file

            if fax_file_type == "application/hplip-fax-coverpage": # render later
                self.cover_page_present = True
                log.debug("Skipping coverpage")

            #if fax_file_type == "application/hplip-fax": # already rendered
            else:
                self.rendered_file_list.append((fax_file_name, "application/hplip-fax",
                    "HP Fax", fax_file_title))

                log.debug("Processing pre-rendered file: %s (%d pages)" %
                    (fax_file_name, fax_file_pages))

            if self.check_for_cancel():
                state = STATE_ABORTED

        log.debug(self.rendered_file_list)

        if self.check_for_cancel():
            state = STATE_ABORTED

        return state


    def count_pages(self, state):
        self.recipient_file_list = self.rendered_file_list[:]
        log.debug("Counting total pages...")
        self.job_total_pages = 0
        log.debug(self.recipient_file_list)

        i = 0
        for fax_file in self.recipient_file_list: # (file, type, desc, title)
            fax_file_name = fax_file[0]
            log.debug("Processing file (counting pages): %s..." % fax_file_name)

            #self.write_queue((STATUS_PROCESSING_FILES, self.job_total_pages, ''))

            if os.path.exists(fax_file_name):
                self.results[fax_file_name] = ERROR_SUCCESS
                fax_file_fd = open(fax_file_name, 'rb')
                header = fax_file_fd.read(FILE_HEADER_SIZE)

                magic, version, total_pages, hort_dpi, vert_dpi, page_size, \
                    resolution, encoding, reserved1, reserved2 = \
                        self.decode_fax_header(header)

                if magic != b'hplip_g3':
                    log.error("Invalid file header. Bad magic.")
                    self.results[fax_file_name] = ERROR_FAX_INVALID_FAX_FILE
                    state = STATE_ERROR
                    continue

                if not i:
                    self.job_hort_dpi, self.job_vert_dpi, self.job_page_size, \
                        self.job_resolution, self.job_encoding = \
                        hort_dpi, vert_dpi, page_size, resolution, encoding

                    i += 1
                else:
                    if self.job_hort_dpi != hort_dpi or \
                        self.job_vert_dpi != vert_dpi or \
                        self.job_page_size != page_size or \
                        self.job_resolution != resolution or \
                        self.job_encoding != encoding:

                        log.error("Incompatible options for file: %s" % fax_file_name)
                        self.results[fax_file_name] = ERROR_FAX_INCOMPATIBLE_OPTIONS
                        state = STATE_ERROR


                log.debug("Magic=%s Ver=%d Pages=%d hDPI=%d vDPI=%d Size=%d Res=%d Enc=%d" %
                          (magic, version, total_pages, hort_dpi,
                           vert_dpi, page_size, resolution, encoding))

                self.job_total_pages += total_pages

                fax_file_fd.close()

            else:
                log.error("Unable to find HP Fax file: %s" % fax_file_name)
                self.results[fax_file_name] = ERROR_FAX_FILE_NOT_FOUND
                state = STATE_ERROR
                break

            if self.check_for_cancel():
                state = STATE_ABORTED
                break


        if self.cover_page_present:
            self.job_total_pages += 1 # Cover pages are truncated to 1 page

        log.debug("Total fax pages=%d" % self.job_total_pages)

        return state

    def decode_fax_header(self, header):
        try:
            return struct.unpack(">8sBIHHBBBII", header)
        except struct.error:
            return -1, -1, -1, -1, -1, -1, -1, -1, -1, -1

    def decode_page_header(self, header):
        try:
            return struct.unpack(">IIIIII", header)
        except struct.error:
            return -1, -1, -1, -1, -1, -1

    def cover_page(self,  recipient):
        if self.job_total_pages > 1:
            state = STATE_MERGE_FILES
        else:
            state = STATE_SINGLE_FILE

        if self.cover_page_present:
            log.debug("Creating cover page for recipient: %s" % recipient['name'])
            fax_file, canceled = self.render_cover_page(recipient)

            if canceled:
                state = STATE_ABORTED
            elif not fax_file:
                state = STATE_ERROR # timeout
            else:
                self.recipient_file_list.insert(0, (fax_file, "application/hplip-fax",
                                                    "HP Fax", 'Cover Page'))

                log.debug("Cover page G3 file: %s" % fax_file)

                self.results[fax_file] = ERROR_SUCCESS

        return state

    def single_file(self, state):
        state = STATE_SEND_FAX

        log.debug("Processing single file...")
        self.f = self.recipient_file_list[0][0]

        try:
            f_fd = open(self.f, 'rb')
        except IOError:
            log.error("Unable to open fax file: %s" % self.f)
            state = STATE_ERROR
        else:
            header = f_fd.read(FILE_HEADER_SIZE)

            magic, version, total_pages, hort_dpi, vert_dpi, page_size, \
                resolution, encoding, reserved1, reserved2 = self.decode_fax_header(header)

            self.results[self.f] = ERROR_SUCCESS

            if magic != b'hplip_g3':
                log.error("Invalid file header. Bad magic.")
                self.results[self.f] = ERROR_FAX_INVALID_FAX_FILE
                state = STATE_ERROR

            log.debug("Magic=%s Ver=%d Pages=%d hDPI=%d vDPI=%d Size=%d Res=%d Enc=%d" %
                      (magic, version, total_pages, hort_dpi, vert_dpi,
                       page_size, resolution, encoding))

            f_fd.close()

        return state


    def merge_files(self, state):
        log.debug("%s State: Merge multiple files" % ("*"*20))
        log.debug(self.recipient_file_list)
        log.debug("Merging g3 files...")
        self.remove_temp_file = True

        if self.job_total_pages:
            f_fd, self.f = utils.make_temp_file()
            log.debug("Temp file=%s" % self.f)

            data = struct.pack(">8sBIHHBBBII", b"hplip_g3", to_long(1), self.job_total_pages,
                self.job_hort_dpi, self.job_vert_dpi, self.job_page_size,
                self.job_resolution, self.job_encoding,
                to_long(0), to_long(0))

            os.write(f_fd, data)

            job_page_num = 1

            for fax_file in self.recipient_file_list:
                fax_file_name = fax_file[0]
                log.debug("Processing file: %s..." % fax_file_name)

                if self.results[fax_file_name] == ERROR_SUCCESS:
                    fax_file_fd = open(fax_file_name, 'rb')
                    header = fax_file_fd.read(FILE_HEADER_SIZE)

                    magic, version, total_pages, hort_dpi, vert_dpi, page_size, \
                        resolution, encoding, reserved1, reserved2 = self.decode_fax_header(header)

                    if magic != b'hplip_g3':
                        log.error("Invalid file header. Bad magic.")
                        state = STATE_ERROR
                        break

                    log.debug("Magic=%s Ver=%d Pages=%d hDPI=%d vDPI=%d Size=%d Res=%d Enc=%d" %
                              (magic, version, total_pages, hort_dpi, vert_dpi, page_size, resolution, encoding))

                    for p in range(total_pages):
                        header = fax_file_fd.read(PAGE_HEADER_SIZE)

                        page_num, ppr, rpp, bytes_to_read, thumbnail_bytes, reserved2 = \
                            self.decode_page_header(header)

                        if page_num == -1:
                            log.error("Page header error")
                            state - STATE_ERROR
                            break

                        header = struct.pack(">IIIIII", job_page_num, ppr, rpp, bytes_to_read, thumbnail_bytes, to_long(0))
                        os.write(f_fd, header)

                        self.write_queue((STATUS_PROCESSING_FILES, job_page_num, ''))

                        log.debug("Page=%d PPR=%d RPP=%d BPP=%d Thumb=%s" %
                                  (page_num, ppr, rpp, bytes_to_read, thumbnail_bytes))

                        os.write(f_fd, fax_file_fd.read(bytes_to_read))
                        job_page_num += 1

                    fax_file_fd.close()

                    if self.check_for_cancel():
                        state = STATE_ABORTED
                        break

                else:
                    log.error("Skipping file: %s" % fax_file_name)
                    continue

            os.close(f_fd)
            log.debug("Total pages=%d" % self.job_total_pages)

        return state


    def next_recipient_gen(self):
        for a in self.phone_num_list:
            yield a

    def next_file_gen(self):
        for a in self.recipient_file_list:
            yield a


    def render_file(self, path, title, mime_type, force_single_page=False):
        all_pages = True
        page_range = ''
        page_set = 0
        nup = 1

        cups.resetOptions()

        if mime_type in ["application/x-cshell",
                         "application/x-perl",
                         "application/x-python",
                         "application/x-shell",
                         "application/x-sh",
                         "text/plain",]:

            cups.addOption('prettyprint')

        if nup > 1:
            cups.addOption('number-up=%d' % nup)

        if force_single_page:
            cups.addOption('page-ranges=1') # Force coverpage to 1 page

        sent_job_id = cups.printFile(self.current_printer, path, title)
        cups.resetOptions()

        log.debug("Job ID=%d" % sent_job_id)
        job_id = 0

        time.sleep(1)

        fax_file = ''
        complete = False

        end_time = time.time() + 300.0 # wait for 5 min. max
        while time.time() < end_time:
            log.debug("Waiting for fax... type =%s"%type(self.dev.device_uri))

            result = list(self.service.CheckForWaitingFax(self.dev.device_uri, prop.username, sent_job_id))

            fax_file = str(result[7])
            log.debug("Fax file=%s" % fax_file)

            if fax_file:
                break

            if self.check_for_cancel():
                log.error("Render canceled. Canceling job #%d..." % sent_job_id)
                cups.cancelJob(sent_job_id)
                return '', True

            time.sleep(1)

        else:
            log.error("Timeout waiting for rendering. Canceling job #%d..." % sent_job_id)
            cups.cancelJob(sent_job_id)
            return '', False

        return fax_file, False


    def check_for_cancel(self):
        canceled = False
        while self.event_queue.qsize():
            try:
                event = self.event_queue.get(0)
                if event[0] == EVENT_FAX_SEND_CANCELED:
                    canceled = True
                    log.debug("Cancel pressed!")
            except Queue.Empty:
                break

        return canceled

    def render_cover_page(self, a):
        log.debug("Creating cover page...")

        #Read file again just before creating the coverpage, so that we get updated voice_phone and email_address from /hplip.conf file
        #hplip.conf file get updated, whenever user changes coverpage info from hp-faxsetup window.
        user_conf.read()

        pdf = self.cover_func(page_size=coverpages.PAGE_SIZE_LETTER,
                              total_pages=self.job_total_pages,

                              recipient_name=a['name'],
                              recipient_phone='', # ???
                              recipient_fax=a['fax'],

                              sender_name=self.sender_name,
                              sender_phone=user_conf.get('fax', 'voice_phone'),
                              sender_fax=self.sender_fax,
                              sender_email=user_conf.get('fax', 'email_address'),

                              regarding=self.cover_re,
                              message=self.cover_message,
                              preserve_formatting=self.preserve_formatting)

        log.debug("PDF File=%s" % pdf)
        fax_file, canceled = self.render_file(pdf, 'Cover Page', "application/pdf",
            force_single_page=True)

        try:
            os.remove(pdf)
        except IOError:
            pass

        return fax_file, canceled


    def write_queue(self, message):
        if self.update_queue is not None and message != self.prev_update:
            self.update_queue.put(message)
            time.sleep(0)
            self.prev_update = message


    def run(self):
        pass



