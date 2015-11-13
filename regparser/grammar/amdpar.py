# vim: set encoding=utf-8
# @todo: this file is becoming too large; refactor
import logging
import string

from pyparsing import CaselessLiteral, FollowedBy, OneOrMore, Optional
from pyparsing import Suppress, Word, LineEnd, ZeroOrMore

from regparser.grammar import atomic, tokens, unified
from regparser.grammar.utils import Marker, WordBoundaries
from regparser.tree.paragraph import p_levels


intro_text_marker = (
    (Marker("introductory") + WordBoundaries(CaselessLiteral("text")))
    | (Marker("subject") + Marker("heading")).setParseAction(lambda _: "text")
)

of_connective = (Marker("of") | Marker("for") | Marker("to"))

passive_marker = (
    Marker("is") | Marker("are") | Marker("was") | Marker("were")
    | Marker("and").setResultsName("and_prefix").setParseAction(
        lambda _: True))


and_token = Marker("and").setParseAction(lambda _: tokens.AndToken())


# Verbs
def generate_verb(word_list, verb, active):
    """Short hand for making tokens.Verb from a list of trigger words"""
    word_list = [CaselessLiteral(w) for w in word_list]
    if not active:
        word_list = [passive_marker + w for w in word_list]
    grammar = reduce(lambda l, r: l | r, word_list)
    grammar = WordBoundaries(grammar)
    grammar = grammar.setParseAction(
        lambda m: tokens.Verb(verb, active, bool(m.and_prefix)))
    return grammar

put_active = generate_verb(
    ['revising', 'revise', 'correcting', 'correct'],
    tokens.Verb.PUT, active=True)

put_passive = generate_verb(
    ['revised', 'corrected'], tokens.Verb.PUT,
    active=False)

post_active = generate_verb(['adding', 'add'], tokens.Verb.POST, active=True)
post_passive = generate_verb(['added'], tokens.Verb.POST, active=False)

delete_active = generate_verb(
    ['removing', 'remove'], tokens.Verb.DELETE, active=True)
delete_passive = generate_verb(['removed'], tokens.Verb.DELETE, active=False)

move_active = generate_verb(
    ['redesignating', 'redesignate'], tokens.Verb.MOVE, active=True)

move_passive = generate_verb(['redesignated'], tokens.Verb.MOVE, active=False)

designate_active = generate_verb(
    ['designate'],
    tokens.Verb.DESIGNATE, active=True)

reserve_active = generate_verb(['reserve', 'reserving'],
                               tokens.Verb.RESERVE, active=True)


#   Context
context_certainty = Optional(
    Marker("in") | Marker("to") | (
        Marker("under") + Optional(
            Marker("subheading")))).setResultsName("certain")

interp = (
    context_certainty + atomic.comment_marker + unified.marker_part
).setParseAction(lambda m: tokens.Context([m.part, 'Interpretations'],
                                          bool(m.certain)))


# This may be a regtext paragraph or it may be an interpretation
paragraph_context = (
    atomic.section
    + unified.depth1_p
    + ~FollowedBy("-")
    ).setParseAction(
    lambda m: tokens.Context([None, None, m.section, m.p1, m.p2, m.p3, m.p4,
                              m.plaintext_p5, m.plaintext_p6]))


def _paren_join(elements):
    return '(' + ')('.join(el for el in elements if el) + ')'


marker_subpart = (
    context_certainty
    + unified.marker_subpart
    ).setParseAction(lambda m: tokens.Context(
        [None, 'Subpart:' + m.subpart], bool(m.certain)))
comment_context_with_section = (
    context_certainty
    #   Confusingly, these are sometimes "comments", sometimes "paragraphs"
    + (Marker("comment") | Marker("paragraph"))
    + atomic.section
    + unified.depth1_p
    + ~FollowedBy("-")
    ).setParseAction(lambda m: tokens.Context(
        [None, 'Interpretations', m.section,
         _paren_join([m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6])
         ], bool(m.certain)))
# Mild modification of the above; catches "under 2(b)"
comment_context_under_with_section = (
    Marker("under")
    + atomic.section
    + unified.depth1_p
    ).setParseAction(lambda m: tokens.Context(
        [None, 'Interpretations', m.section,
         _paren_join([m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6])
         ], True))
comment_context_without_section = (
    context_certainty
    + atomic.paragraph_marker
    + unified.depth2_p
    ).setParseAction(lambda m: tokens.Context(
        [None, 'Interpretations', None,
         _paren_join([m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6])
         ], bool(m.certain)))
