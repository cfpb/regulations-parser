from pyparsing import Word, Optional, LineStart, LineEnd, SkipTo
from parser.grammar.internal_citations import depth1_p
import string


with_paragraph = (
    LineStart()
    + "Paragraph" 
    + Word(string.digits).setResultsName("section")
    + depth1_p.setResultsName("pars")
)


without_paragraph = (
    LineStart() 
    + Word(string.digits).setResultsName("section")
    + depth1_p.setResultsName("pars")
    + SkipTo("\n").setResultsName("term")
    + LineEnd()
)


parser = with_paragraph | without_paragraph
