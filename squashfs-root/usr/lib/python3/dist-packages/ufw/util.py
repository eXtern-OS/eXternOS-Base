'''util.py: utility functions for ufw'''
#
# Copyright 2008-2018 Canonical Ltd.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3,
#    as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import print_function
import binascii
import codecs
import errno
import fcntl
import io
import inspect
import os
import re
import shutil
import socket
import struct
import subprocess
import sys

from functools import reduce
from tempfile import mkstemp, mktemp

DEBUGGING = False
msg_output = None # for redirecting stdout in msg() and write_to_file()

# We support different protocols these days and only come combinations are
# valid
supported_protocols = [ 'tcp', 'udp', 'ipv6', 'esp', 'ah', 'igmp', 'gre' ]
portless_protocols = [ 'ipv6', 'esp', 'ah', 'igmp', 'gre' ]
ipv4_only_protocols = [ 'ipv6', 'igmp' ]


def get_services_proto(port):
    '''Get the protocol for a specified port from /etc/services'''
    proto = ""
    try:
        socket.getservbyname(port)
    except Exception:
        raise

    try:
        socket.getservbyname(port, "tcp")
        proto = "tcp"
    except Exception:
        pass

    try:
        socket.getservbyname(port, "udp")
        if proto == "tcp":
            proto = "any"
        else:
            proto = "udp"
    except Exception:
        pass

    return proto


def parse_port_proto(p_str):
    '''Parse port or port and protocol'''
    port = ""
    proto = ""
    tmp = p_str.split('/')
    if len(tmp) == 1:
        port = tmp[0]
        proto = "any"
    elif len(tmp) == 2:
        port = tmp[0]
        proto = tmp[1]
        if proto in portless_protocols:
            err_msg = _("Invalid port with protocol '%s'" % proto)
            raise ValueError(err_msg)
    else:
        err_msg = _("Bad port")
        raise ValueError(err_msg)
    return (port, proto)


def valid_address6(addr):
    '''Verifies if valid IPv6 address'''
    if not socket.has_ipv6:
        warn("python does not have IPv6 support.")
        return False

    # quick and dirty test
    if len(addr) > 43 or not re.match(r'^[a-fA-F0-9:\./]+$', addr):
        return False

    net = addr.split('/')
    try:
        socket.inet_pton(socket.AF_INET6, net[0])
    except Exception:
        return False

    if len(net) > 2:
        return False
    elif len(net) == 2:
        # Check netmask specified via '/'
        if not _valid_cidr_netmask(net[1], True):
            return False

    return True


def valid_address4(addr):
    '''Verifies if valid IPv4 address'''
    # quick and dirty test
    if len(addr) > 31 or not re.match(r'^[0-9\./]+$', addr):
        return False

    net = addr.split('/')
    try:
        socket.inet_pton(socket.AF_INET, net[0])
        # socket.inet_pton() should raise an exception, but let's be sure
        if not _valid_dotted_quads(net[0], False): # pragma: no cover
            return False
    except Exception:
        return False

    if len(net) > 2:
        return False
    elif len(net) == 2:
        # Check netmask specified via '/'
        if not valid_netmask(net[1], False):
            return False

    return True


def valid_netmask(nm, v6):
    '''Verifies if valid cidr or dotted netmask'''
    return _valid_cidr_netmask(nm, v6) or _valid_dotted_quads(nm, v6)


#
# valid_address()
#    version="6" tests if a valid IPv6 address
#    version="4" tests if a valid IPv4 address
#    version="any" tests if a valid IP address (IPv4 or IPv6)
#
def valid_address(addr, version="any"):
    '''Validate IP addresses'''
    if version == "6":
        return valid_address6(addr)
    elif version == "4":
        return valid_address4(addr)
    elif version == "any":
        return valid_address4(addr) or valid_address6(addr)

    raise ValueError


