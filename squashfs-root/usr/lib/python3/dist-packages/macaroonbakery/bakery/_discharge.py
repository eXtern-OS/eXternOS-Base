# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import abc
from collections import namedtuple

from ._error import (
    ThirdPartyCaveatCheckFailed,
    CaveatNotRecognizedError,
    VerificationError,
)
from ._codec import decode_caveat
from ._macaroon import (
    Macaroon,
    ThirdPartyLocator,
)
from ._versions import VERSION_2
from ._third_party import ThirdPartyCaveatInfo

import macaroonbakery.checkers as checkers

emptyContext = checkers.AuthContext()


def discharge_all(m, get_discharge, local_key=None):
    '''Gathers discharge macaroons for all the third party caveats in m
    (and any subsequent caveats required by those) using get_discharge to
    acquire each discharge macaroon.
    The local_key parameter may optionally hold the key of the client, in
    which case it will be used to discharge any third party caveats with the
    special location "local". In this case, the caveat itself must be "true".
    This can be used be a server to ask a client to prove ownership of the
    private key.
    It returns a list of macaroon with m as the first element, followed by all
    the discharge macaroons.
    All the discharge macaroons will be bound to the primary macaroon.
    The get_discharge function is passed a context (AuthContext),
    the caveat(Caveat) to be discharged and encrypted_caveat (bytes)will be
    passed the external caveat payload found in m, if any.
    '''
    primary = m.macaroon
    discharges = [primary]

    # cav holds the macaroon caveat that needs discharge.
    # encrypted_caveat (bytes) holds encrypted caveat if it was held
    # externally.
    _NeedCaveat = namedtuple('_NeedCaveat', 'cav encrypted_caveat')
    need = []

    def add_caveats(m):
        for cav in m.macaroon.caveats:
            if cav.location is None or cav.location == '':
                continue
            encrypted_caveat = m.caveat_data.get(cav.caveat_id, None)
            need.append(
                _NeedCaveat(cav=cav,
                            encrypted_caveat=encrypted_caveat))
    add_caveats(m)
    while len(need) > 0:
        cav = need[0]
        need = need[1:]
        if cav.cav.location == 'local':
            if local_key is None:
                raise ThirdPartyCaveatCheckFailed(
                    'found local third party caveat but no private key provided',
                )
            # TODO use a small caveat id.
            dm = discharge(ctx=emptyContext,
                           key=local_key,
                           checker=_LocalDischargeChecker(),
                           caveat=cav.encrypted_caveat,
                           id=cav.cav.caveat_id_bytes,
                           locator=_EmptyLocator())
        else:
            dm = get_discharge(cav.cav, cav.encrypted_caveat)
        # It doesn't matter that we're invalidating dm here because we're
        # about to throw it away.
        discharge_m = dm.macaroon
        m = primary.prepare_for_request(discharge_m)
        discharges.append(m)
        add_caveats(dm)
    return discharges


