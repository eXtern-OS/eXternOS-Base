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
import struct
import sys


PACKET_FRAME = ord('$')
PACKET_PAD = 0xff
CMD_HEADER_FMT = ">BHBBBHH" # 10 bytes

# Packet types
PACKET_TYPE_COMMAND = 0
PACKET_TYPE_DISABLE_PACING = 1
PACKET_TYPE_ENABLE_PACING = 2
PACKET_TYPE_RESUME_NORMAL_OPERATION = 3
PACKET_TYPE_DISABLE_RESPONSES = 4
PACKET_TYPE_ENABLE_RESPONSES = 5
PACKET_TYPE_RESET_LIDIL = 6
PACKET_TYPE_SYNC = 7
PACKET_TYPE_SYNC_COMPLETE = 8

# Commands

# Handle Pen
COMMAND_HANDLE_PEN = 8
COMMAND_HANDLE_PEN_ENTER_PEN_CHANGE = 0
COMMAND_HANDLE_PEN_COMPLETE_PEN_CHANGE = 1
COMMAND_HANDLE_PEN_CLEAN_LEVEL1 = 2
COMMAND_HANDLE_PEN_CLEAN_LEVEL2 = 3
COMMAND_HANDLE_PEN_CLEAN_LEVEL3 = 4

# Set ZCA
COMMAND_ZCA = 12
COMMAND_ZCA_OPERATION = 11

# 0.3.8 Set Printer Alignment
COMMAND_SET_PRINTER_ALIGNMENT = 12
COMMAND_SET_PRINTER_ALIGNMENT_OPERATION = 6

# 0.4.3 Set Pen Alignment
COMMAND_SET_PEN_ALIGNMENT = 12
COMMAND_SET_PEN_ALIGNMENT_OPERATION = 18
COMMAND_SET_PEN_ALIGNMENT_PEN_BLACK = 0
COMMAND_SET_PEN_ALIGNMENT_PEN_COLOR = 1
COMMAND_SET_PEN_ALIGNMENT_PEN_PHOTO = 2
COMMAND_SET_PEN_ALIGNMENT_ITEM_HORT = 0
COMMAND_SET_PEN_ALIGNMENT_ITEM_VERT = 1
COMMAND_SET_PEN_ALIGNMENT_ITEM_BIDI = 2

# Set Pens Aligned
COMMAND_SET_PENS_ALIGNED = 12
COMMAND_SET_PENS_ALIGNED_OPERATION = 14
COMMAND_SET_PENS_ALIGNED_K = 0x01
COMMAND_SET_PENS_ALIGNED_C = 0x02
COMMAND_SET_PENS_ALIGNED_M = 0x04
COMMAND_SET_PENS_ALIGNED_Y = 0x08
COMMAND_SET_PENS_ALIGNED_c = 0x10
COMMAND_SET_PENS_ALIGNED_m = 0x20
COMMAND_SET_PENS_ALIGNED_k = 0x40

# Set Hue Compensation
COMMAND_SET_HUE_COMPENSATION = 12
COMMAND_SET_HUE_COMPENSATION_OPERATION = 16
COMMAND_SET_HUE_COMPENSATION_PEN_COLOR = 0
COMMAND_SET_HUE_COMPENSATION_PEN_PHOTO = 1

# Print internal page 0.3.8 and 0.4.3
COMMAND_PRINT_INTERNAL_PAGE = 12
COMMAND_PRINT_INTERNAL_PAGE_OPERATION = 17

# 0.5.4 Report Page 
COMMAND_REPORT_PAGE = 12
COMMAND_REPORT_PAGE_OPERATION = 21
COMMAND_REPORT_PAGE_PEN_CALIBRATION = 81
COMMAND_REPORT_PAGE_PEN_CALIBRATION_VERIFY = 82

