import re
from parser import search
from parser.grammar.interpretation_headers import parser as header_parser

def segment_by_header(text, part):
    """Return a list of headers (section, appendices, paragraphs) and their 
    offsets."""
    section_re = ur'Section %d.\d+.*?' % part
    l4_re = ur'(\([A-Z]+\))?'
    l3_re = ur'(\([ivxlcdm]+\)' + l4_re + ')?'
    l2_re = ur'(\([0-9]+\)' + l3_re + ')?'
    l1_re = ur'\([a-z]+\)' + l2_re
    whole_par_re = ur'\d+' + l1_re + '.*?'
    subpars_re = ur'Paragraph \d+' + l1_re
    appendix_re = ur'Appendix [A-Z].*?'

    mecha_re = re.compile(ur'^((%s)|(%s)|(%s)|(%s))$' % (section_re, 
        whole_par_re, subpars_re, appendix_re), re.MULTILINE)

    def offsets_fn(remaining_text, idx, excludes):
        """Find start/end of the next header"""
        match = mecha_re.search(remaining_text)
        if match:
            next_match = mecha_re.search(remaining_text[match.end():])
            if next_match:
                return (match.start(), next_match.start() + match.end())
            else:
                return (match.start(), len(remaining_text))

    return search.segments(text, offsets_fn)


def get_appendix_letter(title):
    """Pull out appendix letter from header."""
    match = re.match(r'^Appendix ([A-Z])(.*)$', title)
    if match:
        return match.group(1)


def get_section_number(title, part):
    """Pull out section number from header. Assumes proper format"""
    match = re.match(r'^Section %d.(\d+)(.*)$' % part, title)
    if match:
        return match.group(1)


def build_label(label_prefix, match):
    """Create a string to represent this label based on the pyparsing
    match."""
    label = label_prefix + match.section
    for p in range(1,5):
        attr = 'level' + str(p)
        if getattr(match.pars, attr):
            label += "(" + getattr(match.pars, attr) + ")"
    return label


def applicable_paragraph(line):
    """Return a pyparsing match for whatever paragraph is applicable to this
    line (the header)"""
    if not line.endswith("\n"):
        line = line + "\n"
    matches = [match for match, _, _ in header_parser.scanString(line)]
    if matches:
        return matches[0]
