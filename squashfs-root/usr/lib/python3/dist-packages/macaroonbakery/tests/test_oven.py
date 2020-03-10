# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import copy
from datetime import datetime, timedelta
from unittest import TestCase

import macaroonbakery.bakery as bakery

EPOCH = datetime(1900, 11, 17, 19, 00, 13, 0, None)
AGES = EPOCH + timedelta(days=10)


class TestOven(TestCase):
    def test_canonical_ops(self):
        canonical_ops_tests = (
            ('empty array', [], []),
            ('one element', [bakery.Op('a', 'a')],
             [bakery.Op('a', 'a')]),
            ('all in order',
             [bakery.Op('a', 'a'), bakery.Op('a', 'b'),
              bakery.Op('c', 'c')],
             [bakery.Op('a', 'a'), bakery.Op('a', 'b'),
              bakery.Op('c', 'c')]),
            ('out of order',
             [bakery.Op('c', 'c'), bakery.Op('a', 'b'),
              bakery.Op('a', 'a')],
             [bakery.Op('a', 'a'), bakery.Op('a', 'b'),
              bakery.Op('c', 'c')]),
            ('with duplicates',
             [bakery.Op('c', 'c'), bakery.Op('a', 'b'),
              bakery.Op('a', 'a'), bakery.Op('c', 'a'),
              bakery.Op('c', 'b'), bakery.Op('c', 'c'),
              bakery.Op('a', 'a')],
             [bakery.Op('a', 'a'), bakery.Op('a', 'b'),
              bakery.Op('c', 'a'), bakery.Op('c', 'b'),
              bakery.Op('c', 'c')]),
            ('make sure we\'ve got the fields right',
             [bakery.Op(entity='read', action='two'),
              bakery.Op(entity='read', action='one'),
              bakery.Op(entity='write', action='one')],
             [bakery.Op(entity='read', action='one'),
              bakery.Op(entity='read', action='two'),
              bakery.Op(entity='write', action='one')])
        )
        for about, ops, expected in canonical_ops_tests:
            new_ops = copy.copy(ops)
            canonical_ops = bakery.canonical_ops(new_ops)
            self.assertEquals(canonical_ops, expected)
            # Verify that the original array isn't changed.
            self.assertEquals(new_ops, ops)

    def test_multiple_ops(self):
        test_oven = bakery.Oven(
            ops_store=bakery.MemoryOpsStore())
        ops = [bakery.Op('one', 'read'),
               bakery.Op('one', 'write'),
               bakery.Op('two', 'read')]
        m = test_oven.macaroon(bakery.LATEST_VERSION, AGES,
                               None, ops)
        got_ops, conds = test_oven.macaroon_ops([m.macaroon])
        self.assertEquals(len(conds), 1)  # time-before caveat.
        self.assertEquals(bakery.canonical_ops(got_ops), ops)

    def test_multiple_ops_in_id(self):
        test_oven = bakery.Oven()
        ops = [bakery.Op('one', 'read'),
               bakery.Op('one', 'write'),
               bakery.Op('two', 'read')]
        m = test_oven.macaroon(bakery.LATEST_VERSION, AGES,
                               None, ops)
        got_ops, conds = test_oven.macaroon_ops([m.macaroon])
        self.assertEquals(len(conds), 1)  # time-before caveat.
        self.assertEquals(bakery.canonical_ops(got_ops), ops)

    def test_multiple_ops_in_id_with_version1(self):
        test_oven = bakery.Oven()
        ops = [bakery.Op('one', 'read'),
               bakery.Op('one', 'write'),
               bakery.Op('two', 'read')]
        m = test_oven.macaroon(bakery.VERSION_1, AGES, None, ops)
        got_ops, conds = test_oven.macaroon_ops([m.macaroon])
        self.assertEquals(len(conds), 1)  # time-before caveat.
        self.assertEquals(bakery.canonical_ops(got_ops), ops)

    def test_huge_number_of_ops_gives_small_macaroon(self):
        test_oven = bakery.Oven(
            ops_store=bakery.MemoryOpsStore())
        ops = []
        for i in range(30000):
            ops.append(bakery.Op(entity='entity' + str(i),
                                 action='action' + str(i)))

        m = test_oven.macaroon(bakery.LATEST_VERSION, AGES,
                               None, ops)
        got_ops, conds = test_oven.macaroon_ops([m.macaroon])
        self.assertEquals(len(conds), 1)  # time-before caveat.
        self.assertEquals(bakery.canonical_ops(got_ops),
                          bakery.canonical_ops(ops))

        data = m.serialize_json()
        self.assertLess(len(data), 300)

    def test_ops_stored_only_once(self):
        st = bakery.MemoryOpsStore()
        test_oven = bakery.Oven(ops_store=st)

        ops = [bakery.Op('one', 'read'),
               bakery.Op('one', 'write'),
               bakery.Op('two', 'read')]

        m = test_oven.macaroon(bakery.LATEST_VERSION, AGES,
                               None, ops)
        got_ops, conds = test_oven.macaroon_ops([m.macaroon])
        self.assertEquals(bakery.canonical_ops(got_ops),
                          bakery.canonical_ops(ops))

        # Make another macaroon containing the same ops in a different order.
        ops = [bakery.Op('one', 'write'),
               bakery.Op('one', 'read'),
               bakery.Op('one', 'read'),
               bakery.Op('two', 'read')]
        test_oven.macaroon(bakery.LATEST_VERSION, AGES, None,
                           ops)
        self.assertEquals(len(st._store), 1)
