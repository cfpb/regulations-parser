#vim: set encoding=utf-8
from unittest import TestCase
from regparser.layer import table_of_contents
from regparser.tree.struct import Node

class TocTest(TestCase):

    def test_toc_generation(self):
        c1 = Node(label=['1005', '2'], title='Authority and Purpose')
        c2 = Node(label=['1005', '3'], title='Definitions')
        c3 = Node(label=['1005', '4'], title='Coverage')

        n = Node(children=[c1, c2, c3], label=['1005'])

        parser = table_of_contents.TableOfContentsLayer(None)
        toc = parser.process(n)
        self.assertEqual(len(toc), 3)
        self.assertEqual(toc[0].keys(), ['index', 'title'])
        self.assertEqual(toc[0]['index'], ['1005', '2'])
        self.assertEqual(toc[1]['index'], ['1005', '3'])
        self.assertEqual(toc[2]['index'], ['1005', '4'])

    def test_toc_no_children(self):
        tree = Node(label=['1005'])

        parser = table_of_contents.TableOfContentsLayer(None)
        toc = parser.process(tree)
        self.assertEqual(len(toc), 0)

    def test_build_tree(self):
        c1 = Node(label=['1005', 'A', '2'], title='Authority and Purpose')
        c2 = Node(label=['1005', 'A', '3'], title='Definitions')
        c3 = Node(label=['1005', 'A', '4'], title='Coverage')

        a1 = Node(children=[c1, c2, c3], label=['1005', 'A'])

        tree = Node(children=[a1], label=['1005'], title='Zombie Manifesto')

        parser = table_of_contents.TableOfContentsLayer(tree)
        toc_layer = parser.build()
        self.assertEquals(toc_layer.keys(), ['1005-A'])
        self.assertEqual(len(toc_layer['1005-A']), 3)
        self.assertEqual(toc_layer['1005-A'][0]['index'], ['1005', 'A', '2'])
