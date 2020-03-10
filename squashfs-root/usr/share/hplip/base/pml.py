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
import sys
import struct

# Local
from .g import *
from .utils import printable
from .utils import unprintable
from .sixext import to_bytes_utf8, to_unicode, to_bytes_latin, PY3, to_string_latin

# Request codes
GET_REQUEST = 0x00
GET_NEXT_REQUEST = 0x01
GET_BLOCK_REQUEST = 0x02
GET_NEXT_BLOCK_REQUEST = 0x03
SET_REQUEST = 0x04
ENABLE_TRAP_REQUEST = 0x05
DISABLE_TRAP_REQUEST = 0x06
TRAP_REQUEST = 0x07

# Reply codes
GET_REPLY = 0x80
GET_NEXT_REPLY = 0x81
BLOCK_REPLY = 0x82
NEXT_BLOCK_REPLY = 0x83
SET_REPLY = 0x84
ENABLE_TRAP_REPLY = 0x85
DISABLE_TRAP_REPLY = 0x85

# PML Reply error codes
ERROR_OK = 0x00
ERROR_OK_END_OF_SUPPORTED_OBJECTS = 0x01
ERROR_OK_NEAREST_LEGAL_VALUE_SUBSITUTED = 0x02
ERROR_MAX_OK = 0x7f
ERROR_UNKNOWN_REQUEST = 0x80
ERROR_BUFFER_OVERFLOW = 0x81
ERROR_COMMAND_EXECUTION = 0x82
ERROR_UNKNOWN_OID = 0x83
ERROR_OBJ_DOES_NOT_SUPPORT_SPECIFIED_ACTION = 0x84
ERROR_INVALID_OR_UNSUPPORTED_VALUE = 0x85
ERROR_PAST_END_OF_SUPPORTED_OBJS = 0x86
ERROR_ACTION_CANNOT_BE_PERFORMED_NOW = 0x87
ERROR_SYNTAX = 0x88

# Data types
TYPE_MASK = 0xfc
TYPE_OBJECT_IDENTIFIER = 0x00
TYPE_ENUMERATION = 0x04
TYPE_SIGNED_INTEGER = 0x08
TYPE_REAL = 0x0C
TYPE_STRING = 0x10
TYPE_BINARY = 0x14
TYPE_ERROR_CODE = 0x18
TYPE_NULL_VALUE = 0x1c
TYPE_COLLECTION = 0x20
TYPE_UNKNOWN = 0xff

# Misc. constants
MAX_VALUE_LEN = 1023
MAX_OID_LEN = 32
MAX_DATALEN = 4096

# desired_int_sizes
INT_SIZE_BYTE = struct.calcsize('b')
INT_SIZE_WORD = struct.calcsize('h')
INT_SIZE_INT = struct.calcsize('i')


def buildPMLGetPacket(oid): # String dotted notation
    oid = ''.join([chr(int(b.strip())) for b in oid.split('.')])
    return struct.pack('>BBB%ss' % len(oid),
                        GET_REQUEST,
                        TYPE_OBJECT_IDENTIFIER,
                        len(oid), oid)

def buildPMLGetPacketEx(oid): # OID identifier dict
    return buildPMLGetPacket(oid['oid'])

def buildEmbeddedPMLSetPacket(oid, value, data_type):
    return to_bytes_utf8('').join([to_bytes_utf8('PML\x20'), buildPMLSetPacket(oid, value, data_type)])

def buildPMLSetPacket(oid, value, data_type): # String dotted notation
    oid = ''.join([chr(int(b.strip())) for b in oid.split('.')])

    if data_type in (TYPE_ENUMERATION, TYPE_SIGNED_INTEGER, TYPE_COLLECTION):
        data = struct.pack(">i", int(value))

        if value > 0:
            while len(data) > 0 and data[0] == '\x00':
                data = data[1:]
        else:
            while len(data) > 1 and data[0] == '\xff' and data[1] == '\xff':
                data = data[1:]

        data = struct.pack(">BB%ds" % len(data), data_type, len(data), data)

    elif data_type == TYPE_REAL:
        data = struct.pack(">BBf", data_type, struct.calcsize("f"), float(value))

    elif data_type == TYPE_STRING:
        data = struct.pack(">BBBB%ss" % len(value), data_type, len(value) + 2, 0x01, 0x15, value)

    elif data_type == TYPE_BINARY:
        data = struct.pack(">BB%ss" % len(value), data_type, len(value), ''.join([chr(x) for x in value]))

    p = struct.pack('>BBB%ss%ss' % (len(oid), len(data)),
                    SET_REQUEST,
                    TYPE_OBJECT_IDENTIFIER,
                    len(oid), to_bytes_utf8(oid),
                    data)
    return p