class ThirdPartyCaveatChecker(object):
    ''' Defines an abstract class that's used to check third party caveats.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def check_third_party_caveat(self, ctx, info):
        ''' If the caveat is valid, it returns optionally a slice of
        extra caveats that will be added to the discharge macaroon.
        If the caveat kind was not recognised, the checker should
        raise a CaveatNotRecognized exception; if the check failed,
        it should raise a ThirdPartyCaveatCheckFailed exception.
        :param ctx (AuthContext)
        :param info (ThirdPartyCaveatInfo) holds the information decoded from
        a third party caveat id
        :return: An array of extra caveats to be added to the discharge
        macaroon.
        '''
        raise NotImplementedError('check_third_party_caveat method must be '
                                  'defined in subclass')


class _LocalDischargeChecker(ThirdPartyCaveatChecker):
    def check_third_party_caveat(self, ctx, info):
        if info.condition != 'true':
            raise CaveatNotRecognizedError()
        return []


def discharge(ctx, id, caveat, key, checker, locator):
    ''' Creates a macaroon to discharge a third party caveat.

    The given parameters specify the caveat and how it should be checked.
    The condition implicit in the caveat is checked for validity using checker.
    If it is valid, a new macaroon is returned which discharges the caveat.
    The macaroon is created with a version derived from the version that was
    used to encode the id.

    :param id: (bytes) holds the id to give to the discharge macaroon.
    If Caveat is empty, then the id also holds the encrypted third party
    caveat.
    :param caveat: (bytes) holds the encrypted third party caveat.
    If this is None, id will be used.
    :param key: holds the key to use to decrypt the third party caveat
    information and to encrypt any additional third party caveats returned by
    the caveat checker.
    :param checker: used to check the third party caveat, and may also return
    further caveats to be added to the discharge macaroon.
    :param locator: used to information on third parties referred to by third
    party caveats returned by the Checker.
    '''
    caveat_id_prefix = []
    if caveat is None:
        # The caveat information is encoded in the id itself.
        caveat = id
    else:
        # We've been given an explicit id, so when extra third party
        # caveats are added, use that id as the prefix
        # for any more ids.
        caveat_id_prefix = id
    cav_info = decode_caveat(key, caveat)
    cav_info = ThirdPartyCaveatInfo(
        condition=cav_info.condition,
        first_party_public_key=cav_info.first_party_public_key,
        third_party_key_pair=cav_info.third_party_key_pair,
        root_key=cav_info.root_key,
        caveat=cav_info.caveat,
        version=cav_info.version,
        id=id,
        namespace=cav_info.namespace
    )
    # Note that we don't check the error - we allow the
    # third party checker to see even caveats that we can't
    # understand.
    try:
        cond, arg = checkers.parse_caveat(cav_info.condition)
    except ValueError as exc:
        raise VerificationError(exc.args[0])

    if cond == checkers.COND_NEED_DECLARED:
        cav_info = cav_info._replace(condition=arg.encode('utf-8'))
        caveats = _check_need_declared(ctx, cav_info, checker)
    else:
        caveats = checker.check_third_party_caveat(ctx, cav_info)

    # Note that the discharge macaroon does not need to
    # be stored persistently. Indeed, it would be a problem if
    # we did, because then the macaroon could potentially be used
    # for normal authorization with the third party.
    m = Macaroon(
        cav_info.root_key,
        id,
        '',
        cav_info.version,
        cav_info.namespace,
    )
    m._caveat_id_prefix = caveat_id_prefix
    if caveats is not None:
        for cav in caveats:
            m.add_caveat(cav, key, locator)
    return m


def _check_need_declared(ctx, cav_info, checker):
    arg = cav_info.condition.decode('utf-8')
    i = arg.find(' ')
    if i <= 0:
        raise VerificationError(
            'need-declared caveat requires an argument, got %q'.format(arg),
        )
    need_declared = arg[0:i].split(',')
    for d in need_declared:
        if d == '':
            raise VerificationError('need-declared caveat with empty required attribute')
    if len(need_declared) == 0:
        raise VerificationError('need-declared caveat with no required attributes')
    cav_info = cav_info._replace(condition=arg[i + 1:].encode('utf-8'))
    caveats = checker.check_third_party_caveat(ctx, cav_info)
    declared = {}
    for cav in caveats:
        if cav.location is not None and cav.location != '':
            continue
        # Note that we ignore the error. We allow the service to
        # generate caveats that we don't understand here.
        try:
            cond, arg = checkers.parse_caveat(cav.condition)
        except ValueError:
            continue
        if cond != checkers.COND_DECLARED:
            continue
        parts = arg.split()
        if len(parts) != 2:
            raise VerificationError('declared caveat has no value')
        declared[parts[0]] = True
    # Add empty declarations for everything mentioned in need-declared
    # that was not actually declared.
    for d in need_declared:
        if not declared.get(d, False):
            caveats.append(checkers.declared_caveat(d, ''))
    return caveats


class _EmptyLocator(ThirdPartyLocator):
    def third_party_info(self, loc):
        return None


def local_third_party_caveat(key, version):
    ''' Returns a third-party caveat that, when added to a macaroon with
    add_caveat, results in a caveat with the location "local", encrypted with
    the given PublicKey.
    This can be automatically discharged by discharge_all passing a local key.
    '''
    if version >= VERSION_2:
        loc = 'local {} {}'.format(version, key)
    else:
        loc = 'local {}'.format(key)
    return checkers.Caveat(location=loc, condition='')
