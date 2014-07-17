# encoding: utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os


_KEYDIR = os.path.join(os.path.dirname(__file__), "keys")
SERVER_KEY_PRIVATE = os.path.join(_KEYDIR, "sftp_server.priv")
SERVER_KEY_PUBLIC = os.path.join(_KEYDIR, "sftp_server.pub")