def ConvertToPMLDataFormat(value, data_type):
    if data_type in (TYPE_ENUMERATION, TYPE_SIGNED_INTEGER, TYPE_COLLECTION):
        data = struct.pack(">i", int(value))

        if value > 0:
            while len(data) > 0 and data[0] == '\x00':
                data = data[1:]
        else:
            while len(data) > 1 and data[0] == '\xff' and data[1] == '\xff':
                data = data[1:]

        data = struct.pack(">%ds" % len(data), data)

    elif data_type == TYPE_REAL:
        data = struct.pack(">f", float(value))

    elif data_type == TYPE_STRING:
        #For PY2: If data is in unicode, converting to string (e.g Fax Name)
        #For PY3: If data is in string, converting to bytes
        try:
            value = value.encode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            value = value

        data = struct.pack(">BB%ss" % len(value), 0x00, 0x0e, value) # changed for K80, seems to work on others...

    elif data_type == TYPE_BINARY:
        if type(value) == type(''):
            data = value
        elif type(value) == type([]):
            data = struct.pack(">%ds" % len(value), ''.join([chr(x) for x in value]))
        else:
            log.error("Value type error.")

    return data

def ConvertFromPMLDataFormat(data, data_type, desired_int_size=INT_SIZE_INT):
    if data_type in (TYPE_ENUMERATION, TYPE_SIGNED_INTEGER, TYPE_COLLECTION):
        if len(data):
            if data[0] == b'\xff':
                while len(data) < 4:
                    data = b'\xff' + data

            else:
                while len(data) < 4:
                    data = b'\x00' + data

            if desired_int_size == INT_SIZE_INT:
                return struct.unpack(">i", data)[0]

            elif desired_int_size == INT_SIZE_WORD:
                return struct.unpack(">h", data[len(INT_SIZE_WORD)-INT_SIZE_WORD:len(INT_SIZE_WORD)])[0]

            elif desired_int_size == INT_SIZE_BYTE:
                return struct.unpack(">b", data[len(data)-INT_SIZE_BYTE:len(data)])[0]

            else:
                raise Error(ERROR_INTERNAL)

        else:
            return 0

    elif data_type == TYPE_REAL:
        if len(data) == struct.calcsize("f"):
            return struct.unpack(">f", data)[0]
        else:
            return 0.0

    elif data_type == TYPE_STRING:
        if PY3:
            return to_string_latin(b''.join([to_bytes_latin(chr(c)) for c in data if to_bytes_latin(chr(c)) not in unprintable]))
        else:
            return ''.join([c for c in data if c not in unprintable])

    elif data_type == TYPE_BINARY:
        return to_string_latin(data)

    return None


def parsePMLPacket(p, expected_data_type=TYPE_UNKNOWN):
    pos, state = 0, 1

    data_type = TYPE_UNKNOWN
    error_state = False
    while state:

        if state == 1: # reply and error code
            reply, error_code = struct.unpack(">BB", p[pos : pos + 2])
            state, pos = 2, pos + 2

            if error_code > ERROR_MAX_OK:
                error_state = True

        elif state == 2: # data type and length
            data_type, length = struct.unpack(">BB", p[pos : pos + 2])
            state, pos = 3, pos + 2

            if error_state:

                if expected_data_type in (TYPE_COLLECTION, TYPE_ENUMERATION,
                                    TYPE_SIGNED_INTEGER, TYPE_BINARY):
                    data = 0

                elif expected_data_type == TYPE_REAL:
                    data = 0.0

                else:
                    data = ''

                break

        elif state == 3: # data
            data = p[pos : pos + length]
            state, pos = 0, pos + length

            if data_type == TYPE_OBJECT_IDENTIFIER:
                state = 2
                continue

            elif data_type == TYPE_STRING:
                if length > 0:
                    symbol_set, data = struct.unpack(">H%ss" % (length - 2), data)
                else:
                    data = ''

            elif data_type == TYPE_BINARY:
                data = [ord(b) for b in data]

            elif data_type == TYPE_ENUMERATION:
                if length > 0:
                    data = struct.unpack(">i", "%s%s" % ('\x00' * (4 - length), data))[0]
                else:
                    data = 0

            elif data_type == TYPE_REAL:
                if length > 0:
                    data = struct.unpack(">f", data)[0]
                else:
                    data = 0.0

            elif data_type ==  TYPE_SIGNED_INTEGER:
                if length > 0:
                    pad = '\x00'
                    if ord(data[0]) & 0x80: pad = '\xff' # negative number
                    data = struct.unpack(">i", "%s%s" % (pad * (4 - length), data))[0]
                else:
                    data = 0

            elif data_type == TYPE_COLLECTION:
                if length > 0:
                    data = struct.unpack(">i", "%s%s" % ('\x00' * (4 - length), data))[0]
                else:
                    data = 0

            elif data_type == TYPE_ERROR_CODE:
                data = struct.unpack(">B", data)[0]

            elif data_type == TYPE_NULL_VALUE:
                data = None

            break

    return data, data_type, error_code



def HPToSNMP(oid): # 1.
    return '.'.join(['1.3.6.1.4.1.11.2.3.9.4.2', oid, '0'])

def StdToSNMP(oid): # 2.
    return '.'.join(['1.3.6.1.2.1.43', oid[2:]])

def HRToSNMP(oid): # 3.
    return '.'.join(['1.3.6.1.2.1.25', oid[2:]])

def PMLToSNMP(oid):
    assert len(oid) > 2

    if oid[0] == '0': # 0. means its already in SNMP format (will fail for PML)
        return oid[2:]

    elif oid[0] == '1': # HP MIB
        return HPToSNMP(oid)

    elif oid[0] == '2': # Std MIB
        return StdToSNMP(oid)

    elif oid[0] == '3': # Host Resources MIB
        return HRToSNMP(oid)

    assert False


#
# OIDs
#

