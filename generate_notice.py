import sys

from lxml import etree

from regparser.tree.struct import NodeEncoder
from regparser.notice import find_section_by_section, fetch_document_number
from regparser.notice import build_section_by_section, fetch_cfr_part

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: python generate_notice path/to/rule.xml"
        print " e.g.: python generate_notice 28.xml"
        exit()
    rule = etree.parse(sys.argv[1])

    part = fetch_cfr_part(rule)

    sxs = find_section_by_section(rule)
    sxs = build_section_by_section(sxs, part)
    print NodeEncoder().encode({
        'document_number': fetch_document_number(rule),
        'cfr_part': part,
        'section_by_section': sxs
        })