appendix = (
    context_certainty
    + unified.marker_appendix
    + Optional(Marker("to") + unified.marker_part)
    ).setParseAction(lambda m: tokens.Context(
        [m.part, 'Appendix:' + m.appendix], bool(m.certain)))
section = (
    context_certainty
    + atomic.section_marker
    + unified.part_section).setParseAction(lambda m: tokens.Context(
        [m.part, None, m.section], bool(m.certain)))


#   Paragraph components (used when not replacing the whole paragraph)
section_heading = Marker("heading").setParseAction(
    lambda _: tokens.Paragraph([], field=tokens.Paragraph.HEADING_FIELD))
intro_text = intro_text_marker.copy().setParseAction(
    lambda _: tokens.Paragraph([], field=tokens.Paragraph.TEXT_FIELD))


#   Paragraphs
comment_p = (
    Word(string.digits).setResultsName("level2")
    + Optional(
        Suppress(".") + Word("ivxlcdm").setResultsName('level3')
        + Optional(
            Suppress(".")
            + Word(string.ascii_uppercase).setResultsName("level4"))))

section_heading_of = (
    Marker("heading") + of_connective
    + unified.marker_part_section
    ).setParseAction(
    lambda m: tokens.Paragraph([m.part, None, m.section],
                               field=tokens.Paragraph.HEADING_FIELD))

section_paragraph_heading_of = (
    Marker("heading") + of_connective
    + (atomic.paragraph_marker | Marker("comment"))
    + atomic.section
    + unified.depth1_p
    ).setParseAction(
    lambda m: tokens.Paragraph([None, 'Interpretations', m.section,
                                _paren_join([m.p1, m.p2, m.p3, m.p4, m.p5])],
                               field=tokens.Paragraph.HEADING_FIELD))

appendix_subheading = (
    Marker("subheading")
    + unified.marker_appendix
    ).setParseAction(
    # Use '()' to pad the label out to what's expected of interpretations
    lambda m: tokens.Paragraph([None, 'Interpretations', m.appendix, '()'],
                               field=tokens.Paragraph.HEADING_FIELD))


paragraph_heading_of = (
    Marker("heading") + of_connective
    + unified.marker_paragraph.copy()
    ).setParseAction(
    lambda m: tokens.Paragraph([None, None, None, m.p1, m.p2, m.p3, m.p4,
                                m.plaintext_p5, m.plaintext_p6],
                               field=tokens.Paragraph.KEYTERM_FIELD))

comment_heading = (
    Marker("heading")
    + Optional(of_connective)
    + atomic.section
    + unified.depth1_p).setParseAction(
    lambda m: tokens.Paragraph([None, "Interpretations", m.section,
                                _paren_join([m.p1, m.p2, m.p3, m.p4, m.p5])],
                               field=tokens.Paragraph.HEADING_FIELD))

intro_text_of = (
    intro_text_marker + of_connective
    + unified.marker_paragraph.copy()
    ).setParseAction(
    lambda m: tokens.Paragraph([None, None, None, m.p1, m.p2, m.p3, m.p4,
                                m.plaintext_p5, m.plaintext_p6],
                               field=tokens.Paragraph.TEXT_FIELD))

intro_text_of_interp = (
    intro_text_marker + of_connective
    + atomic.paragraph_marker
    + comment_p
    ).setParseAction(lambda m: tokens.Paragraph([
        None, 'Interpretations', None, None, m.level2, m.level3,
        m.level4], field=tokens.Paragraph.TEXT_FIELD))

single_par = (
    unified.marker_paragraph
    + Optional(intro_text_marker)
    ).setParseAction(lambda m: tokens.Paragraph([
        None, None, None, m.p1, m.p2, m.p3, m.p4, m.plaintext_p5,
        m.plaintext_p6],
        field=(tokens.Paragraph.TEXT_FIELD if m[-1] == 'text' else None)))
section_single_par = (
    unified.marker_part_section
    + unified.depth1_p
    + Optional(intro_text_marker)
    ).setParseAction(lambda m: tokens.Paragraph([
        m.part, None, m.section, m.p1, m.p2, m.p3, m.p4, m.plaintext_p5,
        m.plaintext_p6],
        field=(tokens.Paragraph.TEXT_FIELD if m[-1] == 'text' else None)))
# Matches "paragraph (a)(1)(i) of § 12.44"
single_par_section = (
    Optional(atomic.paragraph_marker)
    + unified.depth1_p
    + of_connective
    + unified.marker_part_section
    ).setParseAction(lambda m: tokens.Paragraph([
        m.part, None, m.section, m.p1, m.p2, m.p3, m.p4, m.plaintext_p5,
        m.plaintext_p6]))

