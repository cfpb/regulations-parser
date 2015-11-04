from regparser.tree import supplement
from unittest import TestCase


class DepthSupplementTest(TestCase):

    def test_find_supplement_start(self):
        text = "Supplement A S\nOther\nSupplement I Thing\nXX Supplement C Q"
        self.assertEqual(21, supplement.find_supplement_start(text))
        self.assertEqual(21, supplement.find_supplement_start(text, 'I'))
        self.assertEqual(0, supplement.find_supplement_start(text, 'A'))
        self.assertEqual(None, supplement.find_supplement_start(text, 'C'))
