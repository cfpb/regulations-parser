#vim: set encoding=utf-8
from parser.grammar.internal_citations import *
from pyparsing import ParseException
from unittest import TestCase

class GrammerInternalCitationsTest(TestCase):

    def test_regtext_citation_positive(self):
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
            regtext_citation.parseString(citation)

    def test_regtext_citation_negative(self):
        citations = [u"§§ abc.tt", u"§ bbb.qq", u"205.9(a)", u"§§  205.9(1)"]
        for citation in citations:
            self.assertRaises(ParseException, regtext_citation.parseString, 
                    citation)

    def test_regtext_in_context(self):
        seg1 = u"This text will be checked for "
        seg2 = u"§ 105.22(b)(1)"
        seg3 = u" sections within it. For example § this is not a section\n"
        seg4 = u"§§ 22.32(a) and 39.21(c)(4)(iv)(Q)"
        seg5 = u" § not a section."
        offsets = [(start, end) for _,start,end in 
                regtext_citation.scanString(seg1+seg2+seg3+seg4+seg5)]
        self.assertEqual(offsets,
                #   Trailing space is included
                [   (len(seg1), len(seg1+seg2) + 1),
                    (len(seg1+seg2+seg3), len(seg1+seg2+seg3+seg4) + 1)])

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

    def test_comment_positive(self):
        citations = [
            "comment 10(b)-5",
            "comment 10(b)-7.vi",
            "comment 10(b)-7.vi.Q",
            "comment 8(b)(1)-1",
            "comment 13(x)(5)(iv)-2",
            "comment 10000(z)(9)(x)(Y)-33",
            "comment 10000(z)(9)(x)(Y)-25",
            "comment 10000(z)(9)(x)(Y)-25.xc",
            "comment 10000(z)(9)(x)(Y)-25.xc.Z"
        ]
        for citation in citations:
            self.assertEqual(1, 
                    len(list(comment_citation.scanString(citation))))
            _, _, end = comment_citation.scanString(citation).next()
            self.assertEqual(len(citation), end)

    def test_comment_negative(self):
        citations = [
            "comment 10(5)-5",
            "comment 10(b)"
            "comment 10"
            "comment 8-b(1)"
        ]
        for citation in citations:
            self.assertRaises(ParseException, comment_citation.parseString, 
                    citation)

    def test_comment_whitepace(self):
        """Confirm that whitespace is not allowed between period-separated
        piece"""
        text = "comment 10(x)-3.\nii. Some new content"
        comments = list(comment_citation.scanString(text))
        self.assertEqual(1,len(comments))
        comment_text = text[comments[0][1]:comments[0][2]]
        self.assertFalse("ii." in comment_text)

    def test_comment_in_context(self):
        text = "This has (a)(1) no paragraph (b) commentary citations"
        self.assertEqual([], list(comment_citation.scanString(text)))
        text = "This has one comment 17(b)-7"
        offsets = [(s,e) for _,s,e in comment_citation.scanString(text)]
        self.assertEqual([(13, len(text))], offsets)
        text = "Multiple: comment 17(b)-7 and comment 20(a)(3)-2 and then "
        text += "comment\n20(b)(2)-4.ii."
        #   does not include the trailing space
        offsets = [(s,e) for _,s,e in comment_citation.scanString(text)]
        self.assertEqual([(10, 25), (30, 48), (58, len(text)-1)], offsets)
