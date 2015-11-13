# vim: set encoding=utf-8
from regparser.citations import Label
from regparser.tree import interpretation
from regparser.tree.struct import Node
from unittest import TestCase


class DepthInterpretationTreeTest(TestCase):
    def test_interpParser_iv(self):
        """Make sure a bug with the 4th roman numeral is fixed."""
        sub1 = 'i. One '
        sub2 = 'ii. Two '
        sub3 = 'iii. Three '
        sub4 = 'iv. Four '
        sub5 = 'v. Five '
        sub6 = 'vi. Six'
        text = "1. This is some section\n" + sub1+sub2+sub3+sub4+sub5+sub6
        tree = interpretation.interpParser.build_tree(text, 1)
        self.assertTrue(1, len(tree.children))
        self.assertTrue(6, len(tree.children[0].children))
        self.assertEqual(sub1, tree.children[0].children[0].text)
        self.assertEqual(sub2, tree.children[0].children[1].text)
        self.assertEqual(sub3, tree.children[0].children[2].text)
        self.assertEqual(sub4, tree.children[0].children[3].text)
        self.assertEqual(sub5, tree.children[0].children[4].text)
        self.assertEqual(sub6, tree.children[0].children[5].text)

    def test_interpParser_section(self):
        """Make sure a bug with a label as part of a section number is
        fixed."""
        text = "1. some section referencing 2002.99"
        tree = interpretation.interpParser.build_tree(text, 1)
        self.assertTrue(1, tree.children)
        self.assertEqual(text, tree.children[0].text)

    def test_interpParser_appendix(self):
        """Confirm a bug with a label as part of an appendix reference is
        fixed."""
        text = "1. some section referencing Appendix-2. Then more content"
        tree = interpretation.interpParser.build_tree(text, 1)
        self.assertTrue(1, len(tree.children))
        self.assertEqual(text, tree.children[0].text)

    def test_build_without_subs(self):
        title = "Something here"
        body = "\nAnd then more\nSome more\nAnd yet another line"
        result = interpretation.build(title + body, '100')
        self.assertEqual(body, result.text)
        self.assertEqual(['100', Node.INTERP_MARK], result.label)
        self.assertEqual(title, result.title)
        self.assertEqual(0, len(result.children))

    def test_build_with_appendices(self):
        title = "Awesome Interpretations"
        sec1 = "Section 199.22 Interps"
        sec2 = "Section 199.11 Interps Vengence"
        app1 = "Appendix W - Whoa whoa whoa"
        app2 = "Appendix R - Redrum"
        node = interpretation.build("\n".join([title, sec1, sec2, app1, app2]),
                                    199)
        self.assertEqual(title, node.title)
        self.assertEqual(4, len(node.children))
        self.assertEqual(sec1, node.children[0].title)
        self.assertEqual(sec2, node.children[1].title)
        self.assertEqual(app1, node.children[2].title)
        self.assertEqual(app2, node.children[3].title)

    def test_build_with_subs(self):
        text = "Something here\nSection 100.22\nmore more\nSection 100.5\n"
        text += "and more"
        result = interpretation.build(text, "100")
        self.assertEqual("", result.text.strip())
        self.assertEqual(["100", "Interp"], result.label)
        self.assertEqual("Something here", result.title)
        self.assertEqual(2, len(result.children))

        node = result.children[0]
        self.assertEqual("\nmore more\n", node.text)
        self.assertEqual(['100', '22', Node.INTERP_MARK], node.label)
        self.assertEqual(0, len(node.children))

        node = result.children[1]
        self.assertEqual("\nand more", node.text)
        self.assertEqual(['100', '5', Node.INTERP_MARK], node.label)
        self.assertEqual(0, len(node.children))

    def test_build_interp_headers(self):
        text = "\nSection 876.2 Definitions\n\n2(r) Def1\n\n2(r)(4) SubSub"
        result = interpretation.build(text, "876")

        self.assertEqual(['876', Node.INTERP_MARK], result.label)
        self.assertEqual(1, len(result.children))

        child = result.children[0]
        self.assertEqual(['876', '2', Node.INTERP_MARK], child.label)
        self.assertEqual(1, len(child.children))

        child = child.children[0]
        self.assertEqual(['876', '2', 'r', Node.INTERP_MARK], child.label)
        self.assertEqual(1, len(child.children))

        child = child.children[0]
        self.assertEqual(['876', '2', 'r', '4', Node.INTERP_MARK], child.label)

    def test_segment_tree_appendix(self):
        title = "Appendix Q - The Questions"
        body = "1. Regulation text 2. Some more i. With ii. Subparts"
        node = interpretation.segment_tree(title + "\n" + body, '100', ['100'])
        self.assertEqual(title, node.title)
        self.assertEqual(['100', 'Q', Node.INTERP_MARK], node.label)
        self.assertEqual(2, len(node.children))
        self.assertEqual(2, len(node.children[1].children))

    def test_segment_tree_paragraph(self):
        title = "Paragraph 3(b)"
        depth1 = "1. Inline depth and then\n"
        depth2i = "i. some "
        depth2ii = "ii. sub "
        depth2iii = "iii. sections"
        depth2 = "2. Start of line with "
        text = title + "\n" + depth1 + depth2 + depth2i + depth2ii + depth2iii
        a_tree = interpretation.segment_tree(text, '111', ['111', '3', 'b'])
        self.assertEqual(['111', '3', 'b', Node.INTERP_MARK], a_tree.label)
        self.assertEqual('Paragraph 3(b)', a_tree.title)
        self.assertEqual("", a_tree.text.strip())
        self.assertEqual(2, len(a_tree.children))

        node = a_tree.children[0]
        self.assertEqual(['111', '3', 'b', Node.INTERP_MARK, '1'], node.label)
        self.assertEqual(depth1, node.text)
        self.assertEqual(0, len(node.children))

        node = a_tree.children[1]
        self.assertEqual(['111', '3', 'b', Node.INTERP_MARK, '2'], node.label)
        self.assertEqual(depth2, node.text)
        self.assertEqual(3, len(node.children))

        node = a_tree.children[1].children[0]
        self.assertEqual(['111', '3', 'b', Node.INTERP_MARK, '2', 'i'],
                         node.label)
        self.assertEqual(depth2i, node.text)
        self.assertEqual(0, len(node.children))

        node = a_tree.children[1].children[1]
        self.assertEqual(['111', '3', 'b', Node.INTERP_MARK, '2', 'ii'],
                         node.label)
        self.assertEqual(depth2ii, node.text)
        self.assertEqual(0, len(node.children))

        node = a_tree.children[1].children[2]
        self.assertEqual(['111', '3', 'b', Node.INTERP_MARK, '2', 'iii'],
                         node.label)
        self.assertEqual(depth2iii, node.text)
        self.assertEqual(0, len(node.children))

    def test_segment_tree(self):
        title = "Section 105.11 This is a section title"
        body = "1. Some contents\n2. Other data\ni. Hello hello"
        non_title = "\n" + body
        result = interpretation.segment_tree(title + non_title, '105', ['105'])
        self.assertEqual("\n", result.text)
        self.assertEqual(2, len(result.children))

        child = result.children[0]
        self.assertEqual("1. Some contents\n", child.text)
        self.assertEqual([], child.children)
        self.assertEqual(['105', '11', Node.INTERP_MARK, '1'], child.label)

        child = result.children[1]
        self.assertEqual("2. Other data\n", child.text)
        self.assertEqual(1, len(child.children))
        self.assertEqual(['105', '11', Node.INTERP_MARK, '2'], child.label)

        child = result.children[1].children[0]
        self.assertEqual("i. Hello hello", child.text)
        self.assertEqual([], child.children)
        self.assertEqual(['105', '11', Node.INTERP_MARK, '2', 'i'],
                         child.label)

    def test_segment_tree_no_children(self):
        title = "Section 105.11 This is a section title"
        body = "Body of the interpretation's section"
        non_title = "\n" + body
        result = interpretation.segment_tree(title + non_title, '105', ['105'])
        self.assertEqual(non_title, result.text)
        self.assertEqual(['105', '11', Node.INTERP_MARK], result.label)
        self.assertEqual(0, len(result.children))

    def test_segment_tree_label(self):
        """The section tree should include the section header as label"""
        title = "Section 105.11 This is a section title"
        body = "Body of the interpretation's section"
        non_title = "\n" + body
        result = interpretation.segment_tree(title + non_title, '105', ['105'])
        self.assertEqual(title, result.title)

    def test_segment_tree_with_comment(self):
        text = "Paragraph 20(b)(2)\n1. Some suff.\n"
        text += "2. Ends with see comment 20(b)(2)-4.ii.\n"
        text += "3. Then three\ni. Sub bit\nA. More\n4. Four"

        result = interpretation.segment_tree(text, '28', ['28'])
        self.assertEqual(4, len(result.children))

    def test_segment_by_header(self):
        text = "Interp interp\n"
        s22 = "Section 87.22Some Title\nSome content\n"
        s23 = "Paragraph 23(b)(4)(v)(Z)\nPar par\n"
        s25 = "Section 87.25 Title\nEven more info here\n"
        sb = "Appendix B-Some Title\nContent content\n"
        self.assertEqual(
            [(len(text), len(text + s22)),
             (len(text+s22), len(text+s22+s23)),
             (len(text+s22+s23), len(text+s22+s23+s25)),
             (len(text+s22+s23+s25), len(text+s22+s23+s25+sb))],
            interpretation.segment_by_header(text + s22 + s23 + s25 + sb, 87))

    def test_segment_by_header_ten(self):
        text = "Interp interp\n"
        s10a = "10(a) Some Content\n\n"
        s10a1 = "10(a)(1) Some subcontent\nContent content\n"
        s10b = "10(b) Second level paragraph\nContennnnnt"

        self.assertEqual(
            3, len(interpretation.segment_by_header(
                text + s10a + s10a1 + s10b, 0)))

    def test_text_to_labels(self):
        text = u"9(c)(2)(iii) Charges not Covered by § 1026.6(b)(1) and "
        text += "(b)(2)"
        self.assertEqual(
            [['1111', '9', 'c', '2', 'iii', 'Interp']],
            interpretation.text_to_labels(text,
                                          Label(part='1111', comment=True)))

        text = "Paragraphs 4(b)(7) and (b)(8)."
        self.assertEqual(
            [['1111', '4', 'b', '7', 'Interp'],
             ['1111', '4', 'b', '8', 'Interp']],
            interpretation.text_to_labels(text,
                                          Label(part='1111', comment=True)))

        text = "Appendices G and H-Something"
        self.assertEqual(
            [['1111', 'G', 'Interp'], ['1111', 'H', 'Interp']],
            interpretation.text_to_labels(text,
                                          Label(part='1111', comment=True)))

        text = "Paragraph 38(l)(7)(i)(A)(2)."
        self.assertEqual(
            [['1111', '38', 'l', '7', 'i', 'A', '2', 'Interp']],
            interpretation.text_to_labels(text,
                                          Label(part='1111', comment=True)))

    def test_merge_labels(self):
        labels = [['1021', 'A'], ['1021', 'B']]
        self.assertEqual(['1021', 'A_B'], interpretation.merge_labels(labels))

        labels = [['1021', 'A', '1'], ['1021', 'A', '2']]
        self.assertEqual(['1021', 'A', '1_2'],
                         interpretation.merge_labels(labels))
