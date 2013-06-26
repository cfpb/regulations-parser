# vim: set fileencoding=utf-8
from parser.layer.terms import Ref, Terms
from parser.tree import struct
import settings
from unittest import TestCase

class LayerTermTest(TestCase):

    def setUp(self):
        self.original_subpart = settings.SUBPART_STARTS
        settings.SUBPART_STARTS = {'1': None}

    def tearDown(self):
        settings.SUBPART_STARTS = self.original_subpart

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

    def test_has_definitions_the_term_means(self):
        t = Terms(None)
        node = struct.node("(a) The term Bob means awesome", [],
            struct.label('88-20-a', ['88', '20', 'a']))
        self.assertTrue(t.has_definitions(node))

    def test_is_exclusion(self):
        t = Terms(None)
        self.assertFalse(t.is_exclusion('ex', 'ex ex ex', []))
        self.assertFalse(t.is_exclusion('ex', 'ex ex ex', 
            [Ref('abc', '1', (0, 0))]))
        self.assertFalse(t.is_exclusion('ex', 'ex ex ex', 
            [Ref('ex', '1', (0, 0))]))
        self.assertTrue(t.is_exclusion('ex', 
            u'Something something the term “ex” does not include potato',
            [Ref('ex', '1', (0, 0))]))
        self.assertFalse(t.is_exclusion('ex', 
            u'Something something the term “ex” does not include potato',
            [Ref('abc', '1', (0, 0))]))

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
        defs, excluded = t.node_definitions(tree)
        self.assertEqual(5, len(defs))
        self.assertTrue(Ref('word', 'aaa', (12,16)) in defs)
        self.assertTrue(Ref('another word', 'bbb', (8,20)) in defs)
        self.assertTrue(Ref('moree', 'bbb', (32,37)) in defs)
        self.assertTrue(Ref('does see', 'ccc', (15,23)) in defs)
        self.assertTrue(Ref('subchildren', 'ddd', (7,18)) in defs)

    def test_node_defintions_act(self):
        t = Terms(None)
        node = struct.node(u'“Act” means some reference to 99 U.S.C. 1234')
        included, excluded = t.node_definitions(node)
        self.assertEqual([], included)
        self.assertEqual(1, len(excluded))

        node = struct.node(u'“Act” means something else entirely')
        included, excluded = t.node_definitions(node)
        self.assertEqual(1, len(included))
        self.assertEqual([], excluded)

    def test_node_definitions_exclusion(self):
        t = Terms(None)
        node = struct.node('',[
            struct.node(u'“Bologna” is a type of deli meat',
                label=struct.label('1')),
            struct.node(u'Let us not forget that the term “bologna” ' +
                'does not include turtle meat', label=struct.label('2'))
        ])
        included, excluded = t.node_definitions(node)
        self.assertEqual([Ref('bologna', '1', (1,8))], included)
        self.assertEqual([Ref('bologna', '2', (33,40))], excluded)

    def test_subpart_scope(self):
        t = Terms(None)
        t.subpart_map = { 
            None: ['1','2','3'], 
            'A': ['7','5','0'],
            'Q': ['99', 'abc', 'q']
        }
        self.assertEqual([['111','1'], ['111','2'], ['111','3']], 
                t.subpart_scope(['111', '3']))
        self.assertEqual([['115','7'], ['115','5'], ['115','0']], 
                t.subpart_scope(['115', '5']))
        self.assertEqual([['62','99'], ['62','abc'], ['62','q']], 
                t.subpart_scope(['62', 'abc']))
        self.assertEqual([], t.subpart_scope(['71', 'Z']))

    def test_definitions_scopes(self):
        t = Terms(None)
        node = struct.node("", 
                label=struct.label("1000-22-a-5", ['1000', '22', 'a', '5']))
        node['text'] = 'For the purposes of this part, blah blah'
        self.assertEqual([('1000',)], t.definitions_scopes(node))

        t.subpart_map = {
            'SubPart 1': ['a', '22'],
            'Other': []
        }
        node['text'] = 'For the purposes of this subpart, yada yada'
        self.assertEqual([('1000', 'a'), ('1000', '22'), 
            ('1000','Interpretations','a'), ('1000','Interpretations','22')],
            t.definitions_scopes(node))

        node['text'] = 'For the purposes of this section, blah blah'
        self.assertEqual([('1000', '22'), ('1000', 'Interpretations', '22')], 
                t.definitions_scopes(node))

        node['text'] = 'For the purposes of this paragraph, blah blah'
        self.assertEqual([('1000','22','a','5'), ('1000', 'Interpretations',
            '22', '(a)(5)')], t.definitions_scopes(node))

        node['text'] = 'Default'
        self.assertEqual([('1000',)], t.definitions_scopes(node))

    def test_pre_process(self):
        settings.SUBPART_STARTS = {'2': 'XQXQ'}
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
                ], label=struct.label('88-2', ['88','2']))
            ])
        t = Terms(tree)
        t.pre_process()

        self.assertTrue(('88',) in t.scoped_terms)
        self.assertEqual([Ref('abcd', '88-1', (44,48))], 
                t.scoped_terms[('88',)])
        self.assertTrue(('88','2') in t.scoped_terms)
        self.assertEqual([Ref('axax', '88-2-a-1', (1,5))], 
            t.scoped_terms[('88','2')])
        self.assertTrue(('88','2','b','i','A') in t.scoped_terms)
        self.assertEqual([Ref('awesome sauce', '88-2-b-i-A', (13,26))], 
                t.scoped_terms[('88','2','b','i','A')])

        #   Check subparts are correct
        self.assertEqual({None: ['1'], 'XQXQ': ['2']}, dict(t.subpart_map))

        # Finally, make sure the references are added
        referenced = t.layer['referenced']
        self.assertTrue('abcd:88-1' in referenced)
        self.assertEqual('abcd', referenced['abcd:88-1']['term'])
        self.assertEqual('88-1', referenced['abcd:88-1']['reference'])
        self.assertEqual((44,48), referenced['abcd:88-1']['position'])

        self.assertTrue('axax:88-2-a-1' in referenced)
        self.assertEqual('axax', referenced['axax:88-2-a-1']['term'])
        self.assertEqual('88-2-a-1', referenced['axax:88-2-a-1']['reference'])
        self.assertEqual((1,5), referenced['axax:88-2-a-1']['position'])

        self.assertTrue('awesome sauce:88-2-b-i-A' in referenced)
        self.assertEqual('awesome sauce', 
            referenced['awesome sauce:88-2-b-i-A']['term'])
        self.assertEqual('88-2-b-i-A', 
            referenced['awesome sauce:88-2-b-i-A']['reference'])
        self.assertEqual((13,26), 
            referenced['awesome sauce:88-2-b-i-A']['position'])

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

    def test_calculate_offsets_pluralized(self):
        applicable_terms = [('rock band', 'a'), ('band', 'b'), ('drum', 'c'),
                ('other thing', 'd')]
        text = "I am in a rock band. That's a band with a drum, a rock drum. Many bands. "
        t = Terms(None)
        matches = t.calculate_offsets(text, applicable_terms)
        self.assertEqual(4, len(matches))
        found = [False, False, False, False]
        for _, ref, offsets in matches:
            if ref == 'a' and offsets == [(10,19)]:
                found[0] = True
            if ref == 'b' and offsets == [(66,71)]:
                found[1] = True
            if ref == 'b' and offsets == [(30,34)]:
                found[2] = True
            if ref == 'c' and offsets == [(42,46), (55,59)]:
                found[3] = True
        self.assertEqual([True,True,True,True], found)

    def test_calculate_offsets_pluralized(self):
        applicable_terms = [('activity', 'a'), ('other thing', 'd')]
        text = "activity, activities."
        t = Terms(None)
        matches = t.calculate_offsets(text, applicable_terms)
        self.assertEqual(2, len(matches))

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
                    Ref("abc", "ref1", (1,2)),
                    Ref("aabbcc", "ref2", (2,3))],
                ("101", "22", "b"): [
                    Ref("abc", "ref3", (3,4)),
                    Ref("aaa", "ref4", (4,5)),
                    Ref("abcabc", "ref5", (5,6))],
                ("101", "22", "b", "2", "iii"): [
                    Ref("abc", "ref6", (6,7)),
                    Ref("zzz", "ref7", (7,8))]
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

    def test_process_label_in_node(self):
        """Make sure we don't highlight definitions that are being defined
        in this paragraph."""
        tree = struct.node(children=[
            struct.node("Defining secret phrase.", 
                label=struct.label("AB-a", ["AB", "a"])),
            struct.node("Has secret phrase. Then some other content", 
                label=struct.label("AB-b", ["AB", "b"]))
        ], label=struct.label("AB", ["AB"]))
        t = Terms(tree)
        t.scoped_terms = {
            ('AB',): [Ref("secret phrase", "AB-a", (9,22))]
        }
        #   Term is defined in the first child
        self.assertEqual([], t.process(tree['children'][0]))
        self.assertEqual(1, len(t.process(tree['children'][1])))
