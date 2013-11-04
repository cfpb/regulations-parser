import codecs
import sys

from regparser import api_writer
from regparser.diff import api_reader, treediff
from regparser.federalregister import fetch_notices
from regparser.layer import external_citations, internal_citations, graphics
from regparser.layer import table_of_contents, interpretations, terms
from regparser.layer import section_by_section, paragraph_markers, meta
from regparser.notice.history import applicable as applicable_notices
from regparser.notice.history import modify_effective_dates
from regparser.tree.build import build_whole_regtree

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python build_from.py regulation.txt title "
              + "notice_doc_# act_title act_section (Generate diffs? "
              + "True/False)")
        print("  e.g. python build_from.py rege.txt 12 2011-31725 15 1693 "
              + "False")
        exit()

    writer = api_writer.Client()

    with codecs.open(sys.argv[1], encoding='utf-8') as f:
        reg = unicode(f.read())

    #   First, the regulation tree
    reg_tree = build_whole_regtree(reg)
    cfr_part = reg_tree.label_id()
    cfr_title = sys.argv[2]
    doc_number = sys.argv[3]
    #   Hold off on writing the regulation until after we know we have a valid
    #   doc number

    #   Next, notices
    notices = fetch_notices(cfr_title, cfr_part)
    modify_effective_dates(notices)
    notices = applicable_notices(notices, doc_number)
    #  Didn't include the provided version
    if not notices:
        print "Could not find notice_doc_#, %s" % doc_number
        exit()
    for notice in notices:
        #  No need to carry this around
        del notice['meta']
        writer.notice(notice['document_number']).write(notice)

    writer.regulation(cfr_part, doc_number).write(reg_tree)

    #   Finally, all the layers
    layer = external_citations.ExternalCitationParser(
        reg_tree, sys.argv[4:]).build()
    writer.layer("external-citations", cfr_part, doc_number).write(layer)

    layer = meta.Meta(reg_tree, int(cfr_title), notices, doc_number).build()
    writer.layer("meta", cfr_part, doc_number).write(layer)

    layer = section_by_section.SectionBySection(reg_tree, notices).build()
    writer.layer("analyses", cfr_part, doc_number).write(layer)

    for ident, layer_class in (
            ('internal-citations', internal_citations.InternalCitationParser),
            ('toc', table_of_contents.TableOfContentsLayer),
            ('interpretations', interpretations.Interpretations),
            ('terms', terms.Terms),
            ('paragraph-markers', paragraph_markers.ParagraphMarkers),
            ('graphics', graphics.Graphics)):
        layer = layer_class(reg_tree).build()
        writer.layer(ident, cfr_part, doc_number).write(layer)

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
