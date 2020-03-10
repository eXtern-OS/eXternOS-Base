#
# parser.py: parser class for ufw
#
# Copyright 2009-2018 Canonical Ltd.
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
#
# Adding New Commands
#
# 1. Create a new UFWCommandFoo object that implements UFWCommand
# 2. Create UFWCommandFoo.parse() to return a UFWParserResponse object
# 3. Create UFWCommandFoo.help() to display help for this command
# 4. Register this command with the parser using:
#    parser.register_command(UFWCommandFoo('foo'))
#
#
# Extending Existing Commands
#
# 1. Register the new command with an existing UFWCommand via
#    register_command(). Eg
#    parser.register_command(UFWCommandNewcommand('new_command'))
# 2. Update UFWCommandExisting.parse() for new_command
# 3. Update UFWCommandExisting.help() for new_command
#

import re
import ufw.util
import ufw.applications
from ufw.common import UFWError
from ufw.util import debug


class UFWCommand:
    '''Generic class for parser commands.'''
    def __init__(self, type, command):
        self.command = command
        self.types = []
        if type not in self.types:
            self.types.append(type)
        self.type = type

    def parse(self, argv):
        if len(argv) < 1:
            raise ValueError()

        r = UFWParserResponse(argv[0].lower())

        return r

    def help(self, args):
        raise UFWError("UFWCommand.help: need to override")


