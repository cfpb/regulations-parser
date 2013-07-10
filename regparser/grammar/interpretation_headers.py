import string

from pyparsing import LineEnd, Literal, LineStart, SkipTo, Word

from regparser.grammar.common import depth1_p


with_paragraph = (
    LineStart()
    + Literal("Paragraph")
    + Word(string.digits).setResultsName("section")
    + depth1_p.setResultsName("pars")
)


without_paragraph = (
    LineStart() 
    + Word(string.digits).setResultsName("section")
    + depth1_p.setResultsName("pars")
    + SkipTo(LineEnd()).setResultsName("term")
)


parser = with_paragraph | without_paragraph
