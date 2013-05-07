from itertools import dropwhile, takewhile
import parser.grammar.rule_headers as grammar
import re


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

def fetch_document_number(xml_tree):
    """Pull out the document number, which is the id for this rule"""
    text = xml_tree.xpath('//FRDOC')[0].text
    match = re.search(r"(\d{4}-\d+)", text)
    if match:
        return match.group(1)


def build_section_by_section(sxs, depth=2):
    """Given a list of xml nodes in the section by section analysis, pull
    out hierarchical data into a structure."""
    structures = []
    while sxs:
        title, text_els, sub_sections, sxs = split_into_ttsr(sxs, depth)

        children = [el.text for el in text_els if el.tag == 'P']
        children += build_section_by_section(sub_sections, depth+1)

        structures.append({
            'title': title.text,
            'children': children
            })
    return structures


def split_into_ttsr(sxs, depth=2):
    """Split the provided list of xml nodes into a node with a title, a
    sequence of text nodes, a sequence of nodes associated with the sub
    sections of this header, and the remaining xml nodes"""
    title = sxs[0]
    next_section_marker = 'HD' + str(depth)
    section = list(takewhile(lambda e: e.tag != 'HD'
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
        if match.paragraphs:
            if match.paragraphs.level1:
                paragraph_ids.append(match.paragraphs.level1)
            if match.paragraphs.level2:
                paragraph_ids.append(match.paragraphs.level2)
            if match.paragraphs.level3:
                paragraph_ids.append(match.paragraphs.level3)
            if match.paragraphs.level4:
                paragraph_ids.append(match.paragraphs.level4)
        label = "%s.%s" % (part, match.section)
        for paragraph_id in paragraph_ids:
            label += '(' + paragraph_id + ')'
        return label
