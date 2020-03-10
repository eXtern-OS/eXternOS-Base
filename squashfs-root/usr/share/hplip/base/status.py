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
# Author: Don Welch, Narla Naga Samrat Chowdary, Yashwant Kumar Sahu
#



# Std Lib
import struct
import io
from .sixext import BytesIO, to_bytes_utf8, to_bytes_latin, to_string_latin, to_long

from .g import *
import xml.parsers.expat as expat
import re
import cupsext

try:
    from xml.etree import ElementTree
    etree_loaded = True
except ImportError:
    try:
        from elementtree.ElementTree import XML
        elementtree_loaded = True
    except ImportError:
        elementtree_loaded = False
    etree_loaded = False

# Local
from .g import *
from .codes import *
from . import pml, utils
import hpmudext
"""
status dict structure:
    { 'revision' :     STATUS_REV_00 .. STATUS_REV_04,
      'agents' :       [ list of pens/agents/supplies (dicts) ],
      'top-door' :     TOP_DOOR_NOT_PRESENT | TOP_DOOR_CLOSED | TOP_DOOR_OPEN,
      'status-code' :  STATUS_...,
      'supply-door' :  SUPPLY_DOOR_NOT_PRESENT | SUPPLY_DOOR_CLOSED | SUPPLY_DOOR_OPEN.
      'duplexer' :     DUPLEXER_NOT_PRESENT | DUPLEXER_DOOR_CLOSED | DUPLEXER_DOOR_OPEN,
      'photo_tray' :   PHOTO_TRAY_NOT_PRESENT | PHOTO_TRAY_ENGAGED | PHOTO_TRAY_NOT_ENGAGED,
      'in-tray1' :     IN_TRAY_NOT_PRESENT | IN_TRAY_CLOSED | IN_TRAY_OPEN (| IN_TRAY_DEFAULT | IN_TRAY_LOCKED)*,
      'in-tray2' :     IN_TRAY_NOT_PRESENT | IN_TRAY_CLOSED | IN_TRAY_OPEN (| IN_TRAY_DEFAULT | IN_TRAY_LOCKED)*,
      'media-path' :   MEDIA_PATH_NOT_PRESENT | MEDIA_PATH_CUT_SHEET | MEDIA_PATH_BANNER | MEDIA_PATH_PHOTO,
    }

    * S:02 only

agent dict structure: (pens/supplies/agents/etc)
    { 'kind' :           AGENT_KIND_NONE ... AGENT_KIND_ADF_KIT,
      'type' :           TYPE_BLACK ... AGENT_TYPE_UNSPECIFIED,      # aka color
      'health' :         AGENT_HEALTH_OK ... AGENT_HEALTH_UNKNOWN,
      'level' :          0 ... 100,
      'level-trigger' :  AGENT_LEVEL_TRIGGER_SUFFICIENT_0 ... AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
    }
"""



# 'revision'
STATUS_REV_00 = 0x00
STATUS_REV_01 = 0x01
STATUS_REV_02 = 0x02
STATUS_REV_03 = 0x03
STATUS_REV_04 = 0x04
STATUS_REV_V  = 0xff
STATUS_REV_UNKNOWN = 0xfe

vstatus_xlate  = {'busy' : STATUS_PRINTER_BUSY,
                   'idle' : STATUS_PRINTER_IDLE,
                   'prnt' : STATUS_PRINTER_PRINTING,
                   'offf' : STATUS_PRINTER_TURNING_OFF,
                   'rprt' : STATUS_PRINTER_REPORT_PRINTING,
                   'cncl' : STATUS_PRINTER_CANCELING,
                   'iost' : STATUS_PRINTER_IO_STALL,
                   'dryw' : STATUS_PRINTER_DRY_WAIT_TIME,
                   'penc' : STATUS_PRINTER_PEN_CHANGE,
                   'oopa' : STATUS_PRINTER_OUT_OF_PAPER,
                   'bnej' : STATUS_PRINTER_BANNER_EJECT,
                   'bnmz' : STATUS_PRINTER_BANNER_MISMATCH,
                   'phmz' : STATUS_PRINTER_PHOTO_MISMATCH,
                   'dpmz' : STATUS_PRINTER_DUPLEX_MISMATCH,
                   'pajm' : STATUS_PRINTER_MEDIA_JAM,
                   'cars' : STATUS_PRINTER_CARRIAGE_STALL,
                   'paps' : STATUS_PRINTER_PAPER_STALL,
                   'penf' : STATUS_PRINTER_PEN_FAILURE,
                   'erro' : STATUS_PRINTER_HARD_ERROR,
                   'pwdn' : STATUS_PRINTER_POWER_DOWN,
                   'fpts' : STATUS_PRINTER_FRONT_PANEL_TEST,
                   'clno' : STATUS_PRINTER_CLEAN_OUT_TRAY_MISSING}

REVISION_2_TYPE_MAP = {0 : AGENT_TYPE_NONE,
                        1 : AGENT_TYPE_BLACK,
                        2 : AGENT_TYPE_CYAN,
                        3 : AGENT_TYPE_MAGENTA,
                        4 : AGENT_TYPE_YELLOW,
                        5 : AGENT_TYPE_BLACK,
                        6 : AGENT_TYPE_CYAN,
                        7 : AGENT_TYPE_MAGENTA,
                        8 : AGENT_TYPE_YELLOW,
                       }

STATUS_BLOCK_UNKNOWN = {'revision' : STATUS_REV_UNKNOWN,
                         'agents' : [],
                         'status-code' : STATUS_UNKNOWN,
                       }

NUM_PEN_POS = {STATUS_REV_00 : 16,
                STATUS_REV_01 : 16,
                STATUS_REV_02 : 16,
                STATUS_REV_03 : 18,
                STATUS_REV_04 : 22}

PEN_DATA_SIZE = {STATUS_REV_00 : 8,
                  STATUS_REV_01 : 8,
                  STATUS_REV_02 : 4,
                  STATUS_REV_03 : 8,
                  STATUS_REV_04 : 8}

STATUS_POS = {STATUS_REV_00 : 14,
               STATUS_REV_01 : 14,
               STATUS_REV_02 : 14,
               STATUS_REV_03 : 16,
               STATUS_REV_04 : 20}

def parseSStatus(s, z=''):
    revision = ''
    pens = []
    top_door = TOP_DOOR_NOT_PRESENT
    stat = STATUS_UNKNOWN
    supply_door = SUPPLY_DOOR_NOT_PRESENT
    duplexer = DUPLEXER_NOT_PRESENT
    photo_tray = PHOTO_TRAY_NOT_PRESENT
    in_tray1 = IN_TRAY_NOT_PRESENT
    in_tray2 = IN_TRAY_NOT_PRESENT
    media_path = MEDIA_PATH_NOT_PRESENT
    Z_SIZE = 6

    try:
        z1 = []
        if len(z) > 0:
            z_fields = z.split(',')

            for z_field in z_fields:

                if len(z_field) > 2 and z_field[:2] == '05':
                    z1s = z_field[2:]
                    z1 = [int(x, 16) for x in z1s]

        s1 = [int(x, 16) for x in s]

        revision = s1[1]

        assert STATUS_REV_00 <= revision <= STATUS_REV_04

        top_door = bool(s1[2] & to_long(0x8)) + s1[2] & to_long(0x1)
        supply_door = bool(s1[3] & to_long(0x8)) + s1[3] & to_long(0x1)
        duplexer = bool(s1[4] & to_long(0xc)) +  s1[4] & to_long(0x1)
        photo_tray = bool(s1[5] & 0x8) + s1[5] & 0x1

        if revision == STATUS_REV_02:
            in_tray1 = bool(s1[6] & to_long(0x8)) + s1[6] & to_long(0x1)
            in_tray2 = bool(s1[7] & to_long(0x8)) + s1[7] & to_long(0x1)
        else:
            in_tray1 = bool(s1[6] & to_long(0x8))
            in_tray2 = bool(s1[7] & to_long(0x8))

        media_path = bool(s1[8] & to_long(0x8)) + (s1[8] & to_long(0x1)) + ((bool(s1[18] & to_long(0x2)))<<1)
        status_pos = STATUS_POS[revision]
        status_byte = s1[status_pos]<<4
        if status_byte != 48:
            status_byte = (s1[status_pos]<<4) + s1[status_pos + 1]
        stat = status_byte + STATUS_PRINTER_BASE

        pen, c, d = {}, NUM_PEN_POS[revision]+1, 0
        num_pens = s1[NUM_PEN_POS[revision]]
        index = 0
        pen_data_size = PEN_DATA_SIZE[revision]

        log.debug("num_pens = %d" % num_pens)
        for p in range(num_pens):
            info = int(s[c : c + pen_data_size], 16)

            pen['index'] = index

            if pen_data_size == 4:
                pen['type'] = REVISION_2_TYPE_MAP.get(int((info & to_long(0xf000)) >> to_long(12)), 0)

                if index < (num_pens / 2):
                    pen['kind'] = AGENT_KIND_HEAD
                else:
                    pen['kind'] = AGENT_KIND_SUPPLY

                pen['level-trigger'] = int ((info & to_long(0x0e00)) >> to_long(9))
                pen['health'] = int((info & to_long(0x0180)) >> to_long(7))
                pen['level'] = int(info & to_long(0x007f))
                pen['id'] = 0x1f

            elif pen_data_size == 8:
                pen['kind'] = bool(info & to_long(0x80000000)) + ((bool(info & to_long(0x40000000)))<<to_long(1))
                pen['type'] = int((info & to_long(0x3f000000)) >> to_long(24))
                pen['id'] = int((info & 0xf80000) >> to_long(19))
                pen['level-trigger'] = int((info & to_long(0x70000)) >> to_long(16))
                pen['health'] = int((info & to_long(0xc000)) >> to_long(14))
                pen['level'] = int(info & to_long(0xff))

            else:
                log.error("Pen data size error")

            if len(z1) > 0:
                # TODO: Determine cause of IndexError for C6100 (defect #1111)
                try:
                    pen['dvc'] = int(z1s[d+1:d+5], 16)
                    pen['virgin'] = bool(z1[d+5] & to_long(0x8))
                    pen['hp-ink'] = bool(z1[d+5] & to_long(0x4))
                    pen['known'] = bool(z1[d+5] & to_long(0x2))
                    pen['ack'] = bool(z1[d+5] & to_long(0x1))
                except IndexError:
                    pen['dvc'] = 0
                    pen['virgin'] = 0
                    pen['hp-ink'] = 0
                    pen['known'] = 0
                    pen['ack'] = 0

            log.debug("pen %d %s" % (index, pen))

            index += 1
            pens.append(pen)
            pen = {}
            c += pen_data_size
            d += Z_SIZE

    except (IndexError, ValueError, TypeError) as e:
        log.warn("Status parsing error: %s" % str(e))

    return {'revision' :    revision,
             'agents' :      pens,
             'top-door' :    top_door,
             'status-code' : stat,
             'supply-door' : supply_door,
             'duplexer' :    duplexer,
             'photo-tray' :  photo_tray,
             'in-tray1' :    in_tray1,
             'in-tray2' :    in_tray2,
             'media-path' :  media_path,
           }



