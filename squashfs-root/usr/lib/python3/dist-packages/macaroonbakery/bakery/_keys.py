# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.

import nacl.public


class PrivateKey(object):
    ''' A private key used by the bakery to encrypt and decrypt
    third party caveats.
    Internally, it is a 256-bit Ed25519 private key.
    '''
    def __init__(self, key):
        self._key = key

    @property
    def key(self):
        ''' Internal nacl key representation.
        '''
        return self._key

    @property
    def public_key(self):
        '''
        :return: the PublicKey associated with the private key.
        '''
        return PublicKey(self._key.public_key)

    @classmethod
    def deserialize(cls, serialized):
        ''' Create a PrivateKey from a base64 encoded bytes.
        :return: a PrivateKey
        '''
        return PrivateKey(
            nacl.public.PrivateKey(serialized,
                                   encoder=nacl.encoding.Base64Encoder))

    def serialize(self, raw=False):
        '''Encode the private part of the key in a base64 format by default,
        but when raw is True it will return hex encoded bytes.
        @return: bytes
        '''
        if raw:
            return self._key.encode()
        return self._key.encode(nacl.encoding.Base64Encoder)

    def __str__(self):
        '''Return the private part of the key key as a base64-encoded string'''
        return self.serialize().decode('utf-8')

    def __eq__(self, other):
        return self.key == other.key


class PublicKey(object):
    ''' A public key used by the bakery to encrypt third party caveats.

    Every discharger is associated with a public key which is used to
    encrypt third party caveat ids addressed to that discharger.
    Internally, it is a 256 bit Ed25519 public key.
    '''
    def __init__(self, key):
        self._key = key

    @property
    def key(self):
        ''' Internal nacl key representation.
        '''
        return self._key

    def serialize(self, raw=False):
        '''Encode the private part of the key in a base64 format by default,
        but when raw is True it will return hex encoded bytes.
        @return: bytes
        '''
        if raw:
            return self._key.encode()
        return self._key.encode(nacl.encoding.Base64Encoder)

    def __str__(self):
        '''Return the key as a base64-encoded string'''
        return self.serialize().decode('utf-8')

    @classmethod
    def deserialize(cls, serialized):
        ''' Create a PublicKey from a base64 encoded bytes.
        :return: a PublicKey
        '''
        return PublicKey(
            nacl.public.PublicKey(serialized,
                                  encoder=nacl.encoding.Base64Encoder))

    def __eq__(self, other):
        return self.key == other.key


def generate_key():
    '''GenerateKey generates a new PrivateKey.
    :return: a PrivateKey
    '''
    return PrivateKey(nacl.public.PrivateKey.generate())
