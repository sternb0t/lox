from __future__ import unicode_literals

import time
import uuid

from .states import *
from .errors import *

class Lock(object):
    """
    A basic object that uses a backend to acquire, hold, and release a distributed lock.
    """

    def __init__(self, parent, id=None):
        # immediately set state
        self.state = STATE_INIT
        # parent Lox wrapper class
        self.parent = parent
        self.backend = parent.backend
        # configuration (may be overriden here?)
        self.config = parent.config
        self.id = id or Lock.generate_id()
        # this will hold the lock object from the backend
        self._lock = None

    @staticmethod
    def generate_id():
        return uuid.uuid1()

    def acquire(self, expires_seconds=None, retry=False, num_tries=None, retry_interval_seconds=None):
        """
        Acquire a lock, with optional retry logic. See Lox.acquire for param details.
        """
        if self.state not in OK_TO_ACQUIRE:
            raise UnexpectedStateException("Unable to acquire lock {} because state is {}".format(self.id, self.state))

        self.state = STATE_ACQUIRING

        if not retry:
            num_tries = 1
        if not num_tries:
            num_tries = self.config.get("num_tries", 3)
        if retry_interval_seconds is None:
            retry_interval_seconds = self.config.get("retry_interval_seconds", 1)

        counter = 1
        while counter <= num_tries:
            try:
                self._lock = self.backend.acquire(self.parent.name, self.id)
            except LockInUseException as ex:
                if not retry:
                    self.state = STATE_ACQUIRING_EXCEPTION
                    raise LockInUseException("Could not acquire lock {} because it is in use. " \
                                             "Not retrying.".format(self.id))
                counter += 1
                self.state = STATE_ACQUIRING_RETRYING
                if retry_interval_seconds:
                    time.sleep(retry_interval_seconds)
            else:
                self.state = STATE_ACQUIRED
                break

        if self.state == STATE_ACQUIRING_RETRYING:
            self.state = STATE_ACQUIRING_TIMEDOUT
            raise LockInUseException("Could not acquire lock {} after {} attempts because " \
                                     "it is in use".format(self.id, num_tries))

        return self

    def release(self):
        """
        Explicitly release a lock.
        """
        if self.state not in OK_TO_RELEASE or not self._lock:
            raise UnexpectedStateException("Unable to release lock {} because state is {}".format(self.id, self.state))

        self.state = STATE_RELEASING

        # hit the actual backend here...
        self.backend.release(self._lock)

        self.state = STATE_RELEASED
        return self

    def clear(self):
        """
        Delete a lock without releasing it (meant as a cleanup / admin / testing function).
        """
        self.backend.clear(self.parent.name, self.id)
