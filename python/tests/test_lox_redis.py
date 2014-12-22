from __future__ import unicode_literals

import unittest

from python.lox import Lox

from test_lox_base import LoxTestsBaseMixin

class LoxRedisTests(LoxTestsBaseMixin, unittest.TestCase):

    def setUp(self):
        self.config = {"backend": {"redis": "redis://:@localhost:6379/0"}}
        self.lox = Lox("poppyseedbagel", config=self.config)
        self.lox.clear_all()

    def tearDown(self):
        self.lox.clear_all()
    
    def test_init(self):
        self.assertEqual(self.lox.name, "poppyseedbagel")
        self.assertEqual(self.lox.config, self.config)
        self.assertEqual(self.lox.locks, {})
        self.assertIsNone(self.lox.context_lock)

if __name__ == '__main__':
    unittest.main()
