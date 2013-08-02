# vim: set encoding=utf-8

from regparser.tree.reg_text import *
from regparser.tree.struct import Node
from unittest import TestCase

class DepthRegTextTest(TestCase):

    def test_build_reg_text_tree_no_sections(self):
        text = "Regulation Title\nThen some more content"
        self.assertEqual(Node(text, [], ['201'], 'Regulation Title'), 
                build_reg_text_tree(text, 201))

    def test_build_reg_text_tree_sections(self):
        title = u"Regulation Title"
        sect1_title = u"§ 204.1 Best Section"
        sect1 = u"(a) I believe this is (b) the (1) best section "
        sect1 += "(2) don't (c) you?"
        sect2_title = u"§ 204.2 Second Best Section"
        sect2 = u"Some sections \ndon't have must \ndepth at all."
        sect4_title = u"§ 204.4 I Skipped One"
        sect4 = u"Others \n(a) Skip sections for (1) No \n(2) Apparent \n"
        sect4 += "(3) Reason"

        text = "\n".join((title, sect1_title, sect1, sect2_title, sect2, 
            sect4_title, sect4))

        reg = build_reg_text_tree(text, 204)
        self.assertEqual(["204"], reg.label)
        self.assertEqual(title, reg.title)
        self.assertEqual("", reg.text.strip())
        self.assertEqual(3, len(reg.children))
        (sect1_tree, sect2_tree, sect4_tree) = reg.children

        self.assertEqual(['204', '1'], sect1_tree.label)
        self.assertEqual(sect1_title, sect1_tree.title)
        self.assertEqual("", sect1_tree.text.strip())
        self.assertEqual(3, len(sect1_tree.children))
        self.assertEqual(0, len(sect1_tree.children[0].children))
        self.assertEqual(2, len(sect1_tree.children[1].children))
        self.assertEqual(0, len(sect1_tree.children[2].children))

        self.assertEqual(['204', '2'], sect2_tree.label)
        self.assertEqual(sect2_title, sect2_tree.title)
        self.assertEqual(sect2, sect2_tree.text.strip())
        self.assertEqual(0, len(sect2_tree.children))

        self.assertEqual(['204', '4'], sect4_tree.label)
        self.assertEqual(sect4_title, sect4_tree.title)
        self.assertEqual(u"Others", sect4_tree.text.strip())
        self.assertEqual(1, len(sect4_tree.children))
        self.assertEqual(3, len(sect4_tree.children[0].children))

    def test_find_next_section_start(self):
        text = u"\n\nSomething\n§ 205.3 thing\n\n§ 205.4 Something\n§ 203.19"
        self.assertEqual(12, find_next_section_start(text, 205))
        self.assertEqual(None, find_next_section_start(text, 204))
        self.assertEqual(45, find_next_section_start(text, 203))

    def test_next_section_offsets(self):
        """Should get the start and end of each section, even if it is
        followed by an Appendix or a supplement"""
        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \n asdsas\nSection\n"
        text += u"§ 201.20 dfds \n sdfds § 201.2 saddsa \n\n sdsadsa"
        self.assertEqual((2,45), next_section_offsets(text, 201))

        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \n asdsas\nSection\n"
        text += u"201.20 dfds \n sdfds § 201.2 saddsa \n\n sdsadsa"
        self.assertEqual((2,len(text)), next_section_offsets(text, 201))

        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \nAppendix A"
        self.assertEqual((2,29), next_section_offsets(text, 201))

        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \nSupplement I"
        self.assertEqual((2,29), next_section_offsets(text, 201))

    def test_sections(self):
        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \n asdsas\nSection\n"
        text += u"§ 201.20 dfds \n sdfds § 201.2 saddsa \n\n sdsadsa\n"
        text += u"Appendix A bssds \n sdsdsad \nsadad \ndsada"
        self.assertEqual([(2,45), (45,93)], sections(text, 201))

    def test_build_section_tree(self):
        """Should be just like build_paragraph tree, but with a label"""
        line1 = u"§ 201.20 Super Awesome Section"
        line2 = u"\nThis (a) is a good (1) test (2) of (3) some (b) body."
        tree = build_section_tree(line1+line2, 201)
        p_tree = regParser.build_tree(line2, label=['201', '20'])
        self.assertEqual(p_tree.text, tree.text)
        self.assertEqual(p_tree.children, tree.children)
        self.assertEqual(['201', '20'], tree.label)
        self.assertEqual(line1, tree.title)

    def test_build_section_tree_appendix(self):
        """Should should not break on references to appendices."""
        line1 = u"§ 201.20 Super Awesome Section"
        line2a = "\n(a) Par 1 references Q-5(b) through (d) of Appendix Q"
        line2b = "\n(a) Par 1 references Q-5(a) through (d) of Appendix Q"
        line2c = "\n(a) Par 1 references Q-5(a) of Appendix Q"

        for line2 in [line2a, line2b, line2c]:
            tree = build_section_tree(line1+line2, 201)
            self.assertEqual(tree.text, "\n")
            self.assertEqual(1, len(tree.children))
            child = tree.children[0]
            self.assertEqual(child.text, line2[1:])
            self.assertEqual(0, len(child.children))

    def test_build_section_tree_a_or_b1(self):
        line1 = u"§ 201.20 Super Awesome Section"
        line2 = "\n(a) a (b) b (c) see paragraph (a) or (b)(1) of "
        line2 += "this section"

        tree = build_section_tree(line1+line2, 201)
        self.assertEqual(tree.text, "\n")
        self.assertEqual(3, len(tree.children))
        child = tree.children[2]
        self.assertEqual(child.text, "(c) see paragraph (a) or (b)(1) " +
                "of this section")
        self.assertEqual(0, len(child.children))

    def test_build_section_tree_appendix_through(self):
        line1 = u"§ 201.20 Super Awesome Section"
        line2 = "\n(a) references Model Forms A-30(a) through (b)"

        tree = build_section_tree(line1+line2, 201)
        self.assertEqual(tree.text, "\n")
        self.assertEqual(1, len(tree.children))