def normalize_address(orig, v6):
    '''Convert address to standard form. Use no netmask for IP addresses. If
       netmask is specified and not all 1's, for IPv4 use cidr if possible,
       otherwise dotted netmask and for IPv6, use cidr.
    '''
    net = []
    changed = False
    version = "4"
    s_type = socket.AF_INET
    if v6:
        version = "6"
        s_type = socket.AF_INET6

    if '/' in orig:
        net = orig.split('/')
        # Remove host netmasks
        if v6 and net[1] == "128":
            del net[1]
        elif not v6 and (net[1] == "32" or net[1] == "255.255.255.255"):
            del net[1]
    else:
        net.append(orig)

    if not v6 and len(net) == 2 and _valid_dotted_quads(net[1], v6):
        try:
            net[1] = _dotted_netmask_to_cidr(net[1], v6)
        except Exception:
            # Not valid cidr, so just use the dotted quads
            pass

    addr = net[0]

    # Convert to packed binary, then convert back
    addr = socket.inet_ntop(s_type, socket.inet_pton(s_type, addr))
    if addr != net[0]:
        changed = True

    if len(net) == 2:
        addr += "/" + net[1]
        if not v6:
            network = _address4_to_network(addr)
            if network != addr:
                dbg_msg = "Using '%s' for address '%s'" % (network, addr)
                debug(dbg_msg)
                addr = network
                changed = True

    if not valid_address(addr, version):
        dbg_msg = "Invalid address '%s'" % (addr)
        debug(dbg_msg)
        raise ValueError

    return (addr, changed)


def open_file_read(fn):
    '''Opens the specified file read-only'''
    try:
        orig = open(fn, 'r')
    except Exception:
        raise

    return orig


def open_files(fn):
    '''Opens the specified file read-only and a tempfile read-write.'''
    try:
        orig = open_file_read(fn)
    except Exception:
        raise

    try:
        (tmp, tmpname) = mkstemp()
    except Exception: # pragma: no cover
        orig.close()
        raise

    return { "orig": orig, "origname": fn, "tmp": tmp, "tmpname": tmpname }


def write_to_file(fd, out):
    '''Write to the file descriptor and error out of 0 bytes written. Intended
       to be used with open_files() and close_files().'''
    if out == "":
        return

    if not fd:
        raise OSError(errno.ENOENT, "Not a valid file descriptor")

    # Redirect our writes to stdout to msg_output, if it is set
    if msg_output and fd == sys.stdout.fileno():
        msg_output.write(out)
        return

    rc = -1
    # cover not in python3, so can't test for this
    if sys.version_info[0] >= 3: # pragma: no cover
        rc = os.write(fd, bytes(out, 'ascii'))
    else:
        rc = os.write(fd, out)

    if rc <= 0: # pragma: no cover
        raise OSError(errno.EIO, "Could not write to file descriptor")


def close_files(fns, update=True):
    '''Closes the specified files (as returned by open_files), and update
       original file with the temporary file.
    '''
    fns['orig'].close()
    os.close(fns['tmp'])

    if update:
        try:
            shutil.copystat(fns['origname'], fns['tmpname'])
            shutil.copy(fns['tmpname'], fns['origname'])
        except Exception:
            raise

    try:
        os.unlink(fns['tmpname'])
    except OSError:
        raise


def cmd(command):
    '''Try to execute the given command.'''
    debug(command)
    try:
        sp = subprocess.Popen(command, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              universal_newlines=True)
    except OSError as ex:
        return [127, str(ex)]

    out = sp.communicate()[0]
    return [sp.returncode, str(out)]


def cmd_pipe(command1, command2):
    '''Try to pipe command1 into command2.'''
    try:
        sp1 = subprocess.Popen(command1, stdout=subprocess.PIPE)
        sp2 = subprocess.Popen(command2, stdin=sp1.stdout)
    except OSError as ex:
        return [127, str(ex)]

    out = sp2.communicate()[0]
    return [sp2.returncode, str(out)]


