from copy import deepcopy
from itertools import chain, dropwhile, takewhile

from lxml import etree

import regparser.grammar.rules as grammar
from regparser.tree.struct import Node


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


def find_page(xml, index_line, page_number):
    """Find the FR page that includes the indexed line"""
    for prtpage in takewhile(lambda p: p.sourceline < index_line,
                             xml.xpath('//PRTPAGE')):
        if prtpage.get('P'):
            page_number = int(prtpage.get('P'))

    return page_number


def build_section_by_section(sxs, part, fr_start_page):
    """Given a list of xml nodes in the section by section analysis, pull
    out hierarchical data into a structure."""
    structures = []
    #while sxs: is deprecated
    while len(sxs):
        title, text_els, sub_sections, sxs = split_into_ttsr(sxs)

        page = find_page(title, title.sourceline, fr_start_page)
        paragraph_xmls = [deepcopy(el) for el in text_els if el.tag == 'P']
        for paragraph_xml in paragraph_xmls:
            # Add space to unneeded tags (so they leave one when deleted)
            for tag in chain(paragraph_xml.xpath('.//PRTPAGE'),
                             paragraph_xml.xpath('.//FTREF')):
                tag.text = ' '
            # Remove unneeded tags
            etree.strip_tags(paragraph_xml, 'PRTPAGE', 'FTREF')
            # Anything inside a SU can also be ignored
            for su in paragraph_xml.xpath('./SU'):
                su.getparent().text = su.getparent().text + su.tail
                su.getparent().remove(su)

        paragraphs = [el.text + ''.join(etree.tostring(c) for c in el)
                      for el in paragraph_xmls]
        children = build_section_by_section(sub_sections, part, page)

        next_structure = {
            'page': page,
            'title': title.text,
            'paragraphs': paragraphs,
            'children': children
            }
        label = parse_into_label(title.text, part)
        if label:
            next_structure['label'] = label

        structures.append(next_structure)
    return structures


def is_child_of(child_xml, header_xml):
    """Children are paragraphs, have lower 'source' or the header has
    citations and the child does not"""
    return (child_xml.tag != 'HD'
            or child_xml.get('SOURCE') > header_xml.get('SOURCE')
            or (list(grammar.applicable.scanString(header_xml.text))
                and not list(grammar.applicable.scanString(child_xml.text))))


def split_into_ttsr(sxs):
    """Split the provided list of xml nodes into a node with a title, a
    sequence of text nodes, a sequence of nodes associated with the sub
    sections of this header, and the remaining xml nodes"""
    title = sxs[0]
    section = list(takewhile(lambda e: is_child_of(e, title), sxs[1:]))
    text_elements = list(takewhile(lambda e: e.tag != 'HD', section))
    sub_sections = section[len(text_elements):]
    remaining = sxs[1+len(text_elements)+len(sub_sections):]
    return (title, text_elements, sub_sections, remaining)


def parse_into_label(txt, part):
    """Find what part+section+(paragraph) this text is related to. Returns
    only the first match. Currently only accounts for references to
    regulation text."""

    for match, _, _ in grammar.applicable_interp.scanString(txt):
        label = [part, match.section]
        label.extend(p for p in list(match.p_head))
        label.append(Node.INTERP_MARK)
        if match.comment_levels:
            label.append(match.comment_levels.level1)
            label.append(match.comment_levels.level2)
            label.append(match.comment_levels.level3)
        return "-".join(filter(bool, label)) # remove empty strings
    for match, _, _ in grammar.applicable_section.scanString(txt):
        paragraph_ids = []
        paragraph_ids.extend(p for p in [
            match.level1, match.level2, match.level3, match.level4] if p)
        return "-".join([part, match.section] + paragraph_ids)
    for match, _, _ in grammar.applicable_appendix.scanString(txt):
        return "%s-%s" % (part, match.letter)
