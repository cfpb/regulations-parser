# vim: set fileencoding=utf-8
from parser.layer.terms import Terms
from parser.tree import struct
from unittest import TestCase

class LayerTermTest(TestCase):

    def test_has_definitions(self):
        t = Terms(None)
        valid_label = struct.label("101-22-c", ["101", "22", "c"])
        self.assertFalse(t.has_definitions(struct.node("This has no defs",
            label=valid_label)))
        self.assertFalse(t.has_definitions(struct.node("No Def", 
            label=struct.label("101-22-c", ["101", "22", "c"], "No def"))))
        self.assertFalse(t.has_definitions(
            struct.node("Tomatoes do not meet the definition 'vegetable'",
                label=valid_label)))
        self.assertFalse(t.has_definitions(struct.node("Definition", [],
            struct.label("101-A-1", ["101", "A", "1"]))))
        self.assertFalse(t.has_definitions(struct.node("Definition", [],
            struct.label("101-Interpretations-11", 
                ["101", "Interpretations", "11"]))))
        self.assertTrue(t.has_definitions(
            struct.node("Definition. This has a definition.",
                label=valid_label)))
        self.assertTrue(t.has_definitions(
            struct.node("Definitions. This has multiple!", label=valid_label)))
        self.assertTrue(t.has_definitions(
            struct.node("No body",
                label=struct.label("101-22-c", ["101", "22", "c"],
                "But definition is in the title"))))

    def test_has_definitions_p_marker(self):
        t = Terms(None)
        node = struct.node("(a) Definitions. For purposes of this " +
            "section except blah", 
            [], 
            struct.label('88-20-a', ['88', '20', 'a']))
        self.assertTrue(t.has_definitions(node))

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

    def test_node_defintions_act(self):
        t = Terms(None)
        node = struct.node(u'“Act” means some reference to 99 U.S.C. 1234')
        self.assertEqual([], t.node_definitions(node))

        node = struct.node(u'“Act” means something else entirely')
        self.assertEqual(1, len(t.node_definitions(node)))

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
            struct.node(u"Definition. For the purposes of this part, "
                + u"“abcd” is an alphabet", 
                label=struct.label("88-1", ["88","1"])),
            struct.node(children=[
                struct.node(u"Definitions come later for the purposes of "
                    + "this section ", children=[
                        struct.node(u"“AXAX” means axe-cop",
                            label=struct.label("88-2-a-1", ["88","2","a","1"])
                        )],
                    label=struct.label("88-2-a", ["88","2","a"])),
                struct.node(children=[struct.node(children=[struct.node(
                    u"Definition. “Awesome sauce” means great for the " +
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

    def test_calculate_offsets(self):
        applicable_terms = [('rock band', 'a'), ('band', 'b'), ('drum', 'c'),
                ('other thing', 'd')]
        text = "I am in a rock band. That's a band with a drum, a rock drum."
        t = Terms(None)
        matches = t.calculate_offsets(text, applicable_terms)
        self.assertEqual(3, len(matches))
        found = [False, False, False]
        for _, ref, offsets in matches:
            if ref == 'a' and offsets == [(10,19)]:
                found[0] = True
            if ref == 'b' and offsets == [(30,34)]:
                found[1] = True
            if ref == 'c' and offsets == [(42,46), (55,59)]:
                found[2] = True
        self.assertEqual([True,True,True], found)

    def test_calculate_offsets_lexical_container(self):
        applicable_terms = [('access device', 'a'), ('device', 'd')]
        text = "This access device is fantastic!"
        t = Terms(None)
        matches = t.calculate_offsets(text, applicable_terms)
        self.assertEqual(1, len(matches))
        _, ref, offsets = matches[0]
        self.assertEqual('a', ref)
        self.assertEqual([(5,18)], offsets)

    def test_calculate_offsets_word_part(self):
        """If a defined term is part of another word, don't include it"""
        applicable_terms = [('act', 'a')]
        text = "I am about to act on this transaction."
        t = Terms(None)
        matches = t.calculate_offsets(text, applicable_terms)
        self.assertEqual(1, len(matches))
        self.assertEqual(1, len(matches[0][2]))

    def test_process(self):
        t = Terms(struct.node(children=[
            struct.node("ABC5", children=[struct.node("child")],
                label=struct.label("ref1")),
            struct.node("AABBCC5", label=struct.label("ref2")),
            struct.node("ABC3", label=struct.label("ref3")),
            struct.node("AAA3", label=struct.label("ref4")),
            struct.node("ABCABC3", label=struct.label("ref5")),
            struct.node("ABCOTHER", label=struct.label("ref6")),
            struct.node("ZZZOTHER", label=struct.label("ref7"))]))
        t.scoped_terms = {
                ("101", "22", "b", "2", "ii"): [
                    ("abc", "ref1"),
                    ("aabbcc", "ref2")],
                ("101", "22", "b"): [
                    ("abc", "ref3"),
                    ("aaa", "ref4"),
                    ("abcabc", "ref5")],
                ("101", "22", "b", "2", "iii"): [
                    ("abc", "ref6"),
                    ("zzz", "ref7")]
                }
        #   Check that the return value is correct
        layer_el = t.process(struct.node(
            "This has abc, aabbcc, aaa, abcabc, and zzz", [],
            struct.label("101-22-b-2-ii", ["101", "22", "b", "2", "ii"])))
        self.assertEqual(4, len(layer_el))
        found = [False, False, False, False]
        for ref_obj in layer_el:
            if ref_obj['ref'] == 'abc:ref1':
                found[0] = True
            if ref_obj['ref'] == 'aabbcc:ref2':
                found[1] = True
            if ref_obj['ref'] == 'aaa:ref4':
                found[2] = True
            if ref_obj['ref'] == 'abcabc:ref5':
                found[3] = True
        self.assertEqual([True, True, True, True], found)

        #   Finally, verify that the associated references are present
        self.assertTrue('referenced' in t.layer)

        referenced = t.layer['referenced']
        self.assertTrue('abcabc:ref5' in referenced)
        self.assertEqual('ABCABC3', referenced['abcabc:ref5']['text'])
        self.assertEqual('abcabc', referenced['abcabc:ref5']['term'])
        self.assertEqual('ref5', referenced['abcabc:ref5']['reference'])

        self.assertTrue('aaa:ref4' in referenced)
        self.assertEqual('AAA3', referenced['aaa:ref4']['text'])
        self.assertEqual('aaa', referenced['aaa:ref4']['term'])
        self.assertEqual('ref4', referenced['aaa:ref4']['reference'])

        self.assertTrue('aabbcc:ref2' in referenced)
        self.assertEqual('AABBCC5', referenced['aabbcc:ref2']['text'])
        self.assertEqual('aabbcc', referenced['aabbcc:ref2']['term'])
        self.assertEqual('ref2', referenced['aabbcc:ref2']['reference'])

        self.assertTrue('abc:ref1' in referenced)
        self.assertEqual('ABC5child', referenced['abc:ref1']['text'])
        self.assertEqual('abc', referenced['abc:ref1']['term'])
        self.assertEqual('ref1', referenced['abc:ref1']['reference'])
