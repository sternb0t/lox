from __future__ import unicode_literals

from redis import StrictRedis
from redis.lock import Lock

from python.core.errors import *

class RedisLoxBackend(object):

    def __init__(self, config):
        self.config = config
        self.redis_connection = None

    def connect(self):
        url = self.config["backend"]["redis"]
        self.redis_connection = StrictRedis.from_url(url)

    def acquire(self, lox_name, lock_id):
        key = self.key(lox_name, lock_id)
        lock = Lock(self.redis_connection, key)
        if lock.acquire(blocking=False):
            return lock
        else:
            raise LockInUseException("Lock {} has been acquired previously, possibly by another thread/process, and is not available.".format(key))

    def release(self, lock):
        return lock.release()

    def clear(self, lox_name, lock_id):
        key = self.key(lox_name, lock_id)
        self.redis_connection.delete(key)

    def key(self, lox_name, lock_id):
        return "{}_{}".format(lox_name, lock_id)

