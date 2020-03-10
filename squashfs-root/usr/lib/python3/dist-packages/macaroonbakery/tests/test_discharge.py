# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import unittest

import macaroonbakery.bakery as bakery
import macaroonbakery.checkers as checkers
from macaroonbakery.tests import common
from pymacaroons import MACAROON_V1, Macaroon


class TestDischarge(unittest.TestCase):
    def test_single_service_first_party(self):
        ''' Creates a single service with a macaroon with one first party
        caveat.
        It creates a request with this macaroon and checks that the service
        can verify this macaroon as valid.
        '''
        oc = common.new_bakery('bakerytest')
        primary = oc.oven.macaroon(bakery.LATEST_VERSION,
                                   common.ages, None,
                                   [bakery.LOGIN_OP])
        self.assertEqual(primary.macaroon.location, 'bakerytest')
        primary.add_caveat(checkers.Caveat(condition='str something',
                                           namespace='testns'),
                           oc.oven.key, oc.oven.locator)
        oc.checker.auth([[primary.macaroon]]).allow(
            common.str_context('something'), [bakery.LOGIN_OP])

    def test_macaroon_paper_fig6(self):
        ''' Implements an example flow as described in the macaroons paper:
        http://theory.stanford.edu/~ataly/Papers/macaroons.pdf
        There are three services, ts, fs, bs:
        ts is a store service which has deligated authority to a forum
        service fs.
        The forum service wants to require its users to be logged into to an
        authentication service bs.

        The client obtains a macaroon from fs (minted by ts, with a third party
         caveat addressed to bs).
        The client obtains a discharge macaroon from bs to satisfy this caveat.
        The target service verifies the original macaroon it delegated to fs
        No direct contact between bs and ts is required
        '''
        locator = bakery.ThirdPartyStore()
        bs = common.new_bakery('bs-loc', locator)
        ts = common.new_bakery('ts-loc', locator)
        fs = common.new_bakery('fs-loc', locator)

        # ts creates a macaroon.
        ts_macaroon = ts.oven.macaroon(bakery.LATEST_VERSION,
                                       common.ages,
                                       None, [bakery.LOGIN_OP])

        # ts somehow sends the macaroon to fs which adds a third party caveat
        # to be discharged by bs.
        ts_macaroon.add_caveat(checkers.Caveat(location='bs-loc',
                                               condition='user==bob'),
                               fs.oven.key, fs.oven.locator)

        # client asks for a discharge macaroon for each third party caveat
        def get_discharge(cav, payload):
            self.assertEqual(cav.location, 'bs-loc')
            return bakery.discharge(
                common.test_context,
                cav.caveat_id_bytes,
                payload,
                bs.oven.key,
                common.ThirdPartyStrcmpChecker('user==bob'),
                bs.oven.locator,
            )

        d = bakery.discharge_all(ts_macaroon, get_discharge)

        ts.checker.auth([d]).allow(common.test_context,
                                   [bakery.LOGIN_OP])

    def test_discharge_with_version1_macaroon(self):
        locator = bakery.ThirdPartyStore()
        bs = common.new_bakery('bs-loc', locator)
        ts = common.new_bakery('ts-loc', locator)

        # ts creates a old-version macaroon.
        ts_macaroon = ts.oven.macaroon(bakery.VERSION_1, common.ages,
                                       None, [bakery.LOGIN_OP])
        ts_macaroon.add_caveat(checkers.Caveat(condition='something',
                                               location='bs-loc'),
                               ts.oven.key, ts.oven.locator)

        # client asks for a discharge macaroon for each third party caveat

        def get_discharge(cav, payload):
            # Make sure that the caveat id really is old-style.
            try:
                cav.caveat_id_bytes.decode('utf-8')
            except UnicodeDecodeError:
                self.fail('caveat id is not utf-8')
            return bakery.discharge(
                common.test_context,
                cav.caveat_id_bytes,
                payload,
                bs.oven.key,
                common.ThirdPartyStrcmpChecker('something'),
                bs.oven.locator,
            )

        d = bakery.discharge_all(ts_macaroon, get_discharge)

        ts.checker.auth([d]).allow(common.test_context,
                                   [bakery.LOGIN_OP])

        for m in d:
            self.assertEqual(m.version, MACAROON_V1)

    def test_version1_macaroon_id(self):
        # In the version 1 bakery, macaroon ids were hex-encoded with a
        # hyphenated UUID suffix.
        root_key_store = bakery.MemoryKeyStore()
        b = bakery.Bakery(
            root_key_store=root_key_store,
            identity_client=common.OneIdentity(),
        )
        key, id = root_key_store.root_key()
        root_key_store.get(id)
        m = Macaroon(key=key, version=MACAROON_V1, location='',
                     identifier=id + b'-deadl00f')
        b.checker.auth([[m]]).allow(common.test_context,
                                    [bakery.LOGIN_OP])

    def test_macaroon_paper_fig6_fails_without_discharges(self):
        ''' Runs a similar test as test_macaroon_paper_fig6 without the client
        discharging the third party caveats.
        '''
        locator = bakery.ThirdPartyStore()
        ts = common.new_bakery('ts-loc', locator)
        fs = common.new_bakery('fs-loc', locator)
        common.new_bakery('as-loc', locator)

        # ts creates a macaroon.
        ts_macaroon = ts.oven.macaroon(bakery.LATEST_VERSION,
                                       common.ages, None,
                                       [bakery.LOGIN_OP])

        # ts somehow sends the macaroon to fs which adds a third party
        # caveat to be discharged by as.
        ts_macaroon.add_caveat(checkers.Caveat(location='as-loc',
                                               condition='user==bob'),
                               fs.oven.key, fs.oven.locator)

        # client makes request to ts
        try:
            ts.checker.auth([[ts_macaroon.macaroon]]).allow(
                common.test_context,
                bakery.LOGIN_OP
            )
            self.fail('macaroon unmet should be raised')
        except bakery.VerificationError:
            pass

    def test_macaroon_paper_fig6_fails_with_binding_on_tampered_sig(self):
        ''' Runs a similar test as test_macaroon_paper_fig6 with the discharge
        macaroon binding being done on a tampered signature.
        '''
        locator = bakery.ThirdPartyStore()
        bs = common.new_bakery('bs-loc', locator)
        ts = common.new_bakery('ts-loc', locator)

        # ts creates a macaroon.
        ts_macaroon = ts.oven.macaroon(bakery.LATEST_VERSION,
                                       common.ages, None,
                                       [bakery.LOGIN_OP])
        # ts somehow sends the macaroon to fs which adds a third party caveat
        # to be discharged by as.
        ts_macaroon.add_caveat(checkers.Caveat(condition='user==bob',
                                               location='bs-loc'),
                               ts.oven.key, ts.oven.locator)

        # client asks for a discharge macaroon for each third party caveat
        def get_discharge(cav, payload):
            self.assertEqual(cav.location, 'bs-loc')
            return bakery.discharge(
                common.test_context,
                cav.caveat_id_bytes,
                payload,
                bs.oven.key,
                common.ThirdPartyStrcmpChecker('user==bob'),
                bs.oven.locator,
            )

        d = bakery.discharge_all(ts_macaroon, get_discharge)
        # client has all the discharge macaroons. For each discharge macaroon
        # bind it to our ts_macaroon and add it to our request.
        tampered_macaroon = Macaroon()
        for i, dm in enumerate(d[1:]):
            d[i + 1] = tampered_macaroon.prepare_for_request(dm)

        # client makes request to ts.
        with self.assertRaises(bakery.VerificationError) as exc:
            ts.checker.auth([d]).allow(common.test_context,
                                       bakery.LOGIN_OP)
        self.assertEqual('verification failed: Signatures do not match',
                         exc.exception.args[0])

    def test_need_declared(self):
        locator = bakery.ThirdPartyStore()
        first_party = common.new_bakery('first', locator)
        third_party = common.new_bakery('third', locator)

        # firstParty mints a macaroon with a third-party caveat addressed
        # to thirdParty with a need-declared caveat.
        m = first_party.oven.macaroon(
            bakery.LATEST_VERSION, common.ages, [
                checkers.need_declared_caveat(
                    checkers.Caveat(location='third', condition='something'),
                    ['foo', 'bar']
                )
            ], [bakery.LOGIN_OP])

        # The client asks for a discharge macaroon for each third party caveat.
        def get_discharge(cav, payload):
            return bakery.discharge(
                common.test_context,
                cav.caveat_id_bytes,
                payload,
                third_party.oven.key,
                common.ThirdPartyStrcmpChecker('something'),
                third_party.oven.locator,
            )

        d = bakery.discharge_all(m, get_discharge)

        # The required declared attributes should have been added
        # to the discharge macaroons.
        declared = checkers.infer_declared(d, first_party.checker.namespace())
        self.assertEqual(declared, {
            'foo': '',
            'bar': '',
        })

        # Make sure the macaroons actually check out correctly
        # when provided with the declared checker.
        ctx = checkers.context_with_declared(common.test_context, declared)
        first_party.checker.auth([d]).allow(ctx, [bakery.LOGIN_OP])

        # Try again when the third party does add a required declaration.

        # The client asks for a discharge macaroon for each third party caveat.
        def get_discharge(cav, payload):
            checker = common.ThirdPartyCheckerWithCaveats([
                checkers.declared_caveat('foo', 'a'),
                checkers.declared_caveat('arble', 'b')
            ])
            return bakery.discharge(
                common.test_context,
                cav.caveat_id_bytes,
                payload,
                third_party.oven.key,
                checker,
                third_party.oven.locator,
            )

        d = bakery.discharge_all(m, get_discharge)

        # One attribute should have been added, the other was already there.
        declared = checkers.infer_declared(d, first_party.checker.namespace())
        self.assertEqual(declared, {
            'foo': 'a',
            'bar': '',
            'arble': 'b',
        })

        ctx = checkers.context_with_declared(common.test_context, declared)
        first_party.checker.auth([d]).allow(ctx, [bakery.LOGIN_OP])

        # Try again, but this time pretend a client is sneakily trying
        # to add another 'declared' attribute to alter the declarations.

        def get_discharge(cav, payload):
            checker = common.ThirdPartyCheckerWithCaveats([
                checkers.declared_caveat('foo', 'a'),
                checkers.declared_caveat('arble', 'b'),
            ])

            # Sneaky client adds a first party caveat.
            m = bakery.discharge(
                common.test_context, cav.caveat_id_bytes,
                payload,
                third_party.oven.key, checker,
                third_party.oven.locator,
            )
            m.add_caveat(checkers.declared_caveat('foo', 'c'), None, None)
            return m

        d = bakery.discharge_all(m, get_discharge)

        declared = checkers.infer_declared(d, first_party.checker.namespace())
        self.assertEqual(declared, {
            'bar': '',
            'arble': 'b',
        })

        with self.assertRaises(bakery.AuthInitError) as exc:
            first_party.checker.auth([d]).allow(common.test_context,
                                                bakery.LOGIN_OP)
        self.assertEqual('cannot authorize login macaroon: caveat '
                         '"declared foo a" not satisfied: got foo=null, '
                         'expected "a"', exc.exception.args[0])

    def test_discharge_two_need_declared(self):
        locator = bakery.ThirdPartyStore()
        first_party = common.new_bakery('first', locator)
        third_party = common.new_bakery('third', locator)

        # first_party mints a macaroon with two third party caveats
        # with overlapping attributes.
        m = first_party.oven.macaroon(
            bakery.LATEST_VERSION,
            common.ages, [
                checkers.need_declared_caveat(
                    checkers.Caveat(location='third', condition='x'),
                    ['foo', 'bar']),
                checkers.need_declared_caveat(
                    checkers.Caveat(location='third', condition='y'),
                    ['bar', 'baz']),
            ], [bakery.LOGIN_OP])

        # The client asks for a discharge macaroon for each third party caveat.
        # Since no declarations are added by the discharger,

        def get_discharge(cav, payload):
            return bakery.discharge(
                common.test_context,
                cav.caveat_id_bytes,
                payload,
                third_party.oven.key,
                common.ThirdPartyCaveatCheckerEmpty(),
                third_party.oven.locator,
            )

        d = bakery.discharge_all(m, get_discharge)
        declared = checkers.infer_declared(d, first_party.checker.namespace())
        self.assertEqual(declared, {
            'foo': '',
            'bar': '',
            'baz': '',
        })
        ctx = checkers.context_with_declared(common.test_context, declared)
        first_party.checker.auth([d]).allow(ctx, [bakery.LOGIN_OP])

        # If they return conflicting values, the discharge fails.
        # The client asks for a discharge macaroon for each third party caveat.
        # Since no declarations are added by the discharger,
        class ThirdPartyCaveatCheckerF(bakery.ThirdPartyCaveatChecker):
            def check_third_party_caveat(self, ctx, cav_info):
                if cav_info.condition == b'x':
                    return [checkers.declared_caveat('foo', 'fooval1')]
                if cav_info.condition == b'y':
                    return [
                        checkers.declared_caveat('foo', 'fooval2'),
                        checkers.declared_caveat('baz', 'bazval')
                    ]
                raise common.ThirdPartyCaveatCheckFailed('not matched')

        def get_discharge(cav, payload):
            return bakery.discharge(
                common.test_context,
                cav.caveat_id_bytes,
                payload,
                third_party.oven.key,
                ThirdPartyCaveatCheckerF(),
                third_party.oven.locator,
            )

        d = bakery.discharge_all(m, get_discharge)

        declared = checkers.infer_declared(d, first_party.checker.namespace())
        self.assertEqual(declared, {
            'bar': '',
            'baz': 'bazval',
        })
        with self.assertRaises(bakery.AuthInitError) as exc:
            first_party.checker.auth([d]).allow(common.test_context,
                                                bakery.LOGIN_OP)
        self.assertEqual('cannot authorize login macaroon: caveat "declared '
                         'foo fooval1" not satisfied: got foo=null, expected '
                         '"fooval1"', exc.exception.args[0])

    def test_discharge_macaroon_cannot_be_used_as_normal_macaroon(self):
        locator = bakery.ThirdPartyStore()
        first_party = common.new_bakery('first', locator)
        third_party = common.new_bakery('third', locator)

        # First party mints a macaroon with a 3rd party caveat.
        m = first_party.oven.macaroon(bakery.LATEST_VERSION,
                                      common.ages, [
                                          checkers.Caveat(location='third',
                                                          condition='true')],
                                      [bakery.LOGIN_OP])

        # Acquire the discharge macaroon, but don't bind it to the original.
        class M:
            unbound = None

        def get_discharge(cav, payload):
            m = bakery.discharge(
                common.test_context,
                cav.caveat_id_bytes,
                payload,
                third_party.oven.key,
                common.ThirdPartyStrcmpChecker('true'),
                third_party.oven.locator,
            )
            M.unbound = m.macaroon.copy()
            return m

        bakery.discharge_all(m, get_discharge)
        self.assertIsNotNone(M.unbound)

        # Make sure it cannot be used as a normal macaroon in the third party.
        with self.assertRaises(bakery.VerificationError) as exc:
            third_party.checker.auth([[M.unbound]]).allow(
                common.test_context, [bakery.LOGIN_OP])
        self.assertEqual('no operations found in macaroon',
                         exc.exception.args[0])

    def test_third_party_discharge_macaroon_ids_are_small(self):
        locator = bakery.ThirdPartyStore()
        bakeries = {
            'ts-loc': common.new_bakery('ts-loc', locator),
            'as1-loc': common.new_bakery('as1-loc', locator),
            'as2-loc': common.new_bakery('as2-loc', locator),
        }
        ts = bakeries['ts-loc']

        ts_macaroon = ts.oven.macaroon(bakery.LATEST_VERSION,
                                       common.ages,
                                       None, [bakery.LOGIN_OP])
        ts_macaroon.add_caveat(checkers.Caveat(condition='something',
                                               location='as1-loc'),
                               ts.oven.key, ts.oven.locator)

        class ThirdPartyCaveatCheckerF(bakery.ThirdPartyCaveatChecker):
            def __init__(self, loc):
                self._loc = loc

            def check_third_party_caveat(self, ctx, info):
                if self._loc == 'as1-loc':
                    return [checkers.Caveat(condition='something',
                                            location='as2-loc')]
                if self._loc == 'as2-loc':
                    return []
                raise common.ThirdPartyCaveatCheckFailed(
                    'unknown location {}'.format(self._loc))

        def get_discharge(cav, payload):
            oven = bakeries[cav.location].oven
            return bakery.discharge(
                common.test_context,
                cav.caveat_id_bytes,
                payload,
                oven.key,
                ThirdPartyCaveatCheckerF(cav.location),
                oven.locator,
            )

        d = bakery.discharge_all(ts_macaroon, get_discharge)
        ts.checker.auth([d]).allow(common.test_context,
                                   [bakery.LOGIN_OP])

        for i, m in enumerate(d):
            for j, cav in enumerate(m.caveats):
                if (cav.verification_key_id is not None and
                        len(cav.caveat_id) > 3):
                    self.fail('caveat id on caveat {} of macaroon {} '
                              'is too big ({})'.format(j, i, cav.id))
