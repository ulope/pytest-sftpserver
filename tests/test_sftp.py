from contextlib import contextmanager
from copy import deepcopy
import posixpath
import sys
import time

from paramiko import Transport
from paramiko.channel import Channel
from paramiko.sftp_client import SFTPClient
import pytest

from pytest_sftpserver.sftp.server import SFTPServer

# fmt: off
CONTENT_OBJ = dict(
    a=dict(
        b="testfile1",
        c="testfile2",
        f=["testfile5", "testfile6"]
    ),
    d="testfile3"
)
# fmt: on


@pytest.yield_fixture(scope="session")
def sftpclient(sftpserver):
    transport = Transport((sftpserver.host, sftpserver.port))
    transport.connect(username="a", password="b")
    sftpclient = SFTPClient.from_transport(transport)
    yield sftpclient
    sftpclient.close()
    transport.close()


@pytest.yield_fixture
def content(sftpserver):
    with sftpserver.serve_content(deepcopy(CONTENT_OBJ)):
        yield


@contextmanager
def check_stat_times(client, path, atime_change=False, mtime_change=False):
    # "path" can be just a string, or a tuple of strings
    # The tuple form is useful if testing a file that gets renamed
    if isinstance(path, (tuple, list)):
        old_path, new_path = path
    else:
        old_path, new_path = path, path

    st = client.stat(old_path)

    time.sleep(2)
    yield

    new_st = client.stat(new_path)
    if atime_change:
        assert new_st.st_atime > st.st_atime   # atime should have updated
    else:
        assert new_st.st_atime == st.st_atime  # atime shouldn't have changed
    if mtime_change:
        assert new_st.st_mtime > st.st_mtime   # mtime should have updated
    else:
        assert new_st.st_mtime == st.st_mtime  # mtime shouldn't have updated


@pytest.mark.xfail(sys.version_info < (2, 7), reason="Intermittently broken on 2.6")
def test_sftpserver_bound(sftpserver):
    assert sftpserver.wait_for_bind(1)


def test_sftpserver_available(sftpserver):
    assert isinstance(sftpserver, SFTPServer)
    assert sftpserver.is_alive()
    assert str(sftpserver.port) in sftpserver.url


def test_sftpserver_connect(sftpclient):
    assert isinstance(sftpclient.sock, Channel)


def test_sftpserver_listdir_empty(sftpclient):
    assert sftpclient.listdir("/") == []


def test_sftpserver_listdir(content, sftpclient):
    assert set(sftpclient.listdir("/")) == set(["a", "d"])


def test_sftpserver_get_file_dict(content, sftpclient):
    with sftpclient.open("/a/b", "r") as f:
        assert f.read() == b"testfile1"


def test_sftpserver_get_file_list(content, sftpclient):
    with sftpclient.open("/a/f/0", "r") as f:
        assert f.read() == b"testfile5"


@pytest.mark.parametrize(
    ("offset", "data", "expected"),
    [
        (4, "test", b"testtest6"),
        (5, "test", b"testftest"),
        (9, "test", b"testfile6test"),
        (10, "test", b"testfile6\x00test"),
    ],
)
def test_sftpserver_put_file_offset(content, sftpclient, offset, data, expected):
    with sftpclient.open("/a/f/1", "rw") as f:
        f.seek(offset)
        f.write(data)
        f.seek(0)
        assert f.read() == expected


@pytest.mark.parametrize("path,expected",
    [("/e", set(["a", "d", "e"])),
     ("/a/f/2", set(["0", "1", "2"]))])
def test_sftpserver_put(content, sftpclient, path, expected):
    dirname = posixpath.dirname(path)
    with check_stat_times(sftpclient, dirname, mtime_change=True):
        with sftpclient.open(path, 'w') as f:
            f.write("foobar")
    assert set(sftpclient.listdir(dirname)) == expected


def test_sftpserver_put_file(content, sftpclient, tmpdir):
    tmpfile = tmpdir.join("test.txt")
    tmpfile.write("Hello world")
    with check_stat_times(sftpclient, "/a", mtime_change=True):
        sftpclient.put(str(tmpfile), "/a/test.txt")
    assert set(sftpclient.listdir("/a")) == set(["test.txt", "b", "c", "f"])


