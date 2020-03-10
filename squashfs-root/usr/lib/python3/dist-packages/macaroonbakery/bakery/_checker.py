# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
from collections import namedtuple
from threading import Lock

from ._authorizer import ClosedAuthorizer
from ._identity import NoIdentities
from ._error import (
    AuthInitError,
    VerificationError,
    IdentityError,
    DischargeRequiredError,
    PermissionDenied,
)
import macaroonbakery.checkers as checkers
import pyrfc3339


class Op(namedtuple('Op', 'entity, action')):
    ''' Op holds an entity and action to be authorized on that entity.
    entity string holds the name of the entity to be authorized.

    @param entity should not contain spaces and should
    not start with the prefix "login" or "multi-" (conventionally,
    entity names will be prefixed with the entity type followed
    by a hyphen.
    @param action string holds the action to perform on the entity,
    such as "read" or "delete". It is up to the service using a checker
    to define a set of operations and keep them consistent over time.
    '''


# LOGIN_OP represents a login (authentication) operation.
# A macaroon that is associated with this operation generally
# carries authentication information with it.
LOGIN_OP = Op(entity='login', action='login')


class Checker(object):
    '''Checker implements an authentication and authorization checker.

    It uses macaroons as authorization tokens but it is not itself responsible
    for creating the macaroons
    See the Oven type (TODO) for one way of doing that.
    '''
    def __init__(self, checker=checkers.Checker(),
                 authorizer=ClosedAuthorizer(),
                 identity_client=None,
                 macaroon_opstore=None):
        '''
        :param checker: a first party checker implementing a
        :param authorizer (Authorizer): used to check whether an authenticated
        user is allowed to perform operations.
        The identity parameter passed to authorizer.allow will always have been
        obtained from a call to identity_client.declared_identity.
        :param identity_client (IdentityClient) used for interactions with the
        external identity service used for authentication.
        If this is None, no authentication will be possible.
        :param macaroon_opstore (object with new_macaroon and macaroon_ops
        method): used to retrieve macaroon root keys and other associated
        information.
        '''
        self._first_party_caveat_checker = checker
        self._authorizer = authorizer
        if identity_client is None:
            identity_client = NoIdentities()
        self._identity_client = identity_client
        self._macaroon_opstore = macaroon_opstore

    def auth(self, mss):
        ''' Returns a new AuthChecker instance using the given macaroons to
        inform authorization decisions.
        @param mss: a list of macaroon lists.
        '''
        return AuthChecker(parent=self,
                           macaroons=mss)

    def namespace(self):
        ''' Returns the namespace of the first party checker.
        '''
        return self._first_party_caveat_checker.namespace()


