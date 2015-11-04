from regparser.tree.appendix import tree
from regparser.tree.struct import Node
from unittest import TestCase


class DepthAppendixTreeTest(TestCase):

    def test_generic_tree_no_children(self):
        text = "Non title text"
        node = tree.generic_tree(text, ['lab'])
        self.assertEqual(Node(text, label=['lab'], node_type=Node.APPENDIX),
                         node)

    def test_generic_tree_with_children(self):
        start = "some text\n"
        t1 = "Title Text One"
        b1 = "\nSome body text\nsomething\nsomething\n"
        t2 = "Section Two"
        b2 = "\nSomething else\nhere"
        t = tree.generic_tree(start + t1 + b1 + t2 + b2, ['s', 'l'],
                              'Some label')

        self.assertEqual(start, t.text)
        self.assertEqual(['s', 'l'], t.label)
        self.assertEqual('Some label', t.title)
        self.assertEqual(2, len(t.children))

        node = t.children[0]
        self.assertEqual(b1, node.text)
        self.assertEqual(['s', 'l', 'a'], node.label)
        self.assertEqual(t1, node.title)
        self.assertEqual(0, len(node.children))

        node = t.children[1]
        self.assertEqual(b2, node.text)
        self.assertEqual(['s', 'l', 'b'], node.label)
        self.assertEqual(t2, node.title)
        self.assertEqual(0, len(node.children))

    def test_paragraph_tree_no_children(self):
        text = "Non title text"
        node = tree.paragraph_tree('A', [], text, ['lab'])
        self.assertEqual(Node(text, label=['lab'], node_type=Node.APPENDIX),
                         node)

    def test_paragraph_tree_with_children(self):
        fill = "dsfdffsfs\n"
        t1 = 'Q-3 This is the title'
        p1 = '\nSome paragraph\nContent\nmore\ncontent\n'
        t2 = 'Q-5--Spacing spacing'
        p2 = '\nMore paragraphs\nWe love them all\nParagraphs\n'
        t3 = 'Q-44 - Title here'
        p3 = '\nThird paragraph here'
        root = tree.paragraph_tree(
            'Q',
            [(len(fill), len(fill+t1+p1)),
             (len(fill+t1+p1), len(fill+t1+p1+t2+p2)),
             (len(fill+t1+p1+t2+p2), len(fill+t1+p1+t2+p2+t3+p3))],
            fill+t1+p1+t2+p2+t3+p3,
            ['l'])
        self.assertEqual(fill, root.text)
        self.assertEqual(['l'], root.label)
        self.assertEqual(3, len(root.children))

        node = root.children[0]
        self.assertEqual(p1, node.text)
        self.assertEqual(['l', '3'], node.label)
        self.assertEqual(t1, node.title)
        self.assertEqual(0, len(node.children))

        node = root.children[1]
        self.assertEqual(p2, node.text)
        self.assertEqual(['l', '5'], node.label)
        self.assertEqual(t2, node.title)
        self.assertEqual(0, len(node.children))

        node = root.children[2]
        self.assertEqual(p3, node.text)
        self.assertEqual(['l', '44'], node.label)
        self.assertEqual(t3, node.title)
        self.assertEqual(0, len(node.children))

    def test_trees_from(self):
        reg_text = "Some reg text\nOther reg text\nSection 55. etc.\n"
        titleC = "Appendix C to Part 22 The Reckoning"
        bodyC = "\nSome content\nWith no structure\n"
        titleJ = "Appendix J to Part 22 Junior Notes"
        bodyJ = "\nTitle One\ncontent content\nTitle Two\nmore content\n"
        titleR = "Appendix R to Part 22 Reserved"
        bodyR = "\nR-1--Some Section\nmore more\nR-5--Header\nthen more"

        text = reg_text + titleC + bodyC + titleJ + bodyJ + titleR + bodyR

        nodes = tree.trees_from(text, 22, ['22'])
        self.assertTrue(3, len(nodes))

        self.assertEqual(tree.generic_tree(bodyC, ['22', 'C'], titleC),
                         nodes[0])
        self.assertEqual(tree.generic_tree(bodyJ, ['22', 'J'], titleJ),
                         nodes[1])
        self.assertEqual(
            tree.paragraph_tree('R', [(1, 29), (29, len(bodyR))], bodyR,
                                ['22', 'R'], titleR),
            nodes[2])

    def test_letter_for(self):
        self.assertEqual('a', tree.letter_for(0))
        self.assertEqual('z', tree.letter_for(25))
        self.assertEqual('aa', tree.letter_for(26))
        self.assertEqual('ab', tree.letter_for(27))
        self.assertEqual('ba', tree.letter_for(52))
        #  We have 27 sets of letters; 1 with 1 character each, 26 with 2
        self.assertEqual('zz', tree.letter_for(26*27-1))
