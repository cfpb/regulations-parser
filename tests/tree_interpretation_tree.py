from mock import patch
from reg_parser.tree import struct
from reg_parser.tree.interpretation.tree import *
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
        tree = interpParser.build_paragraph_tree(text, 1)
        self.assertTrue(1, len(tree['children']))
        self.assertTrue(6, len(tree['children'][0]['children']))
        self.assertEqual(sub1, tree['children'][0]['children'][0]['text'])
        self.assertEqual(sub2, tree['children'][0]['children'][1]['text'])
        self.assertEqual(sub3, tree['children'][0]['children'][2]['text'])
        self.assertEqual(sub4, tree['children'][0]['children'][3]['text'])
        self.assertEqual(sub5, tree['children'][0]['children'][4]['text'])
        self.assertEqual(sub6, tree['children'][0]['children'][5]['text'])

    def test_interpParser_section(self):
        """Make sure a bug with a label as part of a section number is
        fixed."""
        text = "1. some section referencing 2002.99"
        tree = interpParser.build_paragraph_tree(text, 1)
        self.assertTrue(1, len(tree['children']))
        self.assertEqual(text, tree['children'][0]['text'])

    def test_interpParser_appendix(self):
        """Confirm a bug with a label as part of an appendix reference is
        fixed."""
        text = "1. some section referencing Appendix-2. Then more content"
        tree = interpParser.build_paragraph_tree(text, 1)
        self.assertTrue(1, len(tree['children']))
        self.assertEqual(text, tree['children'][0]['text'])

    def test_build_without_subs(self):
        title = "Something here"
        body = "\nAnd then more\nSome more\nAnd yet another line"
        result = build(title + body, 100)
        self.assertEqual(body, result['text'])
        self.assertEqual("100-Interpretations", result['label']['text'])
        self.assertEqual(["100", "Interpretations"], result['label']['parts'])
        self.assertEqual(title, result['label']['title'])
        self.assertEqual(0, len(result['children']))

    def test_build_with_appendices(self):
        title = "Awesome Interpretations"
        sec1 = "Section 199.22 Interps"
        sec2 = "Section 199.11 Interps Vengence"
        app1 = "Appendix W - Whoa whoa whoa"
        app2 = "Appendix R - Redrum"
        node = build("\n".join([title, sec1, sec2, app1, app2]), 199)
        self.assertTrue('title' in node['label'])
        self.assertEqual(title, node['label']['title'])
        self.assertEqual(4, len(node['children']))
        for i in range(4):
            self.assertTrue('title' in node['children'][i]['label'])
        self.assertEqual(sec1, node['children'][0]['label']['title'])
        self.assertEqual(sec2, node['children'][1]['label']['title'])
        self.assertEqual(app1, node['children'][2]['label']['title'])
        self.assertEqual(app2, node['children'][3]['label']['title'])

    def test_build_with_subs(self):
        text = "Something here\nSection 100.22\nmore more\nSection 100.5\n"
        text += "and more"
        result = build(text, 100)
        self.assertEqual("", result['text'].strip())
        self.assertEqual("100-Interpretations", result['label']['text'])
        self.assertEqual(["100", "Interpretations"], result['label']['parts'])
        self.assertEqual("Something here", result['label']['title'])
        self.assertEqual(2, len(result['children']))

        node = result['children'][0]
        self.assertEqual("\nmore more\n", node['text'])
        self.assertEqual('100-Interpretations-22', node['label']['text'])
        self.assertEqual(['100', 'Interpretations', '22'], 
                node['label']['parts'])
        self.assertEqual(0, len(node['children']))

        node = result['children'][1]
        self.assertEqual("\nand more", node['text'])
        self.assertEqual('100-Interpretations-5', node['label']['text'])
        self.assertEqual(['100', 'Interpretations', '5'], 
                node['label']['parts'])
        self.assertEqual(0, len(node['children']))


    def test_segment_tree_appendix(self):
        title = "Appendix Q - The Questions"
        body = "1. Regulation text 2. Some more i. With ii. Subparts"
        node = segment_tree(title + "\n" + body, 0, struct.label('Start'))
        self.assertTrue('title' in node['label'])
        self.assertEqual(title, node['label']['title'])
        self.assertEqual('Start-Q', node['label']['text'])
        self.assertEqual(['Q'], node['label']['parts'])
        self.assertEqual(2, len(node['children']))
        self.assertEqual(2, len(node['children'][1]['children']))

    def test_segment_tree_paragraph(self):
        title = "Paragraph 3(b)"
        depth1 = "1. Inline depth and then\n"
        depth2i = "i. some "
        depth2ii = "ii. sub "
        depth2iii = "iii. sections"
        depth2 = "2. Start of line with "
        text = title + "\n" + depth1 + depth2 + depth2i + depth2ii + depth2iii
        a_tree = segment_tree(text, 3, struct.label())
        self.assertEqual(struct.label("-3(b)", ["3(b)"], title), 
                a_tree['label'])
        self.assertEqual("", a_tree['text'].strip())
        self.assertEqual(2, len(a_tree['children']))

        node = a_tree['children'][0]
        self.assertEqual(struct.label("-3(b)-1", ["3(b)", "1"]), node['label'])
        self.assertEqual(depth1, node['text'])
        self.assertEqual(0, len(node['children']))

        node = a_tree['children'][1]
        self.assertEqual(struct.label("-3(b)-2", ["3(b)", "2"]), node['label'])
        self.assertEqual(depth2, node['text'])
        self.assertEqual(3, len(node['children']))

        node = a_tree['children'][1]['children'][0]
        self.assertEqual(struct.label("-3(b)-2-i", ["3(b)", "2", "i"]), 
                node['label'])
        self.assertEqual(depth2i, node['text'])
        self.assertEqual(0, len(node['children']))

        node = a_tree['children'][1]['children'][1]
        self.assertEqual(struct.label("-3(b)-2-ii", ["3(b)", "2", "ii"]), 
                node['label'])
        self.assertEqual(depth2ii, node['text'])
        self.assertEqual(0, len(node['children']))

        node = a_tree['children'][1]['children'][2]
        self.assertEqual(struct.label("-3(b)-2-iii", ["3(b)", "2", "iii"]), 
                node['label'])
        self.assertEqual(depth2iii, node['text'])
        self.assertEqual(0, len(node['children']))

    def test_segment_tree(self):
        title = "Section 105.11 This is a section title"
        body = "1. Some contents\n2. Other data\ni. Hello hello"
        non_title = "\n" + body
        result = segment_tree(title + non_title, 105, 
                struct.label("abcd", ['abcd']))
        self.assertEqual("\n", result['text'])
        self.assertEqual(2, len(result['children']))

        child = result['children'][0]
        self.assertEqual("1. Some contents\n", child['text'])
        self.assertEqual([], child['children'])
        self.assertEqual('abcd-11-1', child['label']['text'])
        self.assertEqual(['abcd', '11', '1'], child['label']['parts'])

        child = result['children'][1]
        self.assertEqual("2. Other data\n", child['text'])
        self.assertEqual(1, len(child['children']))
        self.assertEqual('abcd-11-2', child['label']['text'])
        self.assertEqual(['abcd', '11', '2'], child['label']['parts'])
        
        child = result['children'][1]['children'][0]
        self.assertEqual("i. Hello hello", child['text'])
        self.assertEqual([], child['children'])
        self.assertEqual('abcd-11-2-i', child['label']['text'])
        self.assertEqual(['abcd', '11', '2', 'i'], child['label']['parts'])

    def test_segment_tree_no_children(self):
        title = "Section 105.11 This is a section title"
        body = "Body of the interpretation's section"
        non_title = "\n" + body
        result = segment_tree(title + non_title, 105, struct.label("abcd"))
        self.assertEqual(non_title, result['text'])
        self.assertEqual("abcd-11", result['label']['text'])
        self.assertEqual(0, len(result['children']))

    def test_segment_tree_label(self):
        """The section tree should include the section header as label"""
        title = "Section 105.11 This is a section title"
        body = "Body of the interpretation's section"
        non_title = "\n" + body
        result = segment_tree(title + non_title, 105, struct.label("abcd"))
        self.assertTrue('title' in result['label'])
        self.assertEqual(title, result['label']['title'])

    def test_segment_tree_with_comment(self):
        text = "Paragraph 20(b)(2)\n1. Some suff.\n"
        text += "2. Ends with see comment 20(b)(2)-4.ii.\n"
        text += "3. Then three\ni. Sub bit\nA. More\n4. Four"

        result = segment_tree(text, 28, struct.label("abcd"))
        self.assertEqual(4, len(result['children']))

    def test_label_text_section(self):
        text = "Section 105.11"
        label_text = get_interpretation_label_text(text, 105)
        self.assertEquals(label_text, '11')

    def test_label_text_section(self):
        text = "3(c)(4) Pandas"
        label_text = get_interpretation_label_text(text, 105)
        self.assertEquals(label_text, '3(c)(4)')