# 0.5.4 Set Pen Alignment 3
COMMAND_SET_PEN_ALIGNMENT_3 = 12
COMMAND_SET_PEN_ALIGNMENT_3_OPERATION = 23
COMMAND_SET_PEN_ALIGNMENT_3_K = 0x01
COMMAND_SET_PEN_ALIGNMENT_3_C = 0x02
COMMAND_SET_PEN_ALIGNMENT_3_M = 0x04
COMMAND_SET_PEN_ALIGNMENT_3_Y = 0x08
COMMAND_SET_PEN_ALIGNMENT_3_COLOR = 0x0e
COMMAND_SET_PEN_ALIGNMENT_3_c = 0x10
COMMAND_SET_PEN_ALIGNMENT_3_m = 0x20
COMMAND_SET_PEN_ALIGNMENT_3_k = 0x40
COMMAND_SET_PEN_ALIGNMENT_3_PHOTO = 0x70

# Printer queries
COMMAND_QUERY = 5
QUERY_PRINTER_ALIGNMENT = 3 # 0.3.8
QUERY_PEN_ALIGNMENT = 15 # 0.4.3

# 0.5.4 Dynamic counters
COMMAND_DYNAMIC_COUNTERS = 12
COMMAND_DYNAMIC_COUNTERS_OPERATION = 5


