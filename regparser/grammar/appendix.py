import string

from pyparsing import Literal, Word


def parenthesize(characters, name):
    return Literal("(") + Word(characters).setResultsName(name) + Literal(")")



#   Only used as the top of the appendix hierarchy
a1 = Word(string.digits).setResultsName("a1")


paren_upper = parenthesize(string.ascii_uppercase, "paren_upper")
paren_lower = parenthesize(string.ascii_lowercase, "paren_lower")
