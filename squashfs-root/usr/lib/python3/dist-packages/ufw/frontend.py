'''frontend.py: frontend interface for ufw'''
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
import sys
import warnings

from ufw.common import UFWError
import ufw.util
from ufw.util import error, warn, msg
from ufw.backend_iptables import UFWBackendIptables
import ufw.parser


def parse_command(argv):
    '''Parse command. Returns tuple for action, rule, ip_version and dryrun.'''
    p = ufw.parser.UFWParser()

    # Basic commands
    for i in ['enable', 'disable', 'help', '--help', 'version', '--version', \
              'reload', 'reset' ]:
        p.register_command(ufw.parser.UFWCommandBasic(i))

    # Application commands
    for i in ['list', 'info', 'default', 'update']:
        p.register_command(ufw.parser.UFWCommandApp(i))

    # Logging commands
    for i in ['on', 'off', 'low', 'medium', 'high', 'full']:
        p.register_command(ufw.parser.UFWCommandLogging(i))

    # Default commands
    for i in ['allow', 'deny', 'reject']:
        p.register_command(ufw.parser.UFWCommandDefault(i))

    # Status commands ('status', 'status verbose', 'status numbered')
    for i in [None, 'verbose', 'numbered']:
        p.register_command(ufw.parser.UFWCommandStatus(i))

    # Show commands
    for i in ['raw', 'before-rules', 'user-rules', 'after-rules', \
              'logging-rules', 'builtins', 'listening', 'added']:
        p.register_command(ufw.parser.UFWCommandShow(i))

    # Rule commands
    rule_commands = ['allow', 'limit', 'deny', 'reject', 'insert', 'delete',
                     'prepend']
    for i in rule_commands:
        p.register_command(ufw.parser.UFWCommandRule(i))
        p.register_command(ufw.parser.UFWCommandRouteRule(i))

    # Don't require the user to have to specify 'rule' as the command. Instead
    # insert 'rule' into the arguments if this is a rule command.
    if len(argv) > 2:
        idx = 1
        if argv[idx].lower() == "--dry-run":
            idx = 2
        if argv[idx].lower() != "default" and \
           argv[idx].lower() != "route" and \
           argv[idx].lower() in rule_commands:
            argv.insert(idx, 'rule')

    if len(argv) < 2 or ('--dry-run' in argv and len(argv) < 3):
        error("not enough args") # pragma: no cover

    try:
        pr = p.parse_command(argv[1:])
    except UFWError as e:
        error("%s" % (e.value)) # pragma: no cover
    except Exception:
        error("Invalid syntax", do_exit=False)
        raise

    return pr


def get_command_help():
    '''Print help message'''
    help_msg = _('''
Usage: %(progname)s %(command)s

%(commands)s:
 %(enable)-31s enables the firewall
 %(disable)-31s disables the firewall
 %(default)-31s set default policy
 %(logging)-31s set logging to %(level)s
 %(allow)-31s add allow %(rule)s
 %(deny)-31s add deny %(rule)s
 %(reject)-31s add reject %(rule)s
 %(limit)-31s add limit %(rule)s
 %(delete)-31s delete %(urule)s
 %(insert)-31s insert %(urule)s at %(number)s
 %(route)-31s add route %(urule)s
 %(route-delete)-31s delete route %(urule)s
 %(route-insert)-31s insert route %(urule)s at %(number)s
 %(reload)-31s reload firewall
 %(reset)-31s reset firewall
 %(status)-31s show firewall status
 %(statusnum)-31s show firewall status as numbered list of %(rules)s
 %(statusverbose)-31s show verbose firewall status
 %(show)-31s show firewall report
 %(version)-31s display version information

%(appcommands)s:
 %(applist)-31s list application profiles
 %(appinfo)-31s show information on %(profile)s
 %(appupdate)-31s update %(profile)s
 %(appdefault)-31s set default application policy
''' % ({'progname': ufw.common.programName, \
         'command': "COMMAND", \
         'commands': "Commands", \
         'enable': "enable", \
         'disable': "disable", \
         'default': "default ARG", \
         'logging': "logging LEVEL", \
         'level': "LEVEL", \
         'allow': "allow ARGS", \
         'rule': "rule", \
         'deny': "deny ARGS", \
         'reject': "reject ARGS", \
         'limit': "limit ARGS", \
         'delete': "delete RULE|NUM", \
         'urule': "RULE", \
         'insert': "insert NUM RULE", \
         'prepend': "prepend RULE", \
         'route': "route RULE", \
         'route-delete': "route delete RULE|NUM", \
         'route-insert': "route insert NUM RULE", \
         'number': "NUM", \
         'reload': "reload", \
         'reset': "reset", \
         'status': "status", \
         'statusnum': "status numbered", \
         'rules': "RULES", \
         'statusverbose': "status verbose", \
         'show': "show ARG", \
         'version': "version", \
         'appcommands': "Application profile commands", \
         'applist': "app list", \
         'appinfo': "app info PROFILE", \
         'profile': "PROFILE", \
         'appupdate': "app update PROFILE", \
         'appdefault': "app default ARG"}))

    return (help_msg)


