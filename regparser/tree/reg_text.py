# vim: set encoding=utf-8
import re

from regparser import utils
from regparser.grammar.internal_citations import appendix_citation
from regparser.grammar.internal_citations import regtext_citation
from regparser.search import find_offsets, find_start, segments
from regparser.tree import struct
from regparser.tree.appendix.carving import find_appendix_start
from regparser.tree.paragraph import ParagraphParser
from regparser.tree.supplement import find_supplement_start


def build_reg_text_tree(text, part):
    """Build up the whole tree from the plain text of a single
    regulation."""
    title, body = utils.title_body(text)
    lab = struct.label(str(part), [str(part)], title)

    sects = sections(body, part)
    if not sects:
        return struct.node(text, label=lab)
    children_text = body[:sects[0][0]]

    children = []
    for start,end in sects:
        section_text = body[start:end]
        children.append(build_section_tree(section_text, part))
    return struct.node(children_text, children, lab)


def _mk_label(old_label, next_part):
    return struct.extend_label(old_label, '-' + next_part, next_part)


regParser = ParagraphParser(r"\(%s\)", _mk_label)


def find_next_section_start(text, part):
    """Find the start of the next section (e.g. 205.14)"""
    return find_start(text, u"§", str(part) + r"\.\d+")


def next_section_offsets(text, part):
    """Find the start/end of the next section"""
    offsets = find_offsets(text, lambda t: find_next_section_start(t, part))
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


def build_section_tree(text, part):
    """Construct the tree for a whole section. Assumes the section starts
    with an identifier"""
    title, text = utils.title_body(text)

    exclude = [(start, end) for _, start, end in
            regtext_citation.scanString(text)]
    exclude += [(start, end) for _, start, end in 
            appendix_citation.scanString(text)]
    section = re.search(r'%d\.(\d+) ' % part, title).group(1)
    label = struct.label("%d-%s" % (part, section), [str(part), section])
    p_tree = regParser.build_paragraph_tree(text, exclude=exclude, label=label)

    p_tree['label']['title'] = title
    return p_tree
