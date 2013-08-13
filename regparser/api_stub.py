import codecs
import json

from regparser.tree.struct import node_decode_hook


def get_regulation_as_json(regulations_json_file):
    f = codecs.open(regulations_json_file, encoding='utf-8')
    return json.load(f, object_hook=node_decode_hook)
