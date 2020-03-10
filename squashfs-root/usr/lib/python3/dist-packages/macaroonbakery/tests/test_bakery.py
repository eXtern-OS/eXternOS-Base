# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import os
from unittest import TestCase

import macaroonbakery.httpbakery as httpbakery
import requests
from mock import patch

from httmock import HTTMock, response, urlmatch

ID_PATH = 'http://example.com/someprotecteurl'

json_macaroon = {
    u'identifier': u'macaroon-identifier',
    u'caveats': [
        {
            u'cl': u'http://example.com/identity/v1/discharger',
            u'vid': u'zgtQa88oS9UF45DlJniRaAUT4qqHhLxQzCeUU9N2O1Uu-'
                    u'yhFulgGbSA0zDGdkrq8YNQAxGiARA_-AGxyoh25kiTycb8u47pD',
            u'cid': u'eyJUaGlyZFBhcnR5UHV'
        }, {
            u'cid': u'allow read-no-terms write'
        }, {
            u'cid': u'time-before 2158-07-19T14:29:14.312669464Z'
        }],
    u'location': u'charmstore',
    u'signature': u'52d17cb11f5c84d58441bc0ffd7cc396'
                  u'5115374ce2fa473ecf06265b5d4d9e81'
}

discharge_token = [{
    u'identifier': u'token-identifier===',
    u'caveats': [{
        u'cid': u'declared username someone'
    }, {
        u'cid': u'time-before 2158-08-15T15:55:52.428319076Z'
    }, {
        u'cid': u'origin '
    }],
    u'location': u'https://example.com/identity',
    u'signature': u'5ae0e7a2abf806bdd92f510fcd3'
                  u'198f520691259abe76ffae5623dae048769ef'
}]

discharged_macaroon = {
    u'identifier': u'discharged-identifier=',
    u'caveats': [{
        u'cid': u'declared uuid a1130b10-3deb-59b7-baf0-c2a3f83e7382'
    }, {
        u'cid': u'declared username someone'
    }, {
        u'cid': u'time-before 2158-07-19T15:55:52.432439055Z'
    }],
    u'location': u'',
    u'signature': u'3513db5503ab17f9576760cd28'
                  u'ce658ce8bf6b43038255969fc3c1cd8b172345'
}


@urlmatch(path='.*/someprotecteurl')
def first_407_then_200(url, request):
    if request.headers.get('cookie', '').startswith('macaroon-'):
        return {
            'status_code': 200,
            'content': {
                'Value': 'some value'
            }
        }
    else:
        resp = response(status_code=407,
                        content={
                            'Info': {
                                'Macaroon': json_macaroon,
                                'MacaroonPath': '/',
                                'CookieNameSuffix': 'test'
                            },
                            'Message': 'verification failed: no macaroon '
                                       'cookies in request',
                            'Code': 'macaroon discharge required'
                        },
                        headers={'Content-Type': 'application/json'})
        return request.hooks['response'][0](resp)


@urlmatch(netloc='example.com:8000', path='.*/someprotecteurl')
def first_407_then_200_with_port(url, request):
    if request.headers.get('cookie', '').startswith('macaroon-'):
        return {
            'status_code': 200,
            'content': {
                'Value': 'some value'
            }
        }
    else:
        resp = response(status_code=407,
                        content={
                            'Info': {
                                'Macaroon': json_macaroon,
                                'MacaroonPath': '/',
                                'CookieNameSuffix': 'test'
                            },
                            'Message': 'verification failed: no macaroon '
                                       'cookies in request',
                            'Code': 'macaroon discharge required'
                        },
                        headers={'Content-Type': 'application/json'},
                        request=request)
        return request.hooks['response'][0](resp)


@urlmatch(path='.*/someprotecteurl')
def valid_200(url, request):
    return {
        'status_code': 200,
        'content': {
            'Value': 'some value'
        }
    }


@urlmatch(path='.*/discharge')
def discharge_200(url, request):
    return {
        'status_code': 200,
        'content': {
            'Macaroon': discharged_macaroon
        }
    }


@urlmatch(path='.*/discharge')
def discharge_401(url, request):
    return {
        'status_code': 401,
        'content': {
            'Code': 'interaction required',
            'Info': {
                'VisitURL': 'http://example.com/visit',
                'WaitURL': 'http://example.com/wait'
            }
        },
        'headers': {
            'WWW-Authenticate': 'Macaroon'
        }
    }


@urlmatch(path='.*/visit')
def visit_200(url, request):
    return {
        'status_code': 200,
        'content': {
            'interactive': '/visit'
        }
    }


