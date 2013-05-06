from parser.grammar.internal_citations import depth1_p
import string
from pyparsing import Suppress, Word

section = (
        Suppress("Section")
        + Word(string.digits).setResultsName("part")
        + Suppress(".")
        + Word(string.digits).setResultsName("section"))


paragraph = (
        Word(string.digits).setResultsName("section")
        + depth1_p)


applicable = section | paragraph
