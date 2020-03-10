# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import base64
import json

from ._versions import (VERSION_1, VERSION_2, VERSION_3)
from ._third_party import legacy_namespace, ThirdPartyCaveatInfo
from ._keys import PublicKey
from ._error import VerificationError
import macaroonbakery.checkers as checkers
import nacl.public
import six

_PUBLIC_KEY_PREFIX_LEN = 4
_KEY_LEN = 32
# version3CaveatMinLen holds an underestimate of the
# minimum length of a version 3 caveat.
_VERSION3_CAVEAT_MIN_LEN = 1 + 4 + 32 + 24 + 16 + 1


def encode_caveat(condition, root_key, third_party_info, key, ns):
    '''Encrypt a third-party caveat.

    The third_party_info key holds information about the
    third party we're encrypting the caveat for; the key is the
    public/private key pair of the party that's adding the caveat.

    The caveat will be encoded according to the version information
    found in third_party_info.

    @param condition string
    @param root_key bytes
    @param third_party_info object
    @param key nacl key
    @param ns not used yet
    @return bytes
    '''
    if third_party_info.version == VERSION_1:
        return _encode_caveat_v1(condition, root_key,
                                 third_party_info.public_key, key)
    if (third_party_info.version == VERSION_2 or
            third_party_info.version == VERSION_3):
        return _encode_caveat_v2_v3(third_party_info.version, condition,
                                    root_key, third_party_info.public_key,
                                    key, ns)
    raise NotImplementedError('only bakery v1, v2, v3 supported')


def _encode_caveat_v1(condition, root_key, third_party_pub_key, key):
    '''Create a JSON-encoded third-party caveat.

    The third_party_pub_key key represents the PublicKey of the third party
    we're encrypting the caveat for; the key is the public/private key pair of
    the party that's adding the caveat.

    @param condition string
    @param root_key bytes
    @param third_party_pub_key (PublicKey)
    @param key (PrivateKey)
    @return a base64 encoded bytes
    '''
    plain_data = json.dumps({
        'RootKey': base64.b64encode(root_key).decode('ascii'),
        'Condition': condition
    })
    box = nacl.public.Box(key.key, third_party_pub_key.key)

    encrypted = box.encrypt(six.b(plain_data))
    nonce = encrypted[0:nacl.public.Box.NONCE_SIZE]
    encrypted = encrypted[nacl.public.Box.NONCE_SIZE:]
    return base64.b64encode(six.b(json.dumps({
        'ThirdPartyPublicKey': str(third_party_pub_key),
        'FirstPartyPublicKey': str(key.public_key),
        'Nonce': base64.b64encode(nonce).decode('ascii'),
        'Id': base64.b64encode(encrypted).decode('ascii')
    })))


def _encode_caveat_v2_v3(version, condition, root_key, third_party_pub_key,
                         key, ns):
    '''Create a version 2 or version 3 third-party caveat.

    The format has the following packed binary fields (note
    that all fields up to and including the nonce are the same
    as the v2 format):

        version 2 or 3 [1 byte]
        first 4 bytes of third-party Curve25519 public key [4 bytes]
        first-party Curve25519 public key [32 bytes]
        nonce [24 bytes]
        encrypted secret part [rest of message]

    The encrypted part encrypts the following fields
    with box.Seal:

        version 2 or 3 [1 byte]
        length of root key [n: uvarint]
        root key [n bytes]
        length of encoded namespace [n: uvarint] (Version 3 only)
        encoded namespace [n bytes] (Version 3 only)
        condition [rest of encrypted part]
    '''
    ns_data = bytearray()
    if version >= VERSION_3:
        ns_data = ns.serialize_text()
    data = bytearray()
    data.append(version)
    data.extend(third_party_pub_key.serialize(raw=True)[:_PUBLIC_KEY_PREFIX_LEN])
    data.extend(key.public_key.serialize(raw=True)[:])
    secret = _encode_secret_part_v2_v3(version, condition, root_key, ns_data)
    box = nacl.public.Box(key.key, third_party_pub_key.key)
    encrypted = box.encrypt(secret)
    nonce = encrypted[0:nacl.public.Box.NONCE_SIZE]
    encrypted = encrypted[nacl.public.Box.NONCE_SIZE:]
    data.extend(nonce[:])
    data.extend(encrypted)
    return bytes(data)


def _encode_secret_part_v2_v3(version, condition, root_key, ns):
    '''Creates a version 2 or version 3 secret part of the third party
    caveat. The returned data is not encrypted.

    The format has the following packed binary fields:
    version 2 or 3 [1 byte]
    root key length [n: uvarint]
    root key [n bytes]
    namespace length [n: uvarint] (v3 only)
    namespace [n bytes] (v3 only)
    predicate [rest of message]
    '''
    data = bytearray()
    data.append(version)
    encode_uvarint(len(root_key), data)
    data.extend(root_key)
    if version >= VERSION_3:
        encode_uvarint(len(ns), data)
        data.extend(ns)
    data.extend(condition.encode('utf-8'))
    return bytes(data)


