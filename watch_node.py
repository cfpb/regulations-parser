# @todo - this should be combined with build_from.py
import argparse
import codecs

try:
    import requests_cache
    requests_cache.install_cache('fr_cache')
except ImportError:
    # If the cache library isn't present, do nothing -- we'll just make full
    # HTTP requests rather than looking it up from the cache
    pass

from regparser.builder import Builder
from regparser.notice.changes import node_to_dict, pretty_change
from regparser.tree.struct import find


def init_reg_and_builder(args):
    """This function repeats a lot of what's done in build_from.py -- parse
    the provided regulation file into a tree and create a Builder object"""
    reg_text = ''
    with codecs.open(args.filename, 'r', 'utf-8') as f:
        reg_text = f.read()
    initial_tree = Builder.reg_tree(reg_text)
    title_part = initial_tree.label_id()
    doc_number = Builder.determine_doc_number(
        reg_text, args.title, title_part)
    if not doc_number:
        raise ValueError("Could not determine document number")
    builder = Builder(cfr_title=args.title,
                      cfr_part=title_part,
                      doc_number=doc_number)
    return initial_tree, builder


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Node Watcher")
    parser.add_argument(
        'node_label',
        help='Label for the node you wish to watch. e.g. 1026-5-a')
    parser.add_argument('filename',
                        help='XML file containing the regulation')
    parser.add_argument('title', type=int, help='Title number')
    args = parser.parse_args()

    initial_tree, builder = init_reg_and_builder(args)
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
