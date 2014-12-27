from __future__ import unicode_literals


class BaseLoxBackend(object):
    """
    Base class for lox providers.
    """
    def __init__(self, config):
        self.config = config
        self.connection = None

    @staticmethod
    def key(lox_name, lock_id):
        return "{}_{}".format(lox_name, lock_id)


class BackendLock(object):
    """
    Simple object to hold implementation-specific backend lock details
    """
    def __init__(self, key, lox_name, lock_id, acquire_ts=None, expire_ts=None, provider_lock=None):
        self.lox_name = lox_name
        self.lock_id = lock_id
        self.key = key or BaseLoxBackend.key(lox_name, lock_id)

        self.acquire_ts = acquire_ts
        self.expire_ts = expire_ts

        self.provider_lock = provider_lock