# TODO: this is pretty horrible. We should be using only unicode strings
#       internally and decode() when printing rather than doing this.
def _print(output, s):
    '''Implement our own print statement that will output utf-8 when
       appropriate.'''
    try: # python3
        writer = output.buffer
    except Exception:
        writer = output

    try:
        out = s.encode('utf-8', 'ignore')
    # Depends on python version
    except Exception: # pragma: no cover
        out = s

    if msg_output and inspect.isclass(io.StringIO):
        writer.write(s)
    else:
        writer.write(bytes(out))
    output.flush()


def error(out, do_exit=True):
    '''Print error message and exit'''
    try:
        _print(sys.stderr, 'ERROR: %s\n' % out)
    except IOError: # pragma: no cover
        pass

    if do_exit: # pragma: no cover
        sys.exit(1)


def warn(out):
    '''Print warning message'''
    try:
        _print(sys.stderr, 'WARN: %s\n' % out)
    except IOError: # pragma: no cover
        pass


def msg(out, output=sys.stdout, newline=True):
    '''Print message'''
    if msg_output and output == sys.stdout:
        output = msg_output

    try:
        if newline:
            _print(output, '%s\n' % out)
        else:
            _print(output, '%s' % out)
    except IOError: # pragma: no cover
        pass


def debug(out):
    '''Print debug message'''
    if DEBUGGING:
        try:
            _print(sys.stderr, 'DEBUG: %s\n' % out)
        except IOError: # pragma: no cover
            pass


def word_wrap(text, width):
    '''
    A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line
    breaks are posix newlines (\n).
    '''
    return reduce(lambda line, word, width=width: '%s%s%s' %
                  (line,
                   ' \n'[(len(line)-line.rfind('\n') - 1 +
                          len(word.split('\n', 1)[0]) >= width)],
                   word),
                  text.split(' ')
                 )


def wrap_text(text):
    '''Word wrap to a specific width'''
    return word_wrap(text, 75)


def human_sort(lst):
    '''Sorts list of strings into numeric order, with text case-insensitive.
       Modifies list in place.

       Eg:
       [ '80', 'a222', 'a32', 'a2', 'b1', '443', 'telnet', '3', 'http', 'ZZZ']

       sorts to:
       ['3', '80', '443', 'a2', 'a32', 'a222', 'b1', 'http', 'telnet', 'ZZZ']
    '''
    norm = lambda t: int(t) if t.isdigit() else t.lower()
    lst.sort(key=lambda k: [ norm(c) for c in re.split('([0-9]+)', k)])


def get_ppid(mypid=os.getpid()):
    '''Finds parent process id for pid based on /proc/<pid>/stat. See
       'man 5 proc' for details.
    '''
    try:
        pid = int(mypid)
    except Exception:
        raise ValueError("pid must be an integer")

    name = os.path.join("/proc", str(pid), "stat")
    if not os.path.isfile(name):
        raise IOError("Couldn't find '%s'" % (name))

    try:
        # LP: #1101304
        # 9983 (cmd) S 923 ...
        # 9983 (cmd with spaces) S 923 ...
        ppid = open(name).readlines()[0].split(')')[1].split()[1]
    except Exception: # pragma: no cover
        raise

    return int(ppid)


def under_ssh(pid=os.getpid()):
    '''Determine if current process is running under ssh'''
    try:
        ppid = get_ppid(pid)
    except IOError:
        warn_msg = _("Couldn't find pid (is /proc mounted?)")
        warn(warn_msg)
        return False
    except Exception:
        err_msg = _("Couldn't find parent pid for '%s'") % (str(pid))
        raise ValueError(err_msg)

    # pid '1' is 'init' and '0' is the kernel. This should still work when
    # pid randomization is in use, but needs to be checked.
    if pid == 1 or ppid <= 1:
        return False

    path = os.path.join("/proc", str(ppid), "stat")
    if not os.path.isfile(path): # pragma: no cover
        err_msg = _("Couldn't find '%s'") % (path)
        raise ValueError(err_msg)

    try:
        exe = open(path).readlines()[0].split()[1]
    except Exception: # pragma: no cover
        err_msg = _("Could not find executable for '%s'") % (path)
        raise ValueError(err_msg)
    debug("under_ssh: exe is '%s'" % (exe))

    # unit tests might be run remotely, so can't test for either
    if exe == "(sshd)": # pragma: no cover
        return True
    else: # pragma: no cover
        return under_ssh(ppid)


