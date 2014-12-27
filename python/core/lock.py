from __future__ import unicode_literals

from datetime import datetime
import time
import uuid
import threading

import pytz

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
        self.lox_name = parent.name
        # configuration (may be overriden here?)
        self.config = parent.config
        self.id = id or Lock.generate_id()
        # this will hold the lock object from the backend
        self._lock = None
        # default to not auto-expire
        self.expires_seconds = None
        # holds the timer thread for background auto expiration
        self._expiration_thread = None

    @staticmethod
    def generate_id():
        return uuid.uuid1()

    @property
    def key(self):
        if self._lock:
            return self._lock.key

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
        if expires_seconds == 0:
            raise ValueError("Param 'expires_seconds' must be None, or greater than 0")
        self.expires_seconds = expires_seconds

        counter = 1
        while counter <= num_tries:
            try:
                self._lock = self.backend.acquire(self.parent.name, self.id, expires_seconds=expires_seconds)
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
                if expires_seconds and not self.backend.server_handles_expiration:
                    self.auto_expire(expires_seconds=expires_seconds)
                break

        if self.state == STATE_ACQUIRING_RETRYING:
            self.state = STATE_ACQUIRING_TIMEDOUT
            raise LockInUseException("Could not acquire lock {} after {} attempts because " \
                                     "it is in use".format(self.id, num_tries))

        return self

    def auto_expire(self, **kwargs):
        """
        Set up a background timer to expire the lock in expires_seconds from now, with some padding
        """
        expires_seconds = kwargs.get("expires_seconds", 0)
        counter = kwargs.get("counter", 0)
        # double check expiration time
        if self._lock.expire_ts < datetime.now(tz=pytz.UTC):
            self.expire()
        # don't keep doing this forever...
        elif counter < 10:
            # first attempt, delay = expiration seconds, plus padding; after that, delay for half a second
            delay = expires_seconds + 0.1 if counter == 0 else 0.5
            counter += 1
            kwargs = {"expires_seconds": expires_seconds, "counter": counter}
            timer = threading.Timer(delay, self.auto_expire, kwargs=kwargs)
            timer.start()
            self._expiration_thread = timer

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

    def expire(self):
        """
        Explicitly expire a lock. Similar to release, but uses different states to be explicit as to what happened.
        """
        if self.state not in OK_TO_EXPIRE or not self._lock:
            raise UnexpectedStateException("Unable to expire lock {} because state is {}".format(self.id, self.state))

        self.state = STATE_EXPIRING

        # expiring a lock is the same thing as releasing from the backend's perspective
        self.backend.release(self._lock)

        self.state = STATE_EXPIRED
        return self

    def clear(self):
        """
        Delete a lock without releasing it (meant as a cleanup / admin / testing function).
        """
        self.backend.clear(self.parent.name, self.id)
