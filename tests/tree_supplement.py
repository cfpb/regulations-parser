from regparser.tree.supplement import *
from unittest import TestCase

class DepthSupplementTest(TestCase):

    def test_find_supplement_start(self):
        text = "Supplement A S\nOther\nSupplement I Thing\nXX Supplement C Q"
        self.assertEqual(21, find_supplement_start(text))
        self.assertEqual(21, find_supplement_start(text, 'I'))
        self.assertEqual(0, find_supplement_start(text, 'A'))
        self.assertEqual(None, find_supplement_start(text, 'C'))
