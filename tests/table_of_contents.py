#vim: set encoding=utf-8
from unittest import TestCase
from parser.layer import table_of_contents

class TocTest(TestCase):

    def test_toc_generation(self):
        node =  { 'label': {'parts':['1005']}, 
            'children' : [
                {'label':{'parts':['1005', '2'], 'title':'Authority and Purpose'}},
                {'label':{'parts':['1005', '3'], 'title':'Definitions'}},
                {'label':{'parts':['1005', '4'], 'title':'Coverage'}}
            ],
        }

        parser = table_of_contents.TableOfContentsLayer(None)
        toc = parser.process(node)
        self.assertEqual(len(toc), 3)
        self.assertEqual(toc[0].keys(), ['index', 'title'])
        self.assertEqual(toc[0]['index'], ['1005', '2'])
        self.assertEqual(toc[1]['index'], ['1005', '3'])
        self.assertEqual(toc[2]['index'], ['1005', '4'])

    def test_toc_no_children(self):
        node =  { 'label': {'parts':['1005']}, 
            'children' : [],
        }
        parser = table_of_contents.TableOfContentsLayer(None)
        toc = parser.process(node)
        self.assertEqual(len(toc), 0)

    def test_build_tree(self):
        tree = {'label':{'parts':['1005']},
            'title': 'Regulation E',
            'children' : [
                {'label': {'parts':['1005', 'A']}, 
                'children' : [
                    {'label':{'parts':['1005', 'A', '2'], 'title':'Authority and Purpose'}},
                    {'label':{'parts':['1005', 'A', '3'], 'title':'Definitions'}},
                    {'label':{'parts':['1005', 'A', '4'], 'title':'Coverage'}}
            ],}]
            }
        parser = table_of_contents.TableOfContentsLayer(tree)
        toc_layer = parser.build(sections_list=[['1005', 'A']])
        self.assertEquals(toc_layer.keys(), ['1005-A'])
        self.assertEqual(len(toc_layer['1005-A']), 3)
        self.assertEqual(toc_layer['1005-A'][0]['index'], ['1005', 'A', '2'])
