"""Some common combinations"""
from pyparsing import OneOrMore, Optional

from regparser.grammar.atomic import *
from regparser.grammar.utils import keep_pos


part_section = part + Suppress(".") + section
marker_part_section = (
    section_marker.copy().setParseAction(keep_pos).setResultsName("marker")
    + part_section)

depth5_p = em_digit_p | plaintext_level5_p
depth4_p = upper_p + Optional(depth5_p)
depth3_p = roman_p + Optional(depth4_p)
depth2_p = digit_p + Optional(depth3_p)
depth1_p = lower_p + Optional(depth2_p)
any_depth_p = (depth1_p | depth2_p | depth3_p | depth4_p | depth5_p)

depth2_c = roman_c + Optional(upper_c)
depth1_c = "-" + Word(string.digits).setResultsName("c1") + Optional(depth2_c)

section_paragraph = section + depth1_p

mps_paragraph = marker_part_section + Optional(depth1_p)

marker_paragraph = (
    paragraph_marker.copy().setParseAction(keep_pos).setResultsName("marker")
    + depth1_p)

marker_appendix = (
    appendix_marker.copy().setParseAction(keep_pos).setResultsName("marker")
    + appendix)

appendix_with_section = (
    appendix
    + '-' + appendix_section
    + Optional(depth1_p))

marker_comment = (
    comment_marker.copy().setParseAction(keep_pos).setResultsName("marker")
    + (section_paragraph | mps_paragraph) 
    + Optional(depth1_c))


# Multiple
marker_paragraphs = (
    paragraphs_marker
    + any_depth_p.copy().setParseAction(keep_pos).setResultsName("head")
    + OneOrMore(
        conj_phrases
        + any_depth_p.copy().setParseAction(keep_pos).setResultsName(
            "tail", listAllMatches=True)))
mps_paragraphs = (
    section_marker
    + (part_section + depth1_p).setParseAction(keep_pos).setResultsName(
        "head")
    + OneOrMore(
        conj_phrases
        + any_depth_p.copy().setParseAction(keep_pos).setResultsName(
            "tail", listAllMatches=True)))
appendix_with_sections = (
    appendix_with_section.copy().setParseAction(keep_pos).setResultsName(
        "head")
    + OneOrMore(
        conj_phrases
        + any_depth_p.copy().setParseAction(keep_pos).setResultsName(
            "tail", listAllMatches=True)))

_part_section_p = (part_section + Optional(depth1_p)).setParseAction(keep_pos)
marker_sections = (
    sections_marker
    + _part_section_p.copy().setResultsName("head")
    + OneOrMore(
        conj_phrases
        + _part_section_p.copy().setResultsName("tail", listAllMatches=True)))

_comment = (
    (section_paragraph | mps_paragraph) + Optional(depth1_c)
).setParseAction(keep_pos)

marker_comments = (
    comments_marker
    + _comment.copy().setResultsName("head")
    + OneOrMore(
        conj_phrases
        + _comment.copy().setResultsName("tail", listAllMatches=True)))
