# vim: set encoding=utf-8
from pyparsing import (
    LineStart, Literal, OneOrMore, Optional, Regex, SkipTo, srange, Suppress,
    Word, ZeroOrMore)

from regparser.grammar import atomic, unified
from regparser.grammar.utils import DocLiteral, keep_pos, Marker


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
    + Suppress(Literal("</E>"))
)

xml_term_parser = (
    LineStart()
    + Optional(Suppress(unified.any_depth_p))
    + Suppress(ZeroOrMore(
        Word(srange("[a-zA-Z]") + '.,')
    ))
    + e_tag.setResultsName("head")
    + ZeroOrMore(
        (atomic.conj_phrases + e_tag).setResultsName(
            "tail", listAllMatches=True))
    + Suppress(ZeroOrMore(Regex(r",[a-zA-Z ]+,")))
    + Suppress(ZeroOrMore(
        (Marker("this") | Marker("the")) + Marker("term")))
    + ((Marker("mean") | Marker("means"))
       | (Marker("refers") + ZeroOrMore(Marker("only")) + Marker("to"))
       | ((Marker("has") | Marker("have")) + Marker("the") + Marker("same")
          + Marker("meaning") + Marker("as")))
)

scope_term_type_parser = (
    Marker("purposes") + Marker("of") + Optional(Marker("this"))
    + SkipTo(",").setResultsName("scope") + Literal(",")
    + Optional(Marker("the") + Marker("term"))
    + SkipTo(Marker("means")
             | (Marker("refers") + Marker("to"))
             ).setParseAction(keep_pos).setResultsName("term"))
