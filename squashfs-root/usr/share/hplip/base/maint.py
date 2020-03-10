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
# Author: Don Welch, Naga Samrat Chowdary Narla,
#

# NOTE: Not used by Qt4 code. Use maint_*.py modules instead.

# Local
from .g import *
from .codes import *
from . import status, pml
from prnt import pcl, ldl, colorcal
import time
from .sixext import to_bytes_utf8, StringIO

# ************************* LEDM Clean**************************************** #
CleanXML = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!--  THIS DATA SUBJECT TO DISCLAIMER(S)INCLUDED WITH THE PRODUCT OF ORIGIN. -->
<ipcap:InternalPrintCap xmlns:ipcap=\"http://www.hp.com/schemas/imaging/con/ledm/internalprintcap/2008/03/21\" xmlns:ipdyn=\"http://www.hp.com/schemas/imaging/con/ledm/internalprintdyn/2008/03/21\" xmlns:dd=\"http://www.hp.com/schemas/imaging/con/dictionaries/1.0/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.hp.com/schemas/imaging/con/ledm/internalprintcap/2008/03/21 ../schemas/InternalPrintCap.xsd http://www.hp.com/schemas/imaging/con/ledm/internalprintdyn/2008/03/21 ../schemas/InternalPrintDyn.xsd http://www.hp.com/schemas/imaging/con/dictionaries/1.0/ ../schemas/dd/DataDictionaryMasterLEDM.xsd\">
                                <ipdyn:JobType>%s</ipdyn:JobType>
