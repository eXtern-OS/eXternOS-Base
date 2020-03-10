# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.

import pyrfc3339
from ._auth_context import ContextKey
from ._caveat import parse_caveat
from ._conditions import COND_TIME_BEFORE, STD_NAMESPACE
from ._utils import condition_with_prefix

TIME_KEY = ContextKey('time-key')


def context_with_clock(ctx, clock):
    ''' Returns a copy of ctx with a key added that associates it with the
    given clock implementation, which will be used by the time-before checker
    to determine the current time.
    The clock should have a utcnow method that returns the current time
    as a datetime value in UTC.
    '''
    if clock is None:
        return ctx
    return ctx.with_value(TIME_KEY, clock)


def macaroons_expiry_time(ns, ms):
    ''' Returns the minimum time of any time-before caveats found in the given
    macaroons or None if no such caveats were found.
    :param ns: a Namespace, used to resolve caveats.
    :param ms: a list of pymacaroons.Macaroon
    :return: datetime.DateTime or None.
    '''
    t = None
    for m in ms:
        et = expiry_time(ns, m.caveats)
        if et is not None and (t is None or et < t):
            t = et
    return t


def expiry_time(ns, cavs):
    ''' Returns the minimum time of any time-before caveats found
    in the given list or None if no such caveats were found.

    The ns parameter is
    :param ns: used to determine the standard namespace prefix - if
    the standard namespace is not found, the empty prefix is assumed.
    :param cavs: a list of pymacaroons.Caveat
    :return: datetime.DateTime or None.
    '''
    prefix = ns.resolve(STD_NAMESPACE)
    time_before_cond = condition_with_prefix(
        prefix, COND_TIME_BEFORE)
    t = None
    for cav in cavs:
        if not cav.first_party():
            continue
        cav = cav.caveat_id_bytes.decode('utf-8')
        name, rest = parse_caveat(cav)
        if name != time_before_cond:
            continue
        try:
            et = pyrfc3339.parse(rest, utc=True).replace(tzinfo=None)
            if t is None or et < t:
                t = et
        except ValueError:
            continue
    return t
