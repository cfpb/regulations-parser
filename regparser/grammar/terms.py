#vim: set encoding=utf-8
from pyparsing import SkipTo, Suppress

from regparser.grammar.utils import DocLiteral, keep_pos

smart_quotes = (
    Suppress(DocLiteral(u'“', "left-smart-quote"))
    + SkipTo(
        DocLiteral(u'”', "right-smart-quote")
    ).setParseAction(keep_pos).setResultsName("term")
)

# will eventually include italic text, etc.
term_parser = smart_quotes
