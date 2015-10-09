# -*- coding: utf-8 -*-
from unittest import TestCase

from regparser.grammar import unified


class GrammarCommonTests(TestCase):

    def test_depth1_p(self):
        text = '(c)(2)(ii)(A)(<E T="03">2</E>)'
        result = unified.depth1_p.parseString(text)
        self.assertEqual('c', result.p1)
        self.assertEqual('2', result.p2)
        self.assertEqual('ii', result.p3)
        self.assertEqual('A', result.p4)
        self.assertEqual('2', result.p5)

    def test_notice_cfr_p(self):
        text = '12 CFR Parts 1002, 1024, and 1026'
        result = unified.notice_cfr_p.parseString(text)
        self.assertEqual(['1002', '1024', '1026'], list(result))
        text = '12 CFR Parts 1024, and 1026'
        result = unified.notice_cfr_p.parseString(text)
        self.assertEqual(['1024', '1026'], list(result))
        text = '12 CFR Parts 1024'
        result = unified.notice_cfr_p.parseString(text)
        self.assertEqual(['1024'], list(result))
        text = '12 CFR 1024'
        result = unified.notice_cfr_p.parseString(text)
        self.assertEqual(['1024'], list(result))

    def test_marker_comment(self):
        texts = [u'comment § 1004.3-4-i',
                 u'comment § 1004.3-4.i',
                 u'comment 1004.3-4-i',
                 u'comment 1004.3-4.i',
                 u'comment 3-4-i']
        for t in texts:
            result = unified.marker_comment.parseString(t)
            self.assertEqual("3", result.section)
            self.assertEqual("4", result.c1)
