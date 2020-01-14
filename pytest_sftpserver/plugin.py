# encoding: utf-8
from __future__ import absolute_import, division, print_function

import pytest

from pytest_sftpserver.decorator import sftpserver_factory


@pytest.yield_fixture(scope="session")
def sftpserver(request):
    with sftpserver_factory() as server:
        yield server
