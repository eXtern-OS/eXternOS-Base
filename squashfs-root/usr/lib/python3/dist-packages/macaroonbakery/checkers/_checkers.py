# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import abc
from collections import namedtuple
from datetime import datetime

import pyrfc3339
from ._caveat import parse_caveat
from ._conditions import (
    COND_ALLOW,
    COND_DECLARED,
    COND_DENY,
    COND_ERROR,
    COND_TIME_BEFORE,
    STD_NAMESPACE,
)
from ._declared import DECLARED_KEY
from ._namespace import Namespace
from ._operation import OP_KEY
from ._time import TIME_KEY
from ._utils import condition_with_prefix


class RegisterError(Exception):
    '''Raised when a condition cannot be registered with a Checker.'''
    pass


class FirstPartyCaveatChecker(object):
    '''Used to check first party caveats for validity with respect to
    information in the provided context.

    If the caveat kind was not recognised, the checker should return
    ErrCaveatNotRecognized.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def check_first_party_caveat(self, ctx, caveat):
        '''	Checks that the given caveat condition is valid with respect to
        the given context information.
        :param ctx: an Auth context
        :param caveat a string
        '''
        raise NotImplementedError('check_first_party_caveat method must be '
                                  'defined in subclass')

    def namespace(self):
        '''	Returns the namespace associated with the caveat checker.
        '''
        raise NotImplementedError('namespace method must be '
                                  'defined in subclass')


class Checker(FirstPartyCaveatChecker):
    ''' Holds a set of checkers for first party caveats.
    '''

    def __init__(self, namespace=None, include_std_checkers=True):
        if namespace is None:
            namespace = Namespace()
        self._namespace = namespace
        self._checkers = {}
        if include_std_checkers:
            self.register_std()

    def check_first_party_caveat(self, ctx, cav):
        ''' Checks the caveat against all registered caveat conditions.
        :return: error message string if any or None
        '''
        try:
            cond, arg = parse_caveat(cav)
        except ValueError as ex:
            # If we can't parse it, perhaps it's in some other format,
            # return a not-recognised error.
            return 'cannot parse caveat "{}": {}'.format(cav, ex.args[0])
        checker = self._checkers.get(cond)
        if checker is None:
            return 'caveat "{}" not satisfied: caveat not recognized'.format(
                cav)
        err = checker.check(ctx, cond, arg)
        if err is not None:
            return 'caveat "{}" not satisfied: {}'.format(cav, err)

    def namespace(self):
        ''' Returns the namespace associated with the Checker.
        '''
        return self._namespace

    def info(self):
        ''' Returns information on all the registered checkers.

        Sorted by namespace and then name
        :returns a list of CheckerInfo
        '''
        return sorted(self._checkers.values(), key=lambda x: (x.ns, x.name))

    def register(self, cond, uri, check):
        ''' Registers the given condition(string) in the given namespace
        uri (string) to be checked with the given check function.
        The check function checks a caveat by passing an auth context, a cond
        parameter(string) that holds the caveat condition including any
        namespace prefix and an arg parameter(string) that hold any additional
        caveat argument text. It will return any error as string otherwise
        None.

        It will raise a ValueError if the namespace is not registered or
        if the condition has already been registered.
        '''
        if check is None:
            raise RegisterError(
                'no check function registered for namespace {} when '
                'registering condition {}'.format(uri, cond))

        prefix = self._namespace.resolve(uri)
        if prefix is None:
            raise RegisterError('no prefix registered for namespace {} when '
                                'registering condition {}'.format(uri, cond))

        if prefix == '' and cond.find(':') >= 0:
            raise RegisterError(
                'caveat condition {} in namespace {} contains a colon but its'
                ' prefix is empty'.format(cond, uri))

        full_cond = condition_with_prefix(prefix, cond)
        info = self._checkers.get(full_cond)
        if info is not None:
            raise RegisterError(
                'checker for {} (namespace {}) already registered in '
                'namespace {}'.format(full_cond, uri, info.ns))
        self._checkers[full_cond] = CheckerInfo(
            check=check,
            ns=uri,
            name=cond,
            prefix=prefix)

    def register_std(self):
        ''' Registers all the standard checkers in the given checker.

        If not present already, the standard checkers schema (STD_NAMESPACE) is
        added to the checker's namespace with an empty prefix.
        '''
        self._namespace.register(STD_NAMESPACE, '')
        for cond in _ALL_CHECKERS:
            self.register(cond, STD_NAMESPACE, _ALL_CHECKERS[cond])


class CheckerInfo(namedtuple('CheckInfo', 'prefix name ns check')):
    '''CheckerInfo holds information on a registered checker.
    '''
    __slots__ = ()

    def __new__(cls, prefix, name, ns, check=None):
        '''
        :param check holds the actual checker function which takes an auth
        context and a condition and arg string as arguments.
        :param prefix holds the prefix for the checker condition as string.
        :param name holds the name of the checker condition as string.
        :param ns holds the namespace URI for the checker's schema as
        Namespace.
        '''
        return super(CheckerInfo, cls).__new__(cls, prefix, name, ns, check)


def _check_time_before(ctx, cond, arg):
    clock = ctx.get(TIME_KEY)
    if clock is None:
        now = datetime.utcnow()
    else:
        now = clock.utcnow()

    try:
        # Note: pyrfc3339 returns a datetime with a timezone, which
        # we need to remove before we can compare it with the naive
        # datetime object returned by datetime.utcnow.
        expiry = pyrfc3339.parse(arg, utc=True).replace(tzinfo=None)
        if now >= expiry:
            return 'macaroon has expired'
    except ValueError:
        return 'cannot parse "{}" as RFC 3339'.format(arg)
    return None


def _check_declared(ctx, cond, arg):
    parts = arg.split(' ', 1)
    if len(parts) != 2:
        return 'declared caveat has no value'
    attrs = ctx.get(DECLARED_KEY, {})
    val = attrs.get(parts[0])
    if val is None:
        return 'got {}=null, expected "{}"'.format(parts[0], parts[1])

    if val != parts[1]:
        return 'got {}="{}", expected "{}"'.format(parts[0], val, parts[1])
    return None


def _check_error(ctx, cond, arg):
    return 'bad caveat'


def _check_allow(ctx, cond, arg):
    return _check_operations(ctx, True, arg)


def _check_deny(ctx, cond, arg):
    return _check_operations(ctx, False, arg)


def _check_operations(ctx, need_ops, arg):
    ''' Checks an allow or a deny caveat. The need_ops parameter specifies
    whether we require all the operations in the caveat to be declared in
    the context.
    '''
    ctx_ops = ctx.get(OP_KEY, [])
    if len(ctx_ops) == 0:
        if need_ops:
            f = arg.split()
            if len(f) == 0:
                return 'no operations allowed'
            return '{} not allowed'.format(f[0])
        return None

    fields = arg.split()
    for op in ctx_ops:
        err = _check_op(op, need_ops, fields)
        if err is not None:
            return err
    return None


def _check_op(ctx_op, need_op, fields):
    found = False
    for op in fields:
        if op == ctx_op:
            found = True
            break
    if found != need_op:
        return '{} not allowed'.format(ctx_op)
    return None


_ALL_CHECKERS = {
    COND_TIME_BEFORE: _check_time_before,
    COND_DECLARED: _check_declared,
    COND_ERROR: _check_error,
    COND_ALLOW: _check_allow,
    COND_DENY: _check_deny,
}
