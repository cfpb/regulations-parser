from regparser.tree.struct import *
from unittest import TestCase

class DepthTreeTest(TestCase):

    def test_walk(self):
        n1 = node("1")
        n2 = node("2")
        n3 = node("3")
        n4 = node("4")

        n1['children'] = [n2, n3]
        n2['children'] = [n4]

        order = []
        def add_node(n):
            order.append(n)
            if not n == n2:
                return n['text']
        ret_val = walk(n1, add_node)
        self.assertEqual([n1, n2, n4, n3], order)
        self.assertEqual(["1", "4", "3"], ret_val)

    def test_find(self):
        n1 = node('n1', label=label('n1'))
        n2 = node('n2', label=label('n2'))
        n3 = node('n3', label=label('n3'))
        n4 = node('n4', label=label('n4'))
        n5 = node('n5', label=label('n1'))

        self.assertEqual(n1, find(n1, 'n1'))
        self.assertEqual(n1, find(node(children=[n1,n2,n3]), 'n1'))
        self.assertEqual(n1, find(node(children=[n2,n1,n3]), 'n1'))
        self.assertEqual(n1, find(node(children=[n2,n3,n1]), 'n1'))
        self.assertEqual(n5, find(node(children=[n2,n5,n3,n1]), 'n1'))
        self.assertEqual(None, find(n2, 'n1'))
        self.assertEqual(n2, find(n2, 'n2'))

    def test_join_text(self):
        n1 = node("1")
        n2 = node("2")
        n3 = node("3")
        n4 = node("4")

        n1['children'] = [n2, n3]
        n2['children'] = [n4]

        self.assertEqual("1243", join_text(n1))
        self.assertEqual("24", join_text(n2))
        self.assertEqual("3", join_text(n3))
        self.assertEqual("4", join_text(n4))

    def test_encode(self):
        n1 = Node('typtyp', 'texttext', [Node('t')], ['1','2','3'])
        n2 = Node('someType', title='Some Title')

        enc = NodeEncoder(sort_keys=True)
        self.assertEqual(enc.encode(n1), enc.encode({
            'typ': 'typtyp',
            'text': 'texttext',
            'children': [{'typ':'t', 'text':'', 'children':[], 'label':[]}],
            'label': ['1', '2', '3']
        }))
        self.assertEqual(enc.encode(n2), enc.encode({
            'typ': 'someType',
            'text': '',
            'children': [],
            'label': [],
            'title': 'Some Title'
        }))
