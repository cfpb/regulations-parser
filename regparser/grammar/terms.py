#vim: set encoding=utf-8
from pyparsing import SkipTo, Suppress, Regex

from regparser.grammar.utils import DocLiteral, keep_pos

smart_quotes = (
    Suppress(DocLiteral(u'“', "left-smart-quote"))
    + SkipTo(
        DocLiteral(u'”', "right-smart-quote")
    ).setParseAction(keep_pos).setResultsName("term")
)

starting_e_tag = (
    Suppress(Regex(r"(\)) <E[^>]*>"))
    + SkipTo(
        Regex(r"\</E> means")
    ).setParseAction(keep_pos).setResultsName("term")
)

# will eventually include italic text, etc.
term_parser = (smart_quotes | starting_e_tag)
