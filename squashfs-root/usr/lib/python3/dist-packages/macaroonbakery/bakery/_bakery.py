# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.

from ._authorizer import ClosedAuthorizer
from ._checker import Checker
import macaroonbakery.checkers as checkers
from ._oven import Oven


class Bakery(object):
    '''Convenience class that contains both an Oven and a Checker.
    '''
    def __init__(self, location=None, locator=None, ops_store=None, key=None,
                 identity_client=None, checker=None, root_key_store=None,
                 authorizer=ClosedAuthorizer()):
        '''Returns a new Bakery instance which combines an Oven with a
        Checker for the convenience of callers that wish to use both
        together.
        @param checker holds the checker used to check first party caveats.
        If this is None, it will use checkers.Checker(None).
        @param root_key_store holds the root key store to use.
        If you need to use a different root key store for different operations,
        you'll need to pass a root_key_store_for_ops value to Oven directly.
        @param root_key_store If this is None, it will use MemoryKeyStore().
        Note that that is almost certain insufficient for production services
        that are spread across multiple instances or that need
        to persist keys across restarts.
        @param locator is used to find out information on third parties when
        adding third party caveats. If this is None, no non-local third
        party caveats can be added.
        @param key holds the private key of the oven. If this is None,
        no third party caveats may be added.
        @param identity_client holds the identity implementation to use for
        authentication. If this is None, no authentication will be possible.
        @param authorizer is used to check whether an authenticated user is
        allowed to perform operations. If it is None, it will use
        a ClosedAuthorizer.
        The identity parameter passed to authorizer.allow will
        always have been obtained from a call to
        IdentityClient.declared_identity.
        @param ops_store used to persistently store the association of
        multi-op entities with their associated operations
        when oven.macaroon is called with multiple operations.
        @param location holds the location to use when creating new macaroons.
        '''

        if checker is None:
            checker = checkers.Checker()
        root_keystore_for_ops = None
        if root_key_store is not None:
            def root_keystore_for_ops(ops):
                return root_key_store

        oven = Oven(key=key,
                    location=location,
                    locator=locator,
                    namespace=checker.namespace(),
                    root_keystore_for_ops=root_keystore_for_ops,
                    ops_store=ops_store)
        self._oven = oven

        self._checker = Checker(checker=checker, authorizer=authorizer,
                                identity_client=identity_client,
                                macaroon_opstore=oven)

    @property
    def oven(self):
        return self._oven

    @property
    def checker(self):
        return self._checker
