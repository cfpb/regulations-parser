from unittest import TestCase

from regparser.diff import text as difftext


class DiffTextTests(TestCase):
    def test_getopcodes(self):
        old = 'I have a string to change'
        new = 'We have a string to change now'
        codes = difftext.get_opcodes(old, new)
        self.assertEquals(
            [
                [('delete', 0, 1), ('insert', 0, 'We')],
                ('insert', 25, ' now')], codes)

    def test_ins_opcodes(self):
        old = "I a string to change"
        new = "I have a string to change"
        codes = difftext.get_opcodes(old, new)
        self.assertEquals(
            [('insert', 2, 'have ')], codes)

    def test_del_opcodes(self):
        old = "I have a string to change"
        new = 'have a string to change'
        codes = difftext.get_opcodes(old, new)
        self.assertEquals(
            [('delete', 0, 2)], codes)

    def test_del_opcodes_middle(self):
        old = "I have a string to change"
        new = 'I have a change'
        codes = difftext.get_opcodes(old, new)
        self.assertEquals(
            [('delete', 9, 19)], codes)

    def test_ins_opcodes_trailing_space(self):
        old = 'Howdy howdy. '
        new = 'Howdy howdy. More content'
        codes = difftext.get_opcodes(old, new)
        self.assertEquals(
            [('insert', 13, 'More content')], codes)

    def test_convert_insert(self):
        old = ['gg']
        new = ['ac', 'ef', 'bd']
        op = ('insert', 2, 2, 0, 1)
        converted = difftext.convert_insert(op, old, new)
        self.assertEquals(('insert', 2, 'ac'), converted)

    def test_deconstruct_text(self):
        words = difftext.deconstruct_text("Single-word")
        self.assertEqual(['Single-word'], words)
        words = difftext.deconstruct_text("This is a sentence.")
        self.assertEqual(['This', ' ', 'is', ' ', 'a', ' ', 'sentence.'],
                         words)
        words = difftext.deconstruct_text("An image: "
                                          + "![Appendix A9](ER27DE11.000)")
        self.assertEqual(['An', ' ', 'image:', ' ',
                          '![Appendix A9](ER27DE11.000)'], words)
        words = difftext.deconstruct_text("This\nis\t\ta test\n\tpattern")
        self.assertEqual(
            ['This', '\n', 'is', '\t\t', 'a', ' ', 'test', '\n\t', 'pattern'],
            words)
