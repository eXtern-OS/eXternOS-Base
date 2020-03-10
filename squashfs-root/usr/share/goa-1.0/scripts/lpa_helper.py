#!/usr/bin/env python3
import json
import os
import sys

from urllib.parse import urlencode
import requests  # fades
import macaroonbakery  # fades
import pymacaroons  # fades
from macaroonbakery import httpbakery  # fades


LIVEPATCH_AUTH_ROOT_URL = os.environ.get(
    'LIVEPATCH_AUTH_ROOT_URL', 'https://auth.livepatch.canonical.com')
UBUNTU_SSO_ROOT_URL = os.environ.get(
    'UBUNTU_SSO_ROOT_URL', 'https://login.ubuntu.com')

generic_error = "GENERIC_ERROR"


class AuthenticationFailed(Exception):
    def __init__(self, code, msg):
        super(AuthenticationFailed, self).__init__(msg)
        self.code = code

class USSOMacaroonInteractor(httpbakery.LegacyInteractor):

    def __init__(self, session):
        self.session = requests.Session()

    def kind(self):
        return "interactive"

    def legacy_interact(self, client, location, visit_url):
        # get usso_macaroon
        usso_url = self.get_usso_macaroon_url(visit_url)
        usso_macaroon = self.get_usso_macaroon(usso_url)

        def callback(discharges):
            self.complete_usso_macaroon_discharge(usso_url, discharges)
        discharges = self.discharge_usso_macaroon(usso_macaroon, callback)


    def get_usso_macaroon_url(self, url):
        # find interaction methods for discharge
        response = self.session.get(
            url, headers={'Accept': 'application/json'})
        if not response.ok:
            raise AuthenticationFailed(generic_error, 'can not find interaction methods')

        data = response.json()

        # expect usso_macaroon interaction method
        if 'usso_macaroon' not in data:
            raise AuthenticationFailed(generic_error, 'missing usso_macaroon interaction method')
        return data['usso_macaroon']

    def get_usso_macaroon(self, url):
        response = self.session.get(url)
        if not response.ok:
            raise AuthenticationFailed(generic_error, 'can not get usso macaroon')
        usso_macaroon = response.json()['macaroon']
        return usso_macaroon

    def discharge_usso_macaroon(self, macaroon, callback):
        usso_caveats = [
            cav['cid'] for cav in macaroon.get('caveats', [])
            if cav.get('cl') == UBUNTU_SSO_ROOT_URL]
        if len(usso_caveats) <= 0:
            raise AuthenticationFailed(generic_error, 'no valid usso caveat found')

        data = {'caveat_id': usso_caveats[0]}
        data.update(get_usso_credentials())

        def _discharge_macaroon(data):
            response = self.session.post(
                '{}/api/v2/tokens/discharge'.format(UBUNTU_SSO_ROOT_URL),
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'})
            return response

        response = _discharge_macaroon(data)
        if not response.ok:
            if response.status_code in (400, 401, 403):
                raise AuthenticationFailed(response.json().get('code'), response.json().get('message'))
            else:
                raise AuthenticationFailed(generic_error, 'authentication issue')

        root_m = macaroonbakery.bakery.Macaroon.deserialize_json(
            json.dumps(macaroon)).macaroon
        discharge_m = pymacaroons.Macaroon.deserialize(
            response.json()['discharge_macaroon'])
        bound_discharge = root_m.prepare_for_request(discharge_m)

        callback([root_m.serialize(), bound_discharge.serialize()])

    def complete_usso_macaroon_discharge(self, url, discharges):
        data = {'macaroons': discharges}
        response = self.session.post(
            url, data=json.dumps(data),
            headers={'Content-Type': 'application/json'})
        if not response.ok:
            raise AuthenticationFailed(generic_error, 'can not complete usso macaroon discharge')


def get_usso_credentials():
    email = input('Email: ')
    password = input('Password: ')
    ret = {'email': email, 'password': password}
    otp = input('Two-factor code: ')
    if otp and len(otp) > 0:
        ret.update({'otp': otp})
    return ret

def get_lpa_token(session):
    url = '{}/api/v1/tokens?{}'.format(
        LIVEPATCH_AUTH_ROOT_URL, urlencode({'token_type': 'user'}))
    return session.get(url, timeout=10)

if __name__ == '__main__':
    cookies = requests.cookies.RequestsCookieJar()
    session = requests.Session()

    client = httpbakery.Client(
        interaction_methods=[USSOMacaroonInteractor(session)], cookies=cookies)

    session.auth = client.auth()
    session.cookies = cookies

    try:
        response = get_lpa_token(session)
        if response.ok:
            print(response.json()['token'], file=sys.stderr)
    except AuthenticationFailed as af:
        print(af.code, af, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(generic_error, e, file=sys.stderr)
        sys.exit(1)
