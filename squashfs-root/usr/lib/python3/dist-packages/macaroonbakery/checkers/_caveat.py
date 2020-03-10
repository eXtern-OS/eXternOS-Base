# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import collections

import pyrfc3339
from ._conditions import (
    COND_ALLOW,
    COND_DECLARED,
    COND_DENY,
    COND_ERROR,
    COND_TIME_BEFORE,
    STD_NAMESPACE,
)


class Caveat(collections.namedtuple('Caveat', 'condition location namespace')):
    '''Represents a condition that must be true for a check to complete
    successfully.

    If location is provided, the caveat must be discharged by
    a third party at the given location (a URL string).

    The namespace parameter holds the namespace URI string of the
    condition - if it is provided, it will be converted to a namespace prefix
    before adding to the macaroon.
    '''
    __slots__ = ()

    def __new__(cls, condition, location=None, namespace=None):
        return super(Caveat, cls).__new__(cls, condition, location, namespace)


def declared_caveat(key, value):
    '''Returns a "declared" caveat asserting that the given key is
    set to the given value.

    If a macaroon has exactly one first party caveat asserting the value of a
    particular key, then infer_declared will be able to infer the value, and
    then the check will allow the declared value if it has the value
    specified here.

    If the key is empty or contains a space, it will return an error caveat.
    '''
    if key.find(' ') >= 0 or key == '':
        return error_caveat('invalid caveat \'declared\' key "{}"'.format(key))
    return _first_party(COND_DECLARED, key + ' ' + value)


def error_caveat(f):
    '''Returns a caveat that will never be satisfied, holding f as the text of
    the caveat.

    This should only be used for highly unusual conditions that are never
    expected to happen in practice, such as a malformed key that is
    conventionally passed as a constant. It's not a panic but you should
    only use it in cases where a panic might possibly be appropriate.

    This mechanism means that caveats can be created without error
    checking and a later systematic check at a higher level (in the
    bakery package) can produce an error instead.
    '''
    return _first_party(COND_ERROR, f)


def allow_caveat(ops):
    ''' Returns a caveat that will deny attempts to use the macaroon to perform
    any operation other than those listed. Operations must not contain a space.
    '''
    if ops is None or len(ops) == 0:
        return error_caveat('no operations allowed')
    return _operation_caveat(COND_ALLOW, ops)


def deny_caveat(ops):
    '''Returns a caveat that will deny attempts to use the macaroon to perform
    any of the listed operations. Operations must not contain a space.
    '''
    return _operation_caveat(COND_DENY, ops)


def _operation_caveat(cond, ops):
    ''' Helper for allow_caveat and deny_caveat.

    It checks that all operation names are valid before creating the caveat.
    '''
    for op in ops:
        if op.find(' ') != -1:
            return error_caveat('invalid operation name "{}"'.format(op))
    return _first_party(cond, ' '.join(ops))


def time_before_caveat(t):
    '''Return a caveat that specifies that the time that it is checked at
    should be before t.
    :param t is a a UTC date in - use datetime.utcnow, not datetime.now
    '''

    return _first_party(COND_TIME_BEFORE,
                        pyrfc3339.generate(t, accept_naive=True,
                                           microseconds=True))


def parse_caveat(cav):
    ''' Parses a caveat into an identifier, identifying the checker that should
    be used, and the argument to the checker (the rest of the string).

    The identifier is taken from all the characters before the first
    space character.
    :return two string, identifier and arg
    '''
    if cav == '':
        raise ValueError('empty caveat')
    try:
        i = cav.index(' ')
    except ValueError:
        return cav, ''
    if i == 0:
        raise ValueError('caveat starts with space character')
    return cav[0:i], cav[i + 1:]


def _first_party(name, arg):
    condition = name
    if arg != '':
        condition += ' ' + arg

    return Caveat(condition=condition,
                  namespace=STD_NAMESPACE)
