from itertools import dropwhile, takewhile
from parser.grammar import rule_headers as grammar
import re


def find_section_by_section(xml_tree):
    """Find the section-by-section analysis of this notice"""
    xml_children = xml_tree.xpath('//SUPLINF/*')
    sxs = dropwhile(lambda el: (
        el.tag != 'HD'
        or el.get('SOURCE') != 'HD1' 
        or 'section-by-section' not in el.text.lower()), xml_children)

    try:
        sxs.next()  #   Ignore Header
        sxs = takewhile(lambda e: e.tag != 'HD' or e.get('SOURCE') != 'HD1', 
                sxs)

        return list(sxs)
    except StopIteration:
        return []

def fetch_document_number(xml_tree):
    """Pull out the document number, which is the id for this notice"""
    text = xml_tree.xpath('//FRDOC')[0].text
    match = re.search(r"(\d{4}-\d+)", text)
    if match:
        return match.group(1)

def fetch_cfr_part(xml_tree):
    """The CFR Part is used in the ids used in the section by section
    analysis (and elsewhere). This function figures out to which "part" this
    notice applies."""
    text = xml_tree.xpath('//CFR')[0].text
    match = re.search(r"CFR Part (\d+)", text)
    if match:
        return match.group(1)


def build_section_by_section(sxs, part, depth=2):
    """Given a list of xml nodes in the section by section analysis, pull
    out hierarchical data into a structure."""
    structures = []
    while len(sxs): # while sxs: is deprecated
        title, text_els, sub_sections, sxs = split_into_ttsr(sxs, depth)

        paragraphs = [el.text for el in text_els if el.tag == 'P']
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
        return "-".join([part, match.section] + paragraph_ids)

def build_notice(xml):
    """Given xml alone, build up a corresponding notice structure"""
    cfr_part = fetch_cfr_part(xml)

    sxs = find_section_by_section(xml)
    sxs = build_section_by_section(sxs, cfr_part)
    return {
        'document_number': fetch_document_number(xml),
        'cfr_part': cfr_part,
        'section_by_section': sxs
    }
