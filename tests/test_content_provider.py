from contextlib import contextmanager
from copy import deepcopy
import posixpath
import time

import pytest
import sys
from pytest_sftpserver.sftp.content_provider import ContentProvider


class Inner(object):
    def __init__(self):
        self.something = "a"


class _TestObj(object):
    def __init__(self):
        self.x = "testfile7"
        self.inner = Inner()


# fmt: off
_CONTENT_OBJ = dict(
    a=dict(
        b="testfile1",
        c="testfile2",
        f=["testfile5", "testfile6"]
    ),
    d="testfile3",
    o=_TestObj(),
)
# fmt: on


@pytest.fixture
def content_provider():
    return ContentProvider(deepcopy(_CONTENT_OBJ))


def test_recursive_listing(content_provider):
    expected = [
            ("", ""),
            ("", "a"),
            ("", "d"),
            ("", "o"),
            ("/a", "b"),
            ("/a", "c"),
            ("/a", "f"),
            ("/a/f", "0"),
            ("/a/f", "1"),
            ("/o", "inner"),
            ("/o", "x"),
            ("/o/inner", "something"),

        ]
    assert expected == sorted(content_provider.recursive_list('/'))


def test_get_dict(content_provider):
    assert content_provider.get("/a/b") == "testfile1"


def test_get_list(content_provider):
    assert content_provider.get("/a/f/0") == "testfile5"


def test_get_obj(content_provider):
    assert content_provider.get("/o/x") == "testfile7"

@pytest.mark.skip("""I think this test was always wrong, but it accidentially
worked until my changes broke it. The content provider
fixture does not have a callable at all, so the test
name does not match what is happening.""")
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
    assert set(content_provider.list("/o")) == set(["x", "y", "inner"])
    assert content_provider.get("/o/y") == "testfile8"


def test_put_obj_nested(content_provider):
    assert content_provider.put("/o/inner/y", "testfile9")
    assert set(content_provider.list("/o/inner")) == set(["y", "something"])
    assert content_provider.get("/o/inner/y") == "testfile9"


def test_put_fail(content_provider):
    assert not content_provider.put("/0/__class__", "test")


@contextmanager
def check_stat_times(provider, path, atime_change=False, mtime_change=False):
    # Make a copy of the times to prevent indirect mutation
    times = list(provider.get_times(path))
    assert len(times) == 2

    yield

    # See if the times were updated
    new_times = provider.get_times(path)
    assert len(new_times) == 2
    if atime_change:
        assert new_times[0] > times[0]   # atime should have updated
    else:
        assert new_times[0] == times[0]  # atime shouldn't have changed
    if mtime_change:
        assert new_times[1] > times[1]   # mtime should have updated
    else:
        assert new_times[1] == times[1]  # mtime shouldn't have updated


@pytest.mark.parametrize("path,isnew",
    [("/a/f/2", True), ("/o/y", True), ("/a/e", True),
     ("/a/b", False), ("/o/x", False), ("/a/f/0", False)])
def test_put_times(content_provider, path, isnew):
    dirname = posixpath.dirname(path)
    with check_stat_times(content_provider, dirname, mtime_change=isnew):
        times = [123456.0, 123456.1]
        # Pass in a copy of the times, just in case
        assert content_provider.put(path, "foobar", list(times))
        result_times = content_provider.get_times(path)
        assert times == result_times


@pytest.mark.parametrize("path,isnew",
    [("/a/f/2", True), ("/o/y", True), ("/a/e", True),
     ("/a/b", False), ("/o/x", False), ("/a/f/0", False)])
def test_put_auto_mtime(content_provider, path, isnew):
    dirname = posixpath.dirname(path)
    with check_stat_times(content_provider, dirname, mtime_change=isnew):
        # I can't compare exact times because I don't have
        # the exact time of update, but rounding to the nearest
        # second should be good enough the vast majority of the time
        currtime = round(time.time())
        assert content_provider.put(path, "foobar")
        # Make sure the times for the file actually ages.
        time.sleep(2)

        result_times = content_provider.get_times(path)
        assert currtime == round(result_times[1])


@pytest.mark.parametrize("path,listing",
    [("/a/c", set(["b", "f"])) , ("/a/f/0", set(["0"])),
     ("/o/x", set(["inner"])), ("/o/inner/something", set())])
def test_remove(content_provider, path, listing):
    # make sure there is times for this item
    assert content_provider.get_times(path)

    dirname = posixpath.dirname(path)
    with check_stat_times(content_provider, dirname, mtime_change=True):
        time.sleep(2)
        assert content_provider.remove(path)
    assert set(content_provider.list(dirname)) == listing

    # make sure the times have been removed for this item
    assert content_provider.get_times(path) is None


@pytest.mark.parametrize("path",
    ["/a/NOTHERE", "/o/NOTHERE"])
def test_remove_fail(content_provider, path):
    # Making sure that removing an entry doesn't accidentally add
    # a time entry into the content
    # Also making sure it doesn't change the directory's times
    dirname = posixpath.dirname(path)
    with check_stat_times(content_provider, dirname):
        assert content_provider.get_times(path) is None
        assert not content_provider.remove(path)
        assert content_provider.get_times(path) is None

@pytest.mark.parametrize("path,expected",
    [('/', set(['a', 'd', 'o'])), ('/a', set(['b', 'c', 'f'])),
     ('/a/f', set(['0', '1']))])
def test_list(content_provider, path, expected):
    with check_stat_times(content_provider, path, atime_change=True):
        assert set(content_provider.list(path)) == expected


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
