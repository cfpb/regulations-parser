from pyparsing import Word, Optional, LineStart, LineEnd, SkipTo
import re
from parser import search
import string

def find_next_section_offsets(text, part):
    """Find the start/end of the next section"""
    def find_start(text):
        return search.find_start(text, u"Section", ur"%d.\d+" % part)
    return search.find_offsets(text, find_start)
def sections(text, part):
    """Return a list of section offsets."""
    def offsets_fn(remaining_text, idx, excludes):
        return find_next_section_offsets(remaining_text, part)
    return search.segments(text, offsets_fn)
def get_section_number(title, part):
    """Pull out section number from header. Assumes proper format"""
    return re.match(r'^Section %d.(\d+)(.*)$' % part, title).group(1)

def find_next_appendix_offsets(text):
    """Find the start/end of the next appendix"""
    def find_start(text):
        return search.find_start(text, u"Appendix", ur"[A-Z]")
    return search.find_offsets(text, find_start)
def appendicies(text):
    """Return a list of appendix offsets."""
    def offsets_fn(remaining_text, idx, excludes):
        return find_next_appendix_offsets(remaining_text)
    return search.segments(text, offsets_fn)
def get_appendix_letter(title):
    """Pull out appendix letter from header. Assumes proper format"""
    return re.match(r'^Appendix ([A-Z])(.*)$', title).group(1)

def applicable_offsets(plain_text, section):
    """Return offsets for the text which is applicable only to a certain
    paragraph/keyterm in the regulation."""
    starts = [start for _,start,_ in 
            _applicable_parser(section).scanString(plain_text)]
    starts.append(len(plain_text))
    for i in range(1, len(starts)):
        starts[i-1] = (starts[i-1], starts[i])
    starts = starts[:-1]
    return starts

def build_label(label_prefix, match):
    """Create a string to represent this label based on the pyparsing
    match."""
    label = str(label_prefix)   # copy
    for p in range(1,5):
        attr = 'paragraph' + str(p)
        if getattr(match, attr):
            label += "(" + getattr(match, attr).id + ")"
    return label

lower_alpha_sub = "(" + Word(string.ascii_lowercase).setResultsName("id") + ")"
upper_alpha_sub = "(" + Word(string.ascii_uppercase).setResultsName("id") + ")"
roman_sub = "(" + Word("ivxlcdm").setResultsName("id") + ")"
digit_sub = "(" + Word(string.digits).setResultsName("id") + ")"

def _applicable_parser(section):
    """Return a parser for lines which indicate where this interpretation is
    applicable."""
    paragraph = (str(section) + lower_alpha_sub.setResultsName("paragraph1") + 
            Optional(digit_sub.setResultsName("paragraph2") +
                Optional(roman_sub.setResultsName("paragraph3") + 
                    Optional(upper_alpha_sub.setResultsName("paragraph4")))))

    whole_par = LineStart() + ("Paragraph" + paragraph)
    keyterm = (LineStart() + paragraph + 
            SkipTo("\n").setResultsName("term") + LineEnd())

    return whole_par.setResultsName("whole") | keyterm.setResultsName("keyterm")

def applicable_paragraph(line, section):
    """Return a pyparsing match for whatever paragraph is applicable to this
    line (the header)"""
    if not line.endswith("\n"):
        line = line + "\n"
    matches = [match for match, _, _ in 
            _applicable_parser(section).scanString(line)]
    if matches:
        return matches[0]
