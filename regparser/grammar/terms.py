#vim: set encoding=utf-8
from pyparsing import (
    Literal, OneOrMore, Optional, Regex, SkipTo, srange, Suppress, Word)
from regparser.grammar.utils import DocLiteral, keep_pos, Marker
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

xml_term_parser = (
    beginning_of_paragraph
)

scope_term_type_parser = (
    Marker("purposes") + Marker("of") + Optional(Marker("this"))
    + SkipTo(",").setResultsName("scope") + Literal(",")
    + Optional(Marker("the") + Marker("term"))
    + SkipTo(Marker("means")
             | (Marker("refers") + Marker("to"))
             ).setParseAction(keep_pos).setResultsName("term"))
