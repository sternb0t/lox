from __future__ import unicode_literals

import unittest
from uuid import UUID

from python.lox import Lox
from python.core.lock import Lock
from python.core.states import *

class LockTests(unittest.TestCase):

    def setUp(self):
        self.config = {"backend": {"redis": "redis://:@localhost:6379/0"}}
        self.lox = Lox("sesame", config=self.config)
        self.lox.clear_all()

    def tearDown(self):
        self.lox.clear_all()
    
    def test_init(self):
        lock = Lock(self.lox, 1)
        self.assertEqual(lock.parent, self.lox)
        self.assertEqual(lock.state, STATE_INIT)

    def test_acquire__with_id(self):
        lock = Lock(self.lox, 1)
        lock.acquire()
        self.assertEqual(lock.state, STATE_ACQUIRED)
        # clear from the backend manually,
        # since self.lox doesn't have a reference to this lock
        lock.clear()

    def test_acquire__without_id(self):
        lock = Lock(self.lox)
        # should assign a UUID automatically
        self.assertIsInstance(lock.id, UUID)
        lock.acquire()
        self.assertEqual(lock.state, STATE_ACQUIRED)
        # clear from the backend manually,
        # since self.lox doesn't have a reference to this lock
        lock.clear()

    def test_release(self):
        lock = Lock(self.lox, 1)
        lock = lock.acquire()
        self.assertEqual(lock.state, STATE_ACQUIRED)
        lock.release()
        self.assertEqual(lock.state, STATE_RELEASED)


if __name__ == '__main__':
    unittest.main()
