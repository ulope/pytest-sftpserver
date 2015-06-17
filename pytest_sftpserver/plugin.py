# encoding: utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import pytest

from pytest_sftpserver.core import SFTPServerContextDecorator


@pytest.yield_fixture(scope="session")
def sftpserver(request):
    with SFTPServerContextDecorator() as server:
        yield server
