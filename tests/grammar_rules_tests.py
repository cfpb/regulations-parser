import string
from unittest import TestCase

from regparser.grammar import tokens
from regparser.grammar.rules import *

class GrammarRulesTests(TestCase):

    def test_appendix_through(self):
        result = multiple_appendices.parseString('A-30 through A-41')
        result = result[0]
        self.assertEqual(12, len(result.appendices))
        for i in range(12):
            self.assertEqual('A', result.appendices[i].letter)
            self.assertEqual(str(i+30), result.appendices[i].section)

        result = multiple_appendices.parseString('B-2(d) through B-2(z)')
        result = result[0]
        self.assertEqual(23, len(result.appendices))
        for i in range(23):
            self.assertEqual('B', result.appendices[i].letter)
            self.assertEqual('2(%s)' % string.ascii_lowercase[i+3], 
                    result.appendices[i].section)

    def test_amdpar_appendix_through_revised(self):
        text = "A-30(a) through A-30(d) are added."
        result = [m[0] for m,_,_, in amdpar_tokens.scanString(text)]
        self.assertEqual(2, len(result))
        self.assertTrue(isinstance(result[0], tokens.AppendixList))
        self.assertTrue(isinstance(result[1], tokens.Verb))

    def test_multiple_appendix(self):
        text = "A-30(a), A-30(b), A-30(c), A-30(d)"
        result = multiple_appendices.parseString(text)
        result = result[0]
        self.assertEqual(4, len(result.appendices))
        self.assertEqual('A', result.appendices[0].letter)
        self.assertEqual('30(a)', result.appendices[0].section)
        self.assertEqual('A', result.appendices[1].letter)
        self.assertEqual('30(b)', result.appendices[1].section)
        self.assertEqual('A', result.appendices[2].letter)
        self.assertEqual('30(c)', result.appendices[2].section)
        self.assertEqual('A', result.appendices[3].letter)
        self.assertEqual('30(d)', result.appendices[3].section)