# $HB0$NC0,ff,DN,IDLE,CUT,K0,C0,DP,NR,KP092,CP041
#     0    1  2  3    4   5  6  7  8  9     10
def parseVStatus(s):
    pens, pen, c = [], {}, 0
    fields = s.split(',')
    log.debug(fields)
    f0 = fields[0]

    if len(f0) == 20:
        # TODO: $H00000000$M00000000 style (OJ Pro 1150/70)
        # Need spec
        pass
    elif len(f0) == 8:
        for p in f0:
            if c == 0:
                #assert p == '$'
                c += 1
            elif c == 1:
                if p in ('a', 'A'):
                    pen['type'], pen['kind'] = AGENT_TYPE_NONE, AGENT_KIND_NONE
                c += 1
            elif c == 2:
                pen['health'] = AGENT_HEALTH_OK
                pen['kind'] = AGENT_KIND_HEAD_AND_SUPPLY
                if   p in ('b', 'B'): pen['type'] = AGENT_TYPE_BLACK
                elif p in ('c', 'C'): pen['type'] = AGENT_TYPE_CMY
                elif p in ('d', 'D'): pen['type'] = AGENT_TYPE_KCM
                elif p in ('u', 'U'): pen['type'], pen['health'] = AGENT_TYPE_NONE, AGENT_HEALTH_MISINSTALLED
                c += 1
            elif c == 3:
                if p == '0': pen['state'] = 1
                else: pen['state'] = 0

                pen['level'] = 0
                i = 8

                while True:
                    try:
                        f = fields[i]
                    except IndexError:
                        break
                    else:
                        if f[:2] == 'KP' and pen['type'] == AGENT_TYPE_BLACK:
                            pen['level'] = int(f[2:])
                        elif f[:2] == 'CP' and pen['type'] == AGENT_TYPE_CMY:
                            pen['level'] = int(f[2:])
                    i += 1

                pens.append(pen)
                pen = {}
                c = 0
    else:
        pass

    try:
        fields[2]
    except IndexError:
        top_lid = 1 # something went wrong!
    else:
        if fields[2] == 'DN':
            top_lid = 1
        else:
            top_lid = 2

    try:
        stat = vstatus_xlate.get(fields[3].lower(), STATUS_PRINTER_IDLE)
    except IndexError:
        stat = STATUS_PRINTER_IDLE # something went wrong!

    return {'revision' :   STATUS_REV_V,
             'agents' :     pens,
             'top-door' :   top_lid,
             'status-code': stat,
             'supply-door': SUPPLY_DOOR_NOT_PRESENT,
             'duplexer' :   DUPLEXER_NOT_PRESENT,
             'photo-tray' : PHOTO_TRAY_NOT_PRESENT,
             'in-tray1' :   IN_TRAY_NOT_PRESENT,
             'in-tray2' :   IN_TRAY_NOT_PRESENT,
             'media-path' : MEDIA_PATH_CUT_SHEET, # ?
           }


def parseStatus(DeviceID):
    if 'VSTATUS' in DeviceID:
         return parseVStatus(DeviceID['VSTATUS'])
    elif 'S' in DeviceID:
        return parseSStatus(DeviceID['S'], DeviceID.get('Z', ''))
    else:
        return STATUS_BLOCK_UNKNOWN

def LaserJetDeviceStatusToPrinterStatus(device_status, printer_status, detected_error_state):
    stat = STATUS_PRINTER_IDLE

    if device_status in (pml.DEVICE_STATUS_WARNING, pml.DEVICE_STATUS_DOWN):

        if detected_error_state & pml.DETECTED_ERROR_STATE_LOW_PAPER_MASK and \
            not (detected_error_state & pml.DETECTED_ERROR_STATE_NO_PAPER_MASK):
            stat = STATUS_PRINTER_LOW_PAPER

        elif detected_error_state & pml.DETECTED_ERROR_STATE_NO_PAPER_MASK:
            stat = STATUS_PRINTER_OUT_OF_PAPER

        elif detected_error_state & pml.DETECTED_ERROR_STATE_DOOR_OPEN_MASK:
            stat = STATUS_PRINTER_DOOR_OPEN

        elif detected_error_state & pml.DETECTED_ERROR_STATE_JAMMED_MASK:
            stat = STATUS_PRINTER_MEDIA_JAM

        elif detected_error_state & pml.DETECTED_ERROR_STATE_OUT_CART_MASK:
            stat = STATUS_PRINTER_NO_TONER

        elif detected_error_state & pml.DETECTED_ERROR_STATE_LOW_CART_MASK:
            stat = STATUS_PRINTER_LOW_TONER

        elif detected_error_state == pml.DETECTED_ERROR_STATE_SERVICE_REQUEST_MASK:
            stat = STATUS_PRINTER_SERVICE_REQUEST

        elif detected_error_state & pml.DETECTED_ERROR_STATE_OFFLINE_MASK:
            stat = STATUS_PRINTER_OFFLINE

    else:

        if printer_status == pml.PRINTER_STATUS_IDLE:
            stat = STATUS_PRINTER_IDLE

        elif printer_status == pml.PRINTER_STATUS_PRINTING:
            stat = STATUS_PRINTER_PRINTING

        elif printer_status == pml.PRINTER_STATUS_WARMUP:
            stat = STATUS_PRINTER_WARMING_UP

    return stat

# Map from ISO 10175/10180 to HPLIP types
COLORANT_INDEX_TO_AGENT_TYPE_MAP = {
                                    'other' :   AGENT_TYPE_UNSPECIFIED,
                                    'unknown' : AGENT_TYPE_UNSPECIFIED,
                                    'blue' :    AGENT_TYPE_BLUE,
                                    'cyan' :    AGENT_TYPE_CYAN,
                                    'magenta':  AGENT_TYPE_MAGENTA,
                                    'yellow' :  AGENT_TYPE_YELLOW,
                                    'black' :   AGENT_TYPE_BLACK,
                                    'photoblack': AGENT_TYPE_PHOTO_BLACK,
                                    'matteblack' : AGENT_TYPE_MATTE_BLACK,
                                    'lightgray' : AGENT_TYPE_LG,
                                    'gray': AGENT_TYPE_G,
                                    'darkgray': AGENT_TYPE_DG,
                                    'lightcyan': AGENT_TYPE_LC,
                                    'lightmagenta': AGENT_TYPE_LM,
                                    'red' : AGENT_TYPE_RED,
                                   }

MARKER_SUPPLES_TYPE_TO_AGENT_KIND_MAP = {
    pml.OID_MARKER_SUPPLIES_TYPE_OTHER :              AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_UNKNOWN :            AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_TONER :              AGENT_KIND_TONER_CARTRIDGE,
    pml.OID_MARKER_SUPPLIES_TYPE_WASTE_TONER :        AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_INK :                AGENT_KIND_SUPPLY,
    pml.OID_MARKER_SUPPLIES_TYPE_INK_CART :           AGENT_KIND_HEAD_AND_SUPPLY,
    pml.OID_MARKER_SUPPLIES_TYPE_INK_RIBBON :         AGENT_KIND_HEAD_AND_SUPPLY,
    pml.OID_MARKER_SUPPLIES_TYPE_WASTE_INK :          AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_OPC :                AGENT_KIND_DRUM_KIT,
    pml.OID_MARKER_SUPPLIES_TYPE_DEVELOPER :          AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_FUSER_OIL :          AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_SOLID_WAX :          AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_RIBBON_WAX :         AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_WASTE_WAX :          AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_FUSER :              AGENT_KIND_MAINT_KIT,
    pml.OID_MARKER_SUPPLIES_TYPE_CORONA_WIRE :        AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_FUSER_OIL_WICK :     AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_CLEANER_UNIT :       AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_FUSER_CLEANING_PAD : AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_TRANSFER_UNIT :      AGENT_KIND_TRANSFER_KIT,
    pml.OID_MARKER_SUPPLIES_TYPE_TONER_CART :         AGENT_KIND_TONER_CARTRIDGE,
    pml.OID_MARKER_SUPPLIES_TYPE_FUSER_OILER :        AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_ADF_MAINT_KIT :      AGENT_KIND_ADF_KIT,
}