OID_DEVICE_ID = ('0.1.3.6.1.4.1.11.2.3.9.1.1.7.0', TYPE_STRING) # network/SNMP only (undocumented)

OID_DEVICE_SUPPORTED_FUNCTIONS = ('1.1.2.67', TYPE_COLLECTION)
DEVICE_SUPPORTED_FUNCTIONS_SCAN =                 0x00002
DEVICE_SUPPORTED_FUNCTIONS_SCAN_SIMPLEX =         0x00004
DEVICE_SUPPORTED_FUNCTIONS_SCAN_DUPLEX =          0x00008
DEVICE_SUPPORTED_FUNCTIONS_COPY =                 0x00010
DEVICE_SUPPORTED_FUNCTIONS_COPY_SIMPLEX_SIMPLEX = 0x00020
DEVICE_SUPPORTED_FUNCTIONS_COPY_SIMPLEX_DUPLEX =  0x00040
DEVICE_SUPPORTED_FUNCTIONS_COPY_DUPLEX_SIMPLEX =  0x00080
DEVICE_SUPPORTED_FUNCTIONS_COPY_DUPLEX_DUPLEX =   0x00100
DEVICE_SUPPORTED_FUNCTIONS_COPY_COLLATION =       0x00200
DEVICE_SUPPORTED_FUNCTIONS_PRINT =                0x00400
DEVICE_SUPPORTED_FUNCTIONS_AUTO_FEED_SIMPLEX =    0x00800
DEVICE_SUPPORTED_FUNCTIONS_AUTO_FEED_DUPLEX =     0x01000
DEVICE_SUPPORTED_FUNCTIONS_FAX_SEND =             0x02000
DEVICE_SUPPORTED_FUNCTIONS_FAX_RECV =             0x04000
DEVICE_SUPPORTED_FUNCTIONS_MASS_STORAGE =         0x08000
DEVICE_SUPPORTED_FUNCTIONS_STREAMING_SAVE =       0x10000
DEVICE_SUPPORTED_FUNCTIONS_FAX_CONFIG =           0x20000
DEVICE_SUPPORTED_FUNCTIONS_FAX_CFG_SPEEDDIAL =    0x40000
DEVICE_SUPPORTED_FUNCTIONS_FAX_CFG_GROUPDIAL =    0x80000

OID_CLEAN = ('1.4.1.5.1.1', TYPE_ENUMERATION)
CLEAN_CLEAN = 100
CLEAN_PRIME = 200
CLEAN_WIPE_AND_SPIT = 300

OID_SERIAL_NUMBER = ('1.1.3.3', TYPE_STRING)
OID_R_SETTING = ('1.1.1.35', TYPE_SIGNED_INTEGER)

OID_PRINT_INTERNAL_PAGE = ('1.1.5.2', TYPE_ENUMERATION)
PRINT_INTERNAL_PAGE_SUPPLIES_PAGE = 101
PRINT_INTERNAL_PAGE_COLOR_PALETTE_CMYK_PAGE = 259
PRINT_INTERNAL_PAGE_COLOR_CAL = 1102
PRINT_INTERNAL_PAGE_COLOR_CAL_VERIFICATION = 1104
PRINT_INTERNAL_PAGE_ALIGNMENT_PAGE = 1100 # LBOW/OJ Pro L7xxx
PRINT_INTERNAL_PAGE_ALIGNMENT_PAGE_VERIFICATION = 1150 # LBOW
PRINT_INTERNAL_PAGE_LINEFEED_CALIBRATION = 1407 # OJ Pro
PRINT_INTERNAL_PAGE_AUTOMATIC_COLOR_CALIBRATION = 1408 # PS Pro B8800
PRINT_INTERNAL_PAGE_PRINT_QUALITY_DIAGNOSTIC = 1409 # OJ Pro

# From xojpanel
OID_SPM_LINE1 = ('2.16.5.1.2.1.1', TYPE_STRING)
OID_SPM_LINE2 = ('2.16.5.1.2.1.2', TYPE_STRING)

OID_HP_LINE1 = ('1.1.2.20.2.1.1', TYPE_STRING)
OID_HP_LINE2 = ('1.1.2.20.2.2.1', TYPE_STRING)


# LaserJet Status (status type 3)
OID_ON_OFF_LINE = ('1.1.2.5', TYPE_SIGNED_INTEGER)
ON_OFF_LINE_ONLINE = 1
ON_OFF_LINE_OFFLINE = 2
ON_OFF_LINE_OFFLINE_AT_END_OF_JOB = 3

OID_SLEEP_MODE = ('1.1.1.2', TYPE_SIGNED_INTEGER)
SLEEP_MODE_FALSE = 1
SLEEP_MODE_TRUE = 2

OID_PRINTER_STATUS = ('3.3.5.1.1.1', TYPE_SIGNED_INTEGER)
PRINTER_STATUS_OTHER = 1
PRINTER_STATUS_UNKNOWN = 2
PRINTER_STATUS_IDLE = 3
PRINTER_STATUS_PRINTING = 4
PRINTER_STATUS_WARMUP = 5

OID_COVER_STATUS = ('2.6.1.1.3.1.1', TYPE_SIGNED_INTEGER)
COVER_STATUS_OPEN = 3
COVER_STATUS_CLOSED = 4

