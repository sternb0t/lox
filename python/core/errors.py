from __future__ import unicode_literals

class LockAlreadyAcquiredException(BaseException):
    pass

class LockNotFoundException(BaseException):
    pass

class BackendConfigException(BaseException):
    pass

class LockNotAcquiredException(BaseException):
    pass

class LockInUseException(BaseException):
    pass
