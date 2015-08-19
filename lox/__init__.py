# -*- coding: utf-8 -*-

"""

Lox distributed locking
~~~~~~~~~~~~~~~~~~~~~~~

Lox is a distributed locking library for Python, with schmear.

Currently supported backends:

1. Redis
2. PostgreSQL

A distributed lock can easily be wrapped around code that needs to be atomic:

    >>> from lox import Lox
    >>> with Lox('my-key', 'redis'):
    ...     do_something_with_race_conditions()

:copyright: (c) 2015 by Jeff Sternberg.
:license: MIT, see LICENSE for more details.

"""

__title__ = "lox"
__version__ = "0.1"
__license__ = "MIT"


from .lox import Lox
from .core.lock import Lock
from .core.errors import *
from .core.states import *
