from __future__ import unicode_literals

from lox.lox import DEFAULT_LOX_CONFIG
from lox.lox import Lox
from lox.core.lock import Lock
from lox.core.errors import *
from lox.core.states import *

class LoxTestsBaseMixin(object):

    def tearDown(self):
        self.lox.clear_all()

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

    def test_acquire__twice_separate_threads_raises(self):
        lock = self.lox.acquire(1)
        # make sure it busts if we try this again, even without the local in the instance dict
        del self.lox.locks[1]
        with self.assertRaises(LockInUseException):
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
        self.__ctx_manager(self.config)
        self.__ctx_manager(self.config)

    def test_ctx_manager_default_config(self):
        # config should default to the default
        test_lox = self.__ctx_manager(None)
        self.assertEqual(test_lox.config, DEFAULT_LOX_CONFIG)

    def __ctx_manager(self, test_config):
        with Lox(config=test_config) as test_lox:
            self.assertIsNotNone(test_lox.context_lock)
            self.assertEqual(test_lox.context_lock.state, STATE_ACQUIRED)
        self.assertEqual(test_lox.context_lock.state, STATE_RELEASED)
        return test_lox
