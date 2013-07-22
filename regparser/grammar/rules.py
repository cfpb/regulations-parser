#vim: set encoding=utf-8
import string

from pyparsing import CaselessLiteral, Literal, OneOrMore, Optional, Regex
from pyparsing import Suppress, Word, WordEnd, WordStart

from regparser.grammar import common, tokens
from regparser.grammar.common import WordBoundaries
from regparser.tree.paragraph import p_levels


applicable = (
    common.marker_part_section
    | (common.section + common.depth1_p))
