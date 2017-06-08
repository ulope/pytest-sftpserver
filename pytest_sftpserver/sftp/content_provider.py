# encoding: utf-8
from __future__ import absolute_import, division, print_function

from collections import defaultdict
import posixpath
import time

from six import string_types, binary_type, integer_types


class ContentProvider(object):
    def __init__(self, content_object=None):
        self.content_object = content_object
        # values: [atime, mtime]
        # (alphabetical order for easier remembering)
        self._st_times = defaultdict(lambda : [time.time()] * 2)
        the_time = time.time()
        # This assumes that we start at '/'. Not sure that is
        # a valid assumtion.
        for path, name in self.recursive_list('/'):
            self._st_times[(path, name)] = [the_time] * 2

    def get(self, path):
        obj = self._find_object_for_path(path)
        if obj is not None:
            path, name = self._get_path_components(path)
            # update atime, but not mtime
            self._update_times(path, name, [time.time(), None])
        return obj

    def _update_times(self, path, name, times):
        if len(times) != 2:
            raise ValueError("'times' argument must be a length-2 list. Got %r"
                             % (times,))
        st_times = self._st_times[(path, name)]
        # Mutate the list in-place
        if times[0] is not None:
            st_times[0] = times[0]
        if times[1] is not None:
            st_times[1] = times[1]

    def put(self, path, data, times=None):
        if times is None:
            # So don't override atime or mtime...
            times = [None, None]
        # Cast it as a list
        times = list(times)

        path, name = self._get_path_components(path)
        obj = self._find_object_for_path(path)

        if times[1] is None:
            # ... but do update mtime
            times[1] = time.time()

        if isinstance(obj, dict):
            obj[name] = data
            self._update_times(path, name, times)
            return True
        elif isinstance(obj, list) and name.isdigit():
            # Need to be done *before* casting to integer
            # because code elsewhere won't cast to int
            # before fetching from the dictionary.

            self._update_times(path, name, times)
            name = int(name)
            if name > len(obj) - 1:
                obj.append(data)
            obj[name] = data
            return True
        try:
            setattr(obj, name, data)
        except (TypeError, AttributeError):
            return False
        else:
            self._update_times(path, name, times)
            return True

    def remove(self, path):
        path, name = self._get_path_components(path)
        dirpath, dirname = self._get_path_components(path)
        obj = self._find_object_for_path(path)
        if isinstance(obj, dict):
            try:
                del obj[name]
            except (KeyError, AttributeError):
                return False
            else:
                self._st_times.pop((path, name), None)
                self._update_times(dirpath, dirname, [None, time.time()])
                return True
        elif isinstance(obj, list) and name.isdigit():
            # Need to be done *before* casting to integer
            # because code elsewhere won't cast to int
            # before fetching from the dictionary.
            self._st_times.pop((path, name), None)
            self._update_times(dirpath, dirname, [None, time.time()])
            name = int(name)
            if name < len(obj):
                del obj[name]
                return True
            else:
                return False
        else:
            try:
                delattr(obj, name)
            except (TypeError, AttributeError):
                return False
            else:
                self._st_times.pop((path, name), None)
                self._update_times(dirpath, dirname, [None, time.time()])
                return True

    def list(self, path):
        obj = self._find_object_for_path(path)
        if isinstance(obj, dict):
            return obj.keys()
        elif isinstance(obj, (list, tuple)):
            return [str(i) for i in range(len(obj))]
        else:
            return [n for n in dir(obj) if not n.startswith("__")]

    def recursive_list(self, path):
        subpath, subname = self._get_path_components(path)
        yield subpath if subpath != '/' else '', subname
        if self.is_dir(path):
            for name in self.list(path):
                fullname = posixpath.join(path, name)
                for subpath, subname in self.recursive_list(fullname):
                    yield subpath, subname

    def is_dir(self, path):
        # Using _find_object_for_path to avoid attribute-setting
        # that .get() does.
        return not isinstance(self._find_object_for_path(path),
                              string_types + integer_types)

    def get_size(self, path):
        try:
            return len(self.get(path))
        except TypeError:
            return len(str(self.get(path)))

    def get_times(self, path):
        return self._st_times.get(self._get_path_components(path), None)

    def _find_object_for_path(self, path):
        if not self.content_object:
            return None

        if isinstance(path, binary_type):
            separator = b"/"
        else:
            separator = "/"

        obj = self.content_object
        for part in path.split(separator):
            if part:
                try:
                    new_obj = getattr(obj, part)
                except (AttributeError, TypeError):
                    try:
                        new_obj = obj[part]
                    except (KeyError, TypeError, IndexError):
                        if part.isdigit():
                            try:
                                new_obj = obj[int(part)]
                            except (KeyError, TypeError, IndexError):
                                return None
                        else:
                            return None
                obj = new_obj
                if callable(obj):
                    obj = obj()
        return obj

    def _get_path_components(self, path):
        if isinstance(path, binary_type):
            separator = b"/"
        else:
            separator = "/"
        path, _, name = path.rpartition(separator)
        return path, name