#
# Internal helper functions
#
def _valid_cidr_netmask(nm, v6):
    '''Verifies cidr netmasks'''
    num = 32
    if v6:
        num = 128

    if not re.match(r'^[0-9]+$', nm) or int(nm) < 0 or int(nm) > num:
        return False

    return True


def _valid_dotted_quads(nm, v6):
    '''Verifies dotted quad ip addresses and netmasks'''
    if v6:
        return False
    else:
        if re.match(r'^[0-9]+\.[0-9\.]+$', nm):
            quads = re.split('\.', nm)
            if len(quads) != 4:
                return False
            for q in quads:
                if not q or int(q) < 0 or int(q) > 255:
                    return False
        else:
            return False

    return True


#
# _dotted_netmask_to_cidr()
# Returns:
#   cidr integer (0-32 for ipv4 and 0-128 for ipv6)
#
# Raises exception if cidr cannot be found
#
def _dotted_netmask_to_cidr(nm, v6):
    '''Convert netmask to cidr. IPv6 dotted netmasks are not supported.'''
    cidr = ""
    if v6:
        raise ValueError
    else:
        if not _valid_dotted_quads(nm, v6):
            raise ValueError

        mbits = 0

        # python3 doesn't have long(). We could technically use int() here
        # since python2 guarantees at least 32 bits for int(), but this helps
        # future-proof.
        try: # pragma: no cover
            bits = long(struct.unpack('>L', socket.inet_aton(nm))[0])
        except NameError: # pragma: no cover
            bits = int(struct.unpack('>L', socket.inet_aton(nm))[0])

        found_one = False
        for n in range(32):
            if (bits >> n) & 1 == 1:
                found_one = True
            else:
                if found_one:
                    mbits = -1
                    break
                else:
                    mbits += 1

        if mbits >= 0 and mbits <= 32:
            cidr = str(32 - mbits)

    if not _valid_cidr_netmask(cidr, v6):
        raise ValueError

    return cidr


#
# _cidr_to_dotted_netmask()
# Returns:
#   dotted netmask string
#
# Raises exception if dotted netmask cannot be found
#
def _cidr_to_dotted_netmask(cidr, v6):
    '''Convert cidr to netmask. IPv6 dotted netmasks not supported.'''
    nm = ""
    if v6:
        raise ValueError
    else:
        if not _valid_cidr_netmask(cidr, v6):
            raise ValueError

        # python3 doesn't have long(). We could technically use int() here
        # since python2 guarantees at least 32 bits for int(), but this helps
        # future-proof.
        try: # pragma: no cover
            bits = long(0)
        except NameError: # pragma: no cover
            bits = 0

        for n in range(32):
            if n < int(cidr):
                bits |= 1 << 31 - n
        nm = socket.inet_ntoa(struct.pack('>L', bits))

    # The above socket.inet_ntoa() should raise an error, but let's be sure
    if not _valid_dotted_quads(nm, v6): # pragma: no cover
        raise ValueError

    return nm


