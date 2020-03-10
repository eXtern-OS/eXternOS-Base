# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.


class DischargeRequiredError(Exception):
    ''' Raised by checker when authorization has failed and a discharged
    macaroon might fix it.

    A caller should grant the user the ability to authorize by minting a
    macaroon associated with Ops (see MacaroonStore.MacaroonIdInfo for
    how the associated operations are retrieved) and adding Caveats. If
    the user succeeds in discharging the caveats, the authorization will
    be granted.
    '''
    def __init__(self, msg, ops, cavs):
        '''
        :param msg: holds some reason why the authorization was denied.
        :param ops: holds all the operations that were not authorized.
        If ops contains a single LOGIN_OP member, the macaroon
        should be treated as an login token. Login tokens (also
        known as authentication macaroons) usually have a longer
        life span than other macaroons.
        :param cavs: holds the caveats that must be added to macaroons that
        authorize the above operations.
        '''
        super(DischargeRequiredError, self).__init__(msg)
        self._ops = ops
        self._cavs = cavs

    def ops(self):
        return self._ops

    def cavs(self):
        return self._cavs


class PermissionDenied(Exception):
    '''Raised from AuthChecker when permission has been denied.
    '''
    pass


class CaveatNotRecognizedError(Exception):
    '''Containing the cause of errors returned from caveat checkers when the
    caveat was not recognized.
    '''
    pass


class VerificationError(Exception):
    '''Raised to signify that an error is because of a verification failure
    rather than because verification could not be done.'''
    pass


class AuthInitError(Exception):
    '''Raised if AuthChecker cannot be initialized properly.'''
    pass


class IdentityError(Exception):
    ''' Raised from IdentityClient.declared_identity when an error occurs.
    '''
    pass


class ThirdPartyCaveatCheckFailed(Exception):
    ''' Raised from ThirdPartyCaveatChecker.check_third_party when check fails.
    '''
    pass


class ThirdPartyInfoNotFound(Exception):
    ''' Raised from implementation of ThirdPartyLocator.third_party_info when
    the info cannot be found.
    '''
    pass
