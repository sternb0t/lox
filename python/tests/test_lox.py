from __future__ import unicode_literals

import unittest

from python.lox import Lox
from python.core.lock import Lock
from python.core.errors import *
from python.core.states import *

class LoxTests(unittest.TestCase):
    
    def test_init(self):
        lox = Lox("poppy")
        self.assertEqual(lox.name, "poppy")
        self.assertIsNone(lox.config)
        self.assertEqual(lox.locks, {})
        self.assertIsNone(lox.context_lock)

    def test_acquire__basic(self):
        lox = Lox("plain")
        # get a lock
        lock = lox.acquire(1)
        self.assertIsInstance(lock, Lock)
        self.assertEqual(lox.locks, {1: lock})
        # get another lock, it's fun!
        lock2 = lox.acquire(2)
        self.assertIsInstance(lock2, Lock)
        self.assertEqual(lox.locks, {1: lock, 2: lock2})
        # get another lock without ID
        lock3 = lox.acquire()
        self.assertIsInstance(lock3, Lock)
        self.assertEqual(lox.locks, {1: lock, 2: lock2, lock3.id: lock3})

    def test_acquire__twice_raises(self):
        lox = Lox("plain")
        # get a lock
        lock = lox.acquire(1)
        with self.assertRaises(LockAlreadyAcquiredException):
            lox.acquire(1)

    def test_release__basic(self):
        lox = Lox("plain")
        # get two locks
        lock = lox.acquire(1)
        lock2 = lox.acquire(2)
        # release first
        lox.release(1)
        # make sure 2nd is still in there
        self.assertEqual(lox.locks, {2: lock2})

    def test_release__not_found(self):
        lox = Lox("plain")
        # basic misses
        with self.assertRaises(LockNotFoundException):
            lox.release()
        with self.assertRaises(LockNotFoundException):
            lox.release(1)
        # get a lock, but try to release a different one
        lock = lox.acquire(1)
        with self.assertRaises(LockNotFoundException):
            lox.release(2)

    def test_ctx_manager(self):
        # do this twice to make sure context_lock is handled correctly
        self.__ctx_manager()
        self.__ctx_manager()

    def __ctx_manager(self):
        with Lox() as lox:
            self.assertIsNotNone(lox.context_lock)
            self.assertEqual(lox.context_lock.state, STATE_ACQUIRED)
        self.assertEqual(lox.context_lock.state, STATE_RELEASED)


if __name__ == '__main__':
    unittest.main()
