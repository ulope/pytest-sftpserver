# encoding: utf-8
from __future__ import absolute_import, division, print_function

from six import binary_type, integer_types, string_types


class ContentProvider(object):
    def __init__(self, content_object=None):
        self.content_object = content_object

    def get(self, path):
        return self._find_object_for_path(path)

    def put(self, path, data):
        path, name = self._get_path_components(path)
        obj = self._find_object_for_path(path)
        if isinstance(obj, dict):
            obj[name] = data
            return True
        elif isinstance(obj, list) and name.isdigit():
            name = int(name)
            if name > len(obj) - 1:
                obj.append(data)
            obj[name] = data
            return True
        try:
            setattr(obj, name, data)
            return True
        except (TypeError, AttributeError):
            pass
        return False

    def remove(self, path):
        path, name = self._get_path_components(path)
        obj = self._find_object_for_path(path)
        if isinstance(obj, dict):
            try:
                del obj[name]
                return True
            except (KeyError, AttributeError):
                pass
        elif isinstance(obj, list) and name.isdigit():
            name = int(name)
            if name < len(obj):
                del obj[name]
                return True
            else:
                return False
        else:
            try:
                delattr(obj, name)
                return True
            except (TypeError, AttributeError):
                pass
        return False

    def list(self, path):
        obj = self._find_object_for_path(path)
        if isinstance(obj, dict):
            return obj.keys()
        elif isinstance(obj, (list, tuple)):
            return [str(i) for i in range(len(obj))]
        else:
            return [n for n in dir(obj) if not n.startswith("__")]

    def is_dir(self, path):
        return not isinstance(self.get(path), string_types + integer_types)

    def get_size(self, path):
        try:
            return len(self.get(path))
        except TypeError:
            return len(str(self.get(path)))

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
