#vim: set encoding=utf-8
from unittest import TestCase
from lxml import etree
from lxml import html

from regparser.tree.struct import Node
from regparser.tree.xml_parser import appendices, tree_utils


class AppendicesTest(TestCase):
    def test_process_appendix(self):
        """Integration test for appendices"""
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <P>Intro text</P>
            <HD SOURCE="HD1">Header 1</HD>
            <P>Content H1-1</P>
            <P>Content H1-2</P>
            <HD SOURCE="HD2">Subheader</HD>
            <P>Subheader content</P>
            <HD SOURCE="HD1">Header <E T="03">2</E></HD>
            <P>Final <E T="03">Content</E></P>
            <GPH>
                <PRTPAGE P="650" />
                <GID>MYGID</GID>
            </GPH>
            <GPOTABLE CDEF="s50,15,15" COLS="3" OPTS="L2">
              <BOXHD>
                <CHED H="1">For some reason <LI>lis</LI></CHED>
                <CHED H="2">column two</CHED>
                <CHED H="2">a third column</CHED>
              </BOXHD>
              <ROW>
                <ENT I="01">0</ENT>
                <ENT/>
                <ENT>Content3</ENT>
              </ROW>
              <ROW>
                <ENT>Cell 1</ENT>
                <ENT>Cell 2</ENT>
                <ENT>Cell 3</ENT>
              </ROW>
            </GPOTABLE>
            <FP SOURCE="FR-1">A-3 Some header here</FP>
            <P>Content A-3</P>
            <P>A-4 Another header</P>
            <P>Content A-4</P>
        </APPENDIX>
        """
        appendix = appendices.process_appendix(etree.fromstring(xml), 1111)
        self.assertEqual(5, len(appendix.children))
        intro, h1, h2, a3, a4 = appendix.children

        self.assertEqual([], intro.children)
        self.assertEqual("Intro text", intro.text.strip())

        self.assertEqual(3, len(h1.children))
        self.assertEqual('Header 1', h1.title)
        c1, c2, sub = h1.children
        self.assertEqual([], c1.children)
        self.assertEqual('Content H1-1', c1.text.strip())
        self.assertEqual([], c2.children)
        self.assertEqual('Content H1-2', c2.text.strip())

        self.assertEqual(1, len(sub.children))
        self.assertEqual('Subheader', sub.title)
        self.assertEqual('Subheader content', sub.children[0].text.strip())

        self.assertEqual(3, len(h2.children))
        self.assertEqual('Header 2', h2.title)
        self.assertEqual('Final Content', h2.children[0].text.strip())
        self.assertEqual('![](MYGID)', h2.children[1].text.strip())
        table_lines = h2.children[2].text.strip().split('\n')
        self.assertEqual('|For some reason lis|column two|a third column|',
                         table_lines[0])
        self.assertEqual('|---|---|---|', table_lines[1])
        self.assertEqual('|0||Content3|', table_lines[2])
        self.assertEqual('|Cell 1|Cell 2|Cell 3|', table_lines[3])

        self.assertEqual('A-3 Some header here', a3.title)
        self.assertEqual('A-4 Another header', a4.title)

    def test_process_appendix_header_depth(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <P>1. Some content</P>
            <HD SOURCE="HD3">An Interruption</HD>
            <P>Moo</P>
            <P>2. More content</P>
        </APPENDIX>"""
        appendix = appendices.process_appendix(etree.fromstring(xml), 1111)
        self.assertEqual(2, len(appendix.children))
        a1, a2 = appendix.children

        self.assertEqual(['1111', 'A', '1'], a1.label)
        self.assertEqual(1, len(a1.children))
        self.assertEqual('1. Some content', a1.text.strip())

        self.assertEqual(['1111', 'A', '2'], a2.label)
        self.assertEqual(0, len(a2.children))
        self.assertEqual('2. More content', a2.text.strip())

    def test_process_appendix_header_is_paragraph(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <HD SOURCE="HD2">A-1 - First kind of awesome</HD>
            <HD SOURCE="HD3">(A) First Subkind</HD>
            <P>1. Content</P>
            <HD SOURCE="HD3">(B) Next Subkind</HD>
            <P>1. Moar Contents</P>
            <HD SOURCE="HD3">I. Remains Header</HD>
            <P>1. Content tent</P>
        </APPENDIX>"""
        appendix = appendices.process_appendix(etree.fromstring(xml), 1111)
        self.assertEqual(1, len(appendix.children))
        a1 = appendix.children[0]

        self.assertEqual(['1111', 'A', '1'], a1.label)
        self.assertEqual(2, len(a1.children))
        self.assertEqual('A-1 - First kind of awesome', a1.title.strip())
        a1a, a1B = a1.children

        self.assertEqual(['1111', 'A', '1', 'A'], a1a.label)
        self.assertEqual(1, len(a1a.children))
        self.assertEqual('(A) First Subkind', a1a.text.strip())
        self.assertEqual('1. Content', a1a.children[0].text.strip())

        self.assertEqual(['1111', 'A', '1', 'B'], a1B.label)
        self.assertEqual(1, len(a1B.children))
        self.assertEqual('(B) Next Subkind', a1B.text.strip())
        self.assertEqual('1. Moar Contents', a1B.children[0].text.strip())

        self.assertEqual(1, len(a1B.children))
        a1B1 = a1B.children[0]
        self.assertEqual(1, len(a1B1.children))
        a1B1h = a1B1.children[0]
        self.assertEqual(a1B1h.title.strip(), 'I. Remains Header')
        self.assertEqual(1, len(a1B1h.children))
        self.assertEqual(a1B1h.children[0].text.strip(), '1. Content tent')

    def test_header_ordering(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <HD SOURCE="HD1">A-1 Content</HD>
            <HD SOURCE="HD3">Level 1</HD>
            <HD SOURCE="HD2">Level 2</HD>
            <P>Paragraph</P>
            <HD SOURCE="HD1">A-1(A) More Content</HD>
            <P>A1A Paragraph</P>
        </APPENDIX>"""
        appendix = appendices.process_appendix(etree.fromstring(xml), 1111)
        self.assertEqual(2, len(appendix.children))
        a1, a1A = appendix.children

        self.assertEqual(1, len(a1A.children))

        self.assertEqual(['1111', 'A', '1'], a1.label)
        self.assertEqual(1, len(a1.children))
        a1_1 = a1.children[0]

        self.assertEqual(['1111', 'A', '1', 'h1'], a1_1.label)
        self.assertEqual(1, len(a1_1.children))
        a1_1_1 = a1_1.children[0]

        self.assertEqual(['1111', 'A', '1', 'h1', 'h2'], a1_1_1.label)
        self.assertEqual(1, len(a1_1_1.children))

    def test_process_same_sub_level(self):
        xml = u"""
        <APPENDIX>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <P>1. 1 1 1</P>
            <P>a. 1a 1a 1a</P>
            <P>b. 1b 1b 1b</P>
            <P>c. 1c 1c 1c</P>
            <P>d. 1d 1d 1d</P>
            <P>e. 1e 1e 1e</P>
            <P>f. 1f 1f 1f</P>
            <P>2. 2 2 2</P>
            <P>a. 2a 2a 2a</P>
            <P>i. 2ai 2ai 2ai</P>
            <P>ii. 2aii 2aii 2aii</P>
            <P>a. 2aiia 2aiia 2aiia</P>
            <P>b. 2aiib 2aiib 2aiib</P>
            <P>c. 2aiic 2aiic 2aiic</P>
            <P>d. 2aiid 2aiid 2aiid</P>
            <P>b. 2b 2b 2b</P>
        </APPENDIX>"""
        appendix = appendices.process_appendix(etree.fromstring(xml), 1111)
        self.assertEqual(['1111', 'A'], appendix.label)
        self.assertEqual(2, len(appendix.children))
        a1, a2 = appendix.children

        self.assertEqual(['1111', 'A', '1'], a1.label)
        self.assertEqual(6, len(a1.children))
        for i in range(6):
            self.assertEqual(['1111', 'A', '1', chr(i + ord('a'))],
                             a1.children[i].label)

        self.assertEqual(['1111', 'A', '2'], a2.label)
        self.assertEqual(2, len(a2.children))
        a2a, a2b = a2.children

        self.assertEqual(['1111', 'A', '2', 'a'], a2a.label)
        self.assertEqual(2, len(a2a.children))
        a2ai, a2aii = a2a.children

        self.assertEqual(['1111', 'A', '2', 'a', 'i'], a2ai.label)
        self.assertEqual(0, len(a2ai.children))

        self.assertEqual(['1111', 'A', '2', 'a', 'ii'], a2aii.label)
        self.assertEqual(4, len(a2aii.children))
        for i in range(4):
            self.assertEqual(['1111', 'A', '2', 'a', 'ii', chr(i + ord('a'))],
                             a2aii.children[i].label)

        self.assertEqual(['1111', 'A', '2', 'b'], a2b.label)
        self.assertEqual(0, len(a2b.children))

    def test_process_notes(self):
        xml = u"""
        <APPENDIX>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <NOTE>
                <P>Par</P>
                <E>Emem</E>
                <P>Parparpar</P>
            </NOTE>
        </APPENDIX>"""
        appendix = appendices.process_appendix(etree.fromstring(xml), 1111)
        self.assertEqual(['1111', 'A'], appendix.label)
        self.assertEqual(1, len(appendix.children))
        note = appendix.children[0]
        text = '```note\nPar\nEmem\nParparpar\n```'
        self.assertEqual(note.text, text)

    def test_initial_marker(self):
        self.assertEqual(("i", "i."), appendices.initial_marker("i. Hi"))
        self.assertEqual(("iv", "iv."), appendices.initial_marker("iv. Hi"))
        self.assertEqual(("A", "A."), appendices.initial_marker("A. Hi"))
        self.assertEqual(("3", "3."), appendices.initial_marker("3. Hi"))

        self.assertEqual(("i", "(i)"), appendices.initial_marker("(i) Hi"))
        self.assertEqual(("iv", "(iv)"), appendices.initial_marker("(iv) Hi"))
        self.assertEqual(("A", "(A)"), appendices.initial_marker("(A) Hi"))
        self.assertEqual(("3", "(3)"), appendices.initial_marker("(3) Hi"))

    def test_remove_toc(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <FP>A-1 Awesome</FP>
            <FP>A-2 More Awesome</FP>
            <FP>A-1 Incorrect TOC</FP>
            <P>A-3 The End of Awesome</P>
            <HD>A-1Awesomer</HD>
            <P>Content content</P>
        </APPENDIX>"""
        #   Note that the title isn't identical
        xml = etree.fromstring(xml)
        appendices.remove_toc(xml, 'A')
        self.assertEqual(['EAR', 'HD', 'HD', 'P'], [t.tag for t in xml])

        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <FP>A-1 Awesome</FP>
            <FP>A-2 More Awesome</FP>
            <FP>A-1 Incorrect TOC</FP>
            <P>A-3 The End of Awesome</P>
            <GPH><GID>GIDGID</GID></GPH>
            <HD>A-3Awesomer</HD>
            <P>Content content</P>
        </APPENDIX>"""
        #   Note that the title isn't identical
        xml = etree.fromstring(xml)
        appendices.remove_toc(xml, 'A')
        self.assertEqual(['EAR', 'HD', 'GPH', 'HD', 'P'], [t.tag for t in xml])

        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <FP>A-1 Awesome</FP>
            <P>Good Content here</P>
            <FP>A-2 More Awesome</FP>
            <P>More Content</P>
            <HD>A-11 Crank It Up</HD>
            <P>Content content</P>
        </APPENDIX>"""
        xml = etree.fromstring(xml)
        appendices.remove_toc(xml, 'A')
        self.assertEqual(['EAR', 'HD', 'FP', 'P', 'FP', 'P', 'HD', 'P'],
                         [t.tag for t in xml])

    def test_title_label_pair(self):
        title = u'A-1—Model Clauses'
        self.assertEqual(('1', 2), appendices.title_label_pair(title, 'A'))

        title = u'Part III—Construction Period'
        self.assertEqual(('III', 2), appendices.title_label_pair(title, 'A'))

    def test_title_label_pair_parens(self):
        title = u'G-13(A)—Has No parent'
        self.assertEqual(('13(A)', 2), appendices.title_label_pair(title, 'G'))

        title = u'G-13(C)(1) - Some Title'
        self.assertEqual(('13(C)(1)', 2),
                         appendices.title_label_pair(title, 'G'))

        title = u'G-13A - Some Title'
        self.assertEqual(('13A', 2), appendices.title_label_pair(title, 'G'))

        title = u'G-13And Some Smashed Text'
        self.assertEqual(('13', 2), appendices.title_label_pair(title, 'G'))


class AppendixProcessorTest(TestCase):
    def setUp(self):
        self.ap = appendices.AppendixProcessor()
        self.ap.paragraph_counter = 0
        self.ap.depth = 0
        self.ap.m_stack = tree_utils.NodeStack()

    def result(self):
        return self.ap.m_stack.peek_last()

    def test_paragraph_no_marker(self):
        self.ap.paragraph_no_marker("Paragraph Text")
        lvl, node = self.result()
        self.assertEqual(node.text, 'Paragraph Text')
        self.assertEqual(0, lvl)
        self.assertEqual(node.label, ['p1'])

        #   If a header was before the paragraph, increment the level 1
        self.ap.m_stack.add(0, Node(label=['h1'], title='Some section'))
        self.ap.paragraph_no_marker("Paragraph Text")
        lvl, node = self.result()
        self.assertEqual(node.text, 'Paragraph Text')
        self.assertEqual(1, lvl)
        self.assertEqual(node.label, ['p2'])

    def test_paragraph_with_marker(self):
        self.ap.paragraph_with_marker("(a) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(a) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['a'])

        self.ap.paragraph_with_marker("(b) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(b) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['b'])

        self.ap.paragraph_with_marker("(1) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(1) A paragraph')
        self.assertEqual(lvl, 2)
        self.assertEqual(node.label, ['1'])

        self.ap.paragraph_with_marker("(2) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(2) A paragraph')
        self.assertEqual(lvl, 2)
        self.assertEqual(node.label, ['2'])

        self.ap.paragraph_with_marker("(c) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(c) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['c'])

        self.ap.paragraph_no_marker("Some text")
        lvl, node = self.result()
        self.assertEqual(node.text, 'Some text')
        self.assertEqual(lvl, 1)    # Stay on the same level
        self.assertEqual(node.label, ['p1'])

        self.ap.paragraph_with_marker("(d) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(d) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['d'])

    def test_paragraph_period(self):
        self.ap.paragraph_with_marker("1. A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '1. A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['1'])

        self.ap.paragraph_with_marker("(b) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(b) A paragraph')
        self.assertEqual(lvl, 2)
        self.assertEqual(node.label, ['b'])

        self.ap.paragraph_with_marker("A. A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, 'A. A paragraph')
        self.assertEqual(lvl, 3)
        self.assertEqual(node.label, ['A'])

        self.ap.paragraph_no_marker("code . is here")
        lvl, node = self.result()
        self.assertEqual(node.text, 'code . is here')
        self.assertEqual(lvl, 3)    # Stay on the same level
        self.assertEqual(node.label, ['p1'])

    def test_paragraph_roman(self):
        self.ap.paragraph_with_marker("(1) A paragraph", "(b) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(1) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['1'])

        self.ap.paragraph_with_marker("(b) A paragraph", "(i) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(b) A paragraph')
        self.assertEqual(lvl, 2)
        self.assertEqual(node.label, ['b'])

        self.ap.paragraph_with_marker("(i) A paragraph", "(ii) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(i) A paragraph')
        self.assertEqual(lvl, 3)
        self.assertEqual(node.label, ['i'])

        self.ap.paragraph_with_marker("(ii) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(ii) A paragraph')
        self.assertEqual(lvl, 3)
        self.assertEqual(node.label, ['ii'])

        self.ap.paragraph_with_marker("(v) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(v) A paragraph')
        self.assertEqual(lvl, 3)
        self.assertEqual(node.label, ['v'])

    def test_split_paragraph_text(self):
        res = self.ap.split_paragraph_text("(a) Paragraph. (1) Next paragraph")
        self.assertEqual(['(a) Paragraph. ', '(1) Next paragraph', ''], res)

        res = self.ap.split_paragraph_text("(a) (Keyterm) (1) Next paragraph")
        self.assertEqual(['(a) (Keyterm) ', '(1) Next paragraph', ''], res)

        res = self.ap.split_paragraph_text("(a) Mentions one (1) comment")
        self.assertEqual(['(a) Mentions one (1) comment', ''], res)

    def test_paragraph_double_depth(self):
        self.ap.paragraph_with_marker("(a) A paragraph", "(1) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(a) A paragraph')
        self.assertEqual(lvl, 1)
        self.assertEqual(node.label, ['a'])

        self.ap.paragraph_with_marker("(1) A paragraph", "(i) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(1) A paragraph')
        self.assertEqual(lvl, 2)
        self.assertEqual(node.label, ['1'])

        self.ap.paragraph_with_marker("(i) A paragraph", "(A) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(i) A paragraph')
        self.assertEqual(lvl, 3)
        self.assertEqual(node.label, ['i'])

        self.ap.paragraph_with_marker("(A) A paragraph")
        lvl, node = self.result()
        self.assertEqual(node.text, '(A) A paragraph')
        self.assertEqual(lvl, 4)
        self.assertEqual(node.label, ['A'])

    def test_process_part_cap(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <HD SOURCE="HD1">Part I - Stuff</HD>
            <P>A. Content</P>
        </APPENDIX>
        """
        appendix = self.ap.process(etree.fromstring(xml), 1111)
        self.assertEqual(1, len(appendix.children))
        aI = appendix.children[0]

        self.assertEqual(1, len(aI.children))

    def test_process_depth_look_forward(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <P>(a) aaaaa</P>
            <P>(i) iiiii</P>
            <P>Text text</P>
            <P>(ii) ii ii ii</P>
        </APPENDIX>
        """
        appendix = self.ap.process(etree.fromstring(xml), 1111)
        self.assertEqual(1, len(appendix.children))
        Aa = appendix.children[0]

        child_labels = [child.label for child in Aa.children]
        self.assertTrue(['1111', 'A', 'a', 'i'] in child_labels)
        self.assertTrue(['1111', 'A', 'a', 'ii'] in child_labels)

    def test_process_header_depth(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <HD SOURCE="HD1">Title 1</HD>
            <P>(1) Content 1</P>
            <P>(2) Content 2</P>
            <HD SOURCE="HD1">Title 2</HD>
            <P>A. Content</P>
        </APPENDIX>
        """
        appendix = self.ap.process(etree.fromstring(xml), 1111)
        self.assertEqual(2, len(appendix.children))
        a1, a2 = appendix.children

        self.assertEqual(2, len(a1.children))
        self.assertEqual(1, len(a2.children))

    def test_process_roman(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <HD SOURCE="HD1">Part I - Something</HD>
            <P>(a) Something</P>
            <GPH><GID>Contains (b)(i) - (iv)</GID></GPH>
            <P>(v) Something else</P>
            <P>(vi) Something more</P>
        </APPENDIX>
        """
        appendix = self.ap.process(etree.fromstring(xml), 1111)
        self.assertEqual(1, len(appendix.children))
        aI = appendix.children[0]
        self.assertEqual(2, len(aI.children))
        aIa, aIb = aI.children
        self.assertEqual(2, len(aIb.children))
        aIv, aIvi = aIb.children
        self.assertEqual(['1111', 'A', 'I', 'a'], aIa.label)
        self.assertEqual(['1111', 'A', 'I', 'p1'], aIb.label)
        self.assertEqual(['1111', 'A', 'I', 'p1', 'v'], aIv.label)
        self.assertEqual(['1111', 'A', 'I', 'p1', 'vi'], aIvi.label)

    def test_process_collapsed(self):
        xml = u"""
        <APPENDIX>
            <EAR>Pt. 1111, App. A</EAR>
            <HD SOURCE="HED">Appendix A to Part 1111—Awesome</HD>
            <HD SOURCE="HD1">Part I - Something</HD>
            <P>(a) Something referencing § 999.2(a)(1). (1) Content</P>
            <P>(2) Something else</P>
        </APPENDIX>
        """
        appendix = self.ap.process(etree.fromstring(xml), 1111)
        self.assertEqual(1, len(appendix.children))
        aI = appendix.children[0]
        self.assertEqual(1, len(aI.children))
        aIa = aI.children[0]
        self.assertEqual(2, len(aIa.children))
        aIa1, aIa2 = aIa.children
        self.assertEqual(['1111', 'A', 'I', 'a', '1'], aIa1.label)
        self.assertEqual('(1) Content', aIa1.text)
        self.assertEqual(['1111', 'A', 'I', 'a', '2'], aIa2.label)
        self.assertEqual('(2) Something else', aIa2.text)
