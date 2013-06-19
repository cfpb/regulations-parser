#vim: set encoding=utf-8
from unittest import TestCase

from parser.tree.xml_parser import appendices

class AppendicesTest(TestCase):
    def test_interpretation_markers(self):
        text = '1. Kiwis and Mangos'
        marker = appendices.get_interpretation_markers(text)
        self.assertEqual(marker, '1')

    def test_interpretation_markers_roman(self):
        text = 'iv. Kiwis and Mangos'
        marker = appendices.get_interpretation_markers(text)
        self.assertEqual(marker, 'iv')

    def test_interpretation_markers_none(self):
        text = '(iv) Kiwis and Mangos'
        marker = appendices.get_interpretation_markers(text)
        self.assertEqual(marker, None)

    def test_supplement_letter(self):
        text = u'Supplement J to Part 204'
        letter = appendices.get_supplement_letter(text, 204)
        self.assertEqual('J', letter)

    def test_supplement_letter_none(self):
        text = 'Supplement K'
        letter = appendices.get_supplement_letter(text, 204)
        self.assertEqual(letter, None)

    def test_appendix_section_number(self):
        text = u'A-13 A Very Nice Appendix.'
        number = appendices.get_appendix_section_number(text, 'A')
        self.assertEqual('13', number)

    def test_appendix_section_number_none(self):
        text = u'A Very Nice Appendix.'
        number = appendices.get_appendix_section_number(text, 'A')
        self.assertEqual(None, number)
