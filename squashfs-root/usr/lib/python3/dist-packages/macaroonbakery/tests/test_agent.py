# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta
from unittest import TestCase

import macaroonbakery.bakery as bakery
import macaroonbakery.checkers as checkers
import macaroonbakery.httpbakery as httpbakery
import macaroonbakery.httpbakery.agent as agent
import requests.cookies

from httmock import HTTMock, response, urlmatch
from six.moves.urllib.parse import parse_qs, urlparse

log = logging.getLogger(__name__)

PRIVATE_KEY = 'CqoSgj06Zcgb4/S6RT4DpTjLAfKoznEY3JsShSjKJEU='
PUBLIC_KEY = 'YAhRSsth3a36mRYqQGQaLiS4QJax0p356nd+B8x7UQE='


class TestAgents(TestCase):
    def setUp(self):
        fd, filename = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write(agent_file)
        self.agent_filename = filename
        fd, filename = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write(bad_key_agent_file)
        self.bad_key_agent_filename = filename
        fd, filename = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write(no_username_agent_file)
        self.no_username_agent_filename = filename

    def tearDown(self):
        os.remove(self.agent_filename)
        os.remove(self.bad_key_agent_filename)
        os.remove(self.no_username_agent_filename)

    def test_load_auth_info(self):
        auth_info = agent.load_auth_info(self.agent_filename)
        self.assertEqual(str(auth_info.key), PRIVATE_KEY)
        self.assertEqual(str(auth_info.key.public_key), PUBLIC_KEY)
        self.assertEqual(auth_info.agents, [
            agent.Agent(url='https://1.example.com/', username='user-1'),
            agent.Agent(url='https://2.example.com/discharger', username='user-2'),
            agent.Agent(url='http://0.3.2.1', username='test-user'),
        ])

    def test_invalid_agent_json(self):
        with self.assertRaises(agent.AgentFileFormatError):
            agent.read_auth_info('}')

    def test_invalid_read_auth_info_arg(self):
        with self.assertRaises(agent.AgentFileFormatError):
            agent.read_auth_info(0)

    def test_load_auth_info_with_bad_key(self):
        with self.assertRaises(agent.AgentFileFormatError):
            agent.load_auth_info(self.bad_key_agent_filename)

    def test_load_auth_info_with_no_username(self):
        with self.assertRaises(agent.AgentFileFormatError):
            agent.load_auth_info(self.no_username_agent_filename)

    def test_agent_login(self):
        discharge_key = bakery.generate_key()

        class _DischargerLocator(bakery.ThirdPartyLocator):
            def third_party_info(self, loc):
                if loc == 'http://0.3.2.1':
                    return bakery.ThirdPartyInfo(
                        public_key=discharge_key.public_key,
                        version=bakery.LATEST_VERSION,
                    )
        d = _DischargerLocator()
        server_key = bakery.generate_key()
        server_bakery = bakery.Bakery(key=server_key, locator=d)

        @urlmatch(path='.*/here')
        def server_get(url, request):
            ctx = checkers.AuthContext()
            test_ops = [bakery.Op(entity='test-op', action='read')]
            auth_checker = server_bakery.checker.auth(
                httpbakery.extract_macaroons(request.headers))
            try:
                auth_checker.allow(ctx, test_ops)
                resp = response(status_code=200,
                                content='done')
            except bakery.PermissionDenied:
                caveats = [
                    checkers.Caveat(location='http://0.3.2.1',
                                    condition='is-ok')
                ]
                m = server_bakery.oven.macaroon(
                    version=bakery.LATEST_VERSION,
                    expiry=datetime.utcnow() + timedelta(days=1),
                    caveats=caveats, ops=test_ops)
                content, headers = httpbakery.discharge_required_response(
                    m, '/',
                    'test',
                    'message')
                resp = response(status_code=401,
                                content=content,
                                headers=headers)
            return request.hooks['response'][0](resp)

        @urlmatch(path='.*/discharge')
        def discharge(url, request):
            qs = parse_qs(request.body)
            if qs.get('token64') is None:
                return response(
                    status_code=401,
                    content={
                        'Code': httpbakery.ERR_INTERACTION_REQUIRED,
                        'Message': 'interaction required',
                        'Info': {
                            'InteractionMethods': {
                                'agent': {'login-url': '/login'},
                            },
                        },
                    },
                    headers={'Content-Type': 'application/json'})
            else:
                qs = parse_qs(request.body)
                content = {q: qs[q][0] for q in qs}
                m = httpbakery.discharge(checkers.AuthContext(), content,
                                         discharge_key, None, alwaysOK3rd)
                return {
                    'status_code': 200,
                    'content': {
                        'Macaroon': m.to_dict()
                    }
                }

        auth_info = agent.load_auth_info(self.agent_filename)

        @urlmatch(path='.*/login')
        def login(url, request):
            qs = parse_qs(urlparse(request.url).query)
            self.assertEqual(request.method, 'GET')
            self.assertEqual(
                qs, {'username': ['test-user'], 'public-key': [PUBLIC_KEY]})
            b = bakery.Bakery(key=discharge_key)
            m = b.oven.macaroon(
                version=bakery.LATEST_VERSION,
                expiry=datetime.utcnow() + timedelta(days=1),
                caveats=[bakery.local_third_party_caveat(
                    PUBLIC_KEY,
                    version=httpbakery.request_version(request.headers))],
                ops=[bakery.Op(entity='agent', action='login')])
            return {
                'status_code': 200,
                'content': {
                    'macaroon': m.to_dict()
                }
            }

        with HTTMock(server_get), \
                HTTMock(discharge), \
                HTTMock(login):
            client = httpbakery.Client(interaction_methods=[
                agent.AgentInteractor(auth_info),
            ])
            resp = requests.get(
                'http://0.1.2.3/here',
                cookies=client.cookies,
                auth=client.auth())
        self.assertEqual(resp.content, b'done')

    def test_agent_legacy(self):
        discharge_key = bakery.generate_key()

        class _DischargerLocator(bakery.ThirdPartyLocator):
            def third_party_info(self, loc):
                if loc == 'http://0.3.2.1':
                    return bakery.ThirdPartyInfo(
                        public_key=discharge_key.public_key,
                        version=bakery.LATEST_VERSION,
                    )
        d = _DischargerLocator()
        server_key = bakery.generate_key()
        server_bakery = bakery.Bakery(key=server_key, locator=d)

        @urlmatch(path='.*/here')
        def server_get(url, request):
            ctx = checkers.AuthContext()
            test_ops = [bakery.Op(entity='test-op', action='read')]
            auth_checker = server_bakery.checker.auth(
                httpbakery.extract_macaroons(request.headers))
            try:
                auth_checker.allow(ctx, test_ops)
                resp = response(status_code=200,
                                content='done')
            except bakery.PermissionDenied:
                caveats = [
                    checkers.Caveat(location='http://0.3.2.1',
                                    condition='is-ok')
                ]
                m = server_bakery.oven.macaroon(
                    version=bakery.LATEST_VERSION,
                    expiry=datetime.utcnow() + timedelta(days=1),
                    caveats=caveats, ops=test_ops)
                content, headers = httpbakery.discharge_required_response(
                    m, '/',
                    'test',
                    'message')
                resp = response(
                    status_code=401,
                    content=content,
                    headers=headers,
                )
            return request.hooks['response'][0](resp)

        class InfoStorage:
            info = None

        @urlmatch(path='.*/discharge')
        def discharge(url, request):
            qs = parse_qs(request.body)
            if qs.get('caveat64') is not None:
                content = {q: qs[q][0] for q in qs}

                class InteractionRequiredError(Exception):
                    def __init__(self, error):
                        self.error = error

                class CheckerInError(bakery.ThirdPartyCaveatChecker):
                    def check_third_party_caveat(self, ctx, info):
                        InfoStorage.info = info
                        raise InteractionRequiredError(
                            httpbakery.Error(
                                code=httpbakery.ERR_INTERACTION_REQUIRED,
                                version=httpbakery.request_version(
                                    request.headers),
                                message='interaction required',
                                info=httpbakery.ErrorInfo(
                                    wait_url='http://0.3.2.1/wait?'
                                             'dischargeid=1',
                                    visit_url='http://0.3.2.1/visit?'
                                              'dischargeid=1'
                                ),
                            ),
                        )
                try:
                    httpbakery.discharge(
                        checkers.AuthContext(), content,
                        discharge_key, None, CheckerInError())
                except InteractionRequiredError as exc:
                    return response(
                        status_code=401,
                        content={
                            'Code': exc.error.code,
                            'Message': exc.error.message,
                            'Info': {
                                'WaitURL': exc.error.info.wait_url,
                                'VisitURL': exc.error.info.visit_url,
                            },
                        },
                        headers={'Content-Type': 'application/json'})

        key = bakery.generate_key()

        @urlmatch(path='.*/visit')
        def visit(url, request):
            if request.headers.get('Accept') == 'application/json':
                return {
                    'status_code': 200,
                    'content': {
                        'agent': '/agent-visit',
                    }
                }
            raise Exception('unexpected call to visit without Accept header')

        @urlmatch(path='.*/agent-visit')
        def agent_visit(url, request):
            if request.method != "POST":
                raise Exception('unexpected method')
            log.info('agent_visit url {}'.format(url))
            body = json.loads(request.body.decode('utf-8'))
            if body['username'] != 'test-user':
                raise Exception('unexpected username in body {!r}'.format(request.body))
            public_key = bakery.PublicKey.deserialize(body['public_key'])
            ms = httpbakery.extract_macaroons(request.headers)
            if len(ms) == 0:
                b = bakery.Bakery(key=discharge_key)
                m = b.oven.macaroon(
                    version=bakery.LATEST_VERSION,
                    expiry=datetime.utcnow() + timedelta(days=1),
                    caveats=[bakery.local_third_party_caveat(
                        public_key,
                        version=httpbakery.request_version(request.headers))],
                    ops=[bakery.Op(entity='agent', action='login')])
                content, headers = httpbakery.discharge_required_response(
                    m, '/',
                    'test',
                    'message')
                resp = response(status_code=401,
                                content=content,
                                headers=headers)
                return request.hooks['response'][0](resp)

            return {
                'status_code': 200,
                'content': {
                    'agent_login': True
                }
            }

        @urlmatch(path='.*/wait$')
        def wait(url, request):
            class EmptyChecker(bakery.ThirdPartyCaveatChecker):
                def check_third_party_caveat(self, ctx, info):
                    return []
            if InfoStorage.info is None:
                self.fail('visit url has not been visited')
            m = bakery.discharge(
                checkers.AuthContext(),
                InfoStorage.info.id,
                InfoStorage.info.caveat,
                discharge_key,
                EmptyChecker(),
                _DischargerLocator(),
            )
            return {
                'status_code': 200,
                'content': {
                    'Macaroon': m.to_dict()
                }
            }

        with HTTMock(server_get), \
                HTTMock(discharge), \
                HTTMock(visit), \
                HTTMock(wait), \
                HTTMock(agent_visit):
            client = httpbakery.Client(interaction_methods=[
                agent.AgentInteractor(
                    agent.AuthInfo(
                        key=key,
                        agents=[agent.Agent(username='test-user',
                                            url=u'http://0.3.2.1')],
                    ),
                ),
            ])
            resp = requests.get(
                'http://0.1.2.3/here',
                cookies=client.cookies,
                auth=client.auth(),
            )
        self.assertEqual(resp.content, b'done')


