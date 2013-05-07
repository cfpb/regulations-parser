from unittest import TestCase
from parser.rule.parse import *

class RuleParseTest(TestCase):

    def test_parse_into_label(self):
        self.assertEqual("101.22", 
                parse_into_label("Section 101.22Stuff", "101"))
        self.assertEqual("101.22(d)", 
                parse_into_label("22(d) Content", "101"))
        self.assertEqual("101.22(d)(5)", 
                parse_into_label("22(d)(5) Content", "101"))
        self.assertEqual("101.22(d)(5)(x)", 
                parse_into_label("22(d)(5)(x) Content", "101"))
        self.assertEqual("101.22(d)(5)(x)(Q)", 
                parse_into_label("22(d)(5)(x)(Q) Content", "101"))

        self.assertEqual(None,
                parse_into_label("Application of this rule", "101"))