def buildLIDILPacket(packet_type, command=0, operation=0, other={}):
    p = ''

    if packet_type == PACKET_TYPE_DISABLE_PACING:
        p = '$\x00\x10\x00\x01\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff$'

    elif packet_type == PACKET_TYPE_ENABLE_PACING:
        p = '$\x00\x10\x00\x02\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff$'

    elif packet_type == PACKET_TYPE_RESUME_NORMAL_OPERATION:
        p = '$\x00\x10\x00\x03\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff$'

    elif packet_type == PACKET_TYPE_ENABLE_RESPONSES:
        p = '$\x00\x10\x00\x05\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff$'

    elif packet_type == PACKET_TYPE_DISABLE_RESPONSES:
        p = '$\x00\x10\x00\x04\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff$'

    elif packet_type == PACKET_TYPE_SYNC:
        fmt = ''.join([CMD_HEADER_FMT, 'B'*245, 'B', 'B'*2048])
        p = struct.pack(fmt, PACKET_FRAME, 256, 0, PACKET_TYPE_SYNC, 0, 0, 2048, (0,)*245, 
                         PACKET_FRAME, (0,)*2048)

    elif packet_type == PACKET_TYPE_SYNC_COMPLETE:
        p = '$\x00\x10\x00\x08\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff$'

    elif packet_type == PACKET_TYPE_RESET_LIDIL:
        p = '$\x00\x10\x00\x06\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff$'

    elif packet_type == PACKET_TYPE_COMMAND:

        if command == COMMAND_HANDLE_PEN:   
            fmt = CMD_HEADER_FMT + "BBBBBB"
            p = struct.pack(fmt, PACKET_FRAME, struct.calcsize(fmt), 0, PACKET_TYPE_COMMAND, command, 
                             0, 0, operation, PACKET_PAD, PACKET_PAD,  PACKET_PAD, PACKET_PAD, PACKET_FRAME)

        elif command == COMMAND_SET_PRINTER_ALIGNMENT and operation == COMMAND_SET_PRINTER_ALIGNMENT_OPERATION: # 0.3.8   
            fmt = CMD_HEADER_FMT + "BHBBBBBBBBBBBBB"
            b = (0, 0, other['k_bidi'], other['c_vert'], other['c_hort'], other['c_bidi'],
                        other['c_vert'], other['c_hort'], other['c_bidi'], other['c_vert'],
                        other['c_hort'], other['c_bidi'], PACKET_FRAME)

            p = struct.pack(fmt, PACKET_FRAME, struct.calcsize(fmt), 0, PACKET_TYPE_COMMAND, command, 
                             0, 0, operation, 0x0f, *b)

        elif command == COMMAND_SET_PEN_ALIGNMENT and operation == COMMAND_SET_PEN_ALIGNMENT_OPERATION: # 0.4.3
            fmt = CMD_HEADER_FMT + "BBBbBB"
            p = struct.pack(fmt, PACKET_FRAME, struct.calcsize(fmt), 0, PACKET_TYPE_COMMAND, command, 
                             0, 0, operation, other['pen'], other['item'], other['value'], 
                             PACKET_PAD, PACKET_FRAME)

        elif command == COMMAND_REPORT_PAGE and operation == COMMAND_REPORT_PAGE_OPERATION: # 0.5.4
            fmt = CMD_HEADER_FMT + "BHBBB"
            p = struct.pack(fmt, PACKET_FRAME, struct.calcsize(fmt), 0, PACKET_TYPE_COMMAND, command,
                            0, 0, operation, other['report'], PACKET_PAD, PACKET_PAD, PACKET_FRAME)

        elif command == COMMAND_ZCA and operation == COMMAND_ZCA_OPERATION:    
            fmt = CMD_HEADER_FMT + "BBhBB"
            p = struct.pack(fmt, PACKET_FRAME, struct.calcsize(fmt), 0, PACKET_TYPE_COMMAND, command, 
                             0, 0, operation, 0, other['zca'], PACKET_PAD, PACKET_FRAME)

        elif command == COMMAND_SET_PENS_ALIGNED and operation == COMMAND_SET_PENS_ALIGNED_OPERATION:
            fmt = CMD_HEADER_FMT + "BHBBB"
            p = struct.pack(fmt, PACKET_FRAME, struct.calcsize(fmt), 0, PACKET_TYPE_COMMAND, command, 
                             0, 0, operation, other['colors'], PACKET_PAD, PACKET_PAD, PACKET_FRAME)

        elif command == COMMAND_SET_HUE_COMPENSATION and operation == COMMAND_SET_HUE_COMPENSATION_OPERATION:
            fmt = CMD_HEADER_FMT + "BBbBBB"
            p = struct.pack(fmt, PACKET_FRAME, struct.calcsize(fmt), 0, PACKET_TYPE_COMMAND, command, 
                             0, 0, operation, other['which'], other['value'], PACKET_PAD, 
                             PACKET_PAD, PACKET_FRAME)

        elif command == COMMAND_QUERY:
            fmt = CMD_HEADER_FMT + "BBHBB"
            p = struct.pack(fmt, PACKET_FRAME, struct.calcsize(fmt), 0, PACKET_TYPE_COMMAND, COMMAND_QUERY, 
                             0, 0, 0, operation, 0, PACKET_PAD, PACKET_FRAME)

        elif command == COMMAND_PRINT_INTERNAL_PAGE and operation == COMMAND_PRINT_INTERNAL_PAGE_OPERATION: 
            fmt = CMD_HEADER_FMT + "BBBBBB"
            p = struct.pack(fmt, PACKET_FRAME, struct.calcsize(fmt), 0, PACKET_TYPE_COMMAND, command, 
                             0, 0, operation, PACKET_PAD, PACKET_PAD,  
                             PACKET_PAD, PACKET_PAD, PACKET_FRAME)

        elif command == COMMAND_SET_PEN_ALIGNMENT_3 and operation == COMMAND_SET_PEN_ALIGNMENT_3_OPERATION: # 0.5.4
            selections = other['selections']
            num_selections = len(selections)
            selections.append(PACKET_FRAME)
            fmt = CMD_HEADER_FMT + "BIB" + "B"*(num_selections+1)

            p = struct.pack(fmt, PACKET_FRAME, struct.calcsize(fmt), 0, PACKET_TYPE_COMMAND, command,
                            0, 0, operation, other['active_colors'], 
                            num_selections, *selections)

        elif command == COMMAND_DYNAMIC_COUNTERS and operation == COMMAND_DYNAMIC_COUNTERS_OPERATION: # 0.5.4
            fmt = CMD_HEADER_FMT + "BIB"

            p = struct.pack(fmt, PACKET_FRAME, struct.calcsize(fmt), 0, PACKET_TYPE_COMMAND, command,
                            0, 0, operation, other['counter'], PACKET_FRAME)


    assert len(p) >= 16

    return p



