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

# Std Lib
import struct
import time
import fnmatch
import mimetypes
import array

# Local
from base.g import *
from base.codes import *
from base import device, utils, exif

try:
    import pcardext
except ImportError:
    if not os.getenv("HPLIP_BUILD"):
        log.error("PCARDEXT could not be loaded. Please check HPLIP installation.")
        sys.exit(1)

# Photocard command codes
ACK = 0x0100
NAK = 0x0101
READ_CMD = 0x0010
WRITE_CMD = 0x0020

SECTOR_SIZE = 512 # don't change this (TODO: impl. in pcardext)

# Photocard sector cache
MAX_CACHE = 512 # units = no. sectors 

# PhotoCardFile byte cache
# Used for thumbnails
INITIAL_PCARDFILE_BUFFER = 20*SECTOR_SIZE 
INCREMENTAL_PCARDFILE_BUFFER = 2*SECTOR_SIZE 

class PhotoCardFile:    
    # File-like interface

    def __init__(self, pc, name=None):
        self.pos = 0
        self.closed = True
        self.file_size = 0
        self.pc = pc
        self.buffer = array.array('c') 

        if name is not None:
            self.open(name)

        self.buffer_size = INITIAL_PCARDFILE_BUFFER
        self.buffer.fromstring(pcardext.read(self.name, 0, self.buffer_size))


    def open(self, name):
        self.closed = False
        self.name = name

    def seek(self, offset, whence=0):
        if whence == 0:
            self.pos = offset
        elif whence == 1:
            self.pos += offset
        elif whence == 2:
            self.pos = self.file_size - offset
        else:
            return


    def tell(self):
        return self.pos


    def read(self, size): 
        if size > 0:
            if self.pos + size < self.buffer_size:
                data = self.buffer[self.pos : self.pos + size].tostring()
                self.pos += size
                return data
            else:
                # Read some more in from the card to satisfy the request
                while self.pos + size >= self.buffer_size:
                    self.buffer.fromstring(pcardext.read(self.name, self.buffer_size, INCREMENTAL_PCARDFILE_BUFFER))
                    self.buffer_size += INCREMENTAL_PCARDFILE_BUFFER
                return self.read(size)


    def close(self):
        self.closed = True
        self.pos = 0


