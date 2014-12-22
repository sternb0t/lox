from __future__ import unicode_literals

class LockAlreadyAcquiredException(BaseException):
    """ thrown when a single Lox instance / thread has the same lock """
    pass

class LockInUseException(BaseException):
    """ thrown when another Lox instance / thread has the same lock """
    pass

class LockNotFoundException(BaseException):
    """ thrown when trying to release a lock that hasn't yet been acquired """
    pass

class BackendConfigException(BaseException):
    pass

class UnexpectedStateException(BaseException):
    pass

class SchemaConflictException(BaseException):
    pass
