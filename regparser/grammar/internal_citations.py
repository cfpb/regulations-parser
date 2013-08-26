#vim: set encoding=utf-8
import string

from pyparsing import OneOrMore, Optional, Regex, Suppress, Word
from pyparsing import ParseResults

from regparser.grammar import common
from regparser.grammar.utils import keep_pos

conj_phrases = Suppress(
    Regex(",|and|or|through")
    + Optional("and")
    + Optional("or"))

paragraph_tail = OneOrMore(
    conj_phrases +
    common.any_depth_p.setParseAction(keep_pos).setResultsName(
        "p_tail", listAllMatches=True))

single_section = (
        common.part_section
        + Optional(common.depth1_p.copy().setParseAction(keep_pos).setResultsName("p_head")
            + Optional(paragraph_tail))
        ).setParseAction(keep_pos)

single_section_with_marker = (
    common.section_marker
    + single_section.setResultsName("without_marker"))

multiple_sections = (
    common.section_markers
    + single_section.setResultsName("s_head")
    + OneOrMore(
        conj_phrases
        + single_section.setResultsName("s_tail", listAllMatches=True)))

single_paragraph = (
    common.paragraph_marker
    + common.any_depth_p.setResultsName("p_head")
    #   veeeery similar to paragraph_tail, but is optional
    + Optional(
        conj_phrases +
        common.any_depth_p.setParseAction(keep_pos).setResultsName(
            "p_tail", listAllMatches=True))
    )

multiple_paragraphs = (
    common.paragraph_markers
    + common.any_depth_p.setResultsName("p_head")
    + paragraph_tail)


regtext_citation = (
    multiple_sections.setResultsName("multiple_sections")
    | single_section_with_marker.setResultsName("single_section")
    | single_paragraph.setResultsName("single_paragraph")
    | multiple_paragraphs.setResultsName("multiple_paragraphs")
)


appendix_citation = (
    Word(string.ascii_uppercase).setResultsName("appendix")
    + Suppress('-')
    + Word(string.digits).setResultsName("section")
    + Optional(common.depth1_p.copy().setParseAction(keep_pos).setResultsName("p_head")
        + Optional(paragraph_tail))
)

single_comment = common.single_comment.copy().setParseAction(keep_pos)

single_comment_with_marker = (
    common.comment_marker
    + single_comment.copy().setResultsName('without_marker')
)

multiple_comments = (
    common.comment_markers
    + single_comment.copy().setResultsName("c_head")
    + OneOrMore(
        conj_phrases
        + single_comment.copy().setResultsName(
            "c_tail", listAllMatches=True)))

comment_citation = (
    multiple_comments.copy().setResultsName("multiple_comments")
    | single_comment_with_marker.copy().setResultsName("single_comment")
)
