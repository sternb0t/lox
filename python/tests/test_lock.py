from __future__ import unicode_literals

import unittest
from uuid import UUID

import mox

from python.lox import Lox
from python.core.lock import Lock
from python.core import states
from python.core import errors

class LockTests(mox.MoxTestBase):

    def setUp(self):
        self.config = {"backend": {"redis": "redis://:@localhost:6379/0"}}
        self.lox = Lox("sesamebagel", config=self.config)
        self.lox.clear_all()
        self.lock = None
        super(LockTests, self).setUp()

    def tearDown(self):
        self.lox.clear_all()
        # clear from the backend manually,
        # since self.lox does not have a reference to this lock
        if self.lock:
            self.lock.clear()
        super(LockTests, self).tearDown()

    def test_init(self):
        self.lock = Lock(self.lox, 1)
        self.assertEqual(self.lock.state, states.STATE_INIT)
        self.assertEqual(self.lock.parent, self.lox)
        self.assertEqual(self.lock.backend, self.lox.backend)
        self.assertEqual(self.lock.config, self.lox.config)
        self.assertEqual(self.lock.id, 1)
        self.assertIsNone(self.lock._lock)

    ## ---- acquire ---- ##

    def test_acquire__with_id(self):
        self.lock = Lock(self.lox, 1)
        self.lock.acquire()
        self.assertEqual(self.lock.state, states.STATE_ACQUIRED)

    def test_acquire__without_id(self):
        self.lock = Lock(self.lox)
        # should assign a UUID automatically
        self.assertIsInstance(self.lock.id, UUID)
        self.lock.acquire()
        self.assertEqual(self.lock.state, states.STATE_ACQUIRED)

    def test_acquire__with_retry(self):
        self.lock = Lock(self.lox)
        self.lock.acquire(retry=True)
        self.assertEqual(self.lock.state, states.STATE_ACQUIRED)

    def test_acquire__with_retry_num_retries(self):
        self.lock = Lock(self.lox)
        self.lock.acquire(retry=True, num_tries=2)
        self.assertEqual(self.lock.state, states.STATE_ACQUIRED)

    def test_acquire__with_retry_num_retries_retry_interval(self):
        self.lock = Lock(self.lox)
        self.lock.acquire(retry=True, num_tries=2, retry_interval_seconds=0.5)
        self.assertEqual(self.lock.state, states.STATE_ACQUIRED)

    def test_acquire_works_on_3rd_try(self):
        self.lock = Lock(self.lox)

        # stub out the back end so we can simulate failures
        self.mox.StubOutWithMock(self.lock.backend, "acquire")

        # two fails, one success
        self.lock.backend.acquire(self.lock.parent.name, self.lock.id).AndRaise(errors.LockInUseException)
        self.lock.backend.acquire(self.lock.parent.name, self.lock.id).AndRaise(errors.LockInUseException)
        self.lock.backend.acquire(self.lock.parent.name, self.lock.id).AndReturn("3rd time's a charm")

        self.mox.ReplayAll()

        self.lock.acquire(retry=True, num_tries=3, retry_interval_seconds=0.1)

        self.assertEqual(self.lock.state, states.STATE_ACQUIRED)

    def test_acquire_fails_multiple_tries(self):
        self.lock = Lock(self.lox)

        # stub out the back end so we can simulate failures
        self.mox.StubOutWithMock(self.lock.backend, "acquire")

        # two fails, one success
        self.lock.backend.acquire(self.lock.parent.name, self.lock.id).AndRaise(errors.LockInUseException)
        self.lock.backend.acquire(self.lock.parent.name, self.lock.id).AndRaise(errors.LockInUseException)
        self.lock.backend.acquire(self.lock.parent.name, self.lock.id).AndRaise(errors.LockInUseException)

        self.mox.ReplayAll()

        with self.assertRaises(errors.LockInUseException):
            self.lock.acquire(retry=True, num_tries=3, retry_interval_seconds=0.1)

        self.assertEqual(self.lock.state, states.STATE_ACQUIRING_TIMEDOUT)

    def test_acquire_fails_no_retries(self):
        self.lock = Lock(self.lox)

        # stub out the back end so we can simulate failures
        self.mox.StubOutWithMock(self.lock.backend, "acquire")

        # two fails, one success
        self.lock.backend.acquire(self.lock.parent.name, self.lock.id).AndRaise(errors.LockInUseException)

        self.mox.ReplayAll()

        with self.assertRaises(errors.LockInUseException):
            self.lock.acquire(retry=False)

        self.assertEqual(self.lock.state, states.STATE_ACQUIRING_EXCEPTION)

    def test_acquire_unexpected_state(self):
        self.lock = Lock(self.lox)
        bad_states = [v for k, v in states.__dict__.iteritems()
                      if k.startswith("STATE_") and v not in states.OK_TO_ACQUIRE]
        for bad_state in bad_states:
            self.lock.state = bad_state
            with self.assertRaises(errors.UnexpectedStateException):
                self.lock.acquire()

    ## ---- release ---- ##

    def test_release(self):

        self.lock = Lock(self.lox, 1)
        self.lock.acquire()
        self.assertEqual(self.lock.state, states.STATE_ACQUIRED)
        self.lock.release()
        self.assertEqual(self.lock.state, states.STATE_RELEASED)

    def test_release_unexpected_state(self):
        self.lock = Lock(self.lox)
        bad_states = [v for k, v in states.__dict__.iteritems()
                      if k.startswith("STATE_") and v not in states.OK_TO_RELEASE]
        for bad_state in bad_states:
            self.lock.state = bad_state
            with self.assertRaises(errors.UnexpectedStateException):
                self.lock.release()


if __name__ == '__main__':
    unittest.main()