OID_DETECTED_ERROR_STATE = ('3.3.5.1.2.1', TYPE_BINARY)
DETECTED_ERROR_STATE_LOW_PAPER_MASK = 0x80
DETECTED_ERROR_STATE_NO_PAPER_MASK = 0x40
DETECTED_ERROR_STATE_LOW_CART_MASK = 0x20
DETECTED_ERROR_STATE_OUT_CART_MASK = 0x10
DETECTED_ERROR_STATE_DOOR_OPEN_MASK = 0x08
DETECTED_ERROR_STATE_JAMMED_MASK = 0x04
DETECTED_ERROR_STATE_OFFLINE_MASK = 0x02
DETECTED_ERROR_STATE_SERVICE_REQUEST_MASK = 0x01
DETECTED_ERROR_STATE_NO_ERROR = 0x00

OID_MARKER_SUPPLIES_TYPE_x = '2.11.1.1.5.1.%d'
OID_MARKER_SUPPLIES_TYPE_x_TYPE = TYPE_ENUMERATION
OID_MARKER_SUPPLIES_TYPE_OTHER = 1
OID_MARKER_SUPPLIES_TYPE_UNKNOWN = 2
OID_MARKER_SUPPLIES_TYPE_TONER = 3
OID_MARKER_SUPPLIES_TYPE_WASTE_TONER = 4
OID_MARKER_SUPPLIES_TYPE_INK = 5
OID_MARKER_SUPPLIES_TYPE_INK_CART = 6
OID_MARKER_SUPPLIES_TYPE_INK_RIBBON = 7
OID_MARKER_SUPPLIES_TYPE_WASTE_INK = 8
OID_MARKER_SUPPLIES_TYPE_OPC = 9
OID_MARKER_SUPPLIES_TYPE_DEVELOPER = 10
OID_MARKER_SUPPLIES_TYPE_FUSER_OIL = 11
OID_MARKER_SUPPLIES_TYPE_SOLID_WAX = 12
OID_MARKER_SUPPLIES_TYPE_RIBBON_WAX = 13
OID_MARKER_SUPPLIES_TYPE_WASTE_WAX = 14
OID_MARKER_SUPPLIES_TYPE_FUSER = 15
OID_MARKER_SUPPLIES_TYPE_CORONA_WIRE = 16
OID_MARKER_SUPPLIES_TYPE_FUSER_OIL_WICK = 17
OID_MARKER_SUPPLIES_TYPE_CLEANER_UNIT = 18
OID_MARKER_SUPPLIES_TYPE_FUSER_CLEANING_PAD = 19
OID_MARKER_SUPPLIES_TYPE_TRANSFER_UNIT = 20
OID_MARKER_SUPPLIES_TYPE_TONER_CART = 21
OID_MARKER_SUPPLIES_TYPE_FUSER_OILER = 22
OID_MARKER_SUPPLIES_TYPE_ADF_MAINT_KIT = 23

OID_MARKER_SUPPLIES_COLORANT_INDEX_x = '2.11.1.1.3.1.%d'
OID_MARKER_SUPPLIES_COLORANT_INDEX_x_TYPE = TYPE_SIGNED_INTEGER

OID_MARKER_SUPPLIES_MAX_x = '2.11.1.1.8.1.%d'
OID_MARKER_SUPPLIES_MAX_x_TYPE = TYPE_SIGNED_INTEGER

OID_MARKER_SUPPLIES_LEVEL_x = '2.11.1.1.9.1.%d'
OID_MARKER_SUPPLIES_LEVEL_x_TYPE = TYPE_SIGNED_INTEGER

OID_MARKER_COLORANT_VALUE_x = '2.12.1.1.4.1.%d'
OID_MARKER_COLORANT_VALUE_x_TYPE = TYPE_STRING

OID_MARKER_STATUS_x = '2.10.2.1.15.1.%d'
OID_MARKER_STATUS_x_TYPE = TYPE_SIGNED_INTEGER
OID_MARKER_STATUS_OK = 0
OID_MARKER_STATUS_LOW_TONER_CONT = 8
OID_MARKER_STATUS_LOW_TONER_STOP = 49
OID_MARKER_STATUS_MISINSTALLED = 51

OID_MARKER_SUPPLIES_DESCRIPTION_x = '2.11.1.1.6.1.%d'
OID_MARKER_SUPPLIES_DESCRIPTION_x_TYPE = TYPE_BINARY

OID_DEVICE_STATUS = ('3.3.2.1.5.1', TYPE_ENUMERATION)
DEVICE_STATUS_UNKNOWN = 1
DEVICE_STATUS_RUNNING = 2
DEVICE_STATUS_WARNING = 3
DEVICE_STATUS_TESTING = 4
DEVICE_STATUS_DOWN = 5
#end