class UFWCommandRule(UFWCommand):
    '''Class for parsing ufw rule commands'''
    def __init__(self, command):
        type = 'rule'
        UFWCommand.__init__(self, type, command)

    def parse(self, argv):
        action = ""
        rule = ""
        type = ""
        from_type = "any"
        to_type = "any"
        from_service = ""
        to_service = ""
        insert_pos = ""
        logtype = ""
        remove = False

        if len(argv) > 0 and argv[0].lower() == "rule":
            argv.remove(argv[0])

        # TODO: break this out
        if len(argv) > 0:
            if argv[0].lower() == "delete" and len(argv) > 1:
                remove = True
                argv.remove(argv[0])
                rule_num = None
                try:
                    rule_num = int(argv[0])
                except Exception:
                    action = argv[0]

                # return quickly if deleting by rule number
                if rule_num is not None:
                    r = UFWParserResponse('delete-%d' % rule_num)
                    return r

            elif argv[0].lower() == "insert":
                if len(argv) < 4:
                    raise ValueError()
                insert_pos = argv[1]

                # Using position '0' appends the rule while '-1' prepends,
                # which is potentially confusing for the end user
                if insert_pos == "0" or insert_pos == "-1":
                    err_msg = _("Cannot insert rule at position '%s'") % \
                                (insert_pos)
                    raise UFWError(err_msg)

                # strip out 'insert NUM' and parse as normal
                del argv[1]
                del argv[0]

            elif argv[0].lower() == "prepend":
                insert_pos = -1
                del argv[0]

            action = argv[0]

        if action != "allow" and action != "deny" and action != "reject" and \
           action != "limit":
            raise ValueError()

        nargs = len(argv)
        if nargs < 2:
            raise ValueError()

        # set/strip
        rule_direction = "in"
        if nargs > 1 and (argv[1].lower() == "in" or \
                          argv[1].lower() == "out"):
            rule_direction = argv[1].lower()

        # strip out direction if not an interface rule
        if nargs > 2 and argv[2] != "on" and (argv[1].lower() == "in" or \
                                              argv[1].lower() == "out"):
            rule_direction = argv[1].lower()
            del argv[1]
            nargs = len(argv)

        # strip out 'on' as in 'allow in on eth0 ...'
        has_interface = False
        if nargs > 1 and (argv.count('in') > 0 or argv.count('out') > 0):
            err_msg = _("Invalid interface clause")

            if argv[1].lower() != "in" and argv[1].lower() != "out":
                raise UFWError(err_msg)
            if nargs < 3 or argv[2].lower() != "on":
                raise UFWError(err_msg)

            del argv[2]
            nargs = len(argv)
            has_interface = True

        log_idx = 0
        if has_interface and nargs > 3 and (argv[3].lower() == "log" or \
                                            argv[3].lower() == 'log-all'):
            log_idx = 3
        elif nargs > 2 and (argv[1].lower() == "log" or \
                           argv[1].lower() == 'log-all'):
            log_idx = 1

        if log_idx > 0:
            logtype = argv[log_idx].lower()
            # strip out 'log' or 'log-all' and parse as normal
            del argv[log_idx]
            nargs = len(argv)

        if "log" in argv:
            err_msg = _("Option 'log' not allowed here")
            raise UFWError(err_msg)

        if "log-all" in argv:
            err_msg = _("Option 'log-all' not allowed here")
            raise UFWError(err_msg)

        comment = ""
        if 'comment' in argv:
            comment_idx = argv.index("comment")
            if comment_idx == len(argv) - 1:
                err_msg = _("Option 'comment' missing required argument")
                raise UFWError(err_msg)
            comment = argv[comment_idx+1]
            # TODO: properly support "'" in the comment string. See r949 for
            # details
            if "'" in comment:
                err_msg = _("Comment may not contain \"'\"")
                raise ValueError(err_msg)

            del argv[comment_idx+1]
            del argv[comment_idx]
            nargs = len(argv)

        if nargs < 2 or nargs > 13:
            raise ValueError()

        rule_action = action
        if logtype != "":
            rule_action += "_" + logtype
        rule = ufw.common.UFWRule(rule_action, "any", "any", \
                                  direction=rule_direction,
                                  comment=ufw.util.hex_encode(comment))
        if remove:
            rule.remove = remove
        elif insert_pos != "":
            try:
                rule.set_position(insert_pos)
            except Exception:
                raise
        if nargs == 2:
            # Short form where only app or port/proto is given
            if ufw.applications.valid_profile_name(argv[1]):
                # Check if name collision with /etc/services. If so, use
                # /etc/services instead of application profile
                try:
                    ufw.util.get_services_proto(argv[1])
                except Exception:
                    type = "both"
                    rule.dapp = argv[1]
                    rule.set_port(argv[1], "dst")
            if rule.dapp == "":
                try:
                    (port, proto) = ufw.util.parse_port_proto(argv[1])
                except ValueError as e:
                    raise UFWError(e)

                if not re.match('^\d([0-9,:]*\d+)*$', port):
                    if ',' in port or ':' in port:
                        err_msg = _("Port ranges must be numeric")
                        raise UFWError(err_msg)
                    to_service = port

                try:
                    rule.set_protocol(proto)
                    rule.set_port(port, "dst")
                    type = "both"
                except UFWError:
                    err_msg = _("Bad port")
                    raise UFWError(err_msg)
        elif (nargs + 1) % 2 != 0:
            err_msg = _("Wrong number of arguments")
            raise UFWError(err_msg)
        elif 'from' not in argv and 'to' not in argv and 'in' not in argv and \
             'out' not in argv:
            err_msg = _("Need 'to' or 'from' clause")
            raise UFWError(err_msg)
        else:
            # Full form with PF-style syntax
            keys = [ 'proto', 'from', 'to', 'port', 'app', 'in', 'out' ]

            # quick check
            if argv.count("to") > 1 or \
               argv.count("from") > 1 or \
               argv.count("proto") > 1 or \
               argv.count("port") > 2 or \
               argv.count("in") > 1 or \
               argv.count("out") > 1 or \
               argv.count("app") > 2 or \
               argv.count("app") > 0 and argv.count("proto") > 0:
                err_msg = _("Improper rule syntax")
                raise UFWError(err_msg)

            i = 0
            loc = ""
            for arg in argv:
                if i % 2 != 0 and argv[i] not in keys:
                    err_msg = _("Invalid token '%s'") % (argv[i])
                    raise UFWError(err_msg)
                if arg == "proto":
                    if i+1 < nargs:
                        try:
                            rule.set_protocol(argv[i+1])
                        except Exception:
                            raise
                    else: # pragma: no cover
                        # This can't normally be reached because of nargs
                        # checks above, but leave it here in case our parsing
                        # changes
                        err_msg = _("Invalid 'proto' clause")
                        raise UFWError(err_msg)
                elif arg == "in" or arg == "out":
                    if i+1 < nargs:
                        try:
                            if arg == "in":
                                rule.set_interface("in", argv[i+1])
                            elif arg == "out":
                                rule.set_interface("out", argv[i+1])
                        except Exception:
                            raise
                    else: # pragma: no cover
                        # This can't normally be reached because of nargs
                        # checks above, but leave it here in case our parsing
                        # changes
                        err_msg = _("Invalid '%s' clause") % (arg)
                        raise UFWError(err_msg)
                elif arg == "from":
                    if i+1 < nargs:
                        try:
                            faddr = argv[i+1].lower()
                            if faddr == "any":
                                faddr = "0.0.0.0/0"
                                from_type = "any"
                            else:
                                if ufw.util.valid_address(faddr, "6"):
                                    from_type = "v6"
                                else:
                                    from_type = "v4"
                            rule.set_src(faddr)
                        except Exception:
                            raise
                        loc = "src"
                    else: # pragma: no cover
                        # This can't normally be reached because of nargs
                        # checks above, but leave it here in case our parsing
                        # changes
                        err_msg = _("Invalid 'from' clause")
                        raise UFWError(err_msg)
                elif arg == "to":
                    if i+1 < nargs:
                        try:
                            saddr = argv[i+1].lower()
                            if saddr == "any":
                                saddr = "0.0.0.0/0"
                                to_type = "any"
                            else:
                                if ufw.util.valid_address(saddr, "6"):
                                    to_type = "v6"
                                else:
                                    to_type = "v4"
                            rule.set_dst(saddr)
                        except Exception:
                            raise
                        loc = "dst"
                    else: # pragma: no cover
                        # This can't normally be reached because of nargs
                        # checks above, but leave it here in case our parsing
                        # changes
                        err_msg = _("Invalid 'to' clause")
                        raise UFWError(err_msg)
                elif arg == "port" or arg == "app":
                    if i+1 < nargs:
                        if loc == "":
                            err_msg = _("Need 'from' or 'to' with '%s'") % \
                                        (arg)
                            raise UFWError(err_msg)

                        tmp = argv[i+1]
                        if arg == "app":
                            if loc == "src":
                                rule.sapp = tmp
                            else:
                                rule.dapp = tmp
                        elif not re.match('^\d([0-9,:]*\d+)*$', tmp):
                            if ',' in tmp or ':' in tmp:
                                err_msg = _("Port ranges must be numeric")
                                raise UFWError(err_msg)

                            if loc == "src":
                                from_service = tmp
                            else:
                                to_service = tmp
                        try:
                            rule.set_port(tmp, loc)
                        except Exception:
                            raise
                    else: # pragma: no cover
                        # This can't normally be reached because of nargs
                        # checks above, but leave it here in case our parsing
                        # changes
                        err_msg = _("Invalid 'port' clause")
                        raise UFWError(err_msg)
                i += 1

            # Figure out the type of rule (IPv4, IPv6, or both) this is
            if from_type == "any" and to_type == "any":
                type = "both"
            elif from_type != "any" and to_type != "any" and \
                 from_type != to_type:
                err_msg = _("Mixed IP versions for 'from' and 'to'")
                raise UFWError(err_msg)
            elif from_type != "any":
                type = from_type
            elif to_type != "any":
                type = to_type

        # Adjust protocol
        if to_service != "" or from_service != "":
            proto = ""
            if to_service != "":
                try:
                    proto = ufw.util.get_services_proto(to_service)
                except Exception: # pragma: no cover
                    # This can't normally be reached because of set_port()
                    # checks above, but leave it here in case our parsing
                    # changes
                    err_msg = _("Could not find protocol")
                    raise UFWError(err_msg)
            if from_service != "":
                if proto == "any" or proto == "":
                    try:
                        proto = ufw.util.get_services_proto(from_service)
                    except Exception: # pragma: no cover
                        # This can't normally be reached because of set_port()
                        # checks above, but leave it here in case our parsing
                        # changes
                        err_msg = _("Could not find protocol")
                        raise UFWError(err_msg)
                else:
                    try:
                        tmp = ufw.util.get_services_proto(from_service)
                    except Exception: # pragma: no cover
                        # This can't normally be reached because of set_port()
                        # checks above, but leave it here in case our parsing
                        # changes
                        err_msg = _("Could not find protocol")
                        raise UFWError(err_msg)
                    if proto == "any" or proto == tmp:
                        proto = tmp
                    elif tmp == "any":
                        pass
                    else:
                        err_msg = _("Protocol mismatch (from/to)")
                        raise UFWError(err_msg)

            # Verify found proto with specified proto
            if rule.protocol == "any":
                rule.set_protocol(proto)
            elif proto != "any" and rule.protocol != proto:
                err_msg = _("Protocol mismatch with specified protocol %s") % \
                            (rule.protocol)
                raise UFWError(err_msg)

        # adjust type as needed
        if rule:
            if rule.protocol in ufw.util.ipv4_only_protocols and \
               type == "both":
                debug("Adjusting iptype to 'v4' for protocol '%s'" % \
                      (rule.protocol))
                type = "v4"

            # Now verify the rule
            rule.verify(type)

        r = UFWParserResponse(action)
        r.data['type'] = self.type
        r.data['rule'] = rule
        r.data['iptype'] = type

        return r

    def get_command(r):
        '''Get command string for rule'''
        res = r.action

        if (r.dst == "0.0.0.0/0" or r.dst == "::/0") and \
           (r.src == "0.0.0.0/0" or r.src == "::/0") and \
           r.sport == "any" and \
           r.sapp == "" and \
           r.interface_in == "" and \
           r.interface_out == "" and \
           r.dport != "any":
            # Short syntax
            if r.direction == "out":
                res += " %s" % r.direction
            if r.logtype != "":
                res += " %s" % r.logtype
            if r.dapp != "":
                if " " in r.dapp:
                    res += " '%s'" % r.dapp
                else:
                    res += " %s" % r.dapp
            else:
                res += " %s" % r.dport
                if r.protocol != "any":
                    res += "/%s" % r.protocol
            if r.comment != "":
                res += " comment '%s'" % r.get_comment()
        else:
            # Full syntax
            if r.interface_in != "":
                res += " in on %s" % r.interface_in
            if r.interface_out != "":
                res += " out on %s" % r.interface_out
            elif r.direction == "out":
                res += " %s" % r.direction
            if r.logtype != "":
                res += " %s" % r.logtype

            for i in ['src', 'dst']:
                if i == 'src':
                    loc = r.src
                    port = r.sport
                    app = r.sapp
                    dir = "from"
                else:
                    loc = r.dst
                    port = r.dport
                    app = r.dapp
                    dir = "to"

                if loc == "0.0.0.0/0" or loc == "::/0":
                    loc = "any"

                if loc != "any" or port != "any" or app != "":
                    res += " %s %s" % (dir, loc)
                    if app != "":
                        if " " in app:
                            res += " app '%s'" % app
                        else:
                            res += " app %s" % app
                    elif port != "any":
                        res += " port %s" % port

            # If still haven't added more than action, direction and/or
            # logtype, then we have a very generic rule, so add 'to any' to
            # mark it as extended form.
            if ' to ' not in res and ' from ' not in res and \
                    r.interface_in == "" and r.interface_out == "":
                res += " to any"

            if r.protocol != "any" and r.dapp == "" and r.sapp == "":
                res += " proto %s" % r.protocol

            if r.comment != "":
                res += " comment '%s'" % r.get_comment()

        return res
    get_command = staticmethod(get_command)


