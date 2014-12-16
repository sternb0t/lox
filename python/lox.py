from __future__ import unicode_literals

from .core.lock import Lock
from .core.errors import *

__version__ = "0.0.1"

class Lox(object):
    """
    Main API for distributed locking, with schmear.
    """
    def __init__(self, name=None):
        # you might want to have multiple of these around, so allow naming each
        self.name = name or "Lox"
        # configuration... tbd build settings
        self.config = None
        # will hold a list of locks we're managing here
        self.locks = {}
        # will hold the lock when used as a context manager
        self.context_lock = None

    def acquire(self, id=None):
        """
        Get a lock with the given ID, using the configured backend provider.
        :param id: unique identifier for this lock, within this Lox instance
        :return: the acquired lock object
        """
        if id and id in self.locks:
            raise LockAlreadyAcquiredException("Lock %s cannot be acquired more than once." % id)
        lock = Lock(self, id)
        self.locks[lock.id] = lock
        return lock.acquire()

    def release(self, id=None):
        """
        Release the lock with the given ID.
        :param id: unique identifier for this lock, within this Lox instance
        :return: the released lock object
        """
        if not self.locks:
            raise LockNotFoundException("No locks to release")
        if id and id not in self.locks:
            raise LockNotFoundException("Lock %s not found" % id)
        # free it up
        lock = self.locks.pop(id)
        return lock.release()

    def __enter__(self):
        """
        Use Lox as a context manager.
        """
        self.context_lock = self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Use Lox as a context manager.
        """
        self.context_lock.release()
        if exc_val:
            return False
        return self
