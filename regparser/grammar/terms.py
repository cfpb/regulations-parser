#vim: set encoding=utf-8
from pyparsing import SkipTo, Suppress, Regex, Literal, Word, srange, OneOrMore
from regparser.grammar.utils import DocLiteral, keep_pos
from regparser.grammar.unified import any_depth_p

smart_quotes = (
    Suppress(DocLiteral(u'“', "left-smart-quote"))
    + SkipTo(
        DocLiteral(u'”', "right-smart-quote")
    ).setParseAction(keep_pos).setResultsName("term")
)

e_tag = (
    Suppress(Regex(r"<E[^>]*>"))
    + OneOrMore(
        Word(srange("[a-zA-Z-]"))
    ).setParseAction(keep_pos).setResultsName("term")
    + Suppress(
        Literal("</E>") + Literal("means")
    )
)

beginning_of_paragraph = (
    Suppress(any_depth_p)
    + e_tag
)

term_parser = (
    smart_quotes
)

xml_term_parser = (
    beginning_of_paragraph
)
