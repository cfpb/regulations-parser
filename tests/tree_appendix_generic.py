from parser.tree.appendix.generic import *
from unittest import TestCase

class DepthAppendixGenericTest(TestCase):
    def test_find_next_segment(self):
        long_text = "This Is All I Capital Case But Is Really, Really "
        long_text += "Long. So Long That It Should Not Be A Title Sentence"
        filler = "something here and something there and a little more"
        title = "Title Looking Segment"
        self.assertEqual(None, find_next_segment(long_text))
        self.assertEqual(None, find_next_segment(filler))
        self.assertEqual(None, find_next_segment(filler + "\n" + long_text))
        self.assertEqual(None, find_next_segment(long_text + "\n" + filler))
        self.assertEqual((0, len(title)), find_next_segment(title))
        self.assertEqual((len(filler + "\n"), len(filler + "\n" + title)), 
                find_next_segment(filler + "\n" + title))
        self.assertEqual((len(long_text + "\n"), len(long_text + "\n" + title)),
                find_next_segment(long_text + "\n" + title))
        self.assertEqual((0, len(title + "\n" + long_text + "\n")),
                find_next_segment(title + "\n" + long_text + "\n" + title))
        white_space = "   \n\t\n"
        self.assertEqual((len(white_space), len(white_space + title)),
                find_next_segment(white_space + title))
    def test_is_title_case(self):
        self.assertTrue(is_title_case("This Is In Title Case"))
        self.assertTrue(is_title_case("This is in Title Case"))
        self.assertTrue(is_title_case(""))
        self.assertTrue(is_title_case("        Title\n"))
        self.assertFalse(is_title_case("lowercase"))
        self.assertFalse(is_title_case("This Is Mostly in title case"))
    def test_segments(self):
        lines = [
                "nonsection here",
                "Followed By A Title",
                "And then some content",
                "More content",
                "Yet Another Title",
                "Third Title",
                "Content here, too"
                ]
        offsets = segments("\n".join(lines))
        self.assertEqual(3, len(offsets))

        start = len(lines[0] + "\n")
        end = len("\n".join(lines[:4])+ "\n")
        self.assertEqual((start, end), offsets[0])

        start = len("\n".join(lines[:4]) + "\n")
        end = len("\n".join(lines[:5]) + "\n")
        self.assertEqual((start, end), offsets[1])

        start = len("\n".join(lines[:5]) + "\n")
        end = len("\n".join(lines))
        self.assertEqual((start, end), offsets[2])
