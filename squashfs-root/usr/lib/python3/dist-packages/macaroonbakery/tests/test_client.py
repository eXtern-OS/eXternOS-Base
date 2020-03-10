# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import base64
import datetime
import json
import os
import threading
from unittest import TestCase

import macaroonbakery.bakery as bakery
import macaroonbakery.checkers as checkers
import macaroonbakery.httpbakery as httpbakery
import pymacaroons
import requests
import macaroonbakery._utils as utils

from httmock import HTTMock, urlmatch
from six.moves.urllib.parse import parse_qs
from six.moves.urllib.request import Request

try:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler

AGES = datetime.datetime.utcnow() + datetime.timedelta(days=1)
TEST_OP = bakery.Op(entity='test', action='test')


class TestClient(TestCase):
    def setUp(self):
        super(TestClient, self).setUp()
        # http_proxy would cause requests to talk to the proxy, which is
        # unlikely to know how to talk to the test server.
        os.environ.pop('http_proxy', None)

    def test_single_service_first_party(self):
        b = new_bakery('loc', None, None)

        def handler(*args):
            GetHandler(b, None, None, None, None, AGES, *args)
        try:
            httpd = HTTPServer(('', 0), handler)
            thread = threading.Thread(target=httpd.serve_forever)
            thread.start()
            srv_macaroon = b.oven.macaroon(
                version=bakery.LATEST_VERSION, expiry=AGES,
                caveats=None, ops=[TEST_OP])
            self.assertEquals(srv_macaroon.macaroon.location, 'loc')
            client = httpbakery.Client()
            client.cookies.set_cookie(requests.cookies.create_cookie(
                'macaroon-test', base64.b64encode(json.dumps([
                    srv_macaroon.to_dict().get('m')
                ]).encode('utf-8')).decode('utf-8')
            ))
            resp = requests.get(
                url='http://' + httpd.server_address[0] + ':' +
                    str(httpd.server_address[1]),
                cookies=client.cookies, auth=client.auth())
            resp.raise_for_status()
            self.assertEquals(resp.text, 'done')
        finally:
            httpd.shutdown()

    def test_single_party_with_header(self):
        b = new_bakery('loc', None, None)

        def handler(*args):
            GetHandler(b, None, None, None, None, AGES, *args)
        try:
            httpd = HTTPServer(('', 0), handler)
            thread = threading.Thread(target=httpd.serve_forever)
            thread.start()
            srv_macaroon = b.oven.macaroon(
                version=bakery.LATEST_VERSION,
                expiry=AGES, caveats=None, ops=[TEST_OP])
            self.assertEquals(srv_macaroon.macaroon.location, 'loc')
            headers = {
                'Macaroons': base64.b64encode(json.dumps([
                    srv_macaroon.to_dict().get('m')
                ]).encode('utf-8'))
            }
            resp = requests.get(
                url='http://' + httpd.server_address[0] + ':' +
                    str(httpd.server_address[1]),
                headers=headers)
            resp.raise_for_status()
            self.assertEquals(resp.text, 'done')
        finally:
            httpd.shutdown()

    def test_expiry_cookie_is_set(self):
        class _DischargerLocator(bakery.ThirdPartyLocator):
            def __init__(self):
                self.key = bakery.generate_key()

            def third_party_info(self, loc):
                if loc == 'http://1.2.3.4':
                    return bakery.ThirdPartyInfo(
                        public_key=self.key.public_key,
                        version=bakery.LATEST_VERSION,
                    )

        d = _DischargerLocator()
        b = new_bakery('loc', d, None)

        @urlmatch(path='.*/discharge')
        def discharge(url, request):
            qs = parse_qs(request.body)
            content = {q: qs[q][0] for q in qs}
            m = httpbakery.discharge(checkers.AuthContext(), content, d.key, d,
                                     alwaysOK3rd)
            return {
                'status_code': 200,
                'content': {
                    'Macaroon': m.to_dict()
                }
            }

        ages = datetime.datetime.utcnow() + datetime.timedelta(days=1)

        def handler(*args):
            GetHandler(b, 'http://1.2.3.4', None, None, None, ages, *args)
        try:
            httpd = HTTPServer(('', 0), handler)
            thread = threading.Thread(target=httpd.serve_forever)
            thread.start()
            client = httpbakery.Client()
            with HTTMock(discharge):
                resp = requests.get(
                    url='http://' + httpd.server_address[0] + ':' +
                        str(httpd.server_address[1]),
                    cookies=client.cookies,
                    auth=client.auth())
            resp.raise_for_status()
            m = bakery.Macaroon.from_dict(json.loads(
                base64.b64decode(client.cookies.get('macaroon-test')).decode('utf-8'))[0])
            t = checkers.macaroons_expiry_time(
                checkers.Namespace(), [m.macaroon])
            self.assertEquals(ages, t)
            self.assertEquals(resp.text, 'done')
        finally:
            httpd.shutdown()

    def test_expiry_cookie_set_in_past(self):
        class _DischargerLocator(bakery.ThirdPartyLocator):
            def __init__(self):
                self.key = bakery.generate_key()

            def third_party_info(self, loc):
                if loc == 'http://1.2.3.4':
                    return bakery.ThirdPartyInfo(
                        public_key=self.key.public_key,
                        version=bakery.LATEST_VERSION,
                    )

        d = _DischargerLocator()
        b = new_bakery('loc', d, None)

        @urlmatch(path='.*/discharge')
        def discharge(url, request):
            qs = parse_qs(request.body)
            content = {q: qs[q][0] for q in qs}
            m = httpbakery.discharge(checkers.AuthContext(), content, d.key, d,
                                     alwaysOK3rd)
            return {
                'status_code': 200,
                'content': {
                    'Macaroon': m.to_dict()
                }
            }

        ages = datetime.datetime.utcnow() - datetime.timedelta(days=1)

        def handler(*args):
            GetHandler(b, 'http://1.2.3.4', None, None, None, ages, *args)
        try:
            httpd = HTTPServer(('', 0), handler)
            thread = threading.Thread(target=httpd.serve_forever)
            thread.start()
            client = httpbakery.Client()
            with HTTMock(discharge):
                with self.assertRaises(httpbakery.BakeryException) as ctx:
                    requests.get(
                        url='http://' + httpd.server_address[0] + ':' +
                            str(httpd.server_address[1]),
                        cookies=client.cookies,
                        auth=client.auth())
            self.assertEqual(ctx.exception.args[0],
                             'too many (3) discharge requests')
        finally:
            httpd.shutdown()

    def test_too_many_discharge(self):
        class _DischargerLocator(bakery.ThirdPartyLocator):
            def __init__(self):
                self.key = bakery.generate_key()

            def third_party_info(self, loc):
                if loc == 'http://1.2.3.4':
                    return bakery.ThirdPartyInfo(
                        public_key=self.key.public_key,
                        version=bakery.LATEST_VERSION,
                    )

        d = _DischargerLocator()
        b = new_bakery('loc', d, None)

        @urlmatch(path='.*/discharge')
        def discharge(url, request):
            wrong_macaroon = bakery.Macaroon(
                root_key=b'some key', id=b'xxx',
                location='some other location',
                version=bakery.VERSION_0)
            return {
                'status_code': 200,
                'content': {
                    'Macaroon': wrong_macaroon.to_dict()
                }
            }

        def handler(*args):
            GetHandler(b, 'http://1.2.3.4', None, None, None, AGES, *args)
        try:
            httpd = HTTPServer(('', 0), handler)
            thread = threading.Thread(target=httpd.serve_forever)
            thread.start()
            client = httpbakery.Client()
            with HTTMock(discharge):
                with self.assertRaises(httpbakery.BakeryException) as ctx:
                    requests.get(
                        url='http://' + httpd.server_address[0] + ':' +
                            str(httpd.server_address[1]),
                        cookies=client.cookies,
                        auth=client.auth())
            self.assertEqual(ctx.exception.args[0],
                             'too many (3) discharge requests')
        finally:
            httpd.shutdown()

    def test_third_party_discharge_refused(self):
        class _DischargerLocator(bakery.ThirdPartyLocator):
            def __init__(self):
                self.key = bakery.generate_key()

            def third_party_info(self, loc):
                if loc == 'http://1.2.3.4':
                    return bakery.ThirdPartyInfo(
                        public_key=self.key.public_key,
                        version=bakery.LATEST_VERSION,
                    )

        def check(cond, arg):
            raise bakery.ThirdPartyCaveatCheckFailed('boo! cond' + cond)

        d = _DischargerLocator()
        b = new_bakery('loc', d, None)

        @urlmatch(path='.*/discharge')
        def discharge(url, request):
            qs = parse_qs(request.body)
            content = {q: qs[q][0] for q in qs}
            httpbakery.discharge(checkers.AuthContext(), content, d.key, d,
                                 ThirdPartyCaveatCheckerF(check))

        def handler(*args):
            GetHandler(b, 'http://1.2.3.4', None, None, None, AGES, *args)
        try:
            httpd = HTTPServer(('', 0), handler)
            thread = threading.Thread(target=httpd.serve_forever)
            thread.start()
            client = httpbakery.Client()
            with HTTMock(discharge):
                with self.assertRaises(bakery.ThirdPartyCaveatCheckFailed):
                    requests.get(
                        url='http://' + httpd.server_address[0] + ':' +
                            str(httpd.server_address[1]),
                        cookies=client.cookies,
                        auth=client.auth())
        finally:
            httpd.shutdown()

    def test_discharge_with_interaction_required_error(self):
        class _DischargerLocator(bakery.ThirdPartyLocator):
            def __init__(self):
                self.key = bakery.generate_key()

            def third_party_info(self, loc):
                if loc == 'http://1.2.3.4':
                    return bakery.ThirdPartyInfo(
                        public_key=self.key.public_key,
                        version=bakery.LATEST_VERSION,
                    )
        d = _DischargerLocator()
        b = new_bakery('loc', d, None)

        @urlmatch(path='.*/discharge')
        def discharge(url, request):
            return {
                'status_code': 401,
                'content': {
                    'Code': httpbakery.ERR_INTERACTION_REQUIRED,
                    'Message': 'interaction required',
                    'Info': {
                        'WaitURL': 'http://0.1.2.3/',
                        'VisitURL': 'http://0.1.2.3/',
                    },
                }
            }

        def handler(*args):
            GetHandler(b, 'http://1.2.3.4', None, None, None, AGES, *args)

        try:
            httpd = HTTPServer(('', 0), handler)
            thread = threading.Thread(target=httpd.serve_forever)
            thread.start()

            class MyInteractor(httpbakery.LegacyInteractor):
                def legacy_interact(self, ctx, location, visit_url):
                    raise httpbakery.InteractionError('cannot visit')

                def interact(self, ctx, location, interaction_required_err):
                    pass

                def kind(self):
                    return httpbakery.WEB_BROWSER_INTERACTION_KIND

            client = httpbakery.Client(interaction_methods=[MyInteractor()])

            with HTTMock(discharge):
                with self.assertRaises(httpbakery.InteractionError):
                    requests.get(
                        'http://' + httpd.server_address[0] + ':' + str(
                            httpd.server_address[1]),
                        cookies=client.cookies,
                        auth=client.auth())
        finally:
            httpd.shutdown()

    def test_extract_macaroons_from_request(self):
        def encode_macaroon(m):
            macaroons = '[' + utils.macaroon_to_json_string(m) + ']'
            return base64.urlsafe_b64encode(utils.to_bytes(macaroons)).decode('ascii')

        req = Request('http://example.com')
        m1 = pymacaroons.Macaroon(version=pymacaroons.MACAROON_V2, identifier='one')
        req.add_header('Macaroons', encode_macaroon(m1))
        m2 = pymacaroons.Macaroon(version=pymacaroons.MACAROON_V2, identifier='two')
        jar = requests.cookies.RequestsCookieJar()
        jar.set_cookie(utils.cookie(
            name='macaroon-auth',
            value=encode_macaroon(m2),
            url='http://example.com',
        ))
        jar.set_cookie(utils.cookie(
            name='macaroon-empty',
            value='',
            url='http://example.com',
        ))
        jar.add_cookie_header(req)

        macaroons = httpbakery.extract_macaroons(req)
        self.assertEquals(len(macaroons), 2)
        macaroons.sort(key=lambda ms: ms[0].identifier)
        self.assertEquals(macaroons[0][0].identifier, m1.identifier)
        self.assertEquals(macaroons[1][0].identifier, m2.identifier)


