# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.

import json
from datetime import datetime
from unittest import TestCase

import macaroonbakery.bakery as bakery
import pymacaroons
from macaroonbakery._utils import cookie
from pymacaroons.serializers import json_serializer


class CookieTest(TestCase):

    def test_cookie_expires_naive(self):
        timestamp = datetime.utcnow()
        c = cookie('http://example.com', 'test', 'value', expires=timestamp)
        self.assertEqual(
            c.expires, int((timestamp - datetime(1970, 1, 1)).total_seconds()))

    def test_cookie_expires_with_timezone(self):
        from datetime import tzinfo
        timestamp = datetime.utcnow().replace(tzinfo=tzinfo())
        self.assertRaises(
            ValueError, cookie, 'http://example.com', 'test', 'value',
            expires=timestamp)


class TestB64Decode(TestCase):
    def test_decode(self):
        test_cases = [{
            'about': 'empty string',
            'input': '',
            'expect': '',
        }, {
            'about': 'standard encoding, padded',
            'input': 'Z29+IQ==',
            'expect': 'go~!',
        }, {
            'about': 'URL encoding, padded',
            'input': 'Z29-IQ==',
            'expect': 'go~!',
        }, {
            'about': 'standard encoding, not padded',
            'input': 'Z29+IQ',
            'expect': 'go~!',
        }, {
            'about': 'URL encoding, not padded',
            'input': 'Z29-IQ',
            'expect': 'go~!',
        }, {
            'about': 'standard encoding, not enough much padding',
            'input': 'Z29+IQ=',
            'expect_error': 'illegal base64 data at input byte 8',
        }]
        for test in test_cases:
            if test.get('expect_error'):
                with self.assertRaises(ValueError, msg=test['about']) as e:
                    bakery.b64decode(test['input'])
                self.assertEqual(str(e.exception), 'Incorrect padding')
            else:
                self.assertEqual(bakery.b64decode(test['input']), test['expect'].encode('utf-8'), msg=test['about'])


class MacaroonToDictTest(TestCase):
    def test_macaroon_to_dict(self):
        m = pymacaroons.Macaroon(
            key=b'rootkey', identifier=b'some id', location='here', version=2)
        as_dict = bakery.macaroon_to_dict(m)
        data = json.dumps(as_dict)
        m1 = pymacaroons.Macaroon.deserialize(data, json_serializer.JsonSerializer())
        self.assertEqual(m1.signature, m.signature)
        pymacaroons.Verifier().verify(m1, b'rootkey')
