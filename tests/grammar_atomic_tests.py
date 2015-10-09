from unittest import TestCase

from pyparsing import ParseException
from regparser.grammar import atomic


class GrammarAtomicTests(TestCase):
    def test_em_digit_p(self):
        result = atomic.em_digit_p.parseString('(<E T="03">2</E>)')
        self.assertEqual('2', result.p5)

    def test_double_alpha(self):
        for text, p1 in [('(a)', 'a'),
                         ('(aa)', 'aa'),
                         ('(i)', 'i')]:
            result = atomic.lower_p.parseString(text)
            self.assertEqual(p1, result.p1)

        for text in ['(ii)', '(iv)', '(vi)']:
            with self.assertRaises(ParseException):
                atomic.lower_p.parseString(text)
