#vim: set encoding=utf-8
import string

from pyparsing import CaselessLiteral, Literal, OneOrMore, Optional, Regex
from pyparsing import Suppress, Word, WordEnd, WordStart

from regparser.grammar import common, tokens
from regparser.grammar.common import WordBoundaries
from regparser.tree.paragraph import p_levels

section = (
        Suppress(Regex(u"§|Section"))
        + Word(string.digits).setResultsName("part")
        + Suppress(".")
        + Word(string.digits).setResultsName("section"))


paragraph = (
        Word(string.digits).setResultsName("section")
        + common.depth1_p.copy().setResultsName("paragraphs"))


supplement_i = (
        Suppress(Literal("Supplement I to Part"))
        + Word(string.digits).setResultsName("part"))


applicable = section | paragraph


sectno = (
        section.copy().setResultsName("regtext") 
        | supplement_i.setResultsName("interpretation"))

sections_through = (
        common.section_markers 
        + common.part_section.copy().setResultsName("lhs")
        + common.through
        + common.part_section.copy().setResultsName("rhs")
)

text = Suppress(
        (Literal("introductory") + Literal("text"))
)
