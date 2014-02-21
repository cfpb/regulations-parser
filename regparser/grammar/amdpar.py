#vim: set encoding=utf-8
import string

from pyparsing import CaselessLiteral, FollowedBy, OneOrMore, Optional
from pyparsing import Suppress, Word, LineEnd

from regparser.grammar import atomic, tokens, unified
from regparser.grammar.utils import Marker, WordBoundaries
from regparser.tree.paragraph import p_levels


intro_text_marker = (
    (Marker("introductory") + WordBoundaries(CaselessLiteral("text")))
    | (Marker("subject") + Marker("heading")).setParseAction(lambda _: "text")
)


passive_marker = (
    Marker("is") | Marker("are") | Marker("was") | Marker("were")
    | Marker("and").setResultsName("and_prefix").setParseAction(
        lambda _: True))


and_token = Marker("and").setParseAction(lambda _: tokens.AndToken())


#Verbs
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
    Marker("in") | (
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
         _paren_join([m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6])], bool(m.certain)))
# Mild modification of the above; catches "under 2(b)"
comment_context_under_with_section = (
    Marker("under")
    + atomic.section
    + unified.depth1_p
    ).setParseAction(lambda m: tokens.Context(
        [None, 'Interpretations', m.section,
         _paren_join([m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6])], True))
comment_context_without_section = (
    context_certainty
    + atomic.paragraph_marker
    + unified.depth2_p
    ).setParseAction(lambda m: tokens.Context(
        [None, 'Interpretations', None,
         _paren_join([m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6])], bool(m.certain)))
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
section_heading = Marker("heading").setParseAction(lambda _:
    tokens.Paragraph([], field=tokens.Paragraph.HEADING_FIELD))
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
    Marker("heading") + (Marker("of") | Marker("for"))
    + unified.marker_part_section
    ).setParseAction(
    lambda m: tokens.Paragraph([m.part, None, m.section],
                               field=tokens.Paragraph.HEADING_FIELD))

paragraph_heading_of = (
    Marker("heading") + Marker("of")
    + unified.marker_paragraph.copy()
    ).setParseAction(lambda m: tokens.Paragraph([None, None, None,
        m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6],
        field=tokens.Paragraph.KEYTERM_FIELD))

comment_heading = (
    Marker("heading")
    + Optional(Marker("of") | Marker("for"))
    + atomic.section
    + unified.depth1_p).setParseAction(
    lambda m: tokens.Paragraph([None, "Interpretations", m.section,
                                _paren_join([m.p1, m.p2, m.p3, m.p4, m.p5])],
                               field=tokens.Paragraph.HEADING_FIELD)) 

intro_text_of = (
    intro_text_marker + Marker("of")
    + unified.marker_paragraph.copy()
    ).setParseAction(lambda m: tokens.Paragraph([None, None, None,
        m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6],
        field=tokens.Paragraph.TEXT_FIELD))
single_par = (
    unified.marker_paragraph
    + Optional(intro_text_marker)
    ).setParseAction(lambda m: tokens.Paragraph([None, None, None,
        m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6],
        field=(tokens.Paragraph.TEXT_FIELD if m[-1] == 'text' else None)))
section_single_par = (
    unified.marker_part_section
    + unified.depth1_p
    + Optional(intro_text_marker)
    ).setParseAction(lambda m: tokens.Paragraph([m.part, None,
        m.section, m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6],
        field=(tokens.Paragraph.TEXT_FIELD if m[-1] == 'text' else None)))
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
    ).setParseAction(lambda m: tokens.Paragraph([None,
        'Interpretations', None, None, m.level2, m.level3,
        m.level4]))


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


def make_par_list(listify):
    """Shorthand for turning a pyparsing match into a tokens.Paragraph"""
    def curried(match=None):
        pars = []
        matches = [match.head] + list(match.tail)
        for match in matches:
            match_as_list = listify(match)
            next_par = tokens.Paragraph(match_as_list)
            if match[-1] == 'text':
                next_par.field = tokens.Paragraph.TEXT_FIELD
            if match.through:
                #   Iterate through, creating paragraph tokens
                prev = pars[-1]
                if len(prev.label) == 3:
                    # Section numbers
                    for i in range(int(prev.label[-1]) + 1,
                            int(next_par.label[-1])):
                        pars.append(tokens.Paragraph(prev.label[:2]
                            + [str(i)]))
                if len(prev.label) > 3:
                    # Paragraphs
                    depth = len(prev.label)
                    start = p_levels[depth-4].index(prev.label[-1]) + 1
                    end = p_levels[depth-4].index(next_par.label[-1])
                    for i in range(start, end):
                        pars.append(tokens.Paragraph(prev.label[:depth-1]
                            + [p_levels[depth-4][i]]))
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
    ).setParseAction(make_par_list(lambda m: [m.part, None, m.section,
        m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6]))

multiple_appendices = make_multiple(unified.appendix_with_section
    ).setParseAction(make_par_list(
        lambda m: [None, 'Appendix:' + m.appendix, m.appendix_section, m.p1,
                   m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6]))

multiple_comment_pars = (
    atomic.paragraphs_marker
    + make_multiple(comment_p)
    ).setParseAction(make_par_list(lambda m: [None, 'Interpretations', None,
        None, m.level2, m.level3, m.level4]))

#   Not a context as one wouldn't list these for contextual purposes
multiple_comments = (
    Marker("comments")
    + make_multiple(atomic.section + unified.depth1_p)
    ).setParseAction(make_par_list(
        lambda m: [None, 'Interpretations', m.section,
                   _paren_join([
                    m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6])]))

multiple_interp_entries = (
    Marker("entries") + Marker("for")
    + (atomic.section + unified.depth1_p).setResultsName("head")
    + OneOrMore((
        atomic.conj_phrases
        + unified.any_depth_p
    ).setResultsName("tail", listAllMatches=True))
    ).setParseAction(make_par_list(
    lambda m: [None, None, m.section, m.p1, m.p2, m.p3, m.p4, m.plaintext_p5,
               m.plaintext_p6]))

multiple_paragraphs = (
    (atomic.paragraphs_marker | atomic.paragraph_marker)
    + make_multiple(unified.any_depth_p)
    ).setParseAction(make_par_list(lambda m: [m.part, None, m.section,
        m.p1, m.p2, m.p3, m.p4, m.plaintext_p5, m.plaintext_p6]))


#   grammar which captures all of these possibilities
token_patterns = (
    put_active | put_passive | post_active | post_passive
    | delete_active | delete_passive | move_active | move_passive
    | designate_active | reserve_active

    | interp | marker_subpart | appendix
    | comment_context_with_section | comment_context_without_section
    | comment_context_under_with_section

    | paragraph_heading_of | section_heading_of | intro_text_of
    | comment_heading
    # Must come after other headings as it is a catch-all
    | section_heading
    | multiple_paragraph_sections | section_single_par
    | multiple_interp_entries

    | multiple_sections | multiple_paragraphs | multiple_appendices
    | multiple_comment_pars | multiple_comments
    #   Must come after multiple_pars
    | single_par
    #   Must come after multiple_comment_pars
    | single_comment_with_section | single_comment_par
    #   Must come after section_single_par
    | section
    #   Must come after intro_text_of
    | intro_text

    | paragraph_context
    | and_token
)

subpart_label = (atomic.part + Suppress('-')
                 + atomic.subpart_marker + Suppress(':')
                 + Word(string.ascii_uppercase, max=1)
                 + LineEnd())