</ipcap:InternalPrintCap>\"

        """

status_xml = '/DevMgmt/InternalPrintDyn.xml'
LEDM_CLEAN_CAP_XML = '/DevMgmt/InternalPrintCap.xml'
LEDM_CLEAN_VERIFY_PAGE_JOB="<ipdyn:JobType>cleaningVerificationPage</ipdyn:JobType>"
# **************************************************************************** #

# ********************** Align **********************

def AlignType1(dev, loadpaper_ui): # Auto VIP (using embedded PML)
    ok = loadpaper_ui()
    if ok:
        dev.writeEmbeddedPML(pml.OID_AUTO_ALIGNMENT,
                             pml.AUTO_ALIGNMENT, style=0,
                             direct=True)
        dev.closePrint()

    return ok

def AlignType1PML(dev, loadpaper_ui): # Auto VIP (using PML)
    ok = loadpaper_ui()
    if ok:
        dev.setPML(pml.OID_AUTO_ALIGNMENT, pml.AUTO_ALIGNMENT)
        dev.closePML()

    return ok



def AlignType2(dev, loadpaper_ui, align_ui, bothpens_ui): # 8xx
    state, a, b, c, d = 0, 6, 6, 3, 3
    ok = False
    while state != -1:
        if state == 0:
            state = 1
            pens = dev.getStatusFromDeviceID()['agents']
            pen_types = [pens[x] for x in range(len(pens))]
            if AGENT_TYPE_NONE in pen_types:
                log.error("Cannot perform alignment with 0 or 1 pen installed.")
                state = 100

        elif state == 1:
            state = -1
            ok = loadpaper_ui()
            if ok:
                state = 2

        elif state == 2:
            state = -1
            alignType2Phase1(dev)
            ok, a = align_ui('A', 'h', 'kc', 2, 11)
            if ok:
                state = 3

        elif state == 3:
            state = -1
            ok, b = align_ui('B', 'v', 'kc', 2, 11)
            if ok:
                state = 4

        elif state == 4:
            state = -1
            ok, c = align_ui('C', 'v', 'kc', 2, 5)
            if ok:
                state = 5

        elif state == 5:
            state = -1
            ok, d = align_ui('D', 'v', 'c', 2, 5)
            if ok:
                state = 6

        elif state == 6:
            ok = loadpaper_ui()
            if ok:
                alignType2Phase2(dev, a, b, c, d)
            state = -1

        elif state == 100:
            ok = False
            bothpens_ui()
            state = -1

    return ok



def AlignType3(dev, loadpaper_ui, align_ui, paperedge_ui, align_type): # 9xx
    state, a, b, c, d, zca = 0, 6, 6, 3, 3, 6
    ok = False
    while state != -1:
        if state == 0:
            state = -1
            ok = loadpaper_ui()
            if ok:
                alignType3Phase1(dev)
                state = 1

        elif state == 1:
            state = -1
            ok, a = align_ui('A', 'h', 'kc', 2, 11)
            if ok:
                state = 2

        elif state == 2:
            state = -1
            ok, b = align_ui('B', 'v', 'kc', 2, 11)
            if ok:
                state = 3

        elif state == 3:
            state = -1
            ok, c = align_ui('C', 'v', 'k', 2, 11)
            if ok:
                state = 4

        elif state == 4:
            state = -1
            ok, d = align_ui('D', 'v', 'kc', 2, 11)
            if ok:
                state = 5

        elif state == 5:
            state = -1
            alignType3Phase2(dev, a, b, c, d)
            if align_type == 9:
                state = 7
            else:
                ok = loadpaper_ui()
                if ok:
                    state = 6

        elif state == 6:
            state = -1
            alignType3Phase3(dev)
            ok, zca = paperedge_ui(13)
            if ok:
                state = 7

        elif state == 7:
            ok = loadpaper_ui()
            if ok:
                alignType3Phase4(dev, zca)
            state = -1

    return ok


def AlignxBow(dev, align_type, loadpaper_ui, align_ui, paperedge_ui,
               invalidpen_ui, coloradj_ui): # Types 4, 5, and 7

    state, statepos = 0, 0
    user_cancel_states = [1000, -1]
    a, b, c, d, e, f, g = 0, 0, 0, 0, 0, 0, 0
    error_states = [-1]
    ok = False

    dev.pen_config = status.getPenConfiguration(dev.getStatusFromDeviceID())

    if dev.pen_config in (AGENT_CONFIG_NONE, AGENT_CONFIG_INVALID):
        state, states = 100, [-1]

    elif dev.pen_config == AGENT_CONFIG_BLACK_ONLY:
        state, states = 0, [2, 200, 3, -1]

    elif dev.pen_config == AGENT_CONFIG_PHOTO_ONLY:
        state, states = 0, [2, 200, 3, -1]

    elif dev.pen_config == AGENT_CONFIG_COLOR_ONLY:
        state, states = 0, [2, 300, 3, -1]

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        state, states = 0, [2, 400, 500, 600, 700, 3, 4, -1]

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_PHOTO:
        state, states = 0, [2, 400, 500, 600, 700, 800, 900, 3, 4, -1]

    while state != -1:

        if state == 0:
            ok = loadpaper_ui()
            if ok:
                if align_type == 4:
                    alignType4Phase1(dev)
                elif align_type == 5:
                    alignType5Phase1(dev)
                elif align_type == 7:
                    alignType7Phase1(dev)
                else:
                    statepos, states = 0, error_states
            else:
                statepos, states = 0, user_cancel_states


        elif state == 2:
            ok, a = paperedge_ui(13)
            if not ok:
                statepos, states = 0, user_cancel_states

        elif state == 3:
            if align_type == 4:
                alignType4Phase2(dev, a, b, c, d, e)
            elif align_type == 5:
                alignType5Phase2(dev, a, b, c, d, e, f, g)
            else:
                alignType7Phase2(dev, a, b, c, d, e, f, g)

        elif state == 4:
            ok = loadpaper_ui()
            if ok:
                if align_type == 4:
                    alignType4Phase3(dev)
                elif align_type == 5:
                    alignType5Phase3(dev)
                else:
                    alignType7Phase3(dev)
            else:
                statepos, states = 0, user_cancel_states

        elif state == 100:
            invalidpen_ui()
            state = -1

        elif state == 200: # B Line - Black only or photo only
            ok, b = align_ui('B', 'v', 'k', 2, 11)
            if not ok:
                statepos, states = 0, user_cancel_states

        elif state == 300: # B Line - Color only
            ok, b = align_ui('B', 'v', 'kc', 2, 11)
            if not ok:
                statepos, states = 0, user_cancel_states

        elif state == 400: # B Line - 2 pen
            ok, b = align_ui('B', 'h', 'kc', 2, 17)
            if not ok:
                statepos, states = 0, user_cancel_states

        elif state == 500: # C Line
            ok, c = align_ui('C', 'v', 'kc', 2, 17)
            if not ok:
                statepos, states = 0, user_cancel_states

        elif state == 600 : # D Line
            ok, d = align_ui('D', 'v', 'k', 2, 11)
            if not ok:
                statepos, states = 0, user_cancel_states

        elif state == 700: # E Line
            ok, e = align_ui('E', 'v', 'kc', 2, 11)
            if not ok:
                statepos, states = 0, user_cancel_states

        elif state == 800: # F Line
            ok, f = coloradj_ui('F', 21)
            if not ok:
                statepos, states = 0, user_cancel_states

        elif state == 900: # G Line
            ok, f = coloradj_ui('G', 21)
            if not ok:
                statepos, states = 0, user_cancel_states

        elif state == 1000: # User cancel
            ok = False
            log.warning("Alignment canceled at user request.")

        state = states[statepos]
        statepos += 1

    return ok


def AlignType6(dev, ui1, ui2, loadpaper_ui):
    state = 0
    ok = False

    while state != -1:
        if state == 0:
            state = 2
            accept = ui1()
            if not accept:
                # Need to printout alignment page
                state = 1

        elif state == 1: # Load and print
            state = -1
            ok = loadpaper_ui()
            if ok:
                alignType6Phase1(dev)
                state = 2

        elif state == 2: # Finish
            ui2()
            state = -1


    return ok

def AlignType8(dev, loadpaper_ui, align_ui): # 450
    state, a, b, c, d = 0, 5, 5, 5, 5
    ok = False

    while state != -1:

        if state == 0:
            state = -1
            ok = loadpaper_ui()
            if ok:
                num_inks = alignType8Phase1(dev)
                state = 1

        elif state == 1:
            state = -1
            ok, a = align_ui('A', 'v', 'k', 3, 9)
            if ok:
                state = 2

        elif state == 2:
            state = -1
            ok, b = align_ui('B', 'v', 'c', 3, 9)
            if ok:
                state = 3

        elif state == 3:
            state = -1
            ok, c = align_ui('C', 'v', 'kc', 3, 9)
            if ok:
                state = 4

        elif state == 4:
            state = -1
            ok, d = align_ui('D', 'h', 'kc', 3, 9)
            if ok:
                state = 5

        elif state == 5:
            alignType8Phase2(dev, num_inks, a, b, c, d)
            state = -1

    return ok


def AlignType10(dev, loadpaper_ui, align_ui):
    pattern = alignType10SetPattern(dev)
    state = 0

    while state != -1:
        if state == 0:
            state = -1
            ok = loadpaper_ui()
            if ok:
                alignType10Phase1(dev)
                state = 1

        elif state == 1:
            values = align_ui(pattern, ALIGN_TYPE_LBOW)
            log.debug(values)
            alignType10Phase2(dev, values, pattern)
            state = 2

        elif state == 2:
            state = -1
            ok = loadpaper_ui()
            if ok:
                alignType10Phase3(dev)


def alignType10SetPattern(dev):
    pattern = None
    pen_config = status.getPenConfiguration(dev.getStatusFromDeviceID())
    log.debug("Pen config=%d" % pen_config)

    if pen_config == AGENT_CONFIG_BLACK_ONLY:
        pattern = 1

    elif pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        pattern = 2

    elif pen_config in (AGENT_CONFIG_COLOR_AND_PHOTO, AGENT_CONFIG_COLOR_AND_GREY):
        pattern = 3

    log.debug("Pattern=%d" % pattern)
    return pattern


def alignType10Phase1(dev):
    dev.writeEmbeddedPML(pml.OID_PRINT_INTERNAL_PAGE,
                         pml.PRINT_INTERNAL_PAGE_ALIGNMENT_PAGE)

    dev.closePrint()


def alignType10Phase2(dev, values, pattern):
    i, p = 0, ''.join([pcl.UEL, '\n'])

    for x in values:
        i += 1
        if not x:
            break
        p = ''.join([p, pcl.ESC, '*o5W\x1a', chr(i), '\x00', chr(pattern), chr(x), '\n'])

    p = ''.join([p, pcl.UEL])

    dev.printData(p)
    dev.closePrint()


def alignType10Phase3(dev):
    dev.writeEmbeddedPML(pml.OID_PRINT_INTERNAL_PAGE,
                         pml.PRINT_INTERNAL_PAGE_ALIGNMENT_PAGE_VERIFICATION)

    dev.closePrint()


def align10and11and14Controls(pattern, align_type):
    if align_type == ALIGN_TYPE_LIDIL_0_5_4:
        if pattern == 1:
            controls = { 'A' : (True, 23),
                         'B' : (True, 9),
                         'C' : (True, 9),
                         'D' : (False, 0),
                         'E' : (False, 0),
                         'F' : (False, 0),
                         'G' : (False, 0),
                         'H' : (False, 0),}
        elif pattern == 2: # K + color (ii)
            controls = { 'A' : (True, 17),
                         'B' : (True, 23),
                         'C' : (True, 23),
                         'D' : (True, 23),
                         'E' : (True, 9),
                         'F' : (True, 9),
                         'G' : (True, 9),
                         'H' : (True, 9),}

        elif pattern == 3: # color + photo (iii)
            controls = { 'A' : (True, 9),
                         'B' : (True, 23),
                         'C' : (True, 23),
                         'D' : (True, 23),
                         'E' : (True, 9),
                         'F' : (True, 9),
                         'G' : (True, 9),
                         'H' : (True, 9),}

    elif align_type == ALIGN_TYPE_LIDIL_DJ_D1600:
        if pattern == 1:
            controls = { 'A' : (True, 23),
                         'B' : (True, 9),}
        elif pattern == 2: # K + color (ii)
            controls = { 'A' : (True, 23),
                         'B' : (True, 11),
                         'C' : (True, 23),
                         'D' : (True, 23),
                         'E' : (True, 11),
                         'F' : (True, 11),
                         'G' : (True, 11),
                         'H' : (True, 9),
                         'I' : (True, 9),}

        elif pattern == 3: # color + photo (iii)
            controls = { 'A' : (True, 9),
                         'B' : (True, 23),
                         'C' : (True, 23),
                         'D' : (True, 23),
                         'E' : (True, 9),
                         'F' : (True, 9),
                         'G' : (True, 9),
                         'H' : (True, 9),
                         'I' : (True, 9),}

    else:
        if pattern == 1:
            controls = {'A' : (True, 23),
                         'B' : (True, 9),
                         'C' : (True, 9),
                         'D' : (False, 0),
                         'E' : (False, 0),
                         'F' : (False, 0),
                         'G' : (False, 0),
                         'H' : (False, 0),}
        elif pattern == 2:
            controls = {'A' : (True, 23),
                        'B' : (True, 17),
                         'C' : (True, 23),
                         'D' : (True, 23),
                         'E' : (True, 9),
                         'F' : (True, 9),
                         'G' : (True, 9),
                         'H' : (True, 9),}

        elif pattern == 3:
            controls = {'A' : (True, 23),
                         'B' : (True, 9),
                         'C' : (True, 23),
                         'D' : (True, 23),
                         'E' : (True, 9),
                         'F' : (True, 9),
                         'G' : (True, 9),
                         'H' : (True, 9),}

    return controls


def AlignType11(dev, loadpaper_ui, align_ui, invalidpen_ui):
    pattern = alignType11SetPattern(dev)
    if pattern is None:
        invalidpen_ui()
        return

    state = 0
    while state != -1:
        if state == 0:
            state = -1
            ok = loadpaper_ui()
            if ok:
                alignType11Phase1(dev)
                state = 1

        elif state == 1:
            values = align_ui(pattern, ALIGN_TYPE_LIDIL_0_5_4)
            log.debug(values)
            alignType11Phase2(dev, values, pattern, dev.pen_config)
            state = 2

        elif state == 2:
            state = -1
            ok = loadpaper_ui()
            if ok:
                alignType11Phase3(dev)


def alignType11SetPattern(dev):
    pattern = None
    dev.pen_config = status.getPenConfiguration(dev.getStatusFromDeviceID())
    log.debug("Pen config=%d" % dev.pen_config)

    if dev.pen_config in (AGENT_CONFIG_BLACK_ONLY, AGENT_CONFIG_COLOR_ONLY): # (i)
        pattern = 1

    if dev.pen_config == AGENT_CONFIG_COLOR_AND_BLACK: # (ii)
        pattern = 2

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_PHOTO: # (iii)
        pattern = 3

    elif dev.pen_config == AGENT_CONFIG_PHOTO_ONLY:
        return None

    log.debug("Pattern=%d" % pattern)
    return pattern


def alignType11Phase1(dev):
    dev.printData(ldl.buildResetPacket())
    dev.printData(ldl.buildReportPagePacket(ldl.COMMAND_REPORT_PAGE_PEN_CALIBRATION))
    dev.closePrint()


def alignType11Phase2(dev, values, pattern, pen_config):
    active_colors = 0

    if pen_config == AGENT_CONFIG_BLACK_ONLY:
        active_colors = ldl.COMMAND_SET_PEN_ALIGNMENT_3_K
        values = values[:3]

    elif pen_config == AGENT_CONFIG_COLOR_ONLY:
        active_colors = ldl.COMMAND_SET_PEN_ALIGNMENT_3_COLOR
        values = values[:3]

    elif pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        active_colors = ldl.COMMAND_SET_PEN_ALIGNMENT_3_K | ldl.COMMAND_SET_PEN_ALIGNMENT_3_COLOR

    elif pen_config == AGENT_CONFIG_COLOR_AND_PHOTO:
        active_colors = ldl.COMMAND_SET_PEN_ALIGNMENT_3_COLOR | ldl.COMMAND_SET_PEN_ALIGNMENT_3_PHOTO

    log.debug("Active colors=0x%x Values=%s" % (active_colors, values))

    dev.printData(ldl.buildSetPenAlignment3Packet(active_colors, values))
    dev.closePrint()

def alignType11Phase3(dev):
    dev.printData(ldl.buildResetPacket())
    dev.printData(ldl.buildReportPagePacket(ldl.COMMAND_REPORT_PAGE_PEN_CALIBRATION_VERIFY))
    dev.closePrint()


def AlignType13(dev, loadpaper_ui, scanner_align_load_ui): # Auto AiO (Yellowtail)
    ok = loadpaper_ui()
    if ok:
        alignType13Phase1(dev)
        ok = scanner_align_load_ui()

    return ok

def alignType13Phase1(dev):
    dev.setPML(pml.OID_AUTO_ALIGNMENT, pml.AUTO_ALIGNMENT)
    dev.closePML()

calibrationSession = 1

def dataModelHelper(dev, func, ui2):
    data = status.StatusType10FetchUrl(func, "/Calibration/State")
    if not data:
        data = status.StatusType10FetchUrl(func, "/Calibration/State")

    if not data:
        log.debug("Unable to retrieve calibration state")
        dev.close()
        return 0

    if to_bytes_utf8("ParmsRequested") in data:
        log.error("Restart device and start alignment")
        dev.close()
        return 1

    if to_bytes_utf8("404 Not Found") in data:
        log.error("Device may not support Alignment")
        dev.close()
        return 1

    if to_bytes_utf8("Printing<") in data:
        log.warn("Previous alignment job not completed")
        dev.close()
        return 1

    data = status.StatusType10FetchUrl(func, "/DevMgmt/ConsumableConfigDyn.xml")
    if to_bytes_utf8("AlignmentMode") not in data:
        log.error("Device may not support Alignment")
        dev.close()
        return 1

    if to_bytes_utf8("automatic") in data:
        log.debug("Device supports automatic calibration")
        status.StatusType10FetchUrl(func, "/Calibration/Session", "<cal:CalibrationState xmlns:cal=\\\"http://www.hp.com/schemas/imaging/con/cnx/markingagentcalibration/2009/04/08\\\" xmlns:dd=\\\"http://www.hp.com/schemas/imaging/con/dictionaries/1.0/\\\">Printing</cal:CalibrationState>")
        dev.close()
        return 0

    if to_bytes_utf8("semiAutomatic") in data:
        log.debug("Device supports semiAutomatic calibration")
        status.StatusType10FetchUrl(func, "/Calibration/Session", "<cal:CalibrationState xmlns:cal=\\\"http://www.hp.com/schemas/imaging/con/cnx/markingagentcalibration/2009/04/08\\\" xmlns:dd=\\\"http://www.hp.com/schemas/imaging/con/dictionaries/1.0/\\\">Printing</cal:CalibrationState>")
        dev.close()
        return ui2()

    if to_bytes_utf8("manual") in data:
        log.debug("Device supports manual calibration")
        data = status.StatusType10FetchUrl(func, "/Calibration/Session", "<cal:CalibrationState xmlns:cal=\\\"http://www.hp.com/schemas/imaging/con/cnx/markingagentcalibration/2009/04/08\\\" xmlns:dd=\\\"http://www.hp.com/schemas/imaging/con/dictionaries/1.0/\\\">Printing</cal:CalibrationState>")
        import string
        data = string.split(data, "/Jobs")[1]
        data = string.split(data, "\r\n")[0]
        data = "/Jobs" + data
        data = status.StatusType10FetchUrl(func, data)
        data = string.split(data, "Session/")[1]
        data = string.split(data, "<")[0]
        data = "/Calibration/Session/" + data + "/ManualSelectedPatterns.xml"
        global calibrationSession
        calibrationSession = data
        dev.close()
    return 0

def AlignType16Manual(dev, a, b, c, d, e, f, g, h, i, j):
    log.debug("a=%s b=%s c=%s d=%s e=%s f=%s g=%s h=%s i=%s j=%s" % (a, b, c, d, e, f, g, h, i, j ))
    func = dev.getEWSUrl_LEDM
    data = status.StatusType10FetchUrl(func, "/Calibration/State")

    if not data:
        return 0

    while "ParmsRequested" not in data:
        if "CalibrationValid" in data:
            return
        data = status.StatusType10FetchUrl(func, "/Calibration/State")
    data = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!-- THIS DATA SUBJECT TO DISCLAIMER(S) INCLUDED WITH THE PRODUCT OF ORIGIN. -->\n<ManualSelectedPatterns xmlns=\"http://www.hp.com/schemas/imaging/con/cnx/markingagentcalibration/2009/04/08\" xmlns:locid=\"http://www.hp.com/schemas/imaging/con/ledm/localizationids/2007/10/31/\" xmlns:psdyn=\"http://www.hp.com/schemas/imaging/con/ledm/productstatdyn/2007/10/31\"><SelectedPattern><Identifier><Id>1</Id></Identifier><Choice><Identifier><Id>%s</Id></Identifier></Choice></SelectedPattern><SelectedPattern><Identifier><Id>2</Id></Identifier><Choice><Identifier><Id>%s</Id></Identifier></Choice></SelectedPattern><SelectedPattern><Identifier><Id>3</Id></Identifier><Choice><Identifier><Id>%s</Id></Identifier></Choice></SelectedPattern><SelectedPattern><Identifier><Id>4</Id></Identifier><Choice><Identifier><Id>%s</Id></Identifier></Choice></SelectedPattern><SelectedPattern><Identifier><Id>5</Id></Identifier><Choice><Identifier><Id>%s</Id></Identifier></Choice></SelectedPattern><SelectedPattern><Identifier><Id>6</Id></Identifier><Choice><Identifier><Id>%s</Id></Identifier></Choice></SelectedPattern><SelectedPattern><Identifier><Id>7</Id></Identifier><Choice><Identifier><Id>%s</Id></Identifier></Choice></SelectedPattern><SelectedPattern><Identifier><Id>8</Id></Identifier><Choice><Identifier><Id>%s</Id></Identifier></Choice></SelectedPattern><SelectedPattern><Identifier><Id>9</Id></Identifier><Choice><Identifier><Id>%s</Id></Identifier></Choice></SelectedPattern></SelectedPattern><SelectedPattern><Identifier><Id>10</Id></Identifier><Choice><Identifier><Id>%s</Id></Identifier></Choice></SelectedPattern></ManualSelectedPattern>" % ( a, b, c, d, e, f, g, h, i, j )
    data = "PUT %s HTTP/1.1\r\nHost: localhost\r\nUser-Agent: hp\r\nAccept: text/plain\r\nAccept-Language: en-us,en\r\nAccept-Charset:utf-8\r\nContent-Type: text/xml\r\nContent-Length: %s\r\n\r\n" % ( calibrationSession, len(data)) + data
    data = status.StatusType10FetchUrl(func, calibrationSession, data)

def AlignType15(dev, loadpaper_ui, ui2):
    if not loadpaper_ui():
        return
    return dataModelHelper(dev, dev.getEWSUrl_LEDM, ui2)

def AlignType15Phase1(dev, ui2):
    return dataModelHelper(dev, dev.getEWSUrl_LEDM, ui2)

#AlignType 17 is LEDM via FF/CC/0 USB channel
def AlignType17(dev, loadpaper_ui, ui2):
    if not loadpaper_ui():
        return
    return dataModelHelper(dev, dev.getUrl_LEDM, ui2)

def AlignType17Phase1(dev, ui2):
    return dataModelHelper(dev, dev.getUrl_LEDM, ui2)

def AlignType16(dev, loadpaper_ui, align_ui):
    if not loadpaper_ui():
        return
    dataModelHelper(dev, dev.getEWSUrl_LEDM, align_ui)
    state, a, b, c, d, e, f, g, h, i, j = 0, 6, 6, 3, 3, 6, 6, 6, 6, 6, 6
    ok = False
    while state != -1:
        if state == 0:
            state = -1
            ok, a = align_ui('A', 'v', 'kc', 3, 23)
            if ok:
                state = 1

        elif state == 1:
            state = -1
            ok, b = align_ui('B', 'h', 'kc', 3, 17)
            if ok:
                state = 2

        elif state == 2:
            state = -1
            ok, c = align_ui('C', 'v', 'k', 3, 23)
            if ok:
                state = 3

        elif state == 3:
            state = -1
            ok, d = align_ui('D', 'v', 'c', 3, 23)
            if ok:
                state = 4

        elif state == 4:
            state = -1
            ok, e = align_ui('E', 'h', 'k', 3, 11)
            if ok:
                state = 5

        elif state == 5:
            state = -1
            ok, f = align_ui('F', 'h', 'k', 3, 11)
            if ok:
                state = 6

        elif state == 6:
            state = -1
            ok, g = align_ui('G', 'h', 'k', 3, 11)
            if ok:
                state = 7

        elif state == 7:
            state = -1
            ok, h = align_ui('H', 'h', 'k', 3, 11)
            if ok:
                state = 8

        elif state == 8:
            state = -1
            ok, i = align_ui('I', 'v', 'k', 3, 19)
            if ok:
                state = 9

        elif state == 9:
            state = -1
            ok, j = align_ui('J', 'v', 'k', 3, 19)
            if ok:
                state = 10

        elif state == 10:
            state = -1

    AlignType16Manual(dev, a, b, c, d, e, f, g, h, i, j)

    return ok

def AlignType16Phase1(dev, a, b, c, d, e, f, g, h, i, j):
    AlignType16Manual(dev, a, b, c, d, e, f, g, h, i, j)

def AlignType14(dev, loadpaper_ui, align_ui, invalidpen_ui):
    pattern = alignType14SetPattern(dev)
    if pattern is None:
        invalidpen_ui()
        return

    state = 0
    while state != -1:
        if state == 0:
            state = -1
            ok = loadpaper_ui()
            if ok:
                alignType14Phase1(dev)
                state = 1

        elif state == 1:
            values = align_ui(pattern, ALIGN_TYPE_LIDIL_DJ_D1600)
            log.debug(values)
            alignType14Phase2(dev, values, pattern, dev.pen_config)
            state = 2

        elif state == 2:
            state = -1
            ok = loadpaper_ui()
            if ok:
                alignType14Phase3(dev)


def alignType14SetPattern(dev):
    pattern = None
    dev.pen_config = status.getPenConfiguration(dev.getStatusFromDeviceID())
    log.debug("Pen config=%d" % dev.pen_config)

    if dev.pen_config in (AGENT_CONFIG_BLACK_ONLY, AGENT_CONFIG_COLOR_ONLY): # (i)
        pattern = 1

    if dev.pen_config == AGENT_CONFIG_COLOR_AND_BLACK: # (ii)
        pattern = 2

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_PHOTO: # (iii)
        pattern = 3

    elif dev.pen_config == AGENT_CONFIG_PHOTO_ONLY:
        return None

    log.debug("Pattern=%d" % pattern)
    return pattern


def alignType14Phase1(dev):
    dev.printData(ldl.buildResetPacket())
    dev.printData(ldl.buildReportPagePacket(ldl.COMMAND_REPORT_PAGE_PEN_CALIBRATION))
    dev.closePrint()


def alignType14Phase2(dev, values, pattern, pen_config):
    active_colors = 0

    if pen_config == AGENT_CONFIG_BLACK_ONLY:
        active_colors = ldl.COMMAND_SET_PEN_ALIGNMENT_3_K
        values = values[:2]

    elif pen_config == AGENT_CONFIG_COLOR_ONLY:
        active_colors = ldl.COMMAND_SET_PEN_ALIGNMENT_3_COLOR
        values = values[:2]

    elif pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        active_colors = ldl.COMMAND_SET_PEN_ALIGNMENT_3_K | ldl.COMMAND_SET_PEN_ALIGNMENT_3_COLOR

    elif pen_config == AGENT_CONFIG_COLOR_AND_PHOTO:
        active_colors = ldl.COMMAND_SET_PEN_ALIGNMENT_3_COLOR | ldl.COMMAND_SET_PEN_ALIGNMENT_3_PHOTO

    log.debug("Active colors=0x%x Values=%s" % (active_colors, values))

    dev.printData(ldl.buildSetPenAlignment3Packet(active_colors, values))
    dev.closePrint()

def alignType14Phase3(dev):
    dev.printData(ldl.buildResetPacket())
    dev.printData(ldl.buildReportPagePacket(ldl.COMMAND_REPORT_PAGE_PEN_CALIBRATION_VERIFY))
    dev.closePrint()


def alignType2Phase1(dev): # Type 2 (8xx)
    dev.writeEmbeddedPML(pml.OID_AGENT2_VERTICAL_ALIGNMENT, 0)
    dev.writeEmbeddedPML(pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, 0)
    dev.writeEmbeddedPML(pml.OID_AGENT1_BIDIR_ADJUSTMENT, 0)
    dev.writeEmbeddedPML(pml.OID_AGENT2_BIDIR_ADJUSTMENT, 0)
    dev.closePrint()
    dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'pcl', 'align1_8xx.pcl.gz'))


def alignType2Phase2(dev, a, b, c, d): # (8xx)
    dev.writeEmbeddedPML(pml.OID_AGENT2_VERTICAL_ALIGNMENT, (a - 6) * 12)
    dev.writeEmbeddedPML(pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, (b - 6) * 12)
    dev.writeEmbeddedPML(pml.OID_AGENT1_BIDIR_ADJUSTMENT, (c - 3) * 12)
    dev.writeEmbeddedPML(pml.OID_AGENT2_BIDIR_ADJUSTMENT, (d - 3) * 12)
    dev.writeEmbeddedPML(pml.OID_MARKING_AGENTS_INITIALIZED, 3)
    dev.closePrint()
    dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'pcl', 'align2_8xx.pcl.gz'))


def alignType3Phase1(dev): # Type 3 (9xx)
    dev.writeEmbeddedPML(pml.OID_AGENT2_VERTICAL_ALIGNMENT, 0)
    dev.writeEmbeddedPML(pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, 0)
    dev.writeEmbeddedPML(pml.OID_AGENT1_BIDIR_ADJUSTMENT, 0)
    dev.writeEmbeddedPML(pml.OID_AGENT2_BIDIR_ADJUSTMENT, 0)
    dev.closePrint()
    dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'pcl', 'align1_9xx.pcl.gz'))


def alignType3Phase2(dev, a, b, c, d): # Type 3 (9xx)
    dev.writeEmbeddedPML(pml.OID_AGENT2_VERTICAL_ALIGNMENT, (a - 6) * 12)
    dev.writeEmbeddedPML(pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, (6 - b) * 12)
    dev.writeEmbeddedPML(pml.OID_AGENT1_BIDIR_ADJUSTMENT, (6 - c) * 12)
    dev.writeEmbeddedPML(pml.OID_AGENT2_BIDIR_ADJUSTMENT, (6 - d) * 6)
    dev.closePrint()

def alignType3Phase3(dev): # Type 3 (9xx)
    dev.closePrint()
    dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'pcl', 'align3_9xx.pcl.gz'))


def alignType3Phase4(dev, zca): # Type 3 (9xx)
    dev.writeEmbeddedPML(pml.OID_MARKING_AGENTS_INITIALIZED, 3)
    dev.closePrint()
    dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'pcl', 'align2_9xx.pcl.gz'))


def alignType4Phase1(dev): # Type 4 (xBow/LIDIL 0.3.8)
    dev.printData(ldl.buildLIDILPacket(ldl.PACKET_TYPE_RESUME_NORMAL_OPERATION))

    if dev.pen_config in (AGENT_CONFIG_NONE, AGENT_CONFIG_INVALID):
        return

    elif dev.pen_config == AGENT_CONFIG_BLACK_ONLY:
        ldl_file = 'cbbcal.ldl.gz'

    elif dev.pen_config == AGENT_CONFIG_COLOR_ONLY:
        ldl_file = 'cbccal.ldl.gz'

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        ldl_file = 'cb2pcal.ldl.gz'

    dev.printData(ldl.buildSetPrinterAlignmentPacket(0, 0, 0, 0))
    dev.closePrint()
    dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'ldl', ldl_file))


def alignType4Phase2(dev, a, b, c, d, e): # Type 4 (LIDIL 0.3.8)
    log.debug("A=%d, B=%d, C=%d, D=%d, E=%d" % (a, b, c, d, e))

    if dev.pen_config in (AGENT_CONFIG_NONE, AGENT_CONFIG_INVALID):
        return

    # ZCA
    zca = (7 - a) * -48
    dev.printData(ldl.buildZCAPacket(zca))

    if dev.pen_config == AGENT_CONFIG_BLACK_ONLY:
        k_bidi = (6 - b) * 2
        dev.printData(ldl.buildSetPrinterAlignmentPacket(k_bidi, 0, 0, 0))

    elif dev.pen_config == AGENT_CONFIG_COLOR_ONLY:
        cmy_bidi = (6 - b) * 2
        dev.printData(ldl.buildSetPrinterAlignmentPacket(0, 0, 0, cmy_bidi))

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        vert = (9 - b) * 2
        hort = (9 - c) * -2
        k_bidi = (6 - d) * 2
        cmy_bidi = (6 - e) * 2

        dev.printData(ldl.buildSetPrinterAlignmentPacket(k_bidi, hort, vert, cmy_bidi))

    # Set alignment
    dev.printData(ldl.buildSetPensAlignedPacket())
    dev.closePrint()


def alignType4Phase3(dev): # Type 4 (LIDIL 0.3.8)
    if dev.pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'ldl', 'cb2pcal_done.ldl.gz'))


def alignType5Phase1(dev): # Type 5 (xBow+/LIDIL 0.4.3)
    dev.printData(ldl.buildLIDILPacket(ldl.PACKET_TYPE_RESUME_NORMAL_OPERATION))

    if dev.pen_config in (AGENT_CONFIG_NONE, AGENT_CONFIG_INVALID):
        return

    elif dev.pen_config == AGENT_CONFIG_BLACK_ONLY:
        ldl_file = 'cbbcal.ldl.gz'

    elif dev.pen_config == AGENT_CONFIG_PHOTO_ONLY:
        ldl_file = 'cbpcal.ldl.gz'

    elif dev.pen_config == AGENT_CONFIG_COLOR_ONLY:
        ldl_file = 'cbccal.ldl.gz'

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        ldl_file = 'cb2pcal.ldl.gz'

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_PHOTO:
        ldl_file = 'cbcpcal.ldl.gz'

    dev.printData(ldl.buildZCAPacket(0))
    dev.printData(ldl.buildColorHortPacket(0))
    dev.printData(ldl.buildColorVertPacket(0))
    dev.printData(ldl.buildBlackVertPacket(0))
    dev.printData(ldl.buildBlackHortPacket(0))
    dev.printData(ldl.buildBlackBidiPacket(0))
    dev.printData(ldl.buildColorBidiPacket(0))
    dev.printData(ldl.buildPhotoHuePacket(0))
    dev.printData(ldl.buildColorHuePacket(0))
    dev.closePrint()

    dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'ldl', ldl_file))


def alignType5Phase2(dev, a, b, c, d, e, f, g): # Type 5 (xBow+/LIDIL 0.4.3)
    log.debug("A=%d, B=%d, C=%d, D=%d, E=%d, F=%d, G=%d" % (a, b, c, d, e, f, g))

    if dev.pen_config in (AGENT_CONFIG_NONE, AGENT_CONFIG_INVALID):
        return

    # ZCA
    zca = (7 - a) * -48
    dev.printData(ldl.buildZCAPacket(zca))

    if dev.pen_config == AGENT_CONFIG_BLACK_ONLY:
        k_bidi = (6 - b) * 2
        dev.printData(ldl.buildBlackBidiPacket(k_bidi))

    elif dev.pen_config == AGENT_CONFIG_PHOTO_ONLY:
        kcm_bidi = (6 - b) * 2
        dev.printData(ldl.buildPhotoBidiPacket(kcm_bidi))

    elif dev.pen_config == AGENT_CONFIG_COLOR_ONLY:
        cmy_bidi = (6 - b) * 2
        dev.printData(ldl.buildColorBidiPacket(cmy_bidi))

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        vert = (9 - b) * 2
        hort = (9 - c) * -2
        k_bidi = (6 - d) * 2
        cmy_bidi = (6 - e) * 2

        dev.printData(ldl.buildColorHortPacket(0))
        dev.printData(ldl.buildColorVertPacket(0))
        dev.printData(ldl.buildBlackVertPacket(vert))
        dev.printData(ldl.buildBlackHortPacket(hort))
        dev.printData(ldl.buildBlackBidiPacket(k_bidi))
        dev.printData(ldl.buildColorBidiPacket(cmy_bidi))

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_PHOTO:
        vert = (9 - b) * 2
        hort = (9 - c) * -2
        cmy_bidi = (6 - d) * 2
        kcm_bidi = (6 - e) * 2

        photo_adj = colorcal.PHOTO_ALIGN_TABLE[f][g]
        color_adj = colorcal.COLOR_ALIGN_TABLE[f][g]

        dev.printData(ldl.buildPhotoHortPacket(hort))
        dev.printData(ldl.buildPhotoVertPacket(vert))
        dev.printData(ldl.buildColorHortPacket(0))
        dev.printData(ldl.buildColorVertPacket(0))
        dev.printData(ldl.buildPhotoBidiPacket(kcm_bidi))
        dev.printData(ldl.buildColorBidiPacket(cmy_bidi))
        dev.printData(ldl.buildPhotoHuePacket(photo_adj))
        dev.printData(ldl.buildColorHuePacket(color_adj))

    # Set alignment
    dev.printData(ldl.buildSetPensAlignedPacket())
    dev.closePrint()


def alignType5Phase3(dev): # Type 5 (xBow+/LIDIL 0.4.3)
    dev.closePrint()
    if dev.pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'ldl', "cb2pcal_done.ldl.gz"))

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_PHOTO:
        dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'ldl', "cbccal_done.ldl.gz"))


def alignType6Phase1(dev): # Type 6 (xBow AiO)
    dev.printData(ldl.buildPrintInternalPagePacket())
    dev.closePrint()

def alignType7Phase1(dev): # Type 7 (xBow VIP)
    # Zero out all alignment values
    dev.writeEmbeddedPML(pml.OID_AGENT1_BIDIR_ADJUSTMENT, 0)

    dev.writeEmbeddedPML(pml.OID_AGENT2_VERTICAL_ALIGNMENT, 0)
    dev.writeEmbeddedPML(pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, 0)
    dev.writeEmbeddedPML(pml.OID_AGENT2_BIDIR_ADJUSTMENT, 0)

    dev.writeEmbeddedPML(pml.OID_AGENT3_VERTICAL_ALIGNMENT, 0)
    dev.writeEmbeddedPML(pml.OID_AGENT3_HORIZONTAL_ALIGNMENT, 0)
    dev.writeEmbeddedPML(pml.OID_AGENT3_BIDIR_ADJUSTMENT, 0)

    dev.writeEmbeddedPML(pml.OID_ZCA, 0)

    if dev.pen_config in (AGENT_CONFIG_NONE, AGENT_CONFIG_INVALID):
        return

    elif dev.pen_config == AGENT_CONFIG_BLACK_ONLY:
        pcl_file = 'crbcal.pcl.gz'

    elif dev.pen_config == AGENT_CONFIG_PHOTO_ONLY:
        pcl_file = 'crpcal.pcl.gz'

    elif dev.pen_config == AGENT_CONFIG_COLOR_ONLY:
        pcl_file = 'crccal.pcl.gz'

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        pcl_file = 'crcbcal.pcl.gz'

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_PHOTO:
        pcl_file = 'crcpcal.pcl.gz'

    dev.closePrint()
    dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'pcl', pcl_file))


def alignType7Phase2(dev, a, b, c, d, e, f, g): # Type 7 (xBow VIP)
    log.debug("A=%d, B=%d, C=%d, D=%d, E=%d, F=%d, G=%d" % (a, b, c, d, e, f, g))

    # ZCA
    zca = (7 - a) * -12
    dev.writeEmbeddedPML(pml.OID_ZCA, zca)

    if dev.pen_config == AGENT_CONFIG_BLACK_ONLY:
        k_bidi = (6 - b) * 6
        dev.writeEmbeddedPML(pml.OID_AGENT1_BIDIR_ADJUSTMENT, k_bidi)

    elif dev.pen_config == AGENT_CONFIG_PHOTO_ONLY:
        kcm_bidi = (6 - b) * 6
        dev.writeEmbeddedPML(pml.OID_AGENT3_BIDIR_ADJUSTMENT, kcm_bidi)

    elif dev.pen_config == AGENT_CONFIG_COLOR_ONLY:
        cmy_bidi = (6 - b) * 6
        dev.writeEmbeddedPML(pml.OID_AGENT2_BIDIR_ADJUSTMENT, cmy_bidi)

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_BLACK:
        vert = (9 - b) * 6
        hort = (9 - c) * -6
        k_bidi = (6 - d) * 6
        cmy_bidi = (6 - e) * 6

        dev.writeEmbeddedPML(pml.OID_AGENT1_BIDIR_ADJUSTMENT, k_bidi)
        dev.writeEmbeddedPML(pml.OID_AGENT2_BIDIR_ADJUSTMENT, cmy_bidi)
        dev.writeEmbeddedPML(pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, hort)
        dev.writeEmbeddedPML(pml.OID_AGENT2_VERTICAL_ALIGNMENT, vert)

    elif dev.pen_config == AGENT_CONFIG_COLOR_AND_PHOTO:
        vert = (9 - b) * 6
        hort = (9 - c) * -6
        cmy_bidi = (6 - d) * 6
        kcm_bidi = (6 - e) * 6

        photo_adj = colorcal.PHOTO_ALIGN_TABLE[f][g]
        color_adj = colorcal.COLOR_ALIGN_TABLE[f][g]

        x = (color_adj << 8) + photo_adj

        dev.writeEmbeddedPML(pml.OID_COLOR_CALIBRATION_SELECTION, x)

        dev.writeEmbeddedPML(pml.OID_AGENT2_BIDIR_ADJUSTMENT, cmy_bidi)
        dev.writeEmbeddedPML(pml.OID_AGENT3_BIDIR_ADJUSTMENT, kcm_bidi)
        dev.writeEmbeddedPML(pml.OID_AGENT3_HORIZONTAL_ALIGNMENT, hort)
        dev.writeEmbeddedPML(pml.OID_AGENT3_VERTICAL_ALIGNMENT, vert)

    dev.closePrint()

def alignType7Phase3(dev): # Type 7 (xBow VIP)
    dev.closePrint()
    dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'pcl', "crcaldone.pcl.gz"))


def alignType8Phase1(dev): # 450
    pens = dev.getStatusFromDeviceID()['agents']
    pen_types = [pens[x]['type'] for x in range(len(pens))]

    if AGENT_TYPE_KCM in pen_types:
        f, num_inks = 'align6_450.pcl.gz', 6
    else:
        f, num_inks = 'align4_450.pcl.gz', 4

    dev.closePrint()
    dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'pcl', f))

    return num_inks


def alignType8Phase2(dev, num_inks, a, b, c, d): # 450
    align_values1 = {1 : '\x00\x00\x18',
                      2 : '\x00\x00\x12',
                      3 : '\x00\x00\x0c',
                      4 : '\x00\x00\x06',
                      5 : '\x00\x00\x00',
                      6 : '\x01\x00\x06',
                      7 : '\x01\x00\x0c',
                      8 : '\x01\x00\x12',
                      9 : '\x01\x00\x18',
                    }

    align_values2 = {1 : '\x00\x00\x12',
                      2 : '\x00\x00\x0c',
                      3 : '\x00\x00\x06',
                      4 : '\x00\x00\x00',
                      5 : '\x01\x00\x06',
                      6 : '\x01\x00\x0c',
                      7 : '\x01\x00\x12',
                      8 : '\x01\x00\x18',
                      9 : '\x01\x00\x1e',
                    }

    align_values3 = {1 : '\x00\x00\x24',
                      2 : '\x00\x00\x18',
                      3 : '\x00\x00\x12',
                      4 : '\x00\x00\x06',
                      5 : '\x00\x00\x00',
                      6 : '\x01\x00\x06',
                      7 : '\x01\x00\x12',
                      8 : '\x01\x00\x18',
                      9 : '\x01\x00\x24',
                    }

    if num_inks == 4:
        s = ''.join([pcl.UEL,
              '@PJL ENTER LANGUAGE=PCL3GUI\n',
              pcl.RESET,
              pcl.ESC, '*o5W\x1a\x01', align_values1[a],
              pcl.ESC, '*o5W\x1a\x02', align_values2[a],
              pcl.ESC, '*o5W\x1a\x03', align_values1[b],
              pcl.ESC, '*o5W\x1a\x04', align_values1[b],
              pcl.ESC, '*o5W\x1a\x08', align_values1[c],
              pcl.ESC, '*o5W\x1a\x07', align_values1[d],
              pcl.RESET,
              pcl.UEL])

    else: # 6
        s = ''.join([pcl.UEL,
              '@PJL ENTER LANGUAGE=PCL3GUI\n',
              pcl.RESET,
              pcl.ESC, '*o5W\x1a\x05', align_values1[a],
              pcl.ESC, '*o5W\x1a\x06', align_values3[a],
              pcl.ESC, '*o5W\x1a\x03', align_values1[b],
              pcl.ESC, '*o5W\x1a\x04', align_values1[b],
              pcl.ESC, '*o5W\x1a\x0a', align_values1[c],
              pcl.ESC, '*o5W\x1a\x09', align_values1[d],
              pcl.RESET,
              pcl.UEL])

    dev.printData(s)
    dev.closePrint()


def AlignType12(dev, loadpaper_ui):
    if loadpaper_ui():
        dev.setPML(pml.OID_PRINT_INTERNAL_PAGE, pml.PRINT_INTERNAL_PAGE_ALIGNMENT_PAGE)
        dev.closePML()

# ********************** Clean **********************
def cleanVerifyPage(dev):
    # By default Clean verification page is Enabled
    return True

def cleaning(dev, clean_type, level1, level2, level3,
              loadpaper_ui, dlg1, dlg2, dlg3, wait_ui, verify_page = cleanVerifyPage):

    state = 0
    level = 0
    print_verify_page = verify_page(dev)
    while state != -1:
        if state == 0: # Initial level1 print
            state = 1
            if clean_type == CLEAN_TYPE_PCL_WITH_PRINTOUT:
                ok = loadpaper_ui()
                if not ok:
                    state = -1
            elif clean_type == CLEAN_TYPE_LEDM and print_verify_page == False:
                ok = loadpaper_ui("Clean functinality conformation...", "Clean Conformation")
                if not ok:
                    state = -1

        elif state == 1: # Do level 1
            level1(dev)
            if clean_type == CLEAN_TYPE_LEDM and print_verify_page == False :
                state = 3
            else:
                state = 2

        elif state == 2: # Load plain paper
            state = -1
            ok = loadpaper_ui()
            if ok:
                state = 3

        elif state == 3: # Print test page
            state = 4
            if clean_type == CLEAN_TYPE_LEDM:
                cleanTypeVerify(dev,1, print_verify_page)
            else:
                print_clean_test_page(dev)

        elif state == 4: # Need level 2?
            state = -1
            if print_verify_page == False :
                ok = dlg1("Clean Level 1 is Completed.")
            else:
                ok = dlg1()

            if ok:
                state = 5

        elif state == 5: # Do level 2
            level2(dev)
            if clean_type == CLEAN_TYPE_LEDM and print_verify_page == False :
                state = 7
            else:
                state = 6

        elif state == 6: # Load plain paper
            state = -1
            ok = loadpaper_ui()
            if ok:
                state = 7

        elif state == 7: # Print test page
            state = 8
            if clean_type == CLEAN_TYPE_LEDM:
                cleanTypeVerify(dev,2,print_verify_page)
            else:
                print_clean_test_page(dev)

        elif state == 8: # Need level 3?
            state = -1
            if print_verify_page == False :
                ok = dlg2("Clean Level 2 is Completed.")
            else:
                ok = dlg2()

            if ok:
                state = 9

        elif state == 9: # Do level 3
            level3(dev)
            state = 10
            if clean_type == CLEAN_TYPE_LEDM and print_verify_page == False :
                state = 11
            else:
                state = 10

        elif state == 10: # Load plain paper
            state = -1
            ok = loadpaper_ui()
            if ok:
                state = 11

        elif state == 11: # Print test page
            state = 12
            if clean_type == CLEAN_TYPE_LEDM:
                cleanTypeVerify(dev,3,print_verify_page)
            else:
                print_clean_test_page(dev)

        elif state == 12:
            state = -1
            if print_verify_page == False :
                dlg3("Level 3 cleaning complete. Check this page to see if the problem was fixed. replace the print cartridge(s)")
            else:
                dlg3()

    return ok


def print_clean_test_page(dev):
    dev.closePrint()
    dev.printGzipFile(os.path.join(prop.home_dir, 'data',
                      'ps', 'clean_page.pdf.gz'), raw=False)

def cleanType1(dev): # PCL, Level 1
    dev.writeEmbeddedPML(pml.OID_CLEAN, pml.CLEAN_CLEAN)
    dev.closePrint()

def primeType1(dev): # PCL, Level 2
    dev.writeEmbeddedPML(pml.OID_CLEAN, pml.CLEAN_PRIME)
    dev.closePrint()

def wipeAndSpitType1(dev): # PCL, Level 3
    dev.writeEmbeddedPML(pml.OID_CLEAN, pml.CLEAN_WIPE_AND_SPIT)
    dev.closePrint()

def cleanType2(dev): # LIDIL, Level 1
    dev.printData(ldl.buildResetPacket())
    dev.printData(ldl.buildLIDILPacket(ldl.PACKET_TYPE_COMMAND,
                                       ldl.COMMAND_HANDLE_PEN,
                                       ldl.COMMAND_HANDLE_PEN_CLEAN_LEVEL1))
    dev.closePrint()

def primeType2(dev): # LIDIL, Level 2
    dev.printData(ldl.buildResetPacket())
    dev.printData(ldl.buildLIDILPacket(ldl.PACKET_TYPE_COMMAND,
                                       ldl.COMMAND_HANDLE_PEN,
                                       ldl.COMMAND_HANDLE_PEN_CLEAN_LEVEL2))
    dev.closePrint()

def wipeAndSpitType2(dev): # LIDIL, Level 3
    dev.printData(ldl.buildResetPacket())
    dev.printData(ldl.buildLIDILPacket(ldl.PACKET_TYPE_COMMAND,
                                       ldl.COMMAND_HANDLE_PEN,
                                       ldl.COMMAND_HANDLE_PEN_CLEAN_LEVEL3))
    dev.closePrint()

def setCleanType(name):
    try:
      xml = CleanXML %(name)
    except(UnicodeEncodeError, UnicodeDecodeError):
      log.error("Unicode Error")
    return xml


def getCleanLedmCapacity(dev):
    data_fp = StringIO()
    status_type = dev.mq.get('status-type', STATUS_TYPE_NONE)

    if status_type == STATUS_TYPE_LEDM:
       func = dev.getEWSUrl_LEDM
    elif status_type == STATUS_TYPE_LEDM_FF_CC_0:
       func = dev.getUrl_LEDM
    else:
        log.error("Not an LEDM status-type: %d" % status_type)
        return ""

    data = func(LEDM_CLEAN_CAP_XML, data_fp)
    if data:
        data = data.split(b'\r\n\r\n', 1)[1]
        if data:
            data = status.ExtractXMLData(data)
    return data


def isCleanTypeLedmWithPrint(dev):
    IPCap_data = getCleanLedmCapacity(dev)

    if LEDM_CLEAN_VERIFY_PAGE_JOB in IPCap_data:
        return True
    else:
        return False


def cleanTypeLedm(dev): #LEDM, level 1
    xml = setCleanType('cleaningPage')
    dev.post(status_xml, xml)
    dev.closePrint()

def cleanTypeLedm1(dev): #LEDM, level 2
    xml = setCleanType('cleaningPageLevel1')
    dev.post(status_xml, xml)
    dev.closePrint()

def cleanTypeLedm2(dev): #LEDM, level 3
    xml = setCleanType('cleaningPageLevel2')
    dev.post(status_xml, xml)
    dev.closePrint()

def cleanTypeVerify(dev,level, print_verification_page = True): #LEDM Test Page
    state = 0
    timeout = 0
    status_type = dev.mq.get('status-type', STATUS_TYPE_NONE)
    xml = setCleanType('cleaningVerificationPage')

    if status_type == STATUS_TYPE_LEDM:
       func = dev.getEWSUrl_LEDM

    elif status_type == STATUS_TYPE_LEDM_FF_CC_0:
       func = dev.getUrl_LEDM

    else:
        log.error("Not an LEDM status-type: %d" % status_type)

    print("Performing level %d cleaning...." % level)

    while state != -1:
       status_block = status.StatusType10Status(func)

       if status_block['status-code'] == STATUS_PRINTER_IDLE: # Printer Ready
             state = -1
             if print_verification_page:
                 dev.post(status_xml, xml)
       else:
             time.sleep(8)
             timeout += 1

       if timeout > 20:
             log.error("Timeout waiting for Clean to finish.")
             sys.exit(0)



# ********************** Color Cal **********************


def colorCalType1(dev, loadpaper_ui, colorcal_ui, photopenreq_ui): # 450
    value, state = 4, 0
    ok = False
    while state != -1:

        if state == 0:
            if colorCalType1PenCheck(dev):
                state = 1
            else:
                state = 100

        elif state == 1:
            state = -1
            ok = loadpaper_ui()
            if ok:
                colorCalType1Phase1(dev)
                state = 2

        elif state == 2:
            state = -1
            ok, value = colorcal_ui()
            if ok:
                state = 3

        elif state == 3:
            colorCalType1Phase2(dev, value)
            state = -1

        elif state == 100:
            ok = False
            photopenreq_ui()
            state = -1

    return ok


def colorCalType1PenCheck(dev): # 450
    pens = dev.getStatusFromDeviceID()['agents']
    pen_types = [pens[x]['type'] for x in range(len(pens))]

    if AGENT_TYPE_KCM in pen_types:
        return True

    else:
        log.error("Cannot perform color calibration with no photo pen installed.")
        return False


def colorCalType1Phase1(dev): # 450
    dev.closePrint()
    dev.printGzipFile(os.path.join(prop.home_dir, 'data', 'pcl', 'colorcal1_450.pcl.gz'))


def colorCalType1Phase2(dev, value): # 450
    color_cal = {1 : ('\x0f\x3c', '\x17\x0c'),
                  2 : ('\x10\xcc', '\x15\x7c'),
                  3 : ('\x12\x5c', '\x13\xec'),
                  4 : ('\x13\xec', '\x12\x5c'),
                  5 : ('\x15\x7c', '\x10\xcc'),
                  6 : ('\x17\x0c', '\x0f\x3c'),
                  7 : ('\x18\x9c', '\x0d\xac'),
                }

    s = ''.join([pcl.UEL,
                  '@PJL ENTER LANGUAGE=PCL3GUI\n',
                  pcl.RESET,
                  pcl.ESC, '*o5W\x1a\x0c\x00', color_cal[value][0],
                  pcl.ESC, '*o5W\x1a\x0b\x00', color_cal[value][1],
                  pcl.RESET,
                  pcl.UEL])

    dev.printData(s)
    dev.closePrint()

#
# COLOR CAL TYPE 2
#

def colorCalType2(dev, loadpaper_ui, colorcal_ui, photopenreq_ui):
    value, state = 4, 0
    ok = True
    while state != -1:

        if state == 0:
            if colorCalType2PenCheck(dev):
                state = 1
            else:
                state = 100

        elif state == 1:
            state = -1
            ok = loadpaper_ui()
            if ok:
                colorCalType2Phase1(dev)
                state = 2

        elif state == 2:
            state = -1
            ok, value = colorcal_ui()
            if ok:
                state = 3

        elif state == 3:
            colorCalType2Phase2(dev, value)
            state = -1

        elif state == 100:
            photopenreq_ui()
            ok = False
            state = -1

    return ok

def colorCalType2PenCheck(dev):
    pens = dev.getStatusFromDeviceID()['agents']
    pen_types = [pens[x]['type'] for x in range(len(pens))]

    if not AGENT_TYPE_NONE in pen_types:
        return True

    else:
        log.error("Cannot perform color calibration with pens missing.")
        return False

def colorCalType2Phase1(dev):
    dev.writeEmbeddedPML(pml.OID_PRINT_INTERNAL_PAGE,
                         pml.PRINT_INTERNAL_PAGE_COLOR_CAL)

    dev.closePrint()


def colorCalType2Phase2(dev, value):
    c = colorcal.COLOR_CAL_TABLE
    p = ''.join(['\x1b&b19WPML \x04\x00\x06\x01\x04\x01\x05\x01\t\x08\x04',
                   chr(c[value*4]+100), chr(c[value*4+1]+100),
                   chr(c[value*4+2]+100), chr(c[value*4+3]+100),
                   '\x1b%-12345X'])

    dev.printData(p)
    dev.closePrint()


#
# COLOR CAL TYPE 3
#

def colorCalType3(dev, loadpaper_ui, colorcal_ui, photopenreq_ui):
    value, state = 4, 0
    ok = True
    while state != -1:

        if state == 0:
            if colorCalType3PenCheck(dev):
                state = 1
            else:
                state = 100

        elif state == 1:
            state = -1
            ok = loadpaper_ui()
            if ok:
                colorCalType3Phase1(dev)
                state = 2

        elif state == 2:
            state = -1
            ok, valueA = colorcal_ui('A', 21)
            if ok:
                state = 3

        elif state == 3:
            state = -1
            ok, valueB = colorcal_ui('B', 21)
            if ok:
                state = 4

        elif state == 4:
            colorCalType3Phase2(dev, valueA, valueB)
            state = -1

        elif state == 100:
            photopenreq_ui()
            ok = False
            state = -1

    return ok

def colorCalType3PenCheck(dev):
    pens = dev.getStatusFromDeviceID()['agents']
    pen_types = [pens[x]['type'] for x in range(len(pens))]

    if AGENT_TYPE_KCM in pen_types or \
      AGENT_TYPE_BLUE in pen_types:
        return True

    else:
        log.error("Cannot perform color calibration with no photo (or photo blue) pen installed.")
        return False


def colorCalType3Phase1(dev):
    dev.writeEmbeddedPML(pml.OID_PRINT_INTERNAL_PAGE,
                         pml.PRINT_INTERNAL_PAGE_COLOR_CAL)
    dev.closePrint()

def colorCalType3Phase2(dev, A, B):
    photo_adj = colorcal.PHOTO_ALIGN_TABLE[A-1][B-1]
    color_adj = colorcal.COLOR_ALIGN_TABLE[A-1][B-1]
    adj_value = (color_adj << 8) + photo_adj

    dev.writeEmbeddedPML(pml.OID_COLOR_CALIBRATION_SELECTION, adj_value)
    dev.closePrint()

def colorCalType4(dev, loadpaper_ui, colorcal_ui, wait_ui):
    state = 0
    ok = True

    while state != -1:
        if state == 0:
            state = -1
            ok = loadpaper_ui()
            if ok:
                colorCalType4Phase1(dev)
                state = 2

        elif state == 2:
            state = -1
            #wait_ui(90)
            ok, values = colorcal_ui()
            if ok:
                state = 3

        elif state == 3:
            colorCalType4Phase2(dev, values)
            #wait_ui(5)
            state = 4

        elif state == 4:
            state = -1
            ok = loadpaper_ui()
            if ok:
                colorCalType4Phase3(dev)
                state = -1

    return ok


def colorCalType4Phase1(dev):
    dev.setPML(pml.OID_PRINT_INTERNAL_PAGE,
              pml.PRINT_INTERNAL_PAGE_COLOR_CAL)

    dev.closePML()


def colorCalType4AdjValue(value):
    if value >= 100:
        return 200
    return value+100


def colorCalType4Phase2(dev, values):
    if -1 in values:
        Cadj, Madj, Yadj, cadj, madj, kadj = 244, 244, 244, 244, 244, 244
    else:
        sel1, sel2, sel3, sel4 = values
        tmp1 = colorcal.TYPE_4_C_TABLE[sel1][sel2]
        tmp2 = colorcal.TYPE_4_LC_TABLE[sel3][sel4]

        Cadj = colorCalType4AdjValue(tmp1)
        cadj = colorCalType4AdjValue(tmp1+tmp2)

        tmp1 = colorcal.TYPE_4_M_TABLE[sel1][sel2]
        tmp2 = colorcal.TYPE_4_LM_TABLE[sel3][sel4]

        Madj = colorCalType4AdjValue(tmp1)
        madj = colorCalType4AdjValue(tmp1+tmp2)

        Yadj = colorCalType4AdjValue(colorcal.TYPE_4_Y_TABLE[sel1][sel2])
        kadj = colorCalType4AdjValue(0)

    log.debug("C=%d, M=%d, Y=%d, c=%d, m=%d, k=%d\n" % (Cadj, Madj, Yadj, cadj, madj, kadj))

    dev.setPML(pml.OID_COLOR_CALIBRATION_ARRAY_1,
                            kadj)

    dev.setPML(pml.OID_COLOR_CALIBRATION_ARRAY_2,
                            Cadj)

    dev.setPML(pml.OID_COLOR_CALIBRATION_ARRAY_3,
                            Madj)

    dev.setPML(pml.OID_COLOR_CALIBRATION_ARRAY_4,
                            Yadj)

    dev.setPML(pml.OID_COLOR_CALIBRATION_ARRAY_5,
                            cadj)

    dev.setPML(pml.OID_COLOR_CALIBRATION_ARRAY_6,
                            madj)

    dev.closePML()


def colorCalType4Phase3(dev):
    dev.setPML(pml.OID_PRINT_INTERNAL_PAGE,
                         pml.PRINT_INTERNAL_PAGE_COLOR_PALETTE_CMYK_PAGE)

    dev.closePML()


def colorCalType5(dev, loadpaper_ui):
    if loadpaper_ui():
        dev.printData("""\x1b%-12345X@PJL ENTER LANGUAGE=PCL3GUI\n\x1bE\x1b%Puifp.multi_button_push 20;\nudw.quit;\x1b*rC\x1bE\x1b%-12345X""")
        dev.closePrint()


def colorCalType6(dev, loadpaper_ui):
    if loadpaper_ui():
        dev.setPML(pml.OID_PRINT_INTERNAL_PAGE, pml.PRINT_INTERNAL_PAGE_COLOR_CAL)
        dev.closePML()

def colorCalType7(dev, loadpaper_ui):
    if loadpaper_ui():
        dev.setPML(pml.OID_PRINT_INTERNAL_PAGE, pml.PRINT_INTERNAL_PAGE_AUTOMATIC_COLOR_CALIBRATION)
        dev.closePML()

# ********************** LF Cal **********************

def linefeedCalType1(dev, loadpaper_ui):
    if loadpaper_ui():
        dev.printData("""\x1b%-12345X@PJL ENTER LANGUAGE=PCL3GUI\n\x1bE\x1b%Puifp.multi_button_push 3;\nudw.quit;\x1b*rC\x1bE\x1b%-12345X""")
        dev.closePrint()

def linefeedCalType2(dev, loadpaper_ui):
    if loadpaper_ui():
        dev.setPML(pml.OID_PRINT_INTERNAL_PAGE, pml.PRINT_INTERNAL_PAGE_LINEFEED_CALIBRATION)
        dev.closePML()


# ********************** PQ Diag **********************

def printQualityDiagType1(dev, loadpaper_ui):
    if loadpaper_ui():
        dev.printData("""\x1b%-12345X@PJL ENTER LANGUAGE=PCL3GUI\n\x1bE\x1b%Puifp.multi_button_push 14;\nudw.quit;\x1b*rC\x1bE\x1b%-12345X""")
        dev.closePrint()

def printQualityDiagType2(dev, loadpaper_ui):
    if loadpaper_ui():
        dev.setPML(pml.OID_PRINT_INTERNAL_PAGE, pml.PRINT_INTERNAL_PAGE_PRINT_QUALITY_DIAGNOSTIC)
        dev.closePML()
