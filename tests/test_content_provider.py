from copy import deepcopy
import pytest
from pytest_sftpserver.sftp.content_provider import ContentProvider


class _TestObj(object):
    def __init__(self):
        self.x = "testfile7"

_CONTENT_OBJ = dict(
    a=dict(
        b="testfile1",
        c="testfile2",
        f=["testfile5", "testfile6"]
    ),
    d="testfile3",
    o=_TestObj(),
)


@pytest.fixture
def content_provider():
    return ContentProvider(deepcopy(_CONTENT_OBJ))


def test_get_dict(content_provider):
    assert content_provider.get("/a/b") == "testfile1"


def test_get_list(content_provider):
    assert content_provider.get("/a/f/0") == "testfile5"


def test_get_obj(content_provider):
    assert content_provider.get("/o/x") == "testfile7"


def test_get_callable(content_provider):
    assert content_provider.get("/d/title") == "Testfile3"


def test_put_dict(content_provider):
    assert content_provider.put("/a/e", "testfile4")
    assert set(content_provider.list("/a")) == set(["b", "c", "e", "f"])
    assert content_provider.get("/a/e") == "testfile4"


def test_put_list(content_provider):
    assert content_provider.put("/a/f/2", "testfile4")
    assert set(content_provider.list("/a/f")) == set(["0", "1", "2"])
    assert content_provider.get("/a/f/2") == "testfile4"


def test_put_obj(content_provider):
    assert content_provider.put("/o/y", "testfile8")
    assert set(content_provider.list("/o")) == set(["x", "y"])
    assert content_provider.get("/o/y") == "testfile8"


def test_put_fail(content_provider):
    assert not content_provider.put("/0/__class__", "test")


def test_remove_dict(content_provider):
    assert content_provider.remove("/a/c")
    assert set(content_provider.list("/a")) == set(["b", "f"])


def test_remove_dict_fail(content_provider):
    assert not content_provider.remove("/a/NOTHERE")


def test_remove_list(content_provider):
    assert content_provider.remove("/a/f/0")
    assert set(content_provider.list("/a/f")) == set(["0"])


def test_remove_obj(content_provider):
    assert content_provider.remove("/o/x")
    assert set(content_provider.list("/o")) == set()


def test_remove_obj_fail(content_provider):
    assert not content_provider.remove("/o/NOTHERE")


def test_list_root(content_provider):
    assert set(content_provider.list("/")) == set(["a", "d", "o"])


def test_list_sub(content_provider):
    assert set(content_provider.list("/a")) == set(["b", "c", "f"])
    assert set(content_provider.list("/a/f")) == set(["0", "1"])


def test_is_dir(content_provider):
    assert content_provider.is_dir("/")
    assert content_provider.is_dir("/a")
    assert content_provider.is_dir("/a/f")
    assert content_provider.is_dir("/o")
    assert not content_provider.is_dir("/d")


def test_get_size(content_provider):
    assert content_provider.get_size("/d") == 9


def test_str_and_byte(content_provider):
    assert set(content_provider.list(b"/")) == set(content_provider.list("/"))

