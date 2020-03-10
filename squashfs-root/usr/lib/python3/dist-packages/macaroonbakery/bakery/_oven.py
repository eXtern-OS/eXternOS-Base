# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.

import base64
import hashlib
import itertools
import os

import google
from ._checker import (Op, LOGIN_OP)
from ._store import MemoryKeyStore
from ._error import VerificationError
from ._versions import (
    VERSION_2,
    VERSION_3,
    LATEST_VERSION,
)
from ._macaroon import (
    Macaroon,
    macaroon_version,
)

import macaroonbakery.checkers as checkers
import six
from macaroonbakery._utils import (
    raw_urlsafe_b64encode,
    b64decode,
)
from ._internal import id_pb2
from pymacaroons import MACAROON_V2, Verifier
from pymacaroons.exceptions import (
    MacaroonInvalidSignatureException,
    MacaroonUnmetCaveatException,
)


class Oven:
    ''' Oven bakes macaroons. They emerge sweet and delicious and ready for use
    in a Checker.

    All macaroons are associated with one or more operations (see
    the Op type) which define the capabilities of the macaroon.

    There is one special operation, "login" (defined by LOGIN_OP) which grants
    the capability to speak for a particular user.
    The login capability will never be mixed with other capabilities.

    It is up to the caller to decide on semantics for other operations.
    '''

    def __init__(self, key=None, location=None, locator=None, namespace=None,
                 root_keystore_for_ops=None, ops_store=None):
        '''
        @param namespace holds the namespace to use when adding first party
        caveats.
        @param root_keystore_for_ops a function that will give the macaroon
        storage to be used for root keys associated with macaroons created
        with macaroon.
        @param ops_store object is used to persistently store the association
        of multi-op entities with their associated operations when macaroon is
        called with multiple operations.
        When this is in use, operation entities with the prefix "multi-" are
        reserved - a "multi-"-prefixed entity represents a set of operations
        stored in the OpsStore.
        @param key holds the private nacl key pair used to encrypt third party
        caveats. If it is None, no third party caveats can be created.
        @param location string holds the location that will be associated with
        new macaroons (as returned by Macaroon.Location).
        @param locator is used to find out information on third parties when
        adding third party caveats. If this is None, no non-local third
        party caveats can be added.
        '''
        self.key = key
        self.location = location
        self.locator = locator
        if namespace is None:
            namespace = checkers.Checker().namespace()
        self.namespace = namespace
        self.ops_store = ops_store
        self.root_keystore_for_ops = root_keystore_for_ops
        if root_keystore_for_ops is None:
            my_store = MemoryKeyStore()
            self.root_keystore_for_ops = lambda x: my_store

    def macaroon(self, version, expiry, caveats, ops):
        ''' Takes a macaroon with the given version from the oven,
        associates it with the given operations and attaches the given caveats.
        There must be at least one operation specified.
        The macaroon will expire at the given time - a time_before first party
        caveat will be added with that time.

        @return: a new Macaroon object.
        '''
        if len(ops) == 0:
            raise ValueError('cannot mint a macaroon associated '
                             'with no operations')

        ops = canonical_ops(ops)
        root_key, storage_id = self.root_keystore_for_ops(ops).root_key()

        id = self._new_macaroon_id(storage_id, expiry, ops)

        id_bytes = six.int2byte(LATEST_VERSION) + \
            id.SerializeToString()

        if macaroon_version(version) < MACAROON_V2:
            # The old macaroon format required valid text for the macaroon id,
            # so base64-encode it.
            id_bytes = raw_urlsafe_b64encode(id_bytes)

        m = Macaroon(
            root_key,
            id_bytes,
            self.location,
            version,
            self.namespace,
        )
        m.add_caveat(checkers.time_before_caveat(expiry), self.key,
                     self.locator)
        m.add_caveats(caveats, self.key, self.locator)
        return m

    def _new_macaroon_id(self, storage_id, expiry, ops):
        nonce = os.urandom(16)
        if len(ops) == 1 or self.ops_store is None:
            return id_pb2.MacaroonId(
                nonce=nonce,
                storageId=storage_id,
                ops=_macaroon_id_ops(ops))
        # We've got several operations and a multi-op store, so use the store.
        # TODO use the store only if the encoded macaroon id exceeds some size?
        entity = self.ops_entity(ops)
        self.ops_store.put_ops(entity, expiry, ops)
        return id_pb2.MacaroonId(
            nonce=nonce,
            storageId=storage_id,
            ops=[id_pb2.Op(entity=entity, actions=['*'])])

    def ops_entity(self, ops):
        ''' Returns a new multi-op entity name string that represents
        all the given operations and caveats. It returns the same value
        regardless of the ordering of the operations. It assumes that the
        operations have been canonicalized and that there's at least one
        operation.

        :param ops:
        :return: string that represents all the given operations and caveats.
        '''
        # Hash the operations, removing duplicates as we go.
        hash_entity = hashlib.sha256()
        for op in ops:
            hash_entity.update('{}\n{}\n'.format(
                op.action, op.entity).encode())
        hash_encoded = base64.urlsafe_b64encode(hash_entity.digest())
        return 'multi-' + hash_encoded.decode('utf-8').rstrip('=')

    def macaroon_ops(self, macaroons):
        ''' This method makes the oven satisfy the MacaroonOpStore protocol
        required by the Checker class.

        For macaroons minted with previous bakery versions, it always
        returns a single LoginOp operation.

        :param macaroons:
        :return:
        '''
        if len(macaroons) == 0:
            raise ValueError('no macaroons provided')

        storage_id, ops = _decode_macaroon_id(macaroons[0].identifier_bytes)
        root_key = self.root_keystore_for_ops(ops).get(storage_id)
        if root_key is None:
            raise VerificationError(
                'macaroon key not found in storage')
        v = Verifier()
        conditions = []

        def validator(condition):
            # Verify the macaroon's signature only. Don't check any of the
            # caveats yet but save them so that we can return them.
            conditions.append(condition)
            return True
        v.satisfy_general(validator)
        try:
            v.verify(macaroons[0], root_key, macaroons[1:])
        except (MacaroonUnmetCaveatException,
                MacaroonInvalidSignatureException) as exc:
            raise VerificationError(
                'verification failed: {}'.format(exc.args[0]))

        if (self.ops_store is not None
            and len(ops) == 1
                and ops[0].entity.startswith('multi-')):
            # It's a multi-op entity, so retrieve the actual operations
            # it's associated with.
            ops = self.ops_store.get_ops(ops[0].entity)

        return ops, conditions


