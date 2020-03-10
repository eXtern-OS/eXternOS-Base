# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import copy
import json
import logging
from collections import namedtuple

import macaroonbakery.bakery as bakery
import macaroonbakery.httpbakery as httpbakery
import macaroonbakery._utils as utils
import requests.cookies

from six.moves.urllib.parse import urljoin

log = logging.getLogger(__name__)


class AgentFileFormatError(Exception):
    ''' AgentFileFormatError is the exception raised when an agent file has a
        bad structure.
    '''
    pass


def load_auth_info(filename):
    '''Loads agent authentication information from the specified file.
    The returned information is suitable for passing as an argument
    to the AgentInteractor constructor.
    @param filename The name of the file to open (str)
    @return AuthInfo The authentication information
    @raises AgentFileFormatError when the file format is bad.
    '''
    with open(filename) as f:
        return read_auth_info(f.read())


def read_auth_info(agent_file_content):
    '''Loads agent authentication information from the
    specified content string, as read from an agents file.
    The returned information is suitable for passing as an argument
    to the AgentInteractor constructor.
    @param agent_file_content The agent file content (str)
    @return AuthInfo The authentication information
    @raises AgentFileFormatError when the file format is bad.
    '''
    try:
        data = json.loads(agent_file_content)
        return AuthInfo(
            key=bakery.PrivateKey.deserialize(data['key']['private']),
            agents=list(
                Agent(url=a['url'], username=a['username'])
                for a in data.get('agents', [])
            ),
        )
    except (
        KeyError,
        ValueError,
        TypeError,
    ) as e:
        raise AgentFileFormatError('invalid agent file', e)


class InteractionInfo(object):
    '''Holds the information expected in the agent interaction entry in an
    interaction-required error.
    '''
    def __init__(self, login_url):
        self._login_url = login_url

    @property
    def login_url(self):
        ''' Return the URL from which to acquire a macaroon that can be used
        to complete the agent login. To acquire the macaroon, make a POST
        request to the URL with user and public-key parameters.
        :return string
        '''
        return self._login_url

    @classmethod
    def from_dict(cls, json_dict):
        '''Return an InteractionInfo obtained from the given dictionary as
        deserialized from JSON.
        @param json_dict The deserialized JSON object.
        '''
        return InteractionInfo(json_dict.get('login-url'))


class AgentInteractor(httpbakery.Interactor, httpbakery.LegacyInteractor):
    ''' Interactor that performs interaction using the agent login protocol.
    '''
    def __init__(self, auth_info):
        self._auth_info = auth_info

    def kind(self):
        '''Implement Interactor.kind by returning the agent kind'''
        return 'agent'

    def interact(self, client, location, interaction_required_err):
        '''Implement Interactor.interact by obtaining obtaining
        a macaroon from the discharger, discharging it with the
        local private key using the discharged macaroon as
        a discharge token'''
        p = interaction_required_err.interaction_method('agent',
                                                        InteractionInfo)
        if p.login_url is None or p.login_url == '':
            raise httpbakery.InteractionError(
                'no login-url field found in agent interaction method')
        agent = self._find_agent(location)
        if not location.endswith('/'):
            location += '/'
        login_url = urljoin(location, p.login_url)
        resp = requests.get(
            login_url, params={
                'username': agent.username,
                'public-key': str(self._auth_info.key.public_key)},
            auth=client.auth())
        if resp.status_code != 200:
            raise httpbakery.InteractionError(
                'cannot acquire agent macaroon: {} {}'.format(
                    resp.status_code, resp.text)
            )
        m = resp.json().get('macaroon')
        if m is None:
            raise httpbakery.InteractionError('no macaroon in response')
        m = bakery.Macaroon.from_dict(m)
        ms = bakery.discharge_all(m, None, self._auth_info.key)
        b = bytearray()
        for m in ms:
            b.extend(utils.b64decode(m.serialize()))
        return httpbakery.DischargeToken(kind='agent', value=bytes(b))

    def _find_agent(self, location):
        ''' Finds an appropriate agent entry for the given location.
        :return Agent
        '''
        for a in self._auth_info.agents:
            # Don't worry about trailing slashes
            if a.url.rstrip('/') == location.rstrip('/'):
                return a
        raise httpbakery.InteractionMethodNotFound(
            'cannot find username for discharge location {}'.format(location))

    def legacy_interact(self, client, location, visit_url):
        '''Implement LegacyInteractor.legacy_interact by obtaining
        the discharge macaroon using the client's private key
        '''
        agent = self._find_agent(location)
        # Shallow-copy the client so that we don't unexpectedly side-effect
        # it by changing the key. Another possibility might be to
        # set up agent authentication differently, in such a way that
        # we're sure that client.key is the same as self._auth_info.key.
        client = copy.copy(client)
        client.key = self._auth_info.key
        resp = client.request(
            method='POST',
            url=visit_url,
            json={
                'username': agent.username,
                'public_key': str(self._auth_info.key.public_key),
            },
        )
        if resp.status_code != 200:
            raise httpbakery.InteractionError(
                'cannot acquire agent macaroon from {}: {} (response body: {!r})'.format(visit_url, resp.status_code, resp.text))
        if not resp.json().get('agent_login', False):
            raise httpbakery.InteractionError('agent login failed')


class Agent(namedtuple('Agent', 'url, username')):
    ''' Represents an agent that can be used for agent authentication.
    @param url(string) holds the URL of the discharger that knows about
    the agent.
    @param username holds the username agent (string).
    '''


class AuthInfo(namedtuple('AuthInfo', 'key, agents')):
    ''' Holds the agent information required to set up agent authentication
    information.

    It holds the agent's private key and information about the username
    associated with each known agent-authentication server.
    @param key the agent's private key (bakery.PrivateKey).
    @param agents information about the known agents (list of Agent).
    '''
