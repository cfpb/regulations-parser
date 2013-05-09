import json
import os
import os.path
import settings

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
            text = json.dumps(python_obj, sort_keys=True, indent=4,
                    separators=(', ', ': '))
            out.write(text)


class Client:
    """A Client for writing regulation(s) and meta data."""

    def __init__(self):
        self.writer_class = FSWriteContent

    def regulation(self, label, date):
        return self.writer_class("regulation/%s/%s" % (label, date))

    def layer(self, layer_name, label, date):
        return self.writer_class("layer/%s/%s/%s" % (layer_name, label, date))

    def notice(self, doc_number):
        return self.writer_class("notice/%s" % doc_number)