def buildSyncPacket():
    return buildLIDILPacket(PACKET_TYPE_SYNC)

def buildSyncCompletePacket():
    return buildLIDILPacket(PACKET_TYPE_SYNC_COMPLETE)

def buildResetPacket():
    return buildLIDILPacket(PACKET_TYPE_RESET_LIDIL)

def buildGetAlignmentValues038Packet():
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_QUERY, QUERY_PRINTER_ALIGNMENT)

def buildGetAlignmentValues043Packet():
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_QUERY, QUERY_PEN_ALIGNMENT)

def buildEnableResponsesPacket(enable=True):
    if enable:
        return buildLIDILPacket(PACKET_TYPE_ENABLE_RESPONSES)
    else:
        return buildLIDILPacket(PACKET_TYPE_DISABLE_RESPONSES)

def buildSetPrinterAlignmentPacket(k_bidi,
                                    c_vert, 
                                    c_hort, 
                                    c_bidi): # 0.3.8

    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PRINTER_ALIGNMENT,
                             COMMAND_SET_PRINTER_ALIGNMENT_OPERATION,
                             other={'c_vert' : c_vert,
                                     'c_hort' : c_hort,
                                     'c_bidi' : c_bidi,
                                     'k_bidi' : k_bidi,

                                    })

def buildPrintInternalPagePacket(): # Type 6
    return buildLIDILPacket(PACKET_TYPE_COMMAND, 
                             COMMAND_PRINT_INTERNAL_PAGE,
                             COMMAND_PRINT_INTERNAL_PAGE_OPERATION)


def buildZCAPacket(value):
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_ZCA, 
                             COMMAND_ZCA_OPERATION,  
                             other={'zca' : value})

def buildBlackBidiPacket(value): # 0.4.3
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PEN_ALIGNMENT,
                             COMMAND_SET_PEN_ALIGNMENT_OPERATION,
                             other={'pen' : COMMAND_SET_PEN_ALIGNMENT_PEN_BLACK,
                                     'item' : COMMAND_SET_PEN_ALIGNMENT_ITEM_BIDI,
                                     'value' : value})

def buildPhotoBidiPacket(value): # 0.4.3
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PEN_ALIGNMENT,
                             COMMAND_SET_PEN_ALIGNMENT_OPERATION,
                             other={'pen' : COMMAND_SET_PEN_ALIGNMENT_PEN_PHOTO,
                                     'item' : COMMAND_SET_PEN_ALIGNMENT_ITEM_BIDI,
                                     'value' : value})

def buildColorBidiPacket(value): # 0.4.3
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PEN_ALIGNMENT,
                             COMMAND_SET_PEN_ALIGNMENT_OPERATION,
                             other={'pen' : COMMAND_SET_PEN_ALIGNMENT_PEN_COLOR,
                                     'item' : COMMAND_SET_PEN_ALIGNMENT_ITEM_BIDI,
                                     'value' : value})


def buildColorHortPacket(value): # 0.4.3
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PEN_ALIGNMENT,
                             COMMAND_SET_PEN_ALIGNMENT_OPERATION,
                             other={'pen' : COMMAND_SET_PEN_ALIGNMENT_PEN_COLOR,
                                     'item' : COMMAND_SET_PEN_ALIGNMENT_ITEM_HORT,
                                     'value' :  value})

