#vim: set encoding=utf-8
from unittest import TestCase
from parser.layer import table_of_contents
from parser.tree.struct import node, label

class TocTest(TestCase):

    def test_toc_generation(self):
        c1 = node(text='', children=[], label=label('1005-2', parts=['1005', '2'], title='Authority and Purpose'))
        c2 = node(text='', children=[], label=label('1005-3', parts=['1005', '3'], title='Definitions'))
        c3 = node(text='', children=[], label=label('1005-4', parts=['1005', '4'], title='Coverage'))

        n = node(text='', children=[c1, c2, c3], label=label('', parts=['1005']))

        parser = table_of_contents.TableOfContentsLayer(None)
        toc = parser.process(n)
        self.assertEqual(len(toc), 3)
        self.assertEqual(toc[0].keys(), ['index', 'title'])
        self.assertEqual(toc[0]['index'], ['1005', '2'])
        self.assertEqual(toc[1]['index'], ['1005', '3'])
        self.assertEqual(toc[2]['index'], ['1005', '4'])

    def test_toc_no_children(self):
        tree = node(text='', children=[], label=label('1005', parts=['1005'], title=''))

        parser = table_of_contents.TableOfContentsLayer(None)
        toc = parser.process(tree)
        self.assertEqual(len(toc), 0)

    def test_build_tree(self):
        c1 = node(text='', children=[], label=label('1005-A-2', parts=['1005', 'A', '2'], title='Authority and Purpose'))
        c2 = node(text='', children=[], label=label('1005-A-3', parts=['1005', 'A', '3'], title='Definitions'))
        c3 = node(text='', children=[], label=label('1005-A-4', parts=['1005', 'A', '4'], title='Coverage'))

        a1 = node(text='', children=[c1, c2, c3], label=label('1005-A', parts=['1005', 'A']))

        tree = node(text='', children=[a1], label=label('1005', parts=['1005'], title='Zombie Manifesto'))

        parser = table_of_contents.TableOfContentsLayer(tree)
        toc_layer = parser.build()
        self.assertEquals(toc_layer.keys(), ['1005-A'])
        self.assertEqual(len(toc_layer['1005-A']), 3)
        self.assertEqual(toc_layer['1005-A'][0]['index'], ['1005', 'A', '2'])
