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

upper_c = "." + Word(string.ascii_uppercase).setResultsName('c3')
roman_c = "." + Word("ivxlcdm").setResultsName('c2')

part = Word(string.digits).setResultsName("part")

section = Word(string.digits).setResultsName("section")

appendix = Regex("[A-Z]+[0-9]*").setResultsName("appendix")
appendix_section = Word(string.digits).setResultsName("appendix_section")


section_marker = Suppress(Regex(u"§|Section|section"))
sections_marker = Suppress(Regex(u"§§|Sections|sections"))

paragraph_marker = Marker("paragraph")
paragraphs_marker = Marker("paragraphs")

part_marker = Marker("part")
parts_marker = Marker("parts")

subpart_marker = Marker("subpart")

comment_marker = (
    (Marker("comment")
     | (Marker("official") + Marker("interpretations")))
    + Optional(Marker("of")))
comments_marker = Marker("comments")

appendix_marker = Marker("appendix")

conj_phrases = (
    Regex(",|and|or")
    + Optional("and")
    + Optional("or")
)
through = WordBoundaries(CaselessLiteral("through"))
