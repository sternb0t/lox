from __future__ import unicode_literals

import unittest

from python.lox import Lox
from python.core.lock import Lock
from python.core.errors import *
from python.core.states import *

class LoxTests(unittest.TestCase):

    def setUp(self):
        self.config = {"backend": {"redis": "redis://:@localhost:6379/0"}}
        self.lox = Lox("poppy", config=self.config)
        self.lox.clear_all()

    def tearDown(self):
        self.lox.clear_all()
    
    def test_init(self):
        self.assertEqual(self.lox.name, "poppy")
        self.assertEqual(self.lox.config, self.config)
        self.assertEqual(self.lox.locks, {})
        self.assertIsNone(self.lox.context_lock)

    def test_acquire__basic(self):
        # get a lock
        lock = self.lox.acquire(1)
        self.assertIsInstance(lock, Lock)
        self.assertEqual(self.lox.locks, {1: lock})
        # get another lock, it's fun!
        lock2 = self.lox.acquire(2)
        self.assertIsInstance(lock2, Lock)
        self.assertEqual(self.lox.locks, {1: lock, 2: lock2})
        # get another lock without ID
        lock3 = self.lox.acquire()
        self.assertIsInstance(lock3, Lock)
        self.assertEqual(self.lox.locks, {1: lock, 2: lock2, lock3.id: lock3})

    def test_acquire__twice_raises(self):
        lock = self.lox.acquire(1)
        # make sure it busts if we try this again
        with self.assertRaises(LockAlreadyAcquiredException):
            self.lox.acquire(1)

    def test_release__basic(self):
        # get two locks
        lock = self.lox.acquire(1)
        lock2 = self.lox.acquire(2)
        # release first
        self.lox.release(1)
        # make sure 2nd is still in there
        self.assertEqual(self.lox.locks, {2: lock2})

    def test_release__not_found(self):
        # basic busts
        with self.assertRaises(LockNotFoundException):
            self.lox.release()
        with self.assertRaises(LockNotFoundException):
            self.lox.release(1)
        # get a lock, but try to release a different one
        lock = self.lox.acquire(1)
        with self.assertRaises(LockNotFoundException):
            self.lox.release(2)

    def test_ctx_manager(self):
        # do this twice to make sure context_lock is handled correctly
        self.__ctx_manager()
        self.__ctx_manager()

    def __ctx_manager(self):
        with Lox(config=self.config) as lox:
            self.assertIsNotNone(lox.context_lock)
            self.assertEqual(lox.context_lock.state, STATE_ACQUIRED)
        self.assertEqual(lox.context_lock.state, STATE_RELEASED)


if __name__ == '__main__':
    unittest.main()
