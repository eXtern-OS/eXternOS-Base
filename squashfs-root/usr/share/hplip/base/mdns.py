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

# RFC 1035

# Std Lib
import sys
import time
import socket
import select
import struct
import random
import re

# Local
from .g import *
from . import utils
from .sixext import BytesIO, to_bytes_utf8, to_bytes_latin, to_string_latin

MAX_ANSWERS_PER_PACKET = 24

QTYPE_A = 1
QTYPE_TXT = 16
QTYPE_SRV = 33
QTYPE_AAAA = 28
QTYPE_PTR = 12

QCLASS_IN = 1

# Caller needs to ensure, data should be in string format.
def read_utf8(offset, data, l):
    return offset+l, data[offset:offset+l]

def read_data(offset, data, l):
    return offset+l, data[offset:offset+l]

def read_data_unpack(offset, data, fmt):
    l = struct.calcsize(fmt)
    return offset+l, struct.unpack(fmt, to_bytes_latin(data[offset:offset+l]))

def read_name(offset, data):
    result = ''
    off = offset
    next = -1
    first = off

    while True:
        l = ord(data[off:off+1])
        off += 1

        if l == 0:
            break

        t = l & 0xC0

        if t == 0x00:
            off, utf8 = read_utf8(off, data, l)
            result = ''.join([result, utf8, '.'])

        elif t == 0xC0:
            if next < 0:
                next = off + 1

            off = ((l & 0x3F) << 8) | ord(data[off:off+1])

            if off >= first:
                log.error("Bad domain name (circular) at 0x%04x" % off)
                break

            first = off

        else:
            log.error("Bad domain name at 0x%04x" % off)
            break

    if next >= 0:
        offset = next

    else:
        offset = off

    return offset, result


def write_name(packet, name):
    for p in name.split('.'):
        utf8_string = p.encode('utf-8')
        packet.write(struct.pack('!B', len(utf8_string)))
        packet.write(utf8_string)


def create_outgoing_packets(answers):
    index = 0
    num_questions = 1
    first_packet = True
    packets = []
    packet = BytesIO()
    answer_record = BytesIO()

    while True:
        packet.seek(0)
        packet.truncate()

        num_answers = len(answers[index:index+MAX_ANSWERS_PER_PACKET])

        if num_answers == 0 and num_questions == 0:
            break

        flags = 0x0200 # truncated
        if len(answers) - index <= MAX_ANSWERS_PER_PACKET:
            flags = 0x0000 # not truncated

        # ID/FLAGS/QDCOUNT/ANCOUNT/NSCOUNT/ARCOUNT
        packet.write(struct.pack("!HHHHHH", 0x0000, flags, num_questions, num_answers, 0x0000, 0x0000))

        if num_questions:
            # QNAME
            write_name(packet, "_pdl-datastream._tcp.local") # QNAME
            packet.write(struct.pack("!B", 0x00))

            # QTYPE/QCLASS
            packet.write(struct.pack("!HH", QTYPE_PTR, QCLASS_IN))

        first_record = True
        for d in answers[index:index+MAX_ANSWERS_PER_PACKET]:
            answer_record.seek(0)
            answer_record.truncate()

            # NAME
            if not first_packet and first_record:
                first_record = False
                write_name(answer_record, "_pdl-datastream._tcp.local")
                answer_record.write(struct.pack("!B", 0x00))
            else:
                answer_record.write(struct.pack("!H", 0xc00c)) # Pointer

            # TYPE/CLASS
            answer_record.write(struct.pack("!HH", QTYPE_PTR, QCLASS_IN))

            # TTL
            answer_record.write(struct.pack("!I", 0xffff))
            rdlength_pos = answer_record.tell()

            # RDLENGTH
            answer_record.write(struct.pack("!H", 0x0000)) # (adj later)

            # RDATA
            write_name(answer_record, d)
            answer_record.write(struct.pack("!H", 0xc00c)) # Ptr

            # RDLENGTH
            rdlength = answer_record.tell() - rdlength_pos - 2
            answer_record.seek(rdlength_pos)
            answer_record.write(struct.pack("!H", rdlength))

            answer_record.seek(0)
            packet.write(answer_record.read())

        packets.append(packet.getvalue())

        index += 20

        if first_packet:
            num_questions = 0
            first_packet = False

    return packets

