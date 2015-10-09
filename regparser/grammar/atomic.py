# vim: set encoding=utf-8
"""Atomic components; probably shouldn't use these directly"""
import string

from pyparsing import CaselessLiteral, Optional, Regex, Suppress, Word

from regparser.grammar.utils import Marker, SuffixMarker, WordBoundaries


lower_p = (
    Suppress("(")
    + Regex(r"[ivx]{1}|[a-hj-uwyz]{1,2}").setResultsName("p1")
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
em_roman_p = (
    Suppress(Regex(r"\(<E[^>]*>"))
    + Word("ivxlcdm").setResultsName("p5")
    + Suppress("</E>)"))

# Allow a plaintext version of italic paragraph markers
plaintext_level5_p = (
    Suppress("(")
    + Word(string.digits).setResultsName("plaintext_p5")
    + Suppress(")"))
plaintext_level6_p = (
    Suppress("(")
    + Word("ivxlcdm").setResultsName("plaintext_p6")
    + Suppress(")"))

# Leave whitespace; if there's a space we assume the comment is broken
em_digit_c = ("." + Regex(r"<E[^>]*>")
              + Word(string.digits).setResultsName("c4").leaveWhitespace())
upper_c = "." + Word(string.ascii_uppercase).setResultsName(
    'c3').leaveWhitespace()
roman_c = "." + Word("ivxlcdm").setResultsName('c2').leaveWhitespace()
digit_c = "-" + Word(string.digits).setResultsName('c1').leaveWhitespace()

upper_roman_a = Word("IVXLCDM").setResultsName('a1')
upper_a = "." + Word(string.ascii_uppercase).setResultsName(
    'a2').leaveWhitespace()
digit_a = "." + Word(string.digits).setResultsName('a3').leaveWhitespace()

part = Word(string.digits).setResultsName("part")

section = Word(string.digits).setResultsName("section")

appendix = Regex(r"[A-Z]+[0-9]*\b").setResultsName("appendix")
appendix_digit = Word(string.digits).setResultsName("appendix_digit")

subpart = Word(string.ascii_uppercase).setResultsName("subpart")

section_marker = Suppress(Regex(u"§|Section|section"))
sections_marker = Suppress(Regex(u"§§|Sections|sections"))

# Most of these markers could be SuffixMarkers (which arise due to errors in
# the regulation text). We'll wait until we see explicit examples before
# converting them though, to limit false matches
paragraph_marker = Marker("paragraph")
paragraphs_marker = SuffixMarker("paragraphs")

part_marker = Marker("part")
parts_marker = Marker("parts")

subpart_marker = Marker("subpart")

comment_marker = (
    (Marker("comment")
     | Marker("commentary")
     | (Marker("official") + Marker("interpretations"))
     | (Marker("supplement") + Suppress(WordBoundaries("I"))))
    + Optional(Marker("of") | Marker("to")))
comments_marker = Marker("comments")

appendix_marker = Marker("appendix")
appendices_marker = Marker("appendices")

conj_phrases = (
    (Suppress(",") + Optional(Marker("and") | Marker("or")))
    | Marker("and")
    | Marker("or")
    | (Marker("except") + Marker("for"))
    | Suppress("-")
    | WordBoundaries(CaselessLiteral("through")).setResultsName("through"))

title = Word(string.digits).setResultsName("cfr_title")
