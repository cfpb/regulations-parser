# vim: set encoding=utf-8
import re
from parser import utils
from parser.grammar.internal_citations import regtext_citation
from parser.search import find_offsets, find_start, segments
from parser.tree.appendix.carving import find_appendix_start
from parser.tree.paragraph import ParagraphParser
from parser.tree.supplement import find_supplement_start
from parser.tree import struct

def _mk_label(old_label, next_part):
    return struct.extend_label(old_label, '-' + next_part, next_part)

regParser = ParagraphParser(r"\(%s\)", _mk_label)

def find_next_section_start(text, part):
    """Find the start of the next section (e.g. 205.14)"""
    return find_start(text, u"§", str(part) + r"\.\d+")

def next_section_offsets(text, part):
    """Find the start/end of the next section"""
    offsets = find_offsets(text, lambda t: find_next_section_start(t, part))
    if offsets == None:
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
    section = re.search(r'%d\.(\d+) ' % part, title).group(1)
    label = struct.label("%d-%s" % (part, section), [str(part), section])
    p_tree = regParser.build_paragraph_tree(text, exclude=exclude, label=label)

    p_tree['label']['title'] = title
    return p_tree