def StatusType3( dev, parsedID ): # LaserJet Status (PML/SNMP)
    try:
        dev.openPML()
        #result_code, on_off_line = dev.getPML( pml.OID_ON_OFF_LINE, pml.INT_SIZE_BYTE )
        #result_code, sleep_mode = dev.getPML( pml.OID_SLEEP_MODE, pml.INT_SIZE_BYTE )
        result_code, printer_status = dev.getPML( pml.OID_PRINTER_STATUS, pml.INT_SIZE_BYTE )
        result_code, device_status = dev.getPML( pml.OID_DEVICE_STATUS, pml.INT_SIZE_BYTE )
        result_code, cover_status = dev.getPML( pml.OID_COVER_STATUS, pml.INT_SIZE_BYTE )
        result_code, value = dev.getPML( pml.OID_DETECTED_ERROR_STATE )
    except Error:
       dev.closePML()

       return {'revision' :    STATUS_REV_UNKNOWN,
                 'agents' :      [],
                 'top-door' :    0,
                 'status-code' : STATUS_UNKNOWN,
                 'supply-door' : 0,
                 'duplexer' :    1,
                 'photo-tray' :  0,
                 'in-tray1' :    0,
                 'in-tray2' :    0,
                 'media-path' :  0,
               }

    try:
        detected_error_state = struct.unpack( 'B', to_bytes_latin(value[0]))[0]
    except (IndexError, TypeError):
        detected_error_state = pml.DETECTED_ERROR_STATE_OFFLINE_MASK

    agents, x = [], 1

    while True:
        log.debug( "%s Agent: %d %s" % ("*"*10, x, "*"*10))
        log.debug("OID_MARKER_SUPPLIES_TYPE_%d:" % x)
        oid = ( pml.OID_MARKER_SUPPLIES_TYPE_x % x, pml.OID_MARKER_SUPPLIES_TYPE_x_TYPE )
        result_code, value = dev.getPML( oid, pml.INT_SIZE_BYTE )

        if result_code != ERROR_SUCCESS or value is None:
            log.debug("End of supply information.")
            break

        for a in MARKER_SUPPLES_TYPE_TO_AGENT_KIND_MAP:
            if value == a:
                agent_kind = MARKER_SUPPLES_TYPE_TO_AGENT_KIND_MAP[a]
                break
        else:
            agent_kind = AGENT_KIND_UNKNOWN

        # TODO: Deal with printers that return -1 and -2 for level and max (LJ3380)

        log.debug("OID_MARKER_SUPPLIES_LEVEL_%d:" % x)
        oid = ( pml.OID_MARKER_SUPPLIES_LEVEL_x % x, pml.OID_MARKER_SUPPLIES_LEVEL_x_TYPE )
        result_code, agent_level = dev.getPML( oid )

        if result_code != ERROR_SUCCESS:
            log.debug("Failed")
            break

        log.debug( 'agent%d-level: %d' % ( x, agent_level ) )
        log.debug("OID_MARKER_SUPPLIES_MAX_%d:" % x)
        oid = ( pml.OID_MARKER_SUPPLIES_MAX_x % x, pml.OID_MARKER_SUPPLIES_MAX_x_TYPE )
        result_code, agent_max = dev.getPML( oid )

        if agent_max == 0: agent_max = 1

        if result_code != ERROR_SUCCESS:
            log.debug("Failed")
            break

        log.debug( 'agent%d-max: %d' % ( x, agent_max ) )
        log.debug("OID_MARKER_SUPPLIES_COLORANT_INDEX_%d:" % x)
        oid = ( pml.OID_MARKER_SUPPLIES_COLORANT_INDEX_x % x, pml.OID_MARKER_SUPPLIES_COLORANT_INDEX_x_TYPE )
        result_code, colorant_index = dev.getPML( oid )

        if result_code != ERROR_SUCCESS: # 3080, 3055 will fail here
            log.debug("Failed")
            agent_type = AGENT_TYPE_BLACK
            #break
        else:
            log.debug("Colorant index: %d" % colorant_index)

            log.debug("OID_MARKER_COLORANT_VALUE_%d" % x)
            oid = ( pml.OID_MARKER_COLORANT_VALUE_x % colorant_index, pml.OID_MARKER_COLORANT_VALUE_x_TYPE )
            result_code, colorant_value = dev.getPML( oid )

            if result_code != ERROR_SUCCESS:
                log.debug("Failed. Defaulting to black.")
                agent_type = AGENT_TYPE_BLACK
            #else:
            if 1:
                if agent_kind in (AGENT_KIND_MAINT_KIT, AGENT_KIND_ADF_KIT,
                                  AGENT_KIND_DRUM_KIT, AGENT_KIND_TRANSFER_KIT):

                    agent_type = AGENT_TYPE_UNSPECIFIED

                else:
                    agent_type = AGENT_TYPE_BLACK

                    if result_code != ERROR_SUCCESS:
                        log.debug("OID_MARKER_SUPPLIES_DESCRIPTION_%d:" % x)
                        oid = (pml.OID_MARKER_SUPPLIES_DESCRIPTION_x % x, pml.OID_MARKER_SUPPLIES_DESCRIPTION_x_TYPE)
                        result_code, colorant_value = dev.getPML( oid )

                        if result_code != ERROR_SUCCESS:
                            log.debug("Failed")
                            break

                        if colorant_value is not None:
                            log.debug("colorant value: %s" % colorant_value)
                            colorant_value = colorant_value.lower().strip()

                            for c in COLORANT_INDEX_TO_AGENT_TYPE_MAP:
                                if colorant_value.find(c) >= 0:
                                    agent_type = COLORANT_INDEX_TO_AGENT_TYPE_MAP[c]
                                    break
                            else:
                                agent_type = AGENT_TYPE_BLACK

                    else: # SUCCESS
                        if colorant_value is not None:
                            log.debug("colorant value: %s" % colorant_value)
                            colorant_value = colorant_value.lower().strip()
                            agent_type = COLORANT_INDEX_TO_AGENT_TYPE_MAP.get( colorant_value, AGENT_TYPE_BLACK )

                        if agent_type == AGENT_TYPE_NONE:
                            if agent_kind == AGENT_KIND_TONER_CARTRIDGE:
                                agent_type = AGENT_TYPE_BLACK
                            else:
                                agent_type = AGENT_TYPE_UNSPECIFIED

        log.debug("OID_MARKER_STATUS_%d:" % x)
        oid = ( pml.OID_MARKER_STATUS_x % x, pml.OID_MARKER_STATUS_x_TYPE )
        result_code, agent_status = dev.getPML( oid )

        if result_code != ERROR_SUCCESS:
            log.debug("Failed")
            agent_trigger = AGENT_LEVEL_TRIGGER_SUFFICIENT_0
            agent_health = AGENT_HEALTH_OK
        else:
            agent_trigger = AGENT_LEVEL_TRIGGER_SUFFICIENT_0

            if agent_status is None:
                agent_health = AGENT_HEALTH_OK

            elif agent_status == pml.OID_MARKER_STATUS_OK:
                agent_health = AGENT_HEALTH_OK

            elif agent_status == pml.OID_MARKER_STATUS_MISINSTALLED:
                agent_health = AGENT_HEALTH_MISINSTALLED

            elif agent_status in ( pml.OID_MARKER_STATUS_LOW_TONER_CONT,
                                   pml.OID_MARKER_STATUS_LOW_TONER_STOP ):

                agent_health = AGENT_HEALTH_OK
                agent_trigger = AGENT_LEVEL_TRIGGER_MAY_BE_LOW

            else:
                agent_health = AGENT_HEALTH_OK

        agent_level = int(float(agent_level)/agent_max * 100)


        log.debug("agent%d: kind=%d, type=%d, health=%d, level=%d, level-trigger=%d" % \
            (x, agent_kind, agent_type, agent_health, agent_level, agent_trigger))


        agents.append({'kind' : agent_kind,
                       'type' : agent_type,
                       'health' : agent_health,
                       'level' : agent_level,
                       'level-trigger' : agent_trigger,})

        x += 1

        if x > 20:
            break


    printer_status = printer_status or STATUS_PRINTER_IDLE
    log.debug("printer_status=%d" % printer_status)
    device_status = device_status or pml.DEVICE_STATUS_RUNNING
    log.debug("device_status=%d" % device_status)
    cover_status = cover_status or pml.COVER_STATUS_CLOSED
    log.debug("cover_status=%d" % cover_status)
    detected_error_state = detected_error_state or pml.DETECTED_ERROR_STATE_NO_ERROR
    log.debug("detected_error_state=%d (0x%x)" % (detected_error_state, detected_error_state))

    stat = LaserJetDeviceStatusToPrinterStatus(device_status, printer_status, detected_error_state)

    log.debug("Printer status=%d" % stat)

    if stat == STATUS_PRINTER_DOOR_OPEN:
        supply_door = 0
    else:
        supply_door = 1

    return {'revision' :    STATUS_REV_UNKNOWN,
             'agents' :      agents,
             'top-door' :    cover_status,
             'status-code' : stat,
             'supply-door' : supply_door,
             'duplexer' :    1,
             'photo-tray' :  0,
             'in-tray1' :    1,
             'in-tray2' :    1,
             'media-path' :  1,
           }

def setup_panel_translator():
    printables = list(
"""0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~""")

    map = {}
    for x in [chr(x) for x in range(0,256)]:
        if x in printables:
            map[x] = x
        else:
            map[x] = '\x20'

    map.update({'\x10' : '\xab',
                    '\x11' : '\xbb',
                    '\x12' : '\xa3',
                    '\x13' : '\xbb',
                    '\x80' : '\xab',
                    '\x81' : '\xbb',
                    '\x82' : '\x2a',
                    '\x83' : '\x2a',
                    '\x85' : '\x2a',
                    '\xa0' : '\xab',
                    '\x1f' : '\x3f',
                    '='    : '\x20',
                })

    frm, to = to_bytes_latin(''), to_bytes_latin('')
    map_keys = list(map.keys())
    map_keys.sort()
    for x in map_keys:
        frm = to_bytes_latin('').join([frm, to_bytes_latin(x)])
        to = to_bytes_latin('').join([to, to_bytes_latin(map[x])])

    global PANEL_TRANSLATOR_FUNC
    PANEL_TRANSLATOR_FUNC = utils.Translator(frm, to)

PANEL_TRANSLATOR_FUNC = None
setup_panel_translator()


def PanelCheck(dev):
    line1, line2 = to_bytes_utf8(''), ('')

    if dev.io_mode not in (IO_MODE_RAW, IO_MODE_UNI):

        try:
            dev.openPML()
        except Error:
            pass
        else:

            oids = [(pml.OID_HP_LINE1, pml.OID_HP_LINE2),
                     (pml.OID_SPM_LINE1, pml.OID_SPM_LINE2)]

            for oid1, oid2 in oids:
                result, line1 = dev.getPML(oid1)

                if result < pml.ERROR_MAX_OK:
                    line1 = PANEL_TRANSLATOR_FUNC(line1.encode('utf-8')).rstrip()

                    if to_bytes_utf8('\x0a') in line1:
                        line1, line2 = line1.split(to_bytes_utf8('\x0a'), 1)
                        break

                    result, line2 = dev.getPML(oid2)

                    if result < pml.ERROR_MAX_OK:
                        line2 = PANEL_TRANSLATOR_FUNC(line2.encode('utf-8')).rstrip()
                        break

    return bool(line1 or line2), line1 or to_bytes_utf8(''), line2 or to_bytes_utf8('')


BATTERY_HEALTH_MAP = {0 : AGENT_HEALTH_OK,
                       1 : AGENT_HEALTH_OVERTEMP,
                       2 : AGENT_HEALTH_CHARGING,
                       3 : AGENT_HEALTH_MISINSTALLED,
                       4 : AGENT_HEALTH_FAILED,
                      }


BATTERY_TRIGGER_MAP = {0 : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                        1 : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
                        2 : AGENT_LEVEL_TRIGGER_PROBABLY_OUT,
                        3 : AGENT_LEVEL_TRIGGER_SUFFICIENT_4,
                        4 : AGENT_LEVEL_TRIGGER_SUFFICIENT_2,
                        5 : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                       }

BATTERY_PML_TRIGGER_MAP = {
        (100, 80)  : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
        (79,  60)  : AGENT_LEVEL_TRIGGER_SUFFICIENT_1,
        (59,  40)  : AGENT_LEVEL_TRIGGER_SUFFICIENT_2,
        (39,  30)  : AGENT_LEVEL_TRIGGER_SUFFICIENT_3,
        (29,  20)  : AGENT_LEVEL_TRIGGER_SUFFICIENT_4,
        (19,  10)  : AGENT_LEVEL_TRIGGER_MAY_BE_LOW,
        (9,    5)  : AGENT_LEVEL_TRIGGER_PROBABLY_OUT,
        (4,   -1)  : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
        }