def decode_caveat(key, caveat):
    '''Decode caveat by decrypting the encrypted part using key.

    @param key the nacl private key to decode.
    @param caveat bytes.
    @return ThirdPartyCaveatInfo
    '''
    if len(caveat) == 0:
        raise VerificationError('empty third party caveat')

    first = caveat[:1]
    if first == b'e':
        # 'e' will be the first byte if the caveatid is a base64
        # encoded JSON object.
        return _decode_caveat_v1(key, caveat)
    first_as_int = six.byte2int(first)
    if (first_as_int == VERSION_2 or
            first_as_int == VERSION_3):
        if (len(caveat) < _VERSION3_CAVEAT_MIN_LEN
                and first_as_int == VERSION_3):
            # If it has the version 3 caveat tag and it's too short, it's
            # almost certainly an id, not an encrypted payload.
            raise VerificationError(
                'caveat id payload not provided for caveat id {}'.format(
                    caveat))
        return _decode_caveat_v2_v3(first_as_int, key, caveat)
    raise VerificationError('unknown version for caveat')


def _decode_caveat_v1(key, caveat):
    '''Decode a base64 encoded JSON id.

    @param key the nacl private key to decode.
    @param caveat a base64 encoded JSON string.
    '''

    data = base64.b64decode(caveat).decode('utf-8')
    wrapper = json.loads(data)
    tp_public_key = nacl.public.PublicKey(
        base64.b64decode(wrapper['ThirdPartyPublicKey']))
    if key.public_key.key != tp_public_key:
        raise Exception('public key mismatch')  # TODO

    if wrapper.get('FirstPartyPublicKey', None) is None:
        raise Exception('target service public key not specified')

    # The encrypted string is base64 encoded in the JSON representation.
    secret = base64.b64decode(wrapper.get('Id'))
    nonce = base64.b64decode(wrapper.get('Nonce'))

    fp_public_key = nacl.public.PublicKey(base64.b64decode(
        wrapper.get('FirstPartyPublicKey')))

    box = nacl.public.Box(key.key, fp_public_key)
    c = box.decrypt(secret, nonce)
    record = json.loads(c.decode('utf-8'))
    fp_key = nacl.public.PublicKey(
        base64.b64decode(wrapper.get('FirstPartyPublicKey')))
    return ThirdPartyCaveatInfo(
        condition=record.get('Condition'),
        first_party_public_key=PublicKey(fp_key),
        third_party_key_pair=key,
        root_key=base64.b64decode(record.get('RootKey')),
        caveat=caveat,
        id=None,
        version=VERSION_1,
        namespace=legacy_namespace()
    )


def _decode_caveat_v2_v3(version, key, caveat):
    '''Decodes a version 2 or version 3 caveat.
    '''
    if (len(caveat) < 1 + _PUBLIC_KEY_PREFIX_LEN +
            _KEY_LEN + nacl.public.Box.NONCE_SIZE + 16):
        raise VerificationError('caveat id too short')
    original_caveat = caveat
    caveat = caveat[1:]  # skip version (already checked)

    pk_prefix = caveat[:_PUBLIC_KEY_PREFIX_LEN]
    caveat = caveat[_PUBLIC_KEY_PREFIX_LEN:]
    if key.public_key.serialize(raw=True)[:_PUBLIC_KEY_PREFIX_LEN] != pk_prefix:
        raise VerificationError('public key mismatch')

    first_party_pub = caveat[:_KEY_LEN]
    caveat = caveat[_KEY_LEN:]
    nonce = caveat[:nacl.public.Box.NONCE_SIZE]
    caveat = caveat[nacl.public.Box.NONCE_SIZE:]
    fp_public_key = nacl.public.PublicKey(first_party_pub)
    box = nacl.public.Box(key.key, fp_public_key)
    data = box.decrypt(caveat, nonce)
    root_key, condition, ns = _decode_secret_part_v2_v3(version, data)
    return ThirdPartyCaveatInfo(
        condition=condition.decode('utf-8'),
        first_party_public_key=PublicKey(fp_public_key),
        third_party_key_pair=key,
        root_key=root_key,
        caveat=original_caveat,
        version=version,
        id=None,
        namespace=ns
    )


def _decode_secret_part_v2_v3(version, data):
    if len(data) < 1:
        raise VerificationError('secret part too short')
    got_version = six.byte2int(data[:1])
    data = data[1:]
    if version != got_version:
        raise VerificationError(
            'unexpected secret part version, got {} want {}'.format(
                got_version, version))
    root_key_length, read = decode_uvarint(data)
    data = data[read:]
    root_key = data[:root_key_length]
    data = data[root_key_length:]
    if version >= VERSION_3:
        namespace_length, read = decode_uvarint(data)
        data = data[read:]
        ns_data = data[:namespace_length]
        data = data[namespace_length:]
        ns = checkers.deserialize_namespace(ns_data)
    else:
        ns = legacy_namespace()
    return root_key, data, ns


def encode_uvarint(n, data):
    '''encodes integer into variable-length format into data.'''
    if n < 0:
        raise ValueError('only support positive integer')
    while True:
        this_byte = n & 127
        n >>= 7
        if n == 0:
            data.append(this_byte)
            break
        data.append(this_byte | 128)


def decode_uvarint(data):
    '''Decode a variable-length integer.

    Reads a sequence of unsigned integer byte and decodes them into an integer
    in variable-length format and returns it and the length read.
    '''
    n = 0
    shift = 0
    length = 0
    for b in data:
        if not isinstance(b, int):
            b = six.byte2int(b)
        n |= (b & 0x7f) << shift
        length += 1
        if (b & 0x80) == 0:
            break
        shift += 7
    return n, length
