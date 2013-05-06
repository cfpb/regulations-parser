from itertools import dropwhile, takewhile
from parser.grammar.rule_headers import applicable

def find_section_by_section(xml_tree):
    """Find the section-by-section analysis of this rule"""
    xml_children = xml_tree.xpath('//SUPLINF/*')
    sxs = dropwhile(lambda el: (
        el.tag != 'HD'
        or el.get('SOURCE') != 'HD1' 
        or 'section-by-section' not in el.text.lower()), xml_children)
    sxs = list(sxs)[1:] #   Ignore Header
    sxs = takewhile(lambda e: e.tag != 'HD' or e.get('SOURCE') != 'HD1', sxs)

    return list(sxs)

def split_by_applicability(sxs):
    """Given a list of xml nodes, determine where to break the list into
    sections organized by applicability"""
    header = sxs[0]
    remaining = sxs[1:]
    def not_breakpt(el):
        return el.tag != 'HD' or applicable.scanString(el.text) is None
    first_seg = (header, list(takewhile(not_breakpt, remaining)))
    remaining = sxs[1 + len(first_seg[1]):]
    print len(remaining)
    if len(remaining) == 0:
        return [first_seg]
    else:
        return [first_seg] + split_by_applicability(remaining)