# alignment, cleaning, etc.
OID_AUTO_ALIGNMENT = ('1.1.5.2', TYPE_ENUMERATION)
AUTO_ALIGNMENT = 1100
OID_ZCA = ('1.4.1.8.5.4.1', TYPE_SIGNED_INTEGER)
OID_AGENT2_VERTICAL_ALIGNMENT = ('1.4.1.5.3.2.5', TYPE_SIGNED_INTEGER)
OID_AGENT2_HORIZONTAL_ALIGNMENT = ('1.4.1.5.3.2.6', TYPE_SIGNED_INTEGER)
OID_AGENT1_BIDIR_ADJUSTMENT = ('1.4.1.5.3.1.7', TYPE_SIGNED_INTEGER)
OID_AGENT2_BIDIR_ADJUSTMENT = ('1.4.1.5.3.2.7', TYPE_SIGNED_INTEGER)
OID_MARKING_AGENTS_INITIALIZED = ('1.4.1.5.1.4', TYPE_COLLECTION)
OID_AGENT3_VERTICAL_ALIGNMENT = ("1.4.1.5.3.3.5", TYPE_SIGNED_INTEGER)
OID_AGENT3_HORIZONTAL_ALIGNMENT = ("1.4.1.5.3.3.6", TYPE_SIGNED_INTEGER)
OID_AGENT3_BIDIR_ADJUSTMENT = ("1.4.1.5.3.3.7", TYPE_SIGNED_INTEGER)
OID_COLOR_CALIBRATION_SELECTION = ("1.4.1.5.1.9", TYPE_SIGNED_INTEGER)

# Type 4 color cal
OID_COLOR_CALIBRATION_ARRAY_1 = ("1.4.1.1.30.1.1", TYPE_SIGNED_INTEGER) # K
OID_COLOR_CALIBRATION_ARRAY_2 = ("1.4.1.1.30.1.2", TYPE_SIGNED_INTEGER) # C
OID_COLOR_CALIBRATION_ARRAY_3 = ("1.4.1.1.30.1.3", TYPE_SIGNED_INTEGER) # M
OID_COLOR_CALIBRATION_ARRAY_4 = ("1.4.1.1.30.1.4", TYPE_SIGNED_INTEGER) # Y
OID_COLOR_CALIBRATION_ARRAY_5 = ("1.4.1.1.30.1.5", TYPE_SIGNED_INTEGER) # c
OID_COLOR_CALIBRATION_ARRAY_6 = ("1.4.1.1.30.1.6", TYPE_SIGNED_INTEGER) # m

# Supported funcs
OID_DEVICE_SUPPORTED_FUNCTIONS = ('1.1.2.67', TYPE_COLLECTION)
DEVICE_SUPPORTED_FUNCTIONS_SCAN =                 0x00002
DEVICE_SUPPORTED_FUNCTIONS_SCAN_SIMPLEX =         0x00004
DEVICE_SUPPORTED_FUNCTIONS_SCAN_DUPLEX =          0x00008
DEVICE_SUPPORTED_FUNCTIONS_COPY =                 0x00010
DEVICE_SUPPORTED_FUNCTIONS_COPY_SIMPLEX_SIMPLEX = 0x00020
DEVICE_SUPPORTED_FUNCTIONS_COPY_SIMPLEX_DUPLEX =  0x00040
DEVICE_SUPPORTED_FUNCTIONS_COPY_DUPLEX_SIMPLEX =  0x00080
DEVICE_SUPPORTED_FUNCTIONS_COPY_DUPLEX_DUPLEX =   0x00100
DEVICE_SUPPORTED_FUNCTIONS_COPY_COLLATION =       0x00200
DEVICE_SUPPORTED_FUNCTIONS_PRINT =                0x00400
DEVICE_SUPPORTED_FUNCTIONS_AUTO_FEED_SIMPLEX =    0x00800
DEVICE_SUPPORTED_FUNCTIONS_AUTO_FEED_DUPLEX =     0x01000
DEVICE_SUPPORTED_FUNCTIONS_FAX_SEND =             0x02000
DEVICE_SUPPORTED_FUNCTIONS_FAX_RECV =             0x04000
DEVICE_SUPPORTED_FUNCTIONS_MASS_STORAGE =         0x08000
DEVICE_SUPPORTED_FUNCTIONS_STREAMING_SAVE =       0x10000
DEVICE_SUPPORTED_FUNCTIONS_FAX_CONFIG =           0x20000
DEVICE_SUPPORTED_FUNCTIONS_FAX_CFG_SPEEDDIAL =    0x40000
DEVICE_SUPPORTED_FUNCTIONS_FAX_CFG_GROUPDIAL =    0x80000


OID_BATTERY_LEVEL = ('1.1.2.13', TYPE_SIGNED_INTEGER)
OID_POWER_MODE = ('1.1.2.14', TYPE_ENUMERATION)
POWER_MODE_ADPATER = 0x01
POWER_MODE_BATTERY = 0x02
POWER_MODE_CHARGING = 0x04
POWER_MODE_DISCHARGING = 0x08
POWER_MODE_BATTERY_LEVEL_KNOWN = 0x10

OID_BATTERY_LEVEL_2 = ('1.1.2.61', TYPE_SIGNED_INTEGER)

OID_POWER_SETTINGS = ('1.1.2.118', TYPE_ENUMERATION)
OID_POWER_SETTINGS_15MIN = 1
OID_POWER_SETTINGS_30MIN = 2
OID_POWER_SETTINGS_45MIN = 3
OID_POWER_SETTINGS_1HR = 4
OID_POWER_SETTINGS_2HR = 5
OID_POWER_SETTINGS_3HR = 6
OID_POWER_SETTINGS_NEVER = 999

#
# Fax
#

OID_DEV_DOWNLOAD_TIMEOUT = ('1.1.1.17', TYPE_SIGNED_INTEGER)
DEFAULT_DOWNLOAD_TIMEOUT = 600

