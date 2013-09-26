import re
from regparser import search
from regparser.tree.supplement import find_supplement_start


def find_appendix_start(text):
    """Find the start of the appendix (e.g. Appendix A)"""
    return search.find_start(text, u'Appendix', ur'[A-Z] to Part')


def find_next_appendix_offsets(text):
    """Find the start/end of the next appendix. Accounts for supplements"""
    offsets = search.find_offsets(text, find_appendix_start)
    if offsets is None:
        return None

    start, end = offsets
    supplement_start = find_supplement_start(text)
    if supplement_start is not None and supplement_start < start:
        return None
    if supplement_start is not None and supplement_start < end:
        return (start, supplement_start)
    return (start, end)


def appendices(text):
    """Carve out a list of all the appendix offsets."""
    def offsets_fn(remaining_text, idx, excludes):
        return find_next_appendix_offsets(remaining_text)
    return search.segments(text, offsets_fn)


def find_appendix_section_start(text, appendix):
    """Find the start of an appendix section (e.g. A-1 -- Something"""
    match = re.search(ur'^%s-\d+' % appendix, text, re.MULTILINE)
    if match:
        return match.start()


def find_next_appendix_section_offsets(text, appendix):
    """Find the start/end of the next appendix section."""
    return search.find_offsets(
        text, lambda t: find_appendix_section_start(
            t, appendix))


def appendix_sections(text, appendix):
    """Split an appendix into its sections. Return the offsets"""
    def offsets_fn(remaining_text, idx, excludes):
        return find_next_appendix_section_offsets(remaining_text, appendix)
    return search.segments(text, offsets_fn)


def get_appendix_letter(title, part):
    """Pull out appendix letter from header. Assumes proper format"""
    return re.match(
        ur'^Appendix ([A-Z]+) to Part %d.*$' % part, title).group(1)


def get_appendix_section_number(title, appendix_letter):
    """Pull out appendix section number from header. Assumes proper format"""
    pattern = ur'^%s-(\d+(\([a-zA-Z]+\))*).*$' % appendix_letter
    return re.match(pattern, title).group(1)
