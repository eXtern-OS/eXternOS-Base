# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import abc

from ._identity import ACLIdentity

# EVERYONE is recognized by ACLAuthorizer as the name of a
# group that has everyone in it.
EVERYONE = 'everyone'


class Authorizer(object):
    ''' Used to check whether a given user is allowed to perform a set of
    operations.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def authorize(self, ctx, id, ops):
        ''' Checks whether the given identity (which will be None when there is
        no authenticated user) is allowed to perform the given operations.
        It should raise an exception only when the authorization cannot be
        determined, not when the user has been denied access.

        On success, each element of allowed holds whether the respective
        element of ops has been allowed, and caveats holds any additional
        third party caveats that apply.
        If allowed is shorter then ops, the additional elements are assumed to
        be False.
        ctx(AuthContext) is the context of the authorization request.
        :return: a list of boolean and a list of caveats
        '''
        raise NotImplementedError('authorize method must be defined in '
                                  'subclass')


class AuthorizerFunc(Authorizer):
    ''' Implements a simplified version of Authorizer that operates on a single
    operation at a time.
    '''
    def __init__(self, f):
        '''
        :param f: a function that takes an identity that operates on a single
        operation at a time. Will return if this op is allowed as a boolean and
        and a list of caveat that holds any additional third party caveats
        that apply.
        '''
        self._f = f

    def authorize(self, ctx, identity, ops):
        '''Implements Authorizer.authorize by calling f with the given identity
        for each operation.
        '''
        allowed = []
        caveats = []
        for op in ops:
            ok, fcaveats = self._f(ctx, identity, op)
            allowed.append(ok)
            if fcaveats is not None:
                caveats.extend(fcaveats)
        return allowed, caveats


class ACLAuthorizer(Authorizer):
    ''' ACLAuthorizer is an Authorizer implementation that will check access
    control list (ACL) membership of users. It uses get_acl to find out
    the ACLs that apply to the requested operations and will authorize an
    operation if an ACL contains the group "everyone" or if the identity is
    an instance of ACLIdentity and its allow method returns True for the ACL.
    '''
    def __init__(self, get_acl, allow_public=False):
        '''
        :param get_acl get_acl will be called with an auth context and an Op.
        It should return the ACL that applies (an array of string ids).
        If an entity cannot be found or the action is not recognised,
        get_acl should return an empty list but no error.
        :param allow_public: boolean, If True and an ACL contains "everyone",
        then authorization will be granted even if there is no logged in user.
        '''
        self._allow_public = allow_public
        self._get_acl = get_acl

    def authorize(self, ctx, identity, ops):
        '''Implements Authorizer.authorize by calling identity.allow to
        determine whether the identity is a member of the ACLs associated with
        the given operations.
        '''
        if len(ops) == 0:
            # Anyone is allowed to do nothing.
            return [], []
        allowed = [False] * len(ops)
        has_allow = isinstance(identity, ACLIdentity)
        for i, op in enumerate(ops):
            acl = self._get_acl(ctx, op)
            if has_allow:
                allowed[i] = identity.allow(ctx, acl)
            else:
                allowed[i] = self._allow_public and EVERYONE in acl
        return allowed, []


class ClosedAuthorizer(Authorizer):
    ''' An Authorizer implementation that will never authorize anything.
    '''
    def authorize(self, ctx, id, ops):
        return [False] * len(ops), []
