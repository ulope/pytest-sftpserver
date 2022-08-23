# encoding: utf-8
from __future__ import absolute_import, division, print_function

import pytest

from pytest_sftpserver.core import SFTPServerContextDecorator


@pytest.yield_fixture(scope="session")
def sftpserver(request):
    with SFTPServerContextDecorator() as server:
        yield server