def buildColorVertPacket(value): # 0.4.3
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PEN_ALIGNMENT,
                             COMMAND_SET_PEN_ALIGNMENT_OPERATION,
                             other={'pen' : COMMAND_SET_PEN_ALIGNMENT_PEN_COLOR,
                                     'item' : COMMAND_SET_PEN_ALIGNMENT_ITEM_VERT,
                                     'value' :  value})

def buildBlackVertPacket(value): # 0.4.3
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PEN_ALIGNMENT,
                             COMMAND_SET_PEN_ALIGNMENT_OPERATION,
                             other={'pen' : COMMAND_SET_PEN_ALIGNMENT_PEN_BLACK,
                                     'item' : COMMAND_SET_PEN_ALIGNMENT_ITEM_VERT,
                                     'value' :  value})
def buildBlackHortPacket(value): # 0.4.3
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PEN_ALIGNMENT,
                             COMMAND_SET_PEN_ALIGNMENT_OPERATION,
                             other={'pen' : COMMAND_SET_PEN_ALIGNMENT_PEN_BLACK,
                                     'item' : COMMAND_SET_PEN_ALIGNMENT_ITEM_HORT,
                                     'value' :  value})

def buildPhotoHortPacket(value): # 0.4.3
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PEN_ALIGNMENT,
                             COMMAND_SET_PEN_ALIGNMENT_OPERATION,
                             other={'pen' : COMMAND_SET_PEN_ALIGNMENT_PEN_PHOTO,
                                     'item' : COMMAND_SET_PEN_ALIGNMENT_ITEM_HORT,
                                     'value' :  value})
def buildPhotoVertPacket(value): # 0.4.3
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PEN_ALIGNMENT,
                             COMMAND_SET_PEN_ALIGNMENT_OPERATION,
                             other={'pen' : COMMAND_SET_PEN_ALIGNMENT_PEN_PHOTO,
                                     'item' : COMMAND_SET_PEN_ALIGNMENT_ITEM_VERT,
                                     'value' :  value})

def buildPhotoHuePacket(value): # 0.4.3
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_HUE_COMPENSATION,
                             COMMAND_SET_HUE_COMPENSATION_OPERATION,
                             other={'which' : COMMAND_SET_HUE_COMPENSATION_PEN_PHOTO,
                                     'value' :  value})


def buildColorHuePacket(value): # 0.4.3
   return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_HUE_COMPENSATION,
                            COMMAND_SET_HUE_COMPENSATION_OPERATION,
                            other={'which' : COMMAND_SET_HUE_COMPENSATION_PEN_COLOR,
                                    'value' :  value})

def buildSetPensAlignedPacket():
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PENS_ALIGNED, 
                              COMMAND_SET_PENS_ALIGNED_OPERATION,
                              other={'colors' : COMMAND_SET_PENS_ALIGNED_C | 
                                                 COMMAND_SET_PENS_ALIGNED_M | 
                                                 COMMAND_SET_PENS_ALIGNED_Y |
                                                 COMMAND_SET_PENS_ALIGNED_c | 
                                                 COMMAND_SET_PENS_ALIGNED_m | 
                                                 COMMAND_SET_PENS_ALIGNED_k | 
                                                 COMMAND_SET_PENS_ALIGNED_K})

def buildReportPagePacket(report): # 0.5.4
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_REPORT_PAGE,
                            COMMAND_REPORT_PAGE_OPERATION,
                            other={'report': report})

def buildSetPenAlignment3Packet(active_colors, selections): # 0.5.4
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_SET_PEN_ALIGNMENT_3, 
                            COMMAND_SET_PEN_ALIGNMENT_3_OPERATION,
                            other={'active_colors': active_colors,
                                   'selections': selections,})

def buildDynamicCountersPacket(counter): # 0.5.4
    return buildLIDILPacket(PACKET_TYPE_COMMAND, COMMAND_DYNAMIC_COUNTERS,
                            COMMAND_DYNAMIC_COUNTERS_OPERATION,
                            other={'counter': counter,})

if __name__ == "__main__":

    pass    


