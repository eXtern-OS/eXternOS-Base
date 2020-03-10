# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
from ._auth_context import ContextKey
from ._caveat import Caveat, error_caveat, parse_caveat
from ._conditions import (
    COND_DECLARED,
    COND_NEED_DECLARED,
    STD_NAMESPACE,
)
from ._namespace import Namespace

DECLARED_KEY = ContextKey('declared-key')


def infer_declared(ms, namespace=None):
    '''Retrieves any declared information from the given macaroons and returns
    it as a key-value map.
    Information is declared with a first party caveat as created by
    declared_caveat.

    If there are two caveats that declare the same key with different values,
    the information is omitted from the map. When the caveats are later
    checked, this will cause the check to fail.
    namespace is the Namespace used to retrieve the prefix associated to the
    uri, if None it will use the STD_NAMESPACE only.
    '''
    conditions = []
    for m in ms:
        for cav in m.caveats:
            if cav.location is None or cav.location == '':
                conditions.append(cav.caveat_id_bytes.decode('utf-8'))
    return infer_declared_from_conditions(conditions, namespace)


def infer_declared_from_conditions(conds, namespace=None):
    ''' like infer_declared except that it is passed a set of first party
    caveat conditions as a list of string rather than a set of macaroons.
    '''
    conflicts = []
    # If we can't resolve that standard namespace, then we'll look for
    # just bare "declared" caveats which will work OK for legacy
    # macaroons with no namespace.
    if namespace is None:
        namespace = Namespace()
    prefix = namespace.resolve(STD_NAMESPACE)
    if prefix is None:
        prefix = ''
    declared_cond = prefix + COND_DECLARED

    info = {}
    for cond in conds:
        try:
            name, rest = parse_caveat(cond)
        except ValueError:
            name, rest = '', ''
        if name != declared_cond:
            continue
        parts = rest.split(' ', 1)
        if len(parts) != 2:
            continue
        key, val = parts[0], parts[1]
        old_val = info.get(key)
        if old_val is not None and old_val != val:
            conflicts.append(key)
            continue
        info[key] = val
    for key in set(conflicts):
        del info[key]
    return info


def context_with_declared(ctx, declared):
    ''' Returns a context with attached declared information,
    as returned from infer_declared.
    '''
    return ctx.with_value(DECLARED_KEY, declared)


def need_declared_caveat(cav, keys):
    if cav.location == '':
        return error_caveat('need-declared caveat is not third-party')
    return Caveat(location=cav.location,
                  condition=(COND_NEED_DECLARED + ' ' + ','.join(keys)
                             + ' ' + cav.condition))