class UFWCommandRouteRule(UFWCommandRule):
    '''Class for parsing ufw route rule commands'''
    def __init__(self, command):
        UFWCommandRule.__init__(self, command)
        self.type = 'route'

    def parse(self, argv):
        assert(argv[0] == "route")

        # 'ufw delete NUM' is the correct usage, not 'ufw route delete NUM'
        if 'delete' in argv:
            idx = argv.index('delete')
            err_msg = ""
            if len(argv) > idx:
                try:
                    # 'route delete NUM' is unsupported
                    int(argv[idx + 1])
                    err_msg = _("'route delete NUM' unsupported. Use 'delete NUM' instead.")
                    raise UFWError(err_msg)
                except ValueError:
                    # 'route delete RULE' is supported
                    pass

        # Let's use as much as UFWCommandRule.parse() as possible. The only
        # difference with our rules is that argv[0] is 'route' and we support
        # both 'in on <interface>' and 'out on <interface>' in our rules.
        # Because UFWCommandRule.parse() expects that the interface clause is
        # specified first, strip out the second clause and add it later
        rule_argv = None
        interface = None
        strip = None

        # eg: ['route', 'allow', 'in', 'on', 'eth0', 'out', 'on', 'eth1']
        s = " ".join(argv)
        if " in on " in s and " out on " in s:
            strip = "out"
            if argv.index("in") > argv.index("out"):
                strip = "in"
            # Remove 2nd interface clause from argv and add it to the rule
            # later. Because we searched for " <strip> on " in our joined
            # string we are guaranteed to have argv[argv.index(<strip>) + 2]
            # exist.
            interface = argv[argv.index(strip) + 2]
            rule_argv = argv[0:argv.index(strip)] + argv[argv.index(strip)+3:]
        elif not re.search(r' (in|out) on ', s) and \
             not re.search(r' app (in|out) ', s) and \
             (" in " in s or " out " in s):
            # Specifying a direction without an interface doesn't make any
            # sense with route rules. application names could be 'in' or 'out'
            # so don't artificially limit those names.
            err_msg = _("Invalid interface clause for route rule")
            raise UFWError(err_msg)
        else:
            rule_argv = argv

        rule_argv[0] = "rule"
        r = UFWCommandRule.parse(self, rule_argv)
        if 'rule' in r.data:
            r.data['rule'].forward = True
            if strip and interface:
                r.data['rule'].set_interface(strip, interface)

        return r


