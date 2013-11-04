from copy import deepcopy
from itertools import chain, dropwhile, takewhile

from lxml import etree

import regparser.grammar.rules as grammar
from regparser.notice.util import body_to_string, spaces_then_remove
from regparser.notice.util import swap_emphasis_tags
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
        footnotes = []
        for p_idx, paragraph_xml in enumerate(paragraph_xmls):
            spaces_then_remove(paragraph_xml, 'PRTPAGE')
            spaces_then_remove(paragraph_xml, 'FTREF')
            swap_emphasis_tags(paragraph_xml)
            # Anything inside a SU can also be ignored
            for su in paragraph_xml.xpath('./SU'):
                su_text = etree.tostring(su)
                footnotes.append((p_idx, su.text,
                                  body_to_string(paragraph_xml).find(su_text)))
                if su.tail and su.getprevious() is not None: 
                    su.getprevious().tail = (su.getprevious().tail or '')
                    su.getprevious().tail += su.tail
                elif su.tail:
                    su.getparent().text = (su.getparent().text or '')
                    su.getparent().text += su.tail
                su.getparent().remove(su)

        paragraphs = [body_to_string(el) for el in paragraph_xmls]
            
        children = build_section_by_section(sub_sections, part, page)

        next_structure = {
            'page': page,
            'title': add_spaces_to_title(title.text),
            'paragraphs': paragraphs,
            'children': children,
            'footnotes': footnotes
            }
        label = parse_into_label(title.text, part)
        if label:
            next_structure['label'] = label

        structures.append(next_structure)
    return structures


def add_spaces_to_title(title):
    """Federal Register often seems to miss spaces in the title of SxS
    sections. Make sure spaces get added if appropriate"""
    for _, _, end in grammar.applicable.scanString(title):
        # Next char is an alpha and last char isn't a space
        if end < len(title) and title[end].isalpha() and title[end-1] != ' ':
            title = title[:end] + ' ' + title[end:]
            break   # Assumes there is only one paragraph in a title
    return title


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
        return "-".join(filter(bool, label))  # remove empty strings
    for match, _, _ in grammar.applicable_section.scanString(txt):
        paragraph_ids = []
        paragraph_ids.extend(p for p in [
            match.level1, match.level2, match.level3, match.level4] if p)
        return "-".join([part, match.section] + paragraph_ids)
    for match, _, _ in grammar.applicable_paragraph.scanString(txt):
        paragraph_ids = []
        paragraph_ids.extend(p for p in [
            match.level1, match.level2, match.level3, match.level4] if p)
        return "-".join([part, match.section] + paragraph_ids)
    for match, _, _ in grammar.applicable_appendix.scanString(txt):
        return "%s-%s" % (part, match.letter)
