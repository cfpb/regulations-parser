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


def build_section_by_section(sxs, fr_start_page, previous_label):
    """Given a list of xml nodes in the section by section analysis, pull
    out hierarchical data into a structure. Previous label is carried along to
    merge analyses of the same section."""
    structures = []
    while len(sxs):  # while sxs: is deprecated
        cfr_part = previous_label.split('-')[0]
        title, text_els, sub_sections, sxs = split_into_ttsr(sxs, cfr_part)

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
        label_for_children = previous_label
        labels = parse_into_labels(title.text, cfr_part)
        if labels:
            label_for_children = labels[-1]

        # recursively build children. Be sure to give them the proper label
        children = build_section_by_section(sub_sections, page,
                                            label_for_children)

        next_structure = {
            'page': page,
            'title': add_spaces_to_title(title.text),
            'paragraphs': paragraphs,
            'children': children,
            'footnote_refs': footnotes
            }

        if (labels   # No label => subheader
                # Concatenate if repeat label or backtrack
                and not all(label == previous_label
                            or is_backtrack(previous_label, label)
                            for label in labels)):
            previous_label = labels[-1]
            next_structure['labels'] = labels
        structures.append(next_structure)

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


def is_backtrack(previous_label, next_label):
    """If we've already processes a header with 22(c) in it, we can assume
    that any following headers with 1111.22 are *not* supposed to be an
    analysis of 1111.22"""
    previous_label = previous_label or []
    next_label = next_label or []
    trimmed = previous_label[:len(next_label)]
    return (next_label and len(previous_label) > len(next_label)
            and trimmed == next_label)


def is_child_of(child_xml, header_xml, cfr_part, header_citations=None):
    """Children are paragraphs, have lower 'source', the header has
    citations and the child does not, the citations for header and child
    are the same or the citation in a child is incorrect"""
    if child_xml.tag != 'HD':
        return True
    else:
        if header_citations is None:
            header_citations = parse_into_labels(header_xml.text, cfr_part)
        child_citations = parse_into_labels(child_xml.text, cfr_part)
        if (child_xml.get('SOURCE') > header_xml.get('SOURCE')
                or (header_citations and not child_citations)
                or (header_citations
                    and header_citations[-1] == child_citations[0])):
            return True
        elif header_citations and child_citations:
            return is_backtrack(header_citations[-1].split('-'),
                                child_citations[0].split('-'))
        else:
            return False


def split_into_ttsr(sxs, cfr_part):
    """Split the provided list of xml nodes into a node with a title, a
    sequence of text nodes, a sequence of nodes associated with the sub
    sections of this header, and the remaining xml nodes"""
    title = sxs[0]
    title_citations = parse_into_labels(title.text, cfr_part)
    section = list(takewhile(lambda e: is_child_of(e, title, cfr_part,
                                                   title_citations), sxs[1:]))
    text_elements = list(takewhile(lambda e: e.tag != 'HD', section))
    sub_sections = section[len(text_elements):]
    remaining = sxs[1+len(text_elements)+len(sub_sections):]
    return (title, text_elements, sub_sections, remaining)


def parse_into_labels(txt, part):
    """Find what part+section+(paragraph) (could be multiple) this text is
    related to."""
    citations = internal_citations(txt, Label(part=part))
    # odd corner case: headers shouldn't include both an appendix and regtext
    labels = [c.label for c in citations]
    if any('appendix' in l.settings for l in labels):
        labels = [l for l in labels if 'appendix' in l.settings]
    labels = ['-'.join(l.to_list()) for l in labels]
    return labels