def BatteryCheck(dev, status_block, battery_check):
    try_dynamic_counters = False

    try:
        try:
            dev.openPML()
        except Error:
            if battery_check == STATUS_BATTERY_CHECK_STD:
                log.debug("PML channel open failed. Trying dynamic counters...")
                try_dynamic_counters = True
        else:
            if battery_check == STATUS_BATTERY_CHECK_PML:
                result, battery_level = dev.getPML(pml.OID_BATTERY_LEVEL_2)

                if result > pml.ERROR_MAX_OK:
                    status_block['agents'].append({
                        'kind'   : AGENT_KIND_INT_BATTERY,
                        'type'   : AGENT_TYPE_UNSPECIFIED,
                        'health' : AGENT_HEALTH_UNKNOWN,
                        'level'  : 0,
                        'level-trigger' : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                        })
                    return

                else:
                    status_block['agents'].append({
                        'kind'   : AGENT_KIND_INT_BATTERY,
                        'type'   : AGENT_TYPE_UNSPECIFIED,
                        'health' : AGENT_HEALTH_OK,
                        'level'  : battery_level,
                        'level-trigger' : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                        })
                    return

            else: # STATUS_BATTERY_CHECK_STD
                result, battery_level = dev.getPML(pml.OID_BATTERY_LEVEL)
                result, power_mode =  dev.getPML(pml.OID_POWER_MODE)

                if battery_level is not None and \
                    power_mode is not None:

                    if power_mode & pml.POWER_MODE_BATTERY_LEVEL_KNOWN and \
                        battery_level >= 0:

                        for x in BATTERY_PML_TRIGGER_MAP:
                            if x[0] >= battery_level > x[1]:
                                battery_trigger_level = BATTERY_PML_TRIGGER_MAP[x]
                                break

                        if power_mode & pml.POWER_MODE_CHARGING:
                            agent_health = AGENT_HEALTH_CHARGING

                        elif power_mode & pml.POWER_MODE_DISCHARGING:
                            agent_health = AGENT_HEALTH_DISCHARGING

                        else:
                            agent_health = AGENT_HEALTH_OK

                        status_block['agents'].append({
                            'kind'   : AGENT_KIND_INT_BATTERY,
                            'type'   : AGENT_TYPE_UNSPECIFIED,
                            'health' : agent_health,
                            'level'  : battery_level,
                            'level-trigger' : battery_trigger_level,
                            })
                        return

                    else:
                        status_block['agents'].append({
                            'kind'   : AGENT_KIND_INT_BATTERY,
                            'type'   : AGENT_TYPE_UNSPECIFIED,
                            'health' : AGENT_HEALTH_UNKNOWN,
                            'level'  : 0,
                            'level-trigger' : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                            })
                        return

                else:
                    try_dynamic_counters = True

    finally:
        dev.closePML()


    if battery_check == STATUS_BATTERY_CHECK_STD and \
        try_dynamic_counters:

        try:
            try:
                battery_health = dev.getDynamicCounter(200)
                battery_trigger_level = dev.getDynamicCounter(201)
                battery_level = dev.getDynamicCounter(202)

                status_block['agents'].append({
                    'kind'   : AGENT_KIND_INT_BATTERY,
                    'type'   : AGENT_TYPE_UNSPECIFIED,
                    'health' : BATTERY_HEALTH_MAP[battery_health],
                    'level'  : battery_level,
                    'level-trigger' : BATTERY_TRIGGER_MAP[battery_trigger_level],
                    })
            except Error:
                status_block['agents'].append({
                    'kind'   : AGENT_KIND_INT_BATTERY,
                    'type'   : AGENT_TYPE_UNSPECIFIED,
                    'health' : AGENT_HEALTH_UNKNOWN,
                    'level'  : 0,
                    'level-trigger' : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                    })
        finally:
            dev.closePrint()

    else:
        status_block['agents'].append({
            'kind'   : AGENT_KIND_INT_BATTERY,
            'type'   : AGENT_TYPE_UNSPECIFIED,
            'health' : AGENT_HEALTH_UNKNOWN,
            'level'  : 0,
            'level-trigger' : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
            })



# this works for 2 pen products that allow 1 or 2 pens inserted
# from: k, kcm, cmy, ggk
def getPenConfiguration(s): # s=status dict from parsed device ID
    pens = [p['type'] for p in s['agents']]

    if utils.all(pens, lambda x : x==AGENT_TYPE_NONE):
        return AGENT_CONFIG_NONE

    if AGENT_TYPE_NONE in pens:

        if AGENT_TYPE_BLACK in pens:
            return AGENT_CONFIG_BLACK_ONLY

        elif AGENT_TYPE_CMY in pens:
            return AGENT_CONFIG_COLOR_ONLY

        elif AGENT_TYPE_KCM in pens:
            return AGENT_CONFIG_PHOTO_ONLY

        elif AGENT_TYPE_GGK in pens:
            return AGENT_CONFIG_GREY_ONLY

        else:
            return AGENT_CONFIG_INVALID

    else:
        if AGENT_TYPE_BLACK in pens and AGENT_TYPE_CMY in pens:
            return AGENT_CONFIG_COLOR_AND_BLACK

        elif AGENT_TYPE_CMY in pens and AGENT_TYPE_KCM in pens:
            return AGENT_CONFIG_COLOR_AND_PHOTO

        elif AGENT_TYPE_CMY in pens and AGENT_TYPE_GGK in pens:
            return AGENT_CONFIG_COLOR_AND_GREY

        else:
            return AGENT_CONFIG_INVALID


def getFaxStatus(dev):
    tx_active, rx_active = False, False

    if dev.io_mode not in (IO_MODE_UNI, IO_MODE_RAW):
        try:
            dev.openPML()

            result_code, tx_state = dev.getPML(pml.OID_FAXJOB_TX_STATUS)

            if result_code == ERROR_SUCCESS and tx_state:
                if tx_state not in (pml.FAXJOB_TX_STATUS_IDLE, pml.FAXJOB_TX_STATUS_DONE):
                    tx_active = True

            result_code, rx_state = dev.getPML(pml.OID_FAXJOB_RX_STATUS)

            if result_code == ERROR_SUCCESS and rx_state:
                if rx_state not in (pml.FAXJOB_RX_STATUS_IDLE, pml.FAXJOB_RX_STATUS_DONE):
                    rx_active = True

        finally:
            dev.closePML()

    return tx_active, rx_active


TYPE6_STATUS_CODE_MAP = {
     0    : STATUS_PRINTER_IDLE, #</DevStatusUnknown>
    -19928: STATUS_PRINTER_IDLE,
    -18995: STATUS_PRINTER_CANCELING,
    -17974: STATUS_PRINTER_WARMING_UP,
    -17973: STATUS_PRINTER_PEN_CLEANING, # sic
    -18993: STATUS_PRINTER_BUSY,
    -17949: STATUS_PRINTER_BUSY,
    -19720: STATUS_PRINTER_MANUAL_DUPLEX_BLOCK,
    -19678: STATUS_PRINTER_BUSY,
    -19695: STATUS_PRINTER_OUT_OF_PAPER,
    -17985: STATUS_PRINTER_MEDIA_JAM,
    -19731: STATUS_PRINTER_OUT_OF_PAPER,
    -18974: STATUS_PRINTER_BUSY, #?
    -19730: STATUS_PRINTER_OUT_OF_PAPER,
    -19729: STATUS_PRINTER_OUT_OF_PAPER,
    -19933: STATUS_PRINTER_HARD_ERROR, # out of memory
    -17984: STATUS_PRINTER_DOOR_OPEN,
    -19694: STATUS_PRINTER_DOOR_OPEN,
    -18992: STATUS_PRINTER_MANUAL_FEED_BLOCKED, # ?
    -19690: STATUS_PRINTER_MEDIA_JAM, # tray 1
    -19689: STATUS_PRINTER_MEDIA_JAM, # tray 2
    -19611: STATUS_PRINTER_MEDIA_JAM, # tray 3
    -19686: STATUS_PRINTER_MEDIA_JAM,
    -19688: STATUS_PRINTER_MEDIA_JAM, # paper path
    -19685: STATUS_PRINTER_MEDIA_JAM, # cart area
    -19684: STATUS_PRINTER_MEDIA_JAM, # output bin
    -18848: STATUS_PRINTER_MEDIA_JAM, # duplexer
    -18847: STATUS_PRINTER_MEDIA_JAM, # door open
    -18846: STATUS_PRINTER_MEDIA_JAM, # tray 2
    -19687: STATUS_PRINTER_MEDIA_JAM, # open door
    -17992: STATUS_PRINTER_MEDIA_JAM, # mispick
    -19700: STATUS_PRINTER_HARD_ERROR, # invalid driver
    -17996: STATUS_PRINTER_FUSER_ERROR, # fuser error
    -17983: STATUS_PRINTER_FUSER_ERROR,
    -17982: STATUS_PRINTER_FUSER_ERROR,
    -17981: STATUS_PRINTER_FUSER_ERROR,
    -17971: STATUS_PRINTER_FUSER_ERROR,
    -17995: STATUS_PRINTER_HARD_ERROR, # beam error
    -17994: STATUS_PRINTER_HARD_ERROR, # scanner error
    -17993: STATUS_PRINTER_HARD_ERROR, # fan error
    -18994: STATUS_PRINTER_HARD_ERROR,
    -17986: STATUS_PRINTER_HARD_ERROR,
    -19904: STATUS_PRINTER_HARD_ERROR,
    -19701: STATUS_PRINTER_NON_HP_INK, # [sic]
    -19613: STATUS_PRINTER_IDLE, # HP
    -19654: STATUS_PRINTER_NON_HP_INK, # [sic]
    -19682: STATUS_PRINTER_HARD_ERROR, # resinstall
    -19693: STATUS_PRINTER_IDLE, # ?? To Accept
    -19752: STATUS_PRINTER_LOW_TONER,
    -19723: STATUS_PRINTER_BUSY,
    -19703: STATUS_PRINTER_BUSY,
    -19739: STATUS_PRINTER_NO_TONER,
    -19927: STATUS_PRINTER_BUSY,
    -19932: STATUS_PRINTER_BUSY,
    -19931: STATUS_PRINTER_BUSY,
    -11989: STATUS_PRINTER_BUSY,
    -11995: STATUS_PRINTER_BUSY, # ADF loaded
    -19954: STATUS_PRINTER_CANCELING,
    -19955: STATUS_PRINTER_REPORT_PRINTING,
    -19956: STATUS_PRINTER_REPORT_PRINTING,
    -19934: STATUS_PRINTER_HARD_ERROR,
    -19930: STATUS_PRINTER_BUSY,
    -11990: STATUS_PRINTER_DOOR_OPEN,
    -11999: STATUS_PRINTER_MEDIA_JAM, # ADF
    -12000: STATUS_PRINTER_MEDIA_JAM, # ADF
    -11998: STATUS_PRINTER_MEDIA_JAM, # ADF
    -11986: STATUS_PRINTER_HARD_ERROR, # scanner
    -11994: STATUS_PRINTER_BUSY,
    -14967: STATUS_PRINTER_BUSY,
    -19912: STATUS_PRINTER_HARD_ERROR,
    -14962: STATUS_PRINTER_BUSY, # copy pending
    -14971: STATUS_PRINTER_BUSY, # copying
    -14973: STATUS_PRINTER_BUSY, # copying being canceled
    -14972: STATUS_PRINTER_BUSY, # copying canceled
    -14966: STATUS_PRINTER_DOOR_OPEN,
    -14974: STATUS_PRINTER_MEDIA_JAM,
    -14969: STATUS_PRINTER_HARD_ERROR,
    -14968: STATUS_PRINTER_HARD_ERROR,
    -12996: STATUS_PRINTER_BUSY, # scan
    -12994: STATUS_PRINTER_BUSY, # scan
    -12993: STATUS_PRINTER_BUSY, # scan
    -12991: STATUS_PRINTER_BUSY, # scan
    -12995: STATUS_PRINTER_BUSY, # scan
    -12997: STATUS_PRINTER_HARD_ERROR, # scan
    -12990: STATUS_PRINTER_BUSY,
    -12998: STATUS_PRINTER_BUSY,
    -13000: STATUS_PRINTER_DOOR_OPEN,
    -12999: STATUS_PRINTER_MEDIA_JAM,
    -13859: STATUS_PRINTER_BUSY,
    -13858: STATUS_PRINTER_BUSY, #</DevStatusDialingOut>
    -13868: STATUS_PRINTER_BUSY, #</DevStatusRedialPending>
    -13867: STATUS_PRINTER_BUSY, #</DevStatusFaxSendCanceled>
    -13857: STATUS_PRINTER_BUSY, #</DevStatusConnecting>
    -13856: STATUS_PRINTER_BUSY, #</DevStatusSendingPage>
    -13855: STATUS_PRINTER_BUSY, #</DevStatusOnePageSend>
    -13854: STATUS_PRINTER_BUSY, #</DevStatusMultiplePagesSent>
    -13853: STATUS_PRINTER_BUSY, #</DevStatusSenderCancelingFax>
    -13839: STATUS_PRINTER_BUSY, #</DevStatusIncomingCall>
    -13842: STATUS_PRINTER_BUSY, #</DevStatusBlockingFax>
    -13838: STATUS_PRINTER_BUSY, #</DevStatusReceivingFax>
    -13847: STATUS_PRINTER_BUSY, #</DevStatusSinglePageReceived>
    -13846: STATUS_PRINTER_BUSY, #</DevStatusDoublePagesReceived>
    -13845: STATUS_PRINTER_BUSY, #</DevStatusTriplePagesReceived>
    -13844: STATUS_PRINTER_BUSY, #</DevStatusPrintingFax>
    -13840: STATUS_PRINTER_BUSY, #</DevStatusCancelingFaxPrint>
    -13843: STATUS_PRINTER_BUSY, #</DevStatusFaxCancelingReceive>
    -13850: STATUS_PRINTER_BUSY, #</DevStatusFaxCanceledReceive>
    -13851: STATUS_PRINTER_BUSY, #</DevStatusFaxDelayedSendMemoryFull>
    -13836: STATUS_PRINTER_BUSY, #</DevStatusNoDialTone>
    -13864: STATUS_PRINTER_BUSY, #</DevStatusNoFaxAnswer>
    -13863: STATUS_PRINTER_BUSY, #</DevStatusFaxBusy>
    -13865: STATUS_PRINTER_BUSY, #</DevStatusNoDocumentSent>
    -13862: STATUS_PRINTER_BUSY, #</DevStatusFaxSendError>
    -13837: STATUS_PRINTER_BUSY, #</DevStatusT30Error>
    -13861: STATUS_PRINTER_BUSY, #</DevStatusFaxMemoryFullSend>
    -13866: STATUS_PRINTER_BUSY, #</DevStatusADFNotCleared>
    -13841: STATUS_PRINTER_BUSY, #</DevStatusNoFaxDetected>
    -13848: STATUS_PRINTER_BUSY, #</DevStatusFaxMemoryFullReceive>
    -13849: STATUS_PRINTER_BUSY, #</DevStatusFaxReceiveError>

}

