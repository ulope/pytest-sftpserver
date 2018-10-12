import sys
from copy import deepcopy

import pytest
from paramiko import Transport
from paramiko.channel import Channel
from paramiko.sftp_client import SFTPClient

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


def test_sftpserver_write_offset_unsupported(content, sftpclient):
    with sftpclient.open("/a/f/0", "w") as f:
        f.seek(1)
        with pytest.raises(IOError):
            f.write("test")


def test_sftpserver_put_file_dict(content, sftpclient):
    with sftpclient.open("/e", "w") as f:
        f.write("testfile4")
    assert set(sftpclient.listdir("/")) == set(["a", "d", "e"])


def test_sftpserver_put_file_list(content, sftpclient):
    with sftpclient.open("/a/f/2", "w") as f:
        f.write("testfile7")
    assert set(sftpclient.listdir("/a/f")) == set(["0", "1", "2"])


def test_sftpserver_put_file(content, sftpclient, tmpdir):
    tmpfile = tmpdir.join("test.txt")
    tmpfile.write("Hello world")
    sftpclient.put(str(tmpfile), "/a/test.txt")
    assert set(sftpclient.listdir("/a")) == set(["test.txt", "b", "c", "f"])


def test_sftpserver_round_trip(content, sftpclient, tmpdir):
    tmpfile = tmpdir.join("test.txt")
    thetext = u"Just some plain, normal text"
    tmpfile.write(thetext)
    sftpclient.put(str(tmpfile), "/a/test.txt")
    with sftpclient.open("/a/test.txt", "r") as result:
        assert result.read() == thetext.encode()


def test_sftpserver_remove_file_dict(content, sftpclient):
    sftpclient.remove("/a/c")
    assert set(sftpclient.listdir("/a")) == set(["b", "f"])


def test_sftpserver_remove_file_list(content, sftpclient):
    sftpclient.remove("/a/f/1")
    assert set(sftpclient.listdir("/a/f")) == set(["0"])


def test_sftpserver_remove_file_list_fail(content, sftpclient):
    with pytest.raises(IOError):
        sftpclient.remove("/a/f/10")


def test_sftpserver_rename_file(content, sftpclient):
    sftpclient.rename("/a/c", "/a/x")
    assert set(sftpclient.listdir("/a")) == set(["b", "f", "x"])


def test_sftpserver_rename_file_fail_source(content, sftpclient):
    with pytest.raises(IOError):
        sftpclient.rename("/a/NOTHERE", "/a/x")


def test_sftpserver_rename_file_fail_target(content, sftpclient):
    with pytest.raises(IOError):
        sftpclient.rename("/a/c", "/a/NOTHERE/x")


def test_sftpserver_rmdir(content, sftpclient):
    sftpclient.rmdir("/a")
    assert set(sftpclient.listdir("/")) == set(["d"])


def test_sftpserver_mkdir(content, sftpclient):
    sftpclient.mkdir("/a/x")
    assert set(sftpclient.listdir("/a")) == set(["b", "c", "f", "x"])


def test_sftpserver_mkdir_existing(content, sftpclient):
    with pytest.raises(IOError):
        sftpclient.mkdir("/a")
    assert set(sftpclient.listdir("/a")) == set(["b", "c", "f"])


def test_sftpserver_chmod(content, sftpclient):
    # coverage
    sftpclient.chmod("/a/b", 1)
    with sftpclient.open("/a/b", "r") as f:
        f.chmod(1)


def test_sftpserver_stat_non_str(sftpserver, sftpclient):
    with sftpserver.serve_content(dict(a=123)):
        assert sftpclient.stat("/a").st_size == 3


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
