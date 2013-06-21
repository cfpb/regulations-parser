import codecs
from parser.api_writer import Client
from parser.federalregister import fetch_notices
from parser.layer import external_citations, internal_citations, graphics
from parser.layer import table_of_contents, interpretations, terms
from parser.layer import section_by_section, paragraph_markers, meta
from parser.tree.build import build_whole_regtree
import sys

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python build_from.py regulation.txt title " +
                "doc_#/version act_title act_section")
        print "  e.g. python build_from.py rege.txt 12 2011-31725 15 1693"
        exit()

    writer = Client()

    with codecs.open(sys.argv[1], encoding='utf-8') as f:
        reg = unicode(f.read())

    #   First, the regulation tree
    reg_tree = build_whole_regtree(reg)
    cfr_part = reg_tree['label']['text']
    cfr_title = sys.argv[2]
    doc_number = sys.argv[3]
    writer.regulation(cfr_part, doc_number).write(reg_tree)

    #   Next, notices
    notices = fetch_notices(cfr_title, cfr_part)
    #   @todo: limit to the notices which came before doc_number
    for notice in notices:
        writer.notice(notice['document_number']).write(notice)

    #   Finally, all the layers
    layer = external_citations.ExternalCitationParser(reg_tree, 
        sys.argv[4:]).build()
    writer.layer("external-citations", cfr_part, doc_number).write(layer)

    layer = internal_citations.InternalCitationParser(reg_tree).build()
    writer.layer("internal-citations", cfr_part, doc_number).write(layer)

    layer = table_of_contents.TableOfContentsLayer(reg_tree).build()
    writer.layer("toc", cfr_part, doc_number).write(layer)

    layer = interpretations.Interpretations(reg_tree).build()
    writer.layer("interpretations", cfr_part, doc_number).write(layer)

    layer = terms.Terms(reg_tree).build()
    writer.layer("terms", cfr_part, doc_number).write(layer)

    layer = paragraph_markers.ParagraphMarkers(reg_tree).build()
    writer.layer("paragraph-markers", cfr_part, doc_number).write(layer)

    layer = section_by_section.SectionBySection(reg_tree, notices).build()
    writer.layer("analyses", cfr_part, doc_number).write(layer)

    layer = meta.Meta(reg_tree, int(cfr_title), notices).build()
    writer.layer("meta", cfr_part, doc_number).write(layer)

    layer = graphics.Graphics(reg_tree).build()
    writer.layer("graphics", cfr_part, doc_number).write(layer)
