# vim: set encoding=utf-8
import re

from regparser import utils
from regparser.grammar.internal_citations import appendix_citation
from regparser.grammar.internal_citations import regtext_citation
from regparser.grammar.common import subpart
from regparser.search import find_offsets, find_start, segments
from regparser.tree import struct
from regparser.tree.appendix.carving import find_appendix_start
from regparser.tree.paragraph import ParagraphParser
from regparser.tree.supplement import find_supplement_start


def build_reg_text_tree(text, part):
    """Build up the whole tree from the plain text of a single regulation. This
    only builds the regulation text part, and does not include appendices or
    the supplement. """
    title, body = utils.title_body(text)
    label = [str(part)]

    subpart_locations = subparts(body)
    subparts_list = []

    if subpart_locations:
        for start,end in subpart_locations:
            subpart_body = body[start:end]
            subpart = build_subpart(subpart_body, part)
            sects = sections(subpart_body, part)
            if sects:
                subpart_children = []
                for s,e in sects:
                    section_text = subpart_body[s:e]
                    subpart_children.append(build_section_tree(section_text, part))
            subpart.children = subpart_children
            subparts_list.append(subpart)
        children_text = body[:subpart_locations[0][0]] 
    else:
        sects = sections(body,part)
        empty_part = build_empty_part(part)

        if not sects:
            return struct.Node(text, [empty_part], label, title)

        children = []
        for s,e in sects:
            section_text = body[start:end]
            children.append(build_section_tree(section_text, part))
        empty_part.children = children
        subparts_list.append(empty_part)

        children_text = body[:sects[0][0]]

    return struct.Node(children_text, subparts_list, label, title)
            
    #if not sects:
    #    return struct.Node(text, [], label, title)
    #children_text = body[:sects[0][0]]

    #children = []
    #for start,end in sects:
    #    section_text = body[start:end]
    #    children.append(build_section_tree(section_text, part))
    #return struct.Node(children_text, children, label, title)

regParser = ParagraphParser(r"\(%s\)", struct.Node.REGTEXT)

def build_empty_part(part):
    """ When a regulation doesn't have a subpart, we give it an emptypart (a
    dummy subpart) so that the regulation tree is consistent. """

    label = [str(part), 'Subpart']
    return struct.Node('', [], label, '', 
            node_type=struct.Node.EMPTYPART)

def build_subpart(text, part):
    results = subpart.parseString(text)
    subpart_letter = results.subpart_letter
    subpart_title = results.subpart_title
    label = [str(part), 'Subpart', subpart_letter]

    return struct.Node("", [], label, 
                subpart_title, node_type=struct.Node.SUBPART)

def find_next_subpart_start(text):
    """ Find the start of the next Subpart (e.g. Subpart B)"""
    return find_start(text, u'Subpart', ur'[A-Z]—')

def find_next_section_start(text, part):
    """Find the start of the next section (e.g. 205.14)"""
    return find_start(text, u"§", str(part) + r"\.\d+")

def next_section_offsets(text, part):
    """Find the start/end of the next section"""
    offsets = find_offsets(text, lambda t: find_next_section_start(t, part))
    if offsets is None:
        return None

    start, end = offsets
    subpart_start = find_next_subpart_start(text)
    appendix_start = find_appendix_start(text)
    supplement_start = find_supplement_start(text)
    if subpart_start != None and subpart_start > start and subpart_start < end:
        return (start, subpart_start)
    if appendix_start != None and appendix_start < end:
        return (start, appendix_start)
    if supplement_start != None and supplement_start < end:
        return (start, supplement_start)
    return (start, end)

def next_subpart_offsets(text):
    """Find the start,end of the next subpart"""
    offsets = find_offsets(text, find_next_subpart_start)
    if offsets is None:
        return None
    start, end = offsets
    appendix_start = find_appendix_start(text)
    supplement_start = find_supplement_start(text)
    if appendix_start != None and appendix_start < end:
        return (start, appendix_start)
    if supplement_start != None and supplement_start < end:
        return (start, supplement_start)
    return (start, end)

def sections(text, part):
    """Return a list of section offsets. Does not include appendices."""
    def offsets_fn(remaining_text, idx, excludes):
        return next_section_offsets(remaining_text, part)
    return segments(text, offsets_fn)

def subparts(text):
    """ Return a list of subpart offset. Does not include appendices, supplements. """
    def offsets_fn(remaining_text, idx, excludes):
        return next_subpart_offsets(remaining_text)
    return segments(text, offsets_fn)

def build_section_tree(text, part):
    """Construct the tree for a whole section. Assumes the section starts
    with an identifier"""
    title, text = utils.title_body(text)

    exclude = [(start, end) for _, start, end in
            regtext_citation.scanString(text)]
    exclude += [(start, end) for _, start, end in 
            appendix_citation.scanString(text)]
    section = re.search(r'%d\.(\d+) ' % part, title).group(1)
    label = [str(part), section]
    p_tree = regParser.build_tree(text, exclude=exclude, label=label,
            title=title)
    return p_tree
