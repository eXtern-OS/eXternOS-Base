# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import unittest

import macaroonbakery.bakery as bakery
import macaroonbakery.httpbakery as httpbakery

from httmock import HTTMock, urlmatch


class TestKeyRing(unittest.TestCase):

    def test_cache_fetch(self):
        key = bakery.generate_key()

        @urlmatch(path='.*/discharge/info')
        def discharge_info(url, request):
            return {
                'status_code': 200,
                'content': {
                    'Version': bakery.LATEST_VERSION,
                    'PublicKey': str(key.public_key),
                }
            }

        expectInfo = bakery.ThirdPartyInfo(
            public_key=key.public_key,
            version=bakery.LATEST_VERSION
        )
        kr = httpbakery.ThirdPartyLocator(allow_insecure=True)
        with HTTMock(discharge_info):
            info = kr.third_party_info('http://0.1.2.3/')
        self.assertEqual(info, expectInfo)

    def test_cache_norefetch(self):
        key = bakery.generate_key()

        @urlmatch(path='.*/discharge/info')
        def discharge_info(url, request):
            return {
                'status_code': 200,
                'content': {
                    'Version': bakery.LATEST_VERSION,
                    'PublicKey': str(key.public_key),
                }
            }

        expectInfo = bakery.ThirdPartyInfo(
            public_key=key.public_key,
            version=bakery.LATEST_VERSION
        )
        kr = httpbakery.ThirdPartyLocator(allow_insecure=True)
        with HTTMock(discharge_info):
            info = kr.third_party_info('http://0.1.2.3/')
        self.assertEqual(info, expectInfo)
        info = kr.third_party_info('http://0.1.2.3/')
        self.assertEqual(info, expectInfo)

    def test_cache_fetch_no_version(self):
        key = bakery.generate_key()

        @urlmatch(path='.*/discharge/info')
        def discharge_info(url, request):
            return {
                'status_code': 200,
                'content': {
                    'PublicKey': str(key.public_key),
                }
            }

        expectInfo = bakery.ThirdPartyInfo(
            public_key=key.public_key,
            version=bakery.VERSION_1
        )
        kr = httpbakery.ThirdPartyLocator(allow_insecure=True)
        with HTTMock(discharge_info):
            info = kr.third_party_info('http://0.1.2.3/')
        self.assertEqual(info, expectInfo)

    def test_allow_insecure(self):
        kr = httpbakery.ThirdPartyLocator()
        with self.assertRaises(bakery.ThirdPartyInfoNotFound):
            kr.third_party_info('http://0.1.2.3/')

    def test_fallback(self):
        key = bakery.generate_key()

        @urlmatch(path='.*/discharge/info')
        def discharge_info(url, request):
            return {
                'status_code': 404,
            }

        @urlmatch(path='.*/publickey')
        def public_key(url, request):
            return {
                'status_code': 200,
                'content': {
                    'PublicKey': str(key.public_key),
                }
            }

        expectInfo = bakery.ThirdPartyInfo(
            public_key=key.public_key,
            version=bakery.VERSION_1
        )
        kr = httpbakery.ThirdPartyLocator(allow_insecure=True)
        with HTTMock(discharge_info):
            with HTTMock(public_key):
                info = kr.third_party_info('http://0.1.2.3/')
        self.assertEqual(info, expectInfo)
