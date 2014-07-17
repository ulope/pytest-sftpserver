# encoding: utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from functools import wraps
from pytest_sftpserver.compat import getcallargs
import os


def _mkabspath(path):
    return os.path.abspath(os.path.join("/", path))


def abspath(func):
    @wraps(func)
    def _inner(*args, **kwargs):
        callargs = getcallargs(func, *args, **kwargs)
        for arg_name, arg_value in callargs.items():
            if "path" in arg_name:
                callargs[arg_name] = _mkabspath(arg_value)
        return func(**callargs)

    return _inner
