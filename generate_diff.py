import settings
import json

from regparser.diff import api_reader
from regparser.diff import treediff
from regparser.tree.struct import node_decode_hook

def json_to_node(json_node):
    return json.loads(json_node, object_hook=node_decode_hook)

def get_regulation(regulation, version):
    api = api_reader.Client(settings.API_BASE)
    reg = api.regulation(regulation, version)

    return reg

if __name__ == "__main__":
    old = get_regulation('1005', '2011-31725')
    new = get_regulation('1005', '2013-10604')

    old_tree = json_to_node(old.text)
    new_tree = json_to_node(new.text)

    #treediff.compare(old_tree, new_tree)
    comparer = treediff.Compare(old_tree, new_tree)
    comparer.compare()
    comparer.write()
