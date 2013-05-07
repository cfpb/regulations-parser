import json
from lxml import etree
from parser.rule.parse import find_section_by_section, fetch_document_number
from parser.rule.parse import build_section_by_section
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: python generate_rule path/to/rule.xml"
        print " e.g.: python generate_rule 28.xml"
        exit()
    rule = etree.parse(sys.argv[1])

    sxs = find_section_by_section(rule)
    sxs = build_section_by_section(sxs)
    print json.dumps({
        'document_number': fetch_document_number(rule),
        'section_by_section': sxs
        })
