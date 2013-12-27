#vim: set encoding=utf-8
from pyparsing import SkipTo, Suppress, Regex
from regparser.grammar.utils import DocLiteral, keep_pos

smart_quotes = (
    Suppress(DocLiteral(u'“', "left-smart-quote"))
    + SkipTo(
        DocLiteral(u'”', "right-smart-quote")
    ).setParseAction(keep_pos).setResultsName("term")
)

e_tag = (
    Suppress(Regex(r"<E[^>]*>"))
    + SkipTo(
        Suppress(Regex(r"</E> (or|means)"))
    ).setParseAction(keep_pos).setResultsName("term")
)

beginning_of_paragraph = (
    Suppress(Regex(r"^\(([a-zA-Z0-9]+)\)"))
    + e_tag
)

term_parser = (
    smart_quotes
)

xml_term_parser = (
    beginning_of_paragraph
)
