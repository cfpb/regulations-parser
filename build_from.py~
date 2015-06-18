#!/usr/bin/env python

import argparse
import codecs
import hashlib
import logging

try:
    import requests_cache
    requests_cache.install_cache('fr_cache')
except ImportError:
    # If the cache library isn't present, do nothing -- we'll just make full
    # HTTP requests rather than looking it up from the cache
    pass

from regparser.builder import (
    Builder, Checkpointer, LayerCacheAggregator, NullCheckpointer)
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
    with codecs.open(args.filename, 'r', 'utf-8') as f:
        reg = f.read()
        file_digest = hashlib.sha256(reg.encode('utf-8')).hexdigest()
    act_title_and_section = [args.act_title, args.act_section]

    if args.checkpoint:
        checkpointer = Checkpointer(args.checkpoint)
    else:
        checkpointer = NullCheckpointer()

    #   First, the regulation tree
    reg_tree = checkpointer.checkpoint(
        "init-tree-" + file_digest,
        lambda: Builder.reg_tree(reg))
    title_part = reg_tree.label_id()
    doc_number = checkpointer.checkpoint(
        "doc-number-" + file_digest,
        lambda: Builder.determine_doc_number(reg, args.title, title_part))
    if not doc_number:
        raise ValueError("Could not determine document number")
    checkpointer.suffix = ":".join(
        ["", title_part, str(args.title), doc_number])

    #   Run Builder
    builder = Builder(cfr_title=args.title,
                      cfr_part=title_part,
                      doc_number=doc_number,
                      checkpointer=checkpointer)
    builder.write_notices()

    #   Always do at least the first reg
    logger.info("Version %s", doc_number)
    builder.write_regulation(reg_tree)
    layer_cache = LayerCacheAggregator()

    builder.gen_and_write_layers(reg_tree, act_title_and_section, layer_cache)
    layer_cache.replace_using(reg_tree)

    if args.generate_diffs:
        generate_diffs(doc_number, reg_tree, act_title_and_section, builder,
                       layer_cache, checkpointer)


def generate_diffs(doc_number, reg_tree, act_title_and_section, builder,
                   layer_cache, checkpointer):
    """ Generate all the diffs for the given regulation. Broken out into
        separate function to assist with profiling so it's easier to determine
        which parts of the parser take the most time """
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
    parser.add_argument('--generate-diffs', type=bool, help='Generate diffs?',
                        required=False, default=True)
    parser.add_argument('--checkpoint', required=False,
                        help='Directory to save checkpoint data')

    args = parser.parse_args()
    parse_regulation(args)
