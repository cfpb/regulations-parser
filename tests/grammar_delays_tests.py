from datetime import date
from unittest import TestCase

from regparser.grammar.delays import *

class GrammarDelaysTests(TestCase):

    def test_date_parser(self):
        result = date_parser.parseString("February 7, 2012")
        self.assertEqual(date(2012, 2, 7), result[0])
        result = date_parser.parseString("April 21, 1987")
        self.assertEqual(date(1987, 4, 21), result[0])
