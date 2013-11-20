#vim: set encoding=utf-8
"""Atomic components; probably shouldn't use these directly"""
import string

from pyparsing import CaselessLiteral, Optional, Regex, Suppress, Word

from regparser.grammar.utils import Marker, WordBoundaries


lower_p = (
    Suppress("(")
    + Word(string.ascii_lowercase, max=1).setResultsName("p1")
    + Suppress(")"))
digit_p = (
    Suppress("(")
    + Word(string.digits).setResultsName("p2")
    + Suppress(")"))
roman_p = (
    Suppress("(")
    + Word("ivxlcdm").setResultsName("p3") +
    Suppress(")"))
upper_p = (
    Suppress("(")
    + Word(string.ascii_uppercase).setResultsName("p4")
    + Suppress(")"))
em_digit_p = (
    Suppress(Regex(r"\(<E[^>]*>"))
    + Word(string.digits).setResultsName("p5")
    + Suppress("</E>)"))
# Our support for italicized paragraph markers isn't quite up to par yet;
# allow a plaintext version of italic paragraph markers
plaintext_level5_p = (
    Suppress("(")
    + Word(string.digits).setResultsName("plaintext_p5")
    + Suppress(")"))

# Leave whitespace; if there's a space we assume the comment is broken
upper_c = "." + Word(string.ascii_uppercase).setResultsName(
    'c3').leaveWhitespace()
roman_c = "." + Word("ivxlcdm").setResultsName('c2').leaveWhitespace()
digit_c = "-" + Word(string.digits).setResultsName('c1').leaveWhitespace()

part = Word(string.digits).setResultsName("part")

section = Word(string.digits).setResultsName("section")

appendix = Regex("[A-Z]+[0-9]*").setResultsName("appendix")
appendix_section = Word(string.digits).setResultsName("appendix_section")

subpart = Word(string.ascii_uppercase).setResultsName("subpart")

section_marker = Suppress(Regex(u"§|Section|section"))
sections_marker = Suppress(Regex(u"§§|Sections|sections"))

paragraph_marker = Marker("paragraph")
paragraphs_marker = Marker("paragraphs")

part_marker = Marker("part")
parts_marker = Marker("parts")

subpart_marker = Marker("subpart")

comment_marker = (
    (Marker("comment")
     | (Marker("official") + Marker("interpretations"))
     | (Marker("supplement") + Suppress(WordBoundaries("I"))))
    + Optional(Marker("of") | Marker("to")))
comments_marker = Marker("comments")

appendix_marker = Marker("appendix")

conj_phrases = (
    (Suppress(",") + Optional(Marker("and") | Marker("or")))
    | Marker("and")
    | Marker("or")
    | WordBoundaries(CaselessLiteral("through")).setResultsName("through"))