single_comment_with_section = (
    (Marker("comment") | Marker("paragraph"))
    + atomic.section
    + unified.depth1_p
    + "-"
    + Optional("(") + comment_p + Optional(")")
    ).setParseAction(
    lambda m: tokens.Paragraph(
        [None, 'Interpretations', m.section,
         _paren_join([m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6]),
         m.level2, m.level3, m.level4]))
single_comment_par = (
    atomic.paragraph_marker
    + comment_p
    ).setParseAction(lambda m: tokens.Paragraph([
        None, 'Interpretations', None, None, m.level2, m.level3, m.level4]))


#   Token Lists
def make_multiple(to_repeat):
    """Shorthand for handling repeated tokens ('and', ',', 'through')"""
    return (
        (to_repeat + Optional(intro_text_marker)).setResultsName("head")
        + OneOrMore((
            atomic.conj_phrases
            + to_repeat
            + Optional(intro_text_marker)
        ).setResultsName("tail", listAllMatches=True))
    )


def _through_paren(prev_lab, next_lab):
    """Expand "through" for labels with embedded paragraphs (e.g. 12(c))"""
    lhs, rhs = prev_lab[-1], next_lab[-1]
    lhs_idx, rhs_idx = lhs.rindex('('), rhs.rindex('(')
    # Check if the previous and next labels are "through"-able. For example,
    # we can't compute A-14(a)(2) through B-14(a)(4) nor can we compute
    # A-14(a)(1) through A-14(b)(3)
    if lhs[:lhs_idx] != rhs[:rhs_idx] or prev_lab[:-1] != next_lab[:-1]:
        logging.warning("Bad use of 'through': %s %s", prev_lab, next_lab)
        return []
    else:
        prefix = lhs[:lhs_idx + 1]
        lhs, rhs = lhs[lhs_idx + 1:-1], rhs[rhs_idx + 1:-1]
        for level in p_levels:
            if lhs in level and rhs in level:
                lidx, ridx = level.index(lhs), level.index(rhs)
                if lidx < ridx:
                    return [tokens.Paragraph(prev_lab[:-1]
                                             + [prefix + level[i] + ')'])
                            for i in range(lidx + 1, ridx)]
        logging.warning("Error with 'through': %s %s", prev_lab, next_lab)
        return []


def _through_sect(prev_lab, next_lab):
    """Expand "through" for labels ending in a section number."""
    return [tokens.Paragraph(prev_lab[:2] + [str(i)])
            for i in range(int(prev_lab[-1]) + 1, int(next_lab[-1]))]


def _through_paragraph(prev_lab, next_lab):
    """Expand "through" for labels ending in a paragraph."""
    depth = len(prev_lab)
    start = p_levels[depth-4].index(prev_lab[-1]) + 1
    end = p_levels[depth-4].index(next_lab[-1])
    return [tokens.Paragraph(prev_lab[:depth-1] + [p_levels[depth-4][i]])
            for i in range(start, end)]


def make_par_list(listify):
    """Shorthand for turning a pyparsing match into a tokens.Paragraph"""
    def curried(match=None):
        pars = []
        matches = [match.head] + list(match.tail)
        for match in matches:
            match_as_list = listify(match)
            next_par = tokens.Paragraph(match_as_list)
            next_lab = next_par.label
            if match[-1] == 'text':
                next_par.field = tokens.Paragraph.TEXT_FIELD
            if match.through:
                #   Iterate through, creating paragraph tokens
                prev_lab = pars[-1].label
                if '(' in prev_lab[-1] and '(' in next_lab[-1]:
                    pars.extend(_through_paren(prev_lab, next_lab))
                elif len(prev_lab) == 3:
                    pars.extend(_through_sect(prev_lab, next_lab))
                elif len(prev_lab) > 3:
                    pars.extend(_through_paragraph(prev_lab, next_lab))
            pars.append(next_par)
        return tokens.TokenList(pars)
    return curried

multiple_sections = (
    atomic.sections_marker
    + make_multiple(unified.part_section)
    ).setParseAction(make_par_list(lambda m: [m.part, None, m.section]))


multiple_paragraph_sections = (
    atomic.section_marker
    + make_multiple(Optional(unified.part_section) + unified.any_depth_p)
    ).setParseAction(make_par_list(lambda m: [
        m.part, None, m.section, m.p1, m.p2, m.p3, m.p4, m.plaintext_p5,
        m.plaintext_p6]))


