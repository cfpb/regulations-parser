import codecs
import logging
import sys

#from regparser.diff import api_reader, treediff
from regparser.builder import Builder

logger = logging.getLogger('build_from')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python build_from.py regulation.xml title "
              + "notice_doc_# act_title act_section (Generate diffs? "
              + "True/False)")
        print("  e.g. python build_from.py rege.txt 12 2011-31725 15 1693 "
              + "False")
        exit()

    with codecs.open(sys.argv[1], 'r', 'utf-8') as f:
        reg = f.read()

    #   First, the regulation tree
    reg_tree = Builder.reg_tree(reg)

    builder = Builder(cfr_title=int(sys.argv[2]),
                      cfr_part=reg_tree.label_id(),
                      doc_number=sys.argv[3])

    #  Didn't include the provided version
    if not any(n['document_number'] == sys.argv[3] for n in builder.notices):
        print "Could not find notice_doc_#, %s" % doc_number
        exit()

    builder.write_notices()

    #   Always do at least the first reg
    logger.info("Version %s", sys.argv[3])
    builder.write_regulation(reg_tree)
    builder.gen_and_write_layers(reg_tree, sys.argv[4:6])
    if len(sys.argv) < 7 or sys.argv[6].lower() == 'true':
        for version, old, new_tree in builder.revision_generator(reg_tree):
            logger.info("Version %s", version)
            builder.doc_number = version
            builder.write_regulation(new_tree)
            builder.gen_and_write_layers(new_tree, sys.argv[4:6])

    """
    # Use the seventh value or default to True for building diffs
    if len(sys.argv) < 7 or sys.argv[6].lower() == 'true':
        new_version = doc_number

        reader = api_reader.Client()
        #   We perform diffs with all other versions -- not all make sense, but
        #   they can't hurt
        for old_version in (v['version']
                            for v in reader.regversions(cfr_part)['versions']
                            if v['version'] != new_version):
            old_tree = reader.regulation(cfr_part, old_version)
            comparer = treediff.Compare(old_tree, reg_tree)
            comparer.compare()
            writer.diff(cfr_part, old_version, new_version).write(
                comparer.changes)
    """
