# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
from unittest import TestCase

import macaroonbakery.bakery as bakery


class TestOven(TestCase):
    def test_mem_store(self):
        st = bakery.MemoryKeyStore()

        key, id = st.root_key()
        self.assertEqual(len(key), 24)
        self.assertEqual(id.decode('utf-8'), '0')

        key1, id1 = st.root_key()
        self.assertEqual(key1, key)
        self.assertEqual(id1, id)

        key2 = st.get(id)
        self.assertEqual(key2, key)