def test_sftpserver_round_trip(content, sftpclient, tmpdir):
    tmpfile = tmpdir.join("test.txt")
    thetext = u"Just some plain, normal text"
    tmpfile.write(thetext)
    sftpclient.put(str(tmpfile), "/a/test.txt")
    with sftpclient.open("/a/test.txt", "r") as result:
        assert result.read() == thetext.encode()


@pytest.mark.parametrize("path,expected",
    [("/a/c", set(["b", "f"])),
     ("/a/f/1", set(["0"]))])
def test_sftpserver_remove(content, sftpclient, path, expected):
    dirname = posixpath.dirname(path)
    with check_stat_times(sftpclient, dirname, mtime_change=True):
        sftpclient.remove(path)
    assert set(sftpclient.listdir(dirname)) == expected


def test_sftpserver_remove_file_list_fail(content, sftpclient):
    with pytest.raises(IOError):
        sftpclient.remove("/a/f/10")


def test_sftpserver_rename_file(content, sftpclient):
    dir_st = sftpclient.stat("/a")
    file_st = sftpclient.stat("/a/c")
    with check_stat_times(sftpclient, '/a', mtime_change=True), \
            check_stat_times(sftpclient, ('/a/c', '/a/x')):
        sftpclient.rename("/a/c", "/a/x")
    assert set(sftpclient.listdir("/a")) == set(["b", "f", "x"])


def test_sftpserver_rename_file_fail_source(content, sftpclient):
    with check_stat_times(sftpclient, '/a'):
        with pytest.raises(IOError):
            sftpclient.rename("/a/NOTHERE", "/a/x")


def test_sftpserver_rename_file_fail_target(content, sftpclient):
    with check_stat_times(sftpclient, '/a'):
        with pytest.raises(IOError):
            sftpclient.rename("/a/c", "/a/NOTHERE/x")


def test_sftpserver_rmdir(content, sftpclient):
    with check_stat_times(sftpclient, '/', mtime_change=True):
        sftpclient.rmdir("/a")
    assert set(sftpclient.listdir("/")) == set(["d"])


def test_sftpserver_mkdir(content, sftpclient):
    with check_stat_times(sftpclient, '/a', mtime_change=True):
        sftpclient.mkdir("/a/x")
    assert set(sftpclient.listdir("/a")) == set(["b", "c", "f", "x"])


def test_sftpserver_mkdir_existing(content, sftpclient):
    with check_stat_times(sftpclient, "/"), \
            check_stat_times(sftpclient, "/a"):
        with pytest.raises(IOError):
            sftpclient.mkdir("/a")
    assert set(sftpclient.listdir("/a")) == set(["b", "c", "f"])


def test_sftpserver_chmod(content, sftpclient):
    # coverage
    with check_stat_times(sftpclient, "/a"), \
            check_stat_times(sftpclient, "/a/c"):
        sftpclient.chmod("/a/b", 1)

    with check_stat_times(sftpclient, "/a"), \
            check_stat_times(sftpclient, "/a/c"):
        with sftpclient.open("/a/b", "r") as f:
            f.chmod(1)


def test_sftpserver_stat_non_str(sftpserver, sftpclient):
    with sftpserver.serve_content(dict(a=123)):
        assert sftpclient.stat("/a").st_size == 3


@pytest.mark.skip(reason="Broken test. Callables are now"
                         " called during construction because we need"
                         " to build the stat time dictionary.")
def test_sftpserver_exception(sftpclient, sftpserver):
    with sftpserver.serve_content({"a": lambda: 1 / 0}):
        with pytest.raises(IOError):
            sftpclient.open("/a", "r")


def test_sftpserver_stat_non_existing(sftpclient, sftpserver):
    with sftpserver.serve_content({}):
        with pytest.raises(IOError):
            sftpclient.stat("/a")


def test_sftpserver_chmod_non_existing(sftpclient, sftpserver):
    with sftpserver.serve_content({}):
        with pytest.raises(IOError):
            sftpclient.chmod("/a", 600)
