#vim: set encoding=utf-8
import string
from pyparsing import OneOrMore, Optional, Regex, Suppress, Word

lower_p = (
        Suppress("(") 
        + Word(string.ascii_lowercase).setResultsName("level1") 
        + Suppress(")"))
digit_p = (
        Suppress("(") 
        + Word(string.digits).setResultsName("level2") 
        + Suppress(")"))
roman_p = (
        Suppress("(") 
        + Word("ivxlcdm").setResultsName("level3") + 
        Suppress(")"))
upper_p = (
        Suppress("(") 
        + Word(string.ascii_uppercase).setResultsName("level4") 
        + Suppress(")"))

depth3_p = roman_p + Optional(upper_p)
depth2_p = digit_p + Optional(depth3_p)
depth1_p = lower_p + Optional(depth2_p)

any_depth_p = (depth1_p | depth2_p | depth3_p | upper_p)

and_phrases = Suppress(Regex(",|and|or") + Optional("and"))

paragraph_tail = OneOrMore(and_phrases 
        + any_depth_p.setResultsName("p_tail", listAllMatches=True))

single_section = (
        Word(string.digits).setResultsName("section")
        + Suppress(".")
        + Word(string.digits).setResultsName("part")
        + Optional(depth1_p.setResultsName("p_head") 
            + Optional(paragraph_tail)))

multiple_sections = (
        Suppress(u"§§")
        + single_section.setResultsName("s_head")
        + OneOrMore(and_phrases 
            + single_section.setResultsName("s_tail", listAllMatches=True)))

single_paragraph = Suppress("paragraph") + any_depth_p

multiple_paragraphs = (
        Suppress("paragraphs") 
        + any_depth_p.setResultsName("p_head")
        + paragraph_tail)

any_citation = (
    multiple_sections.setResultsName("multiple_sections") 
    | single_section.setResultsName("single_section")
    | single_paragraph.setResultsName("single_paragraph") 
    | multiple_paragraphs.setResultsName("multiple_paragraphs"))
