from __future__ import unicode_literals

from .core.lock import Lock
from .core.errors import *
from .backends.redis_lox_backend import RedisLoxBackend
from .backends.postgres_lox_backend import PostgresLoxBackend


DEFAULT_LOX_CONFIG = {
    "backend": {
        "redis": "redis://:@localhost:6379/0"
    }
}

class Lox(object):
    """
    Main API for distributed locking, with schmear.
    """
    def __init__(self, name=None, config=None):
        # you might want to have multiple of these around, so allow naming each
        self.name = name or "Lox"
        # configuration: default to redis, for now
        if not config:
            self.config = DEFAULT_LOX_CONFIG
        else:
            self.config = config
        # will hold a list of locks we're managing here
        self.locks = {}
        # will hold the lock when used as a context manager
        self.context_lock = None
        # may want to do lazy connection...
        self.connect_backend()

    def connect_backend(self):
        self.backend = None
        if "redis" in self.config.get("backend"):
            self.backend = RedisLoxBackend(self.config)
        elif "postgres" in self.config.get("backend"):
            self.backend = PostgresLoxBackend(self.config)
        if not self.backend:
            raise BackendConfigException("No backend specified in settings.")
        self.backend.connect()

    def acquire(self, id=None, expires_seconds=None, retry=False, num_tries=None, retry_interval_seconds=None):
        """
        Get a lock with the given ID, using the configured backend provider.
        :param id: unique identifier for this lock, within this Lox instance.
        :param expires_seconds: Automatically expire (i.e release) the lock after this number of seconds.
                                Defaults to never expire the lock based on a timer.
        :param retry: if the lock cannot be acquired immediately, should we try to acquire it again later?
        :param num_tries: try to get this lock this many times before giving up.
        :param retry_interval_seconds: wait this number of seconds between retries.
        :return: the acquired Lock object
        """
        if id and id in self.locks:
            raise LockAlreadyAcquiredException("Lock %s cannot be acquired more than once." % id)
        lock = Lock(self, id)
        self.locks[lock.id] = lock
        return lock.acquire(expires_seconds=expires_seconds,
                            retry=retry,
                            num_tries=num_tries,
                            retry_interval_seconds=retry_interval_seconds)

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
        # free it from the instance level tracking
        lock = self.locks.pop(id)
        return lock.release()

    def clear_all(self):
        """
        Purge all locks from the backend without releasing them.
        This effectively resets the data store.
        Should only be used for admin, testing, etc.
        """
        for id, lock in self.locks.iteritems():
            lock.clear()
        self.locks = {}

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
