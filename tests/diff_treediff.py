# vim: set encoding=utf-8
from unittest import TestCase

from regparser.tree import reg_text
from regparser.tree.struct import FrozenNode
from regparser.diff import treediff


class TreeDiffTest(TestCase):
    def test_getopcodes(self):
        old = 'I have a string to change'
        new = 'We have a string to change now'
        codes = treediff.get_opcodes(old, new)
        self.assertEquals(
            [
                [('delete', 0, 1), ('insert', 0, 'We')],
                ('insert', 25, ' now')], codes)

    def test_ins_opcodes(self):
        old = "I a string to change"
        new = "I have a string to change"
        codes = treediff.get_opcodes(old, new)
        self.assertEquals(
            [('insert', 2, 'have ')], codes)

    def test_del_opcodes(self):
        old = "I have a string to change"
        new = 'have a string to change'
        codes = treediff.get_opcodes(old, new)
        self.assertEquals(
            [('delete', 0, 2)], codes)

    def test_del_opcodes_middle(self):
        old = "I have a string to change"
        new = 'I have a change'
        codes = treediff.get_opcodes(old, new)
        self.assertEquals(
            [('delete', 9, 19)], codes)

    def test_ins_opcodes_trailing_space(self):
        old = 'Howdy howdy. '
        new = 'Howdy howdy. More content'
        codes = treediff.get_opcodes(old, new)
        self.assertEquals(
            [('insert', 13, 'More content')], codes)

    def test_convert_insert(self):
        old = ['gg']
        new = ['ac', 'ef', 'bd']
        op = ('insert', 2, 2, 0, 1)
        converted = treediff.convert_insert(op, old, new)
        self.assertEquals(('insert', 2, 'ac'), converted)

    def test_subparts(self):
        """ Create a tree with no subparts, then add subparts. """
        title = u"Regulation Title"
        sect1_title = u"§ 204.1 First Section"
        sect1 = u"(a) I believe this is (b) the best section "
        sect2_title = u"§ 204.2 Second Section"
        sect2 = u"Some sections \ndon't have \ndepth at all."

        old_text = "\n".join([title, sect1_title, sect1, sect2_title, sect2])
        older = reg_text.build_reg_text_tree(old_text, 204)

        ntitle = u"Regulation Title"
        nsubpart_a = u"Subpart A—First subpart"
        nsect1_title = u"§ 204.1 First Section"
        nsect1 = u"(a) I believe this is (b) the best section "
        nsubpart_b = u"Subpart B—Second subpart"
        nsect2_title = u"§ 204.2 Second Section"
        nsect2 = u"Some sections \ndon't have \ndepth at all."

        new_text = "\n".join([
            ntitle, nsubpart_a, nsect1_title,
            nsect1, nsubpart_b, nsect2_title, nsect2])
        newer = reg_text.build_reg_text_tree(new_text, 204)

        result = dict(treediff.changes_between(
            FrozenNode.from_node(older), FrozenNode.from_node(newer)))

        self.assertEquals(
            result['204-Subpart-A'],
            {"node": {
                "text": u"", "node_type": u"subpart",
                "tagged_text": None,
                "label": ("204", "Subpart", "A"),
                "child_labels": ("204-1",),
                "title": u"First subpart"},
                "op": "added"})
        self.assertTrue('204-Subpart-B' in result)
        self.assertEquals(result['204-Subpart'], {"op": "deleted"})

    def test_deconstruct_text(self):
        words = treediff.deconstruct_text("Single-word")
        self.assertEqual(['Single-word'], words)
        words = treediff.deconstruct_text("This is a sentence.")
        self.assertEqual(['This', ' ', 'is', ' ', 'a', ' ', 'sentence.'],
                         words)
        words = treediff.deconstruct_text("An image: "
                                          + "![Appendix A9](ER27DE11.000)")
        self.assertEqual(['An', ' ', 'image:', ' ',
                          '![Appendix A9](ER27DE11.000)'], words)
        words = treediff.deconstruct_text("This\nis\t\ta test\n\tpattern")
        self.assertEqual(
            ['This', '\n', 'is', '\t\t', 'a', ' ', 'test', '\n\t', 'pattern'],
            words)

    def test_title_disappears(self):
        lhs = FrozenNode("Text", title="Some Title", label=['1111'])
        rhs = FrozenNode("Text", title=None, label=['1111'])

        result = dict(treediff.changes_between(lhs, rhs))
        self.assertEqual(
            result['1111'],
            {'title': [('delete', 0, 10)], 'op': 'modified'})
