#vim: set encoding=utf-8
from parser.grammar.utils import keep_pos
from pyparsing import SkipTo, Suppress

smart_quotes = (
    Suppress(u'“') 
    + SkipTo(u'”').setParseAction(keep_pos).setResultsName("term")
)

term_parser = smart_quotes #   will eventually include italic text, etc.