def _address4_to_network(addr):
    '''Convert an IPv4 address and netmask to a network address'''
    if '/' not in addr:
        debug("_address4_to_network: skipping address without a netmask")
        return addr

    tmp = addr.split('/')
    if len(tmp) != 2 or not _valid_dotted_quads(tmp[0], False):
        raise ValueError

    host = tmp[0]
    orig_nm = tmp[1]

    nm = orig_nm
    if _valid_cidr_netmask(nm, False):
        nm = _cidr_to_dotted_netmask(nm, False)

    # Now have dotted quad host and nm, find the network

    # python3 doesn't have long(). We could technically use int() here
    # since python2 guarantees at least 32 bits for int(), but this helps
    # future-proof.
    try: # pragma: no cover
        host_bits = long(struct.unpack('>L', socket.inet_aton(host))[0])
        nm_bits = long(struct.unpack('>L', socket.inet_aton(nm))[0])
    except NameError: # pragma: no cover
        host_bits = int(struct.unpack('>L', socket.inet_aton(host))[0])
        nm_bits = int(struct.unpack('>L', socket.inet_aton(nm))[0])

    network_bits = host_bits & nm_bits
    network = socket.inet_ntoa(struct.pack('>L', network_bits))

    return "%s/%s" % (network, orig_nm)


def _address6_to_network(addr):
    '''Convert an IPv6 address and netmask to a network address'''
    def dec2bin(num, count):
        '''Decimal to binary'''
        return "".join([str((num >> y) & 1) for y in range(count-1, -1, -1)])

    if '/' not in addr:
        debug("_address6_to_network: skipping address without a netmask")
        return addr

    tmp = addr.split('/')
    if len(tmp) != 2 or not valid_netmask(tmp[1], True):
        raise ValueError

    orig_host = tmp[0]
    netmask = tmp[1]

    unpacked = struct.unpack('>8H', socket.inet_pton(socket.AF_INET6, \
                                                     orig_host))

    # Get the host bits
    try: # python3 doesn't have long()
        host_bits = long(0)
    except NameError: # pragma: no cover
        host_bits = 0

    for i in range(8):
        n = dec2bin(unpacked[i], 16)
        for j in range(16):
            host_bits |= (1 & int(n[j])) << (127-j-i*16)

    # Create netmask bits
    try: # python3 doesn't have long()
        nm_bits = long(0)
    except NameError: # pragma: no cover
        nm_bits = 0

    for i in range(128):
        if i < int(netmask):
            nm_bits |= 1 << (128 - 1) - i

    # Apply the netmask to the host to determine the network
    net = host_bits & nm_bits

    # Break the network into chunks suitable for repacking
    lst = []
    for i in range(8):
        lst.append(int(dec2bin(net, 128)[i*16:i*16+16], 2))

    # Create the network string
    network = socket.inet_ntop(socket.AF_INET6, \
                               struct.pack('>8H', lst[0], lst[1], \
                                           lst[2], lst[3], lst[4], \
                                           lst[5], lst[6], lst[7]))

    return "%s/%s" % (network, netmask)


def in_network(tested_add, tested_net, v6):
    '''Determine if address x is in network y'''
    tmp = tested_net.split('/')
    if len(tmp) != 2 or not valid_netmask(tmp[1], v6):
        raise ValueError

    orig_host = tmp[0]
    netmask = tmp[1]

    if orig_host == "0.0.0.0" or orig_host == "::":
        return True

    address = tested_add
    if '/' in address:
        tmp = address.split('/')
        if len(tmp) != 2 or not valid_netmask(tmp[1], v6):
            raise ValueError
        address = tmp[0]

    if address == "0.0.0.0" or address == "::":
        return True

    if v6:
        if not valid_address6(address) or not valid_address6(orig_host):
            raise ValueError
    else:
        if not valid_address4(address) or not valid_address4(orig_host):
            raise ValueError

    if _valid_cidr_netmask(netmask, v6) and not v6:
        netmask = _cidr_to_dotted_netmask(netmask, v6)

    # Now apply the network's netmask to the address
    if v6:
        orig_network = _address6_to_network("%s/%s" % \
                                            (orig_host, netmask)).split('/')[0]
        network = _address6_to_network("%s/%s" % \
                                       (address, netmask)).split('/')[0]
    else:
        orig_network = _address4_to_network("%s/%s" % \
                                            (orig_host, netmask)).split('/')[0]
        network = _address4_to_network("%s/%s" % \
                                       (address, netmask)).split('/')[0]

    return network == orig_network


