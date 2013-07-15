from unittest import TestCase

from regparser.grammar.common import *

class GrammarCommonTests(TestCase):

    def test_em_digit_p(self):
        result = em_digit_p.parseString('(<E T="03">2</E>)')
        self.assertEqual('2', result.level5)

        text = '(c)(2)(ii)(A)(<E T="03">2</E>)'
        result = depth1_p.parseString(text)
        self.assertEqual('c', result.level1)
        self.assertEqual('2', result.level2)
        self.assertEqual('ii', result.level3)
        self.assertEqual('A', result.level4)
        self.assertEqual('2', result.level5)
