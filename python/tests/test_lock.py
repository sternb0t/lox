from __future__ import unicode_literals

import unittest
from uuid import UUID

from python.lox import Lox
from python.core.lock import Lock
from python.core.states import *

class LoxTests(unittest.TestCase):
    
    def test_init(self):
        lox = Lox("sesame")
        lock = Lock(lox, 1)
        self.assertEqual(lock.parent, lox)
        self.assertEqual(lock.state, STATE_INIT)

    def test_acquire(self):
        lox = Lox("sesame")
        lock = Lock(lox, 1)
        lock = lock.acquire()
        self.assertEqual(lock.state, STATE_ACQUIRED)

        lock2 = Lock(lox)
        self.assertIsInstance(lock2.id, UUID)

    def test_release(self):
        lox = Lox("sesame")
        lock = Lock(lox, 1)
        lock = lock.acquire()
        lock = lock.release()
        self.assertEqual(lock.state, STATE_RELEASED)


if __name__ == '__main__':
    unittest.main()
