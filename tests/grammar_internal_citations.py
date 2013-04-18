#vim: set encoding=utf-8
from grammar.internal_citations import *
from pyparsing import ParseException
from unittest import TestCase

class GrammerInternalCitationsTest(TestCase):
    def test_any_citation_positive(self):
        citations = [
            u"§§ 205.7, 205.8, and 205.9",
            u"§ 205.9(b)",
            u"§ 205.9(a)",
            u"§ 205.9(b)(1)",
            u"§ 205.6(b) (1) and (2)",
            u"§§ 205.6(b)(3) and 205.11(b)(1)(i)",
            u"§\n205.11(c)(2)(ii)",
            u"§ 205.9(b)(1)(i)(C)"
        ]
        for citation in citations:
            any_citation.parseString(citation)
    def test_any_citation_negative(self):
        citations = [u"§§ abc.tt", u"§ bbb.qq", u"205.9(a)", u"§§  205.9(1)"]
        for citation in citations:
            self.assertRaises(ParseException, any_citation.parseString, 
                    citation)
    def test_multiple_paragraph_pieces(self):
        """Check that we can pull out paragraph pieces from
        multiple_paragraphs parser."""
        text = "paragraphs (a)(1), (b)(2), and (c)(3)"
        match = multiple_paragraphs.parseString(text)
        paragraphs = [match.p_head] + list(match.p_tail)
        self.assertEqual(3, len(paragraphs))
        self.assertEqual('a', paragraphs[0].level1)
        self.assertEqual('1', paragraphs[0].level2)
        self.assertEqual('b', paragraphs[1].level1)
        self.assertEqual('2', paragraphs[1].level2)
        self.assertEqual('c', paragraphs[2].level1)
        self.assertEqual('3', paragraphs[2].level2)
