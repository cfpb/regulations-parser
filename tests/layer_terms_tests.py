# vim: set fileencoding=utf-8
from regparser.layer.terms import ParentStack, Ref, Terms
from regparser.tree.struct import Node
import settings
from unittest import TestCase


class LayerTermTest(TestCase):

    def setUp(self):
        self.original_ignores = settings.IGNORE_DEFINITIONS_IN
        settings.IGNORE_DEFINITIONS_IN = {'ALL': {}}

    def tearDown(self):
        settings.IGNORE_DEFINITIONS_IN = self.original_ignores

    def test_has_parent_definitions_indicator(self):
        t = Terms(None)
        stack = ParentStack()
        stack.add(0, Node("This has no defs"))
        self.assertFalse(t.has_parent_definitions_indicator(stack))
        stack.add(1, Node("No Def", title="No def"))
        self.assertFalse(t.has_parent_definitions_indicator(stack))
        stack.add(2, Node("Tomatoes do not meet the definition 'vegetable'"))
        self.assertFalse(t.has_parent_definitions_indicator(stack))

        stack.add(3, Node("Definition. This has a definition."))
        self.assertTrue(t.has_parent_definitions_indicator(stack))
        stack.pop()
        self.assertFalse(t.has_parent_definitions_indicator(stack))

        stack.add(3, Node("Definitions. This has multiple!"))
        self.assertTrue(t.has_parent_definitions_indicator(stack))
        stack.pop()
        self.assertFalse(t.has_parent_definitions_indicator(stack))

        stack.add(3, Node("No body", title="But Definition is in the title"))
        self.assertTrue(t.has_parent_definitions_indicator(stack))

    def test_has_parent_definitions_indicator_p_marker(self):
        t = Terms(None)
        stack = ParentStack()
        stack.add(0, Node("(a) Definitions. For purposes of this " +
                          "section except blah"))
        self.assertTrue(t.has_parent_definitions_indicator(stack))

    def test_has_parent_definitions_indicator_the_term_means(self):
        t = Terms(None)
        stack = ParentStack()
        stack.add(0, Node('Contains no terms or definitions'))
        self.assertFalse(t.has_parent_definitions_indicator(stack))
        stack.add(1, Node("(a) The term Bob means awesome"))
        self.assertTrue(t.has_parent_definitions_indicator(stack))
        stack.add(2, Node("No defs either"))
        self.assertTrue(t.has_parent_definitions_indicator(stack))

        stack.pop()
        stack.pop()
        stack.add(1, Node(u"(a) “Term” means some stuff"))
        self.assertTrue(t.has_parent_definitions_indicator(stack))

        stack.pop()
        stack.add(1, Node("(a) The term Bob refers to"))
        self.assertTrue(t.has_parent_definitions_indicator(stack))

    def test_is_exclusion(self):
        t = Terms(None)
        n = Node('ex ex ex', label=['1111', '2'])
        self.assertFalse(t.is_exclusion('ex', n))

        t.scoped_terms = {('1111',): [Ref('abc', '1', (0, 0))]}
        self.assertFalse(t.is_exclusion('ex', n))

        t.scoped_terms = {('1111',): [Ref('ex', '1', (0, 0))]}
        self.assertFalse(t.is_exclusion('ex', n))
        n.text = u'Something something the term “ex” does not include potato'
        self.assertTrue(t.is_exclusion('ex', n))

        t.scoped_terms = {('1111',): [Ref('abc', '1', (0, 0))]}
        self.assertFalse(t.is_exclusion('ex', n))

    def test_node_definitions(self):
        t = Terms(None)
        smart_quotes = [
            (u'This has a “worD” and then more',
             [Ref('word', 'aaa', (12, 16))]),
            (u'I have “anotheR word” term and “moree”',
             [Ref('another word', 'bbb', (8, 20)),
              Ref('moree', 'bbb', (32, 37))]),
            (u'But the child “DoeS sEe”?',
             [Ref('does see', 'ccc', (15, 23))]),
            (u'Start with “this,”', [Ref('this', 'hhh', (12, 16))]),
            (u'Start with “this;”', [Ref('this', 'iii', (12, 16))]),
            (u'Start with “this.”', [Ref('this', 'jjj', (12, 16))]),
            (u'As do “subchildren”',
             [Ref('subchildren', 'ddd', (7, 18))])]

        no_defs = [
            u'This has no defs',
            u'Also has no terms',
            u'Still no terms, but',
            u'the next one does']

        xml_defs = [
            (u'(4) Thing means a thing that is defined',
             u'(4) <E T="03">Thing</E> means a thing that is defined',
             Ref('thing', 'eee', (4, 9))),
            (u'(e) Well-meaning lawyers means people who do weird things',
             u'(e) <E T="03">Well-meaning lawyers</E> means people who do '
             u'weird things',
             Ref('well-meaning lawyers', 'fff', (4, 24))),
            (u'(e) Words have the same meaning as in a dictionary',
             u'(e) <E T="03">Words</E> have the same meaning as in a '
             u'dictionary',
             Ref('words', 'ffg', (4, 9))),
            (u'(e) Banana has the same meaning as bonono',
             u'(e) <E T="03">Banana</E> has the same meaning as bonono',
             Ref('banana', 'fgf', (4, 10))),
            (u'(f) Huge billowy clouds means I want to take a nap',
             u'(f) <E T="03">Huge billowy clouds</E> means I want to take a '
             u'nap',
             Ref('huge billowy clouds', 'ggg', (4, 23))),
            (u'(v) Lawyers, in relation to coders, means something very '
             u'different',
             u'(v) <E T="03">Lawyers</E>, in relation to coders, means '
             u'something very different',
             Ref(u'lawyers', '', (4, 11))),
            ]

        xml_no_defs = [
            (u'(d) Term1 or term2 means stuff',
             u'(d) <E T="03">Term1</E> or <E T="03">term2></E> means stuff')]

        scope_term_defs = [
            ('For purposes of this section, the term blue means the color',
             Ref('blue', '11-11', (39, 43))),
            ('For purposes of paragraph (a)(1) of this section, the term '
             + 'cool bro means hip cat', Ref('cool bro', '11-22', (59, 67))),
            ('For purposes of this paragraph, po jo means "poor Joe"',
             Ref('po jo', '11-33', (32, 37)))]

        stack = ParentStack()
        stack.add(0, Node(label=['999']))
        for txt in no_defs:
            defs, exc = t.node_definitions(Node(txt), stack)
            self.assertEqual([], defs)
            self.assertEqual([], exc)
        for txt, refs in smart_quotes:
            defs, exc = t.node_definitions(Node(txt), stack)
            self.assertEqual([], defs)
            self.assertEqual([], exc)
        for txt, xml in xml_no_defs:
            node = Node(txt)
            node.tagged_text = xml
            defs, exc = t.node_definitions(node, stack)
            self.assertEqual([], defs)
            self.assertEqual([], exc)
        for txt, xml, ref in xml_defs:
            node = Node(txt, label=[ref.label])
            node.tagged_text = xml
            defs, exc = t.node_definitions(node, stack)
            self.assertEqual([ref], defs)
            self.assertEqual([], exc)
        for txt, ref in scope_term_defs:
            defs, exc = t.node_definitions(
                Node(txt, label=ref.label.split('-')), stack)
            self.assertEqual([ref], defs)
            self.assertEqual([], exc)

        #   smart quotes are affected by the parent
        stack.add(1, Node('Definitions', label=['999', '1']))
        for txt in no_defs:
            defs, exc = t.node_definitions(Node(txt), stack)
            self.assertEqual([], defs)
            self.assertEqual([], exc)
        for txt, refs in smart_quotes:
            defs, exc = t.node_definitions(Node(txt, label=[refs[0].label]),
                                           stack)
            self.assertEqual(refs, defs)
            self.assertEqual([], exc)
        for txt, xml in xml_no_defs:
            node = Node(txt)
            node.tagged_text = xml
            defs, exc = t.node_definitions(node, stack)
            self.assertEqual([], defs)
            self.assertEqual([], exc)
        for txt, xml, ref in xml_defs:
            node = Node(txt, label=[ref.label])
            node.tagged_text = xml
            defs, exc = t.node_definitions(node, stack)
            self.assertEqual([ref], defs)
            self.assertEqual([], exc)

    def test_node_defintions_act(self):
        t = Terms(None)
        stack = ParentStack()
        stack.add(0, Node('Definitions', label=['9999']))

        node = Node(u'“Act” means something else entirely')
        included, excluded = t.node_definitions(node, stack)
        self.assertEqual(1, len(included))
        self.assertEqual([], excluded)

    def test_node_definitions_needs_term(self):
        t = Terms(None)
        stack = ParentStack()
        stack.add(0, Node('Definitions', label=['9999']))
        node = Node(u"However, for purposes of rescission under §§ 1111.15 "
                    + u"and 1111.13, and for purposes of §§ 1111.12(a)(1), "
                    + u"and 1111.46(d)(4), the term means all calendar "
                    + u"days...")
        self.assertEqual(([], []), t.node_definitions(node, stack))

    def test_node_definitions_exclusion(self):
        n1 = Node(u'“Bologna” is a type of deli meat', label=['111', '1'])
        n2 = Node(u'Let us not forget that the term “bologna” does not ' +
                  'include turtle meat', label=['111', '1', 'a'])
        t = Terms(Node(label=['111'], children=[n1, n2]))
        t.pre_process()

        stack = ParentStack()
        stack.add(1, Node('Definitions'))

        included, excluded = t.node_definitions(n1, stack)
        self.assertEqual([Ref('bologna', '111-1', (1, 8))], included)
        self.assertEqual([], excluded)
        t.scoped_terms[('111', '1')] = included

        included, excluded = t.node_definitions(n2, stack)
        self.assertEqual([], included)
        self.assertEqual([Ref('bologna', '111-1-a', (33, 40))], excluded)

    def test_node_definitions_multiple_xml(self):
        t = Terms(None)
        stack = ParentStack()
        stack.add(0, Node(label=['9999']))

        winter = Node("(4) Cold and dreary mean winter.", label=['9999', '4'])
        tagged = '(4) <E T="03">Cold</E> and <E T="03">dreary</E> mean '
        tagged += 'winter.'
        winter.tagged_text = tagged
        inc, _ = t.node_definitions(winter, stack)
        self.assertEqual(len(inc), 2)
        cold, dreary = inc
        self.assertEqual(cold, Ref('cold', '9999-4', (4, 8)))
        self.assertEqual(dreary, Ref('dreary', '9999-4', (13, 19)))

        summer = Node("(i) Hot, humid, or dry means summer.",
                      label=['9999', '4'])
        tagged = '(i) <E T="03">Hot</E>, <E T="03">humid</E>, or '
        tagged += '<E T="03">dry</E> means summer.'
        summer.tagged_text = tagged
        inc, _ = t.node_definitions(summer, stack)
        self.assertEqual(len(inc), 3)
        hot, humid, dry = inc
        self.assertEqual(hot, Ref('hot', '9999-4', (4, 7)))
        self.assertEqual(humid, Ref('humid', '9999-4', (9, 14)))
        self.assertEqual(dry, Ref('dry', '9999-4', (19, 22)))

        tamale = Node("(i) Hot tamale or tamale means nom nom",
                      label=['9999', '4'])
        tagged = '(i) <E T="03">Hot tamale</E> or <E T="03"> tamale</E> '
        tagged += 'means nom nom '
        tamale.tagged_text = tagged
        inc, _ = t.node_definitions(tamale, stack)
        self.assertEqual(len(inc), 2)
        hot, tamale = inc
        self.assertEqual(hot, Ref('hot tamale', '9999-4', (4, 14)))
        self.assertEqual(tamale, Ref('tamale', '9999-4', (18, 24)))

    def test_subpart_scope(self):
        t = Terms(None)
        t.subpart_map = {
            None: ['1', '2', '3'],
            'A': ['7', '5', '0'],
            'Q': ['99', 'abc', 'q']
        }
        self.assertEqual([['111', '1'], ['111', '2'], ['111', '3']],
                         t.subpart_scope(['111', '3']))
        self.assertEqual([['115', '7'], ['115', '5'], ['115', '0']],
                         t.subpart_scope(['115', '5']))
        self.assertEqual([['62', '99'], ['62', 'abc'], ['62', 'q']],
                         t.subpart_scope(['62', 'abc']))
        self.assertEqual([], t.subpart_scope(['71', 'Z']))

    def test_determine_scope(self):
        stack = ParentStack()
        t = Terms(None)

        stack.add(0, Node(label=['1000']))
        stack.add(1, Node(label=['1000', '1']))

        # Defaults to the entire reg
        self.assertEqual([('1000',)], t.determine_scope(stack))

        stack.add(1, Node('For the purposes of this part, blah blah',
                          label=['1001', '2']))
        self.assertEqual([('1001',), ('1001', Node.INTERP_MARK)],
                         t.determine_scope(stack))

        t.subpart_map = {
            'SubPart 1': ['A', '3'],
            'Other': []
        }
        stack.add(1, Node(label=['1000', '3']))
        stack.add(2, Node('For the purposes of this subpart, yada yada',
                          label=['1000', '3', 'c']))
        self.assertEqual([('1000', 'A'), ('1000', '3'),
                          ('1000', 'A', Node.INTERP_MARK),
                          ('1000', '3', Node.INTERP_MARK)],
                         t.determine_scope(stack))

        stack.add(2, Node('For the purposes of this section, blah blah',
                          label=['1000', '3', 'd']))
        self.assertEqual([('1000', '3'), ('1000', '3', Node.INTERP_MARK)],
                         t.determine_scope(stack))

        stack.add(3, Node('For the purposes of this paragraph, blah blah',
                          label=['1000', '3', 'd', '5']))
        self.assertEqual([('1000', '3', 'd', '5'),
                          ('1000', '3', 'd', '5', Node.INTERP_MARK)],
                         t.determine_scope(stack))

        stack.add(3, Node(label=['1002', '3', 'd', '6']))
        self.assertEqual([('1000', '3'), ('1000', '3', Node.INTERP_MARK)],
                         t.determine_scope(stack))

        stack.add(3, Node('Blah as used in this paragraph, blah blah',
                          label=['1000', '3', 'd', '7']))
        self.assertEqual([('1000', '3', 'd', '7'),
                          ('1000', '3', 'd', '7', Node.INTERP_MARK)],
                         t.determine_scope(stack))

        stack.add(4, Node(u'For the purposes of this § 1000.3(d)(6)(i), blah',
                          label=['1000', '3', 'd', '6', 'i']))
        self.assertEqual([('1000', '3', 'd', '6', 'i'),
                          ('1000', '3', 'd', '6', 'i', Node.INTERP_MARK)],
                         t.determine_scope(stack))

        stack.add(4, Node(u'For the purposes of § 1000.3, blah',
                          label=['1000', '3', 'd', '6', 'ii']))
        self.assertEqual([('1000', '3'),
                          ('1000', '3', Node.INTERP_MARK)],
                         t.determine_scope(stack))

        stack.add(4, Node('As used in this section, blah blah',
                          label=['1000', '3', 'd', '6', 'iii']))
        self.assertEqual(
            [('1000', '3'), ('1000', '3', Node.INTERP_MARK)],
            t.determine_scope(stack))

    def test_pre_process(self):
        noname_subpart = Node(
            '',
            label=['88', 'Subpart'],
            node_type=Node.EMPTYPART,
            children=[
                Node(u"Definition. For the purposes of this part, "
                     + u"“abcd” is an alphabet", label=['88', '1'])])
        xqxq_subpart = Node(
            '',
            title='Subpart XQXQ: The unreadable',
            label=['88', 'Subpart', 'XQXQ'], node_type=Node.SUBPART,
            children=[
                Node(label=['88', '2'], children=[
                    Node(label=['88', '2', 'a'],
                         text="Definitions come later for the purposes of "
                              + "this section ",
                         children=[
                             Node(u"“AXAX” means axe-cop",
                                  label=['88', '2', 'a', '1'])]),
                    Node(label=['88', '2', 'b'], children=[
                        Node(label=['88', '2', 'b', 'i'], children=[
                            Node(label=['88', '2', 'b', 'i', 'A'],
                                 text=u"Definition. “Awesome sauce” means "
                                      + "great for the purposes of this "
                                      + "paragraph",)])])])])
        tree = Node(label=['88'], children=[noname_subpart, xqxq_subpart])
        t = Terms(tree)
        t.pre_process()

        self.assertTrue(('88',) in t.scoped_terms)
        self.assertEqual([Ref('abcd', '88-1', (44, 48))],
                         t.scoped_terms[('88',)])
        self.assertTrue(('88', '2') in t.scoped_terms)
        self.assertEqual([Ref('axax', '88-2-a-1', (1, 5))],
                         t.scoped_terms[('88', '2')])
        self.assertTrue(('88', '2', 'b', 'i', 'A') in t.scoped_terms)
        self.assertEqual([Ref('awesome sauce', '88-2-b-i-A', (13, 26))],
                         t.scoped_terms[('88', '2', 'b', 'i', 'A')])

        #   Check subparts are correct
        self.assertEqual({None: ['1'], 'XQXQ': ['2']}, dict(t.subpart_map))

        # Finally, make sure the references are added
        referenced = t.layer['referenced']
        self.assertTrue('abcd:88-1' in referenced)
        self.assertEqual('abcd', referenced['abcd:88-1']['term'])
        self.assertEqual('88-1', referenced['abcd:88-1']['reference'])
        self.assertEqual((44, 48), referenced['abcd:88-1']['position'])

        self.assertTrue('axax:88-2-a-1' in referenced)
        self.assertEqual('axax', referenced['axax:88-2-a-1']['term'])
        self.assertEqual('88-2-a-1', referenced['axax:88-2-a-1']['reference'])
        self.assertEqual((1, 5), referenced['axax:88-2-a-1']['position'])

        self.assertTrue('awesome sauce:88-2-b-i-A' in referenced)
        self.assertEqual('awesome sauce',
                         referenced['awesome sauce:88-2-b-i-A']['term'])
        self.assertEqual('88-2-b-i-A',
                         referenced['awesome sauce:88-2-b-i-A']['reference'])
        self.assertEqual((13, 26),
                         referenced['awesome sauce:88-2-b-i-A']['position'])

    def test_pre_process_defined_twice(self):
        tree = Node(u"The term “lol” means laugh out loud. "
                    + u"How do you pronounce “lol”, though?",
                    label=['1212', '5'])
        t = Terms(tree)
        t.pre_process()

        self.assertEqual(t.layer['referenced']['lol:1212-5']['position'],
                         (10, 13))

    def test_pre_process_subpart(self):
        root = Node("", label=['1212'])
        subpartA = Node("", label=['1212', 'Subpart', 'A'], title='Subpart A')
        section2 = Node("", label=['1212', '2'], title='1212.2')
        def1 = Node(u"“totes” means in total", label=['1212', '2', 'a'])
        subpartB = Node("", label=['1212', 'Subpart', 'B'], title='Subpart B')
        section22 = Node("\nFor the purposes of this subpart",
                         label=['1212', '22'], title='1212.22')
        def2 = Node(u"“totes” means in extremely", label=['1212', '22', 'a'])

        root.children = [subpartA, subpartB]
        subpartA.children, subpartB.children = [section2], [section22]
        section2.children, section22.children = [def1], [def2]

        t = Terms(root)
        t.pre_process()
        self.assertTrue(('1212',) in t.scoped_terms)
        self.assertEqual(len(t.scoped_terms[('1212',)]), 1)
        self.assertEqual('1212-2-a', t.scoped_terms[('1212',)][0].label)

        self.assertTrue(('1212', '22') in t.scoped_terms)
        self.assertEqual(len(t.scoped_terms[('1212', '22')]), 1)
        self.assertEqual('1212-22-a', t.scoped_terms[('1212', '22')][0].label)

    def test_excluded_offsets(self):
        t = Terms(None)
        t.scoped_terms['_'] = [
            Ref('term', 'lablab', (4, 6)), Ref('other', 'lablab', (8, 9)),
            Ref('more', 'nonnon', (1, 8))
        ]
        self.assertEqual([(4, 6), (8, 9)],
                         t.excluded_offsets('lablab', 'Some text'))
        self.assertEqual([(1, 8)], t.excluded_offsets('nonnon', 'Other'))
        self.assertEqual([], t.excluded_offsets('ababab', 'Ab ab ab'))

    def test_excluded_offsets_blacklist(self):
        t = Terms(None)
        t.scoped_terms['_'] = [Ref('bourgeois', '12-Q-2', 'Def')]
        settings.IGNORE_DEFINITIONS_IN['ALL'] = ['bourgeois pig']
        excluded = t.excluded_offsets('12-3', 'You are a bourgeois pig!')
        self.assertEqual([(10, 23)], excluded)

    def test_excluded_offsets_blacklist_per_reg(self):
        t = Terms(None)

        t.scoped_terms['_'] = [
            Ref('bourgeois', '12-Q-2', 'Def'),
            Ref('consumer', '12-Q-3', 'Def')]

        settings.IGNORE_DEFINITIONS_IN['ALL'] = ['bourgeois pig']
        settings.IGNORE_DEFINITIONS_IN['12'] = ['consumer price index']
        exclusions = [(0, 4)]
        excluded = t.per_regulation_ignores(
            exclusions, ['12', '2'], 'There is a consumer price index')
        self.assertEqual([(0, 4), (11, 31)], excluded)

    def test_excluded_offsets_blacklist_word_boundaries(self):
        t = Terms(None)
        t.scoped_terms['_'] = [Ref('act', '28-6-d', 'Def def def')]
        settings.IGNORE_DEFINITIONS_IN['ALL'] = ['shed act']
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
            if ref == 'a' and offsets == [(10, 19)]:
                found[0] = True
            if ref == 'b' and offsets == [(30, 34)]:
                found[1] = True
            if ref == 'c' and offsets == [(42, 46), (55, 59)]:
                found[2] = True
        self.assertEqual([True, True, True], found)

    def test_calculate_offsets_pluralized1(self):
        applicable_terms = [('rock band', 'a'), ('band', 'b'), ('drum', 'c'),
                            ('other thing', 'd')]
        text = "I am in a rock band. That's a band with a drum, a rock drum."
        text += " Many bands. "
        t = Terms(None)
        matches = t.calculate_offsets(text, applicable_terms)
        self.assertEqual(4, len(matches))
        found = [False, False, False, False]
        for _, ref, offsets in matches:
            if ref == 'a' and offsets == [(10, 19)]:
                found[0] = True
            if ref == 'b' and offsets == [(66, 71)]:
                found[1] = True
            if ref == 'b' and offsets == [(30, 34)]:
                found[2] = True
            if ref == 'c' and offsets == [(42, 46), (55, 59)]:
                found[3] = True
        self.assertEqual([True, True, True, True], found)

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
        self.assertEqual([(5, 18)], offsets)

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
        self.assertEqual(
            [], t.calculate_offsets(text, applicable_terms, [(23, 32)]))
        self.assertEqual(
            [('act', 'a', [(29, 32)])],
            t.calculate_offsets(text, applicable_terms, [(1, 5)]))

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
                Ref("abc", "ref1", (1, 2)),
                Ref("aabbcc", "ref2", (2, 3))],
            ("101", "22", "b"): [
                Ref("abc", "ref3", (3, 4)),
                Ref("aaa", "ref4", (4, 5)),
                Ref("abcabc", "ref5", (5, 6))],
            ("101", "22", "b", "2", "iii"): [
                Ref("abc", "ref6", (6, 7)),
                Ref("zzz", "ref7", (7, 8))]}
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
            ('AB',): [Ref("secret phrase", "AB-a", (9, 22))]
        }
        #   Term is defined in the first child
        self.assertEqual([], t.process(tree.children[0]))
        self.assertEqual(1, len(t.process(tree.children[1])))
