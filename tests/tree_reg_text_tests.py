# vim: set encoding=utf-8

from regparser.tree import reg_text
from regparser.tree.struct import Node
from unittest import TestCase


class DepthRegTextTest(TestCase):

    def test_build_reg_text_tree_no_sections(self):
        text = "Regulation Title\nThen some more content"
        empty_part = Node('', [], ['201', 'Subpart'], '',
                          node_type=Node.EMPTYPART)
        self.assertEqual(Node(text, [empty_part], ['201'], 'Regulation Title'),
                         reg_text.build_reg_text_tree(text, 201))

    def test_build_reg_text_empty_and_subpart(self):
        """ In some cases, we have a few sections before the first subpart. """
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

        text = "\n".join((title, sect1_title, sect1, subpart_a, sect2_title,
                          sect2, subpart_b, sect4_title, sect4))
        reg = reg_text.build_reg_text_tree(text, 204)
        self.assertEqual(["204"], reg.label)
        self.assertEqual(title, reg.title)
        self.assertEqual("", reg.text.strip())
        self.assertEqual(3, len(reg.children))

    def test_build_reg_text_tree_sections(self):
        title = u"Regulation Title"
        subpart_a = u"Subpart A—First subpart"
        sect1_title = u"§ 204.1 Best Section"
        sect1 = u"(a) I believe this is (b) the (1) best section "
        sect1 += "(2) don't (c) you?"
        sect2_title = u"§ 204.2 Second Best Section"
        sect2 = u"Some sections \ndon't have must \ndepth at all."
        subpart_b = u"Subpart B—First subpart"
        sect4_title = u"§ 204.4 I Skipped One"
        sect4 = u"Others \n(a) Skip sections for (1) No \n(2) Apparent \n"
        sect4 += "(3) Reason"

        text = "\n".join((title, subpart_a, sect1_title, sect1, sect2_title,
                          sect2, subpart_b, sect4_title, sect4))

        reg = reg_text.build_reg_text_tree(text, 204)
        self.assertEqual(["204"], reg.label)
        self.assertEqual(title, reg.title)
        self.assertEqual("", reg.text.strip())
        self.assertEqual(2, len(reg.children))

        (subpart_a_tree, subpart_b_tree) = reg.children

        (sect1_tree, sect2_tree) = subpart_a_tree.children
        sect4_tree = subpart_b_tree.children[0]

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
        self.assertEqual(12, reg_text.find_next_section_start(text, 205))
        self.assertEqual(None, reg_text.find_next_section_start(text, 204))
        self.assertEqual(45, reg_text.find_next_section_start(text, 203))

    def test_find_next_subpart_start(self):
        text = u"\n\nSomething\nSubpart A—Procedures for Application\n\n"
        self.assertEqual(12, reg_text.find_next_subpart_start(text))

    def test_next_subpart_offsets(self):
        """ Should get the start and end of each offset. """
        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \n asdsas\nSection"
        text += u"\n\nSomething\nSubpart A—Procedures for Application\n\n"
        text += u"\n\nSomething else\nSubpart B—Model Forms for Application\n"
        self.assertEqual((56, 111), reg_text.next_subpart_offsets(text))

        text = u"\n\nSomething\nSubpart A—Application\nAppendix A to Part 201"
        self.assertEqual((12, 34), reg_text.next_subpart_offsets(text))

        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \n asdsas\nSection"
        text += u"\n\nSomething\nubpart A—Procedures for Application\n\n"
        text += u"\n\nSomething else\nSubpart B—Model Forms for Application\n"
        self.assertEqual((110, 148), reg_text.next_subpart_offsets(text))

        text = u"ubpart A—First subpart\n"
        text += u"§ 201.20 dfds \n sdfds § 201.2 saddsa \n\n sdsadsa\n"
        text += u"\nSubpart B—Second subpart\n"
        text += u"§ 2015 dfds \n sdfds § 20132 saddsa \n\n sdsadsa\n"
        self.assertEqual((72, 143), reg_text.next_subpart_offsets(text))

        text = u"Supplement I\n\nSomething else\n"
        text += u"Subpart B—Model Forms for Application\n\n"
        self.assertEqual(None, reg_text.next_subpart_offsets(text))

        text = u"Appendix Q to Part 201\n\nSomething else\n"
        text += u"Subpart B—Model Forms for Application\n"
        self.assertEqual(None, reg_text.next_subpart_offsets(text))

    def test_next_section_offsets(self):
        """Should get the start and end of each section, even if it is
        followed by an Appendix or a supplement"""
        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \n asdsas\nSection\n"
        text += u"§ 201.20 dfds \n sdfds § 201.2 saddsa \n\n sdsadsa"
        self.assertEqual((2, 45), reg_text.next_section_offsets(text, 201))

        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \n asdsas\nSection\n"
        text += u"201.20 dfds \n sdfds § 201.2 saddsa \n\n sdsadsa"
        self.assertEqual((2, len(text)),
                         reg_text.next_section_offsets(text, 201))

        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \nAppendix A to Part 201"
        self.assertEqual((2, 29), reg_text.next_section_offsets(text, 201))

        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \nSupplement I"
        self.assertEqual((2, 29), reg_text.next_section_offsets(text, 201))

        text = u"Appendix A to Part 201\n\n§ 201.3 sdsa\nsdd dsdsadsa"
        self.assertEqual(None, reg_text.next_section_offsets(text, 201))

        text = u"Supplement I\n\n§ 201.3 sdsa\nsdd dsdsadsa"
        self.assertEqual(None, reg_text.next_section_offsets(text, 201))

    def test_sections(self):
        text = u"\n\n§ 201.3 sdsa\nsdd dsdsadsa \n asdsas\nSection\n"
        text += u"§ 201.20 dfds \n sdfds § 201.2 saddsa \n\n sdsadsa\n"
        text += u"Appendix A to Part 201 bssds \n sdsdsad \nsadad \ndsada"
        self.assertEqual([(2, 45), (45, 93)], reg_text.sections(text, 201))

    def test_subparts(self):
        text = u"Subpart A—First subpart\n"
        text += u"§ 201.20 dfds \n sdfds § 201.2 saddsa \n\n sdsadsa\n"
        text += u"\nSubpart B—Second subpart\n"
        text += u"§ 2015 dfds \n sdfds § 20132 saddsa \n\n sdsadsa\n"
        self.assertEqual([(0, 73), (73, 144)], reg_text.subparts(text))

    def test_build_section_tree(self):
        """Should be just like build_paragraph tree, but with a label"""
        line1 = u"§ 201.20 Super Awesome Section"
        line2 = u"\nThis (a) is a good (1) test (2) of (3) some (b) body."
        tree = reg_text.build_section_tree(line1+line2, 201)
        p_tree = reg_text.regParser.build_tree(line2, label=['201', '20'])
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
            tree = reg_text.build_section_tree(line1+line2, 201)
            self.assertEqual(tree.text, "\n")
            self.assertEqual(1, len(tree.children))
            child = tree.children[0]
            self.assertEqual(child.text, line2[1:])
            self.assertEqual(0, len(child.children))

    def test_build_section_tree_a_or_b1(self):
        line1 = u"§ 201.20 Super Awesome Section"
        line2 = "\n(a) a (b) b (c) see paragraph (a) or (b)(1) of "
        line2 += "this section"

        tree = reg_text.build_section_tree(line1+line2, 201)
        self.assertEqual(tree.text, "\n")
        self.assertEqual(3, len(tree.children))
        child = tree.children[2]
        self.assertEqual(child.text, "(c) see paragraph (a) or (b)(1) " +
                                     "of this section")
        self.assertEqual(0, len(child.children))

    def test_build_section_tree_appendix_through(self):
        line1 = u"§ 201.20 Super Awesome Section"
        line2 = "\n(a) references Model Forms A-30(a) through (b)"

        tree = reg_text.build_section_tree(line1+line2, 201)
        self.assertEqual(tree.text, "\n")
        self.assertEqual(1, len(tree.children))

    def test_build_section_tree_nonspace(self):
        line1 = u"§ 201.20. Super Awesome Section"
        line2 = "\nContents contents"

        tree = reg_text.build_section_tree(line1+line2, 201)
        self.assertEqual(line2, tree.text)
        self.assertEqual(['201', '20'], tree.label)
        self.assertEqual(line1, tree.title)
        self.assertEqual(0, len(tree.children))

    def test_build_section_tree_italics_as_plaintext(self):
        line1 = u"§ 201.20 Super Awesome Section"
        line2 = "\n(a)(1)(i) paragraphs (c)(2)(ii)(A)(1) and (B) content"

        tree = reg_text.build_section_tree(line1+line2, 201)
        self.assertEqual(1, len(tree.children))
        self.assertEqual(['201', '20'], tree.label)
        tree = tree.children[0]
        self.assertEqual(1, len(tree.children))
        self.assertEqual(['201', '20', 'a'], tree.label)
        tree = tree.children[0]
        self.assertEqual(1, len(tree.children))
        self.assertEqual(['201', '20', 'a', '1'], tree.label)
        tree = tree.children[0]
        self.assertEqual(0, len(tree.children))
        self.assertEqual(['201', '20', 'a', '1', 'i'], tree.label)

    def test_build_subparts_tree_reserver(self):
        text = u"Subpart C—[Reserved]"

        tree, _ = reg_text.build_subparts_tree(
            text, 8888, lambda p: reg_text.build_subpart(text, 8888))
        self.assertEqual('', tree.text)
        self.assertEqual('subpart', tree.node_type)
        self.assertEqual(['8888', 'Subpart', 'C'], tree.label)
        self.assertEqual([], tree.children)
        self.assertEqual('[Reserved]', tree.title)
