# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import abc
import base64
import json
import logging
import os

import macaroonbakery.checkers as checkers
import pymacaroons
from macaroonbakery._utils import b64decode
from pymacaroons.serializers import json_serializer
from ._versions import (
    LATEST_VERSION,
    VERSION_0,
    VERSION_1,
    VERSION_2,
    VERSION_3,
)
from ._error import (
    ThirdPartyInfoNotFound,
)
from ._codec import (
    encode_uvarint,
    encode_caveat,
)
from ._keys import PublicKey
from ._third_party import (
    legacy_namespace,
    ThirdPartyInfo,
)

log = logging.getLogger(__name__)


class Macaroon(object):
    '''Represent an undischarged macaroon along with its first
    party caveat namespace and associated third party caveat information
    which should be passed to the third party when discharging a caveat.
    '''

    def __init__(self, root_key, id, location=None,
                 version=LATEST_VERSION, namespace=None):
        '''Creates a new macaroon with the given root key, id and location.

        If the version is more than the latest known version,
        the latest known version will be used. The namespace should hold the
        namespace of the service that is creating the macaroon.
        @param root_key bytes or string
        @param id bytes or string
        @param location bytes or string
        @param version the bakery version.
        @param namespace is that of the service creating it
        '''
        if version > LATEST_VERSION:
            log.info('use last known version:{} instead of: {}'.format(
                LATEST_VERSION, version
            ))
            version = LATEST_VERSION
        # m holds the underlying macaroon.
        self._macaroon = pymacaroons.Macaroon(
            location=location, key=root_key, identifier=id,
            version=macaroon_version(version))
        # version holds the version of the macaroon.
        self._version = version
        self._caveat_data = {}
        if namespace is None:
            namespace = checkers.Namespace()
        self._namespace = namespace
        self._caveat_id_prefix = bytearray()

    @property
    def macaroon(self):
        ''' Return the underlying macaroon.
        '''
        return self._macaroon

    @property
    def version(self):
        return self._version

    @property
    def namespace(self):
        return self._namespace

    @property
    def caveat_data(self):
        return self._caveat_data

    def add_caveat(self, cav, key=None, loc=None):
        '''Add a caveat to the macaroon.

        It encrypts it using the given key pair
        and by looking up the location using the given locator.
        As a special case, if the caveat's Location field has the prefix
        "local " the caveat is added as a client self-discharge caveat using
        the public key base64-encoded in the rest of the location. In this
        case, the Condition field must be empty. The resulting third-party
        caveat will encode the condition "true" encrypted with that public
        key.

        @param cav the checkers.Caveat to be added.
        @param key the public key to encrypt third party caveat.
        @param loc locator to find information on third parties when adding
        third party caveats. It is expected to have a third_party_info method
        that will be called with a location string and should return a
        ThirdPartyInfo instance holding the requested information.
        '''
        if cav.location is None:
            self._macaroon.add_first_party_caveat(
                self.namespace.resolve_caveat(cav).condition)
            return
        if key is None:
            raise ValueError(
                'no private key to encrypt third party caveat')
        local_info = _parse_local_location(cav.location)
        if local_info is not None:
            info = local_info
            if cav.condition is not '':
                raise ValueError(
                    'cannot specify caveat condition in '
                    'local third-party caveat')
            cav = checkers.Caveat(location='local', condition='true')
        else:
            if loc is None:
                raise ValueError(
                    'no locator when adding third party caveat')
            info = loc.third_party_info(cav.location)

        root_key = os.urandom(24)

        # Use the least supported version to encode the caveat.
        if self._version < info.version:
            info = ThirdPartyInfo(
                version=self._version,
                public_key=info.public_key,
            )

        caveat_info = encode_caveat(
            cav.condition, root_key, info, key, self._namespace)
        if info.version < VERSION_3:
            # We're encoding for an earlier client or third party which does
            # not understand bundled caveat info, so use the encoded
            # caveat information as the caveat id.
            id = caveat_info
        else:
            id = self._new_caveat_id(self._caveat_id_prefix)
            self._caveat_data[id] = caveat_info

        self._macaroon.add_third_party_caveat(cav.location, root_key, id)

    def add_caveats(self, cavs, key, loc):
        '''Add an array of caveats to the macaroon.

        This method does not mutate the current object.
        @param cavs arrary of caveats.
        @param key the PublicKey to encrypt third party caveat.
        @param loc locator to find the location object that has a method
        third_party_info.
        '''
        if cavs is None:
            return
        for cav in cavs:
            self.add_caveat(cav, key, loc)

    def serialize_json(self):
        '''Return a string holding the macaroon data in JSON format.
        @return a string holding the macaroon data in JSON format
        '''
        return json.dumps(self.to_dict())

    def to_dict(self):
        '''Return a dict representation of the macaroon data in JSON format.
        @return a dict
        '''
        if self.version < VERSION_3:
            if len(self._caveat_data) > 0:
                raise ValueError('cannot serialize pre-version3 macaroon with '
                                 'external caveat data')
            return json.loads(self._macaroon.serialize(
                json_serializer.JsonSerializer()))
        serialized = {
            'm': json.loads(self._macaroon.serialize(
                json_serializer.JsonSerializer())),
            'v': self._version,
        }
        if self._namespace is not None:
            serialized['ns'] = self._namespace.serialize_text().decode('utf-8')
        caveat_data = {}
        for id in self._caveat_data:
            key = base64.b64encode(id).decode('utf-8')
            value = base64.b64encode(self._caveat_data[id]).decode('utf-8')
            caveat_data[key] = value
        if len(caveat_data) > 0:
            serialized['cdata'] = caveat_data
        return serialized

    @classmethod
    def from_dict(cls, json_dict):
        '''Return a macaroon obtained from the given dictionary as
        deserialized from JSON.
        @param json_dict The deserialized JSON object.
        '''
        json_macaroon = json_dict.get('m')
        if json_macaroon is None:
            # Try the v1 format if we don't have a macaroon field.
            m = pymacaroons.Macaroon.deserialize(
                json.dumps(json_dict), json_serializer.JsonSerializer())
            macaroon = Macaroon(root_key=None, id=None,
                                namespace=legacy_namespace(),
                                version=_bakery_version(m.version))
            macaroon._macaroon = m
            return macaroon

        version = json_dict.get('v', None)
        if version is None:
            raise ValueError('no version specified')
        if (version < VERSION_3 or
                version > LATEST_VERSION):
            raise ValueError('unknown bakery version {}'.format(version))
        m = pymacaroons.Macaroon.deserialize(json.dumps(json_macaroon),
                                             json_serializer.JsonSerializer())
        if m.version != macaroon_version(version):
            raise ValueError(
                'underlying macaroon has inconsistent version; '
                'got {} want {}'.format(m.version, macaroon_version(version)))
        namespace = checkers.deserialize_namespace(json_dict.get('ns'))
        cdata = json_dict.get('cdata', {})
        caveat_data = {}
        for id64 in cdata:
            id = b64decode(id64)
            data = b64decode(cdata[id64])
            caveat_data[id] = data
        macaroon = Macaroon(root_key=None, id=None,
                            namespace=namespace,
                            version=version)
        macaroon._caveat_data = caveat_data
        macaroon._macaroon = m
        return macaroon

    @classmethod
    def deserialize_json(cls, serialized_json):
        '''Return a macaroon deserialized from a string
        @param serialized_json The string to decode {str}
        @return {Macaroon}
        '''
        serialized = json.loads(serialized_json)
        return Macaroon.from_dict(serialized)

    def _new_caveat_id(self, base):
        '''Return a third party caveat id

        This does not duplicate any third party caveat ids already inside
        macaroon. If base is non-empty, it is used as the id prefix.

        @param base bytes
        @return bytes
        '''
        id = bytearray()
        if len(base) > 0:
            id.extend(base)
        else:
            # Add a version byte to the caveat id. Technically
            # this is unnecessary as the caveat-decoding logic
            # that looks at versions should never see this id,
            # but if the caveat payload isn't provided with the
            # payload, having this version gives a strong indication
            # that the payload has been omitted so we can produce
            # a better error for the user.
            id.append(VERSION_3)

        # Iterate through integers looking for one that isn't already used,
        # starting from n so that if everyone is using this same algorithm,
        # we'll only perform one iteration.
        i = len(self._caveat_data)
        caveats = self._macaroon.caveats
        while True:
            # We append a varint to the end of the id and assume that
            # any client that's created the id that we're using as a base
            # is using similar conventions - in the worst case they might
            # end up with a duplicate third party caveat id and thus create
            # a macaroon that cannot be discharged.
            temp = id[:]
            encode_uvarint(i, temp)
            found = False
            for cav in caveats:
                if (cav.verification_key_id is not None
                        and cav.caveat_id == temp):
                    found = True
                    break
            if not found:
                return bytes(temp)
            i += 1

    def first_party_caveats(self):
        '''Return the first party caveats from this macaroon.

        @return the first party caveats from this macaroon as pymacaroons
        caveats.
        '''
        return self._macaroon.first_party_caveats()

    def third_party_caveats(self):
        '''Return the third party caveats.

        @return the third party caveats as pymacaroons caveats.
        '''
        return self._macaroon.third_party_caveats()

    def copy(self):
        ''' Returns a copy of the macaroon. Note that the the new
        macaroon's namespace still points to the same underlying Namespace -
        copying the macaroon does not make a copy of the namespace.
        :return a Macaroon
        '''
        m1 = Macaroon(None, None, version=self._version,
                      namespace=self._namespace)
        m1._macaroon = self._macaroon.copy()
        m1._caveat_data = self._caveat_data.copy()
        return m1