class UFWCommandApp(UFWCommand):
    '''Class for parsing ufw application commands'''
    def __init__(self, command):
        type = 'app'
        UFWCommand.__init__(self, type, command)

    def parse(self, argv):
        '''Parse applications command.'''
        name = ""
        action = ""
        addnew = False

        if argv[0] != "app":
            raise ValueError()
        del argv[0]

        nargs = len(argv)
        action = argv[0].lower()

        if action == "info" or action == "update":
            if nargs >= 3 and argv[1] == "--add-new":
                addnew = True
                argv.remove("--add-new")
                nargs = len(argv)

            if nargs < 2:
                raise ValueError()

            # Handle quoted name with spaces in it by stripping Python's ['...']
            # list as string text.
            name = str(argv[1]).strip("[']")

            if addnew:
                action += "-with-new"

        if action == "list" and nargs != 1:
            raise ValueError()

        if action == "default":
            if nargs < 2:
                raise ValueError()
            if argv[1].lower() == "allow":
                action = "default-allow"
            elif argv[1].lower() == "deny":
                action = "default-deny"
            elif argv[1].lower() == "reject":
                action = "default-reject"
            elif argv[1].lower() == "skip":
                action = "default-skip"
            else:
                raise ValueError()

        r = UFWParserResponse(action)
        r.data['type'] = self.type
        r.data['name'] = name

        return r


