from pytest_sftpserver.decorator import sftpserver_factory  # noqa: F401

VERSION = (1, 3, 0)


def get_version():
    return ".".join(str(i) for i in VERSION)