@urlmatch(path='.*/wait')
def wait_after_401(url, request):
    if request.url != 'http://example.com/wait':
        return {'status_code': 500}

    return {
        'status_code': 200,
        'content': {
            'DischargeToken': discharge_token,
            'Macaroon': discharged_macaroon
        }
    }


@urlmatch(path='.*/wait')
def wait_on_error(url, request):
    return {
        'status_code': 500,
        'content': {
            'DischargeToken': discharge_token,
            'Macaroon': discharged_macaroon
        }
    }


class TestBakery(TestCase):
    def setUp(self):
        super(TestBakery, self).setUp()
        # http_proxy would cause requests to talk to the proxy, which is
        # unlikely to know how to talk to the test server.
        os.environ.pop('http_proxy', None)

    def assert_cookie_security(self, cookies, name, secure):
        for cookie in cookies:
            if cookie.name == name:
                assert cookie.secure == secure
                break
        else:
            assert False, 'no cookie named {} found in jar'.format(name)

    def test_discharge(self):
        client = httpbakery.Client()
        with HTTMock(first_407_then_200), HTTMock(discharge_200):
                resp = requests.get(ID_PATH,
                                    cookies=client.cookies,
                                    auth=client.auth())
        resp.raise_for_status()
        assert 'macaroon-test' in client.cookies.keys()
        self.assert_cookie_security(client.cookies, 'macaroon-test',
                                    secure=False)

    @patch('webbrowser.open')
    def test_407_then_401_on_discharge(self, mock_open):
        client = httpbakery.Client()
        with HTTMock(first_407_then_200), HTTMock(discharge_401), \
                HTTMock(wait_after_401):
                resp = requests.get(
                    ID_PATH,
                    cookies=client.cookies,
                    auth=client.auth(),
                )
                resp.raise_for_status()
        mock_open.assert_called_once_with(u'http://example.com/visit', new=1)
        assert 'macaroon-test' in client.cookies.keys()

    @patch('webbrowser.open')
    def test_407_then_error_on_wait(self, mock_open):
        client = httpbakery.Client()
        with HTTMock(first_407_then_200), HTTMock(discharge_401),\
                HTTMock(wait_on_error):
            with self.assertRaises(httpbakery.InteractionError) as exc:
                requests.get(
                    ID_PATH,
                    cookies=client.cookies,
                    auth=client.auth(),
                )
        self.assertEqual(str(exc.exception),
                         'cannot start interactive session: cannot get '
                         'http://example.com/wait')
        mock_open.assert_called_once_with(u'http://example.com/visit', new=1)

    def test_407_then_no_interaction_methods(self):
        client = httpbakery.Client(interaction_methods=[])
        with HTTMock(first_407_then_200), HTTMock(discharge_401):
            with self.assertRaises(httpbakery.InteractionError) as exc:
                requests.get(
                    ID_PATH,
                    cookies=client.cookies,
                    auth=client.auth(),
                )
        self.assertEqual(str(exc.exception),
                         'cannot start interactive session: interaction '
                         'required but not possible')

    def test_407_then_unknown_interaction_methods(self):
        class UnknownInteractor(httpbakery.Interactor):
            def kind(self):
                return 'unknown'
        client = httpbakery.Client(interaction_methods=[UnknownInteractor()])
        with HTTMock(first_407_then_200), HTTMock(discharge_401),\
                HTTMock(visit_200):
            with self.assertRaises(httpbakery.InteractionError) as exc:
                requests.get(
                    ID_PATH,
                    cookies=client.cookies,
                    auth=client.auth(),
                )
        self.assertEqual(
            str(exc.exception),
            'cannot start interactive session: no methods supported; '
            'supported [unknown]; provided [interactive]'
        )

    def test_cookie_with_port(self):
        client = httpbakery.Client()
        with HTTMock(first_407_then_200_with_port):
            with HTTMock(discharge_200):
                resp = requests.get('http://example.com:8000/someprotecteurl',
                                    cookies=client.cookies,
                                    auth=client.auth())
        resp.raise_for_status()
        assert 'macaroon-test' in client.cookies.keys()

    def test_secure_cookie_for_https(self):
        client = httpbakery.Client()
        with HTTMock(first_407_then_200_with_port), HTTMock(discharge_200):
                resp = requests.get(
                    'https://example.com:8000/someprotecteurl',
                    cookies=client.cookies,
                    auth=client.auth())
        resp.raise_for_status()
        assert 'macaroon-test' in client.cookies.keys()
        self.assert_cookie_security(client.cookies, 'macaroon-test',
                                    secure=True)