class UFWCommandBasic(UFWCommand):
    '''Class for parsing ufw basic commands'''
    def __init__(self, command):
        type = 'basic'
        UFWCommand.__init__(self, type, command)

    def parse(self, argv):
        if len(argv) != 1:
            raise ValueError()
        return UFWCommand.parse(self, argv)


class UFWCommandDefault(UFWCommand):
    '''Class for parsing ufw default commands'''
    def __init__(self, command):
        type = 'default'
        UFWCommand.__init__(self, type, command)

    def parse(self, argv):
        # Basic sanity check
        if len(argv) < 2:
            raise ValueError()

        # Set the direction
        action = ""
        direction = "incoming"
        if len(argv) > 2:
            if argv[2].lower() != "incoming" and \
               argv[2].lower() != "input" and \
               argv[2].lower() != "routed" and \
               argv[2].lower() != "forward" and \
               argv[2].lower() != "output" and \
               argv[2].lower() != "outgoing":
                raise ValueError()
            if argv[2].lower().startswith("in"):
                direction = "incoming"
            elif argv[2].lower().startswith("out"):
                direction = "outgoing"
            elif argv[2].lower() == "routed" or argv[2].lower() == "forward":
                direction = "routed"
            else:  # pragma: no cover
                direction = argv[2].lower()

        # Set the policy
        if argv[1].lower() == "deny":
            action = "default-deny"
        elif argv[1].lower() == "allow":
            action = "default-allow"
        elif argv[1].lower() == "reject":
            action = "default-reject"
        else:
            raise ValueError()

        action += "-%s" % (direction)

        return UFWParserResponse(action)


class UFWCommandLogging(UFWCommand):
    '''Class for parsing ufw logging commands'''
    def __init__(self, command):
        type = 'logging'
        UFWCommand.__init__(self, type, command)

    def parse(self, argv):
        action = ""
        if len(argv) < 2:
            raise ValueError()
        elif argv[1].lower() == "off":
            action = "logging-off"
        elif argv[1].lower() == "on" or argv[1].lower() == "low" or \
             argv[1].lower() == "medium" or argv[1].lower() == "high" or \
             argv[1].lower() == "full":
            action = "logging-on"
            if argv[1].lower() != "on":
                action += "_" + argv[1].lower()
        else:
            raise ValueError()

        return UFWParserResponse(action)


