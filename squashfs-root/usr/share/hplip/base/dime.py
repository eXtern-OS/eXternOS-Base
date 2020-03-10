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

# Local
from .g import *

# DIME constants
TYPE_T_MIME = 0x01
TYPE_T_URI = 0x02
DIME_VERSION = 1
PAD_SIZE = 4


class Record(object):
    def __init__(self, id, typ, typ_code, payload):
        self.id = id
        self.typ = typ
        self.typ_code = typ_code
        self.payload = payload
        

class Message(object):
    def __init__(self):
        self.records = []

    def add_record(self, rec):
        self.records.append(rec)
        
    def generate(self, output): # output is a stream type
        for i, r in enumerate(self.records):
            log.debug("Processing record %d (%s)" % (i, r.id))
            mb = me = cf = 0
            if i == 0: mb = 1
            if i == len(self.records)-1: me = 1
                
            output.write(struct.pack("!B", ((DIME_VERSION & 0x1f) << 3 |
                                            (mb & 0x01) << 2 |
                                            (me & 0x01) << 1 |
                                            (cf & 0x01))))
                   
            output.write(struct.pack("!B", ((r.typ_code & 0xf) << 4) & 0xf0))
    
            output.write(struct.pack("!H", 0)) # Options length
            
            id_len = self.bytes_needed(len(r.id))
            output.write(struct.pack("!H", len(r.id))) # ID length
            
            typ_len = self.bytes_needed(len(r.typ))
            output.write(struct.pack("!H", len(r.typ))) # Type length
            
            data_len = self.bytes_needed(len(r.payload))
            output.write(struct.pack("!I", len(r.payload))) # Data length
            
            if id_len:
                output.write(struct.pack("%ds" % id_len, r.id))
                
            if typ_len:
                output.write(struct.pack("%ds" % typ_len, r.typ))
            
            if data_len:
                output.write(struct.pack("%ds" % data_len, r.payload))
        
    
    def bytes_needed(self, data_len, block_size=PAD_SIZE):
        if data_len % block_size == 0:
            return data_len
        else:
            return (int(data_len/block_size+1))*block_size
            
            


if __name__ == "__main__":
    log.set_level("debug")
    import io
    m = Message()
    m.add_record(Record("cid:id0", "http://schemas.xmlsoap.org/soap/envelope/", 
                        TYPE_T_URI, "<test>test</test>"))
    
    m.add_record(Record("test2", "text/xml", TYPE_T_MIME, "<test>test2</test>"))
    
    output = io.StringIO()
    
    m.generate(output)
    
    log.log_data(output.getvalue())



