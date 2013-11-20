from unittest import TestCase

from regparser.grammar.atomic import *


class GrammarAtomicTests(TestCase):
    def test_em_digit_p(self):
        result = em_digit_p.parseString('(<E T="03">2</E>)')
        self.assertEqual('2', result.p5)
