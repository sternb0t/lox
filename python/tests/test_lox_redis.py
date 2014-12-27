from __future__ import unicode_literals

import unittest
import time

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

    def test_acquire__timeout(self):
        lock = self.lox.acquire(expires_seconds=0.5)
        # make sure the underlying key exists
        self.assertTrue(lock._lock.provider_lock.redis.exists(lock.key))
        # wait long enough for the lock to expire
        time.sleep(0.7)
        # make sure redis removed the lock
        self.assertFalse(lock._lock.provider_lock.redis.exists(lock.key))


if __name__ == '__main__':
    unittest.main()
