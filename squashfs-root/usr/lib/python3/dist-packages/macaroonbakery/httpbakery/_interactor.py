# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import abc
from collections import namedtuple

WEB_BROWSER_INTERACTION_KIND = 'browser-window'


class Interactor(object):
    ''' Represents a way of persuading a discharger that it should grant a
    discharge macaroon.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def kind(self):
        '''Returns the interaction method name. This corresponds to the key in
        the Error.interaction_methods type.
        @return {str}
        '''
        raise NotImplementedError('kind method must be defined in subclass')

    def interact(self, client, location, interaction_required_err):
        ''' Performs the interaction, and returns a token that can be
        used to acquire the discharge macaroon. The location provides
        the third party caveat location to make it possible to use
        relative URLs. The client holds the client being used to do the current
        request.

        If the given interaction isn't supported by the client for
        the given location, it may raise an InteractionMethodNotFound
        which will cause the interactor to be ignored that time.
        @param client The client being used for the current request {Client}
        @param location Third party caveat location {str}
        @param interaction_required_err The error causing the interaction to
        take place {Error}
        @return {DischargeToken} The discharge token.
        '''
        raise NotImplementedError('interact method must be defined in subclass')


class LegacyInteractor(object):
    ''' May optionally be implemented by Interactor implementations that
    implement the legacy interaction-required error protocols.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def legacy_interact(self, client, location, visit_url):
        ''' Implements the "visit" half of a legacy discharge
        interaction. The "wait" half will be implemented by httpbakery.
        The location is the location specified by the third party
        caveat. The client holds the client being used to do the current
        request.
        @param client The client being used for the current request {Client}
        @param location Third party caveat location {str}
        @param visit_url The visit_url field from the error {str}
        @return None
        '''
        raise NotImplementedError('legacy_interact method must be defined in subclass')


class DischargeToken(namedtuple('DischargeToken', 'kind, value')):
    ''' Holds a token that is intended to persuade a discharger to discharge
    a third party caveat.
    @param kind holds the kind of the token. By convention this
    matches the name of the interaction method used to
    obtain the token, but that's not required {str}
    @param value holds the token data. {bytes}
    '''
