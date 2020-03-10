'''backend_iptables.py: iptables backend for ufw'''
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

import os
import re
import shutil
import stat
import sys
import time

from ufw.common import UFWError, UFWRule
from ufw.util import warn, debug, msg, cmd, cmd_pipe, _findpath
import ufw.backend


class UFWBackendIptables(ufw.backend.UFWBackend):
    '''Instance class for UFWBackend'''
    def __init__(self, dryrun, rootdir=None, datadir=None):
        '''UFWBackendIptables initialization'''
        self.comment_str = "# " + ufw.common.programName + "_comment #"
        self.rootdir = rootdir
        self.datadir = datadir

        files = {}
        config_dir = _findpath(ufw.common.config_dir, datadir)
        state_dir = _findpath(ufw.common.state_dir, datadir)

        files['rules'] = os.path.join(config_dir, 'ufw/user.rules')
        files['before_rules'] = os.path.join(config_dir, 'ufw/before.rules')
        files['after_rules'] = os.path.join(config_dir, 'ufw/after.rules')
        files['rules6'] = os.path.join(config_dir, 'ufw/user6.rules')
        files['before6_rules'] = os.path.join(config_dir, 'ufw/before6.rules')
        files['after6_rules'] = os.path.join(config_dir, 'ufw/after6.rules')
        files['init'] = os.path.join(state_dir, 'ufw-init')

        ufw.backend.UFWBackend.__init__(self, "iptables", dryrun, files,
                                        rootdir=rootdir, datadir=datadir)

        self.chains = {'before': [], 'user': [], 'after': [], 'misc': []}
        for ver in ['4', '6']:
            chain_prefix = "ufw"
            if ver == "6":
                if self.use_ipv6():
                    chain_prefix += ver
                elif ver == "6":
                    continue

            for loc in ['before', 'user', 'after']:
                for target in ['input', 'output', 'forward']:
                    chain = "%s-%s-logging-%s" % (chain_prefix, loc, target)
                    self.chains[loc].append(chain)
            self.chains['misc'].append(chain_prefix + "-logging-deny")
            self.chains['misc'].append(chain_prefix + "-logging-allow")

        # The default log rate limiting rule ('ufw[6]-user-limit chain should
        # be prepended before use)
        self.ufw_user_limit_log = ['-m', 'limit', \
                                   '--limit', '3/minute', '-j', 'LOG', \
                                   '--log-prefix']
        self.ufw_user_limit_log_text = "[UFW LIMIT BLOCK]"

    def get_default_application_policy(self):
        '''Get current policy'''
        rstr = _("New profiles:")
        if self.defaults['default_application_policy'] == "accept":
            rstr += " allow"
        elif self.defaults['default_application_policy'] == "drop":
            rstr += " deny"
        elif self.defaults['default_application_policy'] == "reject":
            rstr += " reject"
        else:
            rstr += " skip"

        return rstr

    def set_default_policy(self, policy, direction):
        '''Sets default policy of firewall'''
        if not self.dryrun:
            if policy != "allow" and policy != "deny" and policy != "reject":
                err_msg = _("Unsupported policy '%s'") % (policy)
                raise UFWError(err_msg)

            if direction != "incoming" and direction != "outgoing" and \
               direction != "routed":
                err_msg = _("Unsupported policy for direction '%s'") % \
                            (direction)
                raise UFWError(err_msg)

            chain = "INPUT"
            if direction == "outgoing":
                chain = "OUTPUT"
            elif direction == "routed":
                chain = "FORWARD"

            old_log_str = ''
            new_log_str = ''
            if policy == "allow":
                try:
                    self.set_default(self.files['defaults'], \
                                            "DEFAULT_%s_POLICY" % (chain), \
                                            "\"ACCEPT\"")
                except Exception:
                    raise
                old_log_str = 'UFW BLOCK'
                new_log_str = 'UFW ALLOW'
            elif policy == "reject":
                try:
                    self.set_default(self.files['defaults'], \
                                            "DEFAULT_%s_POLICY" % (chain), \
                                            "\"REJECT\"")
                except Exception:
                    raise
                old_log_str = 'UFW ALLOW'
                new_log_str = 'UFW BLOCK'
            else:
                try:
                    self.set_default(self.files['defaults'], \
                                            "DEFAULT_%s_POLICY" % (chain), \
                                            "\"DROP\"")
                except Exception:
                    raise
                old_log_str = 'UFW ALLOW'
                new_log_str = 'UFW BLOCK'

            # Switch logging message in catch-all rules
            pat = re.compile(r'' + old_log_str)
            for f in [self.files['after_rules'], self.files['after6_rules']]:
                try:
                    fns = ufw.util.open_files(f)
                except Exception:
                    raise
                fd = fns['tmp']

                for line in fns['orig']:
                    if pat.search(line):
                        ufw.util.write_to_file(fd, pat.sub(new_log_str, line))
                    else:
                        ufw.util.write_to_file(fd, line)

                try:
                    ufw.util.close_files(fns)
                except Exception:
                    raise

        rstr = _("Default %(direction)s policy changed to '%(policy)s'\n") % \
                 ({'direction': direction, 'policy': policy})
        rstr += _("(be sure to update your rules accordingly)")

        return rstr

    def get_running_raw(self, rules_type):
        '''Show current running status of firewall'''
        if self.dryrun:
            out = "> " + _("Checking raw iptables\n")
            out += "> " + _("Checking raw ip6tables\n")
            return out

        # Initialize the capabilities database
        self.initcaps()

        args = ['-n', '-v', '-x', '-L']
        items = []
        items6 = []

        if rules_type == "raw":
            args.append('-t')
            items = ['filter', 'nat', 'mangle', 'raw']
            items6 = ['filter', 'mangle', 'raw']
        elif rules_type == "builtins":
            for c in ['INPUT', 'FORWARD', 'OUTPUT']:
                items.append('filter:%s' % c)
                items6.append('filter:%s' % c)
            for c in ['PREROUTING', 'INPUT', 'FORWARD', 'OUTPUT', \
                      'POSTROUTING']:
                items.append('mangle:%s' % c)
                items6.append('mangle:%s' % c)
            for c in ['PREROUTING', 'OUTPUT']:
                items.append('raw:%s' % c)
                items6.append('raw:%s' % c)
            for c in ['PREROUTING', 'POSTROUTING', 'OUTPUT']:
                items.append('nat:%s' % c)
        elif rules_type == "before":
            for b in ['input', 'forward', 'output']:
                items.append('ufw-before-%s' % b)
                items6.append('ufw6-before-%s' % b)
        elif rules_type == "user":
            for b in ['input', 'forward', 'output']:
                items.append('ufw-user-%s' % b)
                items6.append('ufw6-user-%s' % b)
            if self.caps['limit']['4']:
                items.append('ufw-user-limit-accept')
                items.append('ufw-user-limit')
            if self.caps['limit']['6']:
                items6.append('ufw6-user-limit-accept')
                items6.append('ufw6-user-limit')
        elif rules_type == "after":
            for b in ['input', 'forward', 'output']:
                items.append('ufw-after-%s' % b)
                items6.append('ufw6-after-%s' % b)
        elif rules_type == "logging":
            for b in ['input', 'forward', 'output']:
                items.append('ufw-before-logging-%s' % b)
                items6.append('ufw6-before-logging-%s' % b)
                items.append('ufw-user-logging-%s' % b)
                items6.append('ufw6-user-logging-%s' % b)
                items.append('ufw-after-logging-%s' % b)
                items6.append('ufw6-after-logging-%s' % b)
            items.append('ufw-logging-allow')
            items.append('ufw-logging-deny')
            items6.append('ufw6-logging-allow')
            items6.append('ufw6-logging-deny')

        out = "IPV4 (%s):\n" % (rules_type)
        for i in items:
            if ':' in i:
                (t, c) = i.split(':')
                out += "(%s) " % (t)
                (rc, tmp) = cmd([self.iptables] + args + [c, '-t', t])
            else:
                (rc, tmp) = cmd([self.iptables] + args + [i])
            out += tmp
            if rules_type != "raw":
                out += "\n"
            if rc != 0:
                raise UFWError(out)

        if rules_type == "raw" or self.use_ipv6():
            out += "\n\nIPV6:\n"
            for i in items6:
                if ':' in i:
                    (t, c) = i.split(':')
                    out += "(%s) " % (t)
                    (rc, tmp) = cmd([self.iptables] + args + [c, '-t', t])
                else:
                    (rc, tmp) = cmd([self.ip6tables] + args + [i])
                out += tmp
                if rules_type != "raw":
                    out += "\n"
                if rc != 0:
                    raise UFWError(out)

        return out

    def get_status(self, verbose=False, show_count=False):
        '''Show ufw managed rules'''
        out = ""
        if self.dryrun:
            out = "> " + _("Checking iptables\n")
            if self.use_ipv6():
                out += "> " + _("Checking ip6tables\n")
            return out

        err_msg = _("problem running")
        for direction in ["input", "output", "forward"]:
            # Is the firewall loaded at all?
            (rc, out) = cmd([self.iptables, '-L', \
                            'ufw-user-%s' % (direction), '-n'])
            if rc == 1:
                return _("Status: inactive")
            elif rc != 0:
                raise UFWError(err_msg + " iptables: %s\n" % (out))

            if self.use_ipv6():
                (rc, out6) = cmd([self.ip6tables, '-L', \
                                 'ufw6-user-%s' % (direction), '-n'])
                if rc != 0:
                    raise UFWError(err_msg + " ip6tables")

        s = ""
        str_out = ""
        str_rte = ""
        rules = self.rules + self.rules6
        count = 1
        app_rules = {}
        for r in rules:
            tmp_str = ""
            location = {}
            tupl = ""
            show_proto = True
            if not verbose and (r.dapp != "" or r.sapp != ""):
                show_proto = False
                tupl = r.get_app_tuple()

                if tupl in app_rules:
                    debug("Skipping found tuple '%s'" % (tupl))
                    continue
                else:
                    app_rules[tupl] = True

            for loc in [ 'dst', 'src' ]:
                location[loc] = ""

                port = ""
                tmp = ""
                if loc == "dst":
                    tmp = r.dst
                    if not verbose and r.dapp != "":
                        port = r.dapp
                        if r.v6 and tmp == "::/0":
                            port += " (v6)"
                    else:
                        port = r.dport
                else:
                    tmp = r.src
                    if not verbose and r.sapp != "":
                        port = r.sapp
                        if r.v6 and tmp == "::/0":
                            port += " (v6)"
                    else:
                        port = r.sport

                if tmp != "0.0.0.0/0" and tmp != "::/0":
                    location[loc] = tmp

                if port != "any":
                    if location[loc] == "":
                        location[loc] = port
                    else:
                        location[loc] += " " + port

                    if show_proto and r.protocol != "any":
                        location[loc] += "/" + r.protocol

                    if verbose:
                        if loc == "dst" and r.dapp != "":
                            location[loc] += " (%s" % (r.dapp)
                            if r.v6 and tmp == "::/0":
                                location[loc] += " (v6)"
                            location[loc] += ")"
                        if loc == "src" and r.sapp != "":
                            location[loc] += " (%s" % (r.sapp)
                            if r.v6 and tmp == "::/0":
                                location[loc] += " (v6)"
                            location[loc] += ")"

                if port == "any":
                    if tmp == "0.0.0.0/0" or tmp == "::/0":
                        location[loc] = "Anywhere"

                        # Show the protocol if Anywhere to Anwhere, have
                        # protocol and source and dest ports are any
                        if show_proto and r.protocol != "any" and \
                           r.dst == r.src and r.dport == r.sport:
                            location[loc] += "/" + r.protocol

                        if tmp == "::/0":
                            location[loc] += " (v6)"
                    else:
                        # Show the protocol if have protocol, and source
                        # and dest ports are any
                        if show_proto and r.protocol != "any" and \
                           r.dport == r.sport:
                            location[loc] += "/" + r.protocol
                elif r.v6 and r.src == "::/0" and r.dst == "::/0" \
                   and ' (v6)' not in location[loc]:
                    # Add v6 if have port but no addresses so it doesn't look
                    # a duplicate of the v4 rule
                    location[loc] += " (v6)"

                # Reporting the interfaces is different in route rules and
                # non-route rules. With route rules, the reporting should be
                # relative to how packets flow through the firewall, with
                # other rules the reporting should be relative to the firewall
                # system as endpoint. As such, for route rules, report the
                # incoming interface under 'From' and the outgoing interface
                # under 'To', and for non-route rules, report the incoming
                # interface under 'To', and the outgoing interface under
                # 'From'.
                if r.forward:
                    if loc == 'src' and r.interface_in != "":
                        location[loc] += " on %s" % (r.interface_in)
                    if loc == 'dst' and r.interface_out != "":
                        location[loc] += " on %s" % (r.interface_out)
                else:
                    if loc == 'dst' and r.interface_in != "":
                        location[loc] += " on %s" % (r.interface_in)
                    if loc == 'src' and r.interface_out != "":
                        location[loc] += " on %s" % (r.interface_out)

            attribs = []
            attrib_str = ""
            if r.logtype or r.direction.lower() == "out":
                if r.logtype:
                    attribs.append(r.logtype.lower())
                # why is the direction added to attribs if shown in action?
                if show_count and r.direction == "out":
                    attribs.append(r.direction)
                if len(attribs) > 0:
                    attrib_str = " (%s)" % (', '.join(attribs))

            # now construct the rule output string
            if show_count:
                tmp_str += "[%2d] " % (count)

            dir_str = r.direction.upper()
            if r.forward:
                dir_str = "FWD"

            if r.direction == "in" and not r.forward and \
               not verbose and not show_count:
                dir_str = ""

            comment_str = ""
            if r.comment != "":
                comment_str = " # %s" % r.get_comment()
            tmp_str += "%-26s %-12s%-26s%s%s\n" % (location['dst'], \
                                                " ".join([r.action.upper(), \
                                                          dir_str]), \
                                                location['src'], attrib_str,
                                                comment_str)

            # Show the list in the order given if a numbered list, otherwise
            # split incoming and outgoing rules
            if show_count:
                s += tmp_str
            else:
                if r.forward:
                    str_rte += tmp_str
                elif r.direction == "out":
                    str_out += tmp_str
                else:
                    s += tmp_str
            count += 1

        if s != "" or str_out != "" or str_rte != "":
            full_str = "\n\n"
            if show_count:
                full_str += "     "
            str_to = _("To")
            str_from = _("From")
            str_action = _("Action")
            rules_header_fmt = "%-26s %-12s%s\n"

            rules_header = rules_header_fmt % (str_to, str_action, str_from)
            if show_count:
                rules_header += "     "
            rules_header += rules_header_fmt % \
                            ("-" * len(str_to), \
                             "-" * len(str_action), \
                             "-" * len(str_from))

            full_str += rules_header

            if s != "":
                full_str += s
            if s != "" and str_out != "":
                full_str += _("\n")
            if str_out != "":
                full_str += str_out
            if s != "" and str_rte != "":
                full_str += _("\n")
            if str_rte != "":
                full_str += str_rte

            s = full_str

        if verbose:
            (level, logging_str) = self.get_loglevel()
            policy_str = _("Default: %(in)s (incoming), " +
                           "%(out)s (outgoing), " +
                           "%(routed)s (routed)") \
                           % ({'in': self._get_default_policy(), \
                               'out': self._get_default_policy("output"), \
                               'routed': self._get_default_policy("forward", \
                                                                  True)})
            app_policy_str = self.get_default_application_policy()
            return _("Status: active\n%(log)s\n%(pol)s\n%(app)s%(status)s") % \
                     ({'log': logging_str, 'pol': policy_str, \
                       'app': app_policy_str, 'status': s})
        else:
            return _("Status: active%s") % (s)

    def stop_firewall(self):
        '''Stop the firewall'''
        if self.dryrun:
            msg("> " + _("running ufw-init"))
        else:
            args = []
            args.append(self.files['init'])
            if self.rootdir is not None and self.datadir is not None:
                args.append('--rootdir')
                args.append(self.rootdir)
                args.append('--datadir')
                args.append(self.datadir)
            args.append('force-stop')
            (rc, out) = cmd(args)
            if rc != 0:
                err_msg = _("problem running ufw-init\n%s" % out)
                raise UFWError(err_msg)

    def start_firewall(self):
        '''Start the firewall'''
        if self.dryrun:
            msg("> " + _("running ufw-init"))
        else:
            args = []
            args.append(self.files['init'])
            if self.rootdir is not None and self.datadir is not None:
                args.append('--rootdir')
                args.append(self.rootdir)
                args.append('--datadir')
                args.append(self.datadir)
            args.append('start')
            (rc, out) = cmd(args)
            if rc != 0:
                err_msg = _("problem running ufw-init\n%s" % out)
                raise UFWError(err_msg)

            if 'loglevel' not in self.defaults or \
               self.defaults['loglevel'] not in list(self.loglevels.keys()):
                # Add the loglevel if not valid
                try:
                    self.set_loglevel("low")
                except Exception:
                    err_msg = _("Could not set LOGLEVEL")
                    raise UFWError(err_msg)
            else:
                try:
                    self.update_logging(self.defaults['loglevel'])
                except Exception:
                    err_msg = _("Could not load logging rules")
                    raise UFWError(err_msg)

    def _need_reload(self, v6):
        '''Check if all chains exist'''
        if self.dryrun:
            return False

        # Initialize the capabilities database
        self.initcaps()

        prefix = "ufw"
        exe = self.iptables
        if v6:
            prefix = "ufw6"
            exe = self.ip6tables

        for chain in [ 'input', 'output', 'forward', 'limit', 'limit-accept' ]:
            if chain == "limit" or chain == "limit-accept":
                if v6 and not self.caps['limit']['6']:
                    continue
                elif not v6 and not self.caps['limit']['4']:
                    continue

            (rc, out) = cmd([exe, '-n', '-L', prefix + "-user-" + chain])
            if rc != 0:
                debug("_need_reload: forcing reload")
                return True

        return False

    def _reload_user_rules(self):
        '''Reload firewall rules file'''
        err_msg = _("problem running")
        if self.dryrun:
            msg("> | iptables-restore")
            if self.use_ipv6():
                msg("> | ip6tables-restore")
        elif self.is_enabled():
            # first flush the user logging chains
            try:
                for c in self.chains['user']:
                    self._chain_cmd(c, ['-F', c])
                    self._chain_cmd(c, ['-Z', c])
            except Exception: # pragma: no coverage
                raise UFWError(err_msg)

            # then restore the system rules
            (rc, out) = cmd_pipe(['cat', self.files['rules']], \
                                 [self.iptables_restore, '-n'])
            if rc != 0:
                raise UFWError(err_msg + " iptables")

            if self.use_ipv6():
                (rc, out) = cmd_pipe(['cat', self.files['rules6']], \
                                     [self.ip6tables_restore, '-n'])
                if rc != 0:
                    raise UFWError(err_msg + " ip6tables")

    def _get_rules_from_formatted(self, frule, prefix, suffix):
        '''Return list of iptables rules appropriate for sending'''
        snippets = []

        # adjust reject and protocol 'all'
        pat_proto = re.compile(r'-p all ')
        pat_port = re.compile(r'port ')
        pat_reject = re.compile(r'-j (REJECT(_log(-all)?)?)')
        if pat_proto.search(frule):
            if pat_port.search(frule):
                if pat_reject.search(frule):
                    snippets.append(pat_proto.sub('-p tcp ', \
                        pat_reject.sub(r'-j \1 --reject-with tcp-reset', \
                        frule)))
                else:
                    snippets.append(pat_proto.sub('-p tcp ', frule))
                snippets.append(pat_proto.sub('-p udp ', frule))
            else:
                snippets.append(pat_proto.sub('', frule))
        else:
            snippets.append(frule)

        # adjust for logging rules
        pat_log = re.compile(r'(.*)-j ([A-Z]+)_log(-all)?(.*)')
        pat_logall = re.compile(r'-j [A-Z]+_log-all')
        pat_chain = re.compile(r'(-A|-D) ([a-zA-Z0-9\-]+)')
        limit_args = '-m limit --limit 3/min --limit-burst 10'
        for i, s in enumerate(snippets):
            if pat_log.search(s):
                policy = pat_log.sub(r'\2', s).strip()
                if policy.lower() == "accept":
                    policy = "ALLOW"
                elif policy.lower() == "limit":
                    policy = "LIMIT"
                else:
                    policy = "BLOCK"

                lstr = '%s -j LOG --log-prefix "[UFW %s] "' % (limit_args, \
                       policy)
                if not pat_logall.search(s):
                    lstr = '-m conntrack --ctstate NEW ' + lstr
                snippets[i] = pat_log.sub(r'\1-j \2\4', s)
                snippets.insert(i, pat_log.sub(r'\1-j ' + prefix + \
                                               '-user-logging-' + suffix, s))
                snippets.insert(i, pat_chain.sub(r'\1 ' + prefix + \
                                                 '-user-logging-' + suffix,
                                                 pat_log.sub(r'\1-j RETURN', \
                                                 s)))
                snippets.insert(i, pat_chain.sub(r'\1 ' + prefix + \
                                                 '-user-logging-' + suffix,
                                                 pat_log.sub(r'\1' + lstr, s)))

        # adjust for limit
        pat_limit = re.compile(r' -j LIMIT')
        for i, s in enumerate(snippets):
            if pat_limit.search(s):
                tmp1 = pat_limit.sub(' -m conntrack --ctstate NEW -m recent --set', \
                                     s)
                tmp2 = pat_limit.sub(' -m conntrack --ctstate NEW -m recent' + \
                                     ' --update --seconds 30 --hitcount 6' + \
                                     ' -j ' + prefix + '-user-limit', s)
                tmp3 = pat_limit.sub(' -j ' + prefix + '-user-limit-accept', s)
                snippets[i] = tmp3
                snippets.insert(i, tmp2)
                snippets.insert(i, tmp1)

        return snippets

    def _get_lists_from_formatted(self, frule, prefix, suffix):
        '''Return list of iptables rules appropriate for sending as arguments
           to cmd()
        '''
        snippets = []
        str_snippets = self._get_rules_from_formatted(frule, prefix, suffix)

        # split the string such that the log prefix can contain spaces
        pat = re.compile(r'(.*) --log-prefix (".* ")(.*)')
        for i, s in enumerate(str_snippets):
            snippets.append(pat.sub(r'\1', s).split())
            if pat.match(s):
                snippets[i].append("--log-prefix")
                snippets[i].append(pat.sub(r'\2', s).replace('"', ''))
                snippets[i] += pat.sub(r'\3', s).split()

        return snippets

    def _read_rules(self):
        '''Read in rules that were added by ufw'''
        rfns = [self.files['rules']]
        if self.use_ipv6():
            rfns.append(self.files['rules6'])

        for f in rfns:
            try:
                orig = ufw.util.open_file_read(f)
            except Exception:
                err_msg = _("Couldn't open '%s' for reading") % (f)
                raise UFWError(err_msg)

            pat_tuple = re.compile(r'^### tuple ###\s*')
            pat_iface_in = re.compile(r'in_\w+')
            pat_iface_out = re.compile(r'out_\w+')
            for orig_line in orig:
                line = orig_line

                comment = ""
                # comment= should always be last, so just strip it out
                if ' comment=' in orig_line:
                    line, hex = orig_line.split(r' comment=')
                    comment = hex.strip()

                if pat_tuple.match(line):
                    tupl = pat_tuple.sub('', line)
                    tmp = re.split(r'\s+', tupl.strip())
                    if len(tmp) < 6 or len(tmp) > 9:
                        wmsg = _("Skipping malformed tuple (bad length): %s") \
                                 % (tupl)
                        warn(wmsg)
                        continue
                    else:
                        # set direction to "in" to support upgrades
                        # from old format, which only had 6 or 8 fields.
                        dtype = "in"
                        interface_in = ""
                        interface_out = ""
                        if len(tmp) == 7 or len(tmp) == 9:
                            wmsg = _("Skipping malformed tuple (iface): %s") \
                                     % (tupl)
                            dtype = tmp[-1].split('_')[0]
                            if '_' in tmp[-1]:
                                if '!' in tmp[-1] and \
                                   pat_iface_in.search(tmp[-1]) and \
                                   pat_iface_out.search(tmp[-1]):
                                    # in_eth0!out_eth1
                                    interface_in = \
                                        tmp[-1].split('!')[0].partition('_')[2]
                                    interface_out = \
                                        tmp[-1].split('!')[1].partition('_')[2]
                                elif tmp[-1].startswith("in_"):
                                    # in_eth0
                                    interface_in = tmp[-1].partition('_')[2]
                                elif tmp[-1].startswith("out_"):
                                    # out_eth0
                                    interface_out = tmp[-1].partition('_')[2]
                                else:
                                    warn(wmsg)
                                    continue
                        try:
                            action = tmp[0]
                            forward = False
                            # route rules use 'route:<action> ...'
                            if ':' in action:
                                forward = True
                                action = action.split(':')[1]
                            if len(tmp) < 8:
                                rule = UFWRule(action, tmp[1], tmp[2], tmp[3],
                                               tmp[4], tmp[5], dtype, forward,
                                               comment)
                            else:
                                rule = UFWRule(action, tmp[1], tmp[2], tmp[3],
                                               tmp[4], tmp[5], dtype, forward,
                                               comment)
                                # Removed leading [sd]app_ and unescape spaces
                                pat_space = re.compile('%20')
                                if tmp[6] != "-":
                                    rule.dapp = pat_space.sub(' ', tmp[6])
                                if tmp[7] != "-":
                                    rule.sapp = pat_space.sub(' ', tmp[7])
                            if interface_in != "":
                                rule.set_interface("in", interface_in)
                            if interface_out != "":
                                rule.set_interface("out", interface_out)

                        except UFWError:
                            warn_msg = _("Skipping malformed tuple: %s") % \
                                        (tupl)
                            warn(warn_msg)
                            continue
                        if f == self.files['rules6']:
                            rule.set_v6(True)
                            self.rules6.append(rule)
                        else:
                            rule.set_v6(False)
                            self.rules.append(rule)

            orig.close()

    def _write_rules(self, v6=False):
        '''Write out new rules to file to user chain file'''
        rules_file = self.files['rules']
        if v6:
            rules_file = self.files['rules6']

        # Perform this here so we can present a nice error to the user rather
        # than a traceback
        if not os.access(rules_file, os.W_OK):
            err_msg = _("'%s' is not writable" % (rules_file))
            raise UFWError(err_msg)

        try:
            fns = ufw.util.open_files(rules_file)
        except Exception:
            raise

        # Initialize the capabilities database
        self.initcaps()

        chain_prefix = "ufw"
        rules = self.rules
        if v6:
            chain_prefix = "ufw6"
            rules = self.rules6

        if self.dryrun:
            fd = sys.stdout.fileno()
        else:
            fd = fns['tmp']

        # Write header
        ufw.util.write_to_file(fd, "*filter\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + "-user-input - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-user-output - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-user-forward - [0:0]\n")

        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-before-logging-input - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-before-logging-output - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-before-logging-forward - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-user-logging-input - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-user-logging-output - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-user-logging-forward - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-after-logging-input - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-after-logging-output - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-after-logging-forward - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-logging-deny - [0:0]\n")
        ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                         "-logging-allow - [0:0]\n")

        # Rate limiting is runtime supported
        if (chain_prefix == "ufw" and self.caps['limit']['4']) or \
           (chain_prefix == "ufw6" and self.caps['limit']['6']):
            ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                             "-user-limit - [0:0]\n")
            ufw.util.write_to_file(fd, ":" + chain_prefix + \
                                             "-user-limit-accept - [0:0]\n")

        ufw.util.write_to_file(fd, "### RULES ###\n")

        # Write rules
        for r in rules:
            action = r.action
            # route rules use 'route:<action> ...'
            if r.forward:
                action = "route:" + r.action
            if r.logtype != "":
                action += "_" + r.logtype

            ifaces = ""
            if r.interface_in == "" and r.interface_out == "":
                ifaces = r.direction
            elif r.interface_in != "" and r.interface_out != "":
                ifaces = "in_%s!out_%s" % (r.interface_in, r.interface_out)
            else:
                if r.interface_in != "":
                    ifaces += "%s_%s" % (r.direction, r.interface_in)
                else:
                    ifaces += "%s_%s" % (r.direction, r.interface_out)

            if r.dapp == "" and r.sapp == "":
                tstr = "\n### tuple ### %s %s %s %s %s %s %s" % \
                     (action, r.protocol, r.dport, r.dst, r.sport, r.src,
                      ifaces)
                if r.comment != '':
                    tstr += " comment=%s" % r.comment
                ufw.util.write_to_file(fd, tstr + "\n")
            else:
                pat_space = re.compile(' ')
                dapp = "-"
                if r.dapp:
                    dapp = pat_space.sub('%20', r.dapp)
                sapp = "-"
                if r.sapp:
                    sapp = pat_space.sub('%20', r.sapp)
                tstr = "\n### tuple ### %s %s %s %s %s %s %s %s %s" % \
                       (action, r.protocol, r.dport, r.dst, r.sport, r.src, \
                        dapp, sapp, ifaces)
                if r.comment != '':
                    tstr += " comment=%s" % r.comment
                ufw.util.write_to_file(fd, tstr + "\n")

            chain_suffix = "input"
            if r.forward:
                chain_suffix = "forward"
            elif r.direction == "out":
                chain_suffix = "output"
            chain = "%s-user-%s" % (chain_prefix, chain_suffix)
            rule_str = "-A %s %s\n" % (chain, r.format_rule())

            for s in self._get_rules_from_formatted(rule_str, chain_prefix, \
                                                    chain_suffix):
                ufw.util.write_to_file(fd, s)

        # Write footer
        ufw.util.write_to_file(fd, "\n### END RULES ###\n")

        # Add logging rules, skipping any delete ('-D') rules
        ufw.util.write_to_file(fd, "\n### LOGGING ###\n")
        try:
            lrules_t = self._get_logging_rules(self.defaults['loglevel'])
        except Exception:
            raise
        for c, r, q in lrules_t:
            if len(r) > 0 and r[0] == '-D':
                continue
            if c.startswith(chain_prefix + "-"):
                ufw.util.write_to_file(fd,
                    " ".join(r).replace('[', '"[').replace('] ', '] "') + \
                    "\n")
        ufw.util.write_to_file(fd, "### END LOGGING ###\n")

        # Rate limiting is runtime supported
        if (chain_prefix == "ufw" and self.caps['limit']['4']) or \
           (chain_prefix == "ufw6" and self.caps['limit']['6']):
            ufw.util.write_to_file(fd, "\n### RATE LIMITING ###\n")
            if self.defaults['loglevel'] != "off":
                ufw.util.write_to_file(fd, "-A " + \
                         chain_prefix + "-user-limit " + \
                         " ".join(self.ufw_user_limit_log) + \
                         " \"" + self.ufw_user_limit_log_text + " \"\n")
            ufw.util.write_to_file(fd, "-A " + chain_prefix + \
                         "-user-limit -j REJECT\n")
            ufw.util.write_to_file(fd, "-A " + chain_prefix + \
                         "-user-limit-accept -j ACCEPT\n")
            ufw.util.write_to_file(fd, "### END RATE LIMITING ###\n")

        ufw.util.write_to_file(fd, "COMMIT\n")

        try:
            if self.dryrun:
                ufw.util.close_files(fns, False)
            else:
                ufw.util.close_files(fns)
        except Exception:
            raise

    def set_rule(self, rule, allow_reload=True):
        '''Updates firewall with rule by:
        * appending the rule to the chain if new rule and firewall enabled
        * deleting the rule from the chain if found and firewall enabled
        * inserting the rule if possible and firewall enabled
        * updating user rules file
        * reloading the user rules file if rule is modified
        '''

        # Initialize the capabilities database
        self.initcaps()

        rstr = ""

        if rule.v6:
            if not self.use_ipv6():
                err_msg = _("Adding IPv6 rule failed: IPv6 not enabled")
                raise UFWError(err_msg)
            if rule.action == 'limit' and not self.caps['limit']['6']:
                # Rate limiting is runtime supported
                return _("Skipping unsupported IPv6 '%s' rule") % (rule.action)
        else:
            if rule.action == 'limit' and not self.caps['limit']['4']:
                # Rate limiting is runtime supported
                return _("Skipping unsupported IPv4 '%s' rule") % (rule.action)

        if rule.multi and rule.protocol != "udp" and rule.protocol != "tcp":
            err_msg = _("Must specify 'tcp' or 'udp' with multiple ports")
            raise UFWError(err_msg)

        newrules = []
        found = False
        modified = False

        rules = self.rules
        position = rule.position
        if rule.v6:
            if self.iptables_version < "1.4" and (rule.dapp != "" or \
                                                  rule.sapp != ""):
                return _("Skipping IPv6 application rule. Need at least iptables 1.4")
            rules = self.rules6

        # bail if we have a bad position
        if position < 0 or position > len(rules):
            err_msg = _("Invalid position '%d'") % (position)
            raise UFWError(err_msg)

        if position > 0 and rule.remove:
            err_msg = _("Cannot specify insert and delete")
            raise UFWError(err_msg)
        if position > len(rules):
            err_msg = _("Cannot insert rule at position '%d'") % position
            raise UFWError(err_msg)

        # First construct the new rules list
        try:
            rule.normalize()
        except Exception:
            raise

        count = 1
        inserted = False
        matches = 0
        last = ('', '', '', '')
        for r in rules:
            try:
                r.normalize()
            except Exception:
                raise

            current = (r.dst, r.src, r.dapp, r.sapp)
            if count == position:
                # insert the rule if:
                # 1. the last rule was not an application rule
                # 2. the current rule is not an application rule
                # 3. the last application rule is different than the current
                #    while the new rule is different than the current one
                if (last[2] == '' and last[3] == '' and count > 1) or \
                   (current[2] == '' and current[3] == '') or \
                   last != current:
                    inserted = True
                    newrules.append(rule.dup_rule())
                    last = ('', '', '', '')
                else:
                    position += 1
            last = current
            count += 1

            ret = UFWRule.match(r, rule)
            if ret < 1:
                matches += 1

            if ret == 0 and not found and not inserted:
                # If find the rule, add it if it's not to be removed, otherwise
                # skip it.
                found = True
                if not rule.remove:
                    newrules.append(rule.dup_rule())
            elif ret == -2 and rule.remove and rule.comment == '':
                # Allow removing a rule if the comment is empty
                found = True
            elif ret < 0 and not rule.remove and not inserted:
                # If only the action is different, replace the rule if it's not
                # to be removed.
                found = True
                modified = True
                newrules.append(rule.dup_rule())
            else:
                newrules.append(r)

        if inserted:
            if matches > 0:
                rstr = _("Skipping inserting existing rule")
                if rule.v6:
                    rstr += " (v6)"
                return rstr
        else:
            # Add rule to the end if it was not already added.
            if not found and not rule.remove:
                newrules.append(rule.dup_rule())

            # Don't process non-existing or unchanged pre-exisiting rules
            if not found and rule.remove and not self.dryrun:
                rstr = _("Could not delete non-existent rule")
                if rule.v6:
                    rstr += " (v6)"
                return rstr
            elif found and not rule.remove and not modified:
                rstr = _("Skipping adding existing rule")
                if rule.v6:
                    rstr += " (v6)"
                return rstr

        if rule.v6:
            self.rules6 = newrules
        else:
            self.rules = newrules

        # Update the user rules file
        try:
            self._write_rules(rule.v6)
        except UFWError:
            raise
        except Exception:
            err_msg = _("Couldn't update rules file")
            UFWError(err_msg)

        # We wrote out the rules, so set reasonable string. We will change
        # this below when operating on the live firewall.
        rstr = _("Rules updated")
        if rule.v6:
            rstr = _("Rules updated (v6)")

        # Operate on the chains
        if self.is_enabled() and not self.dryrun:
            flag = ""
            if modified or self._need_reload(rule.v6) or inserted:
                rstr = ""
                if inserted:
                    rstr += _("Rule inserted")
                else:
                    rstr += _("Rule updated")
                if rule.v6:
                    rstr += " (v6)"
                if allow_reload:
                    # Reload the chain
                    try:
                        self._reload_user_rules()
                    except Exception:
                        raise
                else:
                    rstr += _(" (skipped reloading firewall)")
            elif found and rule.remove:
                flag = '-D'
                rstr = _("Rule deleted")
            elif not found and not modified and not rule.remove:
                flag = '-A'
                rstr = _("Rule added")

            if flag != "":
                exe = self.iptables
                chain_prefix = "ufw"
                if rule.v6:
                    exe = self.ip6tables
                    chain_prefix = "ufw6"
                    rstr += " (v6)"
                chain_suffix = "input"
                if rule.forward:
                    chain_suffix = "forward"
                elif rule.direction == "out":
                    chain_suffix = "output"
                chain = "%s-user-%s" % (chain_prefix, chain_suffix)

                # Is the firewall running?
                err_msg = _("Could not update running firewall")
                (rc, out) = cmd([exe, '-L', chain, '-n'])
                if rc != 0:
                    raise UFWError(err_msg)

                rule_str = "%s %s %s" % (flag, chain, rule.format_rule())
                pat_log = re.compile(r'(-A +)(ufw6?-user-[a-z\-]+)(.*)')
                for s in self._get_lists_from_formatted(rule_str, \
                                                        chain_prefix, \
                                                        chain_suffix):
                    (rc, out) = cmd([exe] + s)
                    if rc != 0:
                        msg(out, sys.stderr)
                        UFWError(err_msg)

                    # delete any lingering RETURN rules (needed for upgrades)
                    if flag == "-A" and pat_log.search(" ".join(s)):
                        c = pat_log.sub(r'\2', " ".join(s))
                        (rc, out) = cmd([exe, '-D', c, '-j', 'RETURN'])
                        if rc != 0:
                            debug("FAILOK: -D %s -j RETURN" % (c))

        return rstr

    def get_app_rules_from_system(self, template, v6):
        '''Return a list of UFWRules from the system based on template rule'''
        rules = []
        app_rules = []

        if v6:
            rules = self.rules6
        else:
            rules = self.rules

        norm = template.dup_rule()
        norm.set_v6(v6)
        norm.normalize()
        tupl = norm.get_app_tuple()

        for r in rules:
            tmp = r.dup_rule()
            tmp.normalize()
            tmp_tuple = tmp.get_app_tuple()
            if tmp_tuple == tupl:
                app_rules.append(tmp)

        return app_rules

    def _chain_cmd(self, chain, args, fail_ok=False):
        '''Perform command on chain'''
        exe = self.iptables
        if chain.startswith("ufw6"):
            exe = self.ip6tables
        (rc, out) = cmd([exe] + args)
        if rc != 0:
            err_msg = _("Could not perform '%s'" % (args))
            if fail_ok:
                debug("FAILOK: " + err_msg)
            else:
                raise UFWError(err_msg)

    def update_logging(self, level):
        '''Update loglevel of running firewall'''
        if self.dryrun:
            return

        # Initialize the capabilities database
        self.initcaps()

        rules_t = []
        try:
            rules_t = self._get_logging_rules(level)
        except Exception:
            raise

        # Update the user rules file
        try:
            self._write_rules(v6=False)
            self._write_rules(v6=True)
        except UFWError:
            raise
        except Exception:
            err_msg = _("Couldn't update rules file for logging")
            UFWError(err_msg)

        # Don't update the running firewall if not enabled
        if not self.is_enabled():
            return

        # make sure all the chains are here, it's redundant but helps make
        # sure the chains are in a consistent state
        err_msg = _("Could not update running firewall")
        for c in self.chains['before'] + self.chains['user'] + \
           self.chains['after'] + self.chains['misc']:
            try:
                self._chain_cmd(c, ['-L', c, '-n'])
            except Exception:
                raise UFWError(err_msg)

        # Flush all the logging chains except 'user'
        try:
            for c in self.chains['before'] + self.chains['after'] + \
               self.chains['misc']:
                self._chain_cmd(c, ['-F', c])
                self._chain_cmd(c, ['-Z', c])
        except Exception:
            raise UFWError(err_msg)

        # Add logging rules to running firewall
        for c, r, q in rules_t:
            fail_ok = False
            if len(r) > 0 and r[0] == '-D':
                fail_ok = True
            try:
                if q == 'delete_first' and len(r) > 1:
                    self._chain_cmd(c, ['-D'] + r[1:], fail_ok=True)
                self._chain_cmd(c, r, fail_ok)
            except Exception:
                raise UFWError(err_msg)

        # Rate limiting is runtime supported
        # Always delete these and re-add them so that we don't have extras
        for chain in ['ufw-user-limit', 'ufw6-user-limit']:
            if (self.caps['limit']['4'] and chain == 'ufw-user-limit') or \
               (self.caps['limit']['6'] and chain == 'ufw6-user-limit'):
                self._chain_cmd(chain, ['-D', chain] + \
                                self.ufw_user_limit_log + \
                                [self.ufw_user_limit_log_text + " "], \
                                fail_ok=True)
                if self.defaults["loglevel"] != "off":
                    self._chain_cmd(chain, ['-I', chain] + \
                                    self.ufw_user_limit_log + \
                                    [self.ufw_user_limit_log_text + " "], \
                                    fail_ok=True)

    def _get_logging_rules(self, level):
        '''Get rules for specified logging level'''
        rules_t = []

        if level not in list(self.loglevels.keys()):
            err_msg = _("Invalid log level '%s'") % (level)
            raise UFWError(err_msg)

        if level == "off":
            # when off, insert a RETURN rule at the top of user rules, thus
            # preserving the rules
            for c in self.chains['user']:
                rules_t.append([c, ['-I', c, '-j', 'RETURN'], 'delete_first'])
            return rules_t
        else:
            # when on, remove the RETURN rule at the top of user rules, thus
            # honoring the log rules
            for c in self.chains['user']:
                rules_t.append([c, ['-D', c, '-j', 'RETURN'], ''])

        limit_args = ['-m', 'limit', '--limit', '3/min', '--limit-burst', '10']

        # log levels of low and higher log blocked packets
        if self.loglevels[level] >= self.loglevels["low"]:
            # Setup the policy violation logging chains
            largs = []
            # log levels under high use limit
            if self.loglevels[level] < self.loglevels["high"]:
                largs = limit_args
            for c in self.chains['after']:
                for t in ['input', 'output', 'forward']:
                    if c.endswith(t):
                        if self._get_default_policy(t) == "reject" or \
                           self._get_default_policy(t) == "deny":
                            prefix = "[UFW BLOCK] "
                            rules_t.append([c, ['-A', c, '-j', 'LOG', \
                                                '--log-prefix', prefix] +
                                                largs, ''])
                        elif self.loglevels[level] >= self.loglevels["medium"]:
                            prefix = "[UFW ALLOW] "
                            rules_t.append([c, ['-A', c, '-j', 'LOG', \
                                                '--log-prefix', prefix] + \
                                                largs, ''])

            # Setup the miscellaneous logging chains
            largs = []
            # log levels under high use limit
            if self.loglevels[level] < self.loglevels["high"]:
                largs = limit_args

            for c in self.chains['misc']:
                if c.endswith("allow"):
                    prefix = "[UFW ALLOW] "
                elif c.endswith("deny"):
                    prefix = "[UFW BLOCK] "
                    if self.loglevels[level] < self.loglevels["medium"]:
                        # only log INVALID in medium and higher
                        rules_t.append([c, ['-I', c, '-m', 'conntrack', \
                                            '--ctstate', 'INVALID', \
                                            '-j', 'RETURN'] + largs, ''])
                    else:
                        rules_t.append([c, ['-A', c, '-m', 'conntrack', \
                                            '--ctstate', 'INVALID', \
                                            '-j', 'LOG', \
                                            '--log-prefix', \
                                            "[UFW AUDIT INVALID] "] + \
                                        largs, ''])
                rules_t.append([c, ['-A', c, '-j', 'LOG', \
                                    '--log-prefix', prefix] + largs, ''])

        # Setup the audit logging chains
        if self.loglevels[level] >= self.loglevels["medium"]:
            # loglevel full logs all packets without limit
            largs = []

            # loglevel high logs all packets with limit
            if self.loglevels[level] < self.loglevels["full"]:
                largs = limit_args

            # loglevel medium logs all new packets with limit
            if self.loglevels[level] < self.loglevels["high"]:
                largs = ['-m', 'conntrack', '--ctstate', 'NEW'] + limit_args

            prefix = "[UFW AUDIT] "
            for c in self.chains['before']:
                rules_t.append([c, ['-I', c, '-j', 'LOG', \
                                    '--log-prefix', prefix] + largs, ''])

        return rules_t

    def reset(self):
        '''Reset the firewall'''
        res = ""
        share_dir = _findpath(ufw.common.share_dir, self.rootdir)
        # First make sure we have all the original files
        allfiles = []
        for i in self.files:
            if not self.files[i].endswith('.rules'):
                continue
            allfiles.append(self.files[i])
            fn = os.path.join(share_dir, "iptables", \
                              os.path.basename(self.files[i]))
            if not os.path.isfile(fn):
                err_msg = _("Could not find '%s'. Aborting") % (fn)
                raise UFWError(err_msg)

        ext = time.strftime("%Y%m%d_%H%M%S")

        # This implementation will intentionally traceback if someone tries to
        # do something to take advantage of the race conditions here.

        # Don't do anything if the files already exist
        for i in allfiles:
            fn = "%s.%s" % (i, ext)
            if os.path.exists(fn):
                err_msg = _("'%s' already exists. Aborting") % (fn)
                raise UFWError(err_msg)

        # Move the old to the new
        for i in allfiles:
            fn = "%s.%s" % (i, ext)
            res += _("Backing up '%(old)s' to '%(new)s'\n") % (\
                     {'old': os.path.basename(i), 'new': fn})
            os.rename(i, fn)

        # Copy files into place
        for i in allfiles:
            old = "%s.%s" % (i, ext)
            shutil.copy(os.path.join(share_dir, "iptables", \
                                     os.path.basename(i)), \
                        os.path.dirname(i))
            shutil.copymode(old, i)

            try:
                statinfo = os.stat(i)
                mode = statinfo[stat.ST_MODE]
            except Exception:
                warn_msg = _("Couldn't stat '%s'") % (i)
                warn(warn_msg)
                continue

            if mode & stat.S_IWOTH:
                res += _("WARN: '%s' is world writable") % (i)
            elif mode & stat.S_IROTH:
                res += _("WARN: '%s' is world readable") % (i)

        return res