agent_file = '''
{
  "key": {
    "public": "YAhRSsth3a36mRYqQGQaLiS4QJax0p356nd+B8x7UQE=",
    "private": "CqoSgj06Zcgb4/S6RT4DpTjLAfKoznEY3JsShSjKJEU="
    },
  "agents": [{
    "url": "https://1.example.com/",
    "username": "user-1"
    }, {
    "url": "https://2.example.com/discharger",
    "username": "user-2"
  }, {
    "url": "http://0.3.2.1",
    "username": "test-user"
  }]
}
'''

bad_key_agent_file = '''
{
  "key": {
    "public": "YAhRSsth3a36mRYqQGQaLiS4QJax0p356nd+B8x7UQE=",
    "private": "CqoSgj06Zcgb4/S6RT4DpTjLAfKoznEY3JsShSjKJE=="
    },
  "agents": [{
    "url": "https://1.example.com/",
    "username": "user-1"
    }, {
    "url": "https://2.example.com/discharger",
    "username": "user-2"
  }]
}
'''


no_username_agent_file = '''
{
  "key": {
    "public": "YAhRSsth3a36mRYqQGQaLiS4QJax0p356nd+B8x7UQE=",
    "private": "CqoSgj06Zcgb4/S6RT4DpTjLAfKoznEY3JsShSjKJEU="
    },
  "agents": [{
    "url": "https://1.example.com/"
    }, {
    "url": "https://2.example.com/discharger",
    "username": "user-2"
  }]
}
'''


class ThirdPartyCaveatCheckerF(bakery.ThirdPartyCaveatChecker):
    def __init__(self, check):
        self._check = check

    def check_third_party_caveat(self, ctx, info):
        cond, arg = checkers.parse_caveat(info.condition)
        return self._check(cond, arg)

alwaysOK3rd = ThirdPartyCaveatCheckerF(lambda cond, arg: [])