def get_iptables_version(exe="/sbin/iptables"):
    '''Return iptables version'''
    (rc, out) = cmd([exe, '-V'])
    if rc != 0:
        raise OSError(errno.ENOENT, "Error running '%s'" % (exe))
    tmp = re.split('\s', out)
    return re.sub('^v', '', tmp[1])


# must be root, so don't report coverage in unit tests
def get_netfilter_capabilities(exe="/sbin/iptables", do_checks=True):
    '''Return capabilities set for netfilter to support new features. Callers
       must be root.'''
    def test_cap(exe, chain, rule):
        args = [exe, '-A', chain]
        (rc, out) = cmd(args + rule)
        if rc == 0:
            return True
        return False # pragma: no cover

    if do_checks and os.getuid() != 0:
        raise OSError(errno.EPERM, "Must be root")

    caps = []

    chain = "ufw-caps-test"
    if exe.endswith("ip6tables"):
        chain = "ufw6-caps-test"

    # Use a unique chain name (with our locking code, this shouldn't be
    # needed, but this is a cheap safeguard in case the chain happens to
    # still be lying around. We do this to avoid a separate call to
    # iptables to check for existence)
    chain += mktemp(prefix='', dir='')

    # First install a test chain
    (rc, out) = cmd([exe, '-N', chain])
    if rc != 0:
        raise OSError(errno.ENOENT, out) # pragma: no cover

    # Now test for various capabilities. We won't test for everything, just
    # the stuff we know isn't supported everywhere but we want to support.

    # recent-set
    if test_cap(exe, chain, ['-m', 'conntrack', '--ctstate', 'NEW', \
                             '-m', 'recent', '--set']):
        caps.append('recent-set')

    # recent-update
    if test_cap(exe, chain, ['-m', 'conntrack', '--ctstate', 'NEW', \
                             '-m', 'recent', '--update', \
                             '--seconds', '30', \
                             '--hitcount', '6']):
        caps.append('recent-update')

    # Cleanup
    cmd([exe, '-F', chain])
    (rc, out) = cmd([exe, '-X', chain])
    if rc != 0:
        raise OSError(errno.ENOENT, out) # pragma: no cover

    return caps


def parse_netstat_output(v6):
    '''Get and parse netstat the output from get_netstat_output()'''

    # d[proto][port] -> list of dicts:
    #   d[proto][port][0][laddr|raddr|uid|pid|exe]

    netstat_output = get_netstat_output(v6)

    d = dict()
    for line in netstat_output.splitlines():
        if not line.startswith('tcp') and not line.startswith('udp'): # pragma: no cover
            continue

        tmp = line.split()

        proto = tmp[0]
        port = tmp[1].split(':')[-1]

        item = dict()
        item['laddr'] = ':'.join(tmp[1].split(':')[:-1])
        item['uid'] = tmp[3]
        item['pid'] = tmp[5].split('/')[0]
        if item['pid'] == '-':
            item['exe'] = item['pid']
        else: # pragma: no cover
            item['exe'] = tmp[5].split('/')[1]

        if proto not in d:
            d[proto] = dict()
            d[proto][port] = []
        else:
            if port not in d[proto]:
                d[proto][port] = []
        d[proto][port].append(item)

    return d


