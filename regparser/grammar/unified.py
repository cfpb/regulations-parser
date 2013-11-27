#vim: set encoding=utf-8
"""Some common combinations"""
from pyparsing import LineEnd, Literal, OneOrMore, Optional, Suppress, SkipTo

from regparser.grammar import atomic
from regparser.grammar.utils import keep_pos


part_section = atomic.part + Suppress(".") + atomic.section
marker_part_section = (
    atomic.section_marker.copy().setParseAction(keep_pos).setResultsName(
        "marker")
    + part_section)

depth5_p = atomic.em_digit_p | atomic.plaintext_level5_p
depth4_p = atomic.upper_p + Optional(depth5_p)
depth3_p = atomic.roman_p + Optional(depth4_p)
depth2_p = atomic.digit_p + Optional(depth3_p)
depth1_p = atomic.lower_p + Optional(depth2_p)
any_depth_p = (depth1_p | depth2_p | depth3_p | depth4_p | depth5_p)

depth2_c = atomic.roman_c + Optional(atomic.upper_c)
depth1_c = atomic.digit_c + Optional(depth2_c)

section_comment = atomic.section + depth1_c

section_paragraph = atomic.section + depth1_p

mps_paragraph = marker_part_section + Optional(depth1_p)

marker_paragraph = (
    atomic.paragraph_marker.copy().setParseAction(keep_pos).setResultsName(
        "marker")
    + depth1_p)

appendix_with_section = (
    atomic.appendix
    + '-' + atomic.appendix_section
    + Optional(depth1_p))

marker_appendix = (
    atomic.appendix_marker.copy().setParseAction(keep_pos).setResultsName(
        "marker")
    + (appendix_with_section | atomic.appendix))

marker_part = (
    atomic.part_marker.copy().setParseAction(keep_pos).setResultsName("marker")
    + atomic.part)

marker_subpart = (
    atomic.subpart_marker.copy().setParseAction(keep_pos).setResultsName(
        "marker")
    + atomic.subpart)
marker_subpart_title = (
    atomic.subpart_marker.copy().setParseAction(keep_pos).setResultsName(
        "marker")
    + atomic.subpart
    + Suppress(Literal(u"—"))
    + SkipTo(LineEnd()).setResultsName("subpart_title")
)

marker_comment = (
    atomic.comment_marker.copy().setParseAction(keep_pos).setResultsName(
        "marker")
    + (section_comment | section_paragraph | mps_paragraph)
    + Optional(depth1_c)
)

_inner_non_comment = (
    any_depth_p
    | (part_section + Optional(depth1_p))
    | (atomic.section + depth1_p)
    | appendix_with_section | marker_appendix)
multiple_non_comments = (
    (atomic.paragraphs_marker | atomic.paragraph_marker
        | atomic.sections_marker | atomic.section_marker)
    + _inner_non_comment.copy().setParseAction(keep_pos).setResultsName("head")
    + OneOrMore(
        atomic.conj_phrases
        + _inner_non_comment.copy().setParseAction(keep_pos).setResultsName(
            "tail", listAllMatches=True)))
multiple_appendix_section = (
    appendix_with_section.copy().setParseAction(keep_pos).setResultsName(
        "head")
    + OneOrMore(
        atomic.conj_phrases
        + _inner_non_comment.copy().setParseAction(keep_pos).setResultsName(
            "tail", listAllMatches=True)))

multiple_comments = (
    (atomic.comments_marker | atomic.comment_marker)
    + (Optional(atomic.section_marker)
        + _inner_non_comment
        + Optional(depth1_c)).setParseAction(keep_pos).setResultsName("head")
    + OneOrMore(
        atomic.conj_phrases
        + (Optional(_inner_non_comment)
            + Optional(depth1_c)).setParseAction(keep_pos).setResultsName(
            "tail", listAllMatches=True)))
