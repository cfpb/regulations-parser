# @todo - this should be combined with build_from.py
import argparse


try:
    import requests_cache
    requests_cache.install_cache('fr_cache')
except ImportError:
    # If the cache library isn't present, do nothing -- we'll just make full
    # HTTP requests rather than looking it up from the cache
    pass

from regparser.builder import tree_and_builder
from regparser.notice.changes import node_to_dict, pretty_change
from regparser.tree.struct import find


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Node Watcher")
    parser.add_argument(
        'node_label',
        help='Label for the node you wish to watch. e.g. 1026-5-a')
    parser.add_argument('filename',
                        help='XML file containing the regulation')
    parser.add_argument('title', type=int, help='Title number')
    args = parser.parse_args()

    initial_tree, builder = tree_and_builder(args.filename, args.title)
    initial_node = find(initial_tree, args.node_label)
    if initial_node:
        print("> " + builder.doc_number)
        print("\t" + pretty_change(
            {'action': 'POST', 'node': node_to_dict(initial_node)}))

    # search for label
    for version, changes in builder.changes_in_sequence():
        if args.node_label in changes:
            print("> " + version)
            for change in changes[args.node_label]:
                print("\t" + pretty_change(change))
