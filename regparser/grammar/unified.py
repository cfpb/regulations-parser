# vim: set encoding=utf-8
"""Some common combinations"""
import string

from pyparsing import Empty, FollowedBy, LineEnd, Literal, OneOrMore, Optional
from pyparsing import Suppress, SkipTo, Word, ZeroOrMore

from regparser.grammar import atomic
from regparser.grammar.utils import keep_pos, Marker

period_section = Suppress(".") + atomic.section
part_section = atomic.part + period_section
marker_part_section = (
    atomic.section_marker.copy().setParseAction(keep_pos).setResultsName(
        "marker")
    + part_section)

depth6_p = atomic.em_roman_p | atomic.plaintext_level6_p
depth5_p = (
    (atomic.em_digit_p | atomic.plaintext_level5_p)
    + Optional(depth6_p))
depth4_p = atomic.upper_p + Optional(depth5_p)
depth3_p = atomic.roman_p + Optional(depth4_p)
depth2_p = atomic.digit_p + Optional(depth3_p)
depth1_p = atomic.lower_p + ~FollowedBy(atomic.upper_p) + Optional(depth2_p)
any_depth_p = depth1_p | depth2_p | depth3_p | depth4_p | depth5_p | depth6_p

depth3_c = atomic.upper_c + Optional(atomic.em_digit_c)
depth2_c = atomic.roman_c + Optional(depth3_c)
depth1_c = atomic.digit_c + Optional(depth2_c)
any_a = atomic.upper_a | atomic.digit_a

section_comment = atomic.section + depth1_c

section_paragraph = atomic.section + depth1_p

mps_paragraph = marker_part_section + Optional(depth1_p)
ps_paragraph = part_section + Optional(depth1_p)
part_section_paragraph = (
    atomic.part + Suppress(".") + atomic.section + depth1_p)


part_section + Optional(depth1_p)

m_section_paragraph = (
    atomic.paragraph_marker.copy().setParseAction(
        keep_pos).setResultsName("marker")
    + atomic.section
    + depth1_p)

marker_paragraph = (
    (atomic.paragraph_marker | atomic.paragraphs_marker).setParseAction(
        keep_pos).setResultsName("marker")
    + depth1_p)


def appendix_section(match):
    """Appendices may have parenthetical paragraphs in its section number."""
    if match.appendix_digit:
        lst = list(match)
        pars = lst[lst.index(match.appendix_digit) + 1:]
        section = match.appendix_digit
        if pars:
            section += '(' + ')('.join(el for el in pars) + ')'
        return section
    else:
        return None

appendix_with_section = (
    atomic.appendix
    + '-'
    + (atomic.appendix_digit
       + ZeroOrMore(atomic.lower_p | atomic.roman_p | atomic.digit_p
                    | atomic.upper_p)
       ).setParseAction(appendix_section).setResultsName("appendix_section"))

# "the" appendix implies there's only one, so it better be appendix A
section_of_appendix_to_this_part = (
    atomic.section_marker
    + atomic.upper_roman_a.copy().setResultsName("appendix_section")
    + Literal("of the appendix to this part").setResultsName(
        "appendix").setParseAction(lambda: 'A')
)

appendix_par_of_part = (
    atomic.paragraph_marker.copy().setParseAction(keep_pos).setResultsName(
        "marker")
    + (Word(string.ascii_uppercase) | Word(string.digits))
    + Optional(any_a) + Optional(any_a)
    + Suppress(".")
    + Marker("of") + Marker("part")
    + atomic.upper_roman_a)

appendix_with_part = (
    atomic.appendix_marker.copy().setParseAction(keep_pos).setResultsName(
        "marker")
    + atomic.appendix
    + Suppress(",") + Marker('part')
    + atomic.upper_roman_a
    + Optional(any_a) + Optional(any_a) + Optional(any_a))

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
    + ((Suppress(Literal(u"—"))
        + SkipTo(LineEnd()).setResultsName("subpart_title"))
       | (Literal("[Reserved]").setResultsName("subpart_title")))
)

marker_comment = (
    atomic.comment_marker.copy().setParseAction(keep_pos).setResultsName(
        "marker")
    + (section_comment | section_paragraph | ps_paragraph | mps_paragraph)
    + Optional(depth1_c)
)


_inner_non_comment = (
    any_depth_p
    | (part_section + Optional(depth1_p))
    | (atomic.section + depth1_p)
    | appendix_with_section | marker_appendix)

_inner_non_comment_tail = OneOrMore(
    Optional(Suppress('('))
    + atomic.conj_phrases
    + _inner_non_comment.copy().setParseAction(keep_pos).setResultsName(
        "tail", listAllMatches=True)
    + Optional(Suppress(')')))

multiple_non_comments = (
    (atomic.paragraphs_marker | atomic.paragraph_marker
        | atomic.sections_marker | atomic.section_marker)
    + _inner_non_comment.copy().setParseAction(keep_pos).setResultsName("head")
    + _inner_non_comment_tail)

multiple_section_paragraphs = (
    section_paragraph.copy().setParseAction(keep_pos).setResultsName("head")
    + _inner_non_comment_tail)

multiple_period_sections = (
    atomic.sections_marker
    + part_section.copy().setParseAction(keep_pos).setResultsName("head")
    + OneOrMore(
        atomic.conj_phrases
        + period_section.copy().setParseAction(keep_pos).setResultsName(
            "tail", listAllMatches=True)))

multiple_appendix_section = (
    appendix_with_section.copy().setParseAction(keep_pos).setResultsName(
        "head")
    + OneOrMore(
        Optional(Suppress('('))
        + atomic.conj_phrases
        + _inner_non_comment.copy().setParseAction(keep_pos).setResultsName(
            "tail", listAllMatches=True)
        + Optional(Suppress(')'))))

#   Use "Empty" so we don't rename atomic.appendix
multiple_appendices = (
    atomic.appendices_marker
    + (atomic.appendix + Empty()).setParseAction(keep_pos).setResultsName(
        "head")
    + OneOrMore(
        atomic.conj_phrases
        + (atomic.appendix + Empty()).setParseAction(keep_pos).setResultsName(
            "tail", listAllMatches=True)))

multiple_comments = (
    (atomic.comments_marker | atomic.comment_marker)
    + (Optional(atomic.section_marker)
        + _inner_non_comment
        + Optional(depth1_c)).setParseAction(keep_pos).setResultsName("head")
    + OneOrMore(
        Optional(Suppress('('))
        + atomic.conj_phrases
        + ((_inner_non_comment + Optional(depth1_c))
            | depth1_c).setParseAction(keep_pos).setResultsName(
            "tail", listAllMatches=True)
        + Optional(Suppress(')'))))

# e.g. 12 CFR 1005.10
internal_cfr_p = (
    atomic.title
    + Suppress("CFR")
    + atomic.part
    + Suppress('.')
    + atomic.section
    + Optional(depth1_p))

# e.g. 12 CFR 1005.10, 1006.21, and 1010.10
multiple_cfr_p = (
    internal_cfr_p.copy().setParseAction(keep_pos).setResultsName("head")
    + OneOrMore(
        atomic.conj_phrases
        + (atomic.part
           + Suppress('.')
           + atomic.section
           + Optional(depth1_p)).setParseAction(keep_pos).setResultsName(
               "tail", listAllMatches=True)))

notice_cfr_p = (
    Suppress(atomic.title)
    + Suppress("CFR")
    + Optional(Suppress(atomic.part_marker | atomic.parts_marker))
    + OneOrMore(
        atomic.part
        + Optional(Suppress(','))
        + Optional(Suppress('and'))
    )
)
