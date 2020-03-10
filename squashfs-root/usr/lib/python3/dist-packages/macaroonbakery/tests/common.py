# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
from datetime import datetime, timedelta

import macaroonbakery.bakery as bakery
import macaroonbakery.checkers as checkers


class _StoppedClock(object):
    def __init__(self, t):
        self.t = t

    def utcnow(self):
        return self.t


epoch = datetime(year=1900, month=11, day=17, hour=19, minute=00, second=13)
ages = epoch + timedelta(days=1)

test_context = checkers.context_with_clock(checkers.AuthContext(),
                                           _StoppedClock(epoch))


def test_checker():
    c = checkers.Checker()
    c.namespace().register('testns', '')
    c.register('str', 'testns', str_check)
    c.register('true', 'testns', true_check)
    return c


_str_key = checkers.ContextKey('str_check')


def str_context(s):
    return test_context.with_value(_str_key, s)


def str_check(ctx, cond, args):
    expect = ctx[_str_key]
    if args != expect:
        return '{} doesn\'t match {}'.format(cond, expect)
    return None


def true_check(ctx, cond, args):
    # Always succeeds.
    return None


class OneIdentity(bakery.IdentityClient):
    '''An IdentityClient implementation that always returns a single identity
    from declared_identity, allowing allow(LOGIN_OP) to work even when there
    are no declaration caveats (this is mostly to support the legacy tests
    which do their own checking of declaration caveats).
    '''

    def identity_from_context(self, ctx):
        return None, None

    def declared_identity(self, ctx, declared):
        return _NoOne()


class _NoOne(object):
    def id(self):
        return 'noone'

    def domain(self):
        return ''


class ThirdPartyStrcmpChecker(bakery.ThirdPartyCaveatChecker):
    def __init__(self, str):
        self.str = str

    def check_third_party_caveat(self, ctx, cav_info):
        condition = cav_info.condition
        if isinstance(cav_info.condition, bytes):
            condition = cav_info.condition.decode('utf-8')
        if condition != self.str:
            raise bakery.ThirdPartyCaveatCheckFailed(
                '{} doesn\'t match {}'.format(condition, self.str))
        return []


class ThirdPartyCheckerWithCaveats(bakery.ThirdPartyCaveatChecker):
    def __init__(self, cavs=None):
        if cavs is None:
            cavs = []
        self.cavs = cavs

    def check_third_party_caveat(self, ctx, cav_info):
        return self.cavs


class ThirdPartyCaveatCheckerEmpty(bakery.ThirdPartyCaveatChecker):
    def check_third_party_caveat(self, ctx, cav_info):
        return []


def new_bakery(location, locator=None):
    # Returns a new Bakery instance using a new
    # key pair, and registers the key with the given locator if provided.
    #
    # It uses test_checker to check first party caveats.
    key = bakery.generate_key()
    if locator is not None:
        locator.add_info(location,
                         bakery.ThirdPartyInfo(
                             public_key=key.public_key,
                             version=bakery.LATEST_VERSION))
    return bakery.Bakery(
        key=key,
        checker=test_checker(),
        location=location,
        identity_client=OneIdentity(),
        locator=locator,
    )
