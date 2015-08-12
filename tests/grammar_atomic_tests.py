from unittest import TestCase

from pyparsing import ParseException
from regparser.grammar.atomic import *


class GrammarAtomicTests(TestCase):
    def test_em_digit_p(self):
        result = em_digit_p.parseString('(<E T="03">2</E>)')
        self.assertEqual('2', result.p5)

    def test_double_alpha(self):
        for text, p1 in [('(a)', 'a'),
                     ('(aa)', 'aa'),
                     ('(i)','i')]:
            result = lower_p.parseString(text)
            self.assertEqual(p1, result.p1)

        for text in ['(ii)', '(iv)', '(vi)']:
            with self.assertRaises(ParseException):
                lower_p.parseString(text)

    def test_appendix(self):
        for text, a in [('A', 'A'),
                ('AB', 'AB'),
                ('BC-1', 'BC-1'),
                ('D1', 'D1')]:
            result = appendix.parseString(text)
            self.assertEqual(a, result.appendix)