OID_FAX_DOWNLOAD_ERROR = ('1.3.7.2.6', TYPE_SIGNED_INTEGER)

OID_FAXJOB_TX_TYPE = ('1.1.6.3.1.3', TYPE_ENUMERATION)
FAXJOB_TX_TYPE_HOST_ONLY = 2

OID_FAXJOB_TX_STATUS = ('1.1.6.3.3.3.1', TYPE_ENUMERATION)
FAXJOB_TX_STATUS_IDLE = 1
FAXJOB_TX_STATUS_DIALING = 2
FAXJOB_TX_STATUS_CONNECTING = 3
FAXJOB_TX_STATUS_TRANSMITTING = 4
FAXJOB_TX_STATUS_DONE = 5

FAXJOB_TX_STATUS_STR = {FAXJOB_TX_STATUS_IDLE: "Idle",
                 FAXJOB_TX_STATUS_DIALING: "Dialing",
                 FAXJOB_TX_STATUS_CONNECTING: "Connecting",
                 FAXJOB_TX_STATUS_TRANSMITTING: "Transmitting",
                 FAXJOB_TX_STATUS_DONE: "Done",}

OID_FAXJOB_RX_STATUS = ('1.1.6.3.3.1.1', TYPE_ENUMERATION)
FAXJOB_RX_STATUS_IDLE = 1
FAXJOB_RX_STATUS_RINGING = 2
FAXJOB_RX_STATUS_ANSWERING = 3
FAXJOB_RX_STATUS_RECEIVING = 4
FAXJOB_RX_STATUS_DONE = 5

FAXJOB_RX_STATUS_STR = {FAXJOB_RX_STATUS_IDLE: "Idle",
                        FAXJOB_RX_STATUS_RINGING: "Ringing",
                        FAXJOB_RX_STATUS_ANSWERING: "Answering",
                        FAXJOB_RX_STATUS_RECEIVING: "Receiving",
                        FAXJOB_RX_STATUS_DONE: "Done",}

OID_FAX_DOWNLOAD = ('1.3.7.1.6', TYPE_ENUMERATION)
UPDN_STATE_IDLE = 1
UPDN_STATE_REQSTART = 2
UPDN_STATE_XFERACTIVE = 3
UPDN_STATE_ERRORABORT = 4
UPDN_STATE_XFERDONE = 5
UPDN_STATE_NEWPAGE = 6
UPDN_STATE_DISABLED = 7

UPDN_STATE_STR = {UPDN_STATE_IDLE: "Idle",
                  UPDN_STATE_REQSTART: "Request start",
                  UPDN_STATE_XFERACTIVE: "Transfer active",
                  UPDN_STATE_ERRORABORT: "Error abort",
                  UPDN_STATE_XFERDONE: "Transfer done",
                  UPDN_STATE_NEWPAGE: "New page",
                  UPDN_STATE_DISABLED: "Disabled",}

# Fax download errors (taken from doc/Fax/WindowsFax/sdcore/DevIO/DevIODefs.h)
#
DN_ERROR_NONE = 0
DN_ERROR_HOST_ABORT = 705
DN_ERROR_STOP_KEY_PRESSED = 706
DN_ERROR_SESSION_FAIL = 709
DN_ERROR_TX_ERROR = 710
DN_ERROR_PHONE_UNAVAILABLE = 711
DN_ERROR_OUT_OF_MEMORY = 713
DN_ERROR_RESULT_BUSY = 714
DN_ERROR_NO_ANSWER = 715
DN_ERROR_NO_DIAL_TONE = 716
DN_ERROR_DOC_JAM = 717
DN_ERROR_DOOR_OPEN = 718
DN_ERROR_POWER_FAILED = 719
DN_ERROR_BLACKLIST = 720
DN_ERROR_DOC_STORAGE_FULL = 721
DN_ERROR_RESULT_COLOR_UNSUP = 722
DN_ERROR_UNKNOWN = 9999

DN_ERROR_STR = {DN_ERROR_NONE: "None",
                DN_ERROR_HOST_ABORT: "Host aborted",
                DN_ERROR_STOP_KEY_PRESSED: "Stop key pressed",
                DN_ERROR_SESSION_FAIL: "Session failed",
                DN_ERROR_TX_ERROR: "Transmit error",
                DN_ERROR_PHONE_UNAVAILABLE: "Phone unavailable",
                DN_ERROR_OUT_OF_MEMORY: "Out of memory",
                DN_ERROR_RESULT_BUSY: "Result busy",
                DN_ERROR_NO_ANSWER: "No answer",
                DN_ERROR_NO_DIAL_TONE: "No dial tone",
                DN_ERROR_DOC_JAM: "Document jammed",
                DN_ERROR_DOOR_OPEN: "Door open",
                DN_ERROR_POWER_FAILED: "Power failed",
                DN_ERROR_BLACKLIST: "Blacklisted",
                DN_ERROR_DOC_STORAGE_FULL: "Document storage full",
                DN_ERROR_RESULT_COLOR_UNSUP: "Color unsupported",
                DN_ERROR_UNKNOWN: "Unknown error"}

OID_FAX_TOKEN = ('1.1.1.27', TYPE_BINARY)

