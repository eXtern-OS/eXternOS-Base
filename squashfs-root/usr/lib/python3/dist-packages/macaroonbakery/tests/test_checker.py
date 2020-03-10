# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import base64
import json
from collections import namedtuple
from datetime import timedelta
from unittest import TestCase

import macaroonbakery.bakery as bakery
import macaroonbakery.checkers as checkers
import pymacaroons
from macaroonbakery.tests.common import epoch, test_checker, test_context
from pymacaroons.verifier import FirstPartyCaveatVerifierDelegate, Verifier


class TestChecker(TestCase):
    def setUp(self):
        self._discharges = []

    def test_authorize_with_open_access_and_no_macaroons(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer(
            {bakery.Op(entity='something', action='read'):
                {bakery.EVERYONE}})
        ts = _Service('myservice', auth, ids, locator)
        client = _Client(locator)
        auth_info = client.do(test_context, ts, [
            bakery.Op(entity='something', action='read'),
        ])
        self.assertEqual(len(self._discharges), 0)
        self.assertIsNotNone(auth_info)
        self.assertIsNone(auth_info.identity)
        self.assertEqual(len(auth_info.macaroons), 0)

    def test_authorization_denied(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = bakery.ClosedAuthorizer()
        ts = _Service('myservice', auth, ids, locator)
        client = _Client(locator)
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        with self.assertRaises(bakery.PermissionDenied):
            client.do(ctx, ts, [bakery.Op(entity='something', action='read')])

    def test_authorize_with_authentication_required(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer(
            {bakery.Op(entity='something', action='read'): {'bob'}})
        ts = _Service('myservice', auth, ids, locator)
        client = _Client(locator)

        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        auth_info = client.do(ctx, ts, [bakery.Op(entity='something',
                                                  action='read')])
        self.assertEqual(self._discharges,
                         [_DischargeRecord(location='ids', user='bob')])
        self.assertIsNotNone(auth_info)
        self.assertEqual(auth_info.identity.id(), 'bob')
        self.assertEqual(len(auth_info.macaroons), 1)

    def test_authorize_multiple_ops(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer(
            {
                bakery.Op(entity='something', action='read'): {'bob'},
                bakery.Op(entity='otherthing', action='read'): {'bob'}
            }
        )
        ts = _Service('myservice', auth, ids, locator)
        client = _Client(locator)
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        client.do(ctx, ts, [
            bakery.Op(entity='something', action='read'),
            bakery.Op(entity='otherthing', action='read')
        ])
        self.assertEqual(self._discharges,
                         [_DischargeRecord(location='ids', user='bob')])

    def test_capability(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer(
            {bakery.Op(entity='something', action='read'): {'bob'}})
        ts = _Service('myservice', auth, ids, locator)
        client = _Client(locator)

        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        m = client.discharged_capability(
            ctx, ts, [bakery.Op(entity='something', action='read')])
        # Check that we can exercise the capability directly on the service
        # with no discharging required.
        auth_info = ts.do(test_context, [m], [
            bakery.Op(entity='something', action='read'),
        ])
        self.assertIsNotNone(auth_info)
        self.assertIsNone(auth_info.identity)
        self.assertEqual(len(auth_info.macaroons), 1)
        self.assertEqual(auth_info.macaroons[0][0].identifier_bytes,
                         m[0].identifier_bytes)

    def test_capability_multiple_entities(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer({
            bakery.Op(entity='e1', action='read'): {'bob'},
            bakery.Op(entity='e2', action='read'): {'bob'},
            bakery.Op(entity='e3', action='read'): {'bob'},
        })
        ts = _Service('myservice', auth, ids, locator)
        client = _Client(locator)
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        m = client.discharged_capability(ctx, ts, [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e2', action='read'),
            bakery.Op(entity='e3', action='read'),
        ])
        self.assertEqual(self._discharges,
                         [_DischargeRecord(location='ids', user='bob')])

        # Check that we can exercise the capability directly on the service
        # with no discharging required.
        ts.do(test_context, [m], [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e2', action='read'),
            bakery.Op(entity='e3', action='read'),
        ])

        # Check that we can exercise the capability to act on a subset of
        # the operations.
        ts.do(test_context, [m], [
            bakery.Op(entity='e2', action='read'),
            bakery.Op(entity='e3', action='read'),
        ])
        ts.do(test_context, [m],
              [bakery.Op(entity='e3', action='read')])

    def test_multiple_capabilities(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer({
            bakery.Op(entity='e1', action='read'): {'alice'},
            bakery.Op(entity='e2', action='read'): {'bob'},
        })
        ts = _Service('myservice', auth, ids, locator)

        # Acquire two capabilities as different users and check
        # that we can combine them together to do both operations
        # at once.
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'alice')
        m1 = _Client(locator).discharged_capability(ctx, ts, [
            bakery.Op(entity='e1', action='read'),
        ])
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        m2 = _Client(locator).discharged_capability(ctx, ts,
                                                    [bakery.Op(
                                                        entity='e2',
                                                        action='read')])
        self.assertEqual(self._discharges, [
            _DischargeRecord(location='ids', user='alice'),
            _DischargeRecord(location='ids', user='bob'),
        ])
        auth_info = ts.do(test_context, [m1, m2], [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e2', action='read'),
        ])
        self.assertIsNotNone(auth_info)
        self.assertIsNone(auth_info.identity)
        self.assertEqual(len(auth_info.macaroons), 2)
        self.assertEqual(auth_info.macaroons[0][0].identifier_bytes,
                         m1[0].identifier_bytes)
        self.assertEqual(auth_info.macaroons[1][0].identifier_bytes,
                         m2[0].identifier_bytes)

    def test_combine_capabilities(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer({
            bakery.Op(entity='e1', action='read'): {'alice'},
            bakery.Op(entity='e2', action='read'): {'bob'},
            bakery.Op(entity='e3', action='read'): {'bob', 'alice'},
        })
        ts = _Service('myservice', auth, ids, locator)

        # Acquire two capabilities as different users and check
        # that we can combine them together into a single capability
        # capable of both operations.
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'alice')
        m1 = _Client(locator).discharged_capability(ctx, ts, [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e3', action='read'),
        ])
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        m2 = _Client(locator).discharged_capability(
            ctx, ts, [bakery.Op(entity='e2', action='read')])

        m = ts.capability(test_context, [m1, m2], [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e2', action='read'),
            bakery.Op(entity='e3', action='read'),
        ])
        ts.do(test_context, [[m.macaroon]], [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e2', action='read'),
            bakery.Op(entity='e3', action='read'),
        ])

    def test_partially_authorized_request(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer({
            bakery.Op(entity='e1', action='read'): {'alice'},
            bakery.Op(entity='e2', action='read'): {'bob'},
        })
        ts = _Service('myservice', auth, ids, locator)

        # Acquire a capability for e1 but rely on authentication to
        # authorize e2.
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'alice')
        m = _Client(locator).discharged_capability(ctx, ts, [
            bakery.Op(entity='e1', action='read'),
        ])
        client = _Client(locator)
        client.add_macaroon(ts, 'authz', m)

        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        client.discharged_capability(ctx, ts, [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e2', action='read'),
        ])

    def test_auth_with_third_party_caveats(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)

        # We make an authorizer that requires a third party discharge
        # when authorizing.
        def authorize_with_tp_discharge(ctx, id, op):
            if (id is not None and id.id() == 'bob' and
                    op == bakery.Op(entity='something', action='read')):
                return True, [checkers.Caveat(condition='question',
                                              location='other third party')]
            return False, None

        auth = bakery.AuthorizerFunc(authorize_with_tp_discharge)
        ts = _Service('myservice', auth, ids, locator)

        class _LocalDischargeChecker(bakery.ThirdPartyCaveatChecker):
            def check_third_party_caveat(_, ctx, info):
                if info.condition != 'question':
                    raise ValueError('third party condition not recognized')
                self._discharges.append(_DischargeRecord(
                    location='other third party',
                    user=ctx.get(_DISCHARGE_USER_KEY)
                ))
                return []

        locator['other third party'] = _Discharger(
            key=bakery.generate_key(),
            checker=_LocalDischargeChecker(),
            locator=locator,
        )
        client = _Client(locator)
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        client.do(ctx, ts, [bakery.Op(entity='something', action='read')])
        self.assertEqual(self._discharges, [
            _DischargeRecord(location='ids', user='bob'),
            _DischargeRecord(location='other third party', user='bob')
        ])

    def test_capability_combines_first_party_caveats(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer({
            bakery.Op(entity='e1', action='read'): {'alice'},
            bakery.Op(entity='e2', action='read'): {'bob'},
        })
        ts = _Service('myservice', auth, ids, locator)

        # Acquire two capabilities as different users, add some first party
        # caveats that we can combine them together into a single capability
        # capable of both operations.
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'alice')
        m1 = _Client(locator).capability(
            ctx, ts, [bakery.Op(entity='e1', action='read')])
        m1.macaroon.add_first_party_caveat('true 1')
        m1.macaroon.add_first_party_caveat('true 2')
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        m2 = _Client(locator).capability(
            ctx, ts, [bakery.Op(entity='e2', action='read')])
        m2.macaroon.add_first_party_caveat('true 3')
        m2.macaroon.add_first_party_caveat('true 4')

        client = _Client(locator)
        client.add_macaroon(ts, 'authz1', [m1.macaroon])
        client.add_macaroon(ts, 'authz2', [m2.macaroon])

        m = client.capability(test_context, ts, [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e2', action='read'),
        ])
        self.assertEqual(_macaroon_conditions(m.macaroon.caveats, False), [
            'true 1',
            'true 2',
            'true 3',
            'true 4',
        ])

    def test_first_party_caveat_squashing(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer({
            bakery.Op(entity='e1', action='read'): {'alice'},
            bakery.Op(entity='e2', action='read'): {'alice'},
        })
        ts = _Service('myservice', auth, ids, locator)
        tests = [
            ('duplicates removed', [
                checkers.Caveat(condition='true 1', namespace='testns'),
                checkers.Caveat(condition='true 2', namespace='testns'),
                checkers.Caveat(condition='true 1', namespace='testns'),
                checkers.Caveat(condition='true 1', namespace='testns'),
                checkers.Caveat(condition='true 3', namespace='testns'),
            ], [
                checkers.Caveat(condition='true 1', namespace='testns'),
                checkers.Caveat(condition='true 2', namespace='testns'),
                checkers.Caveat(condition='true 3', namespace='testns'),
            ]), ('earliest time before', [
                checkers.time_before_caveat(epoch + timedelta(days=1)),
                checkers.Caveat(condition='true 1', namespace='testns'),
                checkers.time_before_caveat(
                    epoch + timedelta(days=0, hours=1)),
                checkers.time_before_caveat(epoch + timedelta(
                    days=0, hours=0, minutes=5)),
            ], [
                checkers.time_before_caveat(epoch + timedelta(
                    days=0, hours=0, minutes=5)),
                checkers.Caveat(condition='true 1', namespace='testns'),
            ]), ('operations and declared caveats removed', [
                checkers.deny_caveat(['foo']),
                checkers.allow_caveat(['read', 'write']),
                checkers.declared_caveat('username', 'bob'),
                checkers.Caveat(condition='true 1', namespace='testns'),
            ], [
                checkers.Caveat(condition='true 1', namespace='testns'),
            ])
        ]
        for test in tests:
            print(test[0])

            # Make a first macaroon with all the required first party caveats.
            ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'alice')
            m1 = _Client(locator).capability(
                ctx, ts, [bakery.Op(entity='e1', action='read')])
            m1.add_caveats(test[1], None, None)

            # Make a second macaroon that's not used to check that it's
            # caveats are not added.
            m2 = _Client(locator).capability(
                ctx, ts, [bakery.Op(entity='e1', action='read')])
            m2.add_caveat(checkers.Caveat(
                condition='true notused', namespace='testns'), None, None)
            client = _Client(locator)
            client.add_macaroon(ts, 'authz1', [m1.macaroon])
            client.add_macaroon(ts, 'authz2', [m2.macaroon])

            m3 = client.capability(
                test_context, ts, [bakery.Op(entity='e1', action='read')])
            self.assertEqual(
                _macaroon_conditions(m3.macaroon.caveats, False),
                _resolve_caveats(m3.namespace, test[2]))

    def test_login_only(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = bakery.ClosedAuthorizer()
        ts = _Service('myservice', auth, ids, locator)

        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        auth_info = _Client(locator).do(ctx, ts, [bakery.LOGIN_OP])
        self.assertIsNotNone(auth_info)
        self.assertEqual(auth_info.identity.id(), 'bob')

    def test_allow_any(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer(
            {
                bakery.Op(entity='e1', action='read'): {'alice'},
                bakery.Op(entity='e2', action='read'): {'bob'},
            })
        ts = _Service('myservice', auth, ids, locator)

        # Acquire a capability for e1 but rely on authentication to
        # authorize e2.
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'alice')
        m = _Client(locator).discharged_capability(ctx, ts, [
            bakery.Op(entity='e1', action='read'),
        ])

        client = _Client(locator)
        client.add_macaroon(ts, 'authz', m)

        self._discharges = []
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        with self.assertRaises(_DischargeRequiredError):
            client.do_any(
                ctx, ts, [
                    bakery.LOGIN_OP,
                    bakery.Op(entity='e1', action='read'),
                    bakery.Op(entity='e1', action='read')
                ]
            )
            self.assertEqual(len(self._discharges), 0)

        # Log in as bob.
        _, err = client.do(ctx, ts, [bakery.LOGIN_OP])

        # All the previous actions should now be allowed.
        auth_info, allowed = client.do_any(ctx, ts, [
            bakery.LOGIN_OP,
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e1', action='read'),
        ])
        self.assertEqual(auth_info.identity.id(), 'bob')
        self.assertEqual(len(auth_info.macaroons), 2)
        self.assertEqual(allowed, [True, True, True])

    def test_auth_with_identity_from_context(self):
        locator = _DischargerLocator()
        ids = _BasicAuthIdService()
        auth = _OpAuthorizer({
            bakery.Op(entity='e1', action='read'): {'sherlock'},
            bakery.Op(entity='e2', action='read'): {'bob'},
        })
        ts = _Service('myservice', auth, ids, locator)

        # Check that we can perform the ops with basic auth in the
        # context.
        ctx = _context_with_basic_auth(test_context, 'sherlock', 'holmes')
        auth_info = _Client(locator).do(
            ctx, ts, [bakery.Op(entity='e1', action='read')])
        self.assertEqual(auth_info.identity.id(), 'sherlock')
        self.assertEqual(len(auth_info.macaroons), 0)

    def test_auth_login_op_with_identity_from_context(self):
        locator = _DischargerLocator()
        ids = _BasicAuthIdService()
        ts = _Service('myservice', bakery.ClosedAuthorizer(), ids, locator)

        # Check that we can use LoginOp
        # when auth isn't granted through macaroons.
        ctx = _context_with_basic_auth(test_context, 'sherlock', 'holmes')
        auth_info = _Client(locator).do(ctx, ts, [bakery.LOGIN_OP])
        self.assertEqual(auth_info.identity.id(), 'sherlock')
        self.assertEqual(len(auth_info.macaroons), 0)

    def test_operation_allow_caveat(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer({
            bakery.Op(entity='e1', action='read'): {'bob'},
            bakery.Op(entity='e1', action='write'): {'bob'},
            bakery.Op(entity='e2', action='read'): {'bob'},
        })
        ts = _Service('myservice', auth, ids, locator)
        client = _Client(locator)

        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        m = client.capability(ctx, ts, [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e1', action='write'),
            bakery.Op(entity='e2', action='read'),
        ])

        # Sanity check that we can do a write.
        ts.do(test_context, [[m.macaroon]],
              [bakery.Op(entity='e1', action='write')])

        m.add_caveat(checkers.allow_caveat(['read']), None, None)

        # A read operation should work.
        ts.do(test_context, [[m.macaroon]], [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e2', action='read'),
        ])

        # A write operation should fail
        # even though the original macaroon allowed it.
        with self.assertRaises(_DischargeRequiredError):
            ts.do(test_context, [[m.macaroon]], [
                bakery.Op(entity='e1', action='write'),
            ])

    def test_operation_deny_caveat(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = _OpAuthorizer({
            bakery.Op(entity='e1', action='read'): {'bob'},
            bakery.Op(entity='e1', action='write'): {'bob'},
            bakery.Op(entity='e2', action='read'): {'bob'},
        })
        ts = _Service('myservice', auth, ids, locator)
        client = _Client(locator)

        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        m = client.capability(ctx, ts, [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e1', action='write'),
            bakery.Op(entity='e2', action='read'),
        ])

        # Sanity check that we can do a write.
        ts.do(test_context, [[m.macaroon]], [
              bakery.Op(entity='e1', action='write')])

        m.add_caveat(checkers.deny_caveat(['write']), None, None)

        # A read operation should work.
        ts.do(test_context, [[m.macaroon]], [
            bakery.Op(entity='e1', action='read'),
            bakery.Op(entity='e2', action='read'),
        ])

        # A write operation should fail
        # even though the original macaroon allowed it.
        with self.assertRaises(_DischargeRequiredError):
            ts.do(test_context, [[m.macaroon]], [
                  bakery.Op(entity='e1', action='write')])

    def test_duplicate_login_macaroons(self):
        locator = _DischargerLocator()
        ids = _IdService('ids', locator, self)
        auth = bakery.ClosedAuthorizer()
        ts = _Service('myservice', auth, ids, locator)

        # Acquire a login macaroon for bob.
        client1 = _Client(locator)
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'bob')
        auth_info = client1.do(ctx, ts, [bakery.LOGIN_OP])
        self.assertEqual(auth_info.identity.id(), 'bob')

        # Acquire a login macaroon for alice.
        client2 = _Client(locator)
        ctx = test_context.with_value(_DISCHARGE_USER_KEY, 'alice')
        auth_info = client2.do(ctx, ts, [bakery.LOGIN_OP])
        self.assertEqual(auth_info.identity.id(), 'alice')

        # Combine the two login macaroons into one client.
        client3 = _Client(locator)
        client3.add_macaroon(ts, '1.bob',
                             client1._macaroons[ts.name()]['authn'])
        client3.add_macaroon(ts, '2.alice',
                             client2._macaroons[ts.name()]['authn'])

        # We should authenticate as bob (because macaroons are presented
        # ordered by "cookie" name)
        auth_info = client3.do(test_context, ts, [bakery.LOGIN_OP])
        self.assertEqual(auth_info.identity.id(), 'bob')
        self.assertEqual(len(auth_info.macaroons), 1)

        # Try them the other way around and we should authenticate as alice.
        client3 = _Client(locator)
        client3.add_macaroon(ts, '1.alice',
                             client2._macaroons[ts.name()]['authn'])
        client3.add_macaroon(ts, '2.bob',
                             client1._macaroons[ts.name()]['authn'])

        auth_info = client3.do(test_context, ts, [bakery.LOGIN_OP])
        self.assertEqual(auth_info.identity.id(), 'alice')
        self.assertEqual(len(auth_info.macaroons), 1)

    def test_macaroon_ops_fatal_error(self):
        # When we get a non-VerificationError error from the
        # opstore, we don't do any more verification.
        checker = bakery.Checker(
            macaroon_opstore=_MacaroonStoreWithError())
        m = pymacaroons.Macaroon(version=pymacaroons.MACAROON_V2)
        with self.assertRaises(bakery.AuthInitError):
            checker.auth([m]).allow(test_context, [bakery.LOGIN_OP])


class _DischargerLocator(bakery.ThirdPartyLocator):
    def __init__(self, dischargers=None):
        if dischargers is None:
            dischargers = {}
        self._dischargers = dischargers

    def third_party_info(self, loc):
        d = self._dischargers.get(loc)
        if d is None:
            return None
        return bakery.ThirdPartyInfo(
            public_key=d._key.public_key,
            version=bakery.LATEST_VERSION,
        )

    def __setitem__(self, key, item):
        self._dischargers[key] = item

    def __getitem__(self, key):
        return self._dischargers[key]

    def get(self, key):
        return self._dischargers.get(key)


class _IdService(bakery.IdentityClient,
                 bakery.ThirdPartyCaveatChecker):
    def __init__(self, location, locator, test_class):
        self._location = location
        self._test = test_class
        key = bakery.generate_key()
        self._discharger = _Discharger(key=key, checker=self, locator=locator)
        locator[location] = self._discharger

    def check_third_party_caveat(self, ctx, info):
        if info.condition != 'is-authenticated-user':
            raise bakery.CaveatNotRecognizedError(
                'third party condition not recognized')

        username = ctx.get(_DISCHARGE_USER_KEY, '')
        if username == '':
            raise bakery.ThirdPartyCaveatCheckFailed('no current user')
        self._test._discharges.append(
            _DischargeRecord(location=self._location, user=username))
        return [checkers.declared_caveat('username', username)]

    def identity_from_context(self, ctx):
        return None, [checkers.Caveat(location=self._location,
                                      condition='is-authenticated-user')]

    def declared_identity(self, ctx, declared):
        user = declared.get('username')
        if user is None:
            raise bakery.IdentityError('no username declared')
        return bakery.SimpleIdentity(user)


_DISCHARGE_USER_KEY = checkers.ContextKey('user-key')

_DischargeRecord = namedtuple('_DISCHARGE_RECORD', ['location', 'user'])


class _Discharger(object):
    ''' utility class that has a discharge function with the same signature of
    get_discharge for discharge_all.
    '''

    def __init__(self, key, locator, checker):
        self._key = key
        self._locator = locator
        self._checker = checker

    def discharge(self, ctx, cav, payload):
        return bakery.discharge(
            ctx,
            key=self._key,
            id=cav.caveat_id,
            caveat=payload,
            checker=self._checker,
            locator=self._locator,
        )


class _OpAuthorizer(bakery.Authorizer):
    '''Implements bakery.Authorizer by looking the operation
    up in the given map. If the username is in the associated list
    or the list contains "everyone", authorization is granted.
    '''

    def __init__(self, auth=None):
        if auth is None:
            auth = {}
        self._auth = auth

    def authorize(self, ctx, id, ops):
        return bakery.ACLAuthorizer(
            allow_public=True,
            get_acl=lambda ctx, op: self._auth.get(op, [])).authorize(
            ctx, id, ops)


class _MacaroonStore(object):
    ''' Stores root keys in memory and puts all operations in the macaroon id.
    '''

    def __init__(self, key, locator):
        self._root_key_store = bakery.MemoryKeyStore()
        self._key = key
        self._locator = locator

    def new_macaroon(self, caveats, namespace, ops):
        root_key, id = self._root_key_store.root_key()
        m_id = {'id': base64.urlsafe_b64encode(id).decode('utf-8'), 'ops': ops}
        data = json.dumps(m_id)
        m = bakery.Macaroon(
            root_key=root_key, id=data, location='',
            version=bakery.LATEST_VERSION,
            namespace=namespace)
        m.add_caveats(caveats, self._key, self._locator)
        return m

    def macaroon_ops(self, ms):
        if len(ms) == 0:
            raise ValueError('no macaroons provided')

        m_id = json.loads(ms[0].identifier_bytes.decode('utf-8'))
        root_key = self._root_key_store.get(
            base64.urlsafe_b64decode(m_id['id'].encode('utf-8')))

        v = Verifier()

        class NoValidationOnFirstPartyCaveat(FirstPartyCaveatVerifierDelegate):
            def verify_first_party_caveat(self, verifier, caveat, signature):
                return True

        v.first_party_caveat_verifier_delegate = \
            NoValidationOnFirstPartyCaveat()
        ok = v.verify(macaroon=ms[0], key=root_key,
                      discharge_macaroons=ms[1:])
        if not ok:
            raise bakery.VerificationError('invalid signature')
        conditions = []
        for m in ms:
            cavs = m.first_party_caveats()
            for cav in cavs:
                conditions.append(cav.caveat_id_bytes.decode('utf-8'))
        ops = []
        for op in m_id['ops']:
            ops.append(bakery.Op(entity=op[0], action=op[1]))
        return ops, conditions


class _Service(object):
    '''Represents a service that requires authorization.

    Clients can make requests to the service to perform operations
    and may receive a macaroon to discharge if the authorization
    process requires it.
    '''

    def __init__(self, name, auth, idm, locator):
        self._name = name
        self._store = _MacaroonStore(bakery.generate_key(), locator)
        self._checker = bakery.Checker(
            checker=test_checker(),
            authorizer=auth,
            identity_client=idm,
            macaroon_opstore=self._store)

    def name(self):
        return self._name

    def do(self, ctx, ms, ops):
        try:
            authInfo = self._checker.auth(ms).allow(ctx, ops)
        except bakery.DischargeRequiredError as exc:
            self._discharge_required_error(exc)
        return authInfo

    def do_any(self, ctx, ms, ops):
        # makes a request to the service to perform any of the given
        # operations. It reports which operations have succeeded.
        try:
            authInfo, allowed = self._checker.auth(ms).allow_any(ctx, ops)
            return authInfo, allowed
        except bakery.DischargeRequiredError as exc:
            self._discharge_required_error(exc)

    def capability(self, ctx, ms, ops):
        try:
            conds = self._checker.auth(ms).allow_capability(ctx, ops)
        except bakery.DischargeRequiredError as exc:
            self._discharge_required_error(exc)

        m = self._store.new_macaroon(None, self._checker.namespace(), ops)
        for cond in conds:
            m.macaroon.add_first_party_caveat(cond)
        return m

    def _discharge_required_error(self, err):
        m = self._store.new_macaroon(err.cavs(), self._checker.namespace(),
                                     err.ops())
        name = 'authz'
        if len(err.ops()) == 1 and err.ops()[0] == bakery.LOGIN_OP:
            name = 'authn'
        raise _DischargeRequiredError(name=name, m=m)


class _DischargeRequiredError(Exception):
    def __init__(self, name, m):
        Exception.__init__(self, 'discharge required')
        self._name = name
        self._m = m

    def m(self):
        return self._m

    def name(self):
        return self._name


class _Client(object):
    max_retries = 3

    def __init__(self, dischargers):
        self._key = bakery.generate_key()
        self._macaroons = {}
        self._dischargers = dischargers

    def do(self, ctx, svc, ops):
        class _AuthInfo:
            authInfo = None

        def svc_do(ms):
            _AuthInfo.authInfo = svc.do(ctx, ms, ops)

        self._do_func(ctx, svc, svc_do)
        return _AuthInfo.authInfo

    def do_any(self, ctx, svc, ops):
        return svc.do_any(ctx, self._request_macaroons(svc), ops)

    def capability(self, ctx, svc, ops):
        # capability returns a capability macaroon for the given operations.

        class _M:
            m = None

        def svc_capability(ms):
            _M.m = svc.capability(ctx, ms, ops)
            return

        self._do_func(ctx, svc, svc_capability)
        return _M.m

    def discharged_capability(self, ctx, svc, ops):
        m = self.capability(ctx, svc, ops)
        return self._discharge_all(ctx, m)

    def _do_func(self, ctx, svc, f):
        for i in range(0, self.max_retries):
            try:
                f(self._request_macaroons(svc))
                return
            except _DischargeRequiredError as exc:
                ms = self._discharge_all(ctx, exc.m())
                self.add_macaroon(svc, exc.name(), ms)
        raise ValueError('discharge failed too many times')

    def _clear_macaroons(self, svc):
        if svc is None:
            self._macaroons = {}
            return
        if svc.name() in self._macaroons:
            del self._macaroons[svc.name()]

    def add_macaroon(self, svc, name, m):
        if svc.name() not in self._macaroons:
            self._macaroons[svc.name()] = {}
        self._macaroons[svc.name()][name] = m

    def _request_macaroons(self, svc):
        mmap = self._macaroons.get(svc.name(), [])
        # Put all the macaroons in the slice ordered by key
        # so that we have deterministic behaviour in the tests.
        names = []
        for name in mmap:
            names.append(name)
        names = sorted(names)
        ms = [None] * len(names)
        for i, name in enumerate(names):
            ms[i] = mmap[name]
        return ms

    def _discharge_all(self, ctx, m):
        def get_discharge(cav, payload):
            d = self._dischargers.get(cav.location)
            if d is None:
                raise ValueError('third party discharger '
                                 '{} not found'.format(cav.location))
            return d.discharge(ctx, cav, payload)

        return bakery.discharge_all(m, get_discharge)


class _BasicAuthIdService(bakery.IdentityClient):
    def identity_from_context(self, ctx):
        user, pwd = _basic_auth_from_context(ctx)
        if user != 'sherlock' or pwd != 'holmes':
            return None, None
        return bakery.SimpleIdentity(user), None

    def declared_identity(self, ctx, declared):
        raise bakery.IdentityError('no identity declarations in basic auth'
                                   ' id service')


_BASIC_AUTH_KEY = checkers.ContextKey('user-key')


class _BasicAuth(object):
    def __init__(self, user, password):
        self.user = user
        self.password = password


def _context_with_basic_auth(ctx, user, password):
    return ctx.with_value(_BASIC_AUTH_KEY, _BasicAuth(user, password))


def _basic_auth_from_context(ctx):
    auth = ctx.get(_BASIC_AUTH_KEY, _BasicAuth('', ''))
    return auth.user, auth.password


def _macaroon_conditions(caveats, allow_third):
    conds = [''] * len(caveats)
    for i, cav in enumerate(caveats):
        if cav.location is not None and cav.location != '':
            if not allow_third:
                raise ValueError('found unexpected third party caveat:'
                                 ' {}'.format(cav.location))
            continue
        conds[i] = cav.caveat_id.decode('utf-8')
    return conds


def _resolve_caveats(ns, caveats):
    conds = [''] * len(caveats)
    for i, cav in enumerate(caveats):
        if cav.location is not None and cav.location != '':
            raise ValueError('found unexpected third party caveat')
        conds[i] = ns.resolve_caveat(cav).condition
    return conds


class _MacaroonStoreWithError(object):
    def new_macaroon(self, caveats, ns, ops):
        raise ValueError('some error')

    def macaroon_ops(self, ms):
        raise ValueError('some error')
