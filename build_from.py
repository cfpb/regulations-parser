import codecs
import logging
import sys


try:
    import requests_cache
    requests_cache.install_cache('fr_cache')
except ImportError:
    # If the cache library isn't present, do nothing -- we'll just make full
    # HTTP requests rather than looking it up from the cache
    pass

from regparser.builder import Builder, LayerCacheAggregator
from regparser.diff.treediff import changes_between
from regparser.tree.struct import FrozenNode


logger = logging.getLogger('build_from')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python build_from.py regulation.xml title "
              + "notice_doc_# act_title act_section (Generate diffs? "
              + "True/False)")
        print("  e.g. python build_from.py rege.txt 12 15 1693 "
              + "False")
        exit()

    with codecs.open(sys.argv[1], 'r', 'utf-8') as f:
        reg = f.read()

    #   First, the regulation tree
    reg_tree = Builder.reg_tree(reg)

    title = int(sys.argv[2])
    title_part = reg_tree.label_id()

    doc_number = Builder.determine_doc_number(reg, title, title_part)
    if not doc_number:
        raise ValueError("Could not determine document number")

    #   Run Builder
    builder = Builder(cfr_title=title,
                      cfr_part=title_part,
                      doc_number=doc_number)

    #  Didn't include the provided version
    if not any(n['document_number'] == doc_number for n in builder.notices):
        print("Could not find notice_doc_#, %s" % doc_number)
        exit()

    builder.write_notices()

    #   Always do at least the first reg
    logger.info("Version %s", doc_number)
    builder.write_regulation(reg_tree)
    layer_cache = LayerCacheAggregator()
    builder.gen_and_write_layers(reg_tree, sys.argv[3:5], layer_cache)
    layer_cache.replace_using(reg_tree)
    if len(sys.argv) < 6 or sys.argv[5].lower() == 'true':
        all_versions = {doc_number: reg_tree}
        for last_notice, old, new_tree, notices in builder.revision_generator(
                reg_tree):
            version = last_notice['document_number']
            logger.info("Version %s", version)
            all_versions[version] = new_tree
            builder.doc_number = version
            builder.write_regulation(new_tree)
            layer_cache.invalidate_by_notice(last_notice)
            builder.gen_and_write_layers(new_tree, sys.argv[3:5],
                                         layer_cache, notices)
            layer_cache.replace_using(new_tree)

        from time import time
        start_time = time()
        # convert to frozen trees
        for doc in all_versions:
            all_versions[doc] = FrozenNode.from_node(all_versions[doc])

        # now build diffs - include "empty" diffs comparing a version to itself
        for lhs_version, lhs_tree in all_versions.iteritems():
            for rhs_version, rhs_tree in all_versions.iteritems():
                changes = changes_between(lhs_tree, rhs_tree)
                builder.writer.diff(
                    reg_tree.label_id(), lhs_version, rhs_version
                ).write(dict(changes))
        print(time() - start_time)