def StatusType6(dev): #  LaserJet Status (XML)
    info_device_status = BytesIO()
    info_ssp = BytesIO()
    try:
        dev.getEWSUrl("/hp/device/info_device_status.xml", info_device_status)
        dev.getEWSUrl("/hp/device/info_ssp.xml", info_ssp)
    except:
        log.warn("Failed to get Device status information")
        pass

    info_device_status = info_device_status.getvalue()
    info_ssp = info_ssp.getvalue()

    device_status = {}
    ssp = {}

    if info_device_status:
        try:
            log.debug_block("info_device_status", to_string_latin(info_device_status))
            device_status = utils.XMLToDictParser().parseXML(info_device_status)
            log.debug(device_status)
        except expat.ExpatError:
            log.error("Device Status XML parse error")
            device_status = {}

    if info_ssp:
        try:
            log.debug_block("info_spp", to_string_latin(info_ssp))
            ssp = utils.XMLToDictParser().parseXML(info_ssp)
            log.debug(ssp)
        except expat.ExpatError:
            log.error("SSP XML parse error")
            ssp = {}

    status_code = device_status.get('devicestatuspage-devicestatus-statuslist-status-code-0', 0)

    if not status_code:
        status_code = ssp.get('devicestatuspage-devicestatus-statuslist-status-code-0', 0)

    black_supply_level = device_status.get('devicestatuspage-suppliesstatus-blacksupply-percentremaining', 0)
    black_supply_low = ssp.get('suppliesstatuspage-blacksupply-lowreached', 0)
    agents = []

    agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                     'type' : AGENT_TYPE_BLACK,
                     'health' : 0,
                     'level' : black_supply_level,
                     'level-trigger' : 0,
                  })

    if dev.tech_type == TECH_TYPE_COLOR_LASER:
        cyan_supply_level = device_status.get('devicestatuspage-suppliesstatus-cyansupply-percentremaining', 0)
        agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                         'type' : AGENT_TYPE_CYAN,
                         'health' : 0,
                         'level' : cyan_supply_level,
                         'level-trigger' : 0,
                      })

        magenta_supply_level = device_status.get('devicestatuspage-suppliesstatus-magentasupply-percentremaining', 0)
        agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                         'type' : AGENT_TYPE_MAGENTA,
                         'health' : 0,
                         'level' : magenta_supply_level,
                         'level-trigger' : 0,
                      })

        yellow_supply_level = device_status.get('devicestatuspage-suppliesstatus-yellowsupply-percentremaining', 0)
        agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                         'type' : AGENT_TYPE_YELLOW,
                         'health' : 0,
                         'level' : yellow_supply_level,
                         'level-trigger' : 0,
                      })

    return {'revision' :    STATUS_REV_UNKNOWN,
             'agents' :      agents,
             'top-door' :    0,
             'supply-door' : 0,
             'duplexer' :    1,
             'photo-tray' :  0,
             'in-tray1' :    1,
             'in-tray2' :    1,
             'media-path' :  1,
             'status-code' : TYPE6_STATUS_CODE_MAP.get(status_code, STATUS_PRINTER_IDLE),
           }

# PJL status codes
PJL_STATUS_MAP = {
    10001: STATUS_PRINTER_IDLE, # online
    10002: STATUS_PRINTER_OFFLINE, # offline
    10003: STATUS_PRINTER_WARMING_UP,
    10004: STATUS_PRINTER_BUSY, # self test
    10005: STATUS_PRINTER_BUSY, # reset
    10006: STATUS_PRINTER_LOW_TONER,
    10007: STATUS_PRINTER_CANCELING,
    10010: STATUS_PRINTER_SERVICE_REQUEST,
    10011: STATUS_PRINTER_OFFLINE,
    10013: STATUS_PRINTER_BUSY,
    10014: STATUS_PRINTER_REPORT_PRINTING,
    10015: STATUS_PRINTER_BUSY,
    10016: STATUS_PRINTER_BUSY,
    10017: STATUS_PRINTER_REPORT_PRINTING,
    10018: STATUS_PRINTER_BUSY,
    10019: STATUS_PRINTER_BUSY,
    10020: STATUS_PRINTER_BUSY,
    10021: STATUS_PRINTER_BUSY,
    10022: STATUS_PRINTER_REPORT_PRINTING,
    10023: STATUS_PRINTER_PRINTING,
    10024: STATUS_PRINTER_SERVICE_REQUEST,
    10025: STATUS_PRINTER_SERVICE_REQUEST,
    10026: STATUS_PRINTER_BUSY,
    10027: STATUS_PRINTER_MEDIA_JAM,
    10028: STATUS_PRINTER_REPORT_PRINTING,
    10029: STATUS_PRINTER_PRINTING,
    10030: STATUS_PRINTER_BUSY,
    10031: STATUS_PRINTER_BUSY,
    10032: STATUS_PRINTER_BUSY,
    10033: STATUS_PRINTER_SERVICE_REQUEST,
    10034: STATUS_PRINTER_CANCELING,
    10035: STATUS_PRINTER_PRINTING,
    10036: STATUS_PRINTER_WARMING_UP,
    10200: STATUS_PRINTER_LOW_BLACK_TONER,
    10201: STATUS_PRINTER_LOW_CYAN_TONER,
    10202: STATUS_PRINTER_LOW_MAGENTA_TONER,
    10203: STATUS_PRINTER_LOW_YELLOW_TONER,
    10204: STATUS_PRINTER_LOW_TONER, # order image drum
    10205: STATUS_PRINTER_LOW_BLACK_TONER, # order black drum
    10206: STATUS_PRINTER_LOW_CYAN_TONER, # order cyan drum
    10207: STATUS_PRINTER_LOW_MAGENTA_TONER, # order magenta drum
    10208: STATUS_PRINTER_LOW_YELLOW_TONER, # order yellow drum
    10209: STATUS_PRINTER_LOW_BLACK_TONER,
    10210: STATUS_PRINTER_LOW_CYAN_TONER,
    10211: STATUS_PRINTER_LOW_MAGENTA_TONER,
    10212: STATUS_PRINTER_LOW_YELLOW_TONER,
    10213: STATUS_PRINTER_SERVICE_REQUEST, # order transport kit
    10214: STATUS_PRINTER_SERVICE_REQUEST, # order cleaning kit
    10215: STATUS_PRINTER_SERVICE_REQUEST, # order transfer kit
    10216: STATUS_PRINTER_SERVICE_REQUEST, # order fuser kit
    10217: STATUS_PRINTER_SERVICE_REQUEST, # maintenance
    10218: STATUS_PRINTER_LOW_TONER,
    10300: STATUS_PRINTER_LOW_BLACK_TONER, # replace black toner
    10301: STATUS_PRINTER_LOW_CYAN_TONER, # replace cyan toner
    10302: STATUS_PRINTER_LOW_MAGENTA_TONER, # replace magenta toner
    10303: STATUS_PRINTER_LOW_YELLOW_TONER, # replace yellow toner
    10304: STATUS_PRINTER_SERVICE_REQUEST, # replace image drum
    10305: STATUS_PRINTER_SERVICE_REQUEST, # replace black drum
    10306: STATUS_PRINTER_SERVICE_REQUEST, # replace cyan drum
    10307: STATUS_PRINTER_SERVICE_REQUEST, # replace magenta drum
    10308: STATUS_PRINTER_SERVICE_REQUEST, # replace yellow drum
    10309: STATUS_PRINTER_SERVICE_REQUEST, # replace black cart
    10310: STATUS_PRINTER_SERVICE_REQUEST, # replace cyan cart
    10311: STATUS_PRINTER_SERVICE_REQUEST, # replace magenta cart
    10312: STATUS_PRINTER_SERVICE_REQUEST, # replace yellow cart
    10313: STATUS_PRINTER_SERVICE_REQUEST, # replace transport kit
    10314: STATUS_PRINTER_SERVICE_REQUEST, # replace cleaning kit
    10315: STATUS_PRINTER_SERVICE_REQUEST, # replace transfer kit
    10316: STATUS_PRINTER_SERVICE_REQUEST, # replace fuser kit
    10317: STATUS_PRINTER_SERVICE_REQUEST,
    10318: STATUS_PRINTER_SERVICE_REQUEST, # replace supplies
    10400: STATUS_PRINTER_NON_HP_INK, # [sic]
    10401: STATUS_PRINTER_IDLE,
    10402: STATUS_PRINTER_SERVICE_REQUEST,
    10403: STATUS_PRINTER_IDLE,
    # 11xyy - Background paper-loading
    # 12xyy - Background paper-tray status
    # 15xxy - Output-bin status
    # 20xxx - PJL parser errors
    # 25xxx - PJL parser warnings
    # 27xxx - PJL semantic errors
    # 30xxx - Auto continuable conditions
    30119: STATUS_PRINTER_MEDIA_JAM,
    # 32xxx - PJL file system errors
    # 35xxx - Potential operator intervention conditions
    # 40xxx - Operator intervention conditions
    40021: STATUS_PRINTER_DOOR_OPEN,
    40022: STATUS_PRINTER_MEDIA_JAM,
    40038: STATUS_PRINTER_LOW_TONER,
    40600: STATUS_PRINTER_NO_TONER,
    # 41xyy - Foreground paper-loading messages
    # 43xyy - Optional paper handling device messages
    # 44xyy - LJ 4xxx/5xxx paper jam messages
    # 50xxx - Hardware errors
    # 55xxx - Personality errors

}