def _decode_macaroon_id(id):
    storage_id = b''
    base64_decoded = False
    first = id[:1]
    if first == b'A':
        # The first byte is not a version number and it's 'A', which is the
        # base64 encoding of the top 6 bits (all zero) of the version number 2
        # or 3, so we assume that it's the base64 encoding of a new-style
        # macaroon id, so we base64 decode it.
        #
        # Note that old-style ids always start with an ASCII character >= 4
        # (> 32 in fact) so this logic won't be triggered for those.
        try:
            dec = b64decode(id.decode('utf-8'))
            # Set the id only on success.
            id = dec
            base64_decoded = True
        except:
            # if it's a bad encoding, we'll get an error which is fine
            pass

    # Trim any extraneous information from the id before retrieving
    # it from storage, including the UUID that's added when
    # creating macaroons to make all macaroons unique even if
    # they're using the same root key.
    first = six.byte2int(id[:1])
    if first == VERSION_2:
        # Skip the UUID at the start of the id.
        storage_id = id[1 + 16:]
    if first == VERSION_3:
        try:
            id1 = id_pb2.MacaroonId.FromString(id[1:])
        except google.protobuf.message.DecodeError:
            raise VerificationError(
                'no operations found in macaroon')
        if len(id1.ops) == 0 or len(id1.ops[0].actions) == 0:
            raise VerificationError(
                'no operations found in macaroon')

        ops = []
        for op in id1.ops:
            for action in op.actions:
                ops.append(Op(op.entity, action))
        return id1.storageId, ops

    if not base64_decoded and _is_lower_case_hex_char(first):
        # It's an old-style id, probably with a hyphenated UUID.
        # so trim that off.
        last = id.rfind(b'-')
        if last >= 0:
            storage_id = id[0:last]
    return storage_id, [LOGIN_OP]


def _is_lower_case_hex_char(b):
    if ord('0') <= b <= ord('9'):
        return True
    if ord('a') <= b <= ord('f'):
        return True
    return False


def canonical_ops(ops):
    ''' Returns the given operations array sorted with duplicates removed.

    @param ops checker.Ops
    @return: checker.Ops
    '''
    new_ops = sorted(set(ops), key=lambda x: (x.entity, x.action))
    return new_ops


def _macaroon_id_ops(ops):
    '''Return operations suitable for serializing as part of a MacaroonId.

    It assumes that ops has been canonicalized and that there's at least
    one operation.
    '''
    id_ops = []
    for entity, entity_ops in itertools.groupby(ops, lambda x: x.entity):
        actions = map(lambda x: x.action, entity_ops)
        id_ops.append(id_pb2.Op(entity=entity, actions=actions))
    return id_ops
