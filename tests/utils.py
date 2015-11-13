import itertools
from regparser import utils
from unittest import TestCase


class Utils(TestCase):

    def test_roman_nums(self):
        first_3999 = list(itertools.islice(utils.roman_nums(), 0, 3999))
        self.assertEqual(['i', 'ii', 'iii', 'iv', 'v'], first_3999[:5])

        def assert_equal(str_value, idx):
            self.assertEqual(str_value, first_3999[idx - 1])

        assert_equal('xvii', 10 + 5 + 1 + 1)
        assert_equal('xlv', (50-10) + 5)
        assert_equal('dclv', 500 + 100 + 50 + 5)
        assert_equal('mcmxcvi', 1000 + (1000-100) + (100-10) + 5 + 1)

    def test_title_body_title_only(self):
        text = "This is some long, long title with no body"
        self.assertEqual((text, ""), utils.title_body(text))

    def test_title_body_normal_case(self):
        title = "This is a title"
        body = "Here is text that follows\nnewlines\n\n\nabout in the body"
        self.assertEqual((title, "\n" + body),
                         utils.title_body(title + "\n" + body))

    def test_flatten(self):
        self.assertEqual(['a', 'b', 'c'],
                         utils.flatten([['a', 'b'], ['c'], []]))
