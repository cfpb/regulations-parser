# vim: set fileencoding=utf-8
from regparser.layer.terms import Ref, Terms
from regparser.tree.struct import Node
import settings
from unittest import TestCase

class LayerTermTest(TestCase):

    def setUp(self):
        self.original_ignores = settings.IGNORE_DEFINITIONS_IN
        settings.IGNORE_DEFINITIONS_IN = []

    def tearDown(self):
        settings.IGNORE_DEFINITIONS_IN = self.original_ignores

    def test_has_definitions(self):
        t = Terms(None)
        self.assertFalse(t.has_definitions(Node("This has no defs",
            label=['101', '22', 'c'])))
        self.assertFalse(t.has_definitions(Node("No Def", 
            label=["101", "22", "c"], title="No def")))
        self.assertFalse(t.has_definitions(
            Node("Tomatoes do not meet the definition 'vegetable'",
                label=['101', '22', 'c'])))
        self.assertFalse(t.has_definitions(Node("Definition",
            label=['101', 'A', '1'], node_type=Node.APPENDIX)))
        self.assertFalse(t.has_definitions(Node("Definition",
            label=['101', '11', Node.INTERP_MARK], node_type=Node.INTERP)))
        self.assertTrue(t.has_definitions(
            Node("Definition. This has a definition.",
                label=['101', '22', 'c'])))
        self.assertTrue(t.has_definitions(
            Node("Definitions. This has multiple!", label=['101','22','c'])))
        self.assertTrue(t.has_definitions(Node("No body", 
            label=['101', '22', 'c'], title="But definition is in the title")))

    def test_has_definitions_p_marker(self):
        t = Terms(None)
        node = Node("(a) Definitions. For purposes of this " +
            "section except blah", label=['88', '20', 'a'])
        self.assertTrue(t.has_definitions(node))

    def test_has_definitions_the_term_means(self):
        t = Terms(None)
        node = Node("(a) The term Bob means awesome", label=['88', '20', 'a'])
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
        text4 = u'Still no terms, but'
        text4a = u'the next one does'
        xml_text4a = text4a
        text4b = u'(4) Thing means a thing that is defined'
        xml_text4b = u'(4) <E T="03">Thing</E> means a thing that is defined'
        text4c = u'This term means should not match'
        xml_text4c = u'<E T="03">This term</E> means should not match'
        text4d = u'(d) Term1 or term2 means stuff'
        xml_text4d = u'(d) <E T="03">Term1</E> or <E T="03">term2></E> means stuff'
        text4e = u'(e) Well-meaning lawyers means people who do weird things'
        xml_text4e = u'(e) <E T="03">Well-meaning lawyers</E> means people who do weird things'
        text4f = u'(f) Huge billowy clouds means I want to take a nap'
        xml_text4f = u'(f) <E T="03">Huge billowy clouds</E> means I want to take a nap'

        node4a = Node(text4a, label=['eee'])
        node4b = Node(text4b, label=['fff'])
        node4c = Node(text4c, label=['ggg'])
        node4d = Node(text4d, label=['hhh'])
        node4e = Node(text4e, label=['iii'])
        node4f = Node(text4f, label=['jjj'])
        node4a.tagged_text = xml_text4a
        node4b.tagged_text = xml_text4b
        node4c.tagged_text = xml_text4c
        node4d.tagged_text = xml_text4d
        node4e.tagged_text = xml_text4e
        node4f.tagged_text = xml_text4f

        tree = Node(children=[ 
            Node(text1, label=['aaa']),
            Node(text2, label=['bbb']),
            Node(text3, children=[ 
                Node(text3a, label=['ccc']),
                Node(children=[ 
                    Node(text3bi, [Node(text3biA)], ['ddd']),
                    Node(text3bii)
                ]),
                Node(text3c)
            ]),
            Node(text4, children=[
                node4a,
                node4b,
                node4c,
                node4d,
                node4e,
                node4f
            ])
        ])
        defs, excluded = t.node_definitions(tree)
        self.assertEqual(8, len(defs))
        self.assertTrue(Ref('word', 'aaa', (12,16)) in defs)
        self.assertTrue(Ref('another word', 'bbb', (8,20)) in defs)
        self.assertTrue(Ref('moree', 'bbb', (32,37)) in defs)
        self.assertTrue(Ref('does see', 'ccc', (15,23)) in defs)
        self.assertTrue(Ref('subchildren', 'ddd', (7,18)) in defs)
        self.assertTrue(Ref('thing', 'fff', (4,9)) in defs)
        self.assertTrue(Ref('well-meaning lawyers', 'iii', (4,24)) in defs)
        self.assertTrue(Ref('huge billowy clouds', 'jjj', (4,23)) in defs)

    def test_node_defintions_act(self):
        t = Terms(None)
        node = Node(u'“Act” means some reference to 99 U.S.C. 1234')
        included, excluded = t.node_definitions(node)
        self.assertEqual([], included)
        self.assertEqual(1, len(excluded))

        node = Node(u'“Act” means something else entirely')
        included, excluded = t.node_definitions(node)
        self.assertEqual(1, len(included))
        self.assertEqual([], excluded)

    def test_node_definitions_exclusion(self):
        t = Terms(None)
        node = Node('',[
            Node(u'“Bologna” is a type of deli meat',
                label=['1']),
            Node(u'Let us not forget that the term “bologna” does not ' +
                'include turtle meat', label=['2'])
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
        node = Node(label=['1000', '22', 'a', '5'])
        node.text = 'For the purposes of this part, blah blah'
        self.assertEqual([('1000',), ('1000', Node.INTERP_MARK)], 
            t.definitions_scopes(node))

        t.subpart_map = {
            'SubPart 1': ['a', '22'],
            'Other': []
        }
        node.text = 'For the purposes of this subpart, yada yada'
        self.assertEqual([('1000', 'a'), ('1000', '22'), 
            ('1000', 'a', Node.INTERP_MARK), ('1000', '22', Node.INTERP_MARK)],
            t.definitions_scopes(node))

        node.text = 'For the purposes of this section, blah blah'
        self.assertEqual([('1000', '22'), ('1000', '22', Node.INTERP_MARK)], 
                t.definitions_scopes(node))

        node.text = 'For the purposes of this paragraph, blah blah'
        self.assertEqual([('1000','22','a','5'), 
            ('1000','22','a','5',Node.INTERP_MARK)], 
            t.definitions_scopes(node))

        node.text = 'Default'
        self.assertEqual([('1000',), ('1000', Node.INTERP_MARK)], 
            t.definitions_scopes(node))

    def test_pre_process(self):
        noname_subpart = Node('', label=['88', 'Subpart'],
            node_type=Node.EMPTYPART, children=[
                Node(u"Definition. For the purposes of this part, "
                     + u"“abcd” is an alphabet", label=['88', '1'])])
        xqxq_subpart = Node('', title='Subpart XQXQ: The unreadable',
            label=['88', 'Subpart', 'XQXQ'], node_type=Node.SUBPART,
            children=[
                Node(label=['88', '2'], children=[
                    Node(label=['88', '2', 'a'],
                         text="Definitions come later for the purposes of "
                              + "this section ", children=[
                            Node(u"“AXAX” means axe-cop",
                                 label=['88', '2', 'a', '1'])]),
                    Node(label=['88', '2', 'b'], children=[
                        Node(label=['88', '2', 'b', 'i'], children=[
                            Node(label=['88', '2', 'b', 'i', 'A'],
                                 text=u"Definition. “Awesome sauce” means "
                                      +"great for the purposes of this "
                                      + "paragraph",)])])])])
        tree = Node(label=['88'], children=[noname_subpart, xqxq_subpart])
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

    def test_excluded_offsets(self):
        t = Terms(None)
        t.scoped_terms['_'] = [
            Ref('term', 'lablab', (4,6)), Ref('other', 'lablab', (8,9)),
            Ref('more', 'nonnon', (1,8))
        ]
        self.assertEqual([(4,6), (8,9)], 
                t.excluded_offsets('lablab', 'Some text'))
        self.assertEqual([(1,8)], t.excluded_offsets('nonnon', 'Other'))
        self.assertEqual([], t.excluded_offsets('ababab', 'Ab ab ab'))

    def test_excluded_offsets_blacklist(self):
        t = Terms(None)
        t.scoped_terms['_'] = [Ref('bourgeois', '12-Q-2', 'Def')]
        settings.IGNORE_DEFINITIONS_IN = ['bourgeois pig']
        excluded = t.excluded_offsets('12-3', 'You are a bourgeois pig!')
        self.assertEqual([(10,23)], excluded)

    def test_excluded_offsets_blacklist_word_boundaries(self):
        t = Terms(None)
        t.scoped_terms['_'] = [Ref('act', '28-6-d', 'Def def def')]
        settings.IGNORE_DEFINITIONS_IN = ['shed act']
        excluded = t.excluded_offsets('28-9', "That's a watershed act")
        self.assertEqual([], excluded)

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

    def test_calculate_offsets_pluralized1(self):
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

    def test_calculate_offsets_pluralized2(self):
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

    def test_calculate_offsets_overlap(self):
        applicable_terms = [('mad cow disease', 'mc'), ('goes mad', 'gm')]
        text = 'There goes mad cow disease'
        t = Terms(None)
        matches = t.calculate_offsets(text, applicable_terms)
        self.assertEqual(1, len(matches))
        _, ref, offsets = matches[0]
        self.assertEqual('mc', ref)
        self.assertEqual('mad cow disease', text[offsets[0][0]:offsets[0][1]])

    def test_calculate_offsets_word_part(self):
        """If a defined term is part of another word, don't include it"""
        applicable_terms = [('act', 'a')]
        text = "I am about to act on this transaction."
        t = Terms(None)
        matches = t.calculate_offsets(text, applicable_terms)
        self.assertEqual(1, len(matches))
        self.assertEqual(1, len(matches[0][2]))

    def test_calculate_offsets_exclusions(self):
        applicable_terms = [('act', 'a')]
        text = "This text defines the 'fudge act'"
        t = Terms(None)
        self.assertEqual([], 
                t.calculate_offsets(text, applicable_terms, [(23,32)]))
        self.assertEqual([('act', 'a', [(29,32)])],
                t.calculate_offsets(text, applicable_terms, [(1,5)]))

    def test_process(self):
        t = Terms(Node(children=[
            Node("ABC5", children=[Node("child")], label=['ref1']),
            Node("AABBCC5", label=['ref2']),
            Node("ABC3", label=['ref3']),
            Node("AAA3", label=['ref4']),
            Node("ABCABC3", label=['ref5']),
            Node("ABCOTHER", label=['ref6']),
            Node("ZZZOTHER", label=['ref7']),
        ]))
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
        layer_el = t.process(Node(
            "This has abc, aabbcc, aaa, abcabc, and zzz",
            label=["101", "22", "b", "2", "ii"]))
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
        tree = Node(children=[
            Node("Defining secret phrase.", label=['AB', 'a']),
            Node("Has secret phrase. Then some other content", 
                label=['AB', 'b'])
        ], label=['AB'])
        t = Terms(tree)
        t.scoped_terms = {
            ('AB',): [Ref("secret phrase", "AB-a", (9,22))]
        }
        #   Term is defined in the first child
        self.assertEqual([], t.process(tree.children[0]))
        self.assertEqual(1, len(t.process(tree.children[1])))
