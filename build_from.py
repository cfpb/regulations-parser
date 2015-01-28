import codecs
import logging
import sys
import argparse

try:
    import requests_cache
    requests_cache.install_cache('fr_cache')
except ImportError:
    # If the cache library isn't present, do nothing -- we'll just make full
    # HTTP requests rather than looking it up from the cache
    pass

from regparser.diff import treediff
from regparser.builder import Builder, LayerCacheAggregator


logger = logging.getLogger('build_from')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Regulation parser')
    parser.add_argument('filename',
                        help='XML file containing the regulation')
    parser.add_argument('title', type=int, help='Title number')
    parser.add_argument('notice', type=str, help='Notice document number')
    parser.add_argument('act_title', type=int, help='Act title', action='store')
    parser.add_argument('act_section', type=int, help='Act section')
    parser.add_argument('--generate-diffs', type=bool, help='Generate diffs?', required=False, default=True)

    args = parser.parse_args()
    
    with codecs.open(args.filename, 'r', 'utf-8') as f:
        reg = f.read()

    doc_number = args.notice
    act_title_and_section = [args.act_title, args.act_section]
    
    #   First, the regulation tree
    reg_tree = Builder.reg_tree(reg)

    builder = Builder(cfr_title=args.title,
                      cfr_part=reg_tree.label_id(),
                      doc_number=doc_number)

    builder.write_notices()
    
    #   Always do at least the first reg
    logger.info("Version %s", doc_number)
    builder.write_regulation(reg_tree)
    layer_cache = LayerCacheAggregator()
    builder.gen_and_write_layers(reg_tree, act_title_and_section, layer_cache)
    layer_cache.replace_using(reg_tree)

    
    # this used to assume implicitly that if gen-diffs was not specified it was
    # True; changed it to explicit check
    if args.generate_diffs:
        all_versions = {doc_number: reg_tree}

        for last_notice, old, new_tree, notices in builder.revision_generator(
                reg_tree):
            version = last_notice['document_number']
            logger.info("Version %s", version)
            all_versions[version] = new_tree
            builder.doc_number = version
            builder.write_regulation(new_tree)
            layer_cache.invalidate_by_notice(last_notice)
            builder.gen_and_write_layers(new_tree, act_title_and_section,
                                         layer_cache, notices)
            layer_cache.replace_using(new_tree)

        # now build diffs - include "empty" diffs comparing a version to itself
        for lhs_version, lhs_tree in all_versions.iteritems():
            for rhs_version, rhs_tree in all_versions.iteritems():
                comparer = treediff.Compare(lhs_tree, rhs_tree)
                comparer.compare()
                builder.writer.diff(
                    reg_tree.label_id(), lhs_version, rhs_version
                ).write(comparer.changes)