class GetHandler(BaseHTTPRequestHandler):
    '''A mock HTTP server that serves a GET request'''
    def __init__(self, bakery, auth_location, mutate_error,
                 caveats, version, expiry, *args):
        '''
        @param bakery used to check incoming requests and macaroons
        for discharge-required errors.
        @param auth_location holds the location of any 3rd party
        authorizer. If this is not None, a 3rd party caveat will be
        added addressed to this location.
        @param mutate_error if non None, will be called with any
        discharge-required error before responding to the client.
        @param caveats called to get caveats to add to the returned
        macaroon.
        @param version holds the version of the bakery that the
        server will purport to serve.
        @param expiry holds the expiry for the macaroon that will be created
        in _write_discharge_error
        '''
        self._bakery = bakery
        self._auth_location = auth_location
        self._mutate_error = mutate_error
        self._caveats = caveats
        self._server_version = version
        self._expiry = expiry
        BaseHTTPRequestHandler.__init__(self, *args)

    def do_GET(self):
        '''do_GET implements a handler for the HTTP GET method'''
        ctx = checkers.AuthContext()
        auth_checker = self._bakery.checker.auth(
            httpbakery.extract_macaroons(self.headers))
        try:
            auth_checker.allow(ctx, [TEST_OP])
        except (bakery.PermissionDenied,
                bakery.VerificationError) as exc:
            return self._write_discharge_error(exc)
        self.send_response(200)
        self.end_headers()
        content_len = int(self.headers.get('content-length', 0))
        content = 'done'
        if self.path != '/no-body'and content_len > 0:
            body = self.rfile.read(content_len)
            content = content + ' ' + body
        self.wfile.write(content.encode('utf-8'))
        return

    def _write_discharge_error(self, exc):
        version = httpbakery.request_version(self.headers)
        if version < bakery.LATEST_VERSION:
            self._server_version = version

        caveats = []
        if self._auth_location != '':
            caveats = [
                checkers.Caveat(location=self._auth_location,
                                condition='is-ok')
            ]
        if self._caveats is not None:
            caveats.extend(self._caveats)

        m = self._bakery.oven.macaroon(
            version=bakery.LATEST_VERSION, expiry=self._expiry,
            caveats=caveats, ops=[TEST_OP])

        content, headers = httpbakery.discharge_required_response(
            m, '/', 'test', exc.args[0])
        self.send_response(401)
        for h in headers:
            self.send_header(h, headers[h])
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(content)


def new_bakery(location, locator, checker):
    '''Return a new bakery instance.
    @param location Location of the bakery {str}.
    @param locator Locator for third parties {ThirdPartyLocator or None}
    @param checker Caveat checker {FirstPartyCaveatChecker or None}
    @return {Bakery}
    '''
    if checker is None:
        c = checkers.Checker()
        c.namespace().register('testns', '')
        c.register('is', 'testns', check_is_something)
        checker = c
    key = bakery.generate_key()
    return bakery.Bakery(
        location=location,
        locator=locator,
        key=key,
        checker=checker,
    )


def is_something_caveat():
    return checkers.Caveat(condition='is something', namespace='testns')


def check_is_something(ctx, cond, arg):
    if arg != 'something':
        return '{} doesn\'t match "something"'.format(arg)
    return None


class ThirdPartyCaveatCheckerF(bakery.ThirdPartyCaveatChecker):
    def __init__(self, check):
        self._check = check

    def check_third_party_caveat(self, ctx, info):
        cond, arg = checkers.parse_caveat(info.condition)
        return self._check(cond, arg)

alwaysOK3rd = ThirdPartyCaveatCheckerF(lambda cond, arg: [])