class AuthChecker(object):
    '''Authorizes operations with respect to a user's request.

    The identity is authenticated only once, the first time any method
    of the AuthChecker is called, using the context passed in then.

    To find out any declared identity without requiring a login,
    use allow(ctx); to require authentication but no additional operations,
    use allow(ctx, LOGIN_OP).
    '''
    def __init__(self, parent, macaroons):
        '''

        :param parent (Checker): used to check first party caveats.
        :param macaroons: a list of py macaroons
        '''
        self._macaroons = macaroons
        self._init_errors = []
        self._executed = False
        self._identity = None
        self._identity_caveats = []
        self.parent = parent
        self._conditions = None
        self._mutex = Lock()

    def _init(self, ctx):
        with self._mutex:
            if not self._executed:
                self._init_once(ctx)
                self._executed = True
        if self._init_errors:
            raise AuthInitError(self._init_errors[0])

    def _init_once(self, ctx):
        self._auth_indexes = {}
        self._conditions = [None] * len(self._macaroons)
        for i, ms in enumerate(self._macaroons):
            try:
                ops, conditions = self.parent._macaroon_opstore.macaroon_ops(
                    ms)
            except VerificationError:
                raise
            except Exception as exc:
                self._init_errors.append(exc.args[0])
                continue

            # It's a valid macaroon (in principle - we haven't checked first
            # party caveats).
            self._conditions[i] = conditions
            is_login = False
            for op in ops:
                if op == LOGIN_OP:
                    # Don't associate the macaroon with the login operation
                    # until we've verified that it is valid below
                    is_login = True
                else:
                    if op not in self._auth_indexes:
                        self._auth_indexes[op] = []
                    self._auth_indexes[op].append(i)
            if not is_login:
                continue
            # It's a login macaroon. Check the conditions now -
            # all calls want to see the same authentication
            # information so that callers have a consistent idea of
            # the client's identity.
            #
            # If the conditions fail, we won't use the macaroon for
            # identity, but we can still potentially use it for its
            # other operations if the conditions succeed for those.
            declared, err = self._check_conditions(ctx, LOGIN_OP, conditions)
            if err is not None:
                self._init_errors.append('cannot authorize login macaroon: ' +
                                         err)
                continue
            if self._identity is not None:
                # We've already found a login macaroon so ignore this one
                # for the purposes of identity.
                continue

            try:
                identity = self.parent._identity_client.declared_identity(
                    ctx, declared)
            except IdentityError as exc:
                self._init_errors.append(
                    'cannot decode declared identity: {}'.format(exc.args[0]))
                continue
            if LOGIN_OP not in self._auth_indexes:
                self._auth_indexes[LOGIN_OP] = []
            self._auth_indexes[LOGIN_OP].append(i)
            self._identity = identity

        if self._identity is None:
            # No identity yet, so try to get one based on the context.
            try:
                identity, cavs = self.parent.\
                    _identity_client.identity_from_context(ctx)
            except IdentityError:
                self._init_errors.append('could not determine identity')
            if cavs is None:
                cavs = []
            self._identity, self._identity_caveats = identity, cavs
        return None

    def allow(self, ctx, ops):
        ''' Checks that the authorizer's request is authorized to
        perform all the given operations. Note that allow does not check
        first party caveats - if there is more than one macaroon that may
        authorize the request, it will choose the first one that does
        regardless.

        If all the operations are allowed, an AuthInfo is returned holding
        details of the decision and any first party caveats that must be
        checked before actually executing any operation.

        If operations include LOGIN_OP, the request should contain an
        authentication macaroon proving the client's identity. Once an
        authentication macaroon is chosen, it will be used for all other
        authorization requests.

        If an operation was not allowed, an exception will be raised which may
        be DischargeRequiredError holding the operations that remain to
        be authorized in order to allow authorization to proceed.
        @param ctx AuthContext
        @param ops an array of Op
        :return: an AuthInfo object.
        '''
        auth_info, _ = self.allow_any(ctx, ops)
        return auth_info

    def allow_any(self, ctx, ops):
        ''' like allow except that it will authorize as many of the
        operations as possible without requiring any to be authorized. If all
        the operations succeeded, the array will be nil.

        If any the operations failed, the returned error will be the same
        that allow would return and each element in the returned slice will
        hold whether its respective operation was allowed.

        If all the operations succeeded, the returned slice will be None.

        The returned AuthInfo will always be non-None.

        The LOGIN_OP operation is treated specially - it is always required if
        present in ops.
        @param ctx AuthContext
        @param ops an array of Op
        :return: an AuthInfo object and the auth used as an array of int.
        '''
        authed, used = self._allow_any(ctx, ops)
        return self._new_auth_info(used), authed

    def _new_auth_info(self, used):
        info = AuthInfo(identity=self._identity, macaroons=[])
        for i, is_used in enumerate(used):
            if is_used:
                info.macaroons.append(self._macaroons[i])
        return info

    def _allow_any(self, ctx, ops):
        self._init(ctx)
        used = [False] * len(self._macaroons)
        authed = [False] * len(ops)
        num_authed = 0
        errors = []
        for i, op in enumerate(ops):
            for mindex in self._auth_indexes.get(op, []):
                _, err = self._check_conditions(ctx, op,
                                                self._conditions[mindex])
                if err is not None:
                    errors.append(err)
                    continue
                authed[i] = True
                num_authed += 1
                used[mindex] = True
                # Use the first authorized macaroon only.
                break
            if op == LOGIN_OP and not authed[i] and self._identity is not None:
                # Allow LOGIN_OP when there's an authenticated user even
                # when there's no macaroon that specifically authorizes it.
                authed[i] = True
        if self._identity is not None:
            # We've authenticated as a user, so even if the operations didn't
            # specifically require it, we add the login macaroon
            # to the macaroons used.
            # Note that the LOGIN_OP conditions have already been checked
            # successfully in initOnceFunc so no need to check again.
            # Note also that there may not be any macaroons if the
            # identity client decided on an identity even with no
            # macaroons.
            for i in self._auth_indexes.get(LOGIN_OP, []):
                used[i] = True
        if num_authed == len(ops):
            # All operations allowed.
            return authed, used
        # There are some unauthorized operations.
        need = []
        need_index = [0] * (len(ops) - num_authed)
        for i, ok in enumerate(authed):
            if not ok:
                need_index[len(need)] = i
                need.append(ops[i])

        # Try to authorize the operations
        # even if we haven't got an authenticated user.
        oks, caveats = self.parent._authorizer.authorize(
            ctx, self._identity, need)
        still_need = []
        for i, _ in enumerate(need):
            if i < len(oks) and oks[i]:
                authed[need_index[i]] = True
            else:
                still_need.append(ops[need_index[i]])
        if len(still_need) == 0 and len(caveats) == 0:
            # No more ops need to be authenticated and
            # no caveats to be discharged.
            return authed, used
        if self._identity is None and len(self._identity_caveats) > 0:
            raise DischargeRequiredError(
                msg='authentication required',
                ops=[LOGIN_OP],
                cavs=self._identity_caveats)
        if caveats is None or len(caveats) == 0:
            all_errors = []
            all_errors.extend(self._init_errors)
            all_errors.extend(errors)
            err = ''
            if len(all_errors) > 0:
                err = all_errors[0]
            raise PermissionDenied(err)
        raise DischargeRequiredError(
            msg='some operations have extra caveats', ops=ops, cavs=caveats)

    def allow_capability(self, ctx, ops):
        '''Checks that the user is allowed to perform all the
        given operations. If not, a discharge error will be raised.
        If allow_capability succeeds, it returns a list of first party caveat
        conditions that must be applied to any macaroon granting capability
        to execute the operations. Those caveat conditions will not
        include any declarations contained in login macaroons - the
        caller must be careful not to mint a macaroon associated
        with the LOGIN_OP operation unless they add the expected
        declaration caveat too - in general, clients should not create
        capabilities that grant LOGIN_OP rights.

        The operations must include at least one non-LOGIN_OP operation.
        '''
        nops = 0
        for op in ops:
            if op != LOGIN_OP:
                nops += 1
        if nops == 0:
            raise ValueError('no non-login operations required in capability')

        _, used = self._allow_any(ctx, ops)
        squasher = _CaveatSquasher()
        for i, is_used in enumerate(used):
            if not is_used:
                continue
            for cond in self._conditions[i]:
                squasher.add(cond)
        return squasher.final()

    def _check_conditions(self, ctx, op, conds):
        declared = checkers.infer_declared_from_conditions(
            conds,
            self.parent.namespace())
        ctx = checkers.context_with_operations(ctx, [op.action])
        ctx = checkers.context_with_declared(ctx, declared)
        for cond in conds:
            err = self.parent._first_party_caveat_checker.\
                check_first_party_caveat(ctx, cond)
            if err is not None:
                return None, err
        return declared, None


