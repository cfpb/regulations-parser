from itertools import dropwhile, takewhile
from parser.grammar.rule_headers import applicable
from parser.tree import struct

def find_section_by_section(xml_tree):
    """Find the section-by-section analysis of this rule"""
    xml_children = xml_tree.xpath('//SUPLINF/*')
    sxs = dropwhile(lambda el: (
        el.tag != 'HD'
        or el.get('SOURCE') != 'HD1' 
        or 'section-by-section' not in el.text.lower()), xml_children)
    sxs.next()  #   Ignore Header
    sxs = takewhile(lambda e: e.tag != 'HD' or e.get('SOURCE') != 'HD1', sxs)

    return list(sxs)

def build_section_by_section(sxs, depth=2):
    """Given a list of xml nodes in the section by section analysis, create
    trees with the same content. Who doesn't love trees?"""
    trees = []
    while sxs:
        title = sxs[0]
        sxs = sxs[1:]
        source = 'HD' + str(depth)
        body = list(takewhile(lambda e: e.tag != 'HD' 
            or e.get('SOURCE') != source, sxs))
        text_xml = list(takewhile(lambda e: e.tag != 'HD', body))
        remaining_body = body[len(text_xml):]
        children = map(convert_to_text, text_xml)
        tree = struct.node('', 
                children + build_section_by_section(remaining_body, depth+1),
                struct.label(title.text))
        trees.append(tree)
        sxs = sxs[len(body):]
    return trees

def convert_to_text(p_xml):
    """XML P to tree node"""
    return struct.node(p_xml.text)

