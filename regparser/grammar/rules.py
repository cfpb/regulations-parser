#vim: set encoding=utf-8
from regparser.grammar import common
import string
from pyparsing import Literal, Regex, Suppress, Word

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

amdpar = (
        common.marker_part.setResultsName("part")
        | sections_through.setResultsName("sections_through")
        | common.marker_part_section.setResultsName("section")
        | common.marker_paragraph.setResultsName("paragraph")
        | text.setResultsName("text")
)
