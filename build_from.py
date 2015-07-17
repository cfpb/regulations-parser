#!/usr/bin/env python

import argparse
import logging

try:
    import requests_cache
    requests_cache.install_cache('fr_cache')
except ImportError:
    # If the cache library isn't present, do nothing -- we'll just make full
    # HTTP requests rather than looking it up from the cache
    pass

from regparser.builder import LayerCacheAggregator, tree_and_builder
from regparser.diff.tree import changes_between
from regparser.tree.struct import FrozenNode

logger = logging.getLogger('build_from')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


# @profile
def parse_regulation(args):
    """ Run the parser on the specified command-line arguments. Broken out
        into separate function to assist in profiling.
    """
    act_title_and_section = [args.act_title, args.act_section]
    #   First, the regulation tree
    reg_tree, builder = tree_and_builder(args.filename, args.title,
                                         args.checkpoint_dir, args.doc_number)
    builder.write_notices()

    #   Always do at least the first reg
    logger.info("Version %s", builder.doc_number)
    builder.write_regulation(reg_tree)
    layer_cache = LayerCacheAggregator()

    builder.gen_and_write_layers(reg_tree, act_title_and_section, layer_cache)
    layer_cache.replace_using(reg_tree)

    if args.generate_diffs:
        generate_diffs(reg_tree, act_title_and_section, builder, layer_cache)


def generate_diffs(reg_tree, act_title_and_section, builder, layer_cache):
    """ Generate all the diffs for the given regulation. Broken out into
        separate function to assist with profiling so it's easier to determine
        which parts of the parser take the most time """
    doc_number, checkpointer = builder.doc_number, builder.checkpointer
    all_versions = {doc_number: FrozenNode.from_node(reg_tree)}

    for last_notice, old, new_tree, notices in builder.revision_generator(
            reg_tree):
        version = last_notice['document_number']
        logger.info("Version %s", version)
        all_versions[version] = FrozenNode.from_node(new_tree)
        builder.doc_number = version
        builder.write_regulation(new_tree)
        layer_cache.invalidate_by_notice(last_notice)
        builder.gen_and_write_layers(new_tree, act_title_and_section,
                                     layer_cache, notices)
        layer_cache.replace_using(new_tree)
        del last_notice, old, new_tree, notices     # free some memory

    label_id = reg_tree.label_id()
    writer = builder.writer
    del reg_tree, layer_cache, builder  # free some memory

    # now build diffs - include "empty" diffs comparing a version to itself
    for lhs_version, lhs_tree in all_versions.iteritems():
        for rhs_version, rhs_tree in all_versions.iteritems():
            changes = checkpointer.checkpoint(
                "-".join(["diff", lhs_version, rhs_version]),
                lambda: dict(changes_between(lhs_tree, rhs_tree)))
            writer.diff(
                label_id, lhs_version, rhs_version
            ).write(changes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Regulation parser')
    parser.add_argument('filename',
                        help='XML file containing the regulation')
    parser.add_argument('title', type=int, help='Title number')
    parser.add_argument('act_title', type=int, help='Act title',
                        action='store')
    parser.add_argument('act_section', type=int, help='Act section')
    diffs = parser.add_mutually_exclusive_group(required=False)
    diffs.add_argument('--generate-diffs', dest='generate_diffs',
                       action='store_true', help='Generate diffs')
    diffs.add_argument('--no-generate-diffs', dest='generate_diffs',
                       action='store_false', help="Don't generate diffs")
    diffs.set_defaults(generate_diffs=True)
    parser.add_argument('--checkpoint', dest='checkpoint_dir', required=False,
                        help='Directory to save checkpoint data')
    parser.add_argument(
        '--version-identifier', dest='doc_number', required=False,
        help=('Do not try to derive the version information. (Only use if '
              "your regulation is older than federalregister.gov's records)"))

    args = parser.parse_args()
    parse_regulation(args)
