import codecs
from parser.api_writer import Client
from parser.layer import external_citations, internal_citations
from parser.layer import table_of_contents, interpretations, terms
from parser.tree.build import build_whole_regtree
import sys

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: python build_from.py regulation.txt date"
        print "  e.g. python build_from.py rege.txt 20090125"
        exit()

    writer = Client()

    with codecs.open(sys.argv[1], encoding='utf-8') as f:
        reg = unicode(f.read())

    reg_tree = build_whole_regtree(reg)
    cfr_part = reg_tree['label']['text']
    date = sys.argv[2]
    writer.regulation(cfr_part, date).write(reg_tree)

    layer = external_citations.ExternalCitationParser(reg_tree).build()
    writer.layer("external-citations", cfr_part, date).write(layer)

    layer = internal_citations.InternalCitationParser(reg_tree).build()
    writer.layer("internal-citations", cfr_part, date).write(layer)

    layer = table_of_contents.TableOfContentsLayer(reg_tree).build()
    writer.layer("toc", cfr_part, date).write(layer)

    layer = interpretations.Interpretations(reg_tree).build()
    writer.layer("interpretations", cfr_part, date).write(layer)

    layer = terms.Terms(reg_tree).build()
    writer.layer("terms", cfr_part, date).write(layer)