MIN_PJL_ERROR_CODE = 10001
DEFAULT_PJL_ERROR_CODE = 10001

def MapPJLErrorCode(error_code, str_code=None):
    if error_code < MIN_PJL_ERROR_CODE:
        return STATUS_PRINTER_BUSY

    if str_code is None:
        str_code = str(error_code)

    if len(str_code) < 5:
        return STATUS_PRINTER_BUSY

    status_code = PJL_STATUS_MAP.get(error_code, None)

    if status_code is None:
        status_code = STATUS_PRINTER_BUSY

        if 10999 < error_code < 12000: # 11xyy - Background paper-loading
            # x = tray #
            # yy = media code
            tray = int(str_code[2])
            media = int(str_code[3:])
            log.debug("Background paper loading for tray #%d" % tray)
            log.debug("Media code = %d" % media)

        elif 11999 < error_code < 13000: # 12xyy - Background paper-tray status
            # x = tray #
            # yy = status code
            tray = int(str_code[2])
            status = int(str_code[3:])
            log.debug("Background paper tray status for tray #%d" % tray)
            log.debug("Status code = %d" % status)

        elif 14999 < error_code < 16000: # 15xxy - Output-bin status
            # xx = output bin
            # y = status code
            bin = int(str_code[2:4])
            status = int(str_code[4])
            log.debug("Output bin full for bin #%d" % bin)
            status_code = STATUS_PRINTER_OUTPUT_BIN_FULL

        elif 19999 < error_code < 28000: # 20xxx, 25xxx, 27xxx PJL errors
            status_code = STATUS_PRINTER_SERVICE_REQUEST

        elif 29999 < error_code < 31000: # 30xxx - Auto continuable conditions
            log.debug("Auto continuation condition #%d" % error_code)
            status_code = STATUS_PRINTER_BUSY

        elif 34999 < error_code < 36000: # 35xxx - Potential operator intervention conditions
            status_code = STATUS_PRINTER_SERVICE_REQUEST

        elif 39999 < error_code < 41000: # 40xxx - Operator intervention conditions
            status_code = STATUS_PRINTER_SERVICE_REQUEST

        elif 40999 < error_code < 42000: # 41xyy - Foreground paper-loading messages
            # x = tray
            # yy = media code
            tray = int(str_code[2])
            media = int(str_code[3:])
            log.debug("Foreground paper loading for tray #%d" % tray)
            log.debug("Media code = %d" % media)
            status_code = STATUS_PRINTER_OUT_OF_PAPER

        elif 41999 < error_code < 43000:
            status_code = STATUS_PRINTER_MEDIA_JAM

        elif 42999 < error_code < 44000: # 43xyy - Optional paper handling device messages
            status_code = STATUS_PRINTER_SERVICE_REQUEST

        elif 43999 < error_code < 45000: # 44xyy - LJ 4xxx/5xxx paper jam messages
            status_code = STATUS_PRINTER_MEDIA_JAM

        elif 49999 < error_code < 51000: # 50xxx - Hardware errors
            status_code = STATUS_PRINTER_HARD_ERROR

        elif 54999 < error_code < 56000 : # 55xxx - Personality errors
            status_code = STATUS_PRINTER_HARD_ERROR

    log.debug("Mapped PJL error code %d to status code %d" % (error_code, status_code))
    return status_code


pjl_code_pat = re.compile("""^CODE\s*=\s*(\d.*)$""", re.IGNORECASE)



def StatusType8(dev): #  LaserJet PJL (B&W only)
    try:
        # Will error if printer is busy printing...
        dev.openPrint()
    except Error as e:
        log.warn(e.msg)
        status_code = STATUS_PRINTER_BUSY
    else:
        try:
            try:
                dev.writePrint(to_bytes_utf8("\x1b%-12345X@PJL INFO STATUS \r\n\x1b%-12345X"))
                pjl_return = dev.readPrint(1024, timeout=5, allow_short_read=True)
                dev.close()

                log.debug_block("PJL return:", to_string_latin(pjl_return))

                str_code = '10001'

                for line in pjl_return.splitlines():
                    line = line.strip()
                    match = pjl_code_pat.match(line.decode('utf-8'))

                    if match is not None:
                        str_code = match.group(1)
                        break

                log.debug("Code = %s" % str_code)

                try:
                    error_code = int(str_code)
                except ValueError:
                    error_code = DEFAULT_PJL_ERROR_CODE

                log.debug("Error code = %d" % error_code)

                status_code = MapPJLErrorCode(error_code, str_code)
            except Error:
                status_code = STATUS_PRINTER_HARD_ERROR
        finally:
            try:
                dev.closePrint()
            except Error:
                pass

    agents = []

    # TODO: Only handles mono lasers...
    if status_code in (STATUS_PRINTER_LOW_TONER, STATUS_PRINTER_LOW_BLACK_TONER):
        health = AGENT_HEALTH_OK
        level_trigger = AGENT_LEVEL_TRIGGER_MAY_BE_LOW
        level = 0

    elif status_code == STATUS_PRINTER_NO_TONER:
        health = AGENT_HEALTH_MISINSTALLED
        level_trigger = AGENT_LEVEL_TRIGGER_MAY_BE_LOW
        level = 0

    else:
        health = AGENT_HEALTH_OK
        level_trigger = AGENT_LEVEL_TRIGGER_SUFFICIENT_0
        level = 100

    log.debug("Agent: health=%d, level=%d, trigger=%d" % (health, level, level_trigger))

    agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                     'type' : AGENT_TYPE_BLACK,
                     'health' : health,
                     'level' : level,
                     'level-trigger' : level_trigger,
                  })

    if dev.tech_type == TECH_TYPE_COLOR_LASER:
        level = 100
        level_trigger = AGENT_LEVEL_TRIGGER_SUFFICIENT_0
        if status_code == STATUS_PRINTER_LOW_CYAN_TONER:
            level = 0
            level_trigger = AGENT_LEVEL_TRIGGER_MAY_BE_LOW

        log.debug("Agent: health=%d, level=%d, trigger=%d" % (health, level, level_trigger))

        agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                         'type' : AGENT_TYPE_CYAN,
                         'health' : AGENT_HEALTH_OK,
                         'level' : level,
                         'level-trigger' : level_trigger,
                      })

        level = 100
        level_trigger = AGENT_LEVEL_TRIGGER_SUFFICIENT_0
        if status_code == STATUS_PRINTER_LOW_MAGENTA_TONER:
            level = 0
            level_trigger = AGENT_LEVEL_TRIGGER_MAY_BE_LOW

        log.debug("Agent: health=%d, level=%d, trigger=%d" % (health, level, level_trigger))

        agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                         'type' : AGENT_TYPE_MAGENTA,
                         'health' : AGENT_HEALTH_OK,
                         'level' : level,
                         'level-trigger' : level_trigger,
                      })

        level = 100
        level_trigger = AGENT_LEVEL_TRIGGER_SUFFICIENT_0
        if status_code == STATUS_PRINTER_LOW_YELLOW_TONER:
            level = 0
            level_trigger = AGENT_LEVEL_TRIGGER_MAY_BE_LOW

        log.debug("Agent: health=%d, level=%d, trigger=%d" % (health, level, level_trigger))

        agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                         'type' : AGENT_TYPE_YELLOW,
                         'health' : AGENT_HEALTH_OK,
                         'level' : level,
                         'level-trigger' : level_trigger,
                      })

    if status_code == 40021:
        top_door = 0
    else:
        top_door = 1

    log.debug("Status code = %d" % status_code)

    return { 'revision' :    STATUS_REV_UNKNOWN,
             'agents' :      agents,
             'top-door' :    top_door,
             'supply-door' : top_door,
             'duplexer' :    0,
             'photo-tray' :  0,
             'in-tray1' :    1,
             'in-tray2' :    1,
             'media-path' :  1,
             'status-code' : status_code,
           }


