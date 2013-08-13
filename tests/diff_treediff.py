#vim: set encoding=utf-8
from unittest import TestCase

import difflib

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
                ('insert', 0, 0, 0, 2)], ('insert', 25, 25, 26, 30)],
            codes)