class UFWFrontend:
    '''UI'''
    def __init__(self, dryrun, backend_type="iptables",
                 rootdir=None, datadir=None):
        if backend_type == "iptables":
            try:
                self.backend = UFWBackendIptables(dryrun, rootdir=rootdir,
                                                  datadir=datadir)
            except Exception: # pragma: no cover
                raise
        else:
            raise UFWError("Unsupported backend type '%s'" % (backend_type))

        # Initialize input strings for translations
        self.no = _("n")
        self.yes = _("y")
        self.yes_full = _("yes")

    def set_enabled(self, enabled):
        '''Toggles ENABLED state in <config_dir>/ufw/ufw.conf and starts or
           stops running firewall.
        '''
        res = ""

        config_str = "no"
        if enabled:
            config_str = "yes"

        changed = False
        if (enabled and not self.backend.is_enabled()) or \
           (not enabled and self.backend.is_enabled()):
            changed = True

        # Update the config files when toggling enable/disable
        if changed:
            try:
                self.backend.set_default(self.backend.files['conf'], \
                                         "ENABLED", config_str)
            except UFWError as e: # pragma: no cover
                error(e.value)

        error_str = ""
        if enabled:
            try:
                self.backend.start_firewall()
            except UFWError as e: # pragma: no cover
                if changed:
                    error_str = e.value

            if error_str != "": # pragma: no cover
                # Revert config files when toggling enable/disable and
                # firewall failed to start
                try:
                    self.backend.set_default(self.backend.files['conf'], \
                                             "ENABLED", "no")
                except UFWError as e:
                    error(e.value)

                # Report the error
                error(error_str)

            res = _("Firewall is active and enabled on system startup")
        else:
            try:
                self.backend.stop_firewall()
            except UFWError as e: # pragma: no cover
                error(e.value)

            res = _("Firewall stopped and disabled on system startup")

        return res

    def set_default_policy(self, policy, direction):
        '''Sets default policy of firewall'''
        res = ""
        try:
            res = self.backend.set_default_policy(policy, direction)
            if self.backend.is_enabled():
                self.backend.stop_firewall()
                self.backend.start_firewall()
        except UFWError as e: # pragma: no cover
            error(e.value)

        return res

    def set_loglevel(self, level):
        '''Sets log level of firewall'''
        res = ""
        try:
            res = self.backend.set_loglevel(level)
        except UFWError as e: # pragma: no cover
            error(e.value)

        return res

    def get_status(self, verbose=False, show_count=False):
        '''Shows status of firewall'''
        try:
            out = self.backend.get_status(verbose, show_count)
        except UFWError as e: # pragma: no cover
            error(e.value)

        return out

    def get_show_raw(self, rules_type="raw"):
        '''Shows raw output of firewall'''
        try:
            out = self.backend.get_running_raw(rules_type)
        except UFWError as e: # pragma: no cover
            error(e.value)

        return out

    def get_show_listening(self):
        '''Shows listening services and incoming rules that might affect
           them'''
        res = ""
        try:
            d = ufw.util.parse_netstat_output(self.backend.use_ipv6())
        except Exception: # pragma: no cover
            err_msg = _("Could not get listening status")
            raise UFWError(err_msg)

        rules = self.backend.get_rules()

        protocols = list(d.keys())
        protocols.sort()
        for proto in protocols:
            if not self.backend.use_ipv6() and proto in ['tcp6', 'udp6']:
                continue # pragma: no cover
            res += "%s:\n" % (proto)
            ports = list(d[proto].keys())
            ports.sort()
            for port in ports:
                for item in d[proto][port]:
                    addr = item['laddr']
                    if not addr.startswith("127.") and \
                       not addr.startswith("::1"):
                        ifname = ""

                        res += "  %s " % port
                        if addr == "0.0.0.0" or addr == "::":
                            res += "* "
                            addr = "%s/0" % (item['laddr'])
                        else:
                            res += "%s " % addr
                            ifname = ufw.util.get_if_from_ip(addr)
                        res += "(%s)" % os.path.basename(item['exe'])

                        # Create an incoming rule since matching outgoing and
                        # forward rules doesn't make sense for this report.
                        rule = ufw.common.UFWRule(action="allow", \
                                                  protocol=proto[:3], \
                                                  dport=port, \
                                                  dst=addr,
                                                  direction="in", \
                                                  forward=False
                                                 )
                        rule.set_v6(proto.endswith("6"))

                        if ifname != "":
                            rule.set_interface("in", ifname)

                        rule.normalize()

                        # Get the non-tuple rule from get_matching(), and then
                        # add its corresponding CLI command.
                        matching = self.backend.get_matching(rule)
                        if len(matching) > 0:
                            res += "\n"
                            for i in matching:
                                if i > 0 and i - 1 < len(rules):
                                    res += "   [%2d] %s\n" % (i, \
                                        # Don't need UFWCommandRule here either
                                        ufw.parser.UFWCommandRule.get_command(\
                                          rules[i-1])
                                    )

                        res += "\n"

        if not self.backend.use_ipv6():
            ufw.util.debug("Skipping tcp6 and udp6 (IPv6 is disabled)")

        return res

    def get_show_added(self):
        '''Shows added rules to the firewall'''
        rules = self.backend.get_rules()

        out = _("Added user rules (see 'ufw status' for running firewall):")

        if len(rules) == 0:
            return out + _("\n(None)")

        added = []
        for r in self.backend.get_rules():
            if r.forward:
                rstr = "route %s" % \
                        ufw.parser.UFWCommandRouteRule.get_command(r)
            else:
                rstr = ufw.parser.UFWCommandRule.get_command(r)

            # Approximate the order the rules were added. Since rules is
            # internally rules4 + rules6, IPv6 only rules will show up after
            # other rules. In terms of rule ordering in the kernel, this is
            # an equivalent ordering.
            if rstr in added:
                continue

            added.append(rstr)
            out += "\nufw %s" % rstr

        return out

    def set_rule(self, rule, ip_version):
        '''Updates firewall with rule'''
        res = ""
        err_msg = ""
        tmp = ""
        rules = []

        if rule.dapp == "" and rule.sapp == "":
            rules.append(rule)
        else:
            tmprules = []
            try:
                if rule.remove:
                    if ip_version == "v4":
                        tmprules = self.backend.get_app_rules_from_system(
                                                                   rule, False)
                    elif ip_version == "v6":
                        tmprules = self.backend.get_app_rules_from_system(
                                                                   rule, True)
                    elif ip_version == "both":
                        tmprules = self.backend.get_app_rules_from_system(
                                                                   rule, False)
                        tmprules6 = self.backend.get_app_rules_from_system(
                                                                   rule, True)
                        # Only add rules that are different by more than v6 (we
                        # will handle 'ip_version == both' specially, below).
                        for x in tmprules:
                            for y in tmprules6:
                                prev6 = y.v6
                                y.v6 = False
                                if not x.match(y):
                                    y.v6 = prev6
                                    tmprules.append(y)
                    else:
                        err_msg = _("Invalid IP version '%s'") % (ip_version)
                        raise UFWError(err_msg)

                    # Don't process removal of non-existing application rules
                    if len(tmprules) == 0 and not self.backend.dryrun:
                        tmp = _("Could not delete non-existent rule")
                        if ip_version == "v4":
                            res = tmp
                        elif ip_version == "v6":
                            res = tmp + " (v6)"
                        elif ip_version == "both":
                            res = tmp + "\n" + tmp + " (v6)"
                        return res

                    for tmp in tmprules:
                        r = tmp.dup_rule()
                        r.remove = rule.remove
                        r.set_action(rule.action)
                        r.set_logtype(rule.logtype)
                        rules.append(r)
                else:
                    rules = self.backend.get_app_rules_from_template(rule)
                    # Reverse the order of rules for inserted or prepended
                    # rules, so they are inserted in the right order
                    if rule.position != 0:
                        rules.reverse()
            except Exception:
                raise

        count = 0
        set_error = False
        pos_err_msg = _("Invalid position '")
        num_v4 = self.backend.get_rules_count(False)
        num_v6 = self.backend.get_rules_count(True)
        for i, r in enumerate(rules):
            count = i
            if r.position > num_v4 + num_v6:
                pos_err_msg += str(r.position) + "'"
                raise UFWError(pos_err_msg)
            try:
                if self.backend.use_ipv6():
                    if ip_version == "v4":
                        if r.position == -1:  # prepend
                            begin = 0 if count == 0 and num_v4 == 0 else 1
                            r.set_position(begin)
                        elif r.position > num_v4:
                            pos_err_msg += str(r.position) + "'"
                            raise UFWError(pos_err_msg)
                        r.set_v6(False)
                        tmp = self.backend.set_rule(r)
                    elif ip_version == "v6":
                        if r.position == -1:  # prepend
                            begin = 0 if count == 0 and num_v6 == 0 else 1
                            r.set_position(begin)
                        elif r.position > num_v4:
                            r.set_position(r.position - num_v4)
                        elif r.position != 0 and r.position <= num_v4:
                            pos_err_msg += str(r.position) + "'"
                            raise UFWError(pos_err_msg)
                        r.set_v6(True)
                        tmp = self.backend.set_rule(r)
                    elif ip_version == "both":
                        user_pos = r.position # user specified position
                        r.set_v6(False)
                        if user_pos == -1:  # prepend
                            begin = 0 if count == 0 and num_v4 == 0 else 1
                            r.set_position(begin)
                        elif not r.remove and user_pos > num_v4:
                            # The user specified a v6 rule, so try to find a
                            # match in the v4 rules and use its position.
                            p = self.backend.find_other_position( \
                                user_pos - num_v4 + count, True)
                            if p > 0:
                                r.set_position(p)
                            else:
                                # If not found, then add the rule
                                r.set_position(0)
                        tmp = self.backend.set_rule(r)

                        # We need to readjust the position since the number
                        # of ipv4 rules increased
                        if not r.remove and user_pos > 0:
                            num_v4 = self.backend.get_rules_count(False)
                            r.set_position(user_pos + 1)

                        r.set_v6(True)
                        if user_pos == -1:  # prepend
                            begin = 0 if count == 0 and num_v6 == 0 else 1
                            r.set_position(begin)
                        elif not r.remove and r.position > 0 and \
                           r.position <= num_v4:
                            # The user specified a v4 rule, so try to find a
                            # match in the v6 rules and use its position.
                            p = self.backend.find_other_position(r.position, \
                                                                 False)
                            if p > 0:
                                # Subtract count since the list is reversed
                                r.set_position(p - count)
                            else:
                                # If not found, then add the rule
                                r.set_position(0)
                        if tmp != "":
                            tmp += "\n"

                        # Readjust position to send to set_rule
                        if not r.remove and r.position > num_v4 and \
                           user_pos != -1:
                            r.set_position(r.position - num_v4)

                        tmp += self.backend.set_rule(r)
                    else:
                        err_msg = _("Invalid IP version '%s'") % (ip_version)
                        raise UFWError(err_msg)
                else:
                    if r.position == -1:  # prepend
                        begin = 0 if count == 0 and num_v4 == 0 else 1
                        r.set_position(begin)
                    if ip_version == "v4" or ip_version == "both":
                        r.set_v6(False)
                        tmp = self.backend.set_rule(r)
                    elif ip_version == "v6":
                        err_msg = _("IPv6 support not enabled")
                        raise UFWError(err_msg)
                    else:
                        err_msg = _("Invalid IP version '%s'") % (ip_version)
                        raise UFWError(err_msg)
            except UFWError as e:
                err_msg = e.value
                set_error = True
                break

            if r.updated:
                warn_msg = _("Rule changed after normalization")
                warnings.warn(warn_msg)

        if not set_error:
            # Just return the last result if no error
            res += tmp
        elif len(rules) == 1:
            # If no error, and just one rule, error out
            error(err_msg) # pragma: no cover
        else:
            # If error and more than one rule, delete the successfully added
            # rules in reverse order
            undo_error = False
            indexes = list(range(count+1))
            indexes.reverse()
            for j in indexes:
                if count > 0 and rules[j]:
                    backout_rule = rules[j].dup_rule()
                    backout_rule.remove = True
                    try:
                        self.set_rule(backout_rule, ip_version)
                    except Exception:
                        # Don't fail, so we can try to backout more
                        undo_error = True
                        warn_msg = _("Could not back out rule '%s'") % \
                                     r.format_rule()
                        warn(warn_msg)

            err_msg += _("\nError applying application rules.")
            if undo_error:
                err_msg += _(" Some rules could not be unapplied.")
            else:
                err_msg += _(" Attempted rules successfully unapplied.")

            raise UFWError(err_msg)

        return res

    def delete_rule(self, number, force=False):
        '''Delete rule'''
        try:
            n = int(number)
        except Exception:
            err_msg = _("Could not find rule '%s'") % number
            raise UFWError(err_msg)

        rules = self.backend.get_rules()
        if n <= 0 or n > len(rules):
            err_msg = _("Could not find rule '%d'") % n
            raise UFWError(err_msg)

        rule = self.backend.get_rule_by_number(n)
        if not rule:
            err_msg = _("Could not find rule '%d'") % n
            raise UFWError(err_msg)

        rule.remove = True

        ip_version = "v4"
        if rule.v6:
            ip_version = "v6"

        proceed = True
        if not force:
            if rule.forward:
                rstr = "route %s" % \
                        ufw.parser.UFWCommandRouteRule.get_command(rule)
            else:
                rstr = ufw.parser.UFWCommandRule.get_command(rule)
            prompt = _("Deleting:\n %(rule)s\nProceed with operation " \
                       "(%(yes)s|%(no)s)? ") % ({'rule': rstr, \
                                                 'yes': self.yes, \
                                                 'no': self.no})
            msg(prompt, output=sys.stdout, newline=False)
            ans = sys.stdin.readline().lower().strip()
            if ans != "y" and ans != self.yes.lower() and \
               ans != self.yes_full.lower():
                proceed = False

        res = ""
        if proceed:
            res = self.set_rule(rule, ip_version)
        else:
            res = _("Aborted")

        return res

    def do_action(self, action, rule, ip_version, force=False):
        '''Perform action on rule. action, rule and ip_version are usually
           based on return values from parse_command().
        '''
        res = ""
        if action.startswith("logging-on"):
            tmp = action.split('_')
            if len(tmp) > 1:
                res = self.set_loglevel(tmp[1])
            else:
                res = self.set_loglevel("on")
        elif action == "logging-off":
            res = self.set_loglevel("off")
        elif action.startswith("default-"):
            err_msg = _("Unsupported default policy")
            tmp = action.split('-')
            if len(tmp) != 3:
                raise UFWError(err_msg)
            res = self.set_default_policy(tmp[1], tmp[2])
        elif action == "reset":
            res = self.reset(force)
        elif action == "status":
            res = self.get_status()
        elif action == "status-verbose":
            res = self.get_status(True)
        elif action.startswith("show"):
            tmp = action.split('-')[1]
            if tmp == "listening":
                res = self.get_show_listening()
            elif tmp == "added":
                res = self.get_show_added()
            else:
                res = self.get_show_raw(tmp)
        elif action == "status-numbered":
            res = self.get_status(False, True)
        elif action == "enable":
            res = self.set_enabled(True)
        elif action == "disable":
            res = self.set_enabled(False)
        elif action == "reload":
            if self.backend.is_enabled():
                self.set_enabled(False)
                self.set_enabled(True)
                res = _("Firewall reloaded")
            else:
                res = _("Firewall not enabled (skipping reload)")
        elif action.startswith("delete-"):
            res = self.delete_rule(action.split('-')[1], force)
        elif action == "allow" or action == "deny" or action == "reject" or \
             action == "limit":
            # allow case insensitive matches for application rules
            if rule.dapp != "":
                try:
                    tmp = self.backend.find_application_name(rule.dapp)
                    if tmp != rule.dapp:
                        rule.dapp = tmp
                        rule.set_port(tmp, "dst")
                except UFWError as e:
                    # allow for the profile being deleted (LP: #407810)
                    if not rule.remove: # pragma: no cover
                        error(e.value)
                    if not ufw.applications.valid_profile_name(rule.dapp):
                        err_msg = _("Invalid profile name")
                        raise UFWError(err_msg)

            if rule.sapp != "":
                try:
                    tmp = self.backend.find_application_name(rule.sapp)
                    if tmp != rule.sapp:
                        rule.sapp = tmp
                        rule.set_port(tmp, "dst")
                except UFWError as e:
                    # allow for the profile being deleted (LP: #407810)
                    if not rule.remove: # pragma: no cover
                        error(e.value)
                    if not ufw.applications.valid_profile_name(rule.sapp):
                        err_msg = _("Invalid profile name")
                        raise UFWError(err_msg)

            res = self.set_rule(rule, ip_version)
        else:
            err_msg = _("Unsupported action '%s'") % (action)
            raise UFWError(err_msg)

        return res

    def set_default_application_policy(self, policy):
        '''Sets default application policy of firewall'''
        res = ""
        try:
            res = self.backend.set_default_application_policy(policy)
        except UFWError as e: # pragma: no cover
            error(e.value)

        return res

    def get_application_list(self):
        '''Display list of known application profiles'''
        names = list(self.backend.profiles.keys())
        names.sort()
        rstr = _("Available applications:")
        for n in names:
            rstr += "\n  %s" % (n)
        return rstr

    def get_application_info(self, pname):
        '''Display information on profile'''
        names = []
        if pname == "all":
            names = list(self.backend.profiles.keys())
            names.sort()
        else:
            if not ufw.applications.valid_profile_name(pname):
                err_msg = _("Invalid profile name")
                raise UFWError(err_msg)
            names.append(pname)

        rstr = ""
        for name in names:
            if name not in self.backend.profiles or \
               not self.backend.profiles[name]:
                err_msg = _("Could not find profile '%s'") % (name)
                raise UFWError(err_msg)

            if not ufw.applications.verify_profile(name, \
               self.backend.profiles[name]):
                err_msg = _("Invalid profile")
                raise UFWError(err_msg)

            rstr += _("Profile: %s\n") % (name)
            rstr += _("Title: %s\n") % (ufw.applications.get_title(\
                                        self.backend.profiles[name]))

            rstr += _("Description: %s\n\n") % \
                                            (ufw.applications.get_description(\
                                             self.backend.profiles[name]))

            ports = ufw.applications.get_ports(self.backend.profiles[name])
            if len(ports) > 1 or ',' in ports[0]:
                rstr += _("Ports:")
            else:
                rstr += _("Port:")

            for p in ports:
                rstr += "\n  %s" % (p)

            if name != names[len(names)-1]:
                rstr += "\n\n--\n\n"

        return ufw.util.wrap_text(rstr)

    def application_update(self, profile):
        '''Refresh application profile'''
        rstr = ""
        allow_reload = True
        trigger_reload = False

        try: # pragma: no cover
            if self.backend.do_checks and ufw.util.under_ssh():
                # Don't reload the firewall if running under ssh
                allow_reload = False
        except Exception: # pragma: no cover
            # If for some reason we get an exception trying to find the parent
            # pid, err on the side of caution and don't automatically reload
            # the firewall. LP: #424528
            allow_reload = False

        if profile == "all":
            profiles = list(self.backend.profiles.keys())
            profiles.sort()
            for p in profiles:
                (tmp, found) = self.backend.update_app_rule(p)
                if found:
                    if tmp != "":
                        tmp += "\n"
                    rstr += tmp
                    trigger_reload = found
        else:
            (rstr, trigger_reload) = self.backend.update_app_rule(profile)
            if rstr != "":
                rstr += "\n"

        if trigger_reload and self.backend.is_enabled():
            if allow_reload:
                try:
                    self.backend._reload_user_rules()
                except Exception:
                    raise
                rstr += _("Firewall reloaded")
            else:
                rstr += _("Skipped reloading firewall")

        return rstr

    def application_add(self, profile):
        '''Refresh application profile'''
        rstr = ""
        policy = ""

        if profile == "all":
            err_msg = _("Cannot specify 'all' with '--add-new'")
            raise UFWError(err_msg)

        default = self.backend.defaults['default_application_policy']
        if default == "skip":
            ufw.util.debug("Policy is '%s', not adding profile '%s'" % \
                           (policy, profile))
            return rstr
        elif default == "accept":
            policy = "allow"
        elif default == "drop":
            policy = "deny"
        elif default == "reject":
            policy = "reject"
        else:
            err_msg = _("Unknown policy '%s'") % (default)
            raise UFWError(err_msg)

        args = [ 'ufw' ]
        if self.backend.dryrun:
            args.append("--dry-run")

        args += [ policy, profile ]
        try:
            pr = parse_command(args)
        except Exception: # pragma: no cover
            raise

        if 'rule' in pr.data:
            rstr = self.do_action(pr.action, pr.data['rule'], \
                                  pr.data['iptype'])
        else:
            rstr = self.do_action(pr.action, "", "")

        return rstr

    def do_application_action(self, action, profile):
        '''Perform action on profile. action and profile are usually based on
           return values from parse_command().
        '''
        res = ""
        if action == "default-allow":
            res = self.set_default_application_policy("allow")
        elif action == "default-deny":
            res = self.set_default_application_policy("deny")
        elif action == "default-reject":
            res = self.set_default_application_policy("reject")
        elif action == "default-skip":
            res = self.set_default_application_policy("skip")
        elif action == "list":
            res = self.get_application_list()
        elif action == "info":
            res = self.get_application_info(profile)
        elif action == "update" or action == "update-with-new":
            str1 = self.application_update(profile)
            str2 = ""
            if action == "update-with-new":
                str2 = self.application_add(profile)

            if str1 != "" and str2 != "":
                str1 += "\n"
            res = str1 + str2
        else:
            err_msg = _("Unsupported action '%s'") % (action)
            raise UFWError(err_msg)

        return res

    def continue_under_ssh(self):
        '''If running under ssh, prompt the user for confirmation'''
        proceed = True
        if self.backend.do_checks and ufw.util.under_ssh(): # pragma: no cover
            prompt = _("Command may disrupt existing ssh connections. " \
                       "Proceed with operation (%(yes)s|%(no)s)? ") % \
                       ({'yes': self.yes, 'no': self.no})
            msg(prompt, output=sys.stdout, newline=False)
            ans = sys.stdin.readline().lower().strip()
            if ans != "y" and ans != self.yes and ans != self.yes_full:
                proceed = False

        return proceed

    def reset(self, force=False):
        '''Reset the firewall'''
        res = ""
        prompt = _("Resetting all rules to installed defaults. Proceed with " \
                   "operation (%(yes)s|%(no)s)? ") % \
                   ({'yes': self.yes, 'no': self.no})
        if self.backend.do_checks and ufw.util.under_ssh():
            prompt = _("Resetting all rules to installed defaults. This may " \
                       "disrupt existing ssh connections. Proceed with " \
                       "operation (%(yes)s|%(no)s)? ") % \
                       ({'yes': self.yes, 'no': self.no})

        if self.backend.do_checks and not force: # pragma: no cover
            msg(ufw.util.wrap_text(prompt), output=sys.stdout, newline=False)
            ans = sys.stdin.readline().lower().strip()
            if ans != "y" and ans != self.yes and ans != self.yes_full:
                res = _("Aborted")
                return res

        if self.backend.is_enabled():
            res += self.set_enabled(False)
        res = self.backend.reset()

        return res
