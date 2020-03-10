# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
from collections import namedtuple
from datetime import timedelta
from unittest import TestCase

import macaroonbakery.checkers as checkers
import pymacaroons
import pyrfc3339
from pymacaroons import Macaroon

t1 = pyrfc3339.parse('2017-10-26T16:19:47.441402074Z', produce_naive=True)
t2 = t1 + timedelta(hours=1)
t3 = t2 + timedelta(hours=1)


def fpcaveat(s):
    return pymacaroons.Caveat(caveat_id=s.encode('utf-8'))


class TestExpireTime(TestCase):
    def test_expire_time(self):
        ExpireTest = namedtuple('ExpireTest', 'about caveats expectTime')
        tests = [
            ExpireTest(
                about='no caveats',
                caveats=[],
                expectTime=None,
            ),
            ExpireTest(
                about='single time-before caveat',
                caveats=[
                    fpcaveat(checkers.time_before_caveat(t1).condition),
                ],
                expectTime=t1,
            ),
            ExpireTest(
                about='multiple time-before caveat',
                caveats=[
                    fpcaveat(checkers.time_before_caveat(t2).condition),
                    fpcaveat(checkers.time_before_caveat(t1).condition),
                ],
                expectTime=t1,
            ),
            ExpireTest(
                about='mixed caveats',
                caveats=[
                    fpcaveat(checkers.time_before_caveat(t1).condition),
                    fpcaveat('allow bar'),
                    fpcaveat(checkers.time_before_caveat(t2).condition),
                    fpcaveat('deny foo'),
                ],
                expectTime=t1,
            ),
            ExpireTest(
                about='mixed caveats',
                caveats=[
                    fpcaveat(checkers.COND_TIME_BEFORE + ' tomorrow'),
                ],
                expectTime=None,
            ),
        ]
        for test in tests:
            print('test ', test.about)
            t = checkers.expiry_time(checkers.Namespace(), test.caveats)
            self.assertEqual(t, test.expectTime)

    def test_macaroons_expire_time(self):
        ExpireTest = namedtuple('ExpireTest', 'about macaroons expectTime')
        tests = [
            ExpireTest(
                about='no macaroons',
                macaroons=[newMacaroon()],
                expectTime=None,
            ),
            ExpireTest(
                about='single macaroon without caveats',
                macaroons=[newMacaroon()],
                expectTime=None,
            ),
            ExpireTest(
                about='multiple macaroon without caveats',
                macaroons=[newMacaroon()],
                expectTime=None,
            ),
            ExpireTest(
                about='single macaroon with time-before caveat',
                macaroons=[
                    newMacaroon([checkers.time_before_caveat(t1).condition]),
                ],
                expectTime=t1,
            ),
            ExpireTest(
                about='single macaroon with multiple time-before caveats',
                macaroons=[
                    newMacaroon([
                        checkers.time_before_caveat(t2).condition,
                        checkers.time_before_caveat(t1).condition,
                    ]),
                ],
                expectTime=t1,
            ),
            ExpireTest(
                about='multiple macaroons with multiple time-before caveats',
                macaroons=[
                    newMacaroon([
                        checkers.time_before_caveat(t3).condition,
                        checkers.time_before_caveat(t1).condition,
                    ]),
                    newMacaroon([
                        checkers.time_before_caveat(t3).condition,
                        checkers.time_before_caveat(t1).condition,
                    ]),
                ],
                expectTime=t1,
            ),
        ]
        for test in tests:
            print('test ', test.about)
            t = checkers.macaroons_expiry_time(checkers.Namespace(),
                                               test.macaroons)
            self.assertEqual(t, test.expectTime)

    def test_macaroons_expire_time_skips_third_party(self):
        m1 = newMacaroon([checkers.time_before_caveat(t1).condition])
        m2 = newMacaroon()
        m2.add_third_party_caveat('https://example.com', 'a-key', '123')
        t = checkers.macaroons_expiry_time(checkers.Namespace(), [m1, m2])
        self.assertEqual(t1, t)


def newMacaroon(conds=[]):
    m = Macaroon(key='key', version=2)
    for cond in conds:
        m.add_first_party_caveat(cond)
    return m