def get_ip_from_if(ifname, v6=False):
    '''Get IP address for interface'''
    addr = ""

    # we may not have an IPv6 address, so no coverage
    if v6: # pragma: no cover
        proc = '/proc/net/if_inet6'
        if not os.path.exists(proc):
            raise OSError(errno.ENOENT, "'%s' does not exist" % proc)

        for line in open(proc).readlines():
            tmp = line.split()
            if ifname == tmp[5]:
                addr = ":".join( \
                           [tmp[0][i:i+4] for i in range(0, len(tmp[0]), 4)])

                if tmp[2].lower() != "80":
                    addr = "%s/%s" % (addr, int(tmp[2].lower(), 16))

        if addr == "":
            raise IOError(errno.ENODEV, "No such device")
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            addr = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, \
                                    struct.pack('256s', ifname[:15]))[20:24])
        except Exception:
            raise IOError(errno.ENODEV, "No such device")

    return normalize_address(addr, v6)[0]


def get_if_from_ip(addr):
    '''Get interface for IP address'''
    v6 = False
    proc = '/proc/net/dev'
    if valid_address6(addr):
        v6 = True
        proc = '/proc/net/if_inet6'
    elif not valid_address4(addr):
        raise IOError(errno.ENODEV, "No such device")

    if not os.path.exists(proc): # pragma: no cover
        raise OSError(errno.ENOENT, "'%s' does not exist" % proc)

    matched = ""
    # we may not have an IPv6 address, so no coverage
    if v6: # pragma: no cover
        for line in open(proc).readlines():
            tmp = line.split()
            ifname = tmp[5].strip()

            tmp_addr = ":".join( \
                           [tmp[0][i:i+4] for i in range(0, len(tmp[0]), 4)])
            if tmp[2].lower() != "80":
                tmp_addr = "%s/%s" % (tmp_addr, int(tmp[2].lower(), 16))

            if addr == tmp_addr or \
               ('/' in tmp_addr and in_network(addr, tmp_addr, True)):
                matched = ifname
                break
    else:
        for line in open(proc).readlines():
            if ':' not in line:
                continue
            ifname = line.split(':')[0].strip()
            # this can fail for certain devices, so just skip them
            try:
                ip = get_ip_from_if(ifname, False)
            except IOError: # pragma: no cover
                continue

            if ip == addr:
                matched = ifname
                break

    return matched


def _get_proc_inodes():
    '''Get inodes of files in /proc'''
    proc_files = os.listdir("/proc")
    proc_files.sort()
    pat = re.compile(r'^[0-9]+$')
    inodes = dict()
    for i in proc_files:
        if not pat.match(i):
            continue

        fd_path = os.path.join("/proc", i, "fd")

        # skip stuff we can't read or that goes away
        if not os.access(fd_path, os.F_OK | os.R_OK):
            continue

        exe_path = "-"
        try:
            exe_path = os.readlink(os.path.join("/proc", i, "exe"))
        except Exception: # pragma: no cover
            pass

        try:
            dirs = os.listdir(fd_path)
        except Exception: # pragma: no cover
            continue

        for j in dirs:
            try:
                inode = os.stat(os.path.join(fd_path, j))[1]
            except Exception: # pragma: no cover
                continue
            inodes[inode] = "%s/%s" % (i, os.path.basename(exe_path))

    return inodes


def _read_proc_net_protocol(protocol):
    '''Read /proc/net/(tcp|udp)[6] file and return a list of tuples '''
    tcp_states = { 1: "ESTABLISHED",
                   2: "SYN_SENT",
                   3: "SYN_RECV",
                   4: "FIN_WAIT1",
                   5: "FIN_WAIT2",
                   6: "TIME_WAIT",
                   7: "CLOSE",
                   8: "CLOSE_WAIT",
                   9: "LAST_ACK",
                   10: "LISTEN",
                   11: "CLOSING"
                 }

    proc_net_fields = { 'local_addr': 1,
                        'state': 3,
                        'uid': 7,
                        'inode': 9
                      }

    fn = os.path.join("/proc/net", protocol)
    # can't test for this
    if not os.access(fn, os.F_OK | os.R_OK): # pragma: no cover
        raise ValueError

    lst = []
    skipped_first = False
    lines = open(fn).readlines()
    for line in lines:
        fields = line.split()
        if not skipped_first:
            skipped_first = True
            continue
        state = tcp_states[int(fields[proc_net_fields['state']], 16)]
        if protocol.startswith("udp"):
            state = "NA"
        elif protocol.startswith("tcp") and state != "LISTEN":
            continue
        laddr, port = fields[proc_net_fields['local_addr']].split(':')
        uid = fields[proc_net_fields['uid']]
        inode = fields[proc_net_fields['inode']]
        lst.append((laddr, int(port, 16), uid, inode, state))

    return lst