def macaroon_version(bakery_version):
    '''Return the macaroon version given the bakery version.

    @param bakery_version the bakery version
    @return macaroon_version the derived macaroon version
    '''
    if bakery_version in [VERSION_0, VERSION_1]:
        return pymacaroons.MACAROON_V1
    return pymacaroons.MACAROON_V2


class ThirdPartyLocator(object):
    '''Used to find information on third party discharge services.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def third_party_info(self, loc):
        '''Return information on the third party at the given location.
        @param loc string
        @return: a ThirdPartyInfo
        @raise: ThirdPartyInfoNotFound
        '''
        raise NotImplementedError('third_party_info method must be defined in '
                                  'subclass')


class ThirdPartyStore(ThirdPartyLocator):
    ''' Implements a simple in memory ThirdPartyLocator.
    '''
    def __init__(self):
        self._store = {}

    def third_party_info(self, loc):
        info = self._store.get(loc.rstrip('/'))
        if info is None:
            raise ThirdPartyInfoNotFound(
                'cannot retrieve the info for location {}'.format(loc))
        return info

    def add_info(self, loc, info):
        '''Associates the given information with the given location.
        It will ignore any trailing slash.
        @param loc the location as string
        @param info (ThirdPartyInfo) to store for this location.
        '''
        self._store[loc.rstrip('/')] = info


def _parse_local_location(loc):
    '''Parse a local caveat location as generated by LocalThirdPartyCaveat.

    This is of the form:

        local <version> <pubkey>

    where <version> is the bakery version of the client that we're
    adding the local caveat for.

    It returns None if the location does not represent a local
    caveat location.
    @return a ThirdPartyInfo.
    '''
    if not (loc.startswith('local ')):
        return None
    v = VERSION_1
    fields = loc.split()
    fields = fields[1:]  # Skip 'local'
    if len(fields) == 2:
        try:
            v = int(fields[0])
        except ValueError:
            return None
        fields = fields[1:]
    if len(fields) == 1:
        key = PublicKey.deserialize(fields[0])
        return ThirdPartyInfo(public_key=key, version=v)
    return None


def _bakery_version(v):
    # bakery_version returns a bakery version that corresponds to
    # the macaroon version v. It is necessarily approximate because
    # several bakery versions can correspond to a single macaroon
    # version, so it's only of use when decoding legacy formats
    #
    # It will raise a ValueError if it doesn't recognize the version.
    if v == pymacaroons.MACAROON_V1:
        # Use version 1 because we don't know of any existing
        # version 0 clients.
        return VERSION_1
    elif v == pymacaroons.MACAROON_V2:
        # Note that this could also correspond to Version 3, but
        # this logic is explicitly for legacy versions.
        return VERSION_2
    else:
        raise ValueError('unknown macaroon version when deserializing legacy '
                         'bakery macaroon; got {}'.format(v))


class MacaroonJSONEncoder(json.JSONEncoder):
    def encode(self, m):
        return m.serialize_json()


class MacaroonJSONDecoder(json.JSONDecoder):
    def decode(self, s, _w=json.decoder.WHITESPACE.match):
        return Macaroon.deserialize_json(s)
