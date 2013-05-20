from datetime import datetime
from itertools import dropwhile, takewhile
from lxml import etree
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

def fetch_docket_number(xml_tree):
    """Pull out the /docket/ number."""
    text = xml_tree.xpath('//DEPDOC')[0].text
    match = re.search(r"(\d+-\d+)", text)
    if match:
        return match.group(1)

def fetch_simple_fields(xml_tree):
    """Return a map with several fields pulled from the XML. These fields
    are easy to find, so we are lumping them together."""
    fields = {}
    #   Regulation ID Number
    rin = xml_tree.xpath('//RIN')
    if rin:
        fields['rin'] = rin[0].text[len('RIN '):]

    fields['agency'] = xml_tree.xpath('//AGENCY')[0].text
    fields['action'] = xml_tree.xpath('//ACT/P')[0].text
    fields['summary'] = xml_tree.xpath('//SUM/P')[0].text

    return fields

def fetch_cfr_part(xml_tree):
    """The CFR Part is used in the ids used in the section by section
    analysis (and elsewhere). This function figures out to which "part" this
    notice applies."""
    text = xml_tree.xpath('//CFR')[0].text
    match = re.search(r"CFR Part (\d+)", text)
    if match:
        return match.group(1)

def parse_date_sentence(sentence):
    """Return the date type + date in this sentence (if one exists)."""
    #   Search for month date, year at the end of the sentence
    sentence = sentence.lower()
    date_re = r".*((january|february|march|april|may|june|july|august"
    date_re += r"|september|october|november|december) \d+, \d+)$"
    match = re.match(date_re, sentence)
    if match:
        date = datetime.strptime(match.group(1), "%B %d, %Y")
        if 'comment' in sentence:
            return ('comments', date.strftime("%Y-%m-%d"))
        if 'effective' in sentence:
            return ('effective', date.strftime("%Y-%m-%d"))
        return ('other', date.strftime('%Y-%m-%d'))

def fetch_dates(xml_tree):
    """Pull out any dates (and their types) from the XML. Not all notices
    have all types of dates, some notices have multiple dates of the same
    type."""
    dates_field = xml_tree.xpath('//EFFDATE/P')
    dates = {}
    if dates_field:
        for sentence in dates_field[0].text.split('.'):
            result_pair = parse_date_sentence(sentence.replace('\n', ' '))
            if result_pair:
                date_type, date = result_pair
                dates[date_type] = dates.get(date_type, []) + [date]
    if dates:
        return dates

def fetch_addresses(xml_tree):
    """Pull out address information (addresses + instructions). Final
    notices do not have addresses (as we no longer accept comments)."""
    address_nodes = xml_tree.xpath('//ADD/P')
    addresses = {}
    for p in address_nodes:
        etree.strip_tags(p, 'E')
        p = p.text
        if ': ' in p:
            lhs, rhs = p.split(': ')
            if rhs.strip():
                addresses['methods'] = (addresses.get('methods', []) +
                    [(lhs.strip(), rhs.strip())])
                continue
        if not addresses:
            addresses['intro'] = p
        else:
            addresses['instructions'] = (addresses.get('instructions', []) +
                [p])
    if addresses:
        return addresses
        

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
    to_return = fetch_simple_fields(xml)
    to_return['document_number'] = fetch_document_number(xml)
    to_return['cfr_part'] = cfr_part
    to_return['section_by_section'] = sxs
    dates = fetch_dates(xml)
    if dates:
        to_return['dates'] = dates
    addresses = fetch_addresses(xml)
    if addresses:
        to_return['addresses'] = addresses
    return to_return
