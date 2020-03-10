# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import abc
import os


class MemoryOpsStore:
    ''' A multi-op store that stores the operations in memory.
    '''
    def __init__(self):
        self._store = {}

    def put_ops(self, key, time, ops):
        ''' Put an ops only if not already there, otherwise it's a no op.
        '''
        if self._store.get(key) is None:
            self._store[key] = ops

    def get_ops(self, key):
        ''' Returns ops from the key if found otherwise raises a KeyError.
        '''
        ops = self._store.get(key)
        if ops is None:
            raise KeyError(
                'cannot get operations for {}'.format(key))
        return ops


class RootKeyStore(object):
    ''' Defines a store for macaroon root keys.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get(self, id):
        ''' Returns the root key for the given id.
        If the item is not there, it returns None.
        @param id: bytes
        @return: bytes
        '''
        raise NotImplementedError('get method must be defined in '
                                  'subclass')

    @abc.abstractmethod
    def root_key(self):
        ''' Returns the root key to be used for making a new macaroon, and an
        id that can be used to look it up later with the get method.
        Note that the root keys should remain available for as long as the
        macaroons using them are valid.
        Note that there is no need for it to return a new root key for every
        call - keys may be reused, although some key cycling is over time is
        advisable.
        @return: bytes
        '''


class MemoryKeyStore(RootKeyStore):
    ''' MemoryKeyStore returns an implementation of
    Store that generates a single key and always
    returns that from root_key. The same id ("0") is always
    used.
    '''
    def __init__(self, key=None):
        ''' If the key is not specified a random key will be generated.
        @param key: bytes
        '''
        if key is None:
            key = os.urandom(24)
        self._key = key

    def get(self, id):
        if id != b'0':
            return None
        return self._key

    def root_key(self):
        return self._key, b'0'
