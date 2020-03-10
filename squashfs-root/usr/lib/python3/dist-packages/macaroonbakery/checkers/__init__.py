# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
from ._conditions import (
    STD_NAMESPACE,
    COND_DECLARED,
    COND_TIME_BEFORE,
    COND_ERROR,
    COND_ALLOW,
    COND_DENY,
    COND_NEED_DECLARED,
)
from ._caveat import (
    allow_caveat,
    deny_caveat,
    declared_caveat,
    parse_caveat,
    time_before_caveat,
    Caveat,
)
from ._declared import (
    context_with_declared,
    infer_declared,
    infer_declared_from_conditions,
    need_declared_caveat,
)
from ._operation import (
    context_with_operations,
)
from ._namespace import (
    Namespace,
    deserialize_namespace
)
from ._time import (
    context_with_clock,
    expiry_time,
    macaroons_expiry_time,
)
from ._checkers import (
    Checker,
    CheckerInfo,
    RegisterError,
)
from ._auth_context import (
    AuthContext,
    ContextKey,
)

from ._utils import (
    condition_with_prefix,
)

__all__ = [
    'AuthContext',
    'Caveat',
    'Checker',
    'CheckerInfo',
    'COND_ALLOW',
    'COND_DECLARED',
    'COND_DENY',
    'COND_ERROR',
    'COND_NEED_DECLARED',
    'COND_TIME_BEFORE',
    'ContextKey',
    'STD_NAMESPACE',
    'Namespace',
    'RegisterError',
    'allow_caveat',
    'condition_with_prefix',
    'context_with_declared',
    'context_with_operations',
    'context_with_clock',
    'declared_caveat',
    'deny_caveat',
    'deserialize_namespace',
    'expiry_time',
    'infer_declared',
    'infer_declared_from_conditions',
    'macaroons_expiry_time',
    'need_declared_caveat',
    'parse_caveat',
    'time_before_caveat',
]
