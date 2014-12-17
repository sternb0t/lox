from __future__ import unicode_literals

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
        return uuid.uuid4()

    def acquire(self):
        if self.state not in [STATE_INIT, STATE_RELEASED]:
            raise LockInUseException("Unable to acquire lock %s because state is %s" % self.id, self.state)

        # immediately set state
        self.state = STATE_ACQUIRING

        # hit the actual backend here...
        # TODO: exception handling
        self._lock = self.backend.acquire(self.parent.name, self.id)

        self.state = STATE_ACQUIRED
        return self

    def release(self):
        if self.state != STATE_ACQUIRED or not self._lock:
            raise LockNotAcquiredException("Unable to release lock %s because state is %s" % self.id, self.state)

        self.state = STATE_RELEASING

        # hit the actual backend here...
        self._lock.release()

        self.state = STATE_RELEASED
        return self

    def clear(self):
        self.backend.clear(self.parent.name, self.id)
