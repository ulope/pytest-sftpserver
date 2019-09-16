# encoding: utf-8
from __future__ import absolute_import, division, print_function

import calendar
import posixpath
import stat
from datetime import datetime
from os import O_CREAT

from paramiko import AUTH_SUCCESSFUL, OPEN_SUCCEEDED, ServerInterface
from paramiko.sftp import SFTP_FAILURE, SFTP_NO_SUCH_FILE, SFTP_OK
from paramiko.sftp_attr import SFTPAttributes
from paramiko.sftp_handle import SFTPHandle
from paramiko.sftp_si import SFTPServerInterface
from six import string_types, text_type

from pytest_sftpserver.sftp.util import abspath


class VirtualSFTPHandle(SFTPHandle):
    def __init__(self, path, content_provider, flags=0):
        super(VirtualSFTPHandle, self).__init__()
        self.path = path
        self.content_provider = content_provider
        if self.content_provider.get(self.path) is None and flags and flags & O_CREAT == O_CREAT:
            # Create new empty "file"
            self.content_provider.put(path, "")

    def close(self):
        return SFTP_OK

    def chattr(self, attr):
        if self.content_provider.get(self.path) is None:
            return SFTP_NO_SUCH_FILE

        return SFTP_OK

    def write(self, offset, data):
        content = self.content_provider.get(self.path)

        if content is None:
            return SFTP_OK if self.content_provider.put(self.path, data) else SFTP_NO_SUCH_FILE

        if not isinstance(content, string_types):
            # Can't offset write into a 'directory' or integer
            return SFTP_FAILURE

        if isinstance(content, text_type):
            content = content.encode()

        if offset > len(content):
            content = content + b"\x00" * (offset - len(content))

        content = content[:offset] + data + content[offset + len(data) :]
        return SFTP_OK if self.content_provider.put(self.path, content) else SFTP_FAILURE

    def read(self, offset, length):
        if self.content_provider.get(self.path) is None:
            return SFTP_NO_SUCH_FILE

        end = offset + length
        return self.content_provider.get(self.path)[offset:end]

    def stat(self):
        if self.content_provider.get(self.path) is None:
            return SFTP_NO_SUCH_FILE

        mtime = calendar.timegm(datetime.now().timetuple())

        sftp_attrs = SFTPAttributes()
        sftp_attrs.st_size = self.content_provider.get_size(self.path)
        sftp_attrs.st_uid = 0
        sftp_attrs.st_gid = 0
        sftp_attrs.st_mode = (
            stat.S_IRWXO
            | stat.S_IRWXG
            | stat.S_IRWXU
            | (stat.S_IFDIR if self.content_provider.is_dir(self.path) else stat.S_IFREG)
        )
        sftp_attrs.st_atime = mtime
        sftp_attrs.st_mtime = mtime
        sftp_attrs.filename = posixpath.basename(self.path)
        return sftp_attrs


class VirtualSFTPServerInterface(SFTPServerInterface):
    def __init__(self, server, *largs, **kwargs):
        self.content_provider = kwargs.pop("content_provider", None)
        ":type: ContentProvider"
        super(VirtualSFTPServerInterface, self).__init__(server, *largs, **kwargs)

    @abspath
    def list_folder(self, path):
        return [
            self.stat(posixpath.join(path, fname)) for fname in self.content_provider.list(path)
        ]

    @abspath
    def open(self, path, flags, attr):
        return VirtualSFTPHandle(path, self.content_provider, flags=flags)

    @abspath
    def remove(self, path):
        return SFTP_OK if self.content_provider.remove(path) else SFTP_NO_SUCH_FILE

    @abspath
    def rename(self, oldpath, newpath):
        content = self.content_provider.get(oldpath)
        if not content:
            return SFTP_NO_SUCH_FILE
        res = self.content_provider.put(newpath, content)
        if res:
            res = res and self.content_provider.remove(oldpath)
        return SFTP_OK if res else SFTP_FAILURE

    @abspath
    def rmdir(self, path):
        return SFTP_OK if self.content_provider.remove(path) else SFTP_FAILURE

    @abspath
    def mkdir(self, path, attr):
        if self.content_provider.get(path) is not None:
            return SFTP_FAILURE
        return SFTP_OK if self.content_provider.put(path, {}) else SFTP_FAILURE

    @abspath
    def stat(self, path):
        return VirtualSFTPHandle(path, self.content_provider).stat()

    @abspath
    def chattr(self, path, attr):
        return VirtualSFTPHandle(path, self.content_provider).chattr(attr)


class AllowAllAuthHandler(ServerInterface):
    def check_auth_none(self, username):
        return AUTH_SUCCESSFUL

    def check_auth_password(self, username, password):
        return AUTH_SUCCESSFUL

    def check_auth_publickey(self, username, key):
        return AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        return OPEN_SUCCEEDED
