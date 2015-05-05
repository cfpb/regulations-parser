import json
from unittest import TestCase

from regparser.tree import struct


class DepthTreeTest(TestCase):

    def test_walk(self):
        n1 = struct.Node("1")
        n2 = struct.Node("2")
        n3 = struct.Node("3")
        n4 = struct.Node("4")

        n1.children = [n2, n3]
        n2.children = [n4]

        order = []

        def add_node(n):
            order.append(n)
            if not n == n2:
                return n.text
        ret_val = struct.walk(n1, add_node)
        self.assertEqual([n1, n2, n4, n3], order)
        self.assertEqual(["1", "4", "3"], ret_val)

    def test_find(self):
        n1 = struct.Node('n1', label=['n1'])
        n2 = struct.Node('n2', label=['n2'])
        n3 = struct.Node('n3', label=['n3'])
        n5 = struct.Node('n5', label=['n1'])

        self.assertEqual(n1, struct.find(n1, 'n1'))
        self.assertEqual(
            n1, struct.find(struct.Node(children=[n1, n2, n3]), 'n1'))
        self.assertEqual(
            n1, struct.find(struct.Node(children=[n2, n1, n3]), 'n1'))
        self.assertEqual(
            n1, struct.find(struct.Node(children=[n2, n3, n1]), 'n1'))
        self.assertEqual(
            n5, struct.find(struct.Node(children=[n2, n5, n3, n1]), 'n1'))
        self.assertEqual(None, struct.find(n2, 'n1'))
        self.assertEqual(n2, struct.find(n2, 'n2'))

    def test_join_text(self):
        n1 = struct.Node("1")
        n2 = struct.Node("2")
        n3 = struct.Node("3")
        n4 = struct.Node("4")

        n1.children = [n2, n3]
        n2.children = [n4]

        self.assertEqual("1243", struct.join_text(n1))
        self.assertEqual("24", struct.join_text(n2))
        self.assertEqual("3", struct.join_text(n3))
        self.assertEqual("4", struct.join_text(n4))

    def test_encode(self):
        n1 = struct.Node('texttext', [struct.Node(node_type='t')],
                         ['1', '2', '3'])
        n2 = struct.Node(node_type='someType', title='Some Title')

        enc = struct.NodeEncoder(sort_keys=True)
        self.assertEqual(enc.encode(n1), enc.encode({
            'node_type': struct.Node.REGTEXT,
            'text': 'texttext',
            'children': [
                {'node_type': 't', 'text': '', 'children': [], 'label': []}],
            'label': ['1', '2', '3']
        }))
        self.assertEqual(enc.encode(n2), enc.encode({
            'node_type': 'someType',
            'text': '',
            'children': [],
            'label': [],
            'title': 'Some Title'
        }))

    def test_decode(self):
        d = {'some': 'example'}
        self.assertEqual(
            d, json.loads(json.dumps(d), object_hook=struct.node_decode_hook))

        d = {'text': 't', 'label': [2, 3, 4], 'node_type': 'regtext',
             'children': [1, 2, 3]}
        self.assertEqual(
            struct.Node('t', [1, 2, 3], [2, 3, 4],
                        node_type=struct.Node.REGTEXT),
            json.loads(json.dumps(d), object_hook=struct.node_decode_hook))

        d = {'text': 't', 'label': [2, 3, 4], 'node_type': 'ttt',
             'children': [1, 2, 3], 'title': 'Example Title'}
        self.assertEqual(
            struct.Node('t', [1, 2, 3], [2, 3, 4], 'Example Title', u'ttt'),
            json.loads(json.dumps(d), object_hook=struct.node_decode_hook))

    def test_treeify(self):
        n1 = struct.Node(label=['1'])
        n1b = struct.Node(label=['1', 'b'])
        n1b5 = struct.Node(label=['1', 'b', '5'])

        n2 = struct.Node(label=['2'])

        result = struct.treeify([n1, n1b5, n2, n1b])
        self.assertEqual(sorted(result), sorted([
            struct.Node(label=['1'], children=[
                struct.Node(label=['1', 'b'], children=[
                    struct.Node(label=['1', 'b', '5'])
                ])
            ]),
            struct.Node(label=['2'])
        ]))

    def test_treeify_interp(self):
        n1 = struct.Node(label=['1', 'Interp'])
        n1b = struct.Node(label=['1', 'b', 'Interp'])
        n1b5 = struct.Node(label=['1', 'b', '5', 'Interp'])

        result = struct.treeify([n1, n1b, n1b5])
        self.assertEqual(result, [
            struct.Node(label=['1', 'Interp'], children=[
                struct.Node(label=['1', 'b', 'Interp'], children=[
                    struct.Node(label=['1', 'b', '5', 'Interp'])
                ])
            ])
        ])

    def test_treeify_keep_children(self):
        n1 = struct.Node(label=['1'])
        n1b = struct.Node(label=['1', 'b'], children=[1, 2, 3])

        self.assertEqual(struct.treeify([n1, n1b]), [
            struct.Node(label=['1'], children=[
                struct.Node(label=['1', 'b'], children=[1, 2, 3])
            ])
        ])


class FrozenNodeTests(TestCase):
    def test_comparison(self):
        """Frozen nodes with the same values are considered equal"""
        args = {'text': 'text', 'children': ['a', 'b'], 'label': ['b', 'c'],
                'title': 'title', 'tagged_text': 'tagged_text'}
        left = struct.FrozenNode(**args)
        right = struct.FrozenNode(**args)
        self.assertEqual(left, right)

    def test_from_node(self):
        """Conversion from a normal struct Node should be accurate and
        recursive"""
        root = struct.Node(
            text='rtext', label=['root'], title='ttt',
            node_type=struct.Node.INTERP, children=[
                struct.Node('child_text', [], ['root', 'child'])])
        root.tagged_text = 'rtagged'
        frozen = struct.FrozenNode.from_node(root)
        self.assertEqual(frozen.text, 'rtext')
        self.assertEqual(frozen.label, ('root',))
        self.assertEqual(frozen.title, 'ttt')
        self.assertEqual(frozen.node_type, struct.Node.INTERP)
        self.assertEqual(frozen.tagged_text, 'rtagged')
        self.assertEqual(len(frozen.children), 1)

        child = frozen.children[0]
        self.assertEqual(child.text, 'child_text')
        self.assertEqual(child.label, ('root', 'child'))
        self.assertEqual(child.title, '')
        self.assertEqual(child.node_type, struct.Node.REGTEXT)
        self.assertEqual(child.tagged_text, '')
        self.assertEqual(child.children, ())