class AuthInfo(namedtuple('AuthInfo', 'identity macaroons')):
    '''AuthInfo information about an authorization decision.

    @param identity: holds information on the authenticated user as
    returned identity_client. It may be None after a successful
    authorization if LOGIN_OP access was not required.

    @param macaroons: holds all the macaroons that were used for the
    authorization. Macaroons that were invalid or unnecessary are
    not included.
    '''


class _CaveatSquasher(object):
    ''' Rationalizes first party caveats created for a capability by:
        - including only the earliest time-before caveat.
        - excluding allow and deny caveats (operations are checked by
        virtue of the operations associated with the macaroon).
        - removing declared caveats.
        - removing duplicates.
    '''
    def __init__(self, expiry=None, conds=None):
        self._expiry = expiry
        if conds is None:
            conds = []
        self._conds = conds

    def add(self, cond):
        if self._add(cond):
            self._conds.append(cond)

    def _add(self, cond):
        try:
            cond, args = checkers.parse_caveat(cond)
        except ValueError:
            # Be safe - if we can't parse the caveat, just leave it there.
            return True

        if cond == checkers.COND_TIME_BEFORE:
            try:
                et = pyrfc3339.parse(args, utc=True).replace(tzinfo=None)
            except ValueError:
                # Again, if it doesn't seem valid, leave it alone.
                return True
            if self._expiry is None or et <= self._expiry:
                self._expiry = et
            return False
        elif cond in [checkers.COND_ALLOW,
                      checkers.COND_DENY, checkers.COND_DECLARED]:
            return False
        return True

    def final(self):
        if self._expiry is not None:
            self._conds.append(
                checkers.time_before_caveat(self._expiry).condition)
        # Make deterministic and eliminate duplicates.
        return sorted(set(self._conds))
