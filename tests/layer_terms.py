# vim: set fileencoding=utf-8
from parser.layer.terms import Terms
from parser.tree import struct
from unittest import TestCase

class LayerTermTest(TestCase):

    def test_has_definitions(self):
        t = Terms(None)
        self.assertFalse(t.has_definitions(struct.node("This has no defs")))
        self.assertTrue(t.has_definitions(
            struct.node("This has at least one definition.")))
        self.assertTrue(t.has_definitions(
            struct.node("This has.\nmultiple Definitions.")))

    def test_node_definitions(self):
        t = Terms(None)
        text1 = u'This has a “worD” and then more'
        text2 = u'I have “anotheR word” term and “moree”'
        text3 = u'This has no defs'
        text3a = u'But the child “DoeS sEe”?'
        text3bi = u'As do “subchildren”'
        text3biA = u'Also has no terms'
        text3bii = u'Has no terms'
        text3c = u'Also has no terms'
        tree = struct.node(children=[ 
            struct.node(text1, label=struct.label("aaa")),
            struct.node(text2, label=struct.label("bbb")),
            struct.node(text3, children=[ 
                struct.node(text3a, label=struct.label('ccc')),
                struct.node(children=[ 
                    struct.node(text3bi, [struct.node(text3biA)], 
                        struct.label('ddd')),
                    struct.node(text3bii)
                    ]),
                struct.node(text3c)
                ])
            ])
        defs = t.node_definitions(tree)
        self.assertEqual(5, len(defs))
        self.assertTrue((u'word', 'aaa') in defs)
        self.assertTrue((u'another word', 'bbb') in defs)
        self.assertTrue((u'moree', 'bbb') in defs)
        self.assertTrue((u'does see', 'ccc') in defs)
        self.assertTrue((u'subchildren', 'ddd') in defs)

    def test_definitions_scope(self):
        t = Terms(None)
        node = struct.node("", 
                label=struct.label("1000-22-a-5", ['1000', '22', 'a', '5']))
        node['text'] = 'For the purposes of this part, blah blah'
        self.assertEqual(('1000',), t.definitions_scope(node))

        node['text'] = 'For the purposes of this section, blah blah'
        self.assertEqual(('1000', '22'), t.definitions_scope(node))

        node['text'] = 'For the purposes of this paragraph, blah blah'
        self.assertEqual(('1000','22','a','5'), t.definitions_scope(node))

        node['text'] = 'Default'
        self.assertEqual(('1000',), t.definitions_scope(node))

    def test_pre_process(self):
        tree = struct.node(children=[
            struct.node(u"For the purposes of this part, “abcd” has the " +
                "definition alphabet", label=struct.label("88-1", ["88","1"])),
            struct.node(children=[
                struct.node(u"For the purposes of this section, " +
                    "definitions come later",
                    children=[struct.node(u"“AXAX” means axe-cop",
                        label=struct.label("88-2-a-1", ["88","2","a","1"]))
                        ],
                    label=struct.label("88-2-a", ["88","2","a"])),
                struct.node(children=[struct.node(children=[struct.node(
                    u"The definition “awesome sauce” means great for the " +
                    "purposes of this paragraph", 
                    label=struct.label("88-2-b-i-A",
                        ["88","2","b","i","A"]))])])
                ])
            ])
        t = Terms(tree)
        t.pre_process()

        self.assertTrue(('88',) in t.scoped_terms)
        self.assertEqual([(u'abcd', '88-1')], t.scoped_terms[('88',)])
        self.assertTrue(('88','2') in t.scoped_terms)
        self.assertEqual([(u'axax', '88-2-a-1')], t.scoped_terms[('88','2')])
        self.assertTrue(('88','2','b','i','A') in t.scoped_terms)
        self.assertEqual([(u'awesome sauce', '88-2-b-i-A')], 
                t.scoped_terms[('88','2','b','i','A')])
