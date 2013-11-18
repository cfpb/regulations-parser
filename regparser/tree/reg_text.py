# vim: set encoding=utf-8
import re

from regparser import utils
from regparser.citations import internal_citations, Label
from regparser.grammar.unified import marker_subpart_title
from regparser.search import find_offsets, find_start, segments
from regparser.tree import struct
from regparser.tree.appendix.carving import find_appendix_start
from regparser.tree.paragraph import ParagraphParser
from regparser.tree.supplement import find_supplement_start


def build_subparts_tree(text, part, subpart_builder):
    """ Build a tree of a subpart, and it's children sections.
    subpart_builder can be a builder that builds a subpart or an
    emptypart. """

    subpart = subpart_builder(part)
    sects = sections(text, part)
    if sects:
        children = []
        for s, e in sects:
            section_text = text[s:e]
            children.append(build_section_tree(section_text, part))
        subpart.children = children
        return (subpart, text[:sects[0][0]])
    return (subpart, text)


def build_reg_text_tree(text, part):
    """Build up the whole tree from the plain text of a single regulation. This
    only builds the regulation text part, and does not include appendices or
    the supplement. """
    title, body = utils.title_body(text)
    label = [str(part)]

    subparts_list = []

    subpart_locations = subparts(body)
    if subpart_locations:
        pre_subpart = body[:subpart_locations[0][0]]
        first_emptypart, children_text = build_subparts_tree(
            pre_subpart, part, build_empty_part)
        if pre_subpart.strip() and first_emptypart.children:
            subparts_list.append(first_emptypart)
        else:
            children_text = pre_subpart

        for start, end in subpart_locations:
            subpart_body = body[start:end]
            subpart, _ = build_subparts_tree(
                subpart_body, part, lambda p: build_subpart(subpart_body, p))
            subparts_list.append(subpart)
    else:
        emptypart, children_text = build_subparts_tree(
            body, part, build_empty_part)
        if emptypart.children:
            subparts_list.append(emptypart)
        else:
            return struct.Node(
                text, [build_empty_part(part)], label, title)
    return struct.Node(children_text, subparts_list, label, title)

regParser = ParagraphParser(r"\(%s\)", struct.Node.REGTEXT)


def build_empty_part(part):
    """ When a regulation doesn't have a subpart, we give it an emptypart (a
    dummy subpart) so that the regulation tree is consistent. """

    label = [str(part), 'Subpart']
    return struct.Node(
        '', [], label, '', node_type=struct.Node.EMPTYPART)


def build_subpart(text, part):
    results = marker_subpart_title.parseString(text)
    subpart_letter = results.subpart
    subpart_title = results.subpart_title
    label = [str(part), 'Subpart', subpart_letter]

    return struct.Node(
        "", [], label, subpart_title, node_type=struct.Node.SUBPART)


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
    if subpart_start is not None \
            and subpart_start > start and subpart_start < end:
        end = subpart_start
    elif appendix_start is not None and appendix_start < end:
        end = appendix_start
    elif supplement_start is not None and supplement_start < end:
        end = supplement_start

    if end >= start:
        return (start, end)


def next_subpart_offsets(text):
    """Find the start,end of the next subpart"""
    offsets = find_offsets(text, find_next_subpart_start)
    if offsets is None:
        return None
    start, end = offsets
    appendix_start = find_appendix_start(text)
    supplement_start = find_supplement_start(text)
    if appendix_start is not None and appendix_start < end:
        end = appendix_start
    elif supplement_start is not None and supplement_start < end:
        end = supplement_start

    if end >= start:
        return (start, end)


def sections(text, part):
    """Return a list of section offsets. Does not include appendices."""
    def offsets_fn(remaining_text, idx, excludes):
        return next_section_offsets(remaining_text, part)
    return segments(text, offsets_fn)


def subparts(text):
    """ Return a list of subpart offset. Does not include appendices,
    supplements. """

    def offsets_fn(remaining_text, idx, excludes):
        return next_subpart_offsets(remaining_text)
    return segments(text, offsets_fn)


def build_section_tree(text, part):
    """Construct the tree for a whole section. Assumes the section starts
    with an identifier"""
    title, text = utils.title_body(text)

    exclude = [(pc.full_start, pc.full_end) for pc in
               internal_citations(text, Label(part=part))]
    section = re.search(r'%d\.(\d+)\b' % part, title).group(1)
    label = [str(part), section]
    p_tree = regParser.build_tree(
        text, exclude=exclude, label=label, title=title)
    return p_tree
