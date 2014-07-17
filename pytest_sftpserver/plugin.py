# encoding: utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import pytest

from pytest_sftpserver.sftp.server import SFTPServer


@pytest.yield_fixture(scope="session")
def sftpserver(request):
    server = SFTPServer()
    server.start()

    yield server

    if server.is_alive():
        server.shutdown()
