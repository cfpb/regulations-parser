import os
import os.path
import requests
import settings

from regparser.tree.struct import NodeEncoder


class FSWriteContent:
    """This writer places the contents in the file system """

    def __init__(self, path):
        self.path = path

    def write(self, python_obj):
        """Write the object as json to disk"""
        path_parts = self.path.split('/')
        dir_path = settings.OUTPUT_DIR + os.path.join(*path_parts[:-1])

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        full_path = settings.OUTPUT_DIR + os.path.join(*path_parts)
        with open(full_path, 'w') as out:
            text = NodeEncoder(
                sort_keys=True, indent=4,
                separators=(', ', ': ')).encode(python_obj)
            out.write(text)


class APIWriteContent:
    """This writer writes the contents to the specified API"""
    def __init__(self, path):
        self.path = path

    def write(self, python_obj):
        """Write the object (as json) to the API"""
        requests.put(
            settings.API_BASE + self.path,
            data=NodeEncoder().encode(python_obj),
            headers={'content-type': 'application/json'})


class Client:
    """A Client for writing regulation(s) and meta data."""

    def __init__(self):
        if settings.API_BASE:
            self.writer_class = APIWriteContent
        else:
            self.writer_class = FSWriteContent

    def regulation(self, label, doc_number):
        return self.writer_class("regulation/%s/%s" % (label, doc_number))

    def layer(self, layer_name, label, doc_number):
        return self.writer_class(
            "layer/%s/%s/%s" % (layer_name, label, doc_number))

    def notice(self, doc_number):
        return self.writer_class("notice/%s" % doc_number)

    def diff(self, label, old_version, new_version):
        return self.writer_class("diff/%s/%s/%s" % (label, old_version,
                                                    new_version))
