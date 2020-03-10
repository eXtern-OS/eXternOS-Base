# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
from unittest import TestCase

import macaroonbakery.bakery as bakery
import macaroonbakery.checkers as checkers


class TestAuthorizer(TestCase):
    def test_authorize_func(self):
        def f(ctx, identity, op):
            self.assertEqual(identity.id(), 'bob')
            if op.entity == 'a':
                return False, None
            elif op.entity == 'b':
                return True, None
            elif op.entity == 'c':
                return True, [checkers.Caveat(location='somewhere',
                                              condition='c')]
            elif op.entity == 'd':
                return True, [checkers.Caveat(location='somewhere',
                                              condition='d')]
            else:
                self.fail('unexpected entity: ' + op.Entity)

        ops = [bakery.Op('a', 'x'), bakery.Op('b', 'x'),
               bakery.Op('c', 'x'), bakery.Op('d', 'x')]
        allowed, caveats = bakery.AuthorizerFunc(f).authorize(
            checkers.AuthContext(),
            bakery.SimpleIdentity('bob'),
            ops
        )
        self.assertEqual(allowed, [False, True, True, True])
        self.assertEqual(caveats, [
            checkers.Caveat(location='somewhere', condition='c'),
            checkers.Caveat(location='somewhere', condition='d')
        ])

    def test_acl_authorizer(self):
        ctx = checkers.AuthContext()
        tests = [
            ('no ops, no problem',
             bakery.ACLAuthorizer(allow_public=True, get_acl=lambda x, y: []),
             None,
             [],
             []),
            ('identity that does not implement ACLIdentity; '
             'user should be denied except for everyone group',
             bakery.ACLAuthorizer(
                 allow_public=True,
                 get_acl=lambda ctx, op: [bakery.EVERYONE] if op.entity == 'a' else ['alice'],
             ),
             SimplestIdentity('bob'),
             [bakery.Op(entity='a', action='a'),
              bakery.Op(entity='b', action='b')],
             [True, False]),
            ('identity that does not implement ACLIdentity with user == Id; '
             'user should be denied except for everyone group',
             bakery.ACLAuthorizer(
                 allow_public=True,
                 get_acl=lambda ctx, op: [bakery.EVERYONE] if op.entity == 'a' else ['bob'],
             ),
             SimplestIdentity('bob'),
             [bakery.Op(entity='a', action='a'),
              bakery.Op(entity='b', action='b')],
             [True, False]),
            ('permission denied for everyone without AllowPublic',
             bakery.ACLAuthorizer(
                 allow_public=False,
                 get_acl=lambda x, y: [bakery.EVERYONE],
             ),
             SimplestIdentity('bob'),
             [bakery.Op(entity='a', action='a')],
             [False]),
            ('permission granted to anyone with no identity with AllowPublic',
             bakery.ACLAuthorizer(
                 allow_public=True,
                 get_acl=lambda x, y: [bakery.EVERYONE],
             ),
             None,
             [bakery.Op(entity='a', action='a')],
             [True])
        ]
        for test in tests:
            allowed, caveats = test[1].authorize(ctx, test[2], test[3])
            self.assertEqual(len(caveats), 0)
            self.assertEqual(allowed, test[4])

    def test_context_wired_properly(self):
        ctx = checkers.AuthContext({'a': 'aval'})

        class Visited:
            in_f = False
            in_allow = False
            in_get_acl = False

        def f(ctx, identity, op):
            self.assertEqual(ctx.get('a'), 'aval')
            Visited.in_f = True
            return False, None

        bakery.AuthorizerFunc(f).authorize(
            ctx, bakery.SimpleIdentity('bob'), ['op1']
        )
        self.assertTrue(Visited.in_f)

        class TestIdentity(SimplestIdentity, bakery.ACLIdentity):
            def allow(other, ctx, acls):
                self.assertEqual(ctx.get('a'), 'aval')
                Visited.in_allow = True
                return False

        def get_acl(ctx, acl):
            self.assertEqual(ctx.get('a'), 'aval')
            Visited.in_get_acl = True
            return []

        bakery.ACLAuthorizer(
            allow_public=False,
            get_acl=get_acl,
        ).authorize(ctx, TestIdentity('bob'), ['op1'])
        self.assertTrue(Visited.in_get_acl)
        self.assertTrue(Visited.in_allow)


class SimplestIdentity(bakery.Identity):
    # SimplestIdentity implements Identity for a string. Unlike
    # SimpleIdentity, it does not implement ACLIdentity.
    def __init__(self, user):
        self._identity = user

    def domain(self):
        return ''

    def id(self):
        return self._identity
