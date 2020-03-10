#!/usr/bin/python3
# Examine the crash files saved by apport to attempt to determine the cause
# of a segfault.  Currently very very simplistic, and only finds commonly
# understood situations for x86/x86_64.
#
# Copyright 2009-2010  Canonical, Ltd.
# Author: Kees Cook <kees@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import sys, re, logging, io


class ParseSegv(object):
    def __init__(self, registers, disassembly, maps, debug=False):
        if debug:
            if sys.version > '3':
                logging.basicConfig(level=logging.DEBUG,
                                    stream=io.TextIOWrapper(sys.stderr, encoding='UTF-8'))
            else:
                logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

        self.regs = self.parse_regs(registers)
        self.sp = None
        for reg in ['rsp', 'esp']:
            if reg in self.regs:
                self.sp = self.regs[reg]

        self.line, self.pc, self.insn, self.src, self.dest = \
            self.parse_disassembly(disassembly)

        self.stack_vma = None
        self.maps = self.parse_maps(maps)

    def find_vma(self, addr):
        for vma in self.maps:
            if addr >= vma['start'] and addr < vma['end']:
                return vma
        return None

    def parse_maps(self, maps_str):
        maps = []
        for line in maps_str.splitlines():
            items = line.strip().split()
            try:
                span, perms, bits, dev = items[0:4]
            except Exception:
                raise ValueError('Cannot parse maps line: %s' % (line.strip()))
            if len(items) == 5:
                name = None
            else:
                name = items[5]
            start, end = [int(x, 16) for x in span.split('-')]
            if name == '[stack]':
                self.stack_vma = len(maps)
            maps.append({'start': start, 'end': end, 'perms': perms, 'name': name})
            logging.debug('start: %s, end: %s, perms: %s, name: %s', start, end, perms, name)
        return maps

    def parse_regs(self, reg_str):
        regs = dict()
        for line in reg_str.splitlines():
            reg, hexvalue = line.split()[0:2]
            regs[reg] = int(hexvalue, 16)
            logging.debug('%s:0x%08x', reg, regs[reg])
        return regs

    def parse_disassembly(self, disassembly):
        if not self.regs:
            raise ValueError('Registers not loaded yet!?')
        lines = disassembly.splitlines()
        # Throw away possible 'Dump' gdb report line
        if len(lines) > 0 and lines[0].startswith('Dump'):
            lines.pop(0)
        if len(lines) < 1:
            raise ValueError('Failed to load empty disassembly')
        line = lines[0].strip()
        # Drop GDB 7.1's leading $pc mark
        if line.startswith('=>'):
            line = line[2:].strip()
        logging.debug(line)
        pc_str = line.split()[0]
        if pc_str.startswith('0x'):
            pc = int(pc_str.split(':')[0], 16)
        else:
            # Could not identify this instruction line
            raise ValueError('Could not parse PC "%s" from disassembly line: %s' % (pc_str, line))
        logging.debug('pc: 0x%08x', pc)

        full_insn_str = line.split(':', 1)[1].strip()
        # Handle invalid memory
        if 'Cannot access memory at address' in full_insn_str or (full_insn_str == '' and len(lines) == 1):
            return line, pc, None, None, None
        # Handle wrapped lines
        if full_insn_str == '' and lines[1].startswith(' '):
            line = line + ' ' + lines[1].strip()
            full_insn_str = line.split(':', 1)[1].strip()

        insn_parts = full_insn_str.split()
        # Drop call target names "call   0xb7a805af <_Unwind_Find_FDE@plt+111>"
        if insn_parts[-1].endswith('>') and insn_parts[-1].startswith('<'):
            insn_parts.pop(-1)
        # Attempt to find arguments
        args_str = ''
        if len(insn_parts) > 1:
            args_str = insn_parts.pop(-1)
        # Assume remainder is the insn itself
        insn = ' '.join(insn_parts)
        logging.debug('insn: %s', insn)

        args = []
        src = None
        dest = None
        if args_str == '':
            # Could not find insn args
            args = None
        else:
            logging.debug('args: "%s"', args_str)

            for m in re.finditer(r'([^,\(]*(\(:?[^\)]+\))*)', args_str):
                if len(m.group(0)):
                    args.append(m.group(0))
            if len(args) > 0:
                src = args[0]
                logging.debug('src: %s', src)
            if len(args) > 1:
                dest = args[1]
                logging.debug('dest: %s', dest)

        # Set up possible implicit memory destinations (stack actions)
        if insn in ['push', 'pop', 'pushl', 'popl', 'call', 'callq', 'ret', 'retq']:
            for reg in ['rsp', 'esp']:
                if reg in self.regs:
                    dest = '(%%%s)' % (reg)
                    break

        return line, pc, insn, src, dest

    def validate_vma(self, perm, addr, name):
        perm_name = {'x': ['executable', 'executing'], 'r': ['readable', 'reading'], 'w': ['writable', 'writing']}
        vma = self.find_vma(addr)
        if vma is None:
            alarmist = 'unknown'
            if addr < 65536:
                alarmist = 'NULL'
            return False, '%s (0x%08x) not located in a known VMA region (needed %s region)!' % (name, addr, perm_name[perm][0]), '%s %s VMA' % (perm_name[perm][1], alarmist)
        elif perm not in vma['perms']:
            alarmist = ''
            if perm == 'x':
                if 'w' in vma['perms']:
                    alarmist = 'writable '
                else:
                    alarmist = 'non-writable '
            short = '%s %sVMA %s' % (perm_name[perm][1], alarmist, vma['name'])

            return False, '%s (0x%08x) in non-%s VMA region: 0x%08x-0x%08x %s %s' % (name, addr, perm_name[perm][0], vma['start'], vma['end'], vma['perms'], vma['name']), short
        else:
            return True, '%s (0x%08x) ok' % (name, addr), '%s ok' % (perm_name[perm][1])

    def register_value(self, reg):
        reg_orig = reg

        # print reg
        mask = 0
        if reg.startswith('%'):
            # print('%s -> %s' % (reg, reg[1:]))
            reg = reg[1:]
        if reg in self.regs:
            # print('got %s (%d & %d == %d)' % (reg, self.regs[reg], mask, self.regs[reg] & ~mask))
            return self.regs[reg]

        if len(reg) == 2 and reg.endswith('l'):
            mask |= 0xff00
            # print('%s -> %sx' % (reg, reg[0]))
            reg = '%sx' % reg[0]
        if reg in self.regs:
            # print('got %s (%d & %d == %d)' % (reg, self.regs[reg], mask, self.regs[reg] & ~mask))
            return self.regs[reg] & ~mask

        if len(reg) == 2 and reg.endswith('x'):
            mask |= 0xffff0000
            # print('%s -> e%s' % (reg, reg))
            reg = 'e%s' % reg
        if reg in self.regs:
            # print('got %s (%d & %d == %d)' % (reg, self.regs[reg], mask, self.regs[reg] & ~mask))
            return self.regs[reg] & ~mask

        if len(reg) == 3 and reg.startswith('e'):
            mask |= 0xffffffff00000000
            # print('%s -> r%s' % (reg, reg[1:]))
            reg = 'r%s' % reg[1:]
        if reg in self.regs:
            # print('got %s (%d & %d == %d)' % (reg, self.regs[reg], mask, self.regs[reg] & ~mask))
            return self.regs[reg] & ~mask
        raise ValueError("Could not resolve register '%s'" % (reg_orig))

    def calculate_arg(self, arg):
        # Check for and pre-remove segment offset
        segment = 0
        if arg.startswith('%') and ':' in arg:
            parts = arg.split(':', 1)
            segment = self.regs[parts[0][1:]]
            arg = parts[1]

        # Handle standard offsets
        parts = arg.split('(')
        offset = parts[0]
        # Handle negative signs
        sign = 1
        if offset.startswith('-'):
            sign = -1
            offset = offset[1:]
        # Skip call target dereferences
        if offset.startswith('*'):
            offset = offset[1:]
        if len(offset) > 0:
            if offset.startswith('%'):
                # Handle the *%REG case
                add = self.regs[offset[1:]]
            else:
                if not offset.startswith('0x'):
                    raise ValueError('Unknown offset literal: %s' % (parts[0]))
                add = int(offset[2:], 16) * sign
        else:
            add = 0

        def _reg_val(self, text, val=0):
            if text.startswith('%'):
                val = self.regs[text[1:]]
            elif text == "":
                val = 0
            else:
                val = int(text)
            return val

        # (%ebx, %ecx, 4) style
        value = 0
        if len(parts) > 1:
            parens = parts[1][0:-1]
            reg_list = parens.split(',')

            base = 0
            if len(reg_list) > 0:
                base = _reg_val(self, reg_list[0], base)
            index = 0
            if len(reg_list) > 1:
                index = _reg_val(self, reg_list[1], index)
            scale = 1
            if len(reg_list) > 2:
                scale = _reg_val(self, reg_list[2], scale)
            value = base + index * scale

        value = segment + value + add
        if 'esp' in self.regs:
            # 32bit
            return value % 0x100000000
        else:
            # 64bit
            return value % 0x10000000000000000

    def report(self):
        understood = False
        reason = []
        details = ['Segfault happened at: %s' % (self.line)]

        # Verify PC is in an executable region
        valid, out, short = self.validate_vma('x', self.pc, 'PC')
        details.append(out)
        if not valid:
            reason.append(short)
            understood = True

        if self.insn in ['lea', 'leal']:
            # Short-circuit for instructions that do not cause vma access
            details.append('insn (%s) does not access VMA' % (self.insn))
        else:
            # Verify source is readable
            if self.src:
                if ':' not in self.src and (self.src[0] in ['%', '$', '*']) and not self.src.startswith('*%'):
                    details.append('source "%s" ok' % (self.src))
                else:
                    addr = self.calculate_arg(self.src)
                    valid, out, short = self.validate_vma('r', addr, 'source "%s"' % (self.src))
                    details.append(out)
                    if not valid:
                        reason.append(short)
                        understood = True

            # Verify destination is writable
            if self.dest:
                if ':' not in self.dest and (self.dest[0] in ['%', '$', '*']):
                    details.append('destination "%s" ok' % (self.dest))
                else:
                    addr = self.calculate_arg(self.dest)
                    valid, out, short = self.validate_vma('w', addr, 'destination "%s"' % (self.dest))
                    details.append(out)
                    if not valid:
                        reason.append(short)
                        understood = True

        # Handle I/O port operations
        if self.insn in ['out', 'in'] and not understood:
            reason.append('disallowed I/O port operation on port %d' % (self.register_value(self.src)))
            details.append('disallowed I/O port operation on port %d' % (self.register_value(self.src)))
            understood = True

        # Note position of SP with regard to "[stack]" VMA
        if self.sp is not None:
            if self.stack_vma is not None:
                if self.sp < self.maps[self.stack_vma]['start']:
                    details.append("Stack memory exhausted (SP below stack segment)")
                if self.sp >= self.maps[self.stack_vma]['end']:
                    details.append("Stack pointer not within stack segment")
            if not understood:
                valid, out, short = self.validate_vma('r', self.sp, 'SP')
                details.append(out)
                if not valid:
                    reason.append(short)
                    understood = True

        if not understood:
            vma = self.find_vma(self.pc)
            if vma and (vma['name'] == '[vdso]' or vma['name'] == '[vsyscall]'):
                reason.append('Reason could not be automatically determined. (Unhandled exception in kernel code?)')
                details.append('Reason could not be automatically determined. (Unhandled exception in kernel code?)')
            else:
                reason.append('Reason could not be automatically determined.')
                details.append('Reason could not be automatically determined.')
        return understood, '\n'.join(reason), '\n'.join(details)