def createSocketsWithsetOption(ttl=4):
    s=None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        x = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        x.connect(('1.2.3.4', 56))
        intf = x.getsockname()[0]
        x.close()

        s.setblocking(0)
        ttl = struct.pack('B', ttl)
    except socket.error:
        log.error("Network error")
        if s:
            s.close()
        return None

    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except (AttributeError, socket.error):
        pass

    try:
        s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, ttl)
        s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(intf) + socket.inet_aton('0.0.0.0'))
        s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP ,1)
    except Exception as e:
        log.error("Unable to setup multicast socket for mDNS: %s" % e)
        if s:
            s.close()
        return None
    return s

def updateReceivedData(data, answers):
    update_spinner()
    y = {'num_devices' : 1, 'num_ports': 1, 'product_id' : '', 'mac': '',
         'status_code': 0, 'device2': '0', 'device3': '0', 'note': ''}

    log.debug("Incoming: (%d)" % len(data))
    log.log_data(data, width=16)

    offset = 0
    offset, (id, flags, num_questions, num_answers, num_authorities, num_additionals) = \
        read_data_unpack(offset, data, "!HHHHHH")

    log.debug("Response: ID=%d FLAGS=0x%x Q=%d A=%d AUTH=%d ADD=%d" %
        (id, flags, num_questions, num_answers, num_authorities, num_additionals))

    for question in range(num_questions):
        update_spinner()
        offset, name = read_name(offset, data)
        offset, (typ, cls) = read_data_unpack(offset, data, "!HH")
        log.debug("Q: %s TYPE=%d CLASS=%d" % (name, typ, cls))

    fmt = '!HHiH'
    for record in range(num_answers + num_authorities + num_additionals):
        update_spinner()
        offset, name = read_name(offset, data)
        offset, info = read_data_unpack(offset, data, "!HHiH")

        if info[0] == QTYPE_A: # ipv4 address
            offset, result = read_data(offset, data, 4)
            ip = '.'.join([str(ord(x)) for x in result])
            log.debug("A: %s" % ip)
            y['ip'] = ip

        elif info[0] == QTYPE_PTR: # PTR
            offset, name = read_name(offset, data)
            log.debug("PTR: %s" % name)
            y['mdns'] = name
            answers.append(name.replace("._pdl-datastream._tcp.local.", ""))

        elif info[0] == QTYPE_TXT:
            offset, name = read_data(offset, data, info[3])
            txt, off = {}, 0

            while off < len(name):
                l = ord(name[off:off+1])
                off += 1
                result = name[off:off+l]

                try:
                    key, value = result.split('=')
                    txt[key] = value
                except ValueError:
                    pass

                off += l

            log.debug("TXT: %s" % repr(txt))
            try:
                y['device1'] = "MFG:Hewlett-Packard;MDL:%s;CLS:PRINTER;" % txt['ty']
            except KeyError:
                log.debug("NO ty Key in txt: %s" % repr(txt))

            if 'note' in txt:
                y['note'] = txt['note']

        elif info[0] == QTYPE_SRV:
            offset, (priority, weight, port) = read_data_unpack(offset, data, "!HHH")
            #ttl = info[3]
            offset, server = read_name(offset, data)
            #log.debug("SRV: %s TTL=%d PRI=%d WT=%d PORT=%d" % (server, ttl, priority, weight, port))
            y['hn'] = server.replace('.local.', '')

        elif info[0] == QTYPE_AAAA: # ipv6 address
            offset, result = read_data(offset, data, 16)
            log.debug("AAAA: %s" % repr(result))

        else:
            log.error("Unknown DNS record type (%d)." % info[0])
            break
    return y, answers


def detectNetworkDevices(ttl=4, timeout=10):
    mcast_addr, mcast_port ='224.0.0.251', 5353
    found_devices = {}
    answers = []

    s = createSocketsWithsetOption(ttl)
    if not s:
        return {}

    now = time.time()
    next = now
    last = now + timeout
    delay = 1

    while True:
        now = time.time()

        if now > last:
            break

        if now >= next:
            try:
                for p in create_outgoing_packets(answers):
                    log.debug("Outgoing: (%d)" % len(p))
                    log.log_data(p, width=16)
                    s.sendto(p, 0, (mcast_addr, mcast_port))

            except socket.error as e:
                log.error("Unable to send broadcast DNS packet: %s" % e)

            next += delay
            delay *= 2

        update_spinner()

        r, w, e = select.select([s], [], [s], 0.5)

        if not r:
            continue

        data, addr = s.recvfrom(16384)
        data = to_string_latin(data)
        if data:
            y, answers = updateReceivedData(data, answers)
            found_devices[y['ip']] = y

    log.debug("Found %d devices" % len(found_devices))
    s.close()
    return found_devices


