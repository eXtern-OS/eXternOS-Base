# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import abc

from ._error import IdentityError


class Identity(object):
    ''' Holds identity information declared in a first party caveat added when
    discharging a third party caveat.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def id(self):
        ''' Returns the id of the user.

        May be an opaque blob with no human meaning. An id is only considered
        to be unique with a given domain.
        :return string
        '''
        raise NotImplementedError('id method must be defined in subclass')

    @abc.abstractmethod
    def domain(self):
        '''Return the domain of the user.

        This will be empty if the user was authenticated
        directly with the identity provider.
        :return string
        '''
        raise NotImplementedError('domain method must be defined in subclass')


class ACLIdentity(Identity):
    ''' ACLIdentity may be implemented by Identity implementations
    to report group membership information.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def allow(self, ctx, acls):
        ''' reports whether the user should be allowed to access
        any of the users or groups in the given acl list.
        :param ctx(AuthContext) is the context of the authorization request.
        :param acls array of string acl
        :return boolean
        '''
        raise NotImplementedError('allow method must be defined in subclass')


class SimpleIdentity(ACLIdentity):
    ''' A simple form of identity where the user is represented by a string.
    '''
    def __init__(self, user):
        self._identity = user

    def domain(self):
        ''' A simple identity has no domain.
        '''
        return ''

    def id(self):
        '''Return the user name as the id.
        '''
        return self._identity

    def allow(self, ctx, acls):
        '''Allow access to any ACL members that was equal to the user name.

        That is, some user u is considered a member of group u and no other.
        '''
        for acl in acls:
            if self._identity == acl:
                return True
        return False


class IdentityClient(object):
    ''' Represents an abstract identity manager. User identities can be based
    on local informaton (for example HTTP basic auth) or by reference to an
    external trusted third party (an identity manager).
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def identity_from_context(self, ctx):
        ''' Returns the identity based on information in the context.

        If it cannot determine the identity based on the context, then it
        should return a set of caveats containing a third party caveat that,
        when discharged, can be used to obtain the identity with
        declared_identity.

        It should only raise an error if it cannot check the identity
        (for example because of a database access error) - it's
        OK to return all zero values when there's
        no identity found and no third party to address caveats to.
        @param ctx an AuthContext
        :return: an Identity and array of caveats
        '''
        raise NotImplementedError('identity_from_context method must be '
                                  'defined in subclass')

    @abc.abstractmethod
    def declared_identity(self, ctx, declared):
        '''Parses the identity declaration from the given declared attributes.

        TODO take the set of first party caveat conditions instead?
        @param ctx (AuthContext)
        @param declared (dict of string/string)
        :return: an Identity
        '''
        raise NotImplementedError('declared_identity method must be '
                                  'defined in subclass')


class NoIdentities(IdentityClient):
    ''' Defines the null identity provider - it never returns any identities.
    '''

    def identity_from_context(self, ctx):
        return None, None

    def declared_identity(self, ctx, declared):
        raise IdentityError('no identity declared or possible')
