from __future__ import unicode_literals

from redis import StrictRedis
from redis.lock import Lock

from lox.core.errors import *
from base_lox_backend import BaseLoxBackend, BackendLock

class RedisLoxBackend(BaseLoxBackend):
    """
    A lox provider that uses Redis as the backend lock store.
    Redis takes care of a lot of the details, including expiration, etc.
    """

    server_handles_expiration = True

    def connect(self):
        url = self.config["backend"]["redis"]
        self.connection = StrictRedis.from_url(url)

    def acquire(self, lox_name, lock_id, expires_seconds=None):
        key = self.key(lox_name, lock_id)
        lock = Lock(self.connection, key, timeout=expires_seconds)
        # retry logic is handled in core.lock, so no blocking here
        if lock.acquire(blocking=False):
            return BackendLock(key, lox_name, lock_id, provider_lock=lock)
        else:
            raise LockInUseException("Lock {} has been acquired previously, possibly by another thread/process, and is not available.".format(key))

    def release(self, lock):
        return lock.provider_lock.release()

    def clear(self, lox_name, lock_id):
        key = self.key(lox_name, lock_id)
        self.connection.delete(key)