def add_info(report):
    # Only interested in segmentation faults...
    if report.get('Signal', '0') != '11':
        return

    needed = ['Signal', 'Architecture', 'Disassembly', 'ProcMaps', 'Registers']
    for field in needed:
        if field not in report:
            report['SegvAnalysis'] = 'Skipped: missing required field "%s"' % (field)
            return

    # Only run on segv for x86 and x86_64...
    if not report['Architecture'] in ['i386', 'amd64']:
        return

    try:
        segv = ParseSegv(report['Registers'], report['Disassembly'], report['ProcMaps'])
        understood, reason, details = segv.report()
        if understood:
            report['SegvReason'] = reason
        report['SegvAnalysis'] = details
    except BaseException as e:
        report['SegvAnalysis'] = 'Failure: %s' % (str(e))


if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] in ['-h', '--help']:
        print('To run self-test, run without any arguments (or with -v)')
        print('To do stand-alone crash parsing:')
        print('  Usage: %s Registers.txt Disassembly.txt ProcMaps.txt' % (sys.argv[0]))
        sys.exit(0)

    segv = ParseSegv(open(sys.argv[1]).read(),
                     open(sys.argv[2]).read(),
                     open(sys.argv[3]).read())
    understood, reason, details = segv.report()
    print('%s\n\n%s' % (reason, details))
    rc = 0
    if not understood:
        rc = 1
    sys.exit(rc)
