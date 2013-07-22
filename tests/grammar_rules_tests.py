#vim: set encoding=utf-8
import string
from unittest import TestCase

from regparser.grammar import tokens, common
from regparser.grammar.amdpar import *

class GrammarRulesTests(TestCase):
    """
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

    def test_single_par_with_section(self):
        text = u'§ 1005.3(a)'
        result = single_par_with_section.parseString(text)
        result = result[0]
        self.assertEqual('1005', result.part)
        self.assertEqual('3', result.section)
        self.assertEqual('a', result.level1)
        self.assertFalse(result.text)

        text = u'§ 8675.301(r)(4) introductory text'
        result = single_par_with_section.parseString(text)
        result = result[0]
        self.assertEqual('8675', result.part)
        self.assertEqual('301', result.section)
        self.assertEqual('r', result.level1)
        self.assertEqual('4', result.level2)
        self.assertTrue(result.text)

    def test_multiple_sections(self):
        text = u'§§ 1005.30, 1005.31, 1005.32, 1005.33, 1005.34, 1005.35,'
        text += ' and 1005.36'
        result = multiple_sections.parseString(text)
        result = result[0]
        self.assertEqual(7, len(result.sections))
        for i in range(7):
            self.assertEqual('1005', result.sections[i].part)
            self.assertEqual(str(i+30), result.sections[i].section)

        result = amdpar_tokens.parseString(text)
        result = result[0]
        self.assertEqual(7, len(result.sections))
        for i in range(7):
            self.assertEqual('1005', result.sections[i].part)
            self.assertEqual(str(i+30), result.sections[i].section)

    def test_single_interp_par(self):
        result = single_interp_par.parseString('paragraph 2;')
        result = result[0]
        self.assertEqual('2', result.level1)

        result = single_interp_par.parseString('paragraph 5.ii.Q;')
        result = result[0]
        self.assertEqual('5', result.level1)
        self.assertEqual('ii', result.level2)
        self.assertEqual('Q', result.level3)


    def test_certainty(self):
        result = token_patterns.scanString("Add subpart B to read as follows")
        print list(result)
        self.assertTrue(False)
    """