OID_FAX_TX_ID = ('1.1.6.3.2.3', TYPE_SIGNED_INTEGER)
OID_FAXJOB_TX_ERROR = ('1.1.6.3.3.4.1', TYPE_SIGNED_INTEGER)

OID_FAX_LOCAL_PHONE_NUM = ('1.1.3.8', TYPE_STRING)
OID_FAX_STATION_NAME = ('1.1.3.9', TYPE_STRING)
OID_FAX_LINE_TYPE = ('1.3.7.1.16', TYPE_ENUMERATION)
OID_FAX_ANSWERMODE = ('1.1.9.2.1.1', TYPE_ENUMERATION)
OID_FAX_RING_ENABLE = ('1.3.7.1.8', TYPE_ENUMERATION)
OID_FAX_NUM_RINGS_PICKUP = ('1.1.9.2.1.2', TYPE_SIGNED_INTEGER)
OID_FAX_MIN_RINGS_PICKUP = ('1.3.7.2.2', TYPE_SIGNED_INTEGER)
OID_FAX_MAX_RINGS_PICKUP = ('1.3.7.2.3', TYPE_SIGNED_INTEGER)
OID_FAX_RING_TYPE_PICKUP = ('1.1.9.2.1.3', TYPE_COLLECTION)
OID_FAX_DIAL_MODE = ('1.1.9.1.1.1', TYPE_ENUMERATION)
OID_FAX_ALLOW_REDIALS = ('1.4.2.5.3', TYPE_ENUMERATION)
OID_FAX_REDIAL = ('1.1.9.1.1.2', TYPE_COLLECTION)
OID_FAX_RESOLUTION = ('1.4.2.1.1', TYPE_BINARY)
OID_FAX_CONTRAST = ('1.4.2.1.2', TYPE_SIGNED_INTEGER)

#OID_FAX_UPLOAD = ('1.3.7.2.1', TYPE_ENUMERATION)
#OID_FAX_UPLOAD_ERROR = ('1.3.7.2.7', TYPE_SIGNED_INTEGER)

OID_FAX_CFG_UPLOAD_DATA_TYPE = ('1.1.1.14', TYPE_ENUMERATION)
FAX_CFG_UPLOAD_DATA_TYPE_SPEEDDIALS = 5
FAX_CFG_UPLOAD_DATA_TYPE_FAXLOGS = 6
FAX_CFG_UPLOAD_DATA_TYPE_CONFIG_PARAMS = 7
FAX_CFG_UPLOAD_DATA_TYPE_JUNK_FAX_DIAL_STRINGS = 8

OID_UPLOAD_TIMEOUT = ('1.1.1.18', TYPE_SIGNED_INTEGER)
DEFAULT_UPLOAD_TIMEOUT = 60

OID_DEVICE_CFG_UPLOAD = ('1.1.1.13', TYPE_ENUMERATION)

#
# Copier
#

OID_COPIER_TOKEN = ('1.1.1.24', TYPE_BINARY)
OID_COPY_SCANNER_DIMENSIONS = ('1.2.2.2.13', TYPE_STRING)

# Sticky settings
OID_COPIER_CONTRAST = ('1.5.1.2', TYPE_SIGNED_INTEGER) # -125, -100, -75, -50, -25, 0, 25, 50, 75, 100, 125
OID_COPIER_REDUCTION = ('1.5.1.4', TYPE_SIGNED_INTEGER) # (100%=no scaling) (OID_COPIER_FIT_TO_PAGE overrides)
                                                        # range: COPIER-REDUCTION-MAXIMUM (25) - COPIER-ENLARGEMENT-MAXIMUM (400)
OID_COPIER_NUM_COPIES = ('1.5.1.6', TYPE_SIGNED_INTEGER) # 1-99

OID_COPIER_COLLATION = ('1.5.1.7', TYPE_ENUMERATION)
COPIER_COLLATION_DISABLED = 1
COPIER_COLLATION_FORWARD = 2

OID_COPIER_ENLARGEMENT_MAXIMUM = ('1.5.1.11', TYPE_SIGNED_INTEGER) # default 400
OID_COPIER_REDUCTION_MAXIMUM = ('1.5.1.12', TYPE_SIGNED_INTEGER) # default 25

OID_COPIER_QUALITY = ('1.5.1.13', TYPE_ENUMERATION)
COPIER_QUALITY_FAST = 1
COPIER_QUALITY_NORMAL = 2
COPIER_QUALITY_PRESENTATION = 3
COPIER_QUALITY_DRAFT = 4
COPIER_QUALITY_BEST = 5

OID_COPIER_ADF_PAGE_COUNT = ('1.5.1.19', TYPE_SIGNED_INTEGER)
OID_COPIER_PRINT_PAGE_COUNT = ('1.5.1.20', TYPE_SIGNED_INTEGER)

OID_COPIER_FIT_TO_PAGE = ('1.5.1.47', TYPE_ENUMERATION)
COPIER_FIT_TO_PAGE_DISABLED = 1
COPIER_FIT_TO_PAGE_ENABLED = 2

# Job (non-sticky) settings
OID_COPIER_JOB_QUALITY = ('1.5.1.22', TYPE_ENUMERATION)
# use enums from OID_COPIER_QUALITY