element_type10_xlate = { 'ink' : AGENT_KIND_SUPPLY,
                         'inkCartridge' : AGENT_KIND_HEAD_AND_SUPPLY,
                         'printhead' : AGENT_KIND_HEAD,
                         'toner' : AGENT_KIND_TONER_CARTRIDGE,
                         'tonerCartridge' : AGENT_KIND_TONER_CARTRIDGE,
                       }

pen_type10_xlate = { 'pK' : AGENT_TYPE_PG,
                     'CMY' : AGENT_TYPE_CMY,
                     'M' : AGENT_TYPE_MAGENTA,
                     'C' : AGENT_TYPE_CYAN,
                     'Y' : AGENT_TYPE_YELLOW,
                     'K' : AGENT_TYPE_BLACK,
                   }

pen_level10_xlate = { 'ok' : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                      'low' : AGENT_LEVEL_TRIGGER_MAY_BE_LOW,
                      'out' : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
                      'empty' : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
                      'missing' : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
                      'unknown' : AGENT_LEVEL_UNKNOWN,
                    }

pen_health10_xlate = { 'ok' : AGENT_HEALTH_OK,
                       'misinstalled' : AGENT_HEALTH_MISINSTALLED,
                       'missing' : AGENT_HEALTH_MISINSTALLED,
                       'unknown' : AGENT_HEALTH_UNKNOWN,
                     }


#ExtractXMLData will extract actual data from http response (Transfer-encoding:  chunked).
#For unchunked response it will not do anything.
def ExtractXMLData(data):
    if data[0:1] != b'<':
        size = -1
        temp = to_bytes_utf8("")
        while size:
            index = data.find(to_bytes_utf8('\r\n'))
            size = int(data[0:index+1], 16)
            temp = temp + data[index+2:index+2+size]
            data = data[index+2+size+2:len(data)]
        data = temp
    return data

def StatusType10FetchUrl(func, url, footer=""):
    data_fp = BytesIO()
    if footer:
        data = func(url, data_fp, footer)
    else:
        data = func(url, data_fp)
        if data:
            while data.find(to_bytes_utf8('\r\n\r\n')) != -1:
                data = data.split(to_bytes_utf8('\r\n\r\n'), 1)[1]
                if not data.startswith(to_bytes_utf8("HTTP")):
                    break

            if data:
                data = ExtractXMLData(data)
    return data

def StatusType10(func): # Low End Data Model
    status_block = { 'revision' :    STATUS_REV_UNKNOWN,
                     'agents' :      [],
                     'top-door' :    TOP_DOOR_NOT_PRESENT,
                     'supply-door' : TOP_DOOR_NOT_PRESENT,
                     'duplexer' :    DUPLEXER_NOT_PRESENT,
                     'photo-tray' :  PHOTO_TRAY_NOT_PRESENT,
                     'in-tray1' :    IN_TRAY_NOT_PRESENT,
                     'in-tray2' :    IN_TRAY_NOT_PRESENT,
                     'media-path' :  MEDIA_PATH_NOT_PRESENT,
                     'status-code' : STATUS_PRINTER_IDLE,
                   }

    if not etree_loaded and not elementtree_loaded:
        log.error("cannot get status for printer. please load ElementTree module")
        return status_block

    status_block = StatusType10Agents(func)

    temp_status_block = {}
    temp_status_block = StatusType10Media(func)
    status_block.update(temp_status_block)

    temp_status_block = {}
    temp_status_block = StatusType10Status(func)
    status_block.update(temp_status_block)

    return status_block


def StatusType10Agents(func): # Low End Data Model
    status_block = {}
    # Get the dynamic consumables configuration
    data = StatusType10FetchUrl(func, "/DevMgmt/ConsumableConfigDyn.xml")
    if not data:
        return status_block
    data = data.replace(to_bytes_utf8("ccdyn:"), to_bytes_utf8("")).replace(to_bytes_utf8("dd:"), to_bytes_utf8(""))

    # Parse the agent status XML
    agents = []
    try:
        if etree_loaded:
            tree = ElementTree.XML(data)
        if not etree_loaded and elementtree_loaded:
            tree = XML(data)
        elements = tree.findall("ConsumableInfo")
        for e in elements:
            health = AGENT_HEALTH_OK
            ink_level = 0
            agent_sku = ''
            try:
                type = e.find("ConsumableTypeEnum").text
                state = e.find("ConsumableLifeState/ConsumableState").text
                quantityState = e.find("ConsumableLifeState/MeasuredQuantityState").text

                # level
                if type == "ink" or type == "inkCartridge" or type == "toner" or type == "tonerCartridge":
                    ink_type = e.find("ConsumableLabelCode").text
                    if state != "missing":
                        try:
                           ink_level = int(e.find("ConsumablePercentageLevelRemaining").text)
                           if ink_level == 0 and quantityState == 'unknown':
                                state = "unknown"
                           elif ink_level == 0:
                               state = "empty"
                           elif ink_level <=10:
                               state = "low"

                           agent_sku = 'Unknown' #Initialize to unknown. IN some old devices, ConsumableSelectibilityNumber is not returned by device.
                        except:
                           ink_level = 0
                elif type == "printhead":
                     continue; #No need of adding this agent.
                else:
                    ink_type = ''
                    if state == "ok":
                        ink_level = 100

                try:
                    agent_sku = e.find("ProductNumber").text
                except:
                    try :
                        agent_sku = e.find("ConsumableSelectibilityNumber").text
                    except :
                        pass

                log.debug("type '%s' state '%s' ink_type '%s' ink_level %d agent_sku = %s" % (type, state, ink_type, ink_level,agent_sku))

                entry = { 'kind' : element_type10_xlate.get(type, AGENT_KIND_NONE),
                          'type' : pen_type10_xlate.get(ink_type, AGENT_TYPE_NONE),
                          'health' : pen_health10_xlate.get(state, AGENT_HEALTH_OK),
                          'level' : int(ink_level),
                          'level-trigger' : pen_level10_xlate.get(state, AGENT_LEVEL_TRIGGER_SUFFICIENT_0),
                          'agent-sku' : agent_sku
                        }

                log.debug("%s" % entry)
                agents.append(entry)
            except AttributeError:
                log.debug("no value found for attribute")
    except (expat.ExpatError, UnboundLocalError):
        agents = []
    status_block['agents'] = agents

    return status_block

def StatusType10Media(func): # Low End Data Model
    status_block = {}
    # Get the media handling configuration
    data = StatusType10FetchUrl(func, "/DevMgmt/MediaHandlingDyn.xml")
    if not data:
        return status_block
    data = data.replace(to_bytes_utf8("mhdyn:"), to_bytes_utf8("")).replace(to_bytes_utf8("dd:"), to_bytes_utf8(""))

    # Parse the media handling XML
    try:
        if etree_loaded:
            tree = ElementTree.XML(data)
        if not etree_loaded and elementtree_loaded:
            tree = XML(data)
        elements = tree.findall("InputTray")
    except (expat.ExpatError, UnboundLocalError):
        elements = []
    for e in elements:
        bin_name = e.find("InputBin").text
        if bin_name == "Tray1":
            status_block['in-tray1'] = IN_TRAY_PRESENT
        elif bin_name == "Tray2":
            status_block['in-tray2'] = IN_TRAY_PRESENT
        elif bin_name == "PhotoTray":
            status_block['photo-tray'] = PHOTO_TRAY_ENGAGED

    try:
        elements = tree.findall("Accessories/MediaHandlingDeviceFunctionType")
    except UnboundLocalError:
        elements = []
    for e in elements:
        if e.text == "autoDuplexor":
            status_block['duplexer'] = DUPLEXER_DOOR_CLOSED

    return status_block

