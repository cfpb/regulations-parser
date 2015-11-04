# vim: set encoding=utf-8
from regparser.tree.appendix import carving
from unittest import TestCase


class DepthAppendixCarvingTest(TestCase):

    def test_find_appendix_start(self):
        text = "Some \nAppendix C to Part 111 Other\n\n "
        text += "Thing Appendix A to Part 111"
        text += "\nAppendix B to Part 111"
        self.assertEqual(6, carving.find_appendix_start(text))
        self.assertEqual(59, carving.find_appendix_start(text[7:]))
        self.assertEqual(None, carving.find_appendix_start(text[7 + 60:]))

    def test_find_next_appendix_offsets(self):
        sect1 = "Some \n"
        appa = "Appendix A to Part 111 Title\nContent\ncontent\n\n"
        appb = "Appendix Q to Part 111 More Info\n\nContent content\n"
        supp = "Supplement I The Interpretations\n\nAppendix Q\n"
        supp += "Interpretations about appendix Q"
        self.assertEqual(
            (len(sect1), len(sect1 + appa)),
            carving.find_next_appendix_offsets(sect1 + appa))
        self.assertEqual(
            (len(sect1), len(sect1 + appa)),
            carving.find_next_appendix_offsets(sect1 + appa + appb))
        self.assertEqual(
            (0, len(appa)), carving.find_next_appendix_offsets(appa + supp))

    def test_appendices(self):
        sect1 = "Some \n"
        appa = "Appendix A to Part 222 Title\nContent\ncontent\n\n"
        appb = "Appendix Q to Part 222 More Info\n\nContent content\n"
        supp = "Supplement I The Interpretations\n\nAppendix Q\n"
        supp += "Interpretations about appendix Q"

        apps = carving.appendices(sect1 + appa + appb + supp)
        self.assertEqual(2, len(apps))
        self.assertEqual((len(sect1), len(sect1+appa)), apps[0])
        self.assertEqual((len(sect1+appa), len(sect1+appa+appb)), apps[1])

    def test_find_appendix_section_start(self):
        """Only find appendix sections that start a line"""
        text = "Some \nA-4--Section here\nB-99--Section C-3 here\nContent"
        self.assertEqual(6, carving.find_appendix_section_start(text, 'A'))
        self.assertEqual(24, carving.find_appendix_section_start(text, 'B'))
        self.assertEqual(None, carving.find_appendix_section_start(text, 'C'))
        self.assertEqual(None, carving.find_appendix_section_start(text, 'D'))

    def test_find_next_appendix_section_offsets(self):
        head = "More\n"
        a5 = "A-5--Some Title\nContent\ncontent\n"
        a8 = "A-8--A Title\nBody body\nbody body text\ntext text"
        self.assertEqual(
            (len(head), len(head + a5)),
            carving.find_next_appendix_section_offsets(head + a5 + a8, 'A'))
        self.assertEqual(
            (0, len(a8)), carving.find_next_appendix_section_offsets(a8, 'A'))

    def test_appendix_sections(self):
        head = "More\n"
        a5 = "A-5--Some Title\nContent\ncontent\n"
        a8 = "A-8--A Title\nBody body\nbody body text\ntext text\n"
        a20 = "A-20--More content\nBody body"
        text = head + a5 + a8 + a20
        offsets = carving.appendix_sections(text, 'A')
        self.assertEqual(3, len(offsets))
        self.assertEqual(a5, text[offsets[0][0]:offsets[0][1]])
        self.assertEqual(a8, text[offsets[1][0]:offsets[1][1]])
        self.assertEqual(a20, text[offsets[2][0]:offsets[2][1]])

    def test_get_appendix_letter(self):
        self.assertEqual(
            "A", carving.get_appendix_letter("Appendix A to Part 511", 511))
        self.assertEqual(
            "ZQR",
            carving.get_appendix_letter("Appendix ZQR to Part 10101", 10101))

    def test_get_appendix_section_number(self):
        self.assertEqual(
            "2", carving.get_appendix_section_number("A-2--Title Stuff", 'A'))
        self.assertEqual(
            "50",
            carving.get_appendix_section_number("QQ-50--Title Stuff", 'QQ'))
        self.assertEqual(
            "21(b)",
            carving.get_appendix_section_number(u"A-21(b)—A Model form", 'A'))
        self.assertEqual(
            "21(B)",
            carving.get_appendix_section_number(u"A-21(B)—A Model form", 'A'))
