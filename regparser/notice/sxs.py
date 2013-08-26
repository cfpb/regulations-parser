from itertools import dropwhile, takewhile

from lxml import etree

import regparser.grammar.rules as grammar


def find_section_by_section(xml_tree):
    """Find the section-by-section analysis of this notice"""
    xml_children = xml_tree.xpath('//SUPLINF/*')
    sxs = dropwhile(lambda el: (
        el.tag != 'HD'
        or el.get('SOURCE') != 'HD1'
        or 'section-by-section' not in el.text.lower()), xml_children)

    try:
        #Ignore Header
        sxs.next()
        sxs = takewhile(
            lambda e: e.tag != 'HD' or e.get('SOURCE') != 'HD1', sxs)

        return list(sxs)
    except StopIteration:
        return []


def build_section_by_section(sxs, part, depth=2):
    """Given a list of xml nodes in the section by section analysis, pull
    out hierarchical data into a structure."""
    structures = []
    #while sxs: is deprecated
    while len(sxs):
        title, text_els, sub_sections, sxs = split_into_ttsr(sxs, depth)

        paragraph_xmls = [el for el in text_els if el.tag == 'P']
        for paragraph_xml in paragraph_xmls:
            etree.strip_tags(paragraph_xml, 'PRTPAGE')
        paragraphs = [el.text for el in paragraph_xmls]
        children = build_section_by_section(sub_sections, part, depth+1)

        next_structure = {
            'title': title.text,
            'paragraphs': paragraphs,
            'children': children
            }
        label = parse_into_label(title.text, part)
        if label:
            next_structure['label'] = label

        structures.append(next_structure)
    return structures


def split_into_ttsr(sxs, depth=2):
    """Split the provided list of xml nodes into a node with a title, a
    sequence of text nodes, a sequence of nodes associated with the sub
    sections of this header, and the remaining xml nodes"""
    title = sxs[0]
    next_section_marker = 'HD' + str(depth)
    section = list(takewhile(
        lambda e: e.tag != 'HD'
        or e.get('SOURCE') != next_section_marker, sxs[1:]))
    text_elements = list(takewhile(lambda e: e.tag != 'HD', section))
    sub_sections = section[len(text_elements):]
    remaining = sxs[1+len(text_elements)+len(sub_sections):]
    return (title, text_elements, sub_sections, remaining)


def parse_into_label(txt, part):
    """Find what part+section+(paragraph) this text is related to. Returns
    only the first match. Currently only accounts for references to
    regulation text."""

    for match, _, _ in grammar.applicable.scanString(txt):
        paragraph_ids = []
        paragraph_ids.extend(p for p in [
            match.level1, match.level2, match.level3, match.level4] if p)
        return "-".join([part, match.section] + paragraph_ids)
