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
    + SkipTo(Regex(r"</E> (or|means)"))
)

start_of_paragraph_e_tag = (
    ((Suppress(") ")
      | Suppress("or "))
    + e_tag
    ).setParseAction(keep_pos).setResultsName("term")
)

term_parser = (
    smart_quotes
    | start_of_paragraph_e_tag
)
