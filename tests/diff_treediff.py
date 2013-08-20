#vim: set encoding=utf-8
from unittest import TestCase

from regparser.tree import reg_text
from regparser.diff import treediff


class TreeDiffTest(TestCase):
    def test_build_hash(self):
        title = u"Regulation Title"
        sect1_title = u"§ 204.1 Best Section"
        sect1 = u"(a) I believe this is (b) the (1) best section "
        sect1 += "(2) don't (c) you?"
        subpart_a = u"Subpart A—First subpart"
        sect2_title = u"§ 204.2 Second Best Section"
        sect2 = u"Some sections \ndon't have must \ndepth at all."
        subpart_b = u"Subpart B—First subpart"
        sect4_title = u"§ 204.4 I Skipped One"
        sect4 = u"Others \n(a) Skip sections for (1) No \n(2) Apparent \n"
        sect4 += "(3) Reason"

        text = "\n".join(
            (title, sect1_title, sect1, subpart_a, sect2_title, sect2,
             subpart_b, sect4_title, sect4))
        reg = reg_text.build_reg_text_tree(text, 204)

        tree_hash = treediff.hash_nodes(reg)
        keys = tree_hash.keys()
        keys.sort()
        self.assertEquals(
            ['204', '204-1', '204-1-a', '204-1-b',
             '204-1-b-1', '204-1-b-2', '204-1-c', '204-2', '204-4',
             '204-4-a', '204-4-a-1', '204-4-a-2', '204-4-a-3', '204-Subpart',
             '204-Subpart-A', '204-Subpart-B'], keys)

    def test_getopcodes(self):
        old = 'I have a string to change'
        new = 'We have a string to change now'
        codes = treediff.get_opcodes(old, new)
        self.assertEquals(
            [[('delete', 0, 1),
                ('insert', 0, 'We')], ('insert', 25, ' now')],
            codes)

    def test_del_opcodes(self):
        old = "I have a string to change"
        new = 'have a string to change'
        codes = treediff.get_opcodes(old, new)
        self.assertEquals(
            [('delete', 0, 2)], codes)

    def test_convert_insert(self):
        new = 'ac ef bd'
        op = ('insert', 2, 2, 2, 6)
        converted = treediff.convert_insert(op, new)
        self.assertEquals(('insert', 2, ' ef '), converted)

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

        comparer = treediff.Compare(older, newer)
        comparer.compare()

        self.assertEquals(
            comparer.changes['204-Subpart-A'],
            {"node": {
                "text": "", "node_type": "subpart",
                "label": ["204", "Subpart", "A"],
                "child_labels": ["204-1"],
                "title": "First subpart"},
                "op": "added"})
        self.assertTrue('204-Subpart-B' in comparer.changes)
        self.assertEquals(comparer.changes['204-Subpart'], {"op": "deleted"})