class PhotoCard:

    def __init__(self, dev_obj=None, device_uri=None, printer_name=None):

        if dev_obj is None:
            self.device = device.Device(device_uri, printer_name)
            self.device.open()
            self.close_device = True
        else:
            self.device = dev_obj
            self.close_device = False

        self.dir_stack = utils.Stack()
        self.current_dir = []
        self.device_uri = self.device.device_uri
        self.pcard_mounted = False
        self.saved_pwd = []
        self.sector_buffer = {}
        self.sector_buffer_counts = {}
        self.cache_flag = True
        self.write_protect = False

        self.callback = None

        self.channel_opened = False


    def START_OPERATION(self, name=''):
        pass

    def END_OPERATION(self, name='', flag=True):
        if self.channel_opened and flag:
            self.close_channel()

    def set_callback(self, callback):
        self.callback = callback

    def _read(self, sector, nsector): 
        log.debug("read pcard sector: sector=%d count=%d" % (sector, nsector))

        if self.cache_flag:
            for s in range(sector, sector+nsector):
                if s not in self.sector_buffer:
                    break
            else:
                buffer = ''
                for s in range(sector, sector+nsector):
                    buffer = ''.join([buffer, self.sector_buffer[s]])
                    log.debug("Cached sector read sector=%d" % s)
                    count = self.sector_buffer_counts[s]
                    self.sector_buffer_counts[s] = count+1

                    if self.callback is not None:
                        self.callback()

                #log.log_data(buffer)
                return buffer

        if self.callback is not None:
            self.callback()

        if not self.channel_opened:
            self.open_channel()

        log.debug("Normal sector read sector=%d count=%d" % (sector, nsector))
        sectors_to_read = list(range(sector, sector+nsector))
        request = struct.pack('!HH' + 'I'*nsector, READ_CMD, nsector, *sectors_to_read)
        #log.log_data(request)
        
        if self.callback is not None:
            self.callback()

        # send out request
        bytes_written = self.device.writePCard(request)
        log.debug("%d bytes written" % bytes_written)

        # read return code
        data = self.device.readPCard(2)
        #log.log_data(data)
        code = struct.unpack('!H', data)[0]

        log.debug("Return code: %x" % code)

        if code == 0x0110:

            # read sector count and version
            data = self.device.readPCard(6)
            nsector_read, ver = struct.unpack('!IH', data)

            log.debug("code=0x%x, nsector=%d, ver=%d" % (code, nsector_read, ver))

            buffer, data_read, total_to_read = '', 0, nsector * SECTOR_SIZE

            while (data_read < total_to_read):
                data = self.device.readPCard(total_to_read)

                data_read += len(data)
                buffer = ''.join([buffer, data])

                if self.callback is not None:
                    self.callback()            

            if self.cache_flag:
                i = 0

                for s in range(sector, sector + nsector_read):
                    self.sector_buffer[s] = buffer[i : i+SECTOR_SIZE]
                    #log.debug("Sector %d data=\n%s" % (s, repr(self.sector_buffer[s])))
                    count = self.sector_buffer_counts.get(s, 0)
                    self.sector_buffer_counts[s] = count+1
                    i += SECTOR_SIZE

                    if self.callback is not None:
                        self.callback()            

                self._check_cache(nsector)

            #log.log_data(buffer)
            return buffer
        else:
            log.error("Error code: %d" % code)
            return ''

    def _write(self, sector, nsector, buffer):

        #log.debug("write pcard sector: sector=%d count=%d len=%d data=\n%s" % (sector, nsector, len(buffer), repr(buffer)))
        log.debug("write pcard sector: sector=%d count=%d len=%d" % (sector, nsector, len(buffer)))
        
        if not self.channel_opened:
            self.open_channel()


        sectors_to_write = list(range(sector, sector+nsector))
        request = struct.pack('!HHH' + 'I'*nsector, WRITE_CMD, nsector, 0, *sectors_to_write)
        request = ''.join([request, buffer])

        if self.callback is not None:
            self.callback()

        self.device.writePCard(request)
        data = self.device.readPCard(2)

        if self.callback is not None:
            self.callback()

        code = struct.unpack('!H', data)[0]

        if code != NAK:
            if self.cache_flag:
                i = 0
                for s in range(sector, sector+nsector):
                    log.debug("Caching sector %d" % sector)
                    self.sector_buffer[s] = buffer[i:i+SECTOR_SIZE]
                    self.sector_buffer_counts[s] = 1
                    i += SECTOR_SIZE

                if self.callback is not None:
                    self.callback()    

                self._check_cache(nsector)

            return 0

        else:    
            if self.cache_flag:
                for s in range(sector, sector+nsector):
                    try:
                        del self.sector_buffer[s]
                        del self.sector_buffer_counts[s]
                    except KeyError:
                        pass

            log.error("Photo card write failed (Card may be write protected)")
            self.close_channel()
            return 1


    def _check_cache(self, nsector):
        if len(self.sector_buffer) > MAX_CACHE:
            # simple minded: scan for first nsector sectors that has count of 1 and throw it away
            t, n = list(self.sector_buffer.keys())[:], 0
            for s in t:
                if self.sector_buffer_counts[s] == 1:
                    del self.sector_buffer[s]
                    del self.sector_buffer_counts[s]
                    n += 1
                    if n >= nsector:
                        break
                    if self.callback is not None:
                        self.callback()



    def cache_info(self):
        return self.sector_buffer_counts

    def cache_check(self, sector):
        return self.sector_buffer_counts.get(sector, 0)

    def cache_control(self, control):
        self.cache_flag = control

        if not self.cache_flag:
            self.cache_reset()

    def cache_state(self):
        return self.cache_flag

    def cache_reset(self):
        self.sector_buffer.clear()
        self.sector_buffer_counts.clear()

    def df(self):
        df = 0
        self.START_OPERATION('df')
        try:
            df = pcardext.df()
        finally:
            self.END_OPERATION('df')
            return df

    def ls(self, force_read=True, glob_list='*', openclose=True):
        if not glob_list:
            glob_list = '*'
        if force_read:
            self.START_OPERATION('ls')
            try:
                self.current_dir = pcardext.ls()
            finally:
                self.END_OPERATION('ls', openclose)

        self.current_dir = [(n.lower(),a,s) for (n,a,s) in self.current_dir]

        if glob_list == '*':
            return self.current_dir

        return [fnmatch.filter(self.current_dir, x) for x in glob_list.strip().lower().split()][0]

    def size(self, name):
        for f in self.current_dir:
            if f == name:
                return self.current_dir[f][2]
        return 0

    def current_files(self):
        return [x for x in self.current_dir if x[1] != 'd']

    def current_directories(self):
        return [x for x in self.current_dir if x[1] == 'd']

    def match_files(self, glob_list):
        if len(glob_list) > 0:
            current_files = [x[0] for x in self.current_files()]
            return [fnmatch.filter(current_files, x) for x in glob_list.strip().lower().split()][0]
        return []

    def match_dirs(self, glob_list):
        if len(glob_list) > 0:
            current_dirs = [x[0] for x in self.current_directories()]
            return [fnmatch.filter(current_dirs, x) for x in glob_list.strip().lower().split()][0]
        return []

    def classify_file(self, filename):
        t = mimetypes.guess_type(filename)[0]
        if t is None:
            return 'unknown/unknown'
        return t

    # copy a single file fom pwd to lpwd
    def cp(self, name, local_file, openclose=True):
        self.START_OPERATION('cp')
        total = 0
        try:
            f = open(local_file, 'w');
            total = pcardext.cp(name, f.fileno())
            f.close()
        finally:
            self.END_OPERATION('cp', openclose)
            return total

    # cp multiple files in the current working directory
    def cp_multiple(self, filelist, remove_after_copy, cp_status_callback=None, rm_status_callback=None):
        delta, total = 0, 0
        self.START_OPERATION('cp_multiple')
        t1 = time.time()
        try:
            for f in filelist:

                size = self.cp(f, f, False)

                if cp_status_callback:
                    cp_status_callback(os.path.join(self.pwd(), f), os.path.join(os.getcwd(), f), size)

                total += size


                if remove_after_copy:
                    pcardext.rm(f)

            t2 = time.time()
            delta = t2-t1
        finally:
            if remove_after_copy:
                self.ls(True, '*', False)
            self.END_OPERATION('cp_multiple')
            return (total, delta)

    # cp multiple files with paths
    def cp_list(self, filelist, remove_after_copy, cp_status_callback=None, rm_status_callback=None):
        self.save_wd()
        delta, total = 0, 0
        self.START_OPERATION('cp_list')
        t1 = time.time()
        try:
            for f in filelist:

                path_list = f.split('/')[:-1]
                filename = f.split('/')[-1]

                for p in path_list:
                    self.cd(p, False)

                size = self.cp(filename, filename, False)

                if cp_status_callback is not None:
                    cp_status_callback(f, os.path.join(os.getcwd(), filename), size)

                total += size    

                if remove_after_copy:
                    pcardext.rm(filename)

                    if rm_status_callback is not None:
                        rm_status_callback(f)

                self.cd('/', False)

            t2 = time.time()
            delta = t2-t1
        finally:
            #if remove_after_copy:
            #    self.ls( True, '*', False )
            self.restore_wd()
            self.END_OPERATION('cp_list')
            return (total, delta)



    def cp_fd(self, name, fd):
        total = 0
        self.START_OPERATION('cp_fd')
        try:
            total = pcardext.cp(name, fd)
        finally:
            self.END_OPERATION('cp_fd')
            return total


    def unload(self, unload_list, cp_status_callback=None, rm_status_callback=None, dont_remove=False):
        was_cancelled = False
        self.save_wd()
        self.START_OPERATION('unload')
        total = 0
        t1 = time.time()

        for f in unload_list:
            if not was_cancelled:
                name, size, typ, subtyp = f

                p = name.split('/')
                dirs = p[:-1]
                filename = p[-1]
                self.cd('/', False)

                if cp_status_callback is not None:
                    if cp_status_callback(os.path.join(self.pwd(), filename), 
                                            os.path.join(os.getcwd(), filename), 0):
                        was_cancelled = True
                        break

                if len(dirs) > 0:
                    for d in dirs:
                        self.cd(d, False)

                if os.path.exists(os.path.join(os.getcwd(), filename)):
                    i = 2

                    while True:
                        if not os.path.exists(os.path.join(os.getcwd(), filename + " (%d)" % i)):
                            break

                        i += 1

                    total += self.cp(filename, filename + " (%d)" % i, False)

                else:    
                    total += self.cp(filename, filename, False)

                if cp_status_callback is not None:
                    if cp_status_callback(os.path.join(self.pwd(), filename), 
                                            os.path.join(os.getcwd(), filename), size):
                        was_cancelled = True
                        break

                if not dont_remove:
                    if rm_status_callback is not None:
                        rm_status_callback(os.path.join(self.pwd(), filename))

                    self.rm(filename, False, False)


        t2 = time.time()
        self.restore_wd(False)
        self.ls(True, '*', False)
        self.END_OPERATION('unload')

        return total, (t2-t1), was_cancelled


    def get_unload_list(self):
        tree = self.tree()
        return self.__build_unload_list(tree)


    def __build_unload_list(self, tree, path=None, out=None): 
        if path is None:
            out = []
            path = utils.Stack()
        for d in tree:
            if type(tree[d]) == type({}):
                path.push(d)
                self.__build_unload_list(tree[d], path, out) 
                path.pop()
            else:
                typ, subtyp = self.classify_file(d).split('/')
                if typ in ['image', 'audio', 'video']:
                    p = path.as_list()
                    name = '/'.join(['/'.join(p), d])
                    out.append((name, tree[d], typ, subtyp)) 

        return out


    def info(self):
        return pcardext.info()


    def cd(self, dirs, openclose=True):
        self.START_OPERATION('cd')
        try:
            stat = pcardext.cd(dirs)
            if stat:
                if dirs == '/':
                    self.dir_stack.clear()

                else:
                    dirs = dirs.split('/')
                    for d in dirs:
                        self.dir_stack.push(d)

                self.ls(True, '*', False)

        finally:
            self.END_OPERATION('cd', openclose)


    def cdup(self, openclose=True):
        if len(self.dir_stack.as_list()) == 0:
            return self.cd('/', openclose)

        self.dir_stack.pop()
        self.START_OPERATION('cdup')
        try:
            pcardext.cd('/')

            for d in self.dir_stack.as_list():
                pcardext.cd(d)

            self.ls(True, '*', False)
        finally:
            self.END_OPERATION('cdup', openclose)

    def rm(self, name, refresh_dir=True, openclose=True):
        self.START_OPERATION()
        try:
            r = pcardext.rm(name)

            if refresh_dir:
                self.ls(True, '*', False)
        finally:
            self.END_OPERATION(openclose)
            return r

    def mount(self):
        log.debug("Mounting photocard...")
        self.START_OPERATION('mount')
        try:
            stat = pcardext.mount(self._read, self._write)
            disk_info = pcardext.info()
            self.write_protect = disk_info[8]
            log.debug("stat=%d" % stat)

            if stat == 0:
                if self.write_protect:
                    # if write_protect is True,
                    # card write NAK'd and channel was 
                    # closed. We have to reopen here.
                    self.open_channel()

                self.pcard_mounted = True
                pcardext.cd('/')

                self.ls(True, '*', False)

            else:
                self.pcard_mounted = False
                raise Error(ERROR_DEVICE_DOES_NOT_SUPPORT_OPERATION)
        finally:
            if self.pcard_mounted:
                self.END_OPERATION('mount')



    def pwd(self):
        return '/' + '/'.join(self.dir_stack.as_list())


    def save_wd(self):
        self.saved_pwd = self.dir_stack.as_list()[:]

    def restore_wd(self, openclose=True):
        self.cd('/', openclose)
        for d in self.saved_pwd:
            self.cd(d, openclose)


    def tree(self):
        self.START_OPERATION('tree')
        dir_tree = {}
        try:
            self.save_wd()
            dir_tree = self.__tree()
            self.restore_wd(False)
        finally:
            self.END_OPERATION('tree')
            return dir_tree

    def __tree(self, __d=None):
        if __d is None:
            __d = {}
            pcardext.cd('/')

        for f in pcardext.ls(): # True, '*', False ):
            fname = f[0].lower()

            if self.callback is not None:
                self.callback()

            if fname not in ('.', '..'):
                if f[1] == 'd':
                    self.cd(fname, False)
                    __d[fname] = {}
                    __d[fname] = self.__tree(__d[fname])
                    self.cdup(False)

                else:
                    __d[fname] = f[2]

        return __d


    def get_exif(self, name):
        exif_info = {}
        self.START_OPERATION('get_exif')
        pcf = None
        try:
            pcf = PhotoCardFile(self, name)
            exif_info = exif.process_file(pcf)
        finally:    
            if pcf is not None:
                pcf.close()
            self.END_OPERATION('get_exif')
            return exif_info


    def get_exif_path(self, name):
        exif_info = {}
        self.START_OPERATION('get_exif_path')
        self.save_wd()
        try:
            path_list = name.split('/')[:-1]
            filename = name.split('/')[-1]

            for p in path_list:
                self.cd(p, False)

            pcf = PhotoCardFile(self, filename)
            exif_info = exif.process_file(pcf)

        finally:    
            self.restore_wd(False)
            pcf.close()
            self.END_OPERATION('get_exif_path')
            return exif_info



    def sector(self, sector):
        self.START_OPERATION('sector')
        try:
            data = self._read(sector, 1)
        finally:
            self.END_OPERATION('sector')
            return data

    def umount(self):
        pcardext.umount()
        self.pcard_mounted = False

    def open_channel(self):
        self.channel_opened = True
        self.device.openPCard()

    def close_channel(self):
        self.channel_opened = False
        self.device.closePCard()






