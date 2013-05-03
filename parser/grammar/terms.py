#vim: set encoding=utf-8
from pyparsing import dblQuotedString, SkipTo

smart_quotes = (u'“' + SkipTo(u'”')).setParseAction(lambda s,l,t: t[1])

term_parser = smart_quotes #   will eventually include italic text, etc.

