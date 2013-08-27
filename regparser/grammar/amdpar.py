#vim: set encoding=utf-8
import string

from pyparsing import CaselessLiteral, Literal, OneOrMore, Optional, Regex
from pyparsing import Suppress, Word, WordEnd, WordStart

from regparser.grammar import common, tokens
from regparser.grammar.common import WordBoundaries
from regparser.tree.paragraph import p_levels


#Verbs
def generate_verb(word_list, verb, active):
    """Short hand for making tokens.Verb from a list of trigger words"""
    grammar = reduce(
        lambda l, r: l | r,
        map(lambda w: CaselessLiteral(w), word_list))
    grammar = WordBoundaries(grammar)
    grammar = grammar.setParseAction(lambda _: tokens.Verb(verb, active))
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


#   Context
context_certainty = Optional(
    common.Marker("in") | (
        common.Marker("under") + Optional(
            common.Marker("subheading")))).setResultsName("certain")

interp = (
    context_certainty
    + common.marker_interpretation
    ).setParseAction(lambda m: tokens.Context(
    [m.part, 'Interpretations'], bool(m.certain)))

marker_subpart = (
    context_certainty
    + common.marker_subpart
    ).setParseAction(lambda m: tokens.Context(
    [None, 'Subpart:' + m.subpart], bool(m.certain)))
comment_context_with_section = (
    context_certainty
    #   Confusingly, these are sometimes "comments", sometimes "paragraphs"
    + (common.Marker("comment") | common.Marker("paragraph"))
    + common.section
    + common.depth1_p
    ).setParseAction(lambda m: tokens.Context([None, 'Interpretations', 
        m.section, '(' + ')('.join(p for p in [m.level1, m.level2, m.level3, 
            m.level4, m.level5] if p) + ')'], bool(m.certain)))
comment_context_without_section = (
    context_certainty
    + common.paragraph_marker
    + common.depth2_p
    ).setParseAction(lambda m: tokens.Context([None, 'Interpretations', None, 
        '(' + ')('.join(p for p in [m.level2, m.level3, m.level4, m.level5] 
            if p) + ')'], bool(m.certain)))
appendix = (
    context_certainty
    + common.appendix_marker
    + common.appendix_letter
    + Optional(common.Marker("to") + common.marker_part)
    ).setParseAction(lambda m: tokens.Context(
        [m.part, 'Appendix:' + m.letter], bool(m.certain)))
section = (
    context_certainty
    + common.section_marker 
    + common.part_section).setParseAction(lambda m: tokens.Context(
        [m.part, None, m.section], bool(m.certain)))


#   Paragraph components (used when not replacing the whole paragraph)
section_heading = common.Marker("heading").setParseAction(lambda _: 
    tokens.Paragraph([], field=tokens.Paragraph.HEADING_FIELD))
intro_text = common.intro_text.copy().setParseAction(
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
    common.Marker("heading") + common.Marker("of")
    + common.marker_part_section
    ).setParseAction(lambda m: tokens.Paragraph([m.part, None, m.section], 
        field=tokens.Paragraph.TEXT_FIELD))
intro_text_of = (
    common.intro_text + common.Marker("of")
    + common.marker_paragraph.copy()
    ).setParseAction(lambda m: tokens.Paragraph([None, None, None,
        m.level1, m.level2, m.level3, m.level4, m.level5], 
        field=tokens.Paragraph.TEXT_FIELD))
single_par = (
    common.marker_paragraph
    + Optional(common.intro_text)
    ).setParseAction(lambda m: tokens.Paragraph([None, None, None,
        m.level1, m.level2, m.level3, m.level4, m.level5], 
        field=(tokens.Paragraph.TEXT_FIELD if m[-1] == 'text' else None)))
section_single_par = (
    common.marker_part_section
    + common.depth1_p
    + Optional(common.intro_text)
    ).setParseAction(lambda m: tokens.Paragraph([m.part, None,
        m.section, m.level1, m.level2, m.level3,
        m.level4, m.level5],
        field=(tokens.Paragraph.TEXT_FIELD if m[-1] == 'text' else None)))
single_comment_par=(
    common.paragraph_marker
    + comment_p
    ).setParseAction(lambda m: tokens.Paragraph([None,
        'Interpretations', None, None, m.level2, m.level3,
        m.level4]))


#   Token Lists
def make_multiple(to_repeat):
    """Shorthand for handling repeated tokens ('and', ',', 'through')"""
    return (
        (to_repeat + Optional(common.intro_text)).setResultsName("head")
        + OneOrMore((
            (common.conj_phrases | common.through).setResultsName("conj")
            + to_repeat
            + Optional(common.intro_text)
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
            if match.conj == 'through':
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
    common.section_markers
    + make_multiple(common.part_section)
    ).setParseAction(make_par_list(lambda m: [m.part, None, m.section]))

multiple_pars = (
    common.paragraph_markers
    + make_multiple(common.depth1_p)
    ).setParseAction(make_par_list(lambda m: [m.part, None, m.section,
        m.level1, m.level2, m.level3, m.level4, m.level5]))

multiple_appendices = make_multiple(common.appendix_shorthand).setParseAction(
    make_par_list(lambda m: [None, 'Appendix:' + m.letter, m.section,
        m.level1, m.level2, m.level3, m.level4, m.level5]))

multiple_comment_pars = (
    common.paragraph_markers
    + make_multiple(comment_p)
    ).setParseAction(make_par_list(lambda m: [None, 'Interpretations', None,
        None, m.level2, m.level3, m.level4]))

#   Not a context as one wouldn't list these for contextual purposes
multiple_comments = (
    common.Marker("comments")
    + make_multiple(common.section + common.depth1_p)
    ).setParseAction(make_par_list(lambda m: [None, 'Interpretations',
        m.section, '(' + ')('.join(p for p in [m.level1, m.level2, m.level3,
            m.level4, m.level5] if p) + ')']))


#   grammar which captures all of these possibilities
token_patterns = (
    put_active | put_passive | post_active | post_passive
    | delete_active | delete_passive | move_active | move_passive

    | interp | marker_subpart | appendix
    | comment_context_with_section | comment_context_without_section

    | section_heading | section_heading_of | intro_text_of
    | single_par | section_single_par

    | multiple_sections | multiple_pars | multiple_appendices
    | multiple_comment_pars | multiple_comments
    #   Must come after multiple_comment_pars
    | single_comment_par
    #   Must come after section_single_par
    | section
    #   Must come after intro_text_of
    | intro_text
)