OID_COPIER_JOB_MEDIA_SIZE = ('1.5.1.21', TYPE_ENUMERATION)
COPIER_JOB_MEDIA_SIZE_US_LETTER = 2
COPIER_JOB_MEDIA_SIZE_US_LEGAL = 3
COPIER_JOB_MEDIA_SIZE_A4 = 26

OID_COPIER_JOB_COLLATION = ('1.5.1.23', TYPE_ENUMERATION)
# use enums from OID_COPIER_COLLATION

OID_COPIER_JOB_NUM_COPIES = ('1.5.1.24', TYPE_SIGNED_INTEGER)
OID_COPIER_JOB_REDUCTION = ('1.5.1.25', TYPE_SIGNED_INTEGER)
OID_COPIER_JOB_CONTRAST = ('1.5.1.26', TYPE_SIGNED_INTEGER) # -125, -100, -75, -50, -25, 0, 25, 50, 75, 100, 125

OID_COPIER_JOB_FIT_TO_PAGE = ('1.5.1.48', TYPE_ENUMERATION)
# use enums from OID_COPIER_FIT_TO_PAGE

# Copy job

OID_COPIER_JOB = ('1.5.1.27', TYPE_ENUMERATION)
COPIER_JOB_IDLE = 1
COPIER_JOB_START = 2
COPIER_JOB_ACTIVE = 3
COPIER_JOB_ABORTING = 4
COPIER_JOB_SETUP = 5

# AiO Specific Copy

OID_COLOR_COPY_REQUEST = ('1.5.1.8', TYPE_ENUMERATION)
OID_SCAN_TO_PRINTER = ('1.5.1.5', TYPE_SIGNED_INTEGER)
SCAN_TO_PRINTER_IDLE         = 1
SCAN_TO_PRINTER_START        = 2
SCAN_TO_PRINTER_ACTIVE       = 3
SCAN_TO_PRINTER_ABORTED      = 4
SCAN_TO_PRINTER_SET_DEFAULTS = 5
SCAN_TO_PRINTER_GET_DEFAULTS = 6

OID_PIXEL_DATA_TYPE = ('1.5.1.3', TYPE_SIGNED_INTEGER)
PIXEL_DATA_TYPE_GRAYSCALE_256     = 8
PIXEL_DATA_TYPE_COLOR_24_BIT      = 24

OID_COPIER_SPECIAL_FEATURES = ('1.5.1.16', TYPE_SIGNED_INTEGER)
COPY_FEATURE_NONE     = 1
COPY_FEATURE_CLONE    = 2
COPY_FEATURE_POSTER   = 3
COPY_FEATURE_MIRROR   = 4
COPY_FEATURE_AUTOFIT  = 5
COPY_FEATURE_TWOUP    = 6
COPY_FEATURE_AUTOFILL = 7


OID_COPIER_PHOTO_MODE = ('1.5.1.15', TYPE_COLLECTION)
ENHANCE_LIGHT_COLORS  =  0x00000001  # Bit  0
ENHANCE_TEXT          =  0x00000002  # Bit  1

OID_COPIER_NUM_COPIES_AIO = ('1.5.1.6', TYPE_SIGNED_INTEGER)
OID_COPIER_CONTRAST_AIO = ('1.5.1.2', TYPE_SIGNED_INTEGER)
OID_COPIER_REDUCTION_AIO = ('1.5.1.4', TYPE_SIGNED_INTEGER)
OID_COPIER_QUALITY_AIO = ('1.5.1.13', TYPE_ENUMERATION)

OID_COPIER_JOB_INPUT_TRAY_SELECT = ('1.5.1.51', TYPE_SIGNED_INTEGER)
COPIER_JOB_INPUT_TRAY_1 = 1
COPIER_JOB_INPUT_TRAY_2 = 1
COPIER_JOB_INPUT_TRAY_3 = 1

OID_COPIER_MEDIA_TYPE = ('1.5.1.14', TYPE_SIGNED_INTEGER)
COPIER_MEDIA_TYPE_PLAIN               = 1
COPIER_MEDIA_TYPE_BRIGHT_WHITE        = 2
COPIER_MEDIA_TYPE_PREMIUM_PHOTO       = 3
COPIER_MEDIA_TYPE_SPECIAL             = 4
COPIER_MEDIA_TYPE_TRANSPARENCY        = 5
COPIER_MEDIA_TYPE_IRON_ON             = 6
COPIER_MEDIA_TYPE_FAST_TRANSPARANCEY  = 7
COPIER_MEDIA_TYPE_BROCHURE_MATTE      = 8
COPIER_MEDIA_TYPE_BROCHURE_GLOSSY     = 9
COPIER_MEDIA_TYPE_PHOTO_GLOSSY        = 10
COPIER_MEDIA_TYPE_MATTE_PAPER         = 11
COPIER_MEDIA_TYPE_EVERYDAY_PHOTO      = 12
COPIER_MEDIA_TYPE_PHOTO_QUAL_INKJET   = 13
COPIER_MEDIA_TYPE_PHOTO               = 14
COPIER_MEDIA_TYPE_AUTOMATIC           = 15
COPIER_MEDIA_TYPE_ADVANCED_PHOTO      = 16
COPIER_MEDIA_TYPE_IRON_ON_MIRRORED    = 17



# Misc

OID_DATE_AND_TIME = ('1.1.2.17', TYPE_BINARY)



