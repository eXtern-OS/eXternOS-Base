# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import json
from unittest import TestCase

import macaroonbakery.bakery as bakery
import macaroonbakery.checkers as checkers
import pymacaroons
import six
from macaroonbakery.tests import common
from pymacaroons import serializers


class TestMacaroon(TestCase):
    def test_new_macaroon(self):
        m = bakery.Macaroon(
            b'rootkey',
            b'some id',
            'here',
            bakery.LATEST_VERSION)
        self.assertIsNotNone(m)
        self.assertEquals(m._macaroon.identifier, b'some id')
        self.assertEquals(m._macaroon.location, 'here')
        self.assertEquals(m.version, bakery.LATEST_VERSION)

    def test_add_first_party_caveat(self):
        m = bakery.Macaroon('rootkey', 'some id', 'here',
                            bakery.LATEST_VERSION)
        m.add_caveat(checkers.Caveat('test_condition'))
        caveats = m.first_party_caveats()
        self.assertEquals(len(caveats), 1)
        self.assertEquals(caveats[0].caveat_id, b'test_condition')

    def test_add_third_party_caveat(self):
        locator = bakery.ThirdPartyStore()
        bs = common.new_bakery('bs-loc', locator)

        lbv = six.int2byte(bakery.LATEST_VERSION)
        tests = [
            ('no existing id', b'', [], lbv + six.int2byte(0)),
            ('several existing ids', b'', [
                lbv + six.int2byte(0),
                lbv + six.int2byte(1),
                lbv + six.int2byte(2)
            ], lbv + six.int2byte(3)),
            ('with base id', lbv + six.int2byte(0), [lbv + six.int2byte(0)],
             lbv + six.int2byte(0) + six.int2byte(0)),
            ('with base id and existing id', lbv + six.int2byte(0), [
                lbv + six.int2byte(0) + six.int2byte(0)
            ], lbv + six.int2byte(0) + six.int2byte(1))
        ]

        for test in tests:
            print('test ', test[0])
            m = bakery.Macaroon(
                root_key=b'root key', id=b'id',
                location='location',
                version=bakery.LATEST_VERSION)
            for id in test[2]:
                m.macaroon.add_third_party_caveat(key=None, key_id=id,
                                                  location='')
                m._caveat_id_prefix = test[1]
            m.add_caveat(checkers.Caveat(location='bs-loc',
                                         condition='something'),
                         bs.oven.key, locator)
            self.assertEqual(m.macaroon.caveats[len(test[2])].caveat_id,
                             test[3])

    def test_marshal_json_latest_version(self):
        locator = bakery.ThirdPartyStore()
        bs = common.new_bakery('bs-loc', locator)
        ns = checkers.Namespace({
            'testns': 'x',
            'otherns': 'y',
        })
        m = bakery.Macaroon(
            root_key=b'root key', id=b'id',
            location='location',
            version=bakery.LATEST_VERSION,
            namespace=ns)
        m.add_caveat(checkers.Caveat(location='bs-loc', condition='something'),
                     bs.oven.key, locator)
        data = m.serialize_json()
        m1 = bakery.Macaroon.deserialize_json(data)
        # Just check the signature and version - we're not interested in fully
        # checking the macaroon marshaling here.
        self.assertEqual(m1.macaroon.signature, m.macaroon.signature)
        self.assertEqual(m1.macaroon.version, m.macaroon.version)
        self.assertEqual(len(m1.macaroon.caveats), 1)
        self.assertEqual(m1.namespace, m.namespace)
        self.assertEqual(m1._caveat_data, m._caveat_data)

        # test with the encoder, decoder
        data = json.dumps(m, cls=bakery.MacaroonJSONEncoder)
        m1 = json.loads(data, cls=bakery.MacaroonJSONDecoder)
        self.assertEqual(m1.macaroon.signature, m.macaroon.signature)
        self.assertEqual(m1.macaroon.version, m.macaroon.version)
        self.assertEqual(len(m1.macaroon.caveats), 1)
        self.assertEqual(m1.namespace, m.namespace)
        self.assertEqual(m1._caveat_data, m._caveat_data)

    def test_json_version1(self):
        self._test_json_with_version(bakery.VERSION_1)

    def test_json_version2(self):
        self._test_json_with_version(bakery.VERSION_2)

    def _test_json_with_version(self, version):
        locator = bakery.ThirdPartyStore()
        bs = common.new_bakery('bs-loc', locator)

        ns = checkers.Namespace({
            'testns': 'x',
        })

        m = bakery.Macaroon(
            root_key=b'root key', id=b'id',
            location='location', version=version,
            namespace=ns)
        m.add_caveat(checkers.Caveat(location='bs-loc', condition='something'),
                     bs.oven.key, locator)

        # Sanity check that no external caveat data has been added.
        self.assertEqual(len(m._caveat_data), 0)

        data = json.dumps(m, cls=bakery.MacaroonJSONEncoder)
        m1 = json.loads(data, cls=bakery.MacaroonJSONDecoder)

        # Just check the signature and version - we're not interested in fully
        # checking the macaroon marshaling here.
        self.assertEqual(m1.macaroon.signature, m.macaroon.signature)
        self.assertEqual(m1.macaroon.version,
                         bakery.macaroon_version(version))
        self.assertEqual(len(m1.macaroon.caveats), 1)

        # Namespace information has been thrown away.
        self.assertEqual(m1.namespace, bakery.legacy_namespace())

        self.assertEqual(len(m1._caveat_data), 0)

    def test_json_unknown_version(self):
        m = pymacaroons.Macaroon(version=pymacaroons.MACAROON_V2)
        with self.assertRaises(ValueError) as exc:
            json.loads(json.dumps({
                'm': m.serialize(serializer=serializers.JsonSerializer()),
                'v': bakery.LATEST_VERSION + 1
            }), cls=bakery.MacaroonJSONDecoder)
        self.assertEqual('unknown bakery version 4', exc.exception.args[0])

    def test_json_inconsistent_version(self):
        m = pymacaroons.Macaroon(version=pymacaroons.MACAROON_V1)
        with self.assertRaises(ValueError) as exc:
            json.loads(json.dumps({
                'm': json.loads(m.serialize(
                    serializer=serializers.JsonSerializer())),
                'v': bakery.LATEST_VERSION
            }), cls=bakery.MacaroonJSONDecoder)
        self.assertEqual('underlying macaroon has inconsistent version; '
                         'got 1 want 2', exc.exception.args[0])

    def test_clone(self):
        locator = bakery.ThirdPartyStore()
        bs = common.new_bakery("bs-loc", locator)
        ns = checkers.Namespace({
            "testns": "x",
        })
        m = bakery.Macaroon(
            root_key=b'root key', id=b'id',
            location='location',
            version=bakery.LATEST_VERSION,
            namespace=ns)
        m.add_caveat(checkers.Caveat(location='bs-loc', condition='something'),
                     bs.oven.key, locator)
        m1 = m.copy()
        self.assertEqual(len(m.macaroon.caveats), 1)
        self.assertEqual(len(m1.macaroon.caveats), 1)
        self.assertEqual(m._caveat_data, m1._caveat_data)
        m.add_caveat(checkers.Caveat(location='bs-loc', condition='something'),
                     bs.oven.key, locator)
        self.assertEqual(len(m.macaroon.caveats), 2)
        self.assertEqual(len(m1.macaroon.caveats), 1)
        self.assertNotEqual(m._caveat_data, m1._caveat_data)

    def test_json_deserialize_from_go(self):
        ns = checkers.Namespace()
        ns.register("someuri", "x")
        m = bakery.Macaroon(
            root_key=b'rootkey', id=b'some id', location='here',
            version=bakery.LATEST_VERSION, namespace=ns)
        m.add_caveat(checkers.Caveat(condition='something',
                                     namespace='someuri'))
        data = '{"m":{"c":[{"i":"x:something"}],"l":"here","i":"some id",' \
               '"s64":"c8edRIupArSrY-WZfa62pgZFD8VjDgqho9U2PlADe-E"},"v":3,' \
               '"ns":"someuri:x"}'
        m_go = bakery.Macaroon.deserialize_json(data)

        self.assertEqual(m.macaroon.signature_bytes,
                         m_go.macaroon.signature_bytes)
        self.assertEqual(m.macaroon.version, m_go.macaroon.version)
        self.assertEqual(len(m_go.macaroon.caveats), 1)
        self.assertEqual(m.namespace, m_go.namespace)
