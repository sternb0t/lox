from __future__ import unicode_literals

import time
import uuid

from .states import *

class Lock(object):
    """
    A basic object that uses a backend to acquire, hold, and release a distributed lock.
    """

    def __init__(self, parent, id=None):
        # immediately set state
        self.state = STATE_INIT
        # parent Lox wrapper class
        self.parent = parent
        # configuration (may be overriden here?)
        self.config = parent.config
        self.id = id or Lock.generate_id()

    @staticmethod
    def generate_id():
        return uuid.uuid4()

    def acquire(self):
        # immediately set state
        self.state = STATE_ACQUIRING

        # hit the actual backend here...
        time.sleep(0.01)

        self.state = STATE_ACQUIRED
        return self

    def release(self):
        # immediately set state
        self.state = STATE_RELEASING

        # hit the actual backend here...
        time.sleep(0.01)

        self.state = STATE_RELEASED
        return self
