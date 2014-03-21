from copy import deepcopy
from itertools import dropwhile, takewhile

from lxml import etree

from regparser.citations import internal_citations, Label
from regparser.notice.util import body_to_string, spaces_then_remove
from regparser.notice.util import swap_emphasis_tags


def remove_extract(xml_tree):
    """Occasionally, the paragraphs/etc. useful to us are inside an EXTRACT
    tag. To normalize, move everything in an EXTRACT tag out"""
    xml_tree = deepcopy(xml_tree)
    for extract in xml_tree.xpath('//EXTRACT'):
        parent = extract.getparent()
        insert_idx = parent.index(extract)
        for child in extract:
            extract.remove(child)
            parent.insert(insert_idx, child)
            insert_idx += 1
        parent.remove(extract)
    return xml_tree


def find_section_by_section(xml_tree):
    """Find the section-by-section analysis of this notice"""
    xml_children = remove_extract(xml_tree).xpath('//SUPLINF/*')
    sxs = dropwhile(lambda el: (
        el.tag != 'HD'
        or el.get('SOURCE') != 'HD1'
        or 'section-by-section' not in el.text.lower()), xml_children)

    try:
        # Ignore Header
        sxs.next()
        # Remove any intro paragraphs
        sxs = dropwhile(lambda el: el.tag != 'HD', sxs)
        sxs = takewhile(
            lambda el: el.tag != 'HD' or el.get('SOURCE') != 'HD1', sxs)

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
        paragraph_xmls = [deepcopy(el) for el in text_els
                          if el.tag == 'P' or el.tag == 'FP']
        footnotes = []
        for p_idx, paragraph_xml in enumerate(paragraph_xmls):
            spaces_then_remove(paragraph_xml, 'PRTPAGE')
            spaces_then_remove(paragraph_xml, 'FTREF')
            swap_emphasis_tags(paragraph_xml)
            # Anything inside a SU can also be ignored
            for su in paragraph_xml.xpath('./SU'):
                su_text = etree.tostring(su)
                footnotes.append({
                    'paragraph': p_idx,
                    'reference': su.text,
                    'offset': body_to_string(paragraph_xml).find(su_text)})
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
            'footnote_refs': footnotes
            }
        labels = parse_into_labels(title.text, part)
        if not labels:
            structures.append(next_structure)
        for label in labels:
            cp_structure = dict(next_structure)  # shallow copy
            cp_structure['label'] = label
            structures.append(cp_structure)

    return structures


def add_spaces_to_title(title):
    """Federal Register often seems to miss spaces in the title of SxS
    sections. Make sure spaces get added if appropriate"""
    for citation in internal_citations(title, Label()):
        end = citation.end
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
            or (internal_citations(header_xml.text, Label())
                and not internal_citations(child_xml.text, Label())))


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


def parse_into_labels(txt, part):
    """Find what part+section+(paragraph) (could be multiple) this text is
    related to."""
    citations = internal_citations(txt, Label(part=part))
    labels = ['-'.join(cit.label.to_list()) for cit in citations]
    return labels
