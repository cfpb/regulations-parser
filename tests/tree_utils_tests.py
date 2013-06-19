#vim: set encoding=utf-8
import unittest
from parser.tree.xml_parser import tree_utils
from parser.tree.node_stack import NodeStack
from lxml import etree

class TreeUtilsTest(unittest.TestCase):
    def test_split_text(self):  
        text = "(A) Apples (B) Bananas (Z) Zebras"
        tokens = ['(A)', '(B)']

        result = tree_utils.split_text(text, tokens)
        expected = ['(A) Apples ', '(B) Bananas (Z) Zebras']
        self.assertEqual(expected, result)

    def test_consecutive_markers(self):
        text = "(A)(2) Bananas"
        tokens = ['(A)', '(2)']

        result = tree_utils.split_text(text, tokens)
        expected = ['(A)', '(2) Bananas']
        self.assertEqual(expected, result)

    def test_get_paragraph_marker(self):
        result = [m for m in tree_utils.get_paragraph_markers('(k)(2)(iii) abc (j)')]
        self.assertListEqual(['k', '2', 'iii'], result)

    def test_get_node_text(self):
        text = '<P>(a)<E T="03">Fruit.</E>Apples,<PRTPAGE P="102"/> and Pineapples</P>'
        doc = etree.fromstring(text)
        result = tree_utils.get_node_text(doc)

        self.assertEquals('(a) <E T="03">Fruit.</E>Apples, and Pineapples', result)

    def test_unwind_stack(self):
        level_one_n = {'label': {'parts': ['272']}, 'children':[]}
        level_two_n = {'label': {'parts': ['a']}, 'children':[]}

        m_stack = NodeStack()
        m_stack.push_last((1, level_one_n))
        tree_utils.add_to_stack(m_stack, 2, level_two_n)

        self.assertEquals(m_stack.size(), 2)
        tree_utils.unwind_stack(m_stack)

        self.assertEquals(m_stack.size(), 1)

        n = m_stack.pop()[0][1]
        self.assertEqual(n['children'][0]['label']['parts'], ['272', 'a'])
