from unittest import TestCase

from pyparsing import ParseException
from regparser.grammar.atomic import *


class GrammarAtomicTests(TestCase):
    def test_em_digit_p(self):
        result = em_digit_p.parseString('(<E T="03">2</E>)')
        self.assertEqual('2', result.p5)

    def test_double_alpha(self):
        # Match (aa), (bb), etc.
        result = lower_p.parseString('(a)')
        self.assertEqual('a', result.p1)

        result = lower_p.parseString('(aa)')
        self.assertEqual('aa', result.p1)

        result = lower_p.parseString('(i)')
        self.assertEqual('i', result.p1)

        # Except for roman numerals
        with self.assertRaises(ParseException):
            result = lower_p.parseString('(ii)')
        with self.assertRaises(ParseException):
            result = lower_p.parseString('(iv)')