appendix_section = (
    unified.appendix_with_section
    ).copy().setParseAction(
    lambda m: tokens.Paragraph(
        [None, 'Appendix:' + m.appendix, m.appendix_section]))

appendix_section_heading_of = (
    Marker("heading") + of_connective
    + unified.appendix_with_section
    ).copy().setParseAction(
    lambda m: tokens.Paragraph(
        [None, 'Appendix:' + m.appendix, m.appendix_section],
        field=tokens.Paragraph.HEADING_FIELD))

multiple_appendices = make_multiple(
    unified.appendix_with_section
    ).setParseAction(make_par_list(
        lambda m: [None, 'Appendix:' + m.appendix, m.appendix_section]))

multiple_comment_pars = (
    atomic.paragraphs_marker
    + make_multiple(comment_p)
    ).setParseAction(make_par_list(lambda m: [
        None, 'Interpretations', None, None, m.level2, m.level3, m.level4]))

#   Not a context as one wouldn't list these for contextual purposes
multiple_comments = (
    Marker("comments")
    + make_multiple(atomic.section + unified.depth1_p)
    ).setParseAction(make_par_list(
        lambda m: [None, 'Interpretations', m.section,
                   _paren_join([m.p1, m.p2, m.p3, m.p4,
                                m.plaintext_p5, m.plaintext_p6])]))

multiple_interp_entries = (
    Marker("entries") + Marker("for")
    + (atomic.section + unified.depth1_p).setResultsName("head")
    + OneOrMore((
        atomic.conj_phrases
        + unified.any_depth_p
    ).setResultsName("tail", listAllMatches=True))
    ).setParseAction(make_par_list(
        lambda m: [None, None, m.section, m.p1, m.p2, m.p3, m.p4,
                   m.plaintext_p5, m.plaintext_p6]))

multiple_paragraphs = (
    (atomic.paragraphs_marker | atomic.paragraph_marker)
    + make_multiple(unified.any_depth_p)
    ).setParseAction(make_par_list(lambda m: [
        m.part, None, m.section, m.p1, m.p2, m.p3, m.p4, m.plaintext_p5,
        m.plaintext_p6]))


def tokenize_override_ps(match):
    """ Create token.Paragraphs for the given override match """
    # Part, Section or Appendix, p1, p2, p3, p4, p5, p6
    match_list = list(match)
    par_list = [match.part, None, None, None, None, None, None, None]

    if match.section:
        par_list[1] = match.section
    elif match.appendix:
        par_list[1] = "Appendix:" + match.appendix

    # Set paragraph depths
    for p in match_list[2:]:
        par_list[match_list.index(p)] = p

    par = tokens.Paragraph(par_list)
    return [par]


override_label = (
    Suppress("[")
    + Marker("label") + Suppress(":")
    + atomic.part
    + Suppress("-")
    + (atomic.section | atomic.appendix)
    + ZeroOrMore(Suppress("-") + Word(string.ascii_lowercase + string.digits))
    + Suppress("]")
    ).setParseAction(tokenize_override_ps)


#   grammar which captures all of these possibilities
token_patterns = (
    put_active | put_passive | post_active | post_passive
    | delete_active | delete_passive | move_active | move_passive
    | designate_active | reserve_active

    | interp | marker_subpart | appendix
    | comment_context_with_section | comment_context_without_section
    | comment_context_under_with_section
    | paragraph_heading_of | section_heading_of | intro_text_of
    | appendix_section_heading_of
    | intro_text_of_interp
    | comment_heading | appendix_subheading | section_paragraph_heading_of
    # Must come after other headings as it is a catch-all
    | section_heading
    | multiple_paragraph_sections | section_single_par
    | multiple_interp_entries

    | multiple_sections | multiple_paragraphs | multiple_appendices
    | multiple_comment_pars | multiple_comments
    #   Must come after multiple_appendices
    | appendix_section
    #   Must come after multiple_pars
    | single_par_section | single_par
    #   Must come after multiple_comment_pars
    | single_comment_with_section | single_comment_par
    #   Must come after section_single_par
    | section
    #   Must come after intro_text_of
    | intro_text

    # Finally allow for an explicit override label
    | override_label

    | paragraph_context
    | and_token
)

subpart_label = (atomic.part + Suppress('-')
                 + atomic.subpart_marker + Suppress(':')
                 + Word(string.ascii_uppercase, max=1)
                 + LineEnd())