class UFWCommandStatus(UFWCommand):
    '''Class for parsing ufw status commands'''
    def __init__(self, command):
        type = 'status'
        UFWCommand.__init__(self, type, command)

    def parse(self, argv):
        r = UFWCommand.parse(self, argv)
        if len(argv) == 1:
            r.action = "status"
        elif len(argv) > 1:
            if argv[1].lower() == "verbose":
                r.action = "status-verbose"
            elif argv[1].lower() == "numbered":
                r.action = "status-numbered"
            else:
                raise ValueError()
        return r


class UFWCommandShow(UFWCommand):
    '''Class for parsing ufw show commands'''
    def __init__(self, command):
        type = 'show'
        UFWCommand.__init__(self, type, command)

    def parse(self, argv):
        action = ""
        if len(argv) == 1:
            raise ValueError()
        elif argv[1].lower() == "raw":
            action = "show-raw"
        elif argv[1].lower() == "before-rules":
            action = "show-before"
        elif argv[1].lower() == "user-rules":
            action = "show-user"
        elif argv[1].lower() == "after-rules":
            action = "show-after"
        elif argv[1].lower() == "logging-rules":
            action = "show-logging"
        elif argv[1].lower() == "builtins":
            action = "show-builtins"
        elif argv[1].lower() == "listening":
            action = "show-listening"
        elif argv[1].lower() == "added":
            action = "show-added"
        else:
            raise ValueError()

        return UFWParserResponse(action)


class UFWParserResponse:
    '''Class for ufw parser response'''
    def __init__(self, action):
        self.action = action.lower()
        self.dryrun = False
        self.force = False
        self.data = {}

    def __str__(self):
        s = "action='%s'" % (self.action)
        keys = list(self.data.keys())
        keys.sort()
        for i in keys:
            s += ",%s='%s'" % (i, self.data[i])
        s += "\n"

        return repr(s)


class UFWParser:
    '''Class for ufw parser'''
    def __init__(self):
        self.commands = {}

    def allowed_command(self, type, cmd):
        '''Return command if it is allowed, otherwise raise an exception'''
        if type.lower() not in list(self.commands.keys()):
            raise ValueError()

        if cmd.lower() not in list(self.commands[type].keys()):
            raise ValueError()

        return cmd.lower()

    def parse_command(self, args):
        '''Parse command. Returns a UFWParserAction'''
        dryrun = False
        if len(args) > 0 and args[0].lower() == "--dry-run":
            dryrun = True
            args.remove(args[0])

        force = False
        if len(args) > 0 and (args[0].lower() == "--force" or \
                              args[0].lower() == "-f"):
            force = True
            args.remove(args[0])

        cmd = ""
        type = ""

        tmp = args[0].lower()
        if len(args) > 1 and tmp in list(self.commands.keys()) and \
                args[1].lower() in list(self.commands[tmp].keys()):
            type = tmp
            cmd = args[1].lower()
        else:
            # Discover the type
            cmd = tmp
            for i in list(self.commands.keys()):
                if cmd in self.commands[i]:
                    # Skip any inherited commands that inherit from
                    # UFWCommandRule since they must have more than one
                    # argument to be valid and used
                    if isinstance(self.commands[i][cmd], UFWCommandRule) and \
                       getattr(self.commands[i][cmd], 'type') != 'rule':
                        continue  # pragma: nocover
                    type = i
                    break
            if type == "":
                type = 'rule'

        action = self.allowed_command(type, cmd)

        cmd = self.commands[type][action]
        response = cmd.parse(args)
        response.dryrun = dryrun
        response.force = force

        return response

    def register_command(self, c):
        '''Register a command with the parser'''
        if c.command is None or c.command == '':
            # If the command is empty, then use 'type' as command
            key = "%s" % (c.type)
        else:
            key = "%s" % (c.command)

        if c.type not in self.commands:
            self.commands[c.type] = {}
        if key in self.commands[c.type]:
            err_msg = _("Command '%s' already exists") % (key)
            raise UFWError(err_msg)
        self.commands[c.type][key] = c