def StatusType10Status(func): # Low End Data Model
    status_block = {}
    # Get the product status
    data = StatusType10FetchUrl(func, "/DevMgmt/ProductStatusDyn.xml")
    if not data:
        return status_block
    data = data.replace(to_bytes_utf8("psdyn:"), to_bytes_utf8("")).replace(to_bytes_utf8("locid:"), to_bytes_utf8(""))
    data = data.replace(to_bytes_utf8("pscat:"), to_bytes_utf8("")).replace(to_bytes_utf8("dd:"), to_bytes_utf8("")).replace(to_bytes_utf8("ad:"), to_bytes_utf8(""))

    # Parse the product status XML
    try:
        if etree_loaded:
            tree = ElementTree.XML(data)
        if not etree_loaded and elementtree_loaded:
            tree = XML(data)
        elements = tree.findall("Status/StatusCategory")
    except (expat.ExpatError, UnboundLocalError):
        elements = []

    for e in elements:

        if e.text == "processing":
            status_block['status-code'] = STATUS_PRINTER_PRINTING
        elif e.text == "ready":
            status_block['status-code'] = STATUS_PRINTER_IDLE
        elif e.text == "closeDoorOrCover":
            status_block['status-code'] = STATUS_PRINTER_DOOR_OPEN
        elif e.text == "shuttingDown":
            status_block['status-code'] = STATUS_PRINTER_TURNING_OFF
        elif e.text == "cancelJob":
            status_block['status-code'] = STATUS_PRINTER_CANCELING
        elif e.text == "trayEmptyOrOpen":
            status_block['status-code'] = STATUS_PRINTER_OUT_OF_PAPER
        elif e.text == "jamInPrinter":
            status_block['status-code'] = STATUS_PRINTER_MEDIA_JAM
        elif e.text == "hardError":
            status_block['status-code'] = STATUS_PRINTER_HARD_ERROR
        elif e.text == "outputBinFull":
            status_block['status-code'] = STATUS_PRINTER_OUTPUT_BIN_FULL
        elif e.text == "unexpectedSizeInTray" or e.text == "sizeMismatchInTray":
            status_block['status-code'] = STATUS_PRINTER_MEDIA_SIZE_MISMATCH
        elif e.text == "insertOrCloseTray2":
            status_block['status-code'] = STATUS_PRINTER_TRAY_2_MISSING
        elif e.text == "scannerError":
            status_block['status-code'] = EVENT_SCANNER_FAIL
        elif e.text == "scanProcessing":
            status_block['status-code'] = EVENT_START_SCAN_JOB
        elif e.text == "scannerAdfLoaded":
            status_block['status-code'] = EVENT_SCAN_ADF_LOADED
        elif e.text == "scanToDestinationNotSet":
            status_block['status-code'] = EVENT_SCAN_TO_DESTINATION_NOTSET
        elif e.text == "scanWaitingForPC":
            status_block['status-code'] = EVENT_SCAN_WAITING_FOR_PC
        elif e.text == "scannerAdfJam":
            status_block['status-code'] = EVENT_SCAN_ADF_JAM
        elif e.text == "scannerAdfDoorOpen":
            status_block['status-code'] = EVENT_SCAN_ADF_DOOR_OPEN
        elif e.text == "faxProcessing":
            status_block['status-code'] = EVENT_START_FAX_JOB
        elif e.text == "faxSending":
            status_block['status-code'] = STATUS_FAX_TX_ACTIVE
        elif e.text == "faxReceiving":
            status_block['status-code'] = STATUS_FAX_RX_ACTIVE
        elif e.text == "faxDialing":
            status_block['status-code'] = EVENT_FAX_DIALING
        elif e.text == "faxConnecting":
            status_block['status-code'] = EVENT_FAX_CONNECTING
        elif e.text == "faxSendError":
            status_block['status-code'] = EVENT_FAX_SEND_ERROR
        elif e.text == "faxErrorStorageFull":
            status_block['status-code'] = EVENT_FAX_ERROR_STORAGE_FULL
        elif e.text == "faxReceiveError":
            status_block['status-code'] = EVENT_FAX_RECV_ERROR
        elif e.text == "faxBlocking":
            status_block['status-code'] = EVENT_FAX_BLOCKING
        elif e.text == "inPowerSave":
            status_block['status-code'] = STATUS_PRINTER_POWER_SAVE
        elif e.text == "incorrectCartridge":
            status_block['status-code'] = STATUS_PRINTER_CARTRIDGE_WRONG
        elif e.text == "cartridgeMissing":
            status_block['status-code'] = STATUS_PRINTER_CARTRIDGE_MISSING
        elif e.text == "missingPrintHead":
            status_block['status-code'] = STATUS_PRINTER_PRINTHEAD_MISSING


        #Alert messages for Pentane products RQ 8888
        elif e.text == "scannerADFMispick":
            status_block['status-code'] = STATUS_SCANNER_ADF_MISPICK

        elif e.text == "mediaTooShortToAutoDuplex":
            status_block['status-code'] = STATUS_PRINTER_PAPER_TOO_SHORT_TO_AUTODUPLEX

        elif e.text == "insertOrCloseTray":
            status_block['status-code'] = STATUS_PRINTER_TRAY_2_3_DOOR_OPEN

        elif e.text == "inkTooLowToPrime":
            status_block['status-code'] = STATUS_PRINTER_INK_TOO_LOW_TO_PRIME

        elif e.text == "cartridgeVeryLow":
            status_block['status-code'] = STATUS_PRINTER_VERY_LOW_ON_INK

        elif e.text == "wasteMarkerCollectorAlmostFull":
            status_block['status-code'] = STATUS_PRINTER_SERVICE_INK_CONTAINER_ALMOST_FULL

        elif e.text == "wasteMarkerCollectorFull":
            status_block['status-code'] = STATUS_PRINTER_SERVICE_INK_CONTAINER_FULL

        elif e.text == "wasteMarkerCollectorFullPrompt":
            status_block['status-code'] = STATUS_PRINTER_SERVICE_INK_CONTAINER_FULL_PROMPT

        elif e.text == "missingDuplexer":
            status_block['status-code'] = STATUS_PRINTER_DUPLEX_MODULE_MISSING

        elif e.text == "printBarStall":
            status_block['status-code'] = STATUS_PRINTER_PRINTHEAD_JAM

        elif e.text == "outputBinClosed":
            status_block['status-code'] = STATUS_PRINTER_CLEAR_OUTPUT_AREA

        elif e.text == "outputBinOpened":
            status_block['status-code'] = STATUS_PRINTER_CLEAR_OUTPUT_AREA

        elif e.text == "reseatDuplexer":
            status_block['status-code'] = STATUS_PRINTER_RESEAT_DUPLEXER

        elif e.text == "unexpectedTypeInTray":
            status_block['status-code'] = STATUS_PRINTER_MEDIA_TYPE_MISMATCH

        elif e.text == "manuallyFeed":
            status_block['status-code'] = STATUS_MANUALLY_FEED

        else:
            status_block['status-code'] = STATUS_UNKNOWN_CODE

    return status_block

#IPP Status Code
IPP_PRINTER_STATE_IDLE = 0x03
IPP_PRINTER_STATE_PROCESSING = 0x04
IPP_PRINTER_STATE_STOPPED = 0x05

marker_kind_xlate =    { 'ink' : AGENT_KIND_SUPPLY,
                         'inkCartridge' : AGENT_KIND_SUPPLY,
                         'printhead' : AGENT_KIND_HEAD,
                         'toner' : AGENT_KIND_TONER_CARTRIDGE,
                         'tonerCartridge' : AGENT_KIND_TONER_CARTRIDGE,
                         'toner-cartridge' : AGENT_KIND_TONER_CARTRIDGE,
                         'maintenanceKit' : AGENT_KIND_MAINT_KIT,
                         'ink-cartridge' : AGENT_KIND_SUPPLY,
                       }

marker_type_xlate = {'magenta ink' : AGENT_TYPE_MAGENTA,
                     'cyan ink' : AGENT_TYPE_CYAN,
                     'yellow ink' : AGENT_TYPE_YELLOW,
                     'black ink' : AGENT_TYPE_BLACK,
                     'Black Cartridge' : AGENT_TYPE_BLACK,
                     'Magenta Cartridge' : AGENT_TYPE_MAGENTA,
                     'Cyan Cartridge' : AGENT_TYPE_CYAN,
                     'Yellow Cartridge' : AGENT_TYPE_YELLOW,
                     'Maintenance Kit' : AGENT_TYPE_NONE,
                    }

marker_leveltrigger_xlate = { 'ok' : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                              'low' : AGENT_LEVEL_TRIGGER_MAY_BE_LOW,
                              'out' : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
                              'empty' : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
                              'missing' : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
                            }

marker_state_xlate = { 'ok' : AGENT_HEALTH_OK,
                       'misinstalled' : AGENT_HEALTH_MISINSTALLED,
                       'missing' : AGENT_HEALTH_MISINSTALLED,
                     }

printer_state_reasons_xlate = { 'none' : STATUS_PRINTER_IDLE,
                               'media-needed' : STATUS_PRINTER_OUT_OF_PAPER,
                               'media-jam' : STATUS_PRINTER_MEDIA_JAM,
                               'shutdown' : STATUS_PRINTER_TURNING_OFF,
                               'toner-low' : STATUS_PRINTER_LOW_TONER,
                               'toner-empty' : STATUS_PRINTER_EMPTY_TONER,
                               'cover-open' : STATUS_PRINTER_DOOR_OPEN,
                               'door-open' : STATUS_PRINTER_DOOR_OPEN,
                               'input-tray-missing' : STATUS_PRINTER_TRAY_2_3_DOOR_OPEN,
                               'media-low' : STATUS_PRINTER_OUT_OF_PAPER,
                               'media-empty' : STATUS_PRINTER_MEDIA_EMPTY_ERROR,
                               'output-tray-missing' : STATUS_PRINTER_TRAY_2_MISSING,
                               'output-area-almost-full' : STATUS_PRINTER_CLEAR_OUTPUT_AREA,
                               'output-area-full' : STATUS_PRINTER_CLEAR_OUTPUT_AREA,
                               'marker-supply-low' : STATUS_PRINTER_VERY_LOW_ON_INK,
                               'marker-supply-empty' : STATUS_PRINTER_VERY_LOW_ON_INK,
                               'paused' : STATUS_PRINTER_PAUSED,
                               'other' : STATUS_UNKNOWN_CODE,
                             }

def StatusTypeIPPStatus(attrs):

    status_block = {}
    if not attrs:
        return status_block

    try:
        printer_state = attrs['printer-state'][0]
        printer_state_reasons = attrs['printer-state-reasons'][0]

        if printer_state == IPP_PRINTER_STATE_IDLE:
            status_block['status-code'] = STATUS_PRINTER_IDLE
        elif printer_state == IPP_PRINTER_STATE_PROCESSING:
            status_block['status-code'] = STATUS_PRINTER_PRINTING
        else:
            printer_state_reasons = printer_state_reasons.replace("-error", "")
            printer_state_reasons = printer_state_reasons.replace("-warning", "")
            printer_state_reasons = printer_state_reasons.replace("-report", "")
            status_block['status-code'] = printer_state_reasons_xlate.get(printer_state_reasons, STATUS_PRINTER_IDLE)

    except Exception as e:
        log.debug("Exception occured while updating printer-state [%s]" %e.args[0])
        status_block = {}

    return status_block


def StatusTypeIPPAgents(attrs):

    status_block = {}
    agents = []

    if not attrs:
        return status_block

    loopcntr = 0
    while(True ):
        try:
            if loopcntr >= len(attrs['marker-names']):
                break

            if attrs['marker-types'][loopcntr] == 'maintenanceKit':
                loopcntr = loopcntr + 1
                continue

            if attrs['marker-levels'][loopcntr] > attrs['marker-low-levels'][loopcntr] :
                state = 'ok'
            else:
                state = 'low'

            #match the type if marker-type is something like 'Black Cartridge HP XXXX'
            mtype = [v for k,v in marker_type_xlate.items() if attrs['marker-names'][loopcntr].startswith(k)]

            entry = { 'kind' : marker_kind_xlate.get(attrs['marker-types'][loopcntr], AGENT_KIND_NONE),
                      'type' : mtype[0] if len(mtype) > 0 else 0,
                      'health' : marker_state_xlate.get(state, AGENT_HEALTH_OK),
                      'level' : attrs['marker-levels'][loopcntr],
                      'level-trigger' : marker_leveltrigger_xlate.get(state, AGENT_LEVEL_TRIGGER_SUFFICIENT_0),
                      'agent-sku' : ''
                    }

            log.debug("%s" % entry)
            agents.append(entry)
        except AttributeError:
            log.error("no value found for attribute")
            return []

        loopcntr = loopcntr + 1

    status_block['agents'] = agents

    return status_block

def StatusTypeIPP(device_uri):
    status_block = { 'revision' :    STATUS_REV_UNKNOWN,
                     'agents' :      [],
                     'top-door' :    TOP_DOOR_NOT_PRESENT,
                     'supply-door' : TOP_DOOR_NOT_PRESENT,
                     'duplexer' :    DUPLEXER_NOT_PRESENT,
                     'photo-tray' :  PHOTO_TRAY_NOT_PRESENT,
                     'in-tray1' :    IN_TRAY_NOT_PRESENT,
                     'in-tray2' :    IN_TRAY_NOT_PRESENT,
                     'media-path' :  MEDIA_PATH_NOT_PRESENT,
                     'status-code' : STATUS_PRINTER_IDLE,
                   }

    status_attrs = cupsext.getStatusAttributes(device_uri)

    if status_attrs:
        status_block.update(StatusTypeIPPAgents(status_attrs) )
        status_block.update(StatusTypeIPPStatus (status_attrs) )

    return status_block


