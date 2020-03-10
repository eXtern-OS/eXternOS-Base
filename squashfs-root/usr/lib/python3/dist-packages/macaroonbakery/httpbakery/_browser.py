# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import base64
from collections import namedtuple

import requests
from ._error import InteractionError
from ._interactor import (
    WEB_BROWSER_INTERACTION_KIND,
    DischargeToken,
    Interactor,
    LegacyInteractor,
)
from macaroonbakery._utils import visit_page_with_browser

from six.moves.urllib.parse import urljoin


class WebBrowserInteractor(Interactor, LegacyInteractor):
    ''' Handles web-browser-based interaction-required errors by opening a
    web browser to allow the user to prove their credentials interactively.
    '''
    def __init__(self, open=visit_page_with_browser):
        '''Create a WebBrowserInteractor that uses the given function
        to open a browser window. The open function is expected to take
        a single argument of string type, the URL to open.
        '''
        self._open_web_browser = open

    def kind(self):
        return WEB_BROWSER_INTERACTION_KIND

    def legacy_interact(self, ctx, location, visit_url):
        '''Implement LegacyInteractor.legacy_interact by opening the
        web browser window'''
        self._open_web_browser(visit_url)

    def interact(self, ctx, location, ir_err):
        '''Implement Interactor.interact by opening the browser window
        and waiting for the discharge token'''
        p = ir_err.interaction_method(self.kind(), WebBrowserInteractionInfo)
        if not location.endswith('/'):
            location += '/'
        visit_url = urljoin(location, p.visit_url)
        wait_token_url = urljoin(location, p.wait_token_url)
        self._open_web_browser(visit_url)
        return self._wait_for_token(ctx, wait_token_url)

    def _wait_for_token(self, ctx, wait_token_url):
        ''' Returns a token from a the wait token URL
        @param wait_token_url URL to wait for (string)
        :return DischargeToken
        '''
        resp = requests.get(wait_token_url)
        if resp.status_code != 200:
            raise InteractionError('cannot get {}'.format(wait_token_url))
        json_resp = resp.json()
        kind = json_resp.get('kind')
        if kind is None:
            raise InteractionError(
                'cannot get kind token from {}'.format(wait_token_url))
        token_val = json_resp.get('token')
        if token_val is None:
            token_val = json_resp.get('token64')
            if token_val is None:
                raise InteractionError(
                    'cannot get token from {}'.format(wait_token_url))
            token_val = base64.b64decode(token_val)
        return DischargeToken(kind=kind, value=token_val)


class WebBrowserInteractionInfo(namedtuple('WebBrowserInteractionInfo',
                                           'visit_url, wait_token_url')):
    ''' holds the information expected in the browser-window interaction
    entry in an interaction-required error.

    :param visit_url holds the URL to be visited in a web browser.
    :param wait_token_url holds a URL that will block on GET until the browser
    interaction has completed.
    '''
    @classmethod
    def from_dict(cls, info_dict):
        '''Create a new instance of WebBrowserInteractionInfo, as expected
        by the Error.interaction_method method.
        @param info_dict The deserialized JSON object
        @return a new WebBrowserInteractionInfo object.
        '''
        return WebBrowserInteractionInfo(
            visit_url=info_dict.get('VisitURL'),
            wait_token_url=info_dict.get('WaitTokenURL'))