def convert_proc_address(paddr):
    '''Convert an address from /proc/net/(tcp|udp)* to a normalized address'''
    converted = ""
    if len(paddr) > 8:
        tmp = ""
        for i in range(0, 32, 8):
            tmp += "".join([ paddr[j-2:j] for j in range(i+8, i, -2) ])
        converted = normalize_address(":".join( \
               [tmp[j:j+4].lower() for j in range(0, len(tmp), 4)]), \
               True)[0]
    else:
        tmp = []
        for i in [ paddr[j-2:j] for j in range(8, 0, -2) ]:
            tmp.append(str(int(i, 16)))
        converted = normalize_address(".".join(tmp), False)[0]

    return converted


def get_netstat_output(v6):
    '''netstat-style output, without IPv6 address truncation'''
    proc_net_data = dict()
    proto = ['tcp', 'udp']
    if v6:
        proto += ['tcp6', 'udp6']
    for p in proto:
        try:
            proc_net_data[p] = _read_proc_net_protocol(p)
        except Exception: # pragma: no cover
            warn_msg = _("Could not get statistics for '%s'" % (p))
            warn(warn_msg)
            continue

    inodes = _get_proc_inodes()

    protocols = list(proc_net_data.keys())
    protocols.sort()

    s = ""
    for p in protocols:
        for (laddr, port, uid, inode, state) in proc_net_data[p]:
            addr = convert_proc_address(laddr)

            exe = "-"
            if int(inode) in inodes:
                # need root for this, so turn off in unit tests
                exe = inodes[int(inode)] # pragma: no cover
            s += "%-5s %-46s %-11s %-5s %-11s %s\n" % (p,
                                                       "%s:%s" % (addr, port),
                                                       state, uid, inode, exe)

    return s


def _findpath(dir, prefix):
    '''Add prefix to dir'''
    if prefix is None:
        return dir
    if dir.startswith('/'):
        if len(dir) < 2:  # /
            newdir = prefix
        else:
            newdir = os.path.join(prefix, dir[1:])
    else:
        newdir = os.path.join(prefix, dir)
    return newdir


def hex_encode(s):
    '''Take a string and convert it to a hex string'''
    if sys.version_info[0] < 3:
        return codecs.encode(s, 'hex')
    # hexlify returns a bytes string (eg, b'ab12cd') so decode that to ascii
    # to have identical output as python2
    return binascii.hexlify(s.encode('utf-8', errors='ignore')).decode('ascii')


def hex_decode(h):
    '''Take a hex string and convert it to a string'''
    if sys.version_info[0] < 3:
        return h.decode(encoding='hex').decode('utf-8')
    return binascii.unhexlify(h).decode('utf-8')


def create_lock(lockfile='/run/ufw.lock', dryrun=False):
    '''Create a blocking lockfile'''
    lock = None
    if not dryrun:
        lock = open(lockfile, 'w')
        fcntl.lockf(lock, fcntl.LOCK_EX)
    return lock


def release_lock(lock):
    '''Free lockfile created with create_lock()'''
    if lock is None:
        return
    try:  # pragma: no cover
        fcntl.lockf(lock, fcntl.LOCK_UN)
        lock.close()
    except ValueError:  # pragma: nocover
        # If the lock is already closed, ignore the exception. This should
        # never happen but let's guard against it in case something changes
        pass
