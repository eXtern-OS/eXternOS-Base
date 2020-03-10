# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import base64
import binascii
import json
import webbrowser
from datetime import datetime

import six
from pymacaroons import Macaroon
from pymacaroons.serializers import json_serializer

import six.moves.http_cookiejar as http_cookiejar
from six.moves.urllib.parse import urlparse


def to_bytes(s):
    '''Return s as a bytes type, using utf-8 encoding if necessary.
    @param s string or bytes
    @return bytes
    '''
    if isinstance(s, six.binary_type):
        return s
    if isinstance(s, six.string_types):
        return s.encode('utf-8')
    raise TypeError('want string or bytes, got {}', type(s))


def macaroon_from_dict(json_macaroon):
    '''Return a pymacaroons.Macaroon object from the given
    JSON-deserialized dict.

    @param JSON-encoded macaroon as dict
    @return the deserialized macaroon object.
    '''
    return Macaroon.deserialize(json.dumps(json_macaroon),
                                json_serializer.JsonSerializer())


def macaroon_to_dict(macaroon):
    '''Turn macaroon into JSON-serializable dict object
    @param pymacaroons.Macaroon.
    '''
    return json.loads(macaroon.serialize(json_serializer.JsonSerializer()))


def macaroon_to_json_string(macaroon):
    '''Serialize macaroon object to a JSON-encoded string.

    @param macaroon object to be serialized.
    @return a string serialization form of the macaroon.
    '''
    return macaroon.serialize(json_serializer.JsonSerializer())


def _add_base64_padding(b):
    '''Add padding to base64 encoded bytes.

    pymacaroons does not give padded base64 bytes from serialization.

    @param bytes b to be padded.
    @return a padded bytes.
    '''
    return b + b'=' * (-len(b) % 4)


def _remove_base64_padding(b):
    '''Remove padding from base64 encoded bytes.

    pymacaroons does not give padded base64 bytes from serialization.

    @param bytes b to be padded.
    @return a padded bytes.
    '''
    return b.rstrip(b'=')


def b64decode(s):
    '''Base64 decodes a base64-encoded string in URL-safe
    or normal format, with or without padding.
    The argument may be string or bytes.

    @param s bytes decode
    @return bytes decoded
    @raises ValueError on failure
    '''
    # add padding if necessary.
    s = to_bytes(s)
    if not s.endswith(b'='):
        s = s + b'=' * (-len(s) % 4)
    try:
        if '_' or '-' in s:
            return base64.urlsafe_b64decode(s)
        else:
            return base64.b64decode(s)
    except (TypeError, binascii.Error) as e:
        raise ValueError(str(e))


def raw_urlsafe_b64encode(b):
    '''Base64 encode using URL-safe encoding with padding removed.

    @param b bytes to decode
    @return bytes decoded
    '''
    b = to_bytes(b)
    b = base64.urlsafe_b64encode(b)
    b = b.rstrip(b'=')  # strip padding
    return b


def visit_page_with_browser(visit_url):
    '''Open a browser so the user can validate its identity.

    @param visit_url: where to prove your identity.
    '''
    webbrowser.open(visit_url, new=1)
    print('Opening an authorization web page in your browser.')
    print('If it does not open, please open this URL:\n', visit_url, '\n')


def cookie(
        url,
        name,
        value,
        expires=None):
    '''Return a new Cookie using a slightly more
    friendly API than that provided by six.moves.http_cookiejar

    @param name The cookie name {str}
    @param value The cookie value {str}
    @param url The URL path of the cookie {str}
    @param expires The expiry time of the cookie {datetime}. If provided,
        it must be a naive timestamp in UTC.
    '''
    u = urlparse(url)
    domain = u.hostname or u.netloc
    port = str(u.port) if u.port is not None else None
    secure = u.scheme == 'https'
    if expires is not None:
        if expires.tzinfo is not None:
            raise ValueError('Cookie expiration must be a naive datetime')
        expires = (expires - datetime(1970, 1, 1)).total_seconds()
    return http_cookiejar.Cookie(
        version=0,
        name=name,
        value=value,
        port=port,
        port_specified=port is not None,
        domain=domain,
        domain_specified=True,
        domain_initial_dot=False,
        path=u.path,
        path_specified=True,
        secure=secure,
        expires=expires,
        discard=False,
        comment=None,
        comment_url=None,
        rest=None,
        rfc2109=False,
    )
