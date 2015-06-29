from unittest import TestCase

from regparser.grammar.unified import *


class GrammarCommonTests(TestCase):

    def test_depth1_p(self):
        text = '(c)(2)(ii)(A)(<E T="03">2</E>)'
        result = depth1_p.parseString(text)
        self.assertEqual('c', result.p1)
        self.assertEqual('2', result.p2)
        self.assertEqual('ii', result.p3)
        self.assertEqual('A', result.p4)
        self.assertEqual('2', result.p5)

    def test_notice_cfr_p(self):
        text = '12 CFR Parts 1002, 1024, and 1026'
        result = notice_cfr_p.parseString(text)
        self.assertEqual(['1002', '1024', '1026'], list(result))
        text = '12 CFR Parts 1024, and 1026'
        result = notice_cfr_p.parseString(text)
        self.assertEqual(['1024', '1026'], list(result))
        text = '12 CFR Parts 1024'
        result = notice_cfr_p.parseString(text)
        self.assertEqual(['1024'], list(result))

