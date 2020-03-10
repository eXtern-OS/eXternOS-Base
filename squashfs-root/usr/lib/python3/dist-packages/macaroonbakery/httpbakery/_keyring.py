# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import macaroonbakery.bakery as bakery
import requests
from ._error import BAKERY_PROTOCOL_HEADER

from six.moves.urllib.parse import urlparse


class ThirdPartyLocator(bakery.ThirdPartyLocator):
    ''' Implements macaroonbakery.ThirdPartyLocator by first looking in the
    backing cache and, if that fails, making an HTTP request to find the
    information associated with the given discharge location.
    '''

    def __init__(self, allow_insecure=False):
        '''
        @param url: the url to retrieve public_key
        @param allow_insecure: By default it refuses to use insecure URLs.
        '''
        self._allow_insecure = allow_insecure
        self._cache = {}

    def third_party_info(self, loc):
        u = urlparse(loc)
        if u.scheme != 'https' and not self._allow_insecure:
            raise bakery.ThirdPartyInfoNotFound(
                'untrusted discharge URL {}'.format(loc))
        loc = loc.rstrip('/')
        info = self._cache.get(loc)
        if info is not None:
            return info
        url_endpoint = '/discharge/info'
        headers = {
            BAKERY_PROTOCOL_HEADER: str(bakery.LATEST_VERSION)
        }
        resp = requests.get(url=loc + url_endpoint, headers=headers)
        status_code = resp.status_code
        if status_code == 404:
            url_endpoint = '/publickey'
            resp = requests.get(url=loc + url_endpoint, headers=headers)
            status_code = resp.status_code
        if status_code != 200:
            raise bakery.ThirdPartyInfoNotFound(
                'unable to get info from {}'.format(url_endpoint))
        json_resp = resp.json()
        if json_resp is None:
            raise bakery.ThirdPartyInfoNotFound(
                'no response from /discharge/info')
        pk = json_resp.get('PublicKey')
        if pk is None:
            raise bakery.ThirdPartyInfoNotFound(
                'no public key found in /discharge/info')
        idm_pk = bakery.PublicKey.deserialize(pk)
        version = json_resp.get('Version', bakery.VERSION_1)
        self._cache[loc] = bakery.ThirdPartyInfo(
            version=version,
            public_key=idm_pk
        )
        return self._cache.get(loc)
