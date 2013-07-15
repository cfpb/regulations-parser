#vim: set encoding=utf-8
import string

from pyparsing import CaselessLiteral, Literal, OneOrMore, Optional, Regex
from pyparsing import Suppress, Word, WordEnd, WordStart

from regparser.grammar import common, tokens
from regparser.tree.paragraph import p_levels

section = (
        Suppress(Regex(u"§|Section"))
        + Word(string.digits).setResultsName("part")
        + Suppress(".")
        + Word(string.digits).setResultsName("section"))


paragraph = (
        Word(string.digits).setResultsName("section")
        + common.depth1_p.setResultsName("paragraphs"))


supplement_i = (
        Suppress(Literal("Supplement I to Part"))
        + Word(string.digits).setResultsName("part"))


applicable = section | paragraph


sectno = (
        section.setResultsName("regtext") 
        | supplement_i.setResultsName("interpretation"))

sections_through = (
        common.section_markers 
        + common.part_section.setResultsName("lhs")
        + common.through
        + common.part_section.setResultsName("rhs")
)

appendix_through = (
        common.appendix_shorthand
        + common.through
        + common.appendix_shorthand
)

text = Suppress(
        (Literal("introductory") + Literal("text"))
)




def WordBoundaries(grammar):
    return WordStart() + grammar + WordEnd()


put_active = WordBoundaries(
        CaselessLiteral("revising") | CaselessLiteral("revise")
        | CaselessLiteral("correcting") | CaselessLiteral("correct")
        ).setParseAction(lambda _: tokens.Verb("PUT", True))
put_passive = WordBoundaries(
        CaselessLiteral("revised") | CaselessLiteral("corrected")
        ).setParseAction(lambda _: tokens.Verb("PUT", False))

post_active = WordBoundaries(
        CaselessLiteral("adding") | CaselessLiteral("add")
        ).setParseAction(lambda _: tokens.Verb("POST", True))
post_passive = WordBoundaries(
        CaselessLiteral("added")
        ).setParseAction(lambda _: tokens.Verb("POST", False))

delete_active = WordBoundaries(
        CaselessLiteral("removing") | CaselessLiteral("remove")
        ).setParseAction(lambda _: tokens.Verb("DELETE", True))
delete_passive = WordBoundaries(
        CaselessLiteral("removed")
        ).setParseAction(lambda _: tokens.Verb("DELETE", False))

move_active = WordBoundaries(
        CaselessLiteral("redesignating") | CaselessLiteral("redesignate")
        ).setParseAction(lambda _: tokens.Verb("MOVE", True))
move_passive = WordBoundaries(
        CaselessLiteral("redesignated")
        ).setParseAction(lambda _: tokens.Verb("MOVE", False))


section = common.marker_part_section.setParseAction(
        lambda match: tokens.Section(match.part, match.section))
marker_subpart = (
        WordBoundaries(CaselessLiteral("subpart"))
        +  Word(string.ascii_uppercase)
        ).setParseAction(lambda match: tokens.Subpart(match[1]))



section_heading = (
        WordBoundaries(CaselessLiteral("section"))
        + WordBoundaries(CaselessLiteral("heading"))
        ).setParseAction(lambda _: tokens.SectionHeading())
section_heading_of = (
        WordBoundaries(CaselessLiteral("section"))
        + WordBoundaries(CaselessLiteral("heading"))
        + WordBoundaries(CaselessLiteral("of"))
        ).setParseAction(lambda _: tokens.SectionHeadingOf())
intro_text = (
        WordBoundaries(CaselessLiteral("introductory"))
        + WordBoundaries(CaselessLiteral("text"))
        ).setParseAction(lambda _: tokens.IntroText())


single_par = (
        common.marker_paragraph
        + Optional(CaselessLiteral("introductory") +
            CaselessLiteral("text"))
        ).setParseAction(lambda match: tokens.Paragraph(None, None, 
            match[0][0].level1, match[0][0].level2, match[0][0].level3, 
            match[0][0].level4, match[0][0].level5, text=match[-1] == 'text'))
single_par_with_section = (
        common.marker_part_section 
        + common.depth1_p
        + Optional(CaselessLiteral("introductory") +
            CaselessLiteral("text"))
        ).setParseAction(lambda match: tokens.Paragraph(match[0].part, 
            match[0].section, match[1][0].level1, match[1][0].level2, 
            match[1][0].level3, match[1][0].level4, match[1][0].level5,
            text=match[-1] == 'text'))
intro_text_of = (
        Suppress(WordBoundaries(CaselessLiteral("introductory")))
        + Suppress(WordBoundaries(CaselessLiteral("text")))
        + Suppress(WordBoundaries(CaselessLiteral("of")))
        + common.marker_paragraph
        ).setParseAction(lambda match: tokens.Paragraph(None, None,
            match[0][0].level1, match[0][0].level2, match[0][0].level3,
            match[0][0].level4, match[0][0].level5, text=True
        ))


def split_pars(match):
    pars = []
    matches = [match.head] + list(match.tail)
    for match in matches:
        par = tokens.Paragraph(match.part, match.section, match.level1, 
                match.level2, match.level3, match.level4, match.level5)
        if match[-1] == 'text':
            par.text = True
        if match.conj == 'through':
            #   Iterate through, creating paragraph tokens
            prev = pars[-1]
            if prev.level5:
                for i in range(p_levels[4].index(prev.level5)+1,
                        p_levels[4].index(par.level5)):
                    pars.append(prev.clone(level5=p_levels[4][i]))
            elif prev.level4:
                for i in range(p_levels[3].index(prev.level4)+1,
                        p_levels[3].index(par.level4)):
                    pars.append(prev.clone(level4=p_levels[3][i]))
            elif prev.level3:
                for i in range(p_levels[2].index(prev.level3)+1,
                        p_levels[2].index(par.level3)):
                    pars.append(prev.clone(level3=p_levels[2][i]))
            elif prev.level2:
                for i in range(p_levels[1].index(prev.level2)+1,
                        p_levels[1].index(par.level2)):
                    pars.append(prev.clone(level2=p_levels[1][i]))
            elif prev.level1:
                for i in range(p_levels[0].index(prev.level1)+1,
                        p_levels[0].index(par.level1)):
                    pars.append(prev.clone(level1=p_levels[0][i]))
        pars.append(par)

    return pars

multiple_par = (
        common.paragraph_markers
        + (common.depth1_p
            + Optional(CaselessLiteral("introductory") +
                CaselessLiteral("text"))).setResultsName("head")
        + OneOrMore((
            (common.conj_phrases | common.through).setResultsName("conj")
            + common.depth1_p
            + Optional(CaselessLiteral("introductory") +
                    CaselessLiteral("text"))
            ).setResultsName("tail", listAllMatches=True))
        ).setParseAction(lambda match:
                tokens.ParagraphList(split_pars(match)))


amdpar_tokens = (
    single_par
    | single_par_with_section
    | multiple_par
    | section
    | put_active | put_passive | post_active | post_passive
    | delete_active | delete_passive | move_active | move_passive
    | intro_text_of
    | intro_text
    | section_heading_of
    | section_heading
    | marker_subpart
)
