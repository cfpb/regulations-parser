from regparser.diff import api_reader
from regparser.diff import treediff
from regparser.tree.struct import node_decode_hook

if __name__ == "__main__":
    api = api_reader.Client()
    old_tree = api.regulation('1005', '2011-31725')
    new_tree = api.regulation('1005', '2013-10604')

    comparer = treediff.Compare(old_tree, new_tree)
    comparer.compare()
    print comparer.as_json()
