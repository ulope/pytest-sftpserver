from functools import wraps

from pytest_sftpserver.sftp.server import SFTPServer


class sftpserver_factory(object):
    def __enter__(self):
        self.server = SFTPServer()
        self.server.start()
        return self.server

    def __exit__(self, *args, **kwargs):
        if self.server.is_alive():
            self.server.shutdown()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                kwargs["sftpserver"] = self.server
                return func(*args, **kwargs)

        return wrapper
