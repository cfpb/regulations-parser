#!/usr/bin/env python

import argparse
import logging
import hashlib
import codecs

import sys
reload(sys)
sys.setdefaultencoding('UTF8')

try:
    import requests_cache
    requests_cache.install_cache('fr_cache')
except ImportError:
    # If the cache library isn't present, do nothing -- we'll just make full
    # HTTP requests rather than looking it up from the cache
    pass

from regparser.builder import (
    LayerCacheAggregator, tree_and_builder, Checkpointer, NullCheckpointer,
    Builder)
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
    logger.info("Version", builder.doc_number)
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


def build_by_notice(filename, title, act_title, act_section,
                    notice_doc_numbers, doc_number=None, checkpoint=None):

    with codecs.open(filename, 'r', 'utf-8') as f:
        reg = f.read()
        file_digest = hashlib.sha256(reg.encode('utf-8')).hexdigest()

    if checkpoint:
        checkpointer = Checkpointer(checkpoint)
    else:
        checkpointer = NullCheckpointer()

    # build the initial tree
    reg_tree = checkpointer.checkpoint(
        "init-tree-" + file_digest,
        lambda: Builder.reg_tree(reg))

    title_part = reg_tree.label_id()

    if doc_number is None:
        doc_number = Builder.determine_doc_number(reg, title, title_part)

    checkpointer.suffix = ":".join(
        ["", title_part, str(args.title), doc_number])

    # create the builder
    builder = Builder(cfr_title=title,
                      cfr_part=title_part,
                      doc_number=doc_number,
                      checkpointer=checkpointer)

    builder.fetch_notices_json()

    for notice in notice_doc_numbers:
        builder.build_notice_from_doc_number(notice)

    builder.write_regulation(reg_tree)
    layer_cache = LayerCacheAggregator()

    act_title_and_section = [act_title, act_section]

    builder.gen_and_write_layers(reg_tree, act_title_and_section, layer_cache)
    layer_cache.replace_using(reg_tree)

    if args.generate_diffs:
        generate_diffs(reg_tree, act_title_and_section, builder, layer_cache)


def generate_xml(filename, title, act_title, act_section, notice_doc_numbers,
                 doc_number=None, checkpoint=None):

    act_title_and_section = [act_title, act_section]
    #   First, the regulation tree

    reg_tree, builder = tree_and_builder(filename, title,
                                         checkpoint, writer_type='XML')
    layer_cache = LayerCacheAggregator()
    layers = builder.generate_layers(reg_tree, act_title_and_section,
                                     layer_cache)

    # Always do at least the first reg
    logger.info("Version", builder.doc_number)
    builder.write_regulation(reg_tree, layers=layers)
    all_versions = {doc_number: FrozenNode.from_node(reg_tree)}

    for last_notice, old, new_tree, notices in builder.revision_generator(
            reg_tree):
        version = last_notice['document_number']
        logger.info("Version %s", version)
        all_versions[version] = FrozenNode.from_node(new_tree)
        builder.doc_number = version
        layers = builder.generate_layers(new_tree, act_title_and_section,
                                         layer_cache, notices)
        builder.write_regulation(new_tree, layers=layers)
        builder.write_notice(version, old_tree=old, reg_tree=new_tree,
                             layers=layers)
        layer_cache.invalidate_by_notice(last_notice)
        layer_cache.replace_using(new_tree)
        del last_notice, old, new_tree, notices     # free some memory


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
              'the regulation has no electronic final rules on '
              'federalregister.gov, i.e. has not changed since before ~2000)'))

    parser.add_argument('--last-notice', type=str,
                        help='the last notice to be used')
    parser.add_argument('--operation', action='store')
    parser.add_argument('--notices-to-apply', nargs='*', action='store')

    args = parser.parse_args()

    if args.operation == 'build_by_notice':
        build_by_notice(args.filename, args.title, args.act_title,
                        args.act_section, args.notices_to_apply,
                        args.last_notice, args.checkpoint_dir)

    elif args.operation == 'generate_xml':

        generate_xml(args.filename, args.title, args.act_title,
                     args.act_section, args.notices_to_apply,
                     args.last_notice, args.checkpoint_dir)

    else:
        parse_regulation(args)
